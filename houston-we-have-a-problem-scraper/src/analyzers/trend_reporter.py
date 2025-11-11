from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
from ..utils.file_utils import append_csv, ensure_dir

HEADER = ["date", "severity", "count"]

def daily_trends(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate counts per day and severity.
    Expects event["timestamp"] in ISO 'YYYY-MM-DD...' format.
    """
    bucket: Dict[tuple[str, str], int] = defaultdict(int)
    for e in events:
        ts = str(e.get("timestamp", ""))
        day = ts[:10] if len(ts) >= 10 else "unknown"
        sev = str(e.get("severity", "info")).lower()
        bucket[(day, sev)] += 1
    rows = [{"date": k[0], "severity": k[1], "count": v} for k, v in bucket.items()]
    rows.sort(key=lambda r: (r["date"], r["severity"]))
    return rows

def write_trend_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    append_csv(
        path,
        ((r["date"], r["severity"], r["count"]) for r in rows),
        header=HEADER,
    )