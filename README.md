# AimiliVPN-NV

A small personal node collector for one person's light use. This is not a public VPN gateway or a public node directory.

## Current pipeline

Every 12 hours (and on manual dispatch or a push to `main`), GitHub Actions:

1. Fetches VPNGate OpenVPN profiles. VPNGate puts the port inside the Base64-encoded OpenVPN profile's `remote` line; the collector extracts it instead of relying on a non-existent CSV `Port` column.
2. Fetches up to 50 candidates from public Clash/Mihomo YAML feeds.
3. Tests up to 20 candidates with the official Mihomo binary. A candidate is verified only after Mihomo config validation, proxy startup, and a real public egress-IP response through that proxy.
4. Builds a standard Mihomo YAML subscription from verified entries only.
5. Publishes the subscription to the Cloudflare Worker when the required GitHub Actions secrets are configured.
6. Uploads redacted summaries only. Proxy passwords, UUIDs, private keys, OpenVPN profiles and subscription YAML are not included in public Git commits or workflow artifacts.

## Verification rules

- Parsing a proxy config or reaching its TCP port is not a successful verification.
- Only a globally routable IP returned through the Mihomo proxy is accepted.
- Failed candidates are excluded from the subscription.
- An empty or invalid new snapshot is rejected; it must not replace the last known-good subscription.
- VPNGate OpenVPN profiles remain OpenVPN. They are never mislabeled as Clash/Mihomo proxy entries.
- Country names in source labels are not treated as verified geolocation. Egress country needs a separate IP-geolocation check.

## Cloudflare Worker setup

The Worker uses the existing `NODES` KV binding in `worker/wrangler.toml`.

1. Deploy the updated Worker from the `worker/` directory (or replace the Worker script in the Cloudflare dashboard with `worker/src/index.js`).
2. Keep the Worker secret `ADMIN_TOKEN` configured. It is used for CI imports and protected management APIs.
3. Add a separate Worker secret named `SUBSCRIPTION_TOKEN`. It protects the read-only subscription URL `/sub/<SUBSCRIPTION_TOKEN>`. Do not put the token in this repository.
4. In GitHub repository Settings → Secrets and variables → Actions, add:
   - `WORKER_URL`: the Worker base URL, without a trailing slash.
   - `WORKER_ADMIN_TOKEN`: the exact same value as the Worker `ADMIN_TOKEN` secret.
5. Once deployed and configured, the private Mihomo subscription URL is:
   `https://<your-worker-host>/sub/<SUBSCRIPTION_TOKEN>`

The read-only subscription endpoint returns YAML with `Content-Type: text/yaml`. It does not require a custom HTTP header, so it can be imported as a remote subscription in Mihomo/Clash clients. The token in the URL acts as a password; keep it private.

## Worker API

- `GET /api/status`: public health/version.
- `GET /api/nodes`, `GET /api/nodes/{id}`, `GET /api/stats`: authenticated VPNGate snapshot data.
- `POST /api/nodes/import`: authenticated VPNGate snapshot import; empty snapshots are refused.
- `GET /api/subscription`: authenticated JSON snapshot (not the Mihomo YAML subscription).
- `POST /api/mihomo/import`: authenticated verified-only YAML import.
- `GET /api/mihomo/status`: authenticated Mihomo publication metadata.
- `GET /sub/{token}`: token-protected read-only Mihomo YAML subscription.

This Worker stores data in KV. It is not a VPN tunnel gateway and does not itself relay user traffic.

## Local checks

Python 3.11+ and PyYAML 6.x:

```sh
python -m pip install 'PyYAML>=6,<7'
python -m unittest discover -s collector/tests -v
python -m collector.main --source sample --output nodes.json
python -m collector.fetch_public_clash --output public-clash-candidates.json --limit 50
python collector/verify_mihomo.py --mihomo ./mihomo --input public-clash-candidates.json --output verified-clash-candidates.json --limit 20
python -m collector.build_subscription --input verified-clash-candidates.json --output mihomo-subscription.yaml
```

## Personal-use scope

- A small verified pool is preferred over thousands of untested nodes.
- Use public endpoints and public proxy sources only where permitted.
- Do not commit live proxy credentials, generated subscriptions, private profiles, Worker secrets, or tokens.
- The repository is public; treat every committed file and workflow artifact as public.
