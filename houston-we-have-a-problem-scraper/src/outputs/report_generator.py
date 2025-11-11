import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

REPORT_FIELDS = [
    "timestamp",
    "source",
    "errorCode",
    "errorMessage",
    "severity",
    "occurrences",
    "is_anomaly",
    "context",
]

def _ensure_parent_dir(path: Path) -> None:
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

def generate_report(
    issues: Iterable[Dict[str, Any]],
    json_path: Path,
    csv_path: Optional[Path] = None,
) -> None:
    """
    Generate structured JSON (and optional CSV) reports for detected issues.

    JSON:
        List of issue objects containing the fields defined in REPORT_FIELDS
        plus any extra metadata that may exist.

    CSV:
        Flat table containing the fields from REPORT_FIELDS.
    """
    issues_list: List[Dict[str, Any]] = list(issues)

    # JSON report
    _ensure_parent_dir(json_path)
    try:
        with json_path.open("w", encoding="utf-8") as jf:
            json.dump(issues_list, jf, indent=2, ensure_ascii=False)
        logger.info("Wrote JSON report with %d issues to %s", len(issues_list), json_path)
    except OSError as e:
        logger.error("Failed to write JSON report to %s: %s", json_path, e)
        raise

    # CSV report
    if csv_path:
        _ensure_parent_dir(csv_path)
        try:
            with csv_path.open("w", encoding="utf-8", newline="") as cf:
                writer = csv.DictWriter(cf, fieldnames=REPORT_FIELDS)
                writer.writeheader()
                for issue in issues_list:
                    row = {field: issue.get(field, "") for field in REPORT_FIELDS}
                    writer.writerow(row)
            logger.info("Wrote CSV report to %s", csv_path)
        except OSError as e:
            logger.error("Failed to write CSV report to %s: %s", csv_path, e)
            raise