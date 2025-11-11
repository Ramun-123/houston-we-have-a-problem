import re
import time

class ValidationRules:
    def __init__(self, settings):
        self.settings = settings
        self.rules = settings.get("rules", {"missing_title": True, "forbidden_words": ["error", "404", "not found"]})

    def check(self, data):
        issues = []
        if self.rules.get("missing_title") and not data.get("title"):
            issues.append({
                "errorType": "missing_data",
                "errorMessage": "Missing page title",
                "timestamp": int(time.time()),
                "severity": "medium",
                "context": {"url": data.get("url")}
            })

        for word in self.rules.get("forbidden_words", []):
            if re.search(word, data.get("content", ""), re.IGNORECASE):
                issues.append({
                    "errorType": "content_mismatch",
                    "errorMessage": f"Found forbidden word: {word}",
                    "timestamp": int(time.time()),
                    "severity": "low",
                    "context": {"url": data.get("url")}
                })
        return issues