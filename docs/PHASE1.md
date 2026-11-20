# Personal MVP – implementation and acceptance

## Scope
1. Fetch the VPNGate public listing.
2. Normalize OpenVPN endpoint metadata, classify by country, and deduplicate.
3. Run a small Python unit-test suite in GitHub Actions.
4. Optionally publish the latest candidate snapshot to the project's dedicated Worker KV namespace.
5. Retain the JSON snapshot briefly as a workflow artifact for manual inspection.

## Explicit limitations
- This source currently provides OpenVPN profiles only.
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
- [ ] A Clash/Mihomo-compatible source is identified before promising a Clash subscription.
- [ ] Mihomo config validation and a real proxy/egress test pass before any node is described as usable in Clash.

The current collector emits candidates with status=pending. This is deliberate: no candidate is upgraded to a successful connection based on source metadata alone.
