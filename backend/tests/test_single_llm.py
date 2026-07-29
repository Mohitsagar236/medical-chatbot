"""Tests for S1 Single LLM."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.routers.single_llm.llm_service.ask_single")
def test_single_llm_returns_answer(mock_ask):
    mock_ask.return_value = {
        "answer": "Hypertension is persistently elevated blood pressure.",
        "model": "llama-3.3-70b-versatile",
        "prompt_tokens": 10,
        "completion_tokens": 8,
    }

    response = client.post("/api/v1/chat/single-llm/", json={"query": "What is hypertension?"})

    assert response.status_code == 200
    data = response.json()
    assert data["strategy"] == "S1-single-llm"
    assert data["answer"] == "Hypertension is persistently elevated blood pressure."
    mock_ask.assert_called_once_with("What is hypertension?")


def test_single_llm_empty_query():
    response = client.post("/api/v1/chat/single-llm/", json={"query": ""})
    assert response.status_code == 422


@patch("app.routers.single_llm.llm_service.ask_single", side_effect=Exception("Groq API down"))
def test_single_llm_failure_returns_500(_mock_ask):
    response = client.post("/api/v1/chat/single-llm/", json={"query": "What is hypertension?"})
    assert response.status_code == 500
