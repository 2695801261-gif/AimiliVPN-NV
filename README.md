# AimiliVPN-NV

A small personal node collector. The target is one person's light use, not a public node directory or a large-scale VPN service.

## Current implementation

- Fetches the public VPNGate listing.
- Fetches up to 50 proxy candidates from two public Clash/Mihomo YAML feeds (nodesfree first, 735754647/Free-Nodes as fallback), preserving protocol-specific fields for later Mihomo checks.
- Parses its OpenVPN profiles, normalizes endpoint metadata, and removes duplicate endpoints.
- Runs a small Python unit-test suite in GitHub Actions.
- Uses the official Mihomo Linux binary to validate candidate configs, start one proxy at a time, and check a public egress-IP endpoint; only candidates that pass both config validation and proxied egress are written to the verified snapshot.
- Optionally stores the latest candidate snapshot in a dedicated Cloudflare Worker KV namespace.

## Important protocol limitation

VPNGate currently supplies OpenVPN profiles. OpenVPN is not a Clash/Mihomo proxy protocol, and an OpenVPN endpoint must not be converted into a fake `proxies:` entry. The current `/api/subscription` endpoint returns authenticated JSON candidate data; it is not yet a Clash subscription URL and does not establish a VPN tunnel.

Two public Clash/Mihomo-compatible candidate feeds are wired as primary/fallback inputs to the scheduled collector. The collector accepts the first feed that downloads and yields supported proxy entries; it does not merge or blindly trust every source. Candidates are tested one at a time by Mihomo in GitHub Actions (currently capped at 20 per run). The verifier runs Mihomo's config test, starts an isolated local HTTP proxy for that one candidate, and requests a public IP through that proxy. It writes `verified-clash-candidates.json` separately; candidates that only pass parsing or port checks are never promoted. The verifier's nine local unit tests pass. The hosted workflow has not yet executed: GitHub reports `runner_id: 0`, an empty step list, and no job log, which means no hosted runner was assigned. This is an account/GitHub Actions dispatch blocker rather than a Mihomo runtime failure; check the repository owner's Actions usage/budget and payment status before interpreting any hosted verification result.

## Personal-use scope

Keep the implementation intentionally small:
- One or a few sources, rather than a large historical candidate pool.
- Deduplicate and classify by country/protocol.
- Publish only formats that match the actual source protocol.
- Do not label ping/port reachability as a successful VPN connection.
- No Android app, public multi-user service, large-scale rotation, or 1,000-node target in this milestone.

## Local checks

Python 3.11+ and PyYAML 6.x (`python -m pip install 'PyYAML>=6,<7'`).

    python -m unittest discover -s collector/tests -v
    python collector/verify_mihomo.py --mihomo ./mihomo --input public-clash-candidates.json --output verified-clash-candidates.json --limit 20
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
