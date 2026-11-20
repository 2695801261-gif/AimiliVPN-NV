# Deployment plan

## Current chosen topology

- **Checker:** Subs-Check PRO runs on the user's Windows PC for on-demand collection and protocol-aware verification. No paid VPS or Render service is required for the first acceptance test.
- **Publisher:** a new Cloudflare Worker named `node-finder-publisher`.
- **Storage:** a new KV namespace bound as `NODE_FINDER_KV`; never reuse the existing `NODES` namespace or CFnew's KV namespace.
- **Phone:** FlClash imports the published Mihomo YAML subscriptions.

## Why Render was paused

Render Free sleeps after inactivity, has ephemeral filesystem storage, and does not provide a reliable always-on background worker/cron service. It is not the right first host for a continuously running node checker. No Render service was deployed.

## Cloudflare isolation rules

The new Worker lives in `node_finder/cloudflare/`. It borrows the Worker + KV deployment pattern from the user's earlier CF project but uses a new Worker and new KV namespace.

The existing `aimilivpn-nv-api` Worker/KV and the separate CFnew Worker/KV (including binding `C` and variable `u`) must remain unchanged.

Set secrets only in the Cloudflare dashboard:
- `AUTH_TOKEN`: compatibility token used by Subs-Check PRO's `save-method: r2` adapter.
- `ADMIN_TOKEN`: separate token for the node-finder publisher management API.

The new Worker's `/storage` route stores upstream `all.yaml`, `mihomo.yaml`, `base64.txt`, and `history.yaml` files in its own KV namespace. This is transport compatibility only; it does not split the three quality categories.

## First deployment and acceptance sequence

1. Review the new Worker code and create a new KV namespace.
2. Deploy the Worker to a new name, bind `NODE_FINDER_KV`, and set the two secrets.
3. Check `GET /health` returns `ok: true`.
4. On Windows, run a small test subscription through a pinned Subs-Check PRO release with ISP checks enabled and conservative concurrency.
5. Verify uploads through `POST /storage?token=...` and downloads through `GET /storage?filename=mihomo.yaml&token=...`.
6. Export structured per-node evidence from the checker run and implement the three-way classifier.
7. Only after classification tests pass, publish the three category-specific Mihomo YAMLs and create separate subscription tokens.
8. Test subscription import and update in FlClash on the Samsung phone.

## What is not done yet

- The new Worker is committed to GitHub but is **not deployed**.
- No new KV namespace or Cloudflare secrets have been created.
- The upstream checker has not yet been run against live nodes.
- The upstream checker YAML output does not contain all structured evidence needed for the quality shelves; the evidence-export/classifier stage remains a blocker before publishing real nodes.
- No subscription tokens or node data have been published.
- No paid hosting, VPS, or Cloudflare upgrade has been purchased or enabled.

Do not publish credentials or unverified nodes. Ask before enabling billing or modifying any existing Cloudflare resource.
