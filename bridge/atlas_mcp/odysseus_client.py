import requests
from atlas_mcp.config import Settings

class OdysseusClient:
    def __init__(self, settings: Settings, http=None):
        self.s = settings
        self.http = http or requests.Session()
        self._logged_in = False
        self._session_id = None

    def _login(self):
        r = self.http.post(f"{self.s.base_url}/api/auth/login",
                           json={"username": self.s.user, "password": self.s.password})
        if r.status_code != 200:
            raise RuntimeError(f"Odysseus login failed ({r.status_code})")
        self._logged_in = True

    def _create_session(self):
        r = self.http.post(
            f"{self.s.base_url}/api/session",
            # skip_validation bypasses Odysseus's cached model-list check, which
            # can lag behind Ollama (e.g. qwen3:8b present in Ollama but not yet
            # in the endpoint's cache). The session still binds to the real
            # enabled endpoint_id, so chat works regardless of cache freshness.
            data={"endpoint_id": self.s.endpoint_id, "model": self.s.model,
                  "name": "atlas-telegram", "rag": self.s.rag,
                  "skip_validation": "true"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"session create failed ({r.status_code})")
        data = r.json()
        self._session_id = data.get("session") or data.get("id")
        if not self._session_id:
            raise RuntimeError("session create returned no id")

    def _ensure(self):
        if not self._logged_in:
            self._login()
        if not self._session_id:
            self._create_session()

    def ask(self, message: str) -> str:
        self._ensure()
        r = self.http.post(f"{self.s.base_url}/api/chat",
                           json={"message": message, "session": self._session_id})
        if r.status_code == 404:                 # session expired/cleared — recreate once
            self._session_id = None
            self._create_session()
            r = self.http.post(f"{self.s.base_url}/api/chat",
                               json={"message": message, "session": self._session_id})
        if r.status_code != 200:
            raise RuntimeError(f"chat failed ({r.status_code})")
        return r.json().get("response", "")
