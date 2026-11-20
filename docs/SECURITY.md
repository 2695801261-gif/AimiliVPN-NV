# Security notes

- Never commit ADMIN_TOKEN, private credentials, or private VPN profiles.
- Store ADMIN_TOKEN as a Worker secret, not a plaintext variable.
- Store WORKER_ADMIN_TOKEN as a GitHub Actions repository secret.
- Use a long random token (at least 32 random bytes); do not reuse a password.
- This API is protected by one bearer token, not a multi-user identity system. Rotate it if exposed.
- Public VPN endpoints are untrusted third-party infrastructure.
- KV is eventually consistent; do not use it for locks, transactions, or high-frequency counters.
- Cloudflare stores node metadata only; it does not proxy the user's VPN traffic.
