thonfrom __future__ import annotations

import json
from typing import Any, Dict, List

def build_json_report(
    *,
    errors: List[Dict[str, Any]],
    summary: Dict[str, Any],
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Build a structured JSON-serializable report combining raw errors,
    summary statistics, and optional metadata.
    """
    metadata = metadata or {}
    report: Dict[str, Any] = {
        "metadata": metadata,
        "summary": summary,
        "errors": errors,
    }
    return report

def format_summary_text(summary: Dict[str, Any]) -> str:
    """
    Build a short human-readable summary string from the summary document.
    """
    total = summary.get("total", 0)
    by_severity = summary.get("by_severity", {})
    by_component = summary.get("by_component", {})

    lines = []
    lines.append("Houston, We Have a Problem! – Summary")
    lines.append("=" * 46)
    lines.append(f"Total errors: {total}")

    if by_severity:
        lines.append("\nBy severity:")
        for sev, count in sorted(by_severity.items(), key=lambda x: x[0]):
            lines.append(f"  - {sev}: {count}")

    if by_component:
        lines.append("\nBy component:")
        for comp, count in sorted(by_component.items(), key=lambda x: x[0]):
            lines.append(f"  - {comp}: {count}")

    recurring = summary.get("recurring_errors") or []
    if recurring:
        lines.append("\nRecurring errors (top 3):")
        for item in recurring[:3]:
            code = item.get("errorCode")
            count = item.get("count")
            msg = item.get("sampleMessage") or ""
            preview = msg[:60] + ("..." if len(msg) > 60 else "")
            lines.append(f"  - {code} (x{count}): {preview}")

    return "\n".join(lines)

def pretty_print_report(report: Dict[str, Any]) -> str:
    """
    Optional helper to pretty-print the full JSON report.
    Not used by main.py but available for interactive usage.
    """
    return json.dumps(report, indent=2, sort_keys=True)