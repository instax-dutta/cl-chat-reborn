# CL Chat

Peer-to-peer command-line chat with **per-connection ECDH encryption**, mesh message propagation, and full input sanitization. No servers, no accounts, no logs.

## Features

- **Peer-to-peer** — every peer is both a client and a server; connect directly to form a mesh
- **Broadcast & direct messages** — talk to everyone or whisper to one
- **Per-connection ECDH encryption** — X25519 key exchange + ChaCha20-Poly1305 AEAD per link
- **Perfect forward secrecy** — ephemeral keypairs, no long-term secrets stored
- **Mesh forwarding** — messages propagate through connected peers (with UUID dedup)
- **Input sanitization** — rate limiting, username validation, control-char stripping
- **Colored terminal UI** — timestamps, system messages, direct-message tagging
- **Nickname system** — change your name mid-session; peers are notified
- **Trace clearance** — memory cleanup on disconnect

## How it works

```
┌──────────┐    X25519 + ChaCha20     ┌──────────┐
│  Peer A  │◄────────────────────────►│  Peer B  │
│  :9000   │      (per-connection)     │  :9001   │
└────┬─────┘                          └────┬─────┘
     │                                     │
     │          ┌──────────┐               │
     └─────────►│  Peer C  │◄──────────────┘
                │  :9002   │
                └──────────┘
```

Each peer starts a TCP listener. Peers connect to each other with `/connect`. Every connection establishes its own ephemeral X25519 keypair and derives a unique shared key via HKDF-SHA256. Messages are encrypted with ChaCha20-Poly1305 before leaving the wire — different keys per link, so an eavesdropper on one connection can't decrypt traffic on another.

When a peer receives a broadcast, it decrypts, displays, then re-encrypts and forwards to all other connected peers. Each hop uses a different key. Duplicate message IDs prevent loops.

## Quick start

```bash
# Terminal 1
python3 peer.py --username Alice --port 9000

# Terminal 2
python3 peer.py --username Bob --port 9001
```

In Bob's terminal:

```
/connect 127.0.0.1 9000
```

Now any text message broadcasts to all peers in the mesh. `/msg <user> <text>` sends a direct message.

## Usage

```
python3 peer.py [options]

  --host HOST           Interface to listen on (default: 0.0.0.0)
  --port PORT           Port to listen on (default: 9000)
  --username NAME       Your display name
  --connect HOST:PORT   Connect to a peer on startup
  --no-encryption       Disable encryption (plaintext)
  --no-ui               Basic console (no colors)
```

### Commands

| Command | Description |
|---|---|
| `/connect <host> <port>` | Connect to another peer |
| `/peers` | List connected peers |
| `/msg <user> <text>` | Send a direct (private) message |
| `/nick <name>` | Change your nickname |
| `/clear` | Clear the screen |
| `/help` | Show available commands |
| `/quit` | Disconnect and exit |

### Examples

```bash
# Three-peer mesh
python3 peer.py --username Alice --port 9000
python3 peer.py --username Bob --port 9001       # /connect 127.0.0.1 9000
python3 peer.py --username Charlie --port 9002    # /connect 127.0.0.1 9000

# Auto-connect on launch
python3 peer.py --username Bob --connect 10.0.0.5:9000

# Disable encryption (debug / LAN-only)
python3 peer.py --username Eve --no-encryption
```

## Cryptographic design

| Layer | Mechanism | Rationale |
|---|---|---|
| **Key agreement** | X25519 ECDH | Curve25519 — fast, constant-time, widely audited |
| **Key derivation** | HKDF-SHA256 | NIST SP 800-56C extract-and-expand |
| **Encryption** | ChaCha20-Poly1305 | AEAD — authenticated encryption + integrity in one pass |
| **Nonce** | Random 12-byte | Per-message random; no counter management needed for forwarding |
| **Forward secrecy** | Ephemeral keypairs | Keys generated per-connection, discarded on disconnect |

Each peer-to-peer link gets its own independent key. An attacker compromising one link cannot decrypt traffic on another. If a key is compromised, only messages on that specific connection are exposed — future sessions generate fresh keys.

**Replay protection**: every broadcast carries a UUID. Peers track 10,000 recent IDs and drop duplicates.

**Rate limiting**: 30 messages per 10-second sliding window per connection.

**Input sanitization**:
- Usernames: `[a-zA-Z0-9][a-zA-Z0-9_-]{1,19}` only
- Messages: control characters stripped, max 4096 bytes
- Maximum 50 concurrent peer connections

## Project structure

```
├── peer.py              # P2P chat application (listener, connector, UI)
├── encryption.py        # X25519 + ChaCha20-Poly1305 + HKDF crypto context
├── sanitizer.py         # Input validation, rate limiter, peer limits
├── terminal_ui.py       # Colored terminal interface (colorama-backed)
├── trace_clearance.py   # Memory & terminal cleanup utility
├── demo.py              # Dependency check and usage instructions
└── requirements.txt     # Dependencies
```

## Requirements

- **Python 3.6+**
- **cryptography >= 3.4.8** — X25519, ChaCha20-Poly1305, HKDF
- **colorama >= 0.4.6** — optional, for colored terminal output

Install: `pip install cryptography colorama`

## License

MIT
