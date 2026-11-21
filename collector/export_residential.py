"""Export live US residential/ISP SOCKS5 proxies as importable chain upstreams.

The upstream pool is public and unauthenticated. "Residential" is a source-side
classification; this exporter independently requires US + hosting=false +
mobile=false + presence in the live SOCKS5 list.
"""
import argparse
import csv
import io
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

BASE = "https://raw.githubusercontent.com/fmw86/free-proxy-pool/main/"
SOURCES = {
    "detail": BASE + "socks5_residential_detail.csv",
    "alive": BASE + "socks5_alive.txt",
    "residential": BASE + "socks5_residential.txt",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "AimiliVPN-NV-residential-export/1.0"})
    with urllib.request.urlopen(req, timeout=35) as response:
        data = response.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024:
        raise ValueError("source exceeds 8 MiB")
    return data.decode("utf-8-sig")


def truth(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def collect():
    detail_text = fetch(SOURCES["detail"])
    alive_text = fetch(SOURCES["alive"])
    residential_text = fetch(SOURCES["residential"])
    alive = {line.strip() for line in alive_text.splitlines() if line.strip()}
    residential = {line.strip() for line in residential_text.splitlines() if line.strip()}
    candidates = []
    seen = set()
    for row in csv.DictReader(io.StringIO(detail_text)):
        endpoint = (row.get("proxy") or "").strip()
        if not endpoint or endpoint not in alive or endpoint not in residential:
            continue
        if (row.get("country") or "").strip().lower() != "united states":
            continue
        if truth(row.get("hosting")) or truth(row.get("mobile")):
            continue
        if ":" not in endpoint:
            continue
        host, port_text = endpoint.rsplit(":", 1)
        try:
            port = int(port_text)
        except ValueError:
            continue
        if not host or not 1 <= port <= 65535 or endpoint in seen:
            continue
        isp = (row.get("isp") or row.get("org") or "US ISP").strip()
        asn = (row.get("asn") or "").strip()
        city = (row.get("city") or "").strip()
        region = (row.get("region") or "").strip()
        name_parts = ["US", isp]
        if city:
            name_parts.append(city)
        name = " - ".join(name_parts)
        candidates.append({
            "name": name, "server": host, "port": port,
            "isp": isp, "asn": asn, "city": city, "region": region,
            "country": "United States",
        })
        seen.add(endpoint)
    candidates.sort(key=lambda p: (p["isp"].lower(), p["region"].lower(), p["city"].lower(), p["server"]))
    return candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="dist")
    args = parser.parse_args()
    nodes = collect()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    # A minimal Mihomo-compatible config, suitable as a node source for chaining.
    yaml_lines = [
        "# Auto-generated. Public unauthenticated SOCKS5 proxies; do not use for sensitive accounts.",
        f"# Generated at: {generated}",
        "proxies:",
    ]
    uri_lines = [
        "# Auto-generated SOCKS5 URIs for NekoBox / compatible clients.",
        f"# Generated at: {generated}",
        "# Public unauthenticated proxies; availability and ISP classification can change.",
    ]
    for index, node in enumerate(nodes, 1):
        name = f"US-ISP-{index:03d} {node['isp']} {node['city']}".strip()
        yaml_lines.extend([
            f"  - name: {json.dumps(name, ensure_ascii=False)}",
            "    type: socks5",
            f"    server: {node['server']}",
            f"    port: {node['port']}",
            "    udp: true",
        ])
        uri_lines.append(
            f"socks5://{node['server']}:{node['port']}#{quote(name, safe='')}"
        )

    (out / "us-residential-socks5.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")
    (out / "us-residential-socks5.txt").write_text("\n".join(uri_lines) + "\n", encoding="utf-8")
    summary = {
        "generated_at": generated,
        "count": len(nodes),
        "criteria": ["United States", "hosting=false", "mobile=false", "in socks5_alive.txt", "in socks5_residential.txt"],
        "source": SOURCES,
        "nodes": nodes,
    }
    (out / "us-residential-socks5.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"US residential SOCKS5 candidates exported: {len(nodes)}")
    print(f"Generated at: {generated}")
    for node in nodes:
        print(f"{node['server']}:{node['port']} | {node['isp']} | {node['city']}, {node['region']} | {node['asn']}")
    if not nodes:
        raise SystemExit("No qualifying US residential SOCKS5 proxies; refusing to publish an empty list.")


if __name__ == "__main__":
    main()
