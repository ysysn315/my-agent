import json

import pytest

from app.agents.tool_runtime import (
    ToolExecutionPolicy,
    get_circuit_snapshot,
    override_tool_policy,
    reset_tool_runtime_state,
    safe_tool_execute,
)


class FakeTool:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    async def ainvoke(self, args):
        self.calls.append(args)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture(autouse=True)
def reset_runtime_state():
    reset_tool_runtime_state()
    yield
    reset_tool_runtime_state()


@pytest.mark.asyncio
async def test_safe_tool_execute_retries_then_succeeds():
    override_tool_policy(
        "flaky_tool",
        retry_attempts=1,
        timeout_seconds=1.0,
        failure_threshold=3,
        recovery_timeout_seconds=60.0,
        backoff_seconds=0.0,
    )
    tool = FakeTool([TimeoutError("timed out"), "ok"])

    result = await safe_tool_execute("flaky_tool", tool, {"query": "cpu"})

    assert result.success is True
    assert result.attempts == 2
    assert result.content == "ok"
    assert tool.calls == [{"query": "cpu"}, {"query": "cpu"}]
    assert get_circuit_snapshot("flaky_tool")["flaky_tool"]["state"] == "closed"


@pytest.mark.asyncio
async def test_safe_tool_execute_opens_circuit_after_repeated_failures():
    override_tool_policy(
        "always_down",
        retry_attempts=0,
        timeout_seconds=1.0,
        failure_threshold=2,
        recovery_timeout_seconds=60.0,
        backoff_seconds=0.0,
    )

    first = await safe_tool_execute("always_down", FakeTool([ConnectionError("down")]), {})
    second = await safe_tool_execute("always_down", FakeTool([ConnectionError("still down")]), {})
    third_tool = FakeTool(["should not run"])
    third = await safe_tool_execute("always_down", third_tool, {})

    assert first.success is False
    assert first.status == "degraded"
    assert second.status == "circuit_open"
    assert second.circuit_state == "open"
    assert third.status == "circuit_open"
    assert third.attempts == 0
    assert third_tool.calls == []


@pytest.mark.asyncio
async def test_safe_tool_execute_allows_half_open_recovery():
    policy = ToolExecutionPolicy(
        retry_attempts=0,
        timeout_seconds=1.0,
        failure_threshold=1,
        recovery_timeout_seconds=0.0,
        backoff_seconds=0.0,
    )
    await safe_tool_execute("recoverable_tool", FakeTool([ConnectionError("down")]), {}, policy=policy)

    result = await safe_tool_execute("recoverable_tool", FakeTool(["healthy"]), {}, policy=policy)

    assert result.success is True
    assert result.content == "healthy"
    assert get_circuit_snapshot("recoverable_tool")["recoverable_tool"]["state"] == "closed"


@pytest.mark.asyncio
async def test_safe_tool_execute_retries_structured_failure_results():
    override_tool_policy(
        "json_tool",
        retry_attempts=1,
        timeout_seconds=1.0,
        failure_threshold=3,
        recovery_timeout_seconds=60.0,
        backoff_seconds=0.0,
    )
    tool = FakeTool(
        [
            json.dumps({"success": False, "error": "temporary error"}),
            json.dumps({"success": True, "data": "ok"}),
        ]
    )

    result = await safe_tool_execute("json_tool", tool, {"x": 1})

    assert result.success is True
    assert result.attempts == 2
    assert json.loads(result.content)["success"] is True
