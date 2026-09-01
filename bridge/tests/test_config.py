import os
from atlas_mcp.config import load_settings

def test_load_settings_prefers_env(monkeypatch, tmp_path):
    monkeypatch.setenv("ODYSSEUS_PASSWORD", "envpw")
    monkeypatch.setenv("TELEGRAM_ALLOWED_ID", "12345")
    s = load_settings(env_file=str(tmp_path / "nope.env"))
    assert s.password == "envpw"
    assert s.allowed_id == 12345
    assert s.base_url == "http://localhost:7000"   # default
    assert s.model == "qwen3:8b"                    # default

def test_load_settings_reads_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("ODYSSEUS_PASSWORD", raising=False)
    f = tmp_path / "a.env"
    f.write_text('ODYSSEUS_PASSWORD="filepw"\nTELEGRAM_ALLOWED_ID=999\n', encoding="utf-8")
    s = load_settings(env_file=str(f))
    assert s.password == "filepw"
    assert s.allowed_id == 999
