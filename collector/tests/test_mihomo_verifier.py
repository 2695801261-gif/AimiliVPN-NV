import subprocess
import unittest
from unittest.mock import patch

from collector.verify_mihomo import build_config, parse_public_ip, verify_one


class MihomoVerifierTests(unittest.TestCase):
    def test_build_config_forces_all_traffic_through_single_proxy(self):
        proxy = {"name": "node-a", "type": "ss", "server": "example.org", "port": 443}
        config = build_config(proxy, 17890)
        self.assertEqual(config["proxies"], [proxy])
        self.assertEqual(config["proxy-groups"][0]["proxies"], ["node-a"])
        self.assertEqual(config["rules"], ["MATCH,VERIFY"])
        self.assertFalse(config["allow-lan"])

    def test_only_accepts_public_egress_ip(self):
        self.assertEqual(parse_public_ip("8.8.8.8\n"), "8.8.8.8")
        self.assertIsNone(parse_public_ip("127.0.0.1"))
        self.assertIsNone(parse_public_ip("not-an-ip"))

    @patch("collector.verify_mihomo.request_egress", return_value="8.8.8.8")
    @patch("collector.verify_mihomo.wait_for_listener")
    @patch("collector.verify_mihomo.subprocess.Popen")
    @patch("collector.verify_mihomo.subprocess.run")
    def test_verify_one_requires_config_check_and_egress(
        self, run, popen, wait_listener, egress
    ):
        run.return_value = subprocess.CompletedProcess([], 0, "", "")
        process = unittest.mock.Mock()
        process.poll.return_value = None
        popen.return_value = process
        proxy = {"name": "node-a", "type": "ss", "server": "example.org", "port": 443}
        result = verify_one(proxy, "mihomo", 17890, 1, 1)
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["egress_ip"], "8.8.8.8")
        run.assert_called_once()
        self.assertIn("-t", run.call_args.args[0])
        wait_listener.assert_called_once()
        egress.assert_called_once_with(17890, 1, attempts=2)

    @patch("collector.verify_mihomo.time.sleep")
    @patch("collector.verify_mihomo.urllib.request.build_opener")
    def test_egress_uses_fallback_endpoint_after_transient_failure(self, build_opener, sleep):
        from collector.verify_mihomo import request_egress

        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"1.1.1.1"
        opener = unittest.mock.Mock()
        opener.open.side_effect = [TimeoutError("first endpoint timed out"), response]
        build_opener.return_value = opener
        self.assertEqual(request_egress(17890, 1, urls=("https://first.invalid", "https://second.invalid"), attempts=1), "1.1.1.1")
        self.assertEqual(opener.open.call_count, 2)


if __name__ == "__main__":
    unittest.main()
