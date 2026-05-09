from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_chat import get_chat_service, router


class FakeChatService:
    def __init__(self):
        self.calls = []

    async def chat(self, session_id: str, question: str, metadata_filters=None):
        self.calls.append(
            {
                "session_id": session_id,
                "question": question,
                "metadata_filters": metadata_filters,
            }
        )
        return {"answer": "ok", "sources": ["cpu.md"]}


def test_chat_route_passes_metadata_filters_to_service():
    app = FastAPI()
    app.include_router(router, prefix="/api")

    fake_service = FakeChatService()
    app.dependency_overrides[get_chat_service] = lambda: fake_service
    client = TestClient(app)

    response = client.post(
        "/api/chat",
        json={
            "Id": "session-1",
            "Question": "这个怎么处理？",
            "metadata_filters": {
                "doc_type": "markdown",
                "title_contains": "CPU",
                "timestamp": 1711900850,
                "timestamp_from": 1711900800,
                "timestamp_to": 1711900900,
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "ok", "sources": ["cpu.md"]}
    assert fake_service.calls == [
        {
            "session_id": "session-1",
            "question": "这个怎么处理？",
            "metadata_filters": {
                "doc_type": "markdown",
                "title_contains": "CPU",
                "timestamp": 1711900850,
                "timestamp_from": 1711900800,
                "timestamp_to": 1711900900,
            },
        }
    ]
