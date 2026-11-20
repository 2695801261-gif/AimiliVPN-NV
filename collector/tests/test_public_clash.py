import unittest
from collector.sources.public_clash import parse_proxies


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
"""
        self.assertEqual(parse_proxies(text), [])

    def test_requires_proxies_list(self):
        with self.assertRaises(ValueError):
            parse_proxies("port: 7890\n")


if __name__ == "__main__":
    unittest.main()
