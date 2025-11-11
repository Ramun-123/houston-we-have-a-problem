thonimport logging
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

def _parse_timestamp(ts: str) -> datetime:
    """Attempt to parse ISO or common timestamp formats."""
    if not isinstance(ts, str):
        raise ValueError("Timestamp must be a string.")

    # Try a couple of formats
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S,%f",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(ts[:26], fmt)
        except ValueError:
            continue

    # Fall back to current time but log a warning
    logger.warning("Could not parse timestamp '%s'; using current time.", ts)
    return datetime.utcnow()

def _latest_errors(errors: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    """Return the N most recent errors, preserving core fields."""
    sorted_errors = sorted(
        errors,
        key=lambda e: _parse_timestamp(e.get("timestamp", "")),
        reverse=True,
    )
    latest = []
    for e in sorted_errors[:limit]:
        latest.append(
            {
                "errorCode": e.get("errorCode"),
                "errorMessage": e.get("errorMessage"),
                "timestamp": e.get("timestamp"),
                "systemComponent": e.get("systemComponent"),
                "severity": e.get("severity"),
                "logUrl": e.get("logUrl"),
            }
        )
    return latest

def _recurring_errors(errors: List[Dict[str, Any]], min_count: int = 2) -> List[Dict[str, Any]]:
    """
    Identify recurring errors by errorCode. Returns list of dicts
    with errorCode, count, and sample message.
    """
    code_counter = Counter()
    sample_message = {}

    for e in errors:
        code = e.get("errorCode") or "UNKNOWN"
        code_counter[code] += 1
        if code not in sample_message:
            sample_message[code] = e.get("errorMessage")

    recurring = []
    for code, count in code_counter.items():
        if count >= min_count:
            recurring.append(
                {
                    "errorCode": code,
                    "count": count,
                    "sampleMessage": sample_message.get(code),
                }
            )

    # Sort by count descending
    recurring.sort(key=lambda x: x["count"], reverse=True)
    return recurring

def analyze_errors(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze a list of error documents and produce a summary.

    The summary includes:
      - total: total number of errors
      - by_severity: counts per severity
      - by_component: counts per systemComponent
      - recurring_errors: list of recurring error codes
      - latest_errors: list of most recent errors
    """
    summary: Dict[str, Any] = {
        "total": len(errors),
        "by_severity": {},
        "by_component": {},
        "recurring_errors": [],
        "latest_errors": [],
    }

    if not errors:
        logger.info("No errors to analyze.")
        return summary

    severity_counts: Counter = Counter()
    component_counts: Counter = Counter()

    for e in errors:
        severity = (e.get("severity") or "unknown").lower()
        component = e.get("systemComponent") or "unknown"

        severity_counts[severity] += 1
        component_counts[component] += 1

    summary["by_severity"] = dict(severity_counts)
    summary["by_component"] = dict(component_counts)
    summary["recurring_errors"] = _recurring_errors(errors)
    summary["latest_errors"] = _latest_errors(errors)

    logger.debug("Summary by severity: %s", summary["by_severity"])
    logger.debug("Summary by component: %s", summary["by_component"])
    logger.info(
        "Analysis complete: %d errors across %d components.",
        summary["total"],
        len(component_counts),
    )

    return summary