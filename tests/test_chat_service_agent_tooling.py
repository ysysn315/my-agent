import pytest

import app.services.chat_service as chat_service_module


class FakeLLM:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class FakeChatAgent:
    def __init__(self, api_key, model, tools):
        self.api_key = api_key
        self.model = model
        self.tools = tools


class FakeSessionStore:
    def get_history(self, session_id):
        return []

    def add_message(self, session_id, role, content):
        return None


class FakeSettings:
    dashscope_api_key = "test-key"
    chat_model = "test-model"
    tavily_api_key = None
    tavily_base_url = None


@pytest.mark.asyncio
async def test_chat_service_agent_uses_rag_service_for_docs_tool(monkeypatch):
    captured = {}
    fake_docs_tool = object()
    fake_rag_service = object()

    monkeypatch.setattr(chat_service_module, "ChatTongyi", FakeLLM)
    monkeypatch.setattr(chat_service_module, "ChatAgent", FakeChatAgent)

    def fake_create_docs_tool(retriever):
        captured["retriever"] = retriever
        return fake_docs_tool

    monkeypatch.setattr(chat_service_module, "create_docs_tool", fake_create_docs_tool)

    service = chat_service_module.ChatService(FakeSettings(), FakeSessionStore())
    service.rag_service = fake_rag_service

    async def fake_ensure_rag_service():
        return None

    service._ensure_rag_service = fake_ensure_rag_service

    await service._ensure_agent()

    assert captured["retriever"] is fake_rag_service
    assert service.chat_agent is not None
    assert fake_docs_tool in service.chat_agent.tools
