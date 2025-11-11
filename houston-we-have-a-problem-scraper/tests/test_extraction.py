import unittest
from src.analyzers.pattern_detector import PatternDetector

class TestPatternDetector(unittest.TestCase):
    def test_fetch_data_structure(self):
        detector = PatternDetector({"timeout": 5})
        sample_html = "<html><head><title>Test</title></head><body>Hello</body></html>"
        from unittest.mock import patch, MagicMock

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.text = sample_html
            mock_response.raise_for_status = lambda: None
            mock_get.return_value = mock_response
            data = detector.fetch_data("https://fakeurl.com")
            self.assertIn("title", data)
            self.assertIn("content", data)

if __name__ == "__main__":
    unittest.main()