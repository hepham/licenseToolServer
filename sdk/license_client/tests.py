"""
Tests for the License Client SDK
"""

import json
import time
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from license_client import (
    LicenseClient,
    DeviceFingerprint,
    LicenseError,
    InvalidLicenseError,
    LicenseAlreadyActiveError,
    LicenseRevokedError,
    DeviceNotAuthorizedError,
    NetworkError,
    SignatureVerificationError,
)
from license_client.signature import SignatureVerifier


class TestDeviceFingerprint:
    """Tests for DeviceFingerprint class."""

    def test_fingerprint_properties_are_strings(self):
        fp = DeviceFingerprint()
        assert isinstance(fp.cpu_id, str)
        assert isinstance(fp.disk_serial, str)
        assert isinstance(fp.motherboard_id, str)
        assert isinstance(fp.mac_address, str)
        assert isinstance(fp.device_id, str)

    def test_device_id_is_sha256_hex(self):
        fp = DeviceFingerprint()
        assert len(fp.device_id) == 64
        assert all(c in '0123456789abcdef' for c in fp.device_id)

    def test_to_dict_returns_all_fields(self):
        fp = DeviceFingerprint()
        data = fp.to_dict()
        assert "cpu_id" in data
        assert "disk_serial" in data
        assert "motherboard_id" in data
        assert "mac_address" in data
        assert "device_id" not in data

    def test_device_id_is_consistent(self):
        fp = DeviceFingerprint()
        id1 = fp.device_id
        id2 = fp.device_id
        assert id1 == id2

    def test_repr(self):
        fp = DeviceFingerprint()
        repr_str = repr(fp)
        assert "DeviceFingerprint" in repr_str
        assert "device_id=" in repr_str


class TestLicenseClient:
    """Tests for LicenseClient class."""

    @pytest.fixture
    def mock_response(self):
        """Create a mock HTTP response."""
        def _mock(data, status=200):
            response = MagicMock()
            response.read.return_value = json.dumps(data).encode('utf-8')
            response.__enter__ = MagicMock(return_value=response)
            response.__exit__ = MagicMock(return_value=False)
            return response
        return _mock

    def test_init_basic(self):
        client = LicenseClient("https://license.example.com")
        assert client.server_url == "https://license.example.com"
        assert client.license_key is None
        assert client.timeout == 30

    def test_init_with_trailing_slash(self):
        client = LicenseClient("https://license.example.com/")
        assert client.server_url == "https://license.example.com"

    def test_init_with_license_key(self):
        client = LicenseClient(
            "https://license.example.com",
            license_key="TEST-KEY-1234-5678"
        )
        assert client.license_key == "TEST-KEY-1234-5678"

    def test_device_id_property(self):
        client = LicenseClient("https://license.example.com")
        device_id = client.device_id
        assert len(device_id) == 64

    @patch('urllib.request.urlopen')
    def test_activate_success(self, mock_urlopen, mock_response):
        mock_urlopen.return_value = mock_response({
            "success": True,
            "message": "License activated successfully",
            "license_key": "TEST-1234-5678-ABCD",
            "device_id": "abc123"
        })
        
        client = LicenseClient("https://license.example.com")
        result = client.activate("TEST-1234-5678-ABCD")
        
        assert result["success"] is True
        assert client.license_key == "TEST-1234-5678-ABCD"
        assert client._is_activated is True

    @patch('urllib.request.urlopen')
    def test_activate_invalid_license(self, mock_urlopen, mock_response):
        mock_urlopen.return_value = mock_response({
            "success": False,
            "message": "Invalid license key"
        })
        
        client = LicenseClient("https://license.example.com")
        
        with pytest.raises(InvalidLicenseError):
            client.activate("INVALID-KEY")

    @patch('urllib.request.urlopen')
    def test_activate_already_active(self, mock_urlopen, mock_response):
        mock_urlopen.return_value = mock_response({
            "success": False,
            "message": "This license is already activated on another device"
        })
        
        client = LicenseClient("https://license.example.com")
        
        with pytest.raises(LicenseAlreadyActiveError):
            client.activate("USED-KEY-1234-5678")

    @patch('urllib.request.urlopen')
    def test_activate_revoked(self, mock_urlopen, mock_response):
        mock_urlopen.return_value = mock_response({
            "success": False,
            "message": "This license has been revoked"
        })
        
        client = LicenseClient("https://license.example.com")
        
        with pytest.raises(LicenseRevokedError):
            client.activate("REVOKED-KEY-1234")

    def test_activate_no_license_key(self):
        client = LicenseClient("https://license.example.com")
        
        with pytest.raises(LicenseError) as exc_info:
            client.activate()
        
        assert "No license key" in str(exc_info.value)

    @patch('urllib.request.urlopen')
    def test_deactivate_success(self, mock_urlopen, mock_response):
        mock_urlopen.return_value = mock_response({
            "success": True,
            "message": "License deactivated successfully"
        })
        
        client = LicenseClient(
            "https://license.example.com",
            license_key="TEST-1234-5678-ABCD"
        )
        client._is_activated = True
        
        result = client.deactivate()
        
        assert result["success"] is True
        assert client._is_activated is False

    def test_deactivate_no_license_key(self):
        client = LicenseClient("https://license.example.com")
        
        with pytest.raises(LicenseError) as exc_info:
            client.deactivate()
        
        assert "No license key" in str(exc_info.value)

    @patch('urllib.request.urlopen')
    def test_validate_success(self, mock_urlopen, mock_response):
        mock_urlopen.return_value = mock_response({
            "valid": True,
            "message": "License is valid"
        })
        
        client = LicenseClient(
            "https://license.example.com",
            license_key="TEST-1234-5678-ABCD"
        )
        
        result = client.validate()
        
        assert result["valid"] is True
        assert client._is_activated is True

    @patch('urllib.request.urlopen')
    def test_validate_not_authorized(self, mock_urlopen, mock_response):
        mock_urlopen.return_value = mock_response({
            "valid": False,
            "message": "License is not activated on this device"
        })
        
        client = LicenseClient(
            "https://license.example.com",
            license_key="TEST-1234-5678-ABCD"
        )
        
        with pytest.raises(DeviceNotAuthorizedError):
            client.validate()

    @patch('urllib.request.urlopen')
    def test_is_valid_returns_true(self, mock_urlopen, mock_response):
        mock_urlopen.return_value = mock_response({
            "valid": True,
            "message": "License is valid"
        })
        
        client = LicenseClient(
            "https://license.example.com",
            license_key="TEST-1234-5678-ABCD"
        )
        
        assert client.is_valid() is True

    @patch('urllib.request.urlopen')
    def test_is_valid_returns_false(self, mock_urlopen, mock_response):
        mock_urlopen.return_value = mock_response({
            "valid": False,
            "message": "Invalid license"
        })
        
        client = LicenseClient(
            "https://license.example.com",
            license_key="TEST-1234-5678-ABCD"
        )
        
        assert client.is_valid() is False

    @patch('urllib.request.urlopen')
    def test_require_valid_license_passes(self, mock_urlopen, mock_response):
        mock_urlopen.return_value = mock_response({
            "valid": True,
            "message": "License is valid"
        })
        
        client = LicenseClient(
            "https://license.example.com",
            license_key="TEST-1234-5678-ABCD"
        )
        
        client.require_valid_license()

    @patch('urllib.request.urlopen')
    def test_require_valid_license_fails(self, mock_urlopen, mock_response):
        mock_urlopen.return_value = mock_response({
            "valid": False,
            "message": "Invalid license"
        })
        
        client = LicenseClient(
            "https://license.example.com",
            license_key="TEST-1234-5678-ABCD"
        )
        
        with pytest.raises(LicenseError):
            client.require_valid_license()

    def test_cache_file_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "license.json"
            
            client1 = LicenseClient(
                "https://license.example.com",
                license_key="TEST-1234-5678-ABCD",
                cache_file=str(cache_path)
            )
            client1._device_id = "test-device-id"
            client1._save_cache()
            
            assert cache_path.exists()
            
            client2 = LicenseClient(
                "https://license.example.com",
                cache_file=str(cache_path)
            )
            
            assert client2.license_key == "TEST-1234-5678-ABCD"
            assert client2._device_id == "test-device-id"

    def test_cache_file_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "license.json"
            
            client = LicenseClient(
                "https://license.example.com",
                license_key="TEST-1234-5678-ABCD",
                cache_file=str(cache_path)
            )
            client._save_cache()
            assert cache_path.exists()
            
            client._clear_cache()
            assert not cache_path.exists()

    def test_repr(self):
        client = LicenseClient("https://license.example.com")
        repr_str = repr(client)
        assert "LicenseClient" in repr_str
        assert "license.example.com" in repr_str


class TestExceptions:
    """Tests for custom exceptions."""

    def test_license_error(self):
        error = LicenseError("Test error", code="TEST")
        assert str(error) == "Test error"
        assert error.code == "TEST"

    def test_invalid_license_error(self):
        error = InvalidLicenseError()
        assert "Invalid license" in str(error)
        assert error.code == "INVALID_LICENSE"

    def test_license_already_active_error(self):
        error = LicenseAlreadyActiveError()
        assert "already activated" in str(error)
        assert error.code == "ALREADY_ACTIVE"

    def test_license_revoked_error(self):
        error = LicenseRevokedError()
        assert "revoked" in str(error)
        assert error.code == "REVOKED"

    def test_device_not_authorized_error(self):
        error = DeviceNotAuthorizedError()
        assert "not authorized" in str(error)
        assert error.code == "DEVICE_NOT_AUTHORIZED"

    def test_network_error(self):
        error = NetworkError()
        assert "connect" in str(error)
        assert error.code == "NETWORK_ERROR"

    def test_signature_verification_error(self):
        error = SignatureVerificationError()
        assert "signature" in str(error).lower()
        assert error.code == "SIGNATURE_INVALID"


class TestSignatureVerifier:
    """Tests for SignatureVerifier class."""

    def test_verifier_disabled_without_key(self):
        verifier = SignatureVerifier(None)
        assert verifier.is_enabled is False
        assert verifier.verify({"any": "data"}) is True

    def test_verifier_enabled_with_key(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        verifier = SignatureVerifier(public_pem)
        assert verifier.is_enabled is True

    def test_verify_valid_signature(self):
        from cryptography.hazmat.primitives.asymmetric import rsa, padding
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.backends import default_backend
        import base64

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        data = {"valid": True, "message": "License is valid", "timestamp": int(time.time())}
        payload = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        signature = private_key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
        data["signature"] = base64.b64encode(signature).decode('utf-8')

        verifier = SignatureVerifier(public_pem)
        assert verifier.verify(data) is True

    def test_verify_invalid_signature(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        data = {
            "valid": True,
            "message": "License is valid",
            "timestamp": int(time.time()),
            "signature": "invalid-signature"
        }

        verifier = SignatureVerifier(public_pem)
        assert verifier.verify(data) is False

    def test_verify_missing_signature(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        data = {"valid": True, "message": "License is valid"}

        verifier = SignatureVerifier(public_pem)
        assert verifier.verify(data) is False

    def test_verify_expired_timestamp(self):
        from cryptography.hazmat.primitives.asymmetric import rsa, padding
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.backends import default_backend
        import base64

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        old_timestamp = int(time.time()) - 600
        data = {"valid": True, "message": "License is valid", "timestamp": old_timestamp}
        payload = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        signature = private_key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
        data["signature"] = base64.b64encode(signature).decode('utf-8')

        verifier = SignatureVerifier(public_pem)
        assert verifier.verify(data) is False


class TestLicenseClientWithSignature:
    """Tests for LicenseClient with signature verification."""

    @pytest.fixture
    def key_pair(self):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        return private_key, public_pem

    def test_client_with_public_key(self, key_pair):
        _, public_pem = key_pair
        client = LicenseClient(
            "https://license.example.com",
            public_key=public_pem
        )
        assert client._verifier.is_enabled is True

    def test_client_without_public_key(self):
        client = LicenseClient("https://license.example.com")
        assert client._verifier.is_enabled is False
