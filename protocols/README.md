# Protocol adapter contract

Each future adapter must implement the same conceptual lifecycle while keeping protocol-specific configuration isolated:

- validate_config(config) -> ValidationResult
- connect(config, cancellation) -> TunnelHandle
- wait_until_ready(handle, timeout) -> ConnectionResult
- get_tunnel_stats(handle) -> Stats
- disconnect(handle)

Success means a real tunnel is established. A successful TCP socket or ICMP ping is only preliminary reachability.

| Protocol ID | Phase 1 model | Android implementation |
|---|---|---|
| openvpn | Defined; VPNGate source | Planned first |
| sstp | Defined; no source yet | Requires client/library and license review |
| softether | Defined; no source yet | Requires native/client feasibility and license review |
| l2tp_ipsec | Defined for compatibility | Android 13 built-in client unavailable; separate implementation required |

No third-party protocol code is copied into this repository at this stage. Any future dependency requires compatibility and license review.
