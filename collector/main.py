import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from collector.normalize import normalize_rows
from collector.sources.vpngate import fetch_csv, parse_csv

SAMPLE = "#HostName,IP,Score,Ping,Speed,CountryLong,CountryShort,NumVpnSessions,OpenVPN_ConfigData_Base64,Port,Message\nsample,198.51.100.10,10,30,1000000,Example,EX,1,,1194,\n"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", choices=("vpngate", "sample"), default="vpngate")
    p.add_argument("--output", default="nodes.json")
    args = p.parse_args()
    raw = SAMPLE if args.source == "sample" else fetch_csv()
    nodes = normalize_rows(parse_csv(raw))
    payload = {"schema_version": 1, "source": args.source, "generated_at": datetime.now(timezone.utc).isoformat(), "count": len(nodes), "nodes": nodes}
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Collected {len(nodes)} unique {args.source} nodes -> {args.output}")

if __name__ == "__main__":
    main()
