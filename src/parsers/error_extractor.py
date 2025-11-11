thonimport logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

# Example log line format:
# 2025-11-11 12:00:00,123 [ERROR] [auth-service] (ERR401) Unauthorized access attempt at /api/login
LOG_LINE_PATTERN = re.compile(
    r"""
    ^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s+
    \[(?P<level>[A-Z]+)\]\s+
    \[(?P<component>[^\]]+)\]\s+
    \((?P<code>[^)]+)\)\s+
    (?P<message>.+)$
    """,
    re.VERBOSE,
)

LEVEL_TO_SEVERITY = {
    "CRITICAL": "critical",
    "ERROR": "critical",
    "WARNING": "warning",
    "WARN": "warning",
    "INFO": "info",
    "DEBUG": "info",
}

def _parse_timestamp(raw: str) -> str:
    """
    Parse a timestamp string and normalize to ISO 8601.

    Falls back to the raw string if parsing fails, but logs a warning.
    """
    for fmt in ("%Y-%m-%d %H:%M:%S,%f", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.isoformat()
        except ValueError:
            continue

    logger.warning("Could not parse timestamp '%s'; keeping raw.", raw)
    return raw

def _level_to_severity(level: str) -> str:
    return LEVEL_TO_SEVERITY.get(level.upper(), "info")

def _build_log_url(
    base: Optional[str],
    error_code: str,
    line_number: Optional[int] = None,
) -> Optional[str]:
    if not base:
        return None
    if not base.endswith("/"):
        base = base + "/"
    url = f"{base}?errorCode={error_code}"
    if line_number is not None:
        url += f"&line={line_number}"
    return url

def parse_error_line(
    line: str,
    *,
    log_url_base: Optional[str] = None,
    line_number: Optional[int] = None,
) -> Optional[Dict]:
    """
    Parse a single log line. Returns a structured error dict or None if the
    line does not represent an error-like entry.
    """
    match = LOG_LINE_PATTERN.match(line.strip())
    if not match:
        return None

    groups = match.groupdict()
    timestamp_raw = groups["timestamp"]
    level = groups["level"]
    component = groups["component"]
    code = groups["code"]
    message = groups["message"].strip()

    severity = _level_to_severity(level)
    timestamp_iso = _parse_timestamp(timestamp_raw)
    log_url = _build_log_url(log_url_base, code, line_number=line_number)

    error_doc = {
        "errorMessage": message,
        "errorCode": code,
        "timestamp": timestamp_iso,
        "systemComponent": component,
        "severity": severity,
        "logUrl": log_url,
        "level": level,
        "lineNumber": line_number,
    }

    logger.debug("Parsed error: %s", error_doc)
    return error_doc

def extract_errors(
    lines: Iterable[str],
    *,
    log_url_base: Optional[str] = None,
) -> List[Dict]:
    """Extract error documents from an iterable of log lines."""
    errors: List[Dict] = []

    for idx, line in enumerate(lines, start=1):
        parsed = parse_error_line(
            line,
            log_url_base=log_url_base,
            line_number=idx,
        )
        if parsed is not None:
            errors.append(parsed)

    logger.info("Extracted %d errors from stream.", len(errors))
    return errors

def extract_errors_from_file(
    log_file: Path,
    *,
    log_url_base: Optional[str] = None,
    encoding: str = "utf-8",
) -> List[Dict]:
    """
    Extract structured error documents from a log file.

    Raises FileNotFoundError if the file does not exist.
    """
    log_file = Path(log_file)

    if not log_file.exists():
        logger.error("Log file does not exist: %s", log_file)
        raise FileNotFoundError(str(log_file))

    try:
        with log_file.open("r", encoding=encoding, errors="replace") as fp:
            lines = fp.readlines()
    except OSError as exc:
        logger.error("Failed to read log file %s: %s", log_file, exc)
        raise

    logger.debug("Read %d lines from %s", len(lines), log_file)
    return extract_errors(lines, log_url_base=log_url_base)