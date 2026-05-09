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
async def test_query_rewriter_includes_summary_in_prompt(monkeypatch):
    QueryRewriter = _load_query_rewriter_with_stubs(monkeypatch)
    llm = FakeLLM("payment-service CPU 告警如何处理")
    rewriter = QueryRewriter(llm)

    rewritten = await rewriter.rewrite(
        "这个怎么处理？",
        history=[{"role": "user", "content": "最近 payment-service CPU 很高"}],
        summary="之前已经确认是 payment-service 的 CPU 告警，用户在排查处理方法。",
    )

    assert rewritten == "payment-service CPU 告警如何处理"
    prompt = llm.prompts[0]
    assert "之前已经确认是 payment-service 的 CPU 告警" in prompt
    assert "最近 payment-service CPU 很高" in prompt
    assert "这个怎么处理？" in prompt
