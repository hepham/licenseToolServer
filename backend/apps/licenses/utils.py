import secrets
import string
import hashlib


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
