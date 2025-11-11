from typing import Dict, Any, List
from pathlib import Path

from .formatter import normalize
from .storage import Storage
from ..alerts.email_notifier import EmailNotifier
from ..alerts.webhook_notifier import WebhookNotifier

class ErrorHandler:
    """
    High-level API to ingest normalized events, persist them, and emit alerts based on thresholds.
    """

    def __init__(
        self,
        storage: Storage,
        email_notifier: EmailNotifier | None = None,
        webhook_notifier: WebhookNotifier | None = None,
        thresholds: dict | None = None,
    ) -> None:
        self.storage = storage
        self.email_notifier = email_notifier
        self.webhook_notifier = webhook_notifier
        self.thresholds = thresholds or {"critical": 1, "error": 10, "warning": 50}

        self._counters = {"critical": 0, "error": 0, "warning": 0, "info": 0}

    def ingest(self, event: Dict[str, Any]) -> Dict[str, Any]:
        ev = normalize(event)
        self.storage.write_event(ev)
        sev = ev["severity"]
        self._counters[sev] = self._counters.get(sev, 0) + 1

        # Check alert thresholds
        threshold = self.thresholds.get(sev)
        if threshold is not None and self._counters[sev] >= threshold:
            self._emit_alert(sev, ev)
            # reset the counter after emitting alert to avoid spamming
            self._counters[sev] = 0

        return ev

    def ingest_many(self, events: List[Dict[str, Any]]) -> int:
        count = 0
        for e in events:
            self.ingest(e)
            count += 1
        return count

    def _emit_alert(self, severity: str, last_event: Dict[str, Any]) -> None:
        title = f"[Houston] {severity.upper()} threshold reached"
        body = (
            f"Severity: {severity}\n"
            f"Last event at: {last_event['timestamp']}\n"
            f"Type: {last_event['errorType']}\n"
            f"Message: {last_event['message']}\n"
            f"Source: {last_event['sourceFile']}:{last_event['lineNumber']}\n"
            f"Environment: {last_event['environment']}\n"
        )
        payload = {
            "title": title,
            "severity": severity,
            "last_event": last_event,
            "counters": self._counters,
        }
        if self.email_notifier:
            self.email_notifier.send(subject=title, body=body)
        if self.webhook_notifier:
            self.webhook_notifier.post(payload)