from typing import Any, Dict
import requests

class WebhookNotifier:
    def __init__(self, url: str, enabled: bool = False, timeout: int = 8) -> None:
        self.url = url
        self.enabled = enabled
        self.timeout = timeout

    def post(self, payload: Dict[str, Any]) -> bool:
        if not self.enabled or not self.url:
            return False
        try:
            resp = requests.post(self.url, json=payload, timeout=self.timeout)
            return 200 <= resp.status_code < 300
        except Exception:
            return False