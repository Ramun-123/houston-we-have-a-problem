from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

from extractors.error_parser import ErrorEvent
from extractors.utils_time import format_timestamp

logger = logging.getLogger(__name__)

def _format_summary(summary: Dict[str, Any]) -> str:
    lines: List[str] = []

    lines.append("=== Error Summary ===")
    lines.append(f"Total events: {summary.get('total_events', 0)}")
    lines.append("")

    lines.append("By severity:")
    for sev, count in sorted(
        summary.get("by_severity", {}).items(), key=lambda kv: kv[0]
    ):
        lines.append(f"  - {sev}: {count}")
    lines.append("")

    lines.append("By subsystem:")
    for sub, count in sorted(
        summary.get("by_subsystem", {}).items(), key=lambda kv: kv[0]
    ):
        lines.append(f"  - {sub}: {count}")
    lines.append("")

    lines.append("Top recurring error patterns:")
    patterns: Iterable[Dict[str, Any]] = summary.get("top_error_patterns", [])
    if not patterns:
        lines.append("  (none)")
    else:
        for entry in patterns:
            lines.append(
                f"  - {entry['subsystem']} / {entry['error_code']}: {entry['count']} occurrences"
            )

    lines.append("")
    lines.append("Unresolved errors by subsystem:")
    unresolved = summary.get("unresolved_by_subsystem", {})
    if not unresolved:
        lines.append("  All reported issues are marked as resolved.")
    else:
        for sub, count in sorted(unresolved.items(), key=lambda kv: kv[0]):
            lines.append(f"  - {sub}: {count} unresolved")

    return "\n".join(lines)

def _format_timeline(events: List[ErrorEvent]) -> str:
    if not events:
        return "No events recorded."

    # Sort by time ascending
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    lines: List[str] = []
    lines.append("=== Event Timeline (first 20 events) ===")

    for ev in sorted_events[:20]:
        ts = format_timestamp(ev.timestamp)
        status = "RESOLVED" if ev.resolved else "UNRESOLVED"
        lines.append(
            f"[{ts}] [{ev.severity}] [{status}] "
            f"{ev.subsystem} / {ev.error_code} - {ev.description}"
        )

    if len(sorted_events) > 20:
        lines.append(f"... {len(sorted_events) - 20} more events omitted for brevity.")

    return "\n".join(lines)

def generate_report(
    events: List[ErrorEvent], summary: Dict[str, Any], output_dir: Path
) -> Path:
    """
    Generate a human-readable text report.

    Returns the path to the generated report file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "error_report.txt"

    summary_section = _format_summary(summary)
    timeline_section = _format_timeline(events)

    content = "\n\n".join(
        [
            "HOUSTON, WE HAVE A PROBLEM! - ERROR REPORT",
            summary_section,
            timeline_section,
        ]
    )

    with report_path.open("w", encoding="utf-8") as f:
        f.write(content)

    logger.info("Report written to %s", report_path)
    return report_path