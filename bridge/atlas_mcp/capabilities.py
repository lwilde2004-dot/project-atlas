"""Launch Atlas capabilities from the MCP bridge.

This is the piece that turns Odysseus from something Lewis queries into
something he deploys work from: a capability named in chat (on his phone,
over Tailscale) is launched as a headless process on the desktop, which
writes Markdown into the Cortex vault.

Two design constraints shape this module:

1. **Fire and forget.** A `claude -p` research run takes ~13 minutes. An MCP
   tool call cannot wait that long, so `launch()` spawns a detached child and
   returns immediately. Completion is reported through the capability log
   (tools/atlas/capability.py) and the 07:30 briefing, not through the return
   value.

2. **Strict allowlist.** These tools are driven by an LLM. Only capabilities
   registered in CAPABILITIES can be launched, arguments are always passed as
   a list, and a shell is never used. There is deliberately no "run arbitrary
   command" escape hatch.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ATLAS_TOOLS = Path(os.environ.get("ATLAS_TOOLS_DIR", r"C:\Project Atlas\tools\atlas"))
PYTHON = Path(os.environ.get(
    "ATLAS_PYTHON",
    r"C:\Project Atlas\tools\automation-venv\Scripts\python.exe",
))
CAPABILITY_LOG = ATLAS_TOOLS / "atlas-capabilities.log"

# name -> script. Adding a capability here is the whole integration step;
# everything else (logging, exit codes, briefing visibility) comes from
# capability.run_capability() inside the script itself.
CAPABILITIES: dict[str, Path] = {
    "research": ATLAS_TOOLS / "atlas_research.py",
    "vault-sync": ATLAS_TOOLS / "vault_sync.py",
}


def build_command(name: str, args: list[str]) -> list[str]:
    """Return the argv for a registered capability. Raises on anything else."""
    script = CAPABILITIES.get(name)
    if script is None:
        raise ValueError(
            f"unknown capability {name!r}; registered: {sorted(CAPABILITIES)}"
        )
    for a in args:
        if not isinstance(a, str):
            raise ValueError(f"capability arguments must be string, got {type(a).__name__}")
        if not a.strip():
            raise ValueError("capability arguments must not be empty")
    return [str(PYTHON), str(script), *args]


def launch(name: str, args: list[str]) -> str:
    """Start a capability in the background and return immediately."""
    cmd = build_command(name, args)
    creationflags = 0
    if sys.platform == "win32":
        # Detach so the child outlives this MCP call and never opens a console.
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(
            subprocess, "DETACHED_PROCESS", 0
        )
    subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
        creationflags=creationflags,
    )
    detail = " ".join(args) if args else "(no arguments)"
    return (
        f"Capability '{name}' started on the desktop with: {detail}. "
        "It runs in the background - check back in a few minutes, or ask for "
        "capability status. Results are written into the vault."
    )


def status() -> str:
    """Human-readable summary of the last run of each capability."""
    if not CAPABILITY_LOG.exists():
        return "No capability runs recorded yet."
    latest: dict[str, dict] = {}
    for line in CAPABILITY_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        latest[entry.get("capability", "?")] = entry
    if not latest:
        return "No capability runs recorded yet."
    lines = []
    for name, e in sorted(latest.items()):
        lines.append(
            f"{name}: {e.get('status')} - {e.get('detail')} "
            f"(finished {e.get('finished')})"
        )
    return "\n".join(lines)
