# Graph Report - .  (2026-06-10)

## Corpus Check
- Corpus is ~6,997 words - fits in a single context window. You may not need a graph.

## Summary
- 349 nodes · 583 edges · 24 communities (22 shown, 2 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 60 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_PeerConnection & Peer Tests|PeerConnection & Peer Tests]]
- [[_COMMUNITY_P2PPeer Core|P2PPeer Core]]
- [[_COMMUNITY_Rate Limiting & De-Duplication|Rate Limiting & De-Duplication]]
- [[_COMMUNITY_CryptoContext & Key Exchange|CryptoContext & Key Exchange]]
- [[_COMMUNITY_Message Sanitization|Message Sanitization]]
- [[_COMMUNITY_Username Validation|Username Validation]]
- [[_COMMUNITY_Simple Terminal UI|Simple Terminal UI]]
- [[_COMMUNITY_Test Fixtures|Test Fixtures]]
- [[_COMMUNITY_Terminal UI Display|Terminal UI Display]]
- [[_COMMUNITY_Chat Messages & Help|Chat Messages & Help]]
- [[_COMMUNITY_Username Utilities|Username Utilities]]
- [[_COMMUNITY_Peer Count Validation|Peer Count Validation]]
- [[_COMMUNITY_Encryption Disabled Mode Tests|Encryption Disabled Mode Tests]]
- [[_COMMUNITY_Screen Management|Screen Management]]
- [[_COMMUNITY_Encryption Enabled Mode Tests|Encryption Enabled Mode Tests]]
- [[_COMMUNITY_Derive Shared Key Tests|Derive Shared Key Tests]]
- [[_COMMUNITY_EncryptDecrypt Roundtrip Tests|Encrypt/Decrypt Roundtrip Tests]]
- [[_COMMUNITY_Terminal UI Styling|Terminal UI Styling]]
- [[_COMMUNITY_Terminal UI Input & Display Loop|Terminal UI Input & Display Loop]]
- [[_COMMUNITY_Demo Module|Demo Module]]
- [[_COMMUNITY_Trace Clearance|Trace Clearance]]
- [[_COMMUNITY_Encryption Module|Encryption Module]]
- [[_COMMUNITY_Encrypt Method|Encrypt Method]]

## God Nodes (most connected - your core abstractions)
1. `P2PPeer` - 54 edges
2. `CryptoContext` - 45 edges
3. `RateLimiter` - 31 edges
4. `TerminalUI` - 23 edges
5. `check_username()` - 20 edges
6. `PeerConnection` - 17 edges
7. `register_peer()` - 16 edges
8. `socket` - 15 edges
9. `TestCheckUsername` - 15 edges
10. `clean_message()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `ChaCha20-Poly1305 AEAD` --references--> `CryptoContext`  [INFERRED]
  README.md → encryption.py
- `Ephemeral Per-Connection Keypairs` --references--> `CryptoContext`  [INFERRED]
  README.md → encryption.py
- `Perfect Forward Secrecy` --references--> `CryptoContext`  [INFERRED]
  README.md → encryption.py
- `HKDF-SHA256` --references--> `CryptoContext`  [INFERRED]
  README.md → encryption.py
- `X25519 ECDH` --references--> `CryptoContext`  [INFERRED]
  README.md → encryption.py

## Import Cycles
- 1-file cycle: `terminal_ui.py -> terminal_ui.py`

## Hyperedges (group relationships)
- **Encryption and Security Protocol Suite** — encryption_cryptocontext, readme_x25519_ecdh, readme_chacha20_poly1305, readme_hkdf_sha256, readme_forward_secrecy, readme_ephemeral_keypairs [INFERRED 0.95]
- **Trust and Security Verification** — readme_tofu_fingerprint, readme_mitm_protection, peer_p2ppeer, encryption_cryptocontext [INFERRED 0.95]
- **Message Processing Pipeline** — peer_p2ppeer, sanitizer_ratelimiter, peer_seenids_dedup, encryption_cryptocontext, readme_mesh_forwarding [INFERRED 0.95]

## Communities (24 total, 2 thin omitted)

### Community 0 - "PeerConnection & Peer Tests"
Cohesion: 0.05
Nodes (38): PeerConnection, make_peer_connection(), mock_sock(), peer(), Tests for peer.py — P2PPeer message processing, dedup, forwarding, nick change,, Messages with different IDs are both processed., Tests for nick_change message processing., A nick_change message updates the peer's username. (+30 more)

### Community 1 - "P2PPeer Core"
Cohesion: 0.11
Nodes (17): main(), P2PPeer, Return path to TOFU known_hosts file., Load TOFU known_hosts JSON. Returns empty dict if file missing or corrupt., Save a peer fingerprint to the TOFU known_hosts file., TOFU verification: check known_hosts, prompt user if unknown or changed., Read one \n-terminated line from socket using 4096-byte buffered reads., Input Sanitization (+9 more)

### Community 2 - "Rate Limiting & De-Duplication"
Cohesion: 0.12
Nodes (12): Seen IDs Dedup System, Rate Limiting, UUID Sliding-Window Dedup, RateLimiter, Sliding-window rate limiter per key., Tests for RateLimiter sliding-window rate limiter., First max_events calls to allow() return True., Call after max_events returns False. (+4 more)

### Community 3 - "CryptoContext & Key Exchange"
Cohesion: 0.11
Nodes (13): CryptoContext, Decrypt base64(nonce + ciphertext) via ChaCha20-Poly1305.          Returns plain, Per-connection cryptographic context.      Uses X25519 ECDH for key agreement an, Return base64-encoded X25519 public key for handshake., Return SHA-256 fingerprint of X25519 public key as colon-separated hex., Derive shared key from peer's base64-encoded public key via X25519 + HKDF., ChaCha20-Poly1305 AEAD, Ephemeral Per-Connection Keypairs (+5 more)

### Community 4 - "Message Sanitization"
Cohesion: 0.15
Nodes (11): clean_message(), Sanitize a chat message. Returns cleaned string., Non-string input returns empty string., Empty string returns empty string (after strip)., Tests for clean_message()., Normal printable message passes through unchanged., Message exceeding MAX_MESSAGE_LENGTH (4096) is truncated., Control characters (\\x00, \\x01) are stripped; newlines preserved. (+3 more)

### Community 5 - "Username Validation"
Cohesion: 0.11
Nodes (10): Tests for check_username()., Usernames with hyphens are valid., Underscore after first char is okay., Empty string returns None., Special characters like '!' return None., Username exceeding 20 chars gets truncated., None input returns None., Non-string input (int) returns None. (+2 more)

### Community 6 - "Simple Terminal UI"
Cohesion: 0.14
Nodes (9): Simplified terminal UI for systems without colorama., Start the simple terminal UI., Main input handling loop., Handle internal UI commands. Only /help and /clear handled locally; all other, Set callback for handling user input., Update the displayed username., Update connection status., Stop the simple terminal UI. (+1 more)

### Community 7 - "Test Fixtures"
Cohesion: 0.12
Nodes (15): alice_crypto(), bob_crypto(), crypto_disabled(), crypto_enabled(), mock_peer(), mock_socket(), Shared pytest fixtures for CL Chat test suite., CryptoContext with encryption enabled. (+7 more)

### Community 8 - "Terminal UI Display"
Cohesion: 0.14
Nodes (8): Handle internal UI commands. Only /help and /clear handled locally; all other, Set callback for handling user input., Update the displayed username., Update connection status., Stop the terminal UI., Modern terminal-like chat interface., Get terminal width, fallback to 80 if not available., TerminalUI

### Community 9 - "Chat Messages & Help"
Cohesion: 0.18
Nodes (7): ChatMessage, Show help information., Add a message to the display queue., Add a system message., Add an error message., Add a message to display., Represents a chat message with metadata.

### Community 10 - "Username Utilities"
Cohesion: 0.20
Nodes (7): get_username(), check_username(), Input sanitization and rate limiting for CL Chat., Validate and sanitize a username. Returns sanitized name or None., Valid usernames return the sanitized name., Single character returns None., Newlines, tabs, and carriage returns are stripped before validation.

### Community 11 - "Peer Count Validation"
Cohesion: 0.21
Nodes (8): Check peer count hasn't exceeded maximum., validate_peer_count(), Tests for sanitizer.py — username validation, message cleaning, peer count valid, Tests for validate_peer_count()., Count below MAX_PEER_COUNT (50) returns True., Count == MAX_PEER_COUNT (50) returns False., Count over MAX_PEER_COUNT returns False., TestValidatePeerCount

### Community 12 - "Encryption Disabled Mode Tests"
Cohesion: 0.17
Nodes (7): Tests for CryptoContext with enabled=False., Disabled mode encrypt returns the raw plaintext unchanged., Disabled mode decrypt returns the raw payload unchanged., Disabled mode get_public_key returns empty string., Disabled mode ready property is False., Disabled mode get_fingerprint returns empty string., TestDisabledMode

### Community 13 - "Screen Management"
Cohesion: 0.22
Nodes (5): Clear the terminal screen., Display welcome message and connection info., Public: Clear chat history and screen., Public: Clear screen., Start the terminal UI.

### Community 14 - "Encryption Enabled Mode Tests"
Cohesion: 0.20
Nodes (6): Enabled mode get_fingerprint returns a colon-separated hex string., Tests for CryptoContext with enabled=True., Enabled mode get_public_key returns a non-empty base64 string., Ready is False before any key derivation., Ready is True after successful key derivation., TestEnabledMode

### Community 15 - "Derive Shared Key Tests"
Cohesion: 0.20
Nodes (6): Tests for derive_shared error handling., Invalid base64 input sets shared_key to None (ready=False)., Valid base64 but wrong-length key bytes sets shared_key to None., Empty string as public key sets shared_key to None., derive_shared on disabled context does nothing (ready stays False)., TestDeriveShared

### Community 16 - "Encrypt/Decrypt Roundtrip Tests"
Cohesion: 0.20
Nodes (6): Tests for encrypt/decrypt with valid shared keys., Encrypt with Alice's context, decrypt with Bob's, matches original., Encrypt with Bob's context, decrypt with Alice's, matches original., Multiple messages can be exchanged correctly., Decrypt with a different shared key returns None., TestEncryptDecryptRoundTrip

### Community 17 - "Terminal UI Styling"
Cohesion: 0.25
Nodes (6): datetime, Back, create_ui(), Fore, Create appropriate UI based on available features., Style

### Community 18 - "Terminal UI Input & Display Loop"
Cohesion: 0.25
Nodes (4): Background thread for displaying messages., Display a single message., Show the input prompt., Main input handling loop.

### Community 19 - "Demo Module"
Cohesion: 0.60
Nodes (5): check_dependencies(), check_port(), main(), print_banner(), show_usage()

### Community 20 - "Trace Clearance"
Cohesion: 0.47
Nodes (5): clear_memory(), clear_terminal(), main(), Force garbage collection to free memory., Clear terminal screen and scrollback buffer.

## Knowledge Gaps
- **15 isolated node(s):** `Fore`, `Back`, `Style`, `validate_peer_count`, `create_ui` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CryptoContext` connect `CryptoContext & Key Exchange` to `PeerConnection & Peer Tests`, `P2PPeer Core`, `Test Fixtures`, `Username Utilities`, `Encryption Disabled Mode Tests`, `Encryption Enabled Mode Tests`, `Derive Shared Key Tests`, `Encrypt/Decrypt Roundtrip Tests`, `Encryption Module`, `Encrypt Method`?**
  _High betweenness centrality (0.363) - this node is a cross-community bridge._
- **Why does `P2PPeer` connect `P2PPeer Core` to `PeerConnection & Peer Tests`, `Rate Limiting & De-Duplication`, `CryptoContext & Key Exchange`, `Test Fixtures`, `Username Utilities`?**
  _High betweenness centrality (0.199) - this node is a cross-community bridge._
- **Why does `RateLimiter` connect `Rate Limiting & De-Duplication` to `PeerConnection & Peer Tests`, `P2PPeer Core`, `Message Sanitization`, `Username Validation`, `Username Utilities`, `Peer Count Validation`?**
  _High betweenness centrality (0.192) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `P2PPeer` (e.g. with `CryptoContext` and `RateLimiter`) actually correct?**
  _`P2PPeer` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `CryptoContext` (e.g. with `P2PPeer` and `PeerConnection`) actually correct?**
  _`CryptoContext` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `RateLimiter` (e.g. with `P2PPeer` and `PeerConnection`) actually correct?**
  _`RateLimiter` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Encryption module for CL Chat X25519 ECDH key exchange + ChaCha20-Poly1305 AEAD`, `Per-connection cryptographic context.      Uses X25519 ECDH for key agreement an`, `Return base64-encoded X25519 public key for handshake.` to the rest of the system?**
  _152 weakly-connected nodes found - possible documentation gaps or missing edges._