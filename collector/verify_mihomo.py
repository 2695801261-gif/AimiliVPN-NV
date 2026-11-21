"""Verify public Clash candidates with a real Mihomo tunnel and public egress check."""
import argparse
import ipaddress
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml


def build_config(proxy, mixed_port):
    """Build an isolated config where every request must use this single proxy."""
    return {
        "mixed-port": mixed_port,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "error",
        "ipv6": False,
        "proxies": [proxy],
        "proxy-groups": [{"name": "VERIFY", "type": "select", "proxies": [proxy["name"]]}],
        "rules": ["MATCH,VERIFY"],
    }


def parse_public_ip(value):
    try:
        address = ipaddress.ip_address(value.strip())
    except (ValueError, AttributeError):
        return None
    if not address.is_global:
        return None
    return str(address)


def wait_for_listener(host, port, process, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Mihomo exited before opening its local proxy port")
        try:
            with socket.create_connection((host, port), timeout=0.4):
                return
        except OSError:
            time.sleep(0.15)
    raise TimeoutError("Mihomo local proxy port did not become ready")


def request_egress(port, timeout):
    proxy_url = f"http://127.0.0.1:{port}"
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
    )
    request = urllib.request.Request(
        "https://api.ipify.org",
        headers={"User-Agent": "AimiliVPN-NV-verifier/0.1"},
    )
    with opener.open(request, timeout=timeout) as response:
        value = response.read(128).decode("ascii", errors="replace")
    address = parse_public_ip(value)
    if not address:
        raise RuntimeError("Egress endpoint did not return a globally routable IP")
    return address


def verify_one(proxy, mihomo_bin, mixed_port, startup_timeout, request_timeout):
    name = str(proxy.get("name") or "unnamed")
    with tempfile.TemporaryDirectory(prefix="aimili-mihomo-") as workdir:
        config_path = Path(workdir) / "config.yaml"
        config_path.write_text(
            yaml.safe_dump(build_config(proxy, mixed_port), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        check = subprocess.run(
            [mihomo_bin, "-t", "-d", workdir, "-f", str(config_path)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if check.returncode != 0:
            detail = (check.stderr or check.stdout or "config validation failed")[-500:]
            raise RuntimeError(f"Mihomo config invalid: {detail}")

        process = subprocess.Popen(
            [mihomo_bin, "-d", workdir, "-f", str(config_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_for_listener("127.0.0.1", mixed_port, process, startup_timeout)
            return {
                "name": name,
                "type": proxy.get("type"),
                "server": proxy.get("server"),
                "port": proxy.get("port"),
                "egress_ip": request_egress(mixed_port, request_timeout),
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "status": "verified",
                "proxy": proxy,
            }
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="public-clash-candidates.json")
    parser.add_argument("--output", default="verified-clash-candidates.json")
    parser.add_argument("--mihomo", default=os.environ.get("MIHOMO_BIN", "mihomo"))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--port", type=int, default=17890)
    parser.add_argument("--startup-timeout", type=float, default=8)
    parser.add_argument("--request-timeout", type=float, default=10)
    args = parser.parse_args()

    source = json.loads(Path(args.input).read_text(encoding="utf-8"))
    candidates = source.get("proxies", [])
    verified, failures = [], []
    for index, proxy in enumerate(candidates[: max(0, args.limit)]):
        try:
            result = verify_one(
                proxy, args.mihomo, args.port, args.startup_timeout, args.request_timeout
            )
            verified.append(result)
            print(f"[verified] {result['name']} -> {result['egress_ip']}")
        except Exception as exc:
            name = str(proxy.get("name") or f"candidate-{index + 1}")
            failures.append({"name": name, "reason": f"{type(exc).__name__}: {exc}"})
            print(f"[failed] {name}: {type(exc).__name__}: {exc}")

    payload = {
        "schema_version": 1,
        "source": source.get("source"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(candidates),
        "tested_count": min(len(candidates), max(0, args.limit)),
        "verified_count": len(verified),
        "status": "egress_verified" if verified else "no_verified_nodes",
        "proxies": [item["proxy"] for item in verified],
        "verification": [
            {key: value for key, value in item.items() if key != "proxy"} for item in verified
        ],
        "failures": failures,
    }
    Path(args.output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"Verified {len(verified)}/{payload['tested_count']} candidates; "
        f"saved {args.output}"
    )


if __name__ == "__main__":
    main()
