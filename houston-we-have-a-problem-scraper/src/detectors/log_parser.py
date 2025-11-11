import logging
import re
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

LOG_PATTERN = re.compile(
    r"""
    ^\[
        (?P<timestamp>.+?)
    \]\s+\[
        (?P<level>[A-Z]+)
    \]\s+\[
        (?P<source>[^\]]+)
    \]\s+
        (?P<code>[A-Z0-9_]+):
        \s*
        (?P<message>[^|]*?)
        (?:\s+\|\s+(?P<context>.*))?
    $
    """,
    re.VERBOSE,
)

def _parse_timestamp(value: str) -> str:
    """Normalize timestamp to ISO 8601 string if possible."""
    # Try common formats; if all fail, return original.
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.isoformat()
        except ValueError:
            continue
    return value.strip()

def parse_logs(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a log file into structured entries.

    Expected format per line (flexible but recommended):

        [2025-11-10 10:15:42] [ERROR] [auth-service] ERR1001: Invalid credentials | user_id=123 ip=1.2.3.4

    Returns a list of dictionaries with fields:
        errorMessage, errorCode, timestamp, source, severity, context, rawLevel, rawLine
    """
    entries: List[Dict[str, Any]] = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_number, raw_line in enumerate(f, start=1):
                line = raw_line.rstrip("\n")
                if not line.strip():
                    continue

                match = LOG_PATTERN.match(line)
                if not match:
                    logger.debug("Unrecognized log format at line %d: %s", line_number, line)
                    # Treat as generic info entry
                    entries.append(
                        {
                            "errorMessage": line.strip(),
                            "errorCode": "GENERIC",
                            "timestamp": "",
                            "source": "unknown",
                            "severity": "info",
                            "context": "",
                            "rawLevel": "INFO",
                            "rawLine": line,
                            "lineNumber": line_number,
                        }
                    )
                    continue

                groups = match.groupdict()
                timestamp = _parse_timestamp(groups["timestamp"])
                level = groups["level"].upper()
                source = groups["source"].strip()
                code = groups["code"].strip()
                message = (groups["message"] or "").strip()
                context = (groups.get("context") or "").strip()

                entry: Dict[str, Any] = {
                    "errorMessage": message,
                    "errorCode": code,
                    "timestamp": timestamp,
                    "source": source,
                    "severity": level.lower(),  # initial "severity" used by classifier
                    "context": context,
                    "rawLevel": level,
                    "rawLine": line,
                    "lineNumber": line_number,
                }
                entries.append(entry)

    except FileNotFoundError:
        logger.error("Log file not found: %s", file_path)
        raise
    except OSError as e:
        logger.error("Error reading log file %s: %s", file_path, e)
        raise

    return entries