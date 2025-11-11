import json
import os

class IssueExporter:
    def __init__(self, settings):
        self.output_dir = settings.get("output_dir", "exports")
        os.makedirs(self.output_dir, exist_ok=True)

    def export(self, issues):
        output_path = os.path.join(self.output_dir, "issues_report.json")
        with open(output_path, "w") as f:
            json.dump(issues, f, indent=2)
        print(f"Issues exported to {output_path}")