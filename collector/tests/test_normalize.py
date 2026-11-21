import base64
import unittest
from collector.normalize import normalize_row, normalize_rows
from collector.sources.vpngate import parse_csv

class NormalizeTests(unittest.TestCase):
    def test_tcp_openvpn_is_not_sstp(self):
        cfg = base64.b64encode(b"client\nproto tcp-client\nremote 203.0.113.7 443\n").decode()
        node = normalize_row({"IP":"203.0.113.7","Port":"443","OpenVPN_ConfigData_Base64":cfg})
        self.assertEqual(node["protocol"], "openvpn")
        self.assertEqual(node["transport"], "tcp")

    def test_vpngate_api_extracts_port_from_embedded_profile(self):
        cfg = base64.b64encode(b"client\\nproto udp\\nremote 198.51.100.22 1194\\n").decode()
        node = normalize_row({"IP":"198.51.100.22","OpenVPN_ConfigData_Base64":cfg})
        self.assertEqual(node["endpoint"]["port"], 1194)
        self.assertEqual(node["transport"], "udp")

    def test_bad_port_skipped(self):
        self.assertIsNone(normalize_row({"IP":"203.0.113.8","Port":"0"}))

    def test_deduplicate(self):
        rows = [{"IP":"203.0.113.9","Port":"1194"},{"IP":"203.0.113.9","Port":"1194"}]
        self.assertEqual(len(normalize_rows(rows)), 1)

    def test_csv_header(self):
        rows = parse_csv("# comment\nIP,Port\n203.0.113.1,1194\n")
        self.assertEqual(rows[0]["IP"], "203.0.113.1")

if __name__ == "__main__":
    unittest.main()
