from datetime import datetime, timezone
from dateutil import parser

def utc_now_iso() -> str:
    """Return current UTC time in ISO 8601 format with 'Z'."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def to_utc_iso(ts: str | datetime) -> str:
    """
    Normalize a timestamp (str or datetime) to ISO 8601 UTC string.
    Accepts a variety of input formats (via dateutil.parser).
    """
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    dt = parser.parse(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")