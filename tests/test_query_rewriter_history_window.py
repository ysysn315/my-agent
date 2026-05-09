import importlib
import sys
import types

import pytest


class FakeResponse:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    def __init__(self, response: str):
        self.response = response
        self.prompts = []

    async def ainvoke(self, messages):
        self.prompts.append(messages[-1].content)
        return FakeResponse(self.response)


def _load_query_rewriter_with_stubs(monkeypatch):
    messages_module = types.ModuleType("langchain_core.messages")

    class StubSystemMessage:
        def __init__(self, content: str):
            self.content = content

    class StubHumanMessage:
        def __init__(self, content: str):
            self.content = content

    messages_module.SystemMessage = StubSystemMessage
    messages_module.HumanMessage = StubHumanMessage

    loguru_module = types.ModuleType("loguru")

    class StubLogger:
        def info(self, *args, **kwargs):
            return None

        def warning(self, *args, **kwargs):
            return None

    loguru_module.logger = StubLogger()

    monkeypatch.setitem(sys.modules, "langchain_core.messages", messages_module)
    monkeypatch.setitem(sys.modules, "loguru", loguru_module)
    sys.modules.pop("app.rag.query_rewriter", None)
    module = importlib.import_module("app.rag.query_rewriter")
    return module.QueryRewriter


@pytest.mark.asyncio
async def test_query_rewriter_only_uses_recent_history_messages(monkeypatch):
    QueryRewriter = _load_query_rewriter_with_stubs(monkeypatch)
    llm = FakeLLM("rewritten question")
    rewriter = QueryRewriter(llm, max_history_messages=2)

    history = [
        {"role": "user", "content": "old user message"},
        {"role": "assistant", "content": "old assistant message"},
        {"role": "user", "content": "recent user message"},
        {"role": "assistant", "content": "recent assistant message"},
    ]

    rewritten = await rewriter.rewrite("follow-up question", history=history)

    assert rewritten == "rewritten question"
    prompt = llm.prompts[0]
    assert "recent user message" in prompt
    assert "recent assistant message" in prompt
    assert "old user message" not in prompt
    assert "old assistant message" not in prompt
