thonimport json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ensure src directory is on sys.path so implicit namespace packages work
CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parent
PROJECT_ROOT = SRC_DIR.parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from parsers.error_extractor import extract_errors_from_file  # noqa: E402
from parsers.log_analyzer import analyze_errors  # noqa: E402
from utils.notifier import Notifier  # noqa: E402
from utils.formatter import build_json_report, format_summary_text  # noqa: E402

def load_settings() -> Dict[str, Any]:
    """Load configuration from src/config/settings.json."""
    config_path = SRC_DIR / "config" / "settings.json"
    try:
        with config_path.open("r", encoding="utf-8") as fp:
            settings = json.load(fp)
            logging.debug("Loaded settings from %s", config_path)
            return settings
    except FileNotFoundError:
        logging.error("Configuration file not found at %s", config_path)
        raise
    except json.JSONDecodeError as exc:
        logging.error("Invalid JSON in configuration file: %s", exc)
        raise

def resolve_path(relative_path: str) -> Path:
    """
    Resolve a project-relative path (e.g. 'data/logs/test_log.txt')
    to an absolute Path based on the project root.
    """
    return (PROJECT_ROOT / relative_path).resolve()

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    logger = logging.getLogger("houston-main")
    logger.info("Starting 'Houston, We Have a Problem!' log analysis.")

    try:
        settings = load_settings()
    except Exception:
        logger.critical("Failed to load settings. Aborting.")
        sys.exit(1)

    paths_cfg = settings.get("paths", {})
    log_file_path = paths_cfg.get("log_file", "data/logs/test_log.txt")
    output_file_path = paths_cfg.get("output_file", "data/sample_errors.json")
    log_url_base = settings.get("log_url_base")
    notifications_cfg = settings.get("notifications", {})

    log_file = resolve_path(log_file_path)
    output_file = resolve_path(output_file_path)

    logger.info("Reading log file: %s", log_file)

    try:
        errors = extract_errors_from_file(
            log_file=log_file,
            log_url_base=log_url_base,
        )
    except FileNotFoundError:
        logger.error("Log file not found: %s", log_file)
        sys.exit(2)
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error while extracting errors: %s", exc)
        sys.exit(3)

    if not errors:
        logger.warning("No errors detected in %s", log_file)
    else:
        logger.info("Extracted %d error entries from log.", len(errors))

    summary = analyze_errors(errors)

    metadata = {
        "source_log": str(log_file),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_errors": len(errors),
    }

    report_dict = build_json_report(errors=errors, summary=summary, metadata=metadata)

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output_file.open("w", encoding="utf-8") as fp:
            json.dump(report_dict, fp, indent=2)
        logger.info("Wrote JSON report to %s", output_file)
    except OSError as exc:
        logger.error("Failed to write JSON report to %s: %s", output_file, exc)
        sys.exit(4)

    # Print a short human-readable summary to stdout
    print(format_summary_text(summary))

    # Trigger notifications for high severity issues
    notifier = Notifier(config=notifications_cfg)
    notifier.notify(summary=summary, errors=errors)

    logger.info("Analysis complete.")

if __name__ == "__main__":
    main()