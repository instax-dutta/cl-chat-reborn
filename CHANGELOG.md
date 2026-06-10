# Changelog

## v0.2.0 (2026-06-10)

### Refactor
- Split 710-line `peer.py` monolith into `core/` modules: `peer.py` (coordinator), `connection.py` (handshake), `router.py` (message routing), `commands.py` (command parsing), `display.py` (UI output), `tofu.py` (fingerprint store), `seen_ids.py` (dedup cache). Each module independently unit-testable.
- Root `peer.py` is now a thin facade importing from `core.peer`.

### Security
- Replaced blocking `input()` in `verify_fingerprint` with async `FingerprintChallenge` queue — no more stdin deadlock with the colorama UI.
- Rate limiter rekeyed from `id(socket)` to `host:port` — rate limits persist across reconnections. Added 120s TTL eviction.
- Wired `/quit` to a proper stop callback instead of a dead `pass`.

### CI & tooling
- Added `.github/workflows/ci.yml` — runs `pytest` on Python 3.9 / 3.11 / 3.12.
- Added `pyproject.toml` with `ruff` (line-length 100, py39 target) and `mypy --strict` config.
- Added `.gitignore` (untracked `__pycache__`, `.clchat/`, `*.pyo`, `*.pyd`, `dist/`, `build/`, `.env`).

### Documentation
- Added `THREAT_MODEL.md` documenting security guarantees and limitations.
- Added `CONTRIBUTING.md` with dev setup, test commands, and PR checklist.
- Updated `README.md` with Security Flags table, link to threat model, and corrected Python requirement (3.9+).
