"""
In-memory conversation store for multi-turn strategies (S3, S4).

Each session holds a capped list of Message dicts:
    [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]

Replace with a Redis or DB backend if persistence across restarts is needed.
"""
from collections import defaultdict
from app.models.schemas import Message
from app.config import get_settings


_sessions: dict[str, list[dict]] = defaultdict(list)


def get_history(session_id: str) -> list[Message]:
    return [Message(**m) for m in _sessions[session_id]]


def append_turn(session_id: str, user_query: str, assistant_answer: str) -> None:
    settings = get_settings()
    history = _sessions[session_id]
    history.append({"role": "user", "content": user_query})
    history.append({"role": "assistant", "content": assistant_answer})

    # Keep only the last N turns (each turn = 1 user + 1 assistant message)
    max_messages = settings.max_history_turns * 2
    if len(history) > max_messages:
        _sessions[session_id] = history[-max_messages:]


def clear_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def session_length(session_id: str) -> int:
    """Returns number of (user, assistant) turn pairs retained."""
    return len(_sessions[session_id]) // 2
