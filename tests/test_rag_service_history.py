import pytest

from app.services.rag_service import RAGService


class FakeVectorStore:
    def __init__(self):
        self.calls = []

    async def search(self, query, top_k=3, metadata_filters=None):
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
                "metadata_filters": metadata_filters,
            }
        )
        return [
            {
                "content": f"doc for {query}",
                "metadata": {"source": f"{query}.md"},
                "score": 1.0,
            }
        ]


class FakeQueryRewriter:
    def __init__(self):
        self.process_calls = []
        self.process_with_expansions_calls = []

    async def process(self, query, history=None, summary=None):
        self.process_calls.append({"query": query, "history": history, "summary": summary})
        return f"rewritten::{query}"

    async def process_with_expansions(self, query, history=None, summary=None):
        self.process_with_expansions_calls.append(
            {"query": query, "history": history, "summary": summary}
        )
        return [f"rewritten::{query}", f"expanded::{query}"]


@pytest.mark.asyncio
async def test_rag_service_retrieve_multi_query_forwards_history_filters_and_summary():
    vector_store = FakeVectorStore()
    service = RAGService(vector_store, llm=None)
    service.query_rewriter = FakeQueryRewriter()

    history = [
        {"role": "user", "content": "payment-service CPU 飙高"},
        {"role": "assistant", "content": "已经定位到 CPU 告警"},
    ]

    docs = await service.retrieve_multi_query(
        "这个怎么处理？",
        top_k=2,
        history=history,
        metadata_filters={"doc_type": "markdown"},
        session_summary="用户正在排查 payment-service 的 CPU 告警",
    )

    assert len(docs) == 2
    assert service.query_rewriter.process_with_expansions_calls == [
        {
            "query": "这个怎么处理？",
            "history": history,
            "summary": "用户正在排查 payment-service 的 CPU 告警",
        }
    ]
    assert vector_store.calls == [
        {
            "query": "rewritten::这个怎么处理？",
            "top_k": 2,
            "metadata_filters": {"doc_type": "markdown"},
        },
        {
            "query": "expanded::这个怎么处理？",
            "top_k": 2,
            "metadata_filters": {"doc_type": "markdown"},
        },
    ]


@pytest.mark.asyncio
async def test_rag_service_retrieve_forwards_history_and_summary_to_single_query_rewrite():
    vector_store = FakeVectorStore()
    service = RAGService(vector_store, llm=None)
    service.query_rewriter = FakeQueryRewriter()

    history = [{"role": "user", "content": "pod CPU 高"}]

    docs = await service.retrieve(
        "这个怎么处理？",
        top_k=1,
        history=history,
        metadata_filters={"source": "cpu.md"},
        session_summary="用户关注 CPU 异常",
    )

    assert len(docs) == 1
    assert service.query_rewriter.process_calls == [
        {
            "query": "这个怎么处理？",
            "history": history,
            "summary": "用户关注 CPU 异常",
        }
    ]
    assert vector_store.calls == [
        {
            "query": "rewritten::这个怎么处理？",
            "top_k": 1,
            "metadata_filters": {"source": "cpu.md"},
        }
    ]
