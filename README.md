# Global Node Finder (Phase 1)

This development branch changes the project direction from a self-built VPN client/gateway to a quality-first public proxy-node collector and multi-client subscription formatter.

The new implementation lives in `node_finder/`. The original `collector/`, `worker/`, `protocols/`, and old schema remain untouched on this branch as legacy reference material while the new design is validated.

## Current Phase 1 work

- Common node record schema for common Mihomo/Clash, Hiddify, and sing-box protocol families.
- Conservative URI parser for common share links.
- Parser fixtures covering VLESS, VMess, Hysteria2, Trojan, SOCKS5 IPv6, invalid schemes, and deduplication.
- All discovered records start as `pending`; parsing is not a connectivity test.

## Run tests

From the repository root:

```powershell
python -m unittest discover -s node_finder/tests -v
```

See [node_finder/README.md](node_finder/README.md) for architecture, security rules, and phase boundaries.

## Important

- This branch is experimental; `main` has not been changed.
- No Cloudflare Worker has been redeployed or modified as part of Phase 1.
- No public node credentials or real subscription links are committed.
- The Cloudflare Worker, when reused later, will store node metadata and distribute authorized subscriptions only. It is not a VPN/proxy gateway.
