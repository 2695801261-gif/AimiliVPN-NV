# Cloudflare publisher (isolated)

This Worker is a lightweight **publisher and subscription delivery edge** for the node-finder project. It is deliberately separate from:

- the existing `aimilivpn-nv-api` Worker and its `NODES` KV namespace;
- the separate CFnew Worker/KV project (including its `C` binding and `u` variable).

Do not bind this Worker to either existing namespace. Create a new KV namespace and use the binding name `NODE_FINDER_KV`.

## What it does

- Public health check: `GET /health`.
- Admin-authenticated publish of already-generated Mihomo YAML for the three approved shelves.
- Creates 256-bit random subscription tokens. Only the SHA-256 hash of each token is stored in KV.
- Serves a token-protected YAML subscription at `GET /sub/{token}`.
- Revokes a subscription token with an authenticated DELETE request.
- Reports publish timestamps and sizes to an authenticated status endpoint.

It does **not** collect nodes, run a proxy core, verify handshakes, observe egress IPs, or classify residential/datacenter IPs. Those jobs belong to the separate checker/verification engine. No node is publishable until that engine supplies validated output.

## Categories

- `us-residential`
- `other-residential`
- `datacenter-low-risk`

Unknown, mobile, business, relay, VPN/Tor, conflicting, and unverified results must remain quarantined and must not be included in these YAML files.

## New Cloudflare resources

1. Create a new Worker named `node-finder-publisher`.
2. Create a **new** KV namespace, e.g. `NODE_FINDER_DATA`.
3. Bind that namespace to the Worker as `NODE_FINDER_KV`.
4. Add Worker secret `ADMIN_TOKEN` (a long random value; do not put it in Git).
5. Deploy this directory using `wrangler.toml.example` after replacing the placeholder namespace ID, or configure the equivalent settings in the dashboard.

Do not edit or repoint the old Worker. Do not reuse the old KV namespace. Do not put secrets in `wrangler.toml`, source files, GitHub Actions logs, or screenshots.

## API

All admin routes require:
`Authorization: Bearer $ADMIN_TOKEN`

### Health

`GET /health`

No authentication. Returns service/version/storage status only.

### Publish

`POST /api/v1/publish`

JSON body:

```json
{
  "yaml": {
    "us-residential": "mixed:\\n  - name: example\\n    type: ...",
    "other-residential": "mixed:\\n  - name: example\\n    type: ...",
    "datacenter-low-risk": "mixed:\\n  - name: example\\n    type: ..."
  }
}
```

Only non-empty category entries supplied in the request are replaced. YAML is stored as supplied; the publisher checks category names and size, **not YAML syntax or node safety**. The upstream verifier/formatter must validate YAML before publishing.

### Create subscription token

`POST /api/v1/tokens`

Body: `{"category":"us-residential"}`

The response contains the token and subscription path once. Save the returned URL privately; the raw token cannot be recovered from KV. Anyone holding the URL can use that category subscription until the token is revoked.

### Revoke token

`DELETE /api/v1/tokens/{token}`

Requires admin authentication. Revocation removes the token-hash mapping.

### Publish status

`GET /api/v1/status`

Requires admin authentication. Returns the latest publish timestamp and YAML byte size for each category.

## Operational cautions

- KV is eventually consistent; a newly published subscription may take a short time to become visible globally.
- Free-plan KV quotas apply. Batch publishes rather than writing one key per node.
- The Worker does not perform background scanning. A Cloudflare Worker is not a substitute for a persistent proxy-core process.
- Subscription tokens are bearer credentials. Keep them private and revoke leaked links.
- This initial implementation is an API foundation, not a complete deployed service. It must pass local tests and a fresh-namespace staging deployment before any real node data is published.
