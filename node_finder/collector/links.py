"""Conservative parser for common proxy share links.

This module identifies and normalizes syntax only. It does NOT prove that a
node is reachable or that its credentials work. Never log the input link:
it may contain passwords, UUIDs, or private keys.
"""
import base64
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlsplit, unquote

SCHEMES = {
    "ss": "shadowsocks",
    "ssr": "shadowsocksr",
    "vmess": "vmess",
    "vless": "vless",
    "trojan": "trojan",
    "hysteria": "hysteria",
    "hysteria2": "hysteria2",
    "hy2": "hysteria2",
    "tuic": "tuic",
    "anytls": "anytls",
    "socks": "socks",
    "socks5": "socks",
    "http": "http",
    "https": "https",
    "ssh": "ssh",
    "snell": "snell",
    "shadowtls": "shadowtls",
}

def _decode_b64(value):
    value = value.strip()
    value += "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value.encode()).decode("utf-8")
    except Exception as exc:
        raise ValueError("invalid base64 payload") from exc

def _host_port(netloc):
    parsed = urlsplit("//" + netloc)
    host = parsed.hostname
    try:
        port = parsed.port
    except ValueError:
        port = None
    if not host or not port or not 1 <= port <= 65535:
        raise ValueError("missing or invalid endpoint")
    return host, port

def parse_link(line, source_id="manual"):
    raw = line.strip()
    if not raw or raw.startswith("#"):
        return None

    if raw.lower().startswith("vmess://"):
        obj = json.loads(_decode_b64(raw[8:]))
        host = str(obj.get("add") or "").strip()
        port = int(obj.get("port") or 0)
        if not host or not 1 <= port <= 65535:
            raise ValueError("invalid vmess endpoint")
        protocol, name = "vmess", unquote(str(obj.get("ps") or "")) or None
    else:
        parsed = urlsplit(raw)
        scheme = parsed.scheme.lower()
        protocol = SCHEMES.get(scheme)
        if not protocol:
            raise ValueError("unsupported scheme")
        name = unquote(parsed.fragment) or None

        if protocol == "shadowsocks":
            authority = parsed.netloc
            if "@" not in authority:
                decoded = _decode_b64(authority.split("#", 1)[0])
                if "@" not in decoded:
                    raise ValueError("unsupported shadowsocks link form")
                authority = decoded.rsplit("@", 1)[1]
            host, port = _host_port(authority)
        else:
            host, port = _host_port(parsed.netloc)

    stable = hashlib.sha256(
        (source_id + "|" + protocol + "|" + host.lower() + "|" + str(port) + "|" + raw).encode("utf-8")
    ).hexdigest()[:32]
    return {
        "id": stable,
        "source_id": source_id,
        "protocol": protocol,
        "endpoint": {"host": host, "port": port},
        "name": name,
        "country_code": None,
        "country_source": "unknown",
        "status": "pending",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "last_checked_at": None,
        "latency_ms": None,
        "egress_ip": None,
        "test_location": None,
        "failure_count": 0,
        "share_link": raw,
        "metadata": {}
    }

def decode_subscription_text(text):
    """Decode a whole base64 subscription only when it clearly contains share links."""
    stripped = text.strip()
    if not stripped or "://" in stripped:
        return text
    compact = "".join(stripped.split())
    try:
        decoded = _decode_b64(compact)
    except Exception:
        return text
    prefixes = tuple(scheme + "://" for scheme in SCHEMES)
    if any(line.strip().lower().startswith(prefixes) for line in decoded.splitlines()):
        return decoded
    return text

def parse_text(text, source_id="manual"):
    text = decode_subscription_text(text)
    nodes, errors = [], []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            node = parse_link(line, source_id=source_id)
            if node:
                nodes.append(node)
        except Exception as exc:
            # Do not echo the original line: it can contain credentials.
            errors.append({"line": number, "reason": str(exc)})
    unique = {node["id"]: node for node in nodes}
    return sorted(unique.values(), key=lambda n: (n["protocol"], n["endpoint"]["host"], n["endpoint"]["port"])), errors
