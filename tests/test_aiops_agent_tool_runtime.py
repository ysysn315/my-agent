import pytest

import app.agents.aiops_agent as aiops_agent_module
from app.agents.tool_runtime import ToolExecutionResult


class FakeResponse:
    def __init__(self, content, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class FakeToolLLM:
    def __init__(self):
        self.messages = []

    async def ainvoke(self, messages):
        self.messages.append(messages)
        return FakeResponse(
            "",
            tool_calls=[{"name": "query_log", "args": {"query": "cpu", "time_range": "5m"}, "id": "tool-1"}],
        )


class FakeChatTongyi:
    def __init__(self, *args, **kwargs):
        self.messages = []
        self.responses = [
            "1. Call query_log to inspect CPU-related logs.",
            "Root cause is CPU saturation. Evidence comes from the collected log result.",
        ]
        self.tool_llm = FakeToolLLM()

    def bind_tools(self, tools):
        self.tools = tools
        return self.tool_llm

    async def ainvoke(self, messages):
        self.messages.append(messages)
        return FakeResponse(self.responses.pop(0))


class DummyTool:
    def __init__(self, name):
        self.name = name


@pytest.mark.asyncio
async def test_aiops_agent_uses_tool_runtime_for_tool_calls(monkeypatch):
    calls = []

    monkeypatch.setattr(aiops_agent_module, "ChatTongyi", FakeChatTongyi)

    async def fake_safe_tool_execute(tool_name, tool, tool_args, **kwargs):
        calls.append({"tool_name": tool_name, "tool_args": tool_args})
        return ToolExecutionResult(
            tool_name=tool_name,
            status="success",
            content='{"success": true, "logs": ["cpu warning"]}',
            attempts=1,
            degraded=False,
            circuit_state="closed",
        )

    monkeypatch.setattr(aiops_agent_module, "safe_tool_execute", fake_safe_tool_execute)

    agent = aiops_agent_module.AIOpsAgent(
        api_key="test-key",
        model="test-model",
        tools=[DummyTool("query_log")],
    )

    report = await agent.analyze("payment-service cpu is high")

    assert calls == [{"tool_name": "query_log", "tool_args": {"query": "cpu", "time_range": "5m"}}]
    assert "Root cause is CPU saturation" in report


def test_aiops_agent_counts_only_successful_tool_steps():
    past_steps = [
        "tool=query_log\nstatus=degraded\nattempts=2\nargs={}\nresult=temporary failure",
        "tool=query_log\nstatus=success\nattempts=1\nargs={}\nresult=ok",
        "tool=query_internal_docs\nstatus=circuit_open\nattempts=0\nargs={}\nresult=unavailable",
    ]

    assert aiops_agent_module.AIOpsAgent._count_successful_tool(past_steps, "query_log") == 1
    assert aiops_agent_module.AIOpsAgent._has_successful_tool(past_steps, "query_log") is True
    assert aiops_agent_module.AIOpsAgent._has_successful_tool(past_steps, "query_internal_docs") is False
