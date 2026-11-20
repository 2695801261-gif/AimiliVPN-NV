import unittest
from node_finder.collector.links import parse_link, parse_text

class LinkParserTests(unittest.TestCase):
    def test_vless(self):
        node = parse_link("vless://00000000-0000-0000-0000-000000000000@example.com:443?security=tls#demo")
        self.assertEqual(node["protocol"], "vless")
        self.assertEqual(node["endpoint"], {"host": "example.com", "port": 443})
        self.assertEqual(node["status"], "pending")

    def test_hysteria2_alias(self):
        node = parse_link("hy2://fake-password@example.com:443#test")
        self.assertEqual(node["protocol"], "hysteria2")

    def test_trojan(self):
        node = parse_link("trojan://fake-password@example.com:443")
        self.assertEqual(node["protocol"], "trojan")

    def test_ipv6(self):
        node = parse_link("socks5://user:pass@[2001:db8::1]:1080")
        self.assertEqual(node["endpoint"]["host"], "2001:db8::1")
        self.assertEqual(node["endpoint"]["port"], 1080)

    def test_invalid_scheme_rejected_without_echoing_secret(self):
        nodes, errors = parse_text("unknown://secret@example.com:443")
        self.assertEqual(nodes, [])
        self.assertNotIn("secret", str(errors))

    def test_deduplication(self):
        link = "trojan://fake-password@example.com:443"
        nodes, errors = parse_text(link + "\n" + link, source_id="fixture")
        self.assertEqual(len(nodes), 1)
        self.assertEqual(errors, [])

if __name__ == "__main__":
    unittest.main()
