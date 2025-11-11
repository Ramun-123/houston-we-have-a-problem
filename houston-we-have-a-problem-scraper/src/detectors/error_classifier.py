import logging
from typing import Any, Dict, Iterable, List, Mapping

logger = logging.getLogger(__name__)

DEFAULT_SEVERITY_MAPPING = {
    "CRITICAL": "critical",
    "FATAL": "critical",
    "PANIC": "critical",
    "ERROR": "error",
    "ERR": "error",
    "WARN": "warning",
    "WARNING": "warning",
    "INFO": "info",
    "DEBUG": "low",
    "TRACE": "low",
}

def _normalize_severity(
    level: str,
    message: str,
    code: str,
    mapping: Mapping[str, str],
) -> str:
    # Code-based overrides first
    code_upper = code.upper()
    if code_upper.startswith("CRIT"):
        return "critical"
    if code_upper.startswith("WARN"):
        return "warning"

    # Explicit mapping based on level
    if level.upper() in mapping:
        return mapping[level.upper()]

    # Keyword-based heuristics
    text = f"{message} {code}".lower()
    if any(k in text for k in ("timeout", "unreachable", "data loss", "corruption")):
        return "critical"
    if any(k in text for k in ("exception", "failed", "failure", "error")):
        return "error"
    if any(k in text for k in ("deprecated", "slow", "retry")):
        return "warning"

    return "info"

def classify_errors(
    entries: Iterable[Dict[str, Any]],
    severity_mapping: Mapping[str, str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Classify severity of parsed log entries.

    Adds/overwrites the 'severity' field on each entry with normalized values:
        info, low, warning, error, critical
    """
    mapping = {**DEFAULT_SEVERITY_MAPPING}
    if severity_mapping:
        # Allow user overrides
        for k, v in severity_mapping.items():
            mapping[k.upper()] = v.lower()

    results: List[Dict[str, Any]] = []
    for entry in entries:
        level = entry.get("rawLevel") or entry.get("severity") or "INFO"
        message = entry.get("errorMessage", "")
        code = entry.get("errorCode", "")
        severity = _normalize_severity(level, message, code, mapping)
        new_entry = dict(entry)
        new_entry["severity"] = severity
        results.append(new_entry)

    logger.debug("Classified %d entries", len(results))
    return results