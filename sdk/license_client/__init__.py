"""
License Client SDK

A Python SDK for integrating software licensing into your tools.
"""

from .client import LicenseClient
from .fingerprint import DeviceFingerprint, FingerprintError
from .exceptions import (
    LicenseError,
    InvalidLicenseError,
    LicenseAlreadyActiveError,
    LicenseRevokedError,
    DeviceNotAuthorizedError,
    NetworkError,
    SignatureVerificationError,
)

__version__ = "1.0.0"
__all__ = [
    "LicenseClient",
    "DeviceFingerprint",
    "FingerprintError",
    "LicenseError",
    "InvalidLicenseError",
    "LicenseAlreadyActiveError",
    "LicenseRevokedError",
    "DeviceNotAuthorizedError",
    "NetworkError",
    "SignatureVerificationError",
]
