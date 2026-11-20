# Personal MVP – implementation and acceptance

## Scope
1. Fetch the VPNGate public listing.
2. Normalize VPNGate OpenVPN endpoint metadata, classify by country, and deduplicate.
3. Fetch up to 50 candidates from two public Clash/Mihomo YAML feeds (primary plus fallback) and preserve their native proxy fields.
4. Run a small Python unit-test suite in GitHub Actions, including the Clash YAML parser.
5. Optionally publish the VPNGate metadata snapshot to the project's dedicated Worker KV namespace.
6. Retain both JSON candidate snapshots briefly as a workflow artifact for manual inspection.

## Explicit limitations
- VPNGate provides OpenVPN profiles only; the separate public Clash/Mihomo feed supplies proxy-format candidates.
- OpenVPN profiles are not Clash/Mihomo proxy entries. Do not synthesize fake Clash YAML from them.
- The Worker stores candidate metadata; it is not a VPN gateway.
- The JSON API is not a Clash subscription URL.
- A candidate's source ping or open port does not prove a successful VPN connection.
- No Android app, public multi-user service, large historical pool, high-volume rotation, or fixed node-count target is part of this personal-use milestone.

## Acceptance
- [x] VPNGate parser classifies records as OpenVPN.
- [x] Duplicate endpoint records are collapsed.
- [x] Unit tests pass locally.
- [ ] GitHub Actions run passes on the hosted runner.
- [ ] Optional Worker deployment and authenticated import/list are verified.
- [x] Two public Clash/Mihomo-compatible candidate feeds are wired into collection with fallback on fetch/parse failure.
- [ ] Mihomo config validation and a real proxy/egress test pass before any node is described as usable in Clash.

The current collector emits candidates with status=pending. This is deliberate: no candidate is upgraded to a successful connection based on source metadata alone.
