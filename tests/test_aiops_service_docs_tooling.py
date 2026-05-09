import pytest

import app.services.aiops_service as aiops_service_module


class FakeAIOpsAgent:
    def __init__(self, api_key, model, tools):
        self.api_key = api_key
        self.model = model
        self.tools = tools

    async def analyze(self, problem):
        return "ok"

    async def analyze_stream(self, problem):
        if False:
            yield None


class FakeMilvusClient:
    def __init__(self, settings):
        self.settings = settings
        self.connected = False
        self.collection_ready = False

    async def connect(self):
        self.connected = True

    async def ensure_collection(self):
        self.collection_ready = True


class FakeEmbeddingService:
    def __init__(self, settings):
        self.settings = settings


class FakeVectorStore:
    def __init__(self, milvus_client, embedding_service):
        self.milvus_client = milvus_client
        self.embedding_service = embedding_service


class FakeLLM:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class FakeRAGService:
    def __init__(self, vector_store, llm):
        self.vector_store = vector_store
        self.llm = llm


class FakeSettings:
    dashscope_api_key = "test-key"
    chat_model = "test-model"


@pytest.mark.asyncio
async def test_aiops_service_uses_rag_service_for_docs_tool(monkeypatch):
    captured = {}
    fake_docs_tool = object()

    monkeypatch.setattr(aiops_service_module, "AIOpsAgent", FakeAIOpsAgent)
    monkeypatch.setattr(aiops_service_module, "MilvusClient", FakeMilvusClient)
    monkeypatch.setattr(aiops_service_module, "EmbeddingService", FakeEmbeddingService)
    monkeypatch.setattr(aiops_service_module, "VectorStore", FakeVectorStore)
    monkeypatch.setattr(aiops_service_module, "ChatTongyi", FakeLLM)
    monkeypatch.setattr(aiops_service_module, "RAGService", FakeRAGService)

    def fake_create_docs_tool(retriever):
        captured["retriever"] = retriever
        return fake_docs_tool

    monkeypatch.setattr(aiops_service_module, "create_docs_tool", fake_create_docs_tool)

    service = aiops_service_module.AIOpsService(FakeSettings())
    await service._ensure_docs_tool()

    assert isinstance(captured["retriever"], FakeRAGService)
    assert captured["retriever"].vector_store is service.vector_store
    assert service.tools[2] is fake_docs_tool
    assert service._docs_ready is True
