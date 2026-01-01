import secrets
import string
import hashlib
import json
import time
import base64
from typing import Optional
from functools import lru_cache

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend


def generate_license_key() -> str:
    """
    Generate a license key in format XXXX-XXXX-XXXX-XXXX.
    Uses cryptographically secure random alphanumeric characters.
    """
    chars = string.ascii_uppercase + string.digits
    segments = []
    for _ in range(4):
        segment = ''.join(secrets.choice(chars) for _ in range(4))
        segments.append(segment)
    return '-'.join(segments)


def hash_fingerprint(fingerprint_data: str) -> str:
    """
    Generate a secure hash of device fingerprint data.
    Uses SHA-256 for consistent, secure hashing.
    """
    return hashlib.sha256(fingerprint_data.encode('utf-8')).hexdigest()


def generate_device_id(cpu_id: str, disk_serial: str, motherboard_id: str, mac_address: str) -> str:
    """
    Generate a unique device ID from hardware components.
    Combines all identifiers and hashes them for privacy.
    """
    combined = f"{cpu_id}:{disk_serial}:{motherboard_id}:{mac_address}"
    return hash_fingerprint(combined)


@lru_cache(maxsize=1)
def _get_signing_key():
    """Load the private signing key from settings."""
    from django.conf import settings
    
    key_path = getattr(settings, 'LICENSE_SIGNING_KEY', None)
    if not key_path:
        return None
    
    try:
        with open(key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        return private_key
    except Exception:
        return None


def sign_response(data: dict) -> dict:
    """
    Sign a response dictionary with the server's private key.
    
    Adds 'timestamp' and 'signature' fields to the response.
    If signing key is not configured, returns data unchanged.
    """
    private_key = _get_signing_key()
    if not private_key:
        return data
    
    signed_data = data.copy()
    signed_data['timestamp'] = int(time.time())
    
    payload = json.dumps(signed_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    
    signature = private_key.sign(
        payload,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    
    signed_data['signature'] = base64.b64encode(signature).decode('utf-8')
    
    return signed_data
