import pytest
from unittest.mock import MagicMock
from atlas_mcp.config import Settings
from atlas_mcp.odysseus_client import OdysseusClient

def _settings():
    return Settings(base_url="http://x", user="lewis", password="pw",
                    endpoint_id="74501faf", model="qwen3:8b", rag="true",
                    bot_token="", allowed_id=1)

def _resp(status=200, json_data=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = json_data or {}
    return r

def test_ask_logs_in_creates_session_then_chats():
    http = MagicMock()
    http.post.side_effect = [
        _resp(200, {"ok": True}),                       # /api/auth/login
        _resp(200, {"session": "sess-1"}),              # /api/session
        _resp(200, {"response": "Entropy is..."}),      # /api/chat
    ]
    c = OdysseusClient(_settings(), http=http)
    out = c.ask("explain entropy")
    assert out == "Entropy is..."
    login_call, sess_call, chat_call = http.post.call_args_list
    assert login_call.args[0].endswith("/api/auth/login")
    assert sess_call.args[0].endswith("/api/session")
    # session-create must bind to the endpoint and skip the stale model-cache check
    assert sess_call.kwargs["data"]["endpoint_id"] == "74501faf"
    assert sess_call.kwargs["data"]["skip_validation"] == "true"
    assert chat_call.args[0].endswith("/api/chat")
    assert chat_call.kwargs["json"]["session"] == "sess-1"
    assert chat_call.kwargs["json"]["message"] == "explain entropy"

def test_ask_reuses_cached_session():
    http = MagicMock()
    http.post.side_effect = [
        _resp(200, {"ok": True}),
        _resp(200, {"session": "sess-1"}),
        _resp(200, {"response": "A"}),
        _resp(200, {"response": "B"}),                  # 2nd ask: no new login/session
    ]
    c = OdysseusClient(_settings(), http=http)
    assert c.ask("q1") == "A"
    assert c.ask("q2") == "B"
    assert http.post.call_count == 4

def test_ask_recreates_session_on_404():
    http = MagicMock()
    http.post.side_effect = [
        _resp(200, {"ok": True}),
        _resp(200, {"session": "sess-1"}),
        _resp(404, {"detail": "not found"}),            # chat: session gone
        _resp(200, {"session": "sess-2"}),              # recreate session
        _resp(200, {"response": "recovered"}),          # retry chat
    ]
    c = OdysseusClient(_settings(), http=http)
    assert c.ask("q") == "recovered"

def test_login_failure_raises():
    http = MagicMock()
    http.post.side_effect = [_resp(401, {"detail": "bad creds"})]
    c = OdysseusClient(_settings(), http=http)
    with pytest.raises(RuntimeError, match="login failed"):
        c.ask("q")
