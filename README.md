# AimiliVPN-NV

A small personal node collector. The target is one person's light use, not a public node directory or a large-scale VPN service.

## Current implementation

- Fetches the public VPNGate listing.
- Parses its OpenVPN profiles, normalizes endpoint metadata, and removes duplicate endpoints.
- Runs a small Python unit-test suite in GitHub Actions.
- Optionally stores the latest candidate snapshot in a dedicated Cloudflare Worker KV namespace.

## Important protocol limitation

VPNGate currently supplies OpenVPN profiles. OpenVPN is not a Clash/Mihomo proxy protocol, and an OpenVPN endpoint must not be converted into a fake `proxies:` entry. The current `/api/subscription` endpoint returns authenticated JSON candidate data; it is not yet a Clash subscription URL and does not establish a VPN tunnel.

A Clash/Mihomo subscription requires actual Clash-compatible proxy nodes (for example, a source that provides a supported proxy URI/config), followed by Mihomo config validation and a real proxy/egress check. Until such a source is identified and tested, this project must not claim that a Clash subscription is ready.

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
