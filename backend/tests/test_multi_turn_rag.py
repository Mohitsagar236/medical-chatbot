"""Tests for S4 Multi-Turn RAG."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.vector_store import get_vector_store
from app.main import app
from app.models.schemas import RetrievedChunk
from app.services.conversation_store import clear_session

client = TestClient(app)


@patch("app.routers.multi_turn_rag.run_s4")
def test_multi_turn_rag_returns_answer(mock_run_s4):
    session_id = "test-session-rag"
    fake_store = object()
    clear_session(session_id)
    app.dependency_overrides[get_vector_store] = lambda: fake_store
    mock_run_s4.return_value = {
        "answer": "ACE inhibitors are commonly used.",
        "prompt_tokens": 100,
        "completion_tokens": 25,
        "chunks": [RetrievedChunk(content="ACE inhibitor context.", source="12345", score=0.91)],
    }

    try:
        response = client.post(
            "/api/v1/chat/multi-turn-rag/",
            json={"session_id": session_id, "query": "How is hypertension treated?", "top_k": 3},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["strategy"] == "S4-multi-turn-rag"
    assert data["session_id"] == session_id
    assert data["history_length"] == 1
    assert data["retrieved_chunks"][0]["source"] == "12345"
    mock_run_s4.assert_called_once()


def test_multi_turn_rag_empty_query():
    response = client.post(
        "/api/v1/chat/multi-turn-rag/",
        json={"session_id": "test-session-1", "query": ""},
    )
    assert response.status_code == 422


def test_clear_session():
    response = client.delete("/api/v1/chat/multi-turn-rag/test-session-1")
    assert response.status_code == 204
