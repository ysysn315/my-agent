import pytest

from app.rag.metadata_filters import build_base_metadata, matches_metadata_filters
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

    def search(self, **kwargs):
        return [self.hits]


class FakeMilvusClient:
    def __init__(self, collection):
        self.collection = collection


def test_build_base_metadata_preserves_explicit_zero_timestamp():
    metadata = build_base_metadata("epoch.md", ingested_at=0)

    assert metadata["ingested_at"] == 0
    assert metadata["timestamp"] == 0


def test_matches_metadata_filters_returns_false_for_invalid_numeric_values():
    metadata = {
        "source": "cpu.md",
        "title": "CPU Guide",
        "timestamp": "bad-value",
        "ingested_at": "bad-value",
    }

    assert not matches_metadata_filters(metadata, {"timestamp": 1711900850})
    assert not matches_metadata_filters(metadata, {"ingested_at_from": 1711900800})


@pytest.mark.asyncio
async def test_vector_store_search_tolerates_invalid_numeric_metadata_rows():
    collection = FakeCollection(
        [
            FakeHit(
                "bad metadata row",
                {
                    "source": "bad.md",
                    "title": "Bad Row",
                    "doc_type": "markdown",
                    "timestamp": "broken",
                    "ingested_at": "broken",
                },
                score=0.95,
            ),
            FakeHit(
                "good metadata row",
                {
                    "source": "good.md",
                    "title": "Good Row",
                    "doc_type": "markdown",
                    "timestamp": 1711900850,
                    "ingested_at": 1711900850,
                },
                score=0.90,
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
        "cpu guide",
        top_k=2,
        metadata_filters={"timestamp": 1711900850},
    )

    assert [doc["metadata"]["source"] for doc in docs] == ["good.md"]
