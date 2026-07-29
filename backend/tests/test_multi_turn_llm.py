"""Tests for S3 Multi-Turn LLM."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.conversation_store import clear_session

client = TestClient(app)


@patch("app.routers.multi_turn_llm.run_s3")
def test_multi_turn_llm_returns_answer(mock_run_s3):
    clear_session("test-session-1")
    mock_run_s3.return_value = {
        "answer": "Hypertension is persistently elevated blood pressure.",
        "model": "llama-3.3-70b-versatile",
        "prompt_tokens": 10,
        "completion_tokens": 8,
        "condensed_query": "What is hypertension?",
    }

    response = client.post(
        "/api/v1/chat/multi-turn-llm/",
        json={"session_id": "test-session-1", "query": "What is hypertension?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["strategy"] == "S3-multi-turn-llm"
    assert data["session_id"] == "test-session-1"
    assert data["history_length"] == 1


@patch("app.routers.multi_turn_llm.run_s3")
def test_multi_turn_llm_memory(mock_run_s3):
    session_id = "test-session-memory"
    clear_session(session_id)
    result = {
        "answer": "Answer.",
        "model": "llama-3.3-70b-versatile",
        "prompt_tokens": 10,
        "completion_tokens": 8,
        "condensed_query": "Condensed question.",
    }
    mock_run_s3.side_effect = lambda *_args: dict(result)

    client.post(
        "/api/v1/chat/multi-turn-llm/",
        json={"session_id": session_id, "query": "What is hypertension?"},
    )
    response = client.post(
        "/api/v1/chat/multi-turn-llm/",
        json={"session_id": session_id, "query": "What medications are used to treat it?"},
    )

    assert response.status_code == 200
    assert response.json()["history_length"] == 2
    assert response.json()["session_id"] == session_id


@patch("app.routers.multi_turn_llm.run_s3")
def test_multi_turn_llm_independent_sessions(mock_run_s3):
    clear_session("session-a")
    clear_session("session-b")
    result = {
        "answer": "Answer.",
        "model": "llama-3.3-70b-versatile",
        "prompt_tokens": 10,
        "completion_tokens": 8,
        "condensed_query": "Condensed question.",
    }
    mock_run_s3.side_effect = lambda *_args: dict(result)

    client.post(
        "/api/v1/chat/multi-turn-llm/",
        json={"session_id": "session-a", "query": "What is diabetes?"},
    )
    response = client.post(
        "/api/v1/chat/multi-turn-llm/",
        json={"session_id": "session-b", "query": "What is hypertension?"},
    )

    assert response.status_code == 200
    assert response.json()["history_length"] == 1


def test_clear_session():
    session_id = "test-session-clear"
    response = client.delete(f"/api/v1/chat/multi-turn-llm/{session_id}")
    assert response.status_code == 204
