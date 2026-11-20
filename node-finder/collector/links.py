"""Conservative parser for common proxy share links.

This module identifies and normalizes syntax only. It does NOT prove that a
node is reachable or that its credentials work. Never log the input link:
it may contain passwords, UUIDs, or private keys.
"""
import base64
import hashlib
import json
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
    for alt in (value, value.replace("-", "+").replace("_", "/")):
        try:
            return base64.b64decode(alt, validate=True).decode("utf-8")
        except Exception:
            pass
    raise ValueError("invalid base64 payload")

def _host_port(netloc):
    # urlsplit handles bracketed IPv6 correctly.
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

    # VMess links carry a base64-encoded JSON object rather than a normal URL.
    if raw.lower().startswith("vmess://"):
        payload = _decode_b64(raw[8:])
        obj = json.loads(payload)
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
            # SIP002 form: ss://method:password@host:port or
            # legacy form: ss://BASE64(method:password@host:port)
            authority = parsed.netloc
            if "@" not in authority:
                decoded = _decode_b64(parsed.netloc.split("#", 1)[0])
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
        "share_link": raw,
        "metadata": {}
    }

def parse_text(text, source_id="manual"):
    """Parse newline-separated links; malformed lines are counted by caller."""
    nodes, errors = [], []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            node = parse_link(line, source_id=source_id)
            if node:
                nodes.append(node)
        except Exception as exc:
            # Error text intentionally excludes the original line/credentials.
            errors.append({"line": number, "reason": str(exc)})
    unique = {node["id"]: node for node in nodes}
    return sorted(unique.values(), key=lambda n: (n["protocol"], n["endpoint"]["host"], n["endpoint"]["port"])), errors
