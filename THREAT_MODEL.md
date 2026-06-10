# CL Chat — Threat Model

## What this protects against
- Passive eavesdropping on any single link (per-connection ECDH keys)
- Replay attacks (UUID dedup, 10k window)
- Spam/flooding (rate limiter: 30 msg/10s per peer endpoint)
- Username impersonation within a session (sanitized, validated)
- Key rotation attacks on known peers (TOFU fingerprint store)

## What this does NOT protect against
- **Relay node trust**: A compromised relay peer sees plaintext before re-encrypting.
  Use `--direct-only` if confidentiality against relays is required.
- **First-connection MITM**: TOFU only catches key changes on subsequent connections.
  Verify the fingerprint out-of-band (in person, Signal, etc.) on first connect.
- **Metadata**: Message timing and frequency between peers is visible to network observers.
  Message size leaks approximate content length even when encrypted.
- **Endpoint compromise**: If a peer's machine is compromised, all messages they can read
  are exposed. This is true of all end-to-end encrypted systems.
- **`--no-encryption` mode**: Plaintext on the wire. Only for debugging on air-gapped LANs.
  The flag is intentionally inconvenient to discourage accidental use.

## Out of scope
- Anonymity (no Tor/onion routing)
- Deniability (messages are signed implicitly by their encryption key)
- Group key agreement (each link is pairwise; mesh nodes are trusted forwarders)
