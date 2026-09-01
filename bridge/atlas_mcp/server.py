import logging, os
from mcp.server.fastmcp import FastMCP
from atlas_mcp.config import load_settings
from atlas_mcp.odysseus_client import OdysseusClient
from atlas_mcp import capabilities

LOG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "atlas-mcp.log")
logging.basicConfig(filename=LOG, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

mcp = FastMCP("atlas")
_settings = load_settings()
_client = OdysseusClient(_settings)

@mcp.tool()
def atlas_ask(question: str) -> str:
    """Answer a question using Lewis's Project Atlas notes (Odysseus RAG + qwen3:8b).
    Use this for ANY question about his studies, modules, notes, or knowledge."""
    logging.info("atlas_ask: %s", question[:200])
    try:
        return _client.ask(question)
    except Exception as e:
        logging.exception("atlas_ask failed")
        return f"(atlas error: {e})"

@mcp.tool()
def atlas_research(topic: str, into: str = "") -> str:
    """Run DEEP RESEARCH on a topic using Claude on Lewis's desktop, writing a
    structured set of linked Markdown notes into his Obsidian vault.

    Use this when he asks to research, read up on, or write notes about a
    subject - not for quick questions (use atlas_ask for those).

    This is slow (roughly 10-15 minutes) and runs in the background, so it
    returns as soon as the run has STARTED. Tell him it is running and that
    the notes will appear in his vault; do not wait for a result. Use
    atlas_capability_status later to check whether it finished.

    topic: what to research, e.g. "Second moment of area for beam bending"
    into:  optional vault-relative output folder; leave blank for the default
    """
    logging.info("atlas_research: %s (into=%s)", topic[:200], into)
    try:
        args = [topic] + (["--into", into] if into.strip() else [])
        return capabilities.launch("research", args)
    except Exception as e:
        logging.exception("atlas_research failed")
        return f"(atlas error: {e})"


@mcp.tool()
def atlas_capability_status() -> str:
    """Report how the last run of each Atlas background capability finished
    (e.g. research, vault-sync). Use this to check whether a research run he
    started earlier has completed, or to explain why one failed."""
    logging.info("atlas_capability_status")
    try:
        return capabilities.status()
    except Exception as e:
        logging.exception("atlas_capability_status failed")
        return f"(atlas error: {e})"


@mcp.tool()
def atlas_sync_vault() -> str:
    """Commit and push Lewis's Obsidian vault to GitHub straight away, instead
    of waiting for the automatic 18:00 run. Use when he asks to save, back up,
    push, or sync his notes."""
    logging.info("atlas_sync_vault")
    try:
        return capabilities.launch("vault-sync", [])
    except Exception as e:
        logging.exception("atlas_sync_vault failed")
        return f"(atlas error: {e})"


if __name__ == "__main__":
    mcp.run()   # stdio transport
