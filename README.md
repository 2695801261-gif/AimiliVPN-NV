# AimiliVPN-NV

Independent no-VPS personal VPN node management system. This project independently implements publicly described concepts; it does not copy proprietary AimiliVPN modules.

## Phase 1

The first milestone provides a shared four-protocol data model, a VPNGate OpenVPN collector, a Cloudflare Worker API backed by a dedicated KV namespace, and GitHub Actions automation. It does not yet provide VPN tunnels or an Android APK.

## Architecture

- GitHub Actions / collector: fetch and normalize public VPNGate OpenVPN listings.
- Cloudflare Worker / KV: authenticated management API and latest node snapshot.
- Android (later): Android VpnService plus separately implemented and validated protocol adapters. The phone connects to real VPN endpoints; the Worker is not a VPN gateway.

## Protocol accuracy

The model reserves openvpn, sstp, softether, and l2tp_ipsec. VPNGate's initial source supplies OpenVPN profiles only. OpenVPN over TCP remains OpenVPN; TCP is a transport, not SSTP. Do not relabel records.

Android 13 removed the platform's built-in L2TP/IPsec VPN client. Target-device support requires a separately verified implementation and is not promised in this phase.

## Layout

- collector/: VPNGate fetch, parser, normalization, tests.
- worker/: Cloudflare Worker API and KV storage.
- schemas/: shared node schema.
- protocols/: adapter contract and capability notes.
- .github/workflows/: scheduled/manual collection and publishing.
- docs/: phase and security notes.

## Local checks

Python 3.11+; standard library only.

    python -m unittest discover -s collector/tests -v
    python collector/main.py --source sample --output nodes.json

Fetch live VPNGate data:

    python collector/main.py --source vpngate --output nodes.json

## Cloudflare setup (later in Phase 1)

1. Create a NEW KV namespace dedicated to this project. Do not reuse another project's namespace.
2. In worker/wrangler.toml replace the placeholder namespace ID.
3. Set Worker secret ADMIN_TOKEN with Wrangler; never commit it.
4. Deploy from worker/.
5. Add GitHub Actions secrets WORKER_URL and WORKER_ADMIN_TOKEN.
6. Run the Collect and publish nodes workflow manually.

KV binding name is NODES. This is intentionally separate from any existing Worker/KV setup.

## API

- GET /api/status: public health/version.
- GET /api/nodes and GET /api/nodes/{id}: authenticated node data.
- GET /api/stats: authenticated counts.
- POST /api/refresh: authenticated refresh marker; GitHub Actions performs collection.
- GET /api/config: authenticated capability declaration.
- POST /api/nodes/import: authenticated snapshot import.
- GET /api/subscription: authenticated JSON snapshot, not a tunnel.

Protected routes require Authorization: Bearer <ADMIN_TOKEN>.

## Security and truthfulness

Never commit credentials or private profiles. Public VPN endpoints are untrusted. A TCP check or source ping is not a successful VPN connection. Only a real protocol tunnel plus egress verification may become verified_connected. Use public nodes only where permitted.
See docs/PHASE1.md and docs/SECURITY.md.
