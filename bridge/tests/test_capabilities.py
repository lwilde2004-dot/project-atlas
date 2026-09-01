"""Tests for the capability launcher exposed over MCP.

These tools are driven by an LLM, so the security property that matters most
is that only registered capabilities can ever be launched, with arguments
passed as a list (never through a shell).
"""
import pytest

from atlas_mcp import capabilities


def test_registry_contains_research():
    assert "research" in capabilities.CAPABILITIES


def test_build_command_uses_the_registered_script():
    cmd = capabilities.build_command("research", ["Beam bending"])
    assert cmd[0].endswith("python.exe") or cmd[0].endswith("python")
    assert cmd[1].endswith("atlas_research.py")
    assert "Beam bending" in cmd


def test_build_command_rejects_unknown_capability():
    with pytest.raises(ValueError, match="unknown capability"):
        capabilities.build_command("rm-rf", [])


def test_build_command_rejects_non_string_args():
    with pytest.raises(ValueError, match="string"):
        capabilities.build_command("research", [123])


def test_build_command_rejects_empty_arg():
    with pytest.raises(ValueError, match="empty"):
        capabilities.build_command("research", ["   "])


def test_launch_is_fire_and_forget(monkeypatch):
    """The MCP call must return immediately - claude -p runs take ~13 minutes."""
    called = {}

    class FakePopen:
        def __init__(self, cmd, **kwargs):
            called["cmd"] = cmd
            called["kwargs"] = kwargs
            self.pid = 4321

        def wait(self, *a, **k):  # pragma: no cover - must never be called
            raise AssertionError("launch() must not block on the child process")

    monkeypatch.setattr(capabilities.subprocess, "Popen", FakePopen)
    msg = capabilities.launch("research", ["Torsion in circular shafts"])

    assert "started" in msg.lower()
    assert "Torsion in circular shafts" in msg
    assert called["cmd"][1].endswith("atlas_research.py")
    # never through a shell
    assert called["kwargs"].get("shell", False) is False


def test_launch_rejects_unknown_capability():
    with pytest.raises(ValueError, match="unknown capability"):
        capabilities.launch("shutdown", [])


def test_status_reports_last_run_per_capability(tmp_path, monkeypatch):
    log = tmp_path / "atlas-capabilities.log"
    log.write_text(
        '{"capability": "research", "status": "ok", "detail": "wrote 7 notes", '
        '"started": "2026-08-30T22:26:57+01:00", "finished": "2026-08-30T22:40:08+01:00"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(capabilities, "CAPABILITY_LOG", log)
    out = capabilities.status()
    assert "research" in out
    assert "wrote 7 notes" in out
    assert "ok" in out


def test_status_handles_missing_log(tmp_path, monkeypatch):
    monkeypatch.setattr(capabilities, "CAPABILITY_LOG", tmp_path / "nope.log")
    assert "no capability runs" in capabilities.status().lower()
