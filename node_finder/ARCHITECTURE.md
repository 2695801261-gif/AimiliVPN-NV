# Global Node Finder — architecture decision

## User-facing target

A private, hosted node catalogue and subscription service, operated from a phone. Initial client target is **FlClash (Mihomo/Clash YAML)**. Hiddify and sing-box are secondary output targets; they are not allowed to delay the first working FlClash subscription.

The service is a catalogue/checker/subscription publisher. It is not a VPN provider and does not relay user traffic.

## Three mutually exclusive IP-origin shelves

1. `US_RESIDENTIAL`: observed egress IP is in the United States and the IP-origin dataset classifies it as residential ISP. Store country evidence and classifier version.
2. `OTHER_RESIDENTIAL`: observed egress IP is outside the United States and the dataset classifies it as residential ISP.
3. `DATACENTER_LOW_RISK`: hosting/datacenter ASN or range, with no positive VPN/Tor/known-abuse signal in the selected datasets. The UI must say "datacenter / no known negative signal", never guarantee "clean", "safe", or "undetectable".

Anything mobile, business, relay, VPN, Tor, CGNAT, unknown, conflicting, or unverified remains **unclassified/quarantine** and is excluded from the three public shelves by default. Residential classification is probabilistic and cannot prove that an IP is a genuine household connection or not a residential proxy.

## Node lifecycle

`discovered -> parsed -> preliminary -> protocol_verified -> egress_observed -> classified -> published`

- Parse success is not availability.
- TCP connect is not a proxy handshake.
- Protocol handshake success is not sufficient without an egress-IP request through the proxy.
- The observed egress IP (not the node's server IP) drives country and network-type classification.
- A result records time, test region, protocol-core version, IP-classifier version, latency, and evidence.
- Stale or repeatedly failing records are withdrawn from subscriptions.

## Proposed components

### A. Intake and normalization
- Reuse current `node_finder/collector/links.py` only as a Phase 1 bootstrap parser; do not treat it as a production-complete parser.
- Prefer a mature parser/checker integration over growing a bespoke URI parser.
- Source registry remains explicit and empty until each source is reviewed for provenance, redistribution rights, freshness, and format.
- Initial intake: curated public subscription feeds and user-supplied feeds. No indiscriminate scraping or publishing credentials from unknown feeds.

### B. Protocol-aware verification
- Evaluate `sinspired/subs-check-pro` as the primary candidate because it already advertises subscription intake, protocol testing, Mihomo and sing-box output, and network-type reporting.
- Verify the exact supported protocols, implementation, license, memory needs, API security, and whether its residential/datacenter labels are backed by explainable IP intelligence before adopting it.
- If adopted, pin a release/container digest and preserve upstream attribution/license. Do not fork-copy blindly.
- Test from a mainland-China vantage point for actual phone usability; an overseas hosted checker is only a separate vantage point.

### C. IP origin classification
- Evaluate OpenASN as an offline, explainable first-pass IP-origin dataset.
- Use the observed proxy egress IP, not the endpoint IP.
- OpenASN can distinguish residential ISP vs hosting and known VPN/Tor overlays, but cannot prove a residential IP is a real home line or detect all residential proxies.
- Preserve `unknown` and conflicting cases rather than forcing a category.
- Add a separate abuse/reputation source only after its terms, cost, and false-positive behavior are reviewed.

### D. Hosting and storage
- First hosting experiment: Render free Docker web service for an on-demand admin/checker UI only. It sleeps after 15 minutes idle and may restart; free plan has no persistent disk and no background worker/cron. Therefore it is not a reliable always-on scheduler or durable node database.
- Use Cloudflare Worker + KV only for lightweight authenticated API and subscription publication. Do not run protocol cores or promise raw TCP/UDP checking in Workers.
- Keep the authoritative snapshot reproducible/exportable. KV is a cache/published snapshot, not the only copy.
- If continuous background checks or persistent state are required, a paid worker/volume or an always-on machine is required. Do not enable billing or purchase anything without explicit user approval.

### E. Mobile consumption
- First output: Mihomo YAML subscription for FlClash.
- Three separate filtered subscription URLs: `us-residential`, `other-residential`, `datacenter-low-risk`.
- Include only nodes that pass protocol handshake and egress-IP verification from a declared test vantage.
- Later adapters: Hiddify/sing-box, only when round-trip compatibility tests pass.

## Quality gates
- Source provenance and license review.
- Strict schema validation and deduplication.
- Protocol handshake + egress check.
- Country and ASN/IP-origin classification with evidence/version.
- No credentials in logs, diagnostics, public repository, or analytics.
- Subscription tokens are high entropy, revocable, and never committed.
- Never label a node "clean" as an absolute security guarantee.
