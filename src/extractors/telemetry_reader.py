from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

logger = logging.getLogger(__name__)

def _read_json_array(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Common pattern: {"records": [...]} or {"events": [...]}
        for key in ("records", "events", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]  # type: ignore[return-value]
    raise ValueError(f"Unsupported JSON structure in {path}")

def _read_json_lines(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "Skipping invalid JSON line %d in %s: %s", line_no, path, exc
                )
                continue
            if isinstance(obj, dict):
                records.append(obj)
            else:
                logger.warning(
                    "Skipping non-object JSON line %d in %s", line_no, path
                )
    return records

def read_telemetry_file(path: Path) -> List[Dict[str, Any]]:
    """
    Read telemetry records from a file.

    Supported formats:
      - JSON array of objects
      - JSONL / NDJSON (one JSON object per line) when the JSON array parse fails
    """
    if not path.exists():
        raise FileNotFoundError(f"Telemetry file not found: {path}")

    if path.suffix.lower() == ".json":
        try:
            return _read_json_array(path)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to parse %s as JSON array (%s). Trying JSON lines.", path, exc
            )
            return _read_json_lines(path)

    # Fallback: assume JSON lines for other text formats
    return _read_json_lines(path)

def merge_sources(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    """
    Utility to ingest multiple files and merge telemetry streams.
    """
    all_records: List[Dict[str, Any]] = []
    for p in paths:
        try:
            records = read_telemetry_file(p)
        except FileNotFoundError:
            logger.error("Telemetry source not found: %s", p)
            continue
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to read telemetry from %s: %s", p, exc)
            continue
        all_records.extend(records)

    return all_records