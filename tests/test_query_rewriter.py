import importlib
import sys
import types

import pytest


class FakeResponse:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    async def ainvoke(self, messages):
        self.prompts.append(messages[-1].content)
        return FakeResponse(self.responses.pop(0))


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
async def test_rewrite_uses_history_to_build_self_contained_query(monkeypatch):
    QueryRewriter = _load_query_rewriter_with_stubs(monkeypatch)
    llm = FakeLLM(["payment-service CPU 使用率过高怎么排查"])
    rewriter = QueryRewriter(llm)

    rewritten = await rewriter.rewrite(
        "这个怎么处理？",
        history=[
            {"role": "user", "content": "payment-service CPU 飙高"},
            {"role": "assistant", "content": "已经定位到 payment-service 的 CPU 告警"},
        ],
    )

    assert rewritten == "payment-service CPU 使用率过高怎么排查"
    assert "payment-service CPU 飙高" in llm.prompts[0]
    assert "这个怎么处理？" in llm.prompts[0]


@pytest.mark.asyncio
async def test_process_with_expansions_rewrites_before_expand(monkeypatch):
    QueryRewriter = _load_query_rewriter_with_stubs(monkeypatch)
    llm = FakeLLM(
        [
            "payment-service CPU 使用率过高怎么排查",
            "payment-service CPU 高\npayment-service CPU 告警排查\npayment-service pod CPU 飙升",
        ]
    )
    rewriter = QueryRewriter(llm)

    queries = await rewriter.process_with_expansions(
        "这个怎么处理？",
        history=[{"role": "user", "content": "payment-service CPU 飙高"}],
    )

    assert queries[0] == "payment-service CPU 使用率过高怎么排查"
    assert "自包含查询：" in llm.prompts[1]
    assert "payment-service CPU 使用率过高怎么排查" in llm.prompts[1]
