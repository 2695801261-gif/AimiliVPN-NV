"""Persistent, bounded candidate history with fair round-robin validation."""
import json
from pathlib import Path
from datetime import datetime, timezone

POOL_LIMIT = 2000
PER_COUNTRY_LIMIT = 40
ROTATE_LIMIT = 100

def _stamp(node):
    return node.get("last_seen_at") or node.get("observed_at") or ""

def load_pool(path):
    p = Path(path)
    if not p.exists():
        return {"version": 1, "cursor": 0, "nodes": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("nodes"), list):
            return {"version": 1, "cursor": max(0, int(data.get("cursor", 0))), "nodes": data["nodes"]}
    except (OSError, ValueError, TypeError):
        pass
    return {"version": 1, "cursor": 0, "nodes": []}

def merge_candidates(existing, incoming, now=None):
    now = now or datetime.now(timezone.utc).isoformat()
    merged = {n["id"]: dict(n) for n in existing if isinstance(n, dict) and n.get("id")}
    for raw in incoming:
        if not isinstance(raw, dict) or not raw.get("id"):
            continue
        node = dict(merged.get(raw["id"], {}))
        # Keep verification evidence; refresh source observations without upgrading status.
        old_status = node.get("status", "pending")
        node.update(raw)
        node["last_seen_at"] = now
        if old_status == "verified_connected":
            node["status"] = old_status
        elif node.get("status") not in ("failed", "paused"):
            node["status"] = "pending"
        merged[node["id"]] = node

    by_country = {}
    for node in merged.values():
        key = (node.get("country_code") or node.get("country") or "UNKNOWN").upper()
        by_country.setdefault(key, []).append(node)
    retained = []
    for group in by_country.values():
        group.sort(key=lambda n: (_stamp(n), n.get("id", "")), reverse=True)
        retained.extend(group[:PER_COUNTRY_LIMIT])
    retained.sort(key=lambda n: (_stamp(n), n.get("id", "")), reverse=True)
    return retained[:POOL_LIMIT]

def select_rotation(nodes, cursor=0, limit=ROTATE_LIMIT):
    ordered = sorted(nodes, key=lambda n: n.get("id", ""))
    if not ordered:
        return [], 0
    start = cursor % len(ordered)
    count = min(max(0, limit), len(ordered))
    selected = [ordered[(start + i) % len(ordered)] for i in range(count)]
    return selected, (start + count) % len(ordered)

def save_pool(path, nodes, cursor):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({"version": 1, "cursor": cursor, "nodes": nodes},
                                    ensure_ascii=False, indent=2), encoding="utf-8")
