# Personal MVP – implementation and acceptance

## Scope
1. Fetch the VPNGate public listing.
2. Normalize VPNGate OpenVPN endpoint metadata, classify by country, and deduplicate.
3. Fetch up to 50 candidates from two public Clash/Mihomo YAML feeds (primary plus fallback) and preserve their native proxy fields.
4. Run a small Python unit-test suite in GitHub Actions, including the Clash YAML parser and Mihomo verifier helpers.
5. On the hosted runner, download the official Mihomo Linux binary, validate candidate configs, start each candidate in isolation, and require a public egress-IP response through the local proxy. Current run attempts never reached a runner (`runner_id: 0`, no steps/logs); account-level Actions usage/billing or GitHub runner dispatch must be restored first.
6. Optionally publish the VPNGate metadata snapshot to the project's dedicated Worker KV namespace.
7. Retain candidate and verified snapshots briefly as a workflow artifact for manual inspection.

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
- [x] Mihomo verifier implementation added: per-node config validation, isolated Mihomo process, proxied public egress-IP check, and separate verified output.
- [ ] Hosted GitHub Actions run confirms the Mihomo binary download and real protocol/egress checks; no node is yet confirmed usable until this run produces a verified result.
- [x] Diagnosed the current Actions blocker: the latest job has `runner_id: 0`, no runner name, zero steps, and no downloadable logs. This is a pre-runner dispatch/account-level failure, not a Python or Mihomo step failure.
- [ ] Repository owner checks GitHub Settings → Billing & licensing → Usage / Actions for included-minute exhaustion, blocked spending budget, or failed payment; if usage is blocked, restore included usage or resolve billing, then rerun the workflow.

The current collector emits candidates with status=pending. This is deliberate: no candidate is upgraded to a successful connection based on source metadata alone.
