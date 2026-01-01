"""
License Client

Main client class for interacting with the license server.
"""

import json
import urllib.request
import urllib.error
from typing import Optional
from pathlib import Path

from .fingerprint import DeviceFingerprint
from .exceptions import (
    LicenseError,
    InvalidLicenseError,
    LicenseAlreadyActiveError,
    LicenseRevokedError,
    DeviceNotAuthorizedError,
    NetworkError,
)


class LicenseClient:
    """
    Client for license activation and validation.
    
    Usage:
        client = LicenseClient("https://your-license-server.com")
        
        # Activate a license
        result = client.activate("XXXX-XXXX-XXXX-XXXX")
        
        # Validate the license
        if client.is_valid():
            print("License is valid!")
        
        # Deactivate when done
        client.deactivate()
    """

    def __init__(
        self,
        server_url: str,
        license_key: Optional[str] = None,
        cache_file: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize the license client.
        
        Args:
            server_url: Base URL of the license server (e.g., "https://license.example.com")
            license_key: Optional license key to use
            cache_file: Optional path to cache activation data locally
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip('/')
        self.license_key = license_key
        self.cache_file = Path(cache_file) if cache_file else None
        self.timeout = timeout
        self._fingerprint = DeviceFingerprint()
        self._device_id: Optional[str] = None
        self._is_activated = False

        if self.cache_file and self.cache_file.exists():
            self._load_cache()

    @property
    def device_id(self) -> str:
        """Get the current device ID."""
        if self._device_id is None:
            self._device_id = self._fingerprint.device_id
        return self._device_id

    def activate(self, license_key: Optional[str] = None) -> dict:
        """
        Activate a license on this device.
        
        Args:
            license_key: The license key to activate. Uses stored key if not provided.
        
        Returns:
            dict with activation details including device_id
        
        Raises:
            InvalidLicenseError: If the license key is invalid
            LicenseAlreadyActiveError: If the license is already activated elsewhere
            LicenseRevokedError: If the license has been revoked
            NetworkError: If unable to connect to the server
        """
        if license_key:
            self.license_key = license_key

        if not self.license_key:
            raise LicenseError("No license key provided")

        payload = {
            "license_key": self.license_key,
            **self._fingerprint.to_dict(),
        }

        response = self._request("POST", "/api/v1/activate", payload)

        if response.get("success"):
            self._device_id = response.get("device_id")
            self._is_activated = True
            self._save_cache()
            return response
        
        message = response.get("message", "Activation failed")
        self._raise_error_from_message(message)

    def deactivate(self) -> dict:
        """
        Deactivate the license from this device.
        
        Returns:
            dict with deactivation confirmation
        
        Raises:
            LicenseError: If deactivation fails
            NetworkError: If unable to connect to the server
        """
        if not self.license_key:
            raise LicenseError("No license key stored")

        payload = {
            "license_key": self.license_key,
            "device_id": self.device_id,
        }

        response = self._request("POST", "/api/v1/deactivate", payload)

        if response.get("success"):
            self._is_activated = False
            self._clear_cache()
            return response
        
        message = response.get("message", "Deactivation failed")
        raise LicenseError(message)

    def validate(self) -> dict:
        """
        Validate the license is active on this device.
        
        Returns:
            dict with validation result
        
        Raises:
            InvalidLicenseError: If the license is invalid
            LicenseRevokedError: If the license has been revoked
            DeviceNotAuthorizedError: If this device is not authorized
            NetworkError: If unable to connect to the server
        """
        if not self.license_key:
            raise LicenseError("No license key stored")

        payload = {
            "license_key": self.license_key,
            "device_id": self.device_id,
        }

        response = self._request("POST", "/api/v1/validate", payload)

        if response.get("valid"):
            self._is_activated = True
            return response
        
        self._is_activated = False
        message = response.get("message", "Validation failed")
        self._raise_error_from_message(message)

    def is_valid(self) -> bool:
        """
        Check if the license is valid without raising exceptions.
        
        Returns:
            True if the license is valid and active on this device
        """
        try:
            self.validate()
            return True
        except LicenseError:
            return False

    def require_valid_license(self) -> None:
        """
        Ensure a valid license exists, raising an exception if not.
        
        Use this at the start of your application to enforce licensing.
        
        Raises:
            LicenseError: If the license is not valid
        """
        if not self.is_valid():
            raise LicenseError(
                "A valid license is required to use this software. "
                "Please activate your license."
            )

    def _request(self, method: str, endpoint: str, data: dict) -> dict:
        """Make an HTTP request to the license server."""
        url = f"{self.server_url}{endpoint}"
        
        try:
            json_data = json.dumps(data).encode('utf-8')
            request = urllib.request.Request(
                url,
                data=json_data,
                method=method,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )
            
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        
        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode('utf-8'))
                return error_body
            except Exception:
                raise NetworkError(f"HTTP {e.code}: {e.reason}")
        
        except urllib.error.URLError as e:
            raise NetworkError(f"Failed to connect: {e.reason}")
        
        except Exception as e:
            raise NetworkError(f"Request failed: {str(e)}")

    def _raise_error_from_message(self, message: str) -> None:
        """Convert error message to appropriate exception."""
        message_lower = message.lower()
        
        if "invalid license" in message_lower:
            raise InvalidLicenseError(message)
        elif "already activated" in message_lower or "already active" in message_lower:
            raise LicenseAlreadyActiveError(message)
        elif "revoked" in message_lower:
            raise LicenseRevokedError(message)
        elif "not activated on this device" in message_lower or "not authorized" in message_lower:
            raise DeviceNotAuthorizedError(message)
        else:
            raise LicenseError(message)

    def _save_cache(self) -> None:
        """Save activation data to cache file."""
        if not self.cache_file:
            return
        
        cache_data = {
            "license_key": self.license_key,
            "device_id": self._device_id,
        }
        
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception:
            pass

    def _load_cache(self) -> None:
        """Load activation data from cache file."""
        if not self.cache_file or not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            self.license_key = cache_data.get("license_key")
            self._device_id = cache_data.get("device_id")
        except Exception:
            pass

    def _clear_cache(self) -> None:
        """Remove the cache file."""
        if self.cache_file and self.cache_file.exists():
            try:
                self.cache_file.unlink()
            except Exception:
                pass

    def __repr__(self) -> str:
        status = "activated" if self._is_activated else "not activated"
        return f"LicenseClient(server={self.server_url}, {status})"
