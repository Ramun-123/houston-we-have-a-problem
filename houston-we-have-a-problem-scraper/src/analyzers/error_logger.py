import json
import os
import time

class ErrorLogger:
    def __init__(self, settings):
        self.settings = settings
        self.log_dir = settings.get("log_dir", "logs")
        os.makedirs(self.log_dir, exist_ok=True)

    def log_issue(self, url, issue):
        log_path = os.path.join(self.log_dir, "issues.log")
        issue_record = {
            "sourceUrl": url,
            **issue
        }
        with open(log_path, "a") as f:
            f.write(json.dumps(issue_record) + "\n")
        return issue_record

    def log_error(self, url, message, severity="high"):
        log_path = os.path.join(self.log_dir, "errors.log")
        error_entry = {
            "sourceUrl": url,
            "errorType": "exception",
            "errorMessage": message,
            "timestamp": int(time.time()),
            "severity": severity
        }
        with open(log_path, "a") as f:
            f.write(json.dumps(error_entry) + "\n")
        return error_entry