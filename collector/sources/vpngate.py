"""VPNGate source: its published connection profiles are OpenVPN, not SSTP."""
import csv
import io
import urllib.request

URLS = ("https://www.vpngate.net/api/iphone/",)

def fetch_csv(timeout=20):
    request = urllib.request.Request(URLS[0], headers={"User-Agent": "AimiliVPN-NV/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        text = response.read(8 * 1024 * 1024).decode("utf-8-sig", errors="replace")
    if "OpenVPN_ConfigData_Base64" not in text and "#HostName" not in text:
        raise ValueError("Response did not resemble the VPNGate CSV format")
    return text

def parse_csv(text):
    lines = [line for line in text.splitlines() if line and not line.startswith("*") and (not line.startswith("#") or line.lower().startswith("#hostname"))]
    return list(csv.DictReader(io.StringIO("\n".join(lines)))) if lines else []
