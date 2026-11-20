"""Validation for the explicit public-source allowlist."""
import json
import re
from urllib.parse import urlsplit

SOURCE_FORMATS = {
    "share_links_text",
    "share_links_base64",
    "clash_yaml",
    "singbox_json",
    "openvpn_ovpn",
    "wireguard_conf",
}
SOURCE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")

def validate_registry(document):
    if not isinstance(document, dict) or document.get("version") != 1:
        raise ValueError("unsupported source registry version")
    sources = document.get("sources")
    if not isinstance(sources, list):
        raise ValueError("sources must be a list")
    seen = set()
    normalized = []
    for item in sources:
        if not isinstance(item, dict):
            raise ValueError("source entry must be an object")
        source_id = item.get("id")
        if not isinstance(source_id, str) or not SOURCE_ID.fullmatch(source_id):
            raise ValueError("invalid source id")
        if source_id in seen:
            raise ValueError("duplicate source id")
        seen.add(source_id)
        url = item.get("url")
        parsed = urlsplit(url if isinstance(url, str) else "")
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("source URL must use HTTPS")
        fmt = item.get("format")
        if fmt not in SOURCE_FORMATS:
            raise ValueError("unsupported source format")
        if not isinstance(item.get("license_note"), str) or not item["license_note"].strip():
            raise ValueError("license_note is required")
        enabled = item.get("enabled", False)
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be boolean")
        normalized.append({
            "id": source_id,
            "url": url,
            "format": fmt,
            "enabled": enabled,
            "license_note": item["license_note"].strip()
        })
    return normalized

def load_registry(path):
    with open(path, "r", encoding="utf-8") as stream:
        return validate_registry(json.load(stream))
