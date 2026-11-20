# Phase 1 – implementation and acceptance

## Scope
1. Independent repository and clean project layout.
2. Shared node model for OpenVPN, SSTP, SoftEther, and L2TP/IPsec.
3. VPNGate OpenVPN source parser, stable IDs, deduplication, and tests.
4. Worker API with KV snapshot storage and bearer-token protection.
5. GitHub Actions manual/scheduled collection and optional publishing.

## Not included
- No Android APK or device-side tunnel implementation.
- No claims of real connection based only on source listing, ping, or open TCP port.
- No Cloudflare Worker acting as a VPN gateway.
- No fabricated SSTP/SoftEther/L2TP nodes from VPNGate OpenVPN records.

## Acceptance
- [x] Independent private repository.
- [x] Four protocol identifiers in shared schema and Worker capability API.
- [x] VPNGate parser explicitly classifies profiles as OpenVPN.
- [x] Duplicate endpoint records are collapsed.
- [ ] Python unit tests pass in a clean runner.
- [ ] Worker deployed with a newly created KV namespace and secret.
- [ ] /api/status returns healthy.
- [ ] Protected endpoints reject missing/wrong bearer token.
- [ ] Authenticated import and list/stats endpoints work.
- [ ] GitHub Actions manual run completes and publish succeeds after secrets are set.

The collector sets new records to pending. VPNGate score/ping are metadata only, not actual tunnel latency or verified connection state.
