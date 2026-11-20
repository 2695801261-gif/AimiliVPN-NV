# Subs-Check PRO integration and classification gates

Primary upstream candidate: https://github.com/sinspired/subs-check-pro

Reviewed against upstream source on 2026-11-20. Pin a release/commit before production use; do not rely on a floating `latest` image for reproducible checks.

## What the upstream actually provides

- It embeds Mihomo and performs protocol-aware proxy checks, then tests egress-dependent services.
- `check.Result` retains observed egress IP, country, country tag, ISP tag, speed, and IP-risk result during the run.
- Its IP/country and ISP code is called through the proxy's HTTP client, so these are intended to describe the proxy egress, not merely the configured server endpoint.
- ISP checking is optional and disabled unless `isp-check: true` and at least one supported provider API key is configured.
- The ISP package classifies hosting, residential, mobile, business, education, government, banking, military, and unknown. It includes a special `hosting + ASN isp` rule named “住宅拨号”, so a residential label is a signal, not proof of a genuine household line.
- The normal save pipeline writes general `all.yaml`, `mihomo.yaml`, and `base64.txt`; it does not natively create our three separate quality shelves.

## Recommended initial checker settings

Start with conservative concurrency and no bandwidth-heavy speed test. Add one or more ISP provider API keys privately in the checker config; do not commit them.

```yaml
rename-node: true
isp-check: true
isp-timeout: 8

# Add provider keys locally, at least one to enable ISP checks.
isp-check-api-key-ipapi: ''
isp-check-api-key-proxycheck: ''
isp-check-api-key-iplocate: ''
isp-check-api-key-ipdata: ''

# Keep IP-risk test enabled. Use a low-impact check profile first.
media-check: true
platforms:
  - iprisk

# Avoid large bandwidth tests during the first acceptance run.
speed-test-url: ''
alive-concurrent: 30
speed-concurrent: 4
media-concurrent: 10

save-method: 'r2'
worker-url: 'https://YOUR-NEW-WORKER.workers.dev'
worker-token: 'SET_TO_AUTH_TOKEN_SECRET'
```

The API keys and worker token belong only in the local private config or secret store. The values above are blank placeholders, not working credentials.

## Required post-processing before publication

Do not publish upstream `all.yaml` or `mihomo.yaml` directly as one of the three quality categories. Build a separate classifier/export stage using the per-node evidence captured during the same check run.

### US residential

Require all of:
- protocol handshake and egress-IP request succeeded;
- egress country code is exactly `US`;
- residential classification has at least two independent agreeing signals, or an explicitly reviewed high-confidence dataset result;
- no conflicting mobile/business/hosting/VPN/Tor/abuse evidence.

### Other-country residential

Same requirements, but egress country is known and not `US`.

### Datacenter low-risk

Require:
- protocol handshake and egress-IP request succeeded;
- independent evidence identifies a hosting/datacenter ASN or range;
- no positive VPN/Tor/known-abuse signal in the selected data sources.

“Low-risk” means no known negative signal in the checked datasets at the recorded time. It is not a safety or anonymity guarantee.

### Quarantine

Always quarantine missing/unknown country, missing ISP evidence, disagreement between providers, mobile, business, education/government, relay, VPN/Tor, suspected residential proxy, and stale results. Do not infer a category from node names alone.

## Important implementation gap

The upstream `check.Result` has `IP`, `Country`, `CountryCodeTag`, `ISPTag`, and `IPRisk`, but its normal output YAML primarily contains proxy configuration and a decorated node name. It does not preserve the complete structured evidence in the YAML file. To meet the quality gates above, we need one of:

1. a small, isolated upstream-compatible export hook that writes a private JSON evidence file alongside YAML; or
2. a local runner wrapper that obtains structured result data from an upstream API/CLI interface, if one is exposed by the pinned release.

Do not scrape decorated node names as the authoritative source for high-confidence classification. Before choosing option 1 or 2, inspect the exact pinned release and its result/export interfaces.

## First acceptance test

1. Run a small manually supplied test subscription on the Windows machine.
2. Verify that each candidate can complete a protocol handshake and an egress-IP request.
3. Enable ISP classification with at least one provider and inspect raw result tags.
4. Confirm that the Cloudflare Worker receives `all.yaml`, `mihomo.yaml`, and `base64.txt` through its `/storage` compatibility route.
5. Confirm that no category subscription is published until structured evidence and the independent classifier are implemented and tested.
