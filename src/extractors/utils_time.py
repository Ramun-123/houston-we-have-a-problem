from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

def parse_timestamp(value: str) -> datetime:
    """
    Parse an ISO-8601-like timestamp into a timezone-aware UTC datetime.

    Supports:
      - 2025-11-10T10:15:30Z
      - 2025-11-10T10:15:30+00:00
      - 2025-11-10 10:15:30
    """
    if not value:
        raise ValueError("Empty timestamp")

    text = value.strip()

    # Normalize trailing Z to +00:00
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    # Try full ISO parsing first
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        # Fallback formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        else:
            raise

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt

def format_timestamp(dt: datetime, *, with_timezone: bool = True) -> str:
    """
    Format a datetime in a consistent ISO representation.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    if with_timezone:
        return dt.astimezone(timezone.utc).isoformat()
    return dt.replace(tzinfo=None).isoformat(sep=" ")