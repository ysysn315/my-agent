import pytest

import app.agents.chat_agent as chat_agent_module
from app.agents.tool_runtime import ToolExecutionResult
from langchain_core.messages import ToolMessage


class FakeResponse:
    def __init__(self, content, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class FakeChatTongyi:
    def __init__(self, *args, **kwargs):
        self.messages = []

    def bind_tools(self, tools):
        self.tools = tools
        return self

    async def ainvoke(self, messages):
        self.messages.append(messages)
        last = messages[-1]
        if isinstance(last, ToolMessage):
            return FakeResponse(f"final:{last.content}")
        return FakeResponse(
            "",
            tool_calls=[{"name": "query_internal_docs", "args": {"query": "cpu"}, "id": "tool-1"}],
        )


class DummyTool:
    def __init__(self, name):
        self.name = name


@pytest.mark.asyncio
async def test_chat_agent_uses_tool_runtime_for_tool_calls(monkeypatch):
    calls = []

    monkeypatch.setattr(chat_agent_module, "ChatTongyi", FakeChatTongyi)

    async def fake_safe_tool_execute(tool_name, tool, tool_args, **kwargs):
        calls.append({"tool_name": tool_name, "tool_args": tool_args})
        return ToolExecutionResult(
            tool_name=tool_name,
            status="degraded",
            content="docs unavailable",
            attempts=2,
            error="timeout",
            degraded=True,
            circuit_state="closed",
        )

    monkeypatch.setattr(chat_agent_module, "safe_tool_execute", fake_safe_tool_execute)

    agent = chat_agent_module.ChatAgent(
        api_key="test-key",
        model="test-model",
        tools=[DummyTool("query_internal_docs")],
    )

    answer = await agent.chat("how to troubleshoot cpu")

    assert calls == [{"tool_name": "query_internal_docs", "tool_args": {"query": "cpu"}}]
    assert answer == "final:[tool_status=degraded] docs unavailable"
