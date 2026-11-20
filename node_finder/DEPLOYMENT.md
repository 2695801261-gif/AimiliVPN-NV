# Deployment plan

## What can be hosted for $0

Render's free Docker web service can host an on-demand web UI/API without a credit card, but it sleeps after 15 minutes idle, can restart at any time, and free workers/cron jobs/persistent disks are not included. It is suitable for a proof-of-concept UI, not reliable scheduled verification or durable storage.

The existing Cloudflare Worker can distribute a precomputed snapshot and protected Mihomo YAML. It cannot run the proxy core needed for full VLESS/Trojan/Hysteria2/etc. handshakes or carry user proxy traffic.

## Proposed low-friction split

- Render free web service: temporary admin/checker UI experiment only, if the upstream image fits its 512 MB RAM / CPU limits.
- Cloudflare Worker + dedicated KV keys: authenticated snapshot read/write and subscription delivery.
- Snapshot source of truth: exportable JSON artifact in the private repo/release or other durable storage, not Render's ephemeral filesystem.
- Real verification: run in the checker container only during on-demand sessions; no claim of always-on checks.
- If the checker exceeds free limits or needs scheduled/background jobs, stop and ask before choosing paid hosting.

## No changes made

This document does not create a Render service, connect a new provider, change Cloudflare resources, expose subscription links, or deploy a container. Those actions require the user's explicit account-side setup/approval.
