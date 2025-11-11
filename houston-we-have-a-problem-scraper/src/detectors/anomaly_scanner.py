import logging
from collections import Counter
from typing import Any, Dict, Iterable, List, Tuple

logger = logging.getLogger(__name__)

def scan_anomalies(
    entries: Iterable[Dict[str, Any]],
    threshold: int = 3,
) -> List[Dict[str, Any]]:
    """
    Detect anomalies based on repeated error codes per source.

    For simplicity, an error is considered anomalous if the combination of
    (errorCode, source) appears at least `threshold` times in the dataset.

    Adds:
        occurrences: int   - number of times this (code, source) pair appears
        is_anomaly: bool   - True if occurrences >= threshold
    """
    entries_list = list(entries)

    key_counts: Counter[Tuple[str, str]] = Counter()
    for e in entries_list:
        code = str(e.get("errorCode", "")).upper()
        source = str(e.get("source", "unknown"))
        key_counts[(code, source)] += 1

    results: List[Dict[str, Any]] = []
    for e in entries_list:
        code = str(e.get("errorCode", "")).upper()
        source = str(e.get("source", "unknown"))
        count = key_counts[(code, source)]
        entry = dict(e)
        entry["occurrences"] = count
        entry["is_anomaly"] = count >= threshold
        results.append(entry)

    logger.debug(
        "Anomaly scan complete: %d entries, %d unique (code, source) pairs",
        len(results),
        len(key_counts),
    )
    return results