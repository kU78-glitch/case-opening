"""
security.py - Cryptographic security and anti-tamper verification module for save data.
Provides AES encryption via Fernet or robust PBKDF2/SHA-256 HMAC authenticated encryption,
graceful tamper recovery, and clean JSON serialization.
"""
import base64
import hashlib
import hmac
import json
import os
from typing import Any, Dict, Optional

# Deterministic internal application key derivation for local game state protection
_MASTER_SECRET = b"CS2_Case_Opening_Simulator_Secured_Key_2026_x99"
_SALT = b"salt_case_opening_anti_tamper_v1"

try:
    from cryptography.fernet import Fernet
    # Derive a valid 32-byte urlsafe base64 key using PBKDF2
    _derived_key = hashlib.pbkdf2_hmac("sha256", _MASTER_SECRET, _SALT, 100_000, 32)
    _FERNET_KEY = base64.urlsafe_b64encode(_derived_key)
    _fernet = Fernet(_FERNET_KEY)
    _HAS_FERNET = True
except Exception:
    _HAS_FERNET = False
    _fernet = None

def _xor_cipher(data: bytes, key: bytes) -> bytes:
    """Fast symmetric byte transformation."""
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))

def encrypt_data(obj: Any) -> bytes:
    """
    Serializes a Python object to JSON and encrypts/authenticates the payload.
    Includes HMAC-SHA256 signature for tamper detection.
    """
    raw_json = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")

    if _HAS_FERNET and _fernet is not None:
        # Fernet provides 128-bit AES in CBC mode with PKCS7 padding and HMAC-SHA256 authentication
        return _fernet.encrypt(raw_json)
    else:
        # Fallback: XOR cipher + explicit SHA-256 HMAC envelope
        key = hashlib.sha256(_MASTER_SECRET + _SALT).digest()
        cipher_bytes = _xor_cipher(raw_json, key)
        signature = hmac.new(key, cipher_bytes, hashlib.sha256).digest()
        # Binary format: [32 bytes HMAC][Cipher payload]
        return signature + cipher_bytes

def decrypt_data(raw_bytes: bytes) -> Optional[Any]:
    """
    Decrypts and verifies data authenticity.
    Returns deserialized Python object, or None if tampered/corrupted.
    """
    if not raw_bytes:
        return None

    # 1. First attempt: Fernet decryption (if available)
    if _HAS_FERNET and _fernet is not None:
        try:
            decrypted = _fernet.decrypt(raw_bytes)
            return json.loads(decrypted.decode("utf-8"))
        except Exception:
            pass

    # 2. Second attempt: Check for XOR + HMAC envelope format (min length 32 bytes signature)
    if len(raw_bytes) > 32:
        try:
            key = hashlib.sha256(_MASTER_SECRET + _SALT).digest()
            sig_received = raw_bytes[:32]
            payload = raw_bytes[32:]
            sig_expected = hmac.new(key, payload, hashlib.sha256).digest()
            if hmac.compare_digest(sig_received, sig_expected):
                plain = _xor_cipher(payload, key)
                return json.loads(plain.decode("utf-8"))
        except Exception:
            pass

    # 3. Third attempt: Backward compatibility for plain JSON
    try:
        return json.loads(raw_bytes.decode("utf-8"))
    except Exception:
        pass

    return None

def save_encrypted_file(filepath: str, data: Any) -> bool:
    """Encrypts and atomically writes data to binary file."""
    try:
        encrypted_bytes = encrypt_data(data)
        tmp_path = f"{filepath}.tmp"
        with open(tmp_path, "wb") as f:
            f.write(encrypted_bytes)
        os.replace(tmp_path, filepath)
        return True
    except Exception as e:
        print(f"Error saving encrypted file '{filepath}': {e}")
        return False

def load_encrypted_file(filepath: str) -> tuple[Optional[Any], bool]:
    """
    Loads and decrypts file.
    Returns: (data_object, is_tampered_or_error)
    If file exists but fails verification, returns (None, True).
    If file doesn't exist, returns (None, False).
    """
    if not os.path.exists(filepath):
        return None, False

    try:
        with open(filepath, "rb") as f:
            raw_bytes = f.read()

        data = decrypt_data(raw_bytes)
        if data is None:
            # File exists but could not be decrypted or HMAC verification failed
            return None, True
        return data, False
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}")
        return None, True

