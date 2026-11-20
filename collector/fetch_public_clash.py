"""Fetch a small public Clash/Mihomo candidate snapshot (not a live subscription)."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from collector.sources.public_clash import fetch_candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="public-clash-candidates.json")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    source_url, proxies = fetch_candidates(limit=max(1, min(args.limit, 100)))
    payload = {
        "schema_version": 1,
        "source": source_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(proxies),
        "status": "pending_mihomo_egress_verification",
        "proxies": proxies,
    }
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Fetched {len(proxies)} Mihomo-compatible candidates -> {args.output}")


if __name__ == "__main__":
    main()
