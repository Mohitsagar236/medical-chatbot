"""Tests for S2 Single RAG."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.vector_store import get_vector_store
from app.main import app
from app.models.schemas import RetrievedChunk

client = TestClient(app)


def test_single_rag_empty_query():
    response = client.post("/api/v1/chat/single-rag/", json={"query": ""})
    assert response.status_code == 422


def test_single_rag_top_k_too_low():
    response = client.post("/api/v1/chat/single-rag/", json={"query": "hypertension", "top_k": 0})
    assert response.status_code == 422


def test_single_rag_top_k_too_high():
    response = client.post("/api/v1/chat/single-rag/", json={"query": "hypertension", "top_k": 21})
    assert response.status_code == 422


@patch("app.routers.single_rag.run_s2")
def test_single_rag_success(mock_run_s2):
    fake_store = object()
    app.dependency_overrides[get_vector_store] = lambda: fake_store
    mock_run_s2.return_value = {
        "answer": "Metformin is the first-line treatment.",
        "model": "llama-3.3-70b-versatile",
        "prompt_tokens": 100,
        "completion_tokens": 25,
        "chunks": [RetrievedChunk(content="Metformin is first-line therapy.", source="12345", score=0.87)],
    }

    try:
        response = client.post("/api/v1/chat/single-rag/", json={"query": "How is diabetes treated?", "top_k": 3})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["strategy"] == "S2-single-rag"
    assert data["answer"] == "Metformin is the first-line treatment."
    assert data["retrieved_chunks"][0]["source"] == "12345"
    mock_run_s2.assert_called_once_with("How is diabetes treated?", fake_store, 3)


@patch("app.routers.single_rag.run_s2", side_effect=Exception("Groq API down"))
def test_single_rag_failure_returns_500(_mock_run_s2):
    app.dependency_overrides[get_vector_store] = lambda: object()
    try:
        response = client.post("/api/v1/chat/single-rag/", json={"query": "What is cancer?"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
