# Candidate history and verification contract

- Candidate pool: maximum 2,000 records; at most 40 per country (including UNKNOWN).
- Each collection merges by stable node ID and records last_seen_at. The workflow restores/saves the pool through GitHub Actions cache.
- Each run rotates at most 100 records using a persisted cursor. Selection is fair across runs.
- A candidate is not a subscription node. Only status=verified_connected may be published.
- The current source supplies OpenVPN profiles. Mihomo does not implement OpenVPN client profiles; therefore the current VPNGate source is verified with the native OpenVPN client, not mislabeled as Mihomo validation. A Mihomo-compatible source/adapter must be added separately before Mihomo can verify those protocols.
- Tunnel success requires a route through the tunnel interface, a successful egress-IP request bound to that interface, and a DNS-over-HTTPS request through the same interface. TCP/UDP port reachability and source ping are metadata only.
- Public VPN profiles are untrusted. The verifier allowlists profile directives and drops script, plugin, config, and hook directives before invoking OpenVPN.
- FreeNodes publication counts only verified_connected nodes; the 1,000 value is a maximum, not a guarantee of supply.
