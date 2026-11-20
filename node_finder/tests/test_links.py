import base64
import json
import unittest
from node_finder.collector.links import parse_link, parse_text

class LinkParserTests(unittest.TestCase):
    def test_vless(self):
        node = parse_link("vless://00000000-0000-0000-0000-000000000000@example.com:443?security=tls#demo")
        self.assertEqual(node["protocol"], "vless")
        self.assertEqual(node["endpoint"], {"host": "example.com", "port": 443})
        self.assertEqual(node["status"], "pending")

    def test_vmess(self):
        payload = base64.urlsafe_b64encode(json.dumps({"add":"example.com","port":"443","ps":"demo"}).encode()).decode().rstrip("=")
        node = parse_link("vmess://" + payload)
        self.assertEqual(node["protocol"], "vmess")
        self.assertEqual(node["endpoint"]["port"], 443)

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

    def test_invalid_scheme_does_not_echo_secret(self):
        nodes, errors = parse_text("unknown://secret@example.com:443")
        self.assertEqual(nodes, [])
        self.assertNotIn("secret", str(errors))

    def test_base64_subscription(self):
        import base64
        raw = "vless://00000000-0000-0000-0000-000000000000@example.com:443"
        encoded = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
        nodes, errors = parse_text(encoded, source_id="fixture")
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["protocol"], "vless")
        self.assertEqual(errors, [])

    def test_deduplication(self):
        link = "trojan://fake-password@example.com:443"
        nodes, errors = parse_text(link + "\n" + link, source_id="fixture")
        self.assertEqual(len(nodes), 1)
        self.assertEqual(errors, [])

if __name__ == "__main__":
    unittest.main()
