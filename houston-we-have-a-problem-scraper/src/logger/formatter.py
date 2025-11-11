from typing import Dict, Any
from ..utils.time_utils import to_utc_iso

REQUIRED_FIELDS = [
    "timestamp",
    "errorType",
    "message",
    "stackTrace",
    "severity",
    "sourceFile",
    "lineNumber",
    "environment",
    "device",
    "resolved",
]

def normalize(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the error event contains all required fields and normalized types.
    - timestamp normalized to UTC ISO
    - severity to lower str
    - resolved to bool
    - lineNumber to int (>=0)
    """
    missing = [f for f in REQUIRED_FIELDS if f not in event]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    normalized = dict(event)
    normalized["timestamp"] = to_utc_iso(event["timestamp"])
    normalized["severity"] = str(event["severity"]).lower()
    normalized["resolved"] = bool(event["resolved"])

    try:
        ln = int(event["lineNumber"])
        if ln < 0:
            ln = 0
        normalized["lineNumber"] = ln
    except Exception as e:
        raise ValueError(f"Invalid lineNumber '{event['lineNumber']}': {e}")

    # Text fields to string
    normalized["errorType"] = str(event["errorType"])
    normalized["message"] = str(event["message"])
    normalized["stackTrace"] = str(event["stackTrace"])
    normalized["sourceFile"] = str(event["sourceFile"])
    normalized["environment"] = str(event["environment"])
    normalized["device"] = str(event["device"])

    return normalized