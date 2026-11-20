"""Fetch and admit candidates from a public Mihomo/Clash YAML feed.

Candidates remain unverified until the project runs its own Mihomo egress checks.
"""
import json
import urllib.request

PUBLIC_CLASH_URL = "https://radarhub.top/clash.yaml"
SUPPORTED_TYPES = {"ss", "vmess", "vless", "trojan", "hysteria", "hysteria2", "tuic", "anytls"}


def fetch_text(url=PUBLIC_CLASH_URL, timeout=25):
    request = urllib.request.Request(url, headers={"User-Agent": "AimiliVPN-NV/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(4 * 1024 * 1024).decode("utf-8-sig", errors="replace")


def parse_proxies(text, limit=50):
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to parse public Clash YAML") from exc

    document = yaml.safe_load(text)
    if not isinstance(document, dict) or not isinstance(document.get("proxies"), list):
        raise ValueError("Source did not contain a Clash YAML proxies list")

    unique = {}
    for item in document["proxies"]:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("type", "")).lower()
        server = item.get("server")
        try:
            port = int(item.get("port"))
        except (TypeError, ValueError):
            continue
        if kind not in SUPPORTED_TYPES or not isinstance(server, str) or not server.strip():
            continue
        if not 1 <= port <= 65535:
            continue
        # Keep protocol-specific fields intact; do not reconstruct credentials.
        key = json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        unique.setdefault(key, item)
        if len(unique) >= limit:
            break
    return list(unique.values())
