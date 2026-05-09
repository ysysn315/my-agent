import pytest

import app.services.chat_service as chat_service_module


class FakeLLM:
    def __init__(self, *args, **kwargs):
        return None


class FakeSummaryLLM:
    def __init__(self, response):
        self.response = response
        self.messages = []

    async def ainvoke(self, messages):
        self.messages.append(messages)

        class Response:
            def __init__(self, content):
                self.content = content

        return Response(self.response)


class FakeChatAgent:
    def __init__(self):
        self.calls = []

    async def chat(self, question, history, summary=""):
        self.calls.append({"question": question, "history": history, "summary": summary})
        return "agent answer"


class FakeQueryRewriter:
    def __init__(self):
        self.calls = []

    async def process(self, query, history=None, summary=None):
        self.calls.append({"query": query, "history": history, "summary": summary})
        return f"rewritten::{query}"


class FakeRAGService:
    def __init__(self):
        self.query_rewriter = FakeQueryRewriter()


class FakeSessionStore:
    def __init__(self):
        self.max_messages = 4
        self.history = [
            {"role": "user", "content": "问题 1"},
            {"role": "assistant", "content": "回答 1"},
            {"role": "user", "content": "问题 2"},
            {"role": "assistant", "content": "回答 2"},
        ]
        self.summary = "较早轮次摘要"

    def get_history(self, session_id):
        return list(self.history)

    def get_summary(self, session_id):
        return self.summary

    def add_message(self, session_id, role, content):
        self.history.append({"role": role, "content": content})

    def get_messages_to_summarize(self, session_id):
        if len(self.history) <= self.max_messages:
            return []
        return self.history[:-self.max_messages]

    def apply_summary_and_trim(self, session_id, summary):
        self.summary = summary
        self.history = self.history[-self.max_messages :]


class FakeSettings:
    dashscope_api_key = "test-key"
    chat_model = "test-model"
    tavily_api_key = None
    tavily_base_url = None


@pytest.mark.asyncio
async def test_chat_service_uses_summary_for_rewrite_and_compacts_history(monkeypatch):
    monkeypatch.setattr(chat_service_module, "ChatTongyi", FakeLLM)

    session_store = FakeSessionStore()
    service = chat_service_module.ChatService(FakeSettings(), session_store)
    service.rag_service = FakeRAGService()
    service.chat_agent = FakeChatAgent()
    service.summary_llm = FakeSummaryLLM("合并后的摘要")

    async def fake_ensure_agent():
        return None

    async def fake_ensure_rag_service():
        return None

    service._ensure_agent = fake_ensure_agent
    service._ensure_rag_service = fake_ensure_rag_service

    result = await service.chat("session-1", "这个怎么处理？")

    assert result["answer"] == "agent answer"
    assert service.rag_service.query_rewriter.calls == [
        {
            "query": "这个怎么处理？",
            "history": [
                {"role": "user", "content": "问题 1"},
                {"role": "assistant", "content": "回答 1"},
                {"role": "user", "content": "问题 2"},
                {"role": "assistant", "content": "回答 2"},
            ],
            "summary": "较早轮次摘要",
        }
    ]
    assert service.chat_agent.calls == [
        {
            "question": "rewritten::这个怎么处理？",
            "history": [
                {"role": "user", "content": "问题 1"},
                {"role": "assistant", "content": "回答 1"},
                {"role": "user", "content": "问题 2"},
                {"role": "assistant", "content": "回答 2"},
            ],
            "summary": "较早轮次摘要",
        }
    ]
    assert session_store.summary == "合并后的摘要"
    assert session_store.history == [
        {"role": "user", "content": "问题 2"},
        {"role": "assistant", "content": "回答 2"},
        {"role": "user", "content": "这个怎么处理？"},
        {"role": "assistant", "content": "agent answer"},
    ]
