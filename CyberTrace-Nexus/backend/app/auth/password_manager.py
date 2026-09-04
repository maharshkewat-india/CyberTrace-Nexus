"""
password_manager.py - PBKDF2-HMAC-SHA256 password hashing with random salt.

Design notes:
- Uses PBKDF2 with HMAC-SHA256 (recommended by NIST SP 800-132).
- Salt length: 16 bytes (128 bits) — cryptographically random.
- Iterations: 210_000 (tuned for ~100ms cost on typical modern CPUs).
- Derived key length: 32 bytes (256 bits, output size of SHA-256).
- Passwords are never stored as plaintext; hash+salt only.
- The `must_change_password` flag mechanism allows forcing a password change
  on first login for demo accounts.
"""

import os
import base64
import hmac
from typing import Tuple

import hashlib


SALT_BYTES = 16   # 128-bit salt
ITERATIONS = 210_000
DK_LEN = 32       # bytes (256-bit derived key, length of SHA-256 output)


def hash_password(password: str) -> Tuple[str, str]:
    """
    Hash a plaintext password and return (salt_hex, hash_hex).

    Args:
        password: The plaintext password string.

    Returns:
        A tuple of (salt_hex, hash_hex), both hex-encoded strings.
    """
    salt = os.urandom(SALT_BYTES).hex()
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        ITERATIONS,
        dklen=DK_LEN,
    )
    hash_hex = dk.hex()
    return salt, hash_hex


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """
    Verify a password against its stored hash+salt.

    Uses ``hmac.compare_digest`` for constant-time comparison to prevent
    timing-attack based password guessing.

    Args:
        password: The plaintext password to test.
        salt_hex: Hex-encoded salt that was used when hashing.
        hash_hex: Hex-encoded hash that was stored.

    Returns:
        True if the password matches; False otherwise.
    """
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS,
        dklen=DK_LEN,
    )
    computed = dk.hex()
    return hmac.compare_digest(computed, hash_hex)


def generate_must_change_token(user_id: int) -> Tuple[str, str]:
    """
    Generate a salted token value that signals the user must change password
    on next login. The token is derived from the user's own user_id so it is
    bound to that account.

    Returns a (hex_token, hex_salt) tuple.
    """
    salt = os.urandom(SALT_BYTES).hex()
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        str(user_id).encode("utf-8"),
        bytes.fromhex(salt),
        ITERATIONS,
        dklen=DK_LEN,
    )
    token = dk.hex()
    return token, salt