from collections import Counter, defaultdict
from typing import Dict, Any, List

def top_patterns(events: List[Dict[str, Any]], top_n: int = 5) -> Dict[str, list[tuple[str, int]]]:
    """
    Return top patterns by:
      - errorType
      - message (exact)
      - source (sourceFile:lineNumber)
    """
    by_type = Counter()
    by_message = Counter()
    by_source = Counter()

    for e in events:
        by_type[e.get("errorType", "")] += 1
        by_message[e.get("message", "")] += 1
        src = f"{e.get('sourceFile', '')}:{e.get('lineNumber', '')}"
        by_source[src] += 1

    return {
        "errorType": by_type.most_common(top_n),
        "message": by_message.most_common(top_n),
        "source": by_source.most_common(top_n),
    }

def severity_breakdown(events: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = defaultdict(int)
    for e in events:
        sev = e.get("severity", "info")
        counts[sev] += 1
    return dict(counts)