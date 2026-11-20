import unittest
from node_finder.collector.registry import validate_registry

class RegistryTests(unittest.TestCase):
    def test_empty_registry(self):
        self.assertEqual(validate_registry({"version": 1, "sources": []}), [])

    def test_valid_https_source(self):
        rows = validate_registry({"version": 1, "sources": [{
            "id": "fixture-source", "url": "https://example.com/nodes.txt",
            "format": "share_links_text", "enabled": True,
            "license_note": "Test fixture only"
        }]})
        self.assertEqual(rows[0]["id"], "fixture-source")

    def test_http_source_rejected(self):
        with self.assertRaises(ValueError):
            validate_registry({"version": 1, "sources": [{
                "id": "fixture-source", "url": "http://example.com/nodes.txt",
                "format": "share_links_text", "license_note": "Test"
            }]})

    def test_duplicate_ids_rejected(self):
        source = {"id": "fixture-source", "url": "https://example.com/a",
                  "format": "share_links_text", "license_note": "Test"}
        with self.assertRaises(ValueError):
            validate_registry({"version": 1, "sources": [source, dict(source)]})

if __name__ == "__main__":
    unittest.main()
