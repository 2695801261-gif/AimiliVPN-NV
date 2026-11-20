# Global Node Finder

Quality-first public proxy-node collector and subscription formatter for Mihomo/Clash, Hiddify, and sing-box.

## Principles

- Collect only from an explicit, reviewable source allowlist.
- Parse and normalize; never infer a protocol from a port or transport.
- Newly discovered records remain `pending`.
- A reachable TCP port or source-reported ping is not a successful proxy connection.
- Only a successful protocol handshake followed by an egress-IP check may become `verified_connected`.
- Never print share links, passwords, UUIDs, private keys, or subscription tokens in logs.
- Never expose subscription data without an unguessable access token.

## Architecture

1. Collectors run on the user's Windows PC or another controlled runner and fetch allowlisted public sources.
2. The normalizer creates a common record with source, protocol, endpoint, timestamps, and stable ID.
3. The verifier (Phase 2) uses protocol-aware clients to establish outbound connections and check the observed egress IP. Each result records its test location.
4. The existing dedicated AimiliVPN-NV Worker/KV is a candidate for metadata and subscription distribution after its API/schema is upgraded. Worker is not a proxy or VPN gateway.
5. Formatters (Phase 3) generate separate, validated Mihomo YAML, Hiddify-compatible share-link subscriptions, and sing-box JSON.

## Phase 1 parser scope

Implemented in this branch: common URI share-link syntax for Shadowsocks, VMess, VLESS, Trojan, Hysteria/Hysteria2, TUIC, AnyTLS, SOCKS, HTTP(S), SSH, Snell, and ShadowTLS.

WireGuard `.conf` and OpenVPN `.ovpn` file parsers are separate inputs to add after the share-link parser tests pass. A schema entry does not mean a parser or verifier already exists.

Client capabilities are not identical. Each formatter must use an explicit compatibility matrix; unsupported protocols are omitted, never silently rewritten.

## Phases

- Phase 1: schema, safe share-link parsing, source registry contract, fixtures, and unit tests.
- Phase 2: curated source collection and protocol-aware real-connection verification.
- Phase 3: Mihomo/Hiddify/sing-box output adapters and subscription endpoints.
- Phase 4: scheduled refresh, stale-node retirement, health history, and phone acceptance tests.

## Local development

Python 3.11+; standard library only.

```powershell
python -m unittest discover -s node_finder/tests -v
```

Fixtures use reserved example addresses and fake credentials; tests do not depend on live public nodes.
