import json
from pathlib import Path
from typing import Dict, Any

from langchain_community.chat_models import ChatTongyi

from app.core.settings import get_settings
from app.clients.milvus_client import MilvusClient
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.services.rag_service import RAGService


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str, data: Dict[str, Any]):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


async def build_rag(enable_hybrid: bool, enable_rerank: bool, dense_top_k: int = 10):
    settings = get_settings()
    milvus_client = MilvusClient(settings)
    await milvus_client.connect()
    await milvus_client.ensure_collection()

    embedding_service = EmbeddingService(settings)

    reranker_llm = ChatTongyi(
        dashscope_api_key=settings.dashscope_api_key,
        model_name="qwen-turbo",
        streaming=False,
        temperature=0.0,
    )

    vector_store = VectorStore(
        milvus_client=milvus_client,
        embedding_service=embedding_service,
        reranker_llm=reranker_llm,
        reranker=None,
        dense_top_k=dense_top_k,
        enable_rerank=enable_rerank,
        enable_hybrid=enable_hybrid,
    )

    llm = ChatTongyi(
        dashscope_api_key=settings.dashscope_api_key,
        model_name=settings.chat_model,
        streaming=False,
        temperature=0.0,
    )

    rag_service = RAGService(vector_store, llm)
    return rag_service, vector_store
