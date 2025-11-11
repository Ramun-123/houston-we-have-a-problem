import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Allow absolute-style imports from src/
CURRENT_DIR = Path(__file__).parent
ROOT_DIR = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from utils.file_utils import list_files, read_json  # noqa: E402
from utils.time_utils import utc_now_iso  # noqa: E402
from logger.storage import Storage  # noqa: E402
from logger.handler import ErrorHandler  # noqa: E402
from alerts.email_notifier import EmailNotifier  # noqa: E402
from alerts.webhook_notifier import WebhookNotifier  # noqa: E402
from analyzers.pattern_detector import top_patterns, severity_breakdown  # noqa: E402
from analyzers.trend_reporter import daily_trends, write_trend_csv  # noqa: E402

def load_settings(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found at {path}")
    return read_json(path)

def build_handler(cfg: Dict[str, Any]) -> ErrorHandler:
    archive_csv = ROOT_DIR / cfg.get("archive_csv", "data/archives/error_history.csv")
    jsonl_path = cfg.get("jsonl_path")
    if jsonl_path:
        jsonl_path = ROOT_DIR / jsonl_path

    storage = Storage(csv_path=archive_csv, jsonl_path=jsonl_path)

    email_cfg = cfg.get("email", {})
    email_notifier = EmailNotifier(
        host=email_cfg.get("host", ""),
        port=int(email_cfg.get("port", 587)),
        username=email_cfg.get("username") or None,
        password=email_cfg.get("password") or None,
        from_addr=email_cfg.get("from", ""),
        to_addr=email_cfg.get("to", ""),
        use_tls=bool(email_cfg.get("use_tls", True)),
        enabled=bool(email_cfg.get("enabled", False)),
    )

    webhook_cfg = cfg.get("webhook", {})
    webhook_notifier = WebhookNotifier(
        url=webhook_cfg.get("url", ""),
        enabled=bool(webhook_cfg.get("enabled", False)),
    )

    thresholds = cfg.get("alert_thresholds", {"critical": 1, "error": 10, "warning": 50})
    return ErrorHandler(storage, email_notifier, webhook_notifier, thresholds)

def ingest_from_dir(handler: ErrorHandler, input_dir: Path) -> int:
    """
    Reads all .json files in input_dir and ingests them as error events.
    Files may contain either a single event object or an array of events.
    """
    count = 0
    files = list_files(input_dir, ".json")
    for jf in files:
        try:
            data = read_json(jf)
            if isinstance(data, list):
                for ev in data:
                    handler.ingest(ev)
                    count += 1
            elif isinstance(data, dict):
                handler.ingest(data)
                count += 1
            else:
                print(f"[WARN] Unsupported JSON structure in {jf.name}")
        except Exception as e:
            print(f"[ERROR] Failed to ingest {jf.name}: {e}")
    return count

def generate_reports(cfg: Dict[str, Any], storage: Storage) -> None:
    recent_n = int(cfg.get("report", {}).get("recent_sample", 200))
    recent = storage.read_recent(limit=recent_n)
    patterns = top_patterns(recent, top_n=5)
    sev = severity_breakdown(recent)
    trend_rows = daily_trends(recent)
    trend_path = ROOT_DIR / cfg.get("report", {}).get("trend_csv", "data/archives/daily_trends.csv")
    write_trend_csv(trend_path, trend_rows)

    # Print a compact summary to stdout
    print("=== Houston Summary ===")
    print(f"Generated at: {utc_now_iso()}")
    print(f"Recent sample size: {len(recent)}")
    print("Severity breakdown:", json.dumps(sev, indent=2))
    print("Top patterns:", json.dumps(patterns, indent=2))
    print(f"Trend CSV updated: {trend_path}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Houston Error Monitor")
    parser.add_argument(
        "--config",
        default=str(ROOT_DIR / "src" / "config" / "settings.json"),
        help="Path to settings.json",
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Ingest events from configured log_input_dir",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate analytics reports (severity breakdown, trends)",
    )
    args = parser.parse_args()

    cfg = load_settings(Path(args.config))
    handler = build_handler(cfg)

    if args.ingest:
        input_dir = ROOT_DIR / cfg.get("log_input_dir", "data/logs")
        n = ingest_from_dir(handler, input_dir)
        print(f"[INFO] Ingested {n} event(s) from {input_dir}")

    if args.report:
        generate_reports(cfg, handler.storage)

    if not args.ingest and not args.report:
        # Default action: ingest then report
        input_dir = ROOT_DIR / cfg.get("log_input_dir", "data/logs")
        n = ingest_from_dir(handler, input_dir)
        print(f"[INFO] Ingested {n} event(s) from {input_dir}")
        generate_reports(cfg, handler.storage)

if __name__ == "__main__":
    main()