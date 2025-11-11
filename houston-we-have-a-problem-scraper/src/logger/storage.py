from pathlib import Path
from typing import Dict, Any, Iterable, List
import json

from ..utils.file_utils import append_csv, ensure_dir

CSV_HEADER = [
    "timestamp",
    "severity",
    "errorType",
    "message",
    "sourceFile",
    "lineNumber",
    "environment",
    "device",
    "resolved",
    "stackTrace",
]

class Storage:
    """
    Persists events to:
      - JSON lines file (optional)
      - CSV archive (required)
    """

    def __init__(self, csv_path: Path, jsonl_path: Path | None = None) -> None:
        self.csv_path = Path(csv_path)
        self.jsonl_path = Path(jsonl_path) if jsonl_path else None
        ensure_dir(self.csv_path.parent)
        if self.jsonl_path:
            ensure_dir(self.jsonl_path.parent)

    def write_event(self, event: Dict[str, Any]) -> None:
        # CSV
        row = [
            event["timestamp"],
            event["severity"],
            event["errorType"],
            event["message"].replace("\n", " ").strip(),
            event["sourceFile"],
            event["lineNumber"],
            event["environment"],
            event["device"],
            str(event["resolved"]).lower(),
            event["stackTrace"].replace("\n", "\\n"),
        ]
        append_csv(self.csv_path, [row], header=CSV_HEADER)

        # JSONL
        if self.jsonl_path:
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def write_many(self, events: Iterable[Dict[str, Any]]) -> int:
        count = 0
        for e in events:
            self.write_event(e)
            count += 1
        return count

    def read_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return last N rows from CSV (naive, reads file tail)."""
        if not self.csv_path.exists():
            return []
        # Efficient tail read
        with open(self.csv_path, "rb") as f:
            f.seek(0, 2)
            file_size = f.tell()
            block = 4096
            data = b""
            lines = []
            while file_size > 0 and len(lines) <= limit:
                step = min(block, file_size)
                file_size -= step
                f.seek(file_size)
                data = f.read(step) + data
                lines = data.split(b"\n")
            # Drop header if present
            text_lines = [l.decode("utf-8") for l in lines if l.strip()]
        if not text_lines:
            return []
        # Remove header (first line) if file is small enough to include it
        if text_lines and text_lines[0].startswith("timestamp,"):
            text_lines = text_lines[1:]
        # Keep last N
        text_lines = text_lines[-limit:]
        # Parse CSV minimally (split by comma), stackTrace may contain escaped \n but commas should be safe (message stripped)
        records = []
        for line in text_lines:
            cols = line.split(",")
            if len(cols) < len(CSV_HEADER):
                continue
            record = {CSV_HEADER[i]: ",".join(cols[i:]) if i == len(CSV_HEADER) - 1 else cols[i] for i in range(len(CSV_HEADER))}
            records.append(record)
        return records