from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .utils_time import parse_timestamp

logger = logging.getLogger(__name__)

@dataclass
class ErrorEvent:
    timestamp: "datetime.datetime"
    subsystem: str
    error_code: str
    severity: str
    description: str
    telemetry_id: str
    resolved: bool

def _normalize_severity(raw: Any, severity_levels: Dict[str, int]) -> str:
    if raw is None:
        return "UNKNOWN"

    text = str(raw).strip()
    if not text:
        return "UNKNOWN"

    key = text.upper()
    if key in severity_levels:
        return key

    # Simple mapping for common variants
    aliases = {
        "INFO": "LOW",
        "WARN": "MEDIUM",
        "WARNING": "MEDIUM",
        "ERR": "HIGH",
        "FATAL": "CRITICAL",
    }
    if key in aliases and aliases[key] in severity_levels:
        return aliases[key]

    return "UNKNOWN"

def parse_events(
    raw_events: List[Dict[str, Any]], config: Dict[str, Any]
) -> List[ErrorEvent]:
    """
    Convert raw telemetry objects into normalized ErrorEvent instances.
    """
    severity_levels: Dict[str, int] = {
        k.upper(): int(v)
        for k, v in config.get("severity_levels", {}).items()
    }

    parsed: List[ErrorEvent] = []
    for idx, raw in enumerate(raw_events):
        try:
            event = _parse_single(raw, severity_levels)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to parse event #%d: %s", idx, exc)
            continue
        parsed.append(event)

    return parsed

def _parse_single(raw: Dict[str, Any], severity_levels: Dict[str, int]) -> ErrorEvent:
    from datetime import datetime  # Imported here to avoid circular type hints

    ts_raw = raw.get("timestamp") or raw.get("time") or raw.get("ts")
    if ts_raw is None:
        raise ValueError("Missing timestamp field")

    timestamp = parse_timestamp(str(ts_raw))

    subsystem = str(raw.get("subsystem") or raw.get("module") or "UNKNOWN").strip()
    error_code = str(raw.get("error_code") or raw.get("code") or "UNKNOWN").strip()
    description = str(
        raw.get("description") or raw.get("message") or "No description provided"
    ).strip()
    telemetry_id = str(raw.get("telemetry_id") or raw.get("id") or "N/A").strip()

    severity_raw = raw.get("severity") or raw.get("level") or "UNKNOWN"
    severity = _normalize_severity(severity_raw, severity_levels)

    resolved_raw = raw.get("resolved")
    if isinstance(resolved_raw, bool):
        resolved = resolved_raw
    elif isinstance(resolved_raw, str):
        resolved = resolved_raw.strip().lower() in {"true", "1", "yes", "y"}
    else:
        resolved = False

    return ErrorEvent(
        timestamp=timestamp,
        subsystem=subsystem or "UNKNOWN",
        error_code=error_code or "UNKNOWN",
        severity=severity,
        description=description,
        telemetry_id=telemetry_id,
        resolved=resolved,
    )

def aggregate_events(events: List[ErrorEvent]) -> Dict[str, Any]:
    """
    Compute high-level statistics about the error stream.
    """
    by_severity: Counter[str] = Counter()
    by_subsystem: Counter[str] = Counter()
    error_pairs: Counter[Tuple[str, str]] = Counter()
    unresolved_by_subsystem: Dict[str, int] = defaultdict(int)

    for ev in events:
        by_severity[ev.severity] += 1
        by_subsystem[ev.subsystem] += 1
        error_pairs[(ev.subsystem, ev.error_code)] += 1
        if not ev.resolved:
            unresolved_by_subsystem[ev.subsystem] += 1

    top_error_patterns = [
        {
            "subsystem": sub,
            "error_code": code,
            "count": count,
        }
        for (sub, code), count in error_pairs.most_common(10)
    ]

    summary: Dict[str, Any] = {
        "total_events": len(events),
        "by_severity": dict(by_severity),
        "by_subsystem": dict(by_subsystem),
        "top_error_patterns": top_error_patterns,
        "unresolved_by_subsystem": dict(unresolved_by_subsystem),
    }

    logger.debug("Aggregation summary: %s", summary)
    return summary