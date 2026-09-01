import os
import sys

# Make the project root importable when run as a script (python scripts/smoke_chat.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from atlas_mcp.config import load_settings
from atlas_mcp.odysseus_client import OdysseusClient

if __name__ == "__main__":
    c = OdysseusClient(load_settings())
    print(c.ask("In one sentence, what module is EN1213?"))
