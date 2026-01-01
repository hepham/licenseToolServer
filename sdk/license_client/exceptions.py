"""
License Client Exceptions

Custom exceptions for license operations.
"""


class LicenseError(Exception):
    """Base exception for all license-related errors."""

    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class InvalidLicenseError(LicenseError):
    """Raised when the license key is invalid or not found."""

    def __init__(self, message: str = "Invalid license key"):
        super().__init__(message, code="INVALID_LICENSE")


class LicenseAlreadyActiveError(LicenseError):
    """Raised when trying to activate an already active license."""

    def __init__(self, message: str = "License is already activated on another device"):
        super().__init__(message, code="ALREADY_ACTIVE")


class LicenseRevokedError(LicenseError):
    """Raised when the license has been revoked."""

    def __init__(self, message: str = "License has been revoked"):
        super().__init__(message, code="REVOKED")


class DeviceNotAuthorizedError(LicenseError):
    """Raised when the device is not authorized for this license."""

    def __init__(self, message: str = "Device is not authorized for this license"):
        super().__init__(message, code="DEVICE_NOT_AUTHORIZED")


class NetworkError(LicenseError):
    """Raised when there is a network communication error."""

    def __init__(self, message: str = "Failed to connect to license server"):
        super().__init__(message, code="NETWORK_ERROR")
