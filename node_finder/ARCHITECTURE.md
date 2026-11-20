# Global Node Finder — architecture decision

## User-facing target

A private, hosted node catalogue and subscription service, operated from a phone. Initial client target is **FlClash (Mihomo/Clash YAML)**. Hiddify and sing-box are secondary output targets; they must not delay the first working FlClash subscription.

The service is a catalogue/checker/subscription publisher. It is not a VPN provider and does not relay user traffic.

## Three mutually exclusive IP-origin shelves

1. `US_RESIDENTIAL`: observed egress IP is in the United States and independent IP-origin evidence classifies it as residential ISP.
2. `OTHER_RESIDENTIAL`: observed egress IP is outside the United States and independent IP-origin evidence classifies it as residential ISP.
3. `DATACENTER_LOW_RISK`: hosting/datacenter ASN or range, with no positive VPN/Tor/known-abuse signal in the selected datasets.

Anything mobile, business, education/government, relay, VPN, Tor, CGNAT, unknown, conflicting, or unverified remains **unclassified/quarantine** and is excluded from the three public shelves by default. Residential classification is probabilistic and cannot prove a genuine household connection or the absence of residential-proxy resale.

## Node lifecycle

`discovered -> parsed -> protocol_verified -> egress_observed -> classified -> published`

- Parse success is not availability.
- TCP connect is not a proxy handshake.
- Protocol handshake success is not sufficient without an egress-IP request through the proxy.
- The observed egress IP (not the node's server IP) drives country and network-type classification.
- A result records time, test region, protocol-core version, IP-classifier version, latency, and evidence.
- Stale or repeatedly failing records are withdrawn from subscriptions.

## Proposed components

### A. Intake and normalization

- Reuse current `node_finder/collector/links.py` only as a Phase 1 bootstrap parser; do not treat it as production-complete.
- Evaluate a mature parser/checker integration before expanding bespoke protocol code.
- Source registry remains explicit and empty until each source is reviewed for provenance, redistribution rights, freshness, and format.
- Initial intake: curated public subscription feeds and user-supplied feeds. No indiscriminate scraping or publishing credentials from unknown feeds.

### B. Protocol-aware verification

- Primary candidate: [sinspired/subs-check-pro](https://github.com/sinspired/subs-check-pro), GPL-3.0, which embeds Mihomo and performs protocol-aware checks, egress-dependent IP/location checks, optional ISP classification, and Mihomo output.
- Upstream `check.Result` carries egress IP, country, ISP tag, and IP-risk result during a run. Its ordinary YAML export does not preserve all structured evidence, so a separate evidence export/classifier is still required.
- `isp-check` requires enabling the option and configuring at least one supported provider API key. The upstream label is a useful signal, not proof. Its current classification logic includes “住宅拨号” for hosting company + ISP ASN, so we must quarantine borderline/conflicting results.
- Keep the upstream binary/container unmodified where possible. If modifying and distributing a derivative, comply with GPL-3.0 and preserve notices. Pin a release/commit; avoid floating `latest`.
- First checker host: user's Windows PC for on-demand runs, avoiding a paid VPS and avoiding Render Free sleep/ephemeral-storage constraints. It can push results to the new Cloudflare Worker. Continuous checks still require a machine that remains online.

### C. IP-origin classification

- Evaluate OpenASN as an offline, explainable first-pass IP-origin dataset.
- Use the observed proxy egress IP, not the endpoint IP.
- OpenASN can distinguish residential ISP vs hosting and known VPN/Tor overlays, but cannot prove a genuine household line or detect all residential proxies.
- Preserve `unknown` and conflicting outcomes rather than forcing a category.
- Use at least two independent agreeing signals for residential publication, or a separately reviewed high-confidence data source. Add abuse/reputation sources only after terms, cost, and false-positive behavior are reviewed.

### D. Hosting and storage

- **Cloudflare Worker + a new dedicated KV namespace** provides the lightweight authenticated upload API and subscription delivery.
- The new publisher has a compatibility endpoint for Subs-Check PRO's `save-method: r2` storage contract, implemented over KV. It is separate from the old `aimilivpn-nv-api` Worker and from the CFnew Worker/KV project.
- Never reuse or modify the old `NODES` namespace or CFnew's `C` binding/`u` variable. Create a new Worker and a new KV namespace for node-finder.
- Worker is not a proxy core and must not attempt raw TCP/UDP protocol checks.
- KV is the published snapshot/edge store, not the sole authoritative evidence archive. Keep a local export from each checker run.
- Cloudflare Free quotas are finite; batch writes and avoid one KV write per node.

### E. Mobile consumption

- First output: Mihomo YAML subscription for FlClash.
- Three separate filtered subscription URLs: `us-residential`, `other-residential`, `datacenter-low-risk`.
- Include only nodes that pass protocol handshake, egress-IP verification, and the relevant classification gate.
- Later adapters: Hiddify/sing-box, only when round-trip compatibility tests pass.

## Quality gates

- Source provenance and redistribution-rights review.
- Strict schema validation and deduplication.
- Protocol handshake + egress check.
- Country and ASN/IP-origin classification with evidence/version.
- No credentials in logs, diagnostics, public repository, or analytics.
- Subscription tokens are high entropy, revocable, and never committed.
- Never label a node “clean” as an absolute security guarantee.
