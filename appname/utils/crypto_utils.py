import base64
import binascii
import os
from typing import Optional, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


_PREFIX = "enc:v1:"
_NONCE_LEN = 12  # AES-GCM standard nonce size
_KEY_LEN = 32  # AES-256


_warned_disabled = False


def _warn_once(msg: str) -> None:
    global _warned_disabled
    if _warned_disabled:
        return
    _warned_disabled = True
    # Avoid leaking secrets. This is only a high-level warning.
    print(f"[crypto] {msg}")


def _add_b64_padding(s: str) -> str:
    # Base64 strings should be a multiple of 4.
    missing = (-len(s)) % 4
    return s + ("=" * missing)


def _decode_key_from_env() -> Tuple[Optional[bytes], Optional[str]]:
    """Decode encryption key from environment.

    Supported:
      - ENCRYPTION_KEY_B64: base64 or base64url of 32 raw bytes (padding optional)
      - ENCRYPTION_KEY_HEX: 64 hex chars (32 raw bytes)

    Returns (key_bytes, error_reason). If key_bytes is None, encryption is disabled.
    """

    key_hex = (os.getenv("ENCRYPTION_KEY_HEX", "") or "").strip().strip('"').strip("'")
    if key_hex:
        try:
            key = binascii.unhexlify(key_hex)
            if len(key) != _KEY_LEN:
                return None, f"ENCRYPTION_KEY_HEX must decode to {_KEY_LEN} bytes"
            return key, None
        except Exception:
            return None, "ENCRYPTION_KEY_HEX is not valid hex"

    key_b64 = (os.getenv("ENCRYPTION_KEY_B64", "") or "").strip().strip('"').strip("'")
    if not key_b64:
        return None, "ENCRYPTION_KEY_B64 missing"

    # Try standard base64 first, then urlsafe base64 (both with optional padding)
    for decoder_name in ("std", "urlsafe"):
        try:
            padded = _add_b64_padding(key_b64)
            if decoder_name == "std":
                key = base64.b64decode(padded)
            else:
                key = base64.urlsafe_b64decode(padded)
            if len(key) != _KEY_LEN:
                return None, f"ENCRYPTION_KEY_B64 must decode to {_KEY_LEN} bytes"
            return key, None
        except Exception:
            continue

    return None, "ENCRYPTION_KEY_B64 is not valid base64/base64url"


def encryption_enabled() -> bool:
    key, err = _decode_key_from_env()
    if key is None:
        if os.getenv("ENCRYPTION_STRICT", "").strip() in ("1", "true", "True", "yes", "YES"):
            raise RuntimeError(f"Encryption is required but disabled: {err}")
        return False
    return True


def encryption_status() -> dict:
    key, err = _decode_key_from_env()
    return {
        "enabled": key is not None,
        "reason": None if key is not None else err,
        "prefix": _PREFIX,
        "key_len_bytes": len(key) if key is not None else None,
        "strict": os.getenv("ENCRYPTION_STRICT", "").strip() in ("1", "true", "True", "yes", "YES"),
    }

def _get_key() -> Optional[bytes]:
    """Return raw key bytes, or None if encryption is disabled.

    IMPORTANT: This is intentionally NOT cached because:
      - developers often set ENCRYPTION_KEY_B64 via .env during local dev
      - caching a missing key would keep encryption disabled until restart
    """

    key, err = _decode_key_from_env()
    if key is None:
        if os.getenv("ENCRYPTION_STRICT", "").strip() in ("1", "true", "True", "yes", "YES"):
            raise RuntimeError(f"Encryption is required but disabled: {err}")
        _warn_once(
            "Encryption disabled (missing/invalid key). Set ENCRYPTION_KEY_B64 (base64 of 32 bytes) or ENCRYPTION_KEY_HEX (64 hex chars)."
        )
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
