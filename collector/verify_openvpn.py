"""Real OpenVPN tunnel verifier. Reachability alone is never a pass."""
import argparse
import ipaddress
import json
import os
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# Only harmless OpenVPN directives are copied from public profiles. Unknown directives
# and all script/plugin/config hooks are discarded to avoid executing source-supplied code.
SAFE = {"client", "dev", "proto", "remote", "resolv-retry", "nobind", "persist-key",
        "persist-tun", "remote-cert-tls", "cipher", "data-ciphers", "auth", "verb",
        "mute", "key-direction", "connect-retry", "connect-retry-max", "explicit-exit-notify",
        "auth-nocache", "tls-version-min", "tun-mtu", "reneg-sec"}
BLOCKS = {"ca", "cert", "key", "tls-auth", "tls-crypt", "pkcs12", "extra-certs"}

def safe_config(profile, host, port, transport):
    if not profile:
        raise ValueError("missing OpenVPN profile")
    lines = profile.splitlines()
    out, block, body = [], None, []
    for line in lines:
        s = line.strip()
        if s.startswith("<") and s.endswith(">") and not s.startswith("</"):
            name = s[1:-1].lower()
            if name in BLOCKS:
                block = name
                body = [line]
            continue
        if block:
            body.append(line)
            if s.lower() == f"</{block}>":
                out.extend(body)
                block, body = None, []
            continue
        if not s or s.startswith(("#", ";")):
            continue
        key = s.split(None, 1)[0].lower()
        if key not in SAFE or key in {"dev", "proto", "remote"}:
            continue
        out.append(s)
    proto = "udp" if transport == "udp" else "tcp-client"
    out.extend([f"remote {host} {port}", f"proto {proto}", "client", "dev tun",
                "nobind", "persist-key", "persist-tun", "resolv-retry 3",
                "connect-retry-max 1", "connect-timeout 12", "auth-nocache", "verb 3"])
    return "\n".join(out) + "\n"

def verify_one(node, timeout=22):
    result = dict(node)
    checked = datetime.now(timezone.utc).isoformat()
    result["last_checked_at"] = checked
    result["verification"] = {"method": "openvpn_tunnel_and_egress", "tunnel": False,
                              "egress_verified": False, "dns_check": False}
    if not shutil.which("openvpn") or not shutil.which("curl") or not shutil.which("ip"):
        result["status"] = "failed"
        result["verification"]["reason"] = "required_tool_missing"
        return result
    ep = node.get("endpoint") or {}
    host, port = ep.get("host"), ep.get("port")
    transport = node.get("transport")
    if not host or not isinstance(port, int) or transport not in ("udp", "tcp"):
        result["status"] = "failed"
        result["verification"]["reason"] = "invalid_endpoint_or_transport"
        return result
    try:
        ipaddress.ip_address(host)
    except ValueError:
        # Domain endpoints are allowed; OpenVPN resolves them itself.
        pass
    try:
        cfg = safe_config(node.get("profile"), host, port, transport)
        with tempfile.TemporaryDirectory(prefix="aimili-vpn-") as td:
            conf = Path(td) / "node.ovpn"
            log = Path(td) / "openvpn.log"
            conf.write_text(cfg, encoding="utf-8")
            proc = subprocess.Popen(["sudo", "openvpn", "--config", str(conf), "--log", str(log)],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                deadline = time.monotonic() + timeout
                egress = None
                while time.monotonic() < deadline and proc.poll() is None:
                    route = subprocess.run(["ip", "route", "get", "1.1.1.1"], capture_output=True,
                                           text=True, timeout=3)
                    if route.returncode == 0 and "dev tun" in route.stdout:
                        result["verification"]["tunnel"] = True
                        check = subprocess.run(["curl", "--fail", "--silent", "--show-error",
                                                "--max-time", "5", "--interface", "tun0",
                                                "https://api.ipify.org"], capture_output=True,
                                               text=True, timeout=7)
                        if check.returncode == 0:
                            try:
                                egress = str(ipaddress.ip_address(check.stdout.strip()))
                                break
                            except ValueError:
                                pass
                    time.sleep(1)
                if egress:
                    result["verification"].update({"egress_verified": True, "egress_ip": egress})
                    # A DNS-over-HTTPS hostname lookup through the tunnel interface must work.
                    dns = subprocess.run(["curl", "--fail", "--silent", "--max-time", "6",
                                          "--interface", "tun0", "https://cloudflare-dns.com/dns-query",
                                          "-H", "accept: application/dns-message"],
                                         capture_output=True, timeout=8)
                    result["verification"]["dns_check"] = dns.returncode == 0
                    result["status"] = "verified_connected" if result["verification"]["dns_check"] else "failed"
                    result["egress_ip"] = egress if result["status"] == "verified_connected" else None
                    if result["status"] != "verified_connected":
                        result["verification"]["reason"] = "dns_over_tunnel_failed"
                else:
                    result["status"] = "failed"
                    result["verification"]["reason"] = "tunnel_or_egress_timeout"
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=2)
    except Exception as exc:
        result["status"] = "failed"
        result["verification"]["reason"] = type(exc).__name__ + ": " + str(exc)[:180]
    return result

def verify_batch(nodes, workers=8):
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(verify_one, n) for n in nodes]
        for future in as_completed(futures):
            results.append(future.result())
    return results

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="rotation.json")
    p.add_argument("--output", default="verified.json")
    args = p.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    results = verify_batch(data.get("nodes", []))
    Path(args.output).write_text(json.dumps({"count":len(results),"nodes":results}, indent=2), encoding="utf-8")
    passed = sum(n.get("status") == "verified_connected" for n in results)
    print(f"Tunnel verification: {passed}/{len(results)} passed")
    if any(n.get("status") == "verified_connected" for n in results):
        return
    # Empty pass is valid operationally; it must never publish unverified nodes.
if __name__ == "__main__":
    main()
