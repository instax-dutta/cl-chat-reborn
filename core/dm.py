DM_MAGIC = b'\x00\x44\x4d\x00'   # 4 bytes, invalid UTF-8 sequence


def encode_dm(target_username: str, plaintext: str) -> str:
    """Encode a DM as a magic-prefixed plaintext string."""
    inner = DM_MAGIC + target_username.encode('utf-8') + b'\x00' + plaintext.encode('utf-8')
    return inner.decode('latin-1')


def decode_dm(plaintext: str) -> tuple:
    """
    Returns (is_dm, target_username, body).
    If not a DM: (False, None, plaintext).
    If a DM:     (True,  target, body).
    """
    raw = plaintext.encode('latin-1')
    if not raw.startswith(DM_MAGIC):
        return (False, None, plaintext)
    rest = raw[len(DM_MAGIC):]
    if b'\x00' not in rest:
        return (False, None, plaintext)
    sep = rest.index(b'\x00')
    target = rest[:sep].decode('utf-8')
    body = rest[sep+1:].decode('utf-8')
    return (True, target, body)
