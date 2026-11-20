import unittest
from collector.candidate_pool import merge_candidates, select_rotation, POOL_LIMIT, PER_COUNTRY_LIMIT

def node(i, country="US"):
    return {"id": str(i), "country_code": country, "country": country,
            "observed_at": f"2026-01-{(i % 28)+1:02d}T00:00:00Z", "status": "pending"}

class CandidatePoolTests(unittest.TestCase):
    def test_country_cap(self):
        out = merge_candidates([], [node(i) for i in range(60)], now="2026-11-20T00:00:00Z")
        self.assertEqual(len(out), PER_COUNTRY_LIMIT)
    def test_global_cap(self):
        incoming = [node(i, f"C{i:03d}") for i in range(POOL_LIMIT + 100)]
        out = merge_candidates([], incoming, now="2026-11-20T00:00:00Z")
        self.assertLessEqual(len(out), POOL_LIMIT)
    def test_deduplicate_and_preserve_verified(self):
        old = [dict(node(1), status="verified_connected", egress_ip="203.0.113.9")]
        out = merge_candidates(old, [node(1)], now="2026-11-20T00:00:00Z")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["status"], "verified_connected")
        self.assertEqual(out[0]["egress_ip"], "203.0.113.9")
    def test_rotation_advances(self):
        nodes = [node(i) for i in range(8)]
        a, cursor = select_rotation(nodes, 0, 3)
        b, _ = select_rotation(nodes, cursor, 3)
        self.assertEqual(len({n["id"] for n in a + b}), 6)
if __name__ == "__main__":
    unittest.main()
