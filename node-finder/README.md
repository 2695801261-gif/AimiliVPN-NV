# Global Node Finder

A private, quality-first collector and subscription formatter for public proxy nodes compatible with Mihomo/Clash, Hiddify, and sing-box.

## Principles

- Collect only from an explicit, reviewable source allowlist.
- Parse and normalize; never infer a protocol from a port or transport.
- Keep newly discovered records in `pending`.
- A reachable TCP port or source-reported ping is not a successful proxy connection.
- Only a successful protocol handshake followed by an egress-IP check may be marked `verified_connected`.
- Never print share links, passwords, UUIDs, private keys, or subscription tokens in logs.
- Do not expose the subscription endpoint publicly without an unguessable per-user token.

## Architecture

1. **Collectors** run on the user's Windows PC or another controlled runner. They fetch allowlisted public sources and parse share links/config files.
2. **Normalizer** creates a common record with source, protocol, endpoint, country hints, timestamps, and a stable ID.
3. **Verifier** (Phase 2) uses protocol-aware clients to establish real outbound connections and checks the observed egress IP. It records test vantage point because a result from one network does not guarantee reachability from another.
4. **Store/API** uses the already-created dedicated Cloudflare Worker + KV from AimiliVPN-NV only after the new schema/API is ready. Worker is metadata and subscription distribution only; it is not a proxy or VPN gateway.
5. **Formatters** (Phase 3) generate separate, validated Mihomo YAML, Hiddify-compatible share-link subscriptions, and sing-box JSON.

## Protocol scope

Initial parser targets: Shadowsocks, VMess, VLESS, Trojan, Hysteria2, TUIC, AnyTLS, SOCKS, HTTP(S), SSH, and WireGuard configuration files. Additional formats are added only when parser and client compatibility tests exist.

The clients do not have identical feature sets. Every formatter must use an explicit capability matrix; unsupported protocols are omitted, never silently rewritten.

## Phases

- Phase 1: schema, safe parsing, source registry contract, fixtures, and unit tests.
- Phase 2: curated source collection and protocol-aware real-connection verification.
- Phase 3: Mihomo/Hiddify/sing-box output adapters and subscription endpoints.
- Phase 4: scheduled refresh, stale-node retirement, health history, and phone acceptance tests.

## Local development

Python 3.11+; standard library only for the Phase 1 parser.

```powershell
python -m unittest discover -s node-finder/tests -v
```

No live public node is included in tests. Fixtures use reserved example addresses and fake credentials.
