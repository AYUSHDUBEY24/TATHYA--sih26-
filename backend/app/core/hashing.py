"""
Cryptographic hashing service (Phase 5).

Single reusable implementation so every hash in the system is computed the
same way: SHA-256 over the exact stored file bytes, lowercase hexadecimal.
"""

import hashlib


def sha256_hex(data: bytes) -> str:
    """Return the lowercase hex SHA-256 digest of the given bytes."""
    return hashlib.sha256(data).hexdigest()


def is_sha256_hex(value: str) -> bool:
    """True if the value looks like a 64-char lowercase hex SHA-256 digest."""
    return (
        len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )
