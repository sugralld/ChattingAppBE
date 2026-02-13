import base64
import os
from functools import lru_cache
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_PREFIX = "enc:v1:"
_NONCE_LEN = 12  # AES-GCM standard nonce size
_KEY_LEN = 32  # AES-256


@lru_cache(maxsize=1)
def _get_key() -> Optional[bytes]:
    """Return raw key bytes from env var ENCRYPTION_KEY_B64.

    If missing/invalid, return None (encryption disabled, passthrough).
    """

    key_b64 = os.getenv("ENCRYPTION_KEY_B64", "").strip()
    if not key_b64:
        return None

    try:
        key = base64.b64decode(key_b64)
    except Exception:
        return None

    if len(key) != _KEY_LEN:
        return None

    return key


def is_encrypted(value: Optional[str]) -> bool:
    return bool(value) and isinstance(value, str) and value.startswith(_PREFIX)


def encrypt_text(plaintext: Optional[str]) -> Optional[str]:
    """Encrypt a string for storage.

    - Idempotent: if already encrypted, returns as-is.
    - If ENCRYPTION_KEY_B64 is not configured, returns plaintext (passthrough).
    """

    if plaintext is None:
        return None
    if not isinstance(plaintext, str):
        plaintext = str(plaintext)

    if plaintext.startswith(_PREFIX):
        return plaintext

    key = _get_key()
    if key is None:
        return plaintext

    aesgcm = AESGCM(key)
    nonce = os.urandom(_NONCE_LEN)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    token = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")
    return _PREFIX + token


def decrypt_text(value: Optional[str]) -> Optional[str]:
    """Decrypt a stored string.

    - If not encrypted, returns as-is.
    - If key missing/invalid or decryption fails, returns input (passthrough).
    """

    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)

    if not value.startswith(_PREFIX):
        return value

    key = _get_key()
    if key is None:
        return value

    token = value[len(_PREFIX) :]
    try:
        raw = base64.urlsafe_b64decode(token)
        nonce = raw[:_NONCE_LEN]
        ciphertext = raw[_NONCE_LEN:]
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception:
        return value
