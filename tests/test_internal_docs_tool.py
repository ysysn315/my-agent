import pytest

from app.agents.tools.internal_docs_tool import create_docs_tool


class FakeRAGRetriever:
    def __init__(self):
        self.calls = []

    async def retrieve_multi_query(self, query, top_k=3, metadata_filters=None):
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
                "metadata_filters": metadata_filters,
            }
        )
        return [
            {
                "content": "cpu troubleshooting steps",
                "metadata": {
                    "source": "cpu.md",
                    "title": "CPU Guide",
                    "doc_type": "markdown",
                    "timestamp": 1711900850,
                },
            }
        ]


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
        return []


@pytest.mark.asyncio
async def test_docs_tool_prefers_multi_query_retriever():
    retriever = FakeRAGRetriever()
    tool = create_docs_tool(retriever)

    result = await tool.ainvoke(
        {
            "query": "how to troubleshoot cpu",
            "doc_type": "markdown",
            "timestamp_from": 1711900800,
        }
    )

    assert "cpu troubleshooting steps" in result
    assert retriever.calls == [
        {
            "query": "how to troubleshoot cpu",
            "top_k": 3,
            "metadata_filters": {
                "doc_type": "markdown",
                "title": None,
                "title_contains": None,
                "source": None,
                "section_path": None,
                "section_path_contains": None,
                "sheet_name": None,
                "timestamp": None,
                "ingested_at_from": None,
                "ingested_at_to": None,
                "timestamp_from": 1711900800,
                "timestamp_to": None,
            },
        }
    ]


@pytest.mark.asyncio
async def test_docs_tool_falls_back_to_vector_store_search():
    vector_store = FakeVectorStore()
    tool = create_docs_tool(vector_store)

    result = await tool.ainvoke({"query": "how to troubleshoot cpu"})

    assert result == "未找到相关文档"
    assert vector_store.calls == [
        {
            "query": "how to troubleshoot cpu",
            "top_k": 3,
            "metadata_filters": {
                "doc_type": None,
                "title": None,
                "title_contains": None,
                "source": None,
                "section_path": None,
                "section_path_contains": None,
                "sheet_name": None,
                "timestamp": None,
                "ingested_at_from": None,
                "ingested_at_to": None,
                "timestamp_from": None,
                "timestamp_to": None,
            },
        }
    ]
