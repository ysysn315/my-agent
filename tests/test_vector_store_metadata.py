import pytest

from app.rag.vector_store import VectorStore


class FakeEmbeddingService:
    async def embed_text(self, query: str):
        return [0.1, 0.2, 0.3]


class FakeEntity:
    def __init__(self, content, metadata):
        self._data = {"content": content, "metadata": metadata}

    def get(self, key):
        return self._data.get(key)


class FakeHit:
    def __init__(self, content, metadata, score=1.0):
        self.entity = FakeEntity(content, metadata)
        self.score = score


class FakeCollection:
    def __init__(self, hits):
        self.hits = hits
        self.last_search_kwargs = None

    def search(self, **kwargs):
        self.last_search_kwargs = kwargs
        return [self.hits]


class FakeMilvusClient:
    def __init__(self, collection):
        self.collection = collection


@pytest.mark.asyncio
async def test_vector_store_search_applies_metadata_filters_and_expands_candidates():
    collection = FakeCollection(
        [
            FakeHit(
                "cpu markdown doc",
                {
                    "source": "cpu.md",
                    "title": "CPU 排障",
                    "doc_type": "markdown",
                    "section_path": "概述/排查步骤",
                    "timestamp": 1711900850,
                    "ingested_at": 1711900850,
                },
                score=0.9,
            ),
            FakeHit(
                "excel doc",
                {
                    "source": "metrics.xlsx",
                    "title": "指标报表",
                    "doc_type": "excel",
                    "sheet_name": "Sheet1",
                    "timestamp": 1711900851,
                    "ingested_at": 1711900851,
                },
                score=0.8,
            ),
        ]
    )
    store = VectorStore(
        FakeMilvusClient(collection),
        FakeEmbeddingService(),
        dense_top_k=2,
        enable_rerank=False,
        enable_hybrid=False,
    )

    docs = await store.search(
        "CPU 怎么排查",
        top_k=2,
        metadata_filters={
            "doc_type": "markdown",
            "title_contains": "CPU",
            "section_path_contains": "排查",
            "timestamp": 1711900850,
        },
    )

    assert collection.last_search_kwargs["limit"] == 30
    assert len(docs) == 1
    assert docs[0]["metadata"]["source"] == "cpu.md"


@pytest.mark.asyncio
async def test_vector_store_search_without_filters_uses_regular_candidate_limit():
    collection = FakeCollection(
        [
            FakeHit("doc1", {"source": "a.md", "doc_type": "markdown"}, score=0.9),
            FakeHit("doc2", {"source": "b.md", "doc_type": "markdown"}, score=0.8),
        ]
    )
    store = VectorStore(
        FakeMilvusClient(collection),
        FakeEmbeddingService(),
        dense_top_k=4,
        enable_rerank=False,
        enable_hybrid=False,
    )

    docs = await store.search("CPU 怎么排查", top_k=2)

    assert collection.last_search_kwargs["limit"] == 4
    assert len(docs) == 2
