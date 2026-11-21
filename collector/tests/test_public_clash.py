import unittest
from unittest.mock import patch

from collector.sources.public_clash import fetch_candidates, parse_proxies


class PublicClashTests(unittest.TestCase):
    def test_accepts_supported_proxy_and_deduplicates(self):
        text = """
proxies:
  - name: test-ss
    type: ss
    server: 192.0.2.10
    port: 443
    cipher: aes-128-gcm
    password: example
  - name: test-ss
    type: ss
    server: 192.0.2.10
    port: 443
    cipher: aes-128-gcm
    password: example
"""
        self.assertEqual(len(parse_proxies(text)), 1)

    def test_rejects_invalid_and_unsupported(self):
        text = """
proxies:
  - name: bad-port
    type: vless
    server: example.org
    port: 70000
  - name: unsupported
    type: openvpn
    server: example.org
    port: 443
  - name: boolean-port
    type: ss
    server: example.org
    port: true
"""
        self.assertEqual(parse_proxies(text), [])

    def test_requires_proxies_list(self):
        with self.assertRaises(ValueError):
            parse_proxies("port: 7890\n")

    def test_limit_is_respected(self):
        text = """
proxies:
  - name: one
    type: ss
    server: one.example
    port: 443
    cipher: aes-128-gcm
    password: p
  - name: two
    type: ss
    server: two.example
    port: 443
    cipher: aes-128-gcm
    password: p
"""
        self.assertEqual(len(parse_proxies(text, limit=1)), 1)
        self.assertEqual(parse_proxies(text, limit=0), [])

    @patch("collector.sources.public_clash.fetch_text")
    def test_falls_back_when_one_source_is_unavailable(self, fetch_text):
        valid = "proxies:\n  - name: ok\n    type: ss\n    server: node.example\n    port: 443\n    cipher: aes-128-gcm\n    password: p\n"
        fetch_text.side_effect = [ValueError("first source down"), valid]
        source, nodes = fetch_candidates(urls=("https://first.invalid", "https://second.invalid"))
        self.assertEqual(source, "https://second.invalid")
        self.assertEqual(len(nodes), 1)

    @patch("collector.sources.public_clash.fetch_text")
    def test_merges_sources_round_robin_and_deduplicates(self, fetch_text):
        first = "proxies:\n  - {name: a, type: ss, server: a.example, port: 443, cipher: aes-128-gcm, password: p}\n  - {name: b, type: ss, server: b.example, port: 443, cipher: aes-128-gcm, password: p}\n"
        second = "proxies:\n  - {name: c, type: ss, server: c.example, port: 443, cipher: aes-128-gcm, password: p}\n  - {name: b, type: ss, server: b.example, port: 443, cipher: aes-128-gcm, password: p}\n"
        fetch_text.side_effect = [first, second]
        source, nodes = fetch_candidates(limit=3, urls=("https://one.invalid", "https://two.invalid"))
        self.assertEqual(source, "https://one.invalid;https://two.invalid")
        self.assertEqual([n["name"] for n in nodes], ["a", "c", "b"])


if __name__ == "__main__":
    unittest.main()
