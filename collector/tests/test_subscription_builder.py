import unittest
import yaml

from collector.build_subscription import build_subscription


class SubscriptionBuilderTests(unittest.TestCase):
    def snapshot(self):
        return {
            "verified_count": 2,
            "proxies": [
                {"name": "same node", "type": "ss", "server": "192.0.2.1", "port": 443, "cipher": "aes-128-gcm", "password": "public-source-secret"},
                {"name": "same node", "type": "trojan", "server": "192.0.2.2", "port": 443, "password": "another-secret", "sni": "example.org"},
            ],
            "verification": [{"status": "verified"}, {"status": "verified"}],
        }

    def test_builds_valid_yaml_with_only_verified_records(self):
        result = yaml.safe_load(build_subscription(self.snapshot()))
        self.assertEqual(len(result["proxies"]), 2)
        self.assertEqual(result["proxies"][0]["name"], "same-node")
        self.assertEqual(result["proxies"][1]["name"], "same-node-2")
        self.assertEqual(result["rules"], ["MATCH,Aimili Select"])
        self.assertEqual(result["proxy-groups"][0]["type"], "url-test")

    def test_refuses_empty_snapshot(self):
        snapshot = self.snapshot()
        snapshot["proxies"] = []
        snapshot["verification"] = []
        with self.assertRaises(ValueError):
            build_subscription(snapshot)

    def test_refuses_mismatched_verification_count(self):
        snapshot = self.snapshot()
        snapshot["verification"] = snapshot["verification"][:1]
        with self.assertRaises(ValueError):
            build_subscription(snapshot)

    def test_refuses_non_object_proxy_instead_of_silently_dropping_it(self):
        snapshot = self.snapshot()
        snapshot["proxies"][1] = None
        with self.assertRaisesRegex(ValueError, "not an object"):
            build_subscription(snapshot)

    def test_refuses_invalid_endpoint_fields(self):
        for field, value in (("server", ""), ("port", 70000), ("port", True), ("type", "")):
            with self.subTest(field=field, value=value):
                snapshot = self.snapshot()
                snapshot["proxies"][0][field] = value
                with self.assertRaises(ValueError):
                    build_subscription(snapshot)


if __name__ == "__main__":
    unittest.main()
