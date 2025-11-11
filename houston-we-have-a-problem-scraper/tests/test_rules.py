import unittest
from src.analyzers.validation_rules import ValidationRules

class TestValidationRules(unittest.TestCase):
    def setUp(self):
        self.rules = ValidationRules({"rules": {"missing_title": True, "forbidden_words": ["error"]}})

    def test_missing_title(self):
        data = {"url": "https://example.com", "title": None, "content": "sample"}
        issues = self.rules.check(data)
        self.assertTrue(any(i["errorType"] == "missing_data" for i in issues))

    def test_forbidden_word(self):
        data = {"url": "https://example.com", "title": "Page", "content": "something error found"}
        issues = self.rules.check(data)
        self.assertTrue(any("forbidden" in i["errorMessage"] for i in issues))

if __name__ == "__main__":
    unittest.main()