thonimport logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class Notifier:
    """
    Simple notifier that logs high-severity issues.

    This is intentionally minimal but structured so you can later extend it
    to use Slack, email, or other channels without changing callers.
    """

    _SEVERITY_ORDER = {
        "info": 1,
        "warning": 2,
        "critical": 3,
    }

    def __init__(self, config: Dict[str, Any] | None = None):
        config = config or {}
        self.enabled: bool = config.get("enabled", True)
        self.min_severity: str = config.get("min_severity", "critical").lower()

    def _severity_score(self, severity: str | None) -> int:
        if not severity:
            return 0
        return self._SEVERITY_ORDER.get(severity.lower(), 0)

    def _threshold_score(self) -> int:
        return self._SEVERITY_ORDER.get(self.min_severity, 3)

    def notify(self, summary: Dict[str, Any], errors: List[Dict[str, Any]]) -> None:
        """
        Notify about high severity issues.

        Right now this just logs alerts to the Python logger, but the public
        interface is intentionally generic so that it can be wired to
        external services later.
        """
        if not self.enabled:
            logger.debug("Notifications are disabled; skipping notify() call.")
            return

        if not errors:
            logger.debug("No errors to notify about.")
            return

        threshold = self._threshold_score()
        flagged = [
            e
            for e in errors
            if self._severity_score(e.get("severity")) >= threshold
        ]

        if not flagged:
            logger.info(
                "No errors met the notification threshold (%s).",
                self.min_severity,
            )
            return

        # Build a concise alert message
        codes = {e.get("errorCode") for e in flagged if e.get("errorCode")}
        components = {e.get("systemComponent") for e in flagged if e.get("systemComponent")}
        message_lines = [
            "ALERT: High severity issues detected.",
            f"  Threshold: {self.min_severity}",
            f"  Matching errors: {len(flagged)}",
            f"  Affected components: {', '.join(sorted(components)) or 'n/a'}",
            f"  Error codes: {', '.join(sorted(codes)) or 'n/a'}",
        ]

        # Log as a warning so it surfaces but doesn't crash the program
        logger.warning("\n".join(message_lines))