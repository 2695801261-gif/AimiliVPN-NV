# AimiliVPN-NV

A small personal node collector. The target is one person's light use, not a public node directory or a large-scale VPN service.

## Current implementation

- Fetches the public VPNGate listing.
- Fetches up to 50 proxy candidates from a public Clash/Mihomo YAML feed (two public Clash/Mihomo feeds (nodesfree and 735754647/Free-Nodes, tried in order)), preserving protocol-specific fields for later Mihomo checks.
- Parses its OpenVPN profiles, normalizes endpoint metadata, and removes duplicate endpoints.
- Runs a small Python unit-test suite in GitHub Actions.
- Optionally stores the latest candidate snapshot in a dedicated Cloudflare Worker KV namespace.

## Important protocol limitation

VPNGate currently supplies OpenVPN profiles. OpenVPN is not a Clash/Mihomo proxy protocol, and an OpenVPN endpoint must not be converted into a fake `proxies:` entry. The current `/api/subscription` endpoint returns authenticated JSON candidate data; it is not yet a Clash subscription URL and does not establish a VPN tunnel.

Two public Clash/Mihomo-compatible candidate feeds are wired as primary/fallback inputs to the scheduled collector. The collector accepts the first feed that downloads and yields supported proxy entries; it does not merge or blindly trust every source. These are still untrusted, pending candidates: this project has not yet run its own Mihomo config validation or real proxy/egress test, so it does not publish them as working nodes or claim that a finished personal subscription is ready.

## Personal-use scope

Keep the implementation intentionally small:
- One or a few sources, rather than a large historical candidate pool.
- Deduplicate and classify by country/protocol.
- Publish only formats that match the actual source protocol.
- Do not label ping/port reachability as a successful VPN connection.
- No Android app, public multi-user service, large-scale rotation, or 1,000-node target in this milestone.

## Local checks

Python 3.11+; standard library only.

    python -m unittest discover -s collector/tests -v
    python collector/main.py --source sample --output nodes.json

Fetch live VPNGate data:

    python collector/main.py --source vpngate --output nodes.json

## Cloudflare setup (optional)

1. Use a dedicated KV namespace for this project.
2. Set the Worker secret `ADMIN_TOKEN`; never commit it.
3. Deploy from `worker/`.
4. Add GitHub Actions secrets `WORKER_URL` and `WORKER_ADMIN_TOKEN` if snapshot publishing is wanted.

## API

- `GET /api/status`: public health/version.
- `GET /api/nodes`, `GET /api/nodes/{id}`, `GET /api/stats`: authenticated candidate data.
- `POST /api/nodes/import`: authenticated snapshot import.
- `GET /api/subscription`: authenticated JSON snapshot only; not a Clash/Mihomo subscription.

Protected routes require `Authorization: Bearer <ADMIN_TOKEN>`.

## Security

Public VPN profiles are untrusted. Never commit credentials or private profiles. Only a real protocol tunnel plus egress verification can be called a verified connection. Use public endpoints only where permitted.
See `docs/SECURITY.md`.
