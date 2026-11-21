"""Fetch and merge public Clash/Mihomo feeds without trusting their health claims."""
import json
import urllib.request

PUBLIC_CLASH_URLS = (
    "https://nodesfree.github.io/clashnode/clash.yaml",
    "https://735754647.github.io/Free-Nodes/clash.yaml",
    "https://github.com/learnLi/free-nodes/releases/latest/download/list.meta.cn.yml",
)
PUBLIC_CLASH_URL = PUBLIC_CLASH_URLS[0]
SUPPORTED_TYPES = {"ss", "vmess", "vless", "trojan", "hysteria", "hysteria2", "tuic", "anytls"}


def fetch_text(url, timeout=25, max_bytes=4 * 1024 * 1024):
    request = urllib.request.Request(url, headers={"User-Agent": "AimiliVPN-NV/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError(f"Feed exceeds {max_bytes} bytes: {url}")
    return raw.decode("utf-8-sig", errors="replace")


def parse_proxies(text, limit=50):
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to parse public Clash YAML") from exc

    document = yaml.safe_load(text)
    if not isinstance(document, dict) or not isinstance(document.get("proxies"), list):
        raise ValueError("Source did not contain a Clash YAML proxies list")
    if limit < 1:
        return []

    unique = {}
    for item in document["proxies"]:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("type", "")).lower()
        server = item.get("server")
        port = item.get("port")
        if kind not in SUPPORTED_TYPES or not isinstance(server, str) or not server.strip():
            continue
        if isinstance(port, bool):
            continue
        try:
            port = int(port)
        except (TypeError, ValueError):
            continue
        if not 1 <= port <= 65535:
            continue
        # Preserve protocol-specific credentials and TLS/transport settings verbatim.
        proxy = dict(item)
        proxy["port"] = port
        key = json.dumps(proxy, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        unique.setdefault(key, proxy)
        if len(unique) >= limit:
            break
    return list(unique.values())


def fetch_candidates(limit=50, urls=PUBLIC_CLASH_URLS):
    """Merge healthy feeds fairly; one unavailable source must not block the others."""
    if limit < 1:
        return "", []
    errors, successful_sources, source_pools = [], [], []
    for url in urls:
        try:
            text = fetch_text(url)
            proxies = parse_proxies(text, limit=limit)
            if not proxies:
                raise ValueError("Feed contained no supported proxies")
            successful_sources.append(url)
            source_pools.append(proxies)
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")

    # Round-robin across feeds so the first large feed cannot starve later sources.
    merged, seen = [], set()
    max_items = max((len(pool) for pool in source_pools), default=0)
    for index in range(max_items):
        for pool in source_pools:
            if index >= len(pool):
                continue
            proxy = pool[index]
            key = json.dumps(proxy, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            if key in seen:
                continue
            seen.add(key)
            merged.append(proxy)
            if len(merged) >= limit:
                break
        if len(merged) >= limit:
            break

    if not merged:
        raise RuntimeError("All public Clash feeds failed: " + " | ".join(errors))

    # Spend the bounded verification budget on modern Reality candidates first.
    # This is only a test-order preference, never a health or trust assertion.
    def protocol_priority(proxy):
        kind = str(proxy.get("type", "")).lower()
        reality = isinstance(proxy.get("reality-opts"), dict)
        flow = str(proxy.get("flow", "")).lower()
        if kind == "vless" and reality and flow == "xtls-rprx-vision":
            return 0
        if kind == "vless" and reality:
            return 1
        if kind == "vless":
            return 2
        if kind in {"hysteria2", "tuic", "anytls"}:
            return 3
        return 4

    merged.sort(key=protocol_priority)
    return ";".join(successful_sources), merged
