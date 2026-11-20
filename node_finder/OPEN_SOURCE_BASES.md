# Open-source bases reviewed

Review date: 2026-11-20

## 1. sinspired/subs-check-pro — strongest candidate for checker foundation

Repository: https://github.com/sinspired/subs-check-pro

Why it is relevant:
- Subscription intake and node checking.
- Advertises Mihomo and sing-box subscription generation.
- Web UI designed for desktop and phone.
- Docker image and Windows/Linux/macOS options.
- Advertises ISP type and residential/datacenter classification.

License/repo check: GitHub repository metadata currently reports GPL-3.0, Go, public repository, and active pushes. The README documents Docker image deployment, default WebUI port 8199, an API key, Mihomo and sing-box output, Android subs-free client, ISP type and residential/datacenter analysis. The Docker Hub listing documents 8299/8199 ports and the same advertised classification.

Decision: **evaluate as the first candidate to reuse**, rather than implementing a full checker ourselves. The license is copyleft: if we modify and distribute a derivative, GPL-3.0 obligations apply; keep it as a separately deployed upstream component unless we deliberately accept those obligations. Before adoption, inspect source code and license, exact protocol-core implementation, how it obtains egress IP, how it classifies residential vs hosting, and its minimum memory/CPU requirements. Do not treat marketing labels as proof.

## 2. OpenASN — IP-origin classification data

Repository: https://github.com/openasn/openasn

License check: GitHub metadata reports the repository code as MIT; the project README separately states its core data artifacts and overrides are CC0. Keep code and data licenses distinct and follow the artifact's own manifest/attribution.

Why it is relevant:
- Offline IP-origin classification: residential ISP, hosting, VPN, Tor, relay, business, unknown.
- Explainable signals and provenance.
- Open data artifacts; repository states core artifacts are CC0.

Limit:
- It cannot prove an IP is a genuine household endpoint.
- It explicitly does not detect all residential proxies or prove an IP is safe.
- Use it as one evidence source, preserve unknown/conflicting outcomes.

Decision: **use as a candidate classification layer**, after validating the artifact format and current release against the code we choose.

## 3. FlClash — primary Android client

Repository: https://github.com/chen08209/FlClash

Why it is relevant:
- Android client based on Mihomo.
- Imports a subscription profile or local configuration.
- Supports proxy groups and TUN mode.

Decision: **first client target**. Generate and validate Mihomo YAML, then test import/update on the user's Samsung Android phone. The client does not supply nodes.

## 4. Other references, not first deployment base

- https://github.com/daimon3332/easy-proxies — sing-box-powered subscription importer, checker, lifecycle manager, and WebUI. Useful for lifecycle/testing design; not selected as first base until its egress classification and hosting requirements are compared.
- https://github.com/waterlens/ssconv — Rust parser/converter for Mihomo; useful as a format/parser reference, not a node source or checker.
- https://github.com/tbxark/sub-store-convert — conversion core supports Cloudflare Workers; useful for later format conversion only. It does not collect or verify nodes.
- https://github.com/Earl9/subconv-next — self-hosted Mihomo subscription converter; useful for private subscription publishing, not node discovery or verification.

## 5. License and reuse rule

Do not copy code or data until the repository's exact LICENSE and third-party dependency/data licenses are checked. Pin upstream versions or commits, keep notices, and isolate adapters so an upstream replacement does not require rewriting the whole project.
