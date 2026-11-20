"""Normalize VPNGate records; never infer SSTP from TCP transport."""
import base64
import hashlib
from datetime import datetime, timezone

def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def normalize_row(row, observed_at=None):
    host = (row.get("IP") or "").strip()
    port = _int(row.get("Port"), 0)
    if not host or not 1 <= port <= 65535:
        return None
    config_b64 = (row.get("OpenVPN_ConfigData_Base64") or "").strip()
    profile, transport = None, "unknown"
    if config_b64:
        try:
            decoded = base64.b64decode(config_b64, validate=True).decode("utf-8", errors="replace")
            profile = decoded[:60000]
            for line in decoded.splitlines():
                parts = line.strip().lower().split()
                if len(parts) >= 2 and parts[0] == "proto":
                    if parts[1] in ("tcp", "tcp-client"):
                        transport = "tcp"
                    elif parts[1] in ("udp", "udp4", "udp6"):
                        transport = "udp"
                    break
        except Exception:
            profile = None
    protocol = "openvpn"
    node_id = hashlib.sha256(f"vpngate|{host}|{port}|{protocol}".encode()).hexdigest()[:24]
    return {
        "id": node_id, "source": "vpngate",
        "country": row.get("CountryLong") or None,
        "country_code": (row.get("CountryShort") or "").upper() or None,
        "protocol": protocol, "transport": transport,
        "endpoint": {"host": host, "port": port},
        "auth": {"type": "profile_defined"}, "profile": profile,
        "status": "pending",
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
        "last_checked_at": None, "latency_ms": None, "egress_ip": None,
        "failure_count": 0,
        "metadata": {"score": _int(row.get("Score")), "source_ping_ms": _int(row.get("Ping"), -1),
                     "sessions": _int(row.get("NumVpnSessions")), "operator_message": row.get("Message") or ""}
    }

def normalize_rows(rows):
    unique = {}
    for row in rows:
        node = normalize_row(row)
        if node:
            unique[node["id"]] = node
    return sorted(unique.values(), key=lambda n: (n["country"] or "", n["endpoint"]["host"], n["endpoint"]["port"]))
