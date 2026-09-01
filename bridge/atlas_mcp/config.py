import os
from dataclasses import dataclass

DEFAULT_ENV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

def _read_env_file(key, env_file):
    if not os.path.isfile(env_file):
        return None
    with open(env_file, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    return None

def _get(key, env_file, default=None):
    return os.environ.get(key) or _read_env_file(key, env_file) or default

@dataclass
class Settings:
    base_url: str
    user: str
    password: str
    endpoint_id: str
    model: str
    rag: str
    bot_token: str
    allowed_id: int

def load_settings(env_file: str = DEFAULT_ENV) -> Settings:
    allowed = _get("TELEGRAM_ALLOWED_ID", env_file, "0")
    return Settings(
        base_url=_get("ODYSSEUS_URL", env_file, "http://localhost:7000"),
        user=_get("ODYSSEUS_USER", env_file, "lewis"),
        password=_get("ODYSSEUS_PASSWORD", env_file, ""),
        # Default is the Ollama endpoint created in the 2026-08-30 rebuild;
        # the old install's "74501faf" no longer exists.
        endpoint_id=_get("ATLAS_ENDPOINT_ID", env_file, "1b6ab8ef"),
        model=_get("ATLAS_MODEL", env_file, "qwen3:8b"),
        rag=_get("ATLAS_RAG", env_file, "true"),
        bot_token=_get("TELEGRAM_BOT_TOKEN", env_file, ""),
        allowed_id=int(allowed or "0"),
    )
