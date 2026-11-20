# Project status — 2026-11-20

## Current branch

`feature/global-node-finder-phase1`

Latest known branch commit: `40116a5de2f23250045433d7f1438f031e4a6469`

## Pivot confirmed

Render Free was paused before deployment. The selected first topology is:

- Windows PC: on-demand Subs-Check PRO checker.
- Cloudflare: a new isolated Worker + a new KV namespace for publishing.
- Android: FlClash / Mihomo YAML subscription consumer.

No paid hosting or VPS is required for the first acceptance test. Continuous unattended checks require a machine that stays online or separately approved hosting.

## New files added

- `node_finder/cloudflare/worker.js`: isolated publisher; supports a compatible `/storage` API for Subs-Check PRO `save-method: r2`, tokenized subscription routes, and management endpoints.
- `node_finder/cloudflare/wrangler.toml.example`: new KV binding template; placeholder namespace ID.
- `node_finder/cloudflare/README.md`: deployment, secrets, compatibility API.
- `node_finder/checker/SUBS_CHECK_PRO_INTEGRATION.md`: upstream integration and classification gates.

Architecture and deployment docs were updated to remove Render as the primary path.

## Important isolation rule

Do not modify:
- existing `aimilivpn-nv-api` Worker;
- its `NODES` KV namespace;
- the separate CFnew Worker/KV project, including its `C` binding and `u` variable.

Create a new Worker and new KV namespace for this project. Nothing has been deployed to Cloudflare yet.

## Upstream checker

- Project: https://github.com/sinspired/subs-check-pro
- Latest release observed: `v3.6.1`, published 2026-11-15.
- Windows x86_64 asset: `subs-check-pro_Windows_x86_64.zip`.
- License: GPL-3.0.
- `save-method: r2` posts `{filename,value}` to `/storage?token=...`; the new Worker implements that contract using KV.
- `isp-check` requires `isp-check: true` and at least one provider API key. Its result struct includes egress IP, country, ISP tag, and IP-risk result during the run.
- Normal YAML output does not preserve all structured evidence. Do not use decorated node names as the authoritative classifier. A structured evidence export or equivalent result interface is still required before category publication.

## Next steps

1. User creates a **new KV namespace** in Cloudflare (do not reuse existing ones).
2. Deploy `node_finder/cloudflare/worker.js` as a new Worker and bind the new namespace as `NODE_FINDER_KV`.
3. Set secrets `AUTH_TOKEN` and `ADMIN_TOKEN` in the new Worker.
4. Test `GET /health` and the Subs-Check PRO `/storage` upload/download contract using fake YAML only.
5. Install/run pinned Subs-Check PRO v3.6.1 on Windows with a small test input.
6. Implement structured evidence export and the three-way quality classifier.
7. Only after classifier tests pass, create category subscriptions and import them into FlClash.

## Current state — do not overclaim

- Worker code is committed but not deployed.
- New KV namespace does not exist yet.
- No secrets have been configured.
- No real nodes have been checked or published.
- No category subscription URLs exist.
- No end-to-end or live-network tests have passed yet.
