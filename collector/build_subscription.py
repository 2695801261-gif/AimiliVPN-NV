"""Build a Mihomo YAML subscription from egress-verified proxy records only."""
import argparse
import json
import re
from pathlib import Path

import yaml


def build_subscription(snapshot):
    proxies = snapshot.get("proxies") if isinstance(snapshot, dict) else None
    verification = snapshot.get("verification") if isinstance(snapshot, dict) else None
    if not isinstance(proxies, list) or not isinstance(verification, list):
        raise ValueError("verified snapshot must contain proxies and verification arrays")
    if not proxies or len(proxies) != len(verification):
        raise ValueError("refusing to publish an empty or inconsistent verified snapshot")
    if snapshot.get("verified_count") != len(proxies) or any(
        not isinstance(item, dict) or item.get("status") != "verified" for item in verification
    ):
        raise ValueError("snapshot contains entries without successful egress verification")

    output, names = [], set()
    for index, source in enumerate(proxies, 1):
        # Fail closed: never silently drop a malformed entry while retaining the
        # original verified_count, which could make publication metadata inaccurate.
        if not isinstance(source, dict):
            raise ValueError(f"verified proxy entry {index} is not an object")
        proxy = dict(source)
        if not isinstance(proxy.get("server"), str) or not proxy["server"].strip():
            raise ValueError(f"verified proxy entry {index} has no valid server")
        if isinstance(proxy.get("port"), bool) or not isinstance(proxy.get("port"), int) or not 1 <= proxy["port"] <= 65535:
            raise ValueError(f"verified proxy entry {index} has no valid port")
        if not isinstance(proxy.get("type"), str) or not proxy["type"].strip():
            raise ValueError(f"verified proxy entry {index} has no valid type")

        base = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(proxy.get("name") or f"Verified-{index}")).strip("-.")
        if not base:
            base = f"Verified-{index}"
        name, suffix = base, 2
        while name in names:
            name = f"{base}-{suffix}"
            suffix += 1
        names.add(name)
        proxy["name"] = name
        output.append(proxy)

    if len(output) != snapshot["verified_count"]:
        raise ValueError("published proxy count does not match verified_count")

    proxy_names = [item["name"] for item in output]
    document = {
        "mixed-port": 7890,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "info",
        "ipv6": False,
        "proxies": output,
        "proxy-groups": [
            {
                "name": "Aimili Auto",
                "type": "url-test",
                "proxies": proxy_names,
                "url": "https://www.gstatic.com/generate_204",
                "interval": 600,
                "tolerance": 150,
            },
            {
                "name": "Aimili Select",
                "type": "select",
                "proxies": ["Aimili Auto", *proxy_names],
            },
        ],
        "rules": ["MATCH,Aimili Select"],
    }
    return yaml.safe_dump(document, allow_unicode=True, sort_keys=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="verified-clash-candidates.json")
    parser.add_argument("--output", default="mihomo-subscription.yaml")
    args = parser.parse_args()
    snapshot = json.loads(Path(args.input).read_text(encoding="utf-8"))
    content = build_subscription(snapshot)
    # Reparse before writing so malformed YAML never reaches the publisher.
    parsed = yaml.safe_load(content)
    if not isinstance(parsed, dict) or not parsed.get("proxies"):
        raise ValueError("generated Mihomo YAML failed structural validation")
    Path(args.output).write_text(content, encoding="utf-8")
    print(f"Built Mihomo subscription with {len(parsed['proxies'])} verified proxies")


if __name__ == "__main__":
    main()
