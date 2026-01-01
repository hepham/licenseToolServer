import re
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.licenses.utils import generate_license_key, hash_fingerprint, generate_device_id
from apps.licenses.models import License, Device


class TestLicenseKeyGenerator:
    def test_generate_license_key_format(self):
        key = generate_license_key()
        pattern = r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'
        assert re.match(pattern, key), f"Key {key} doesn't match expected format"

    def test_generate_license_key_uniqueness(self):
        keys = [generate_license_key() for _ in range(100)]
        assert len(keys) == len(set(keys)), "Generated keys should be unique"

    def test_generate_license_key_length(self):
        key = generate_license_key()
        assert len(key) == 19, "Key should be 19 characters (4x4 + 3 dashes)"


class TestHashFingerprint:
    def test_hash_fingerprint_returns_hex(self):
        result = hash_fingerprint("test_data")
        assert len(result) == 64, "SHA-256 should produce 64 hex characters"
        assert all(c in '0123456789abcdef' for c in result)

    def test_hash_fingerprint_consistency(self):
        data = "test_fingerprint"
        hash1 = hash_fingerprint(data)
        hash2 = hash_fingerprint(data)
        assert hash1 == hash2, "Same input should produce same hash"

    def test_hash_fingerprint_different_inputs(self):
        hash1 = hash_fingerprint("input1")
        hash2 = hash_fingerprint("input2")
        assert hash1 != hash2, "Different inputs should produce different hashes"


class TestGenerateDeviceId:
    def test_generate_device_id_format(self):
        device_id = generate_device_id("cpu123", "disk456", "mb789", "AA:BB:CC:DD:EE:FF")
        assert len(device_id) == 64
        assert all(c in '0123456789abcdef' for c in device_id)

    def test_generate_device_id_consistency(self):
        id1 = generate_device_id("cpu", "disk", "mb", "mac")
        id2 = generate_device_id("cpu", "disk", "mb", "mac")
        assert id1 == id2

    def test_generate_device_id_different_hardware(self):
        id1 = generate_device_id("cpu1", "disk", "mb", "mac")
        id2 = generate_device_id("cpu2", "disk", "mb", "mac")
        assert id1 != id2


@pytest.mark.django_db
class TestLicenseModel:
    def test_license_auto_generates_key(self):
        license = License.objects.create()
        assert license.key is not None
        assert len(license.key) == 19

    def test_license_default_status(self):
        license = License.objects.create()
        assert license.status == License.Status.INACTIVE

    def test_license_is_activated_property(self):
        license = License.objects.create(status=License.Status.ACTIVE)
        assert license.is_activated is True

        license.status = License.Status.INACTIVE
        assert license.is_activated is False

    def test_license_unique_key(self):
        license1 = License.objects.create()
        with pytest.raises(Exception):
            License.objects.create(key=license1.key)


@pytest.mark.django_db
class TestDeviceModel:
    def test_device_creation(self):
        license = License.objects.create()
        device = Device.objects.create(
            license=license,
            device_id="a" * 64,
            fingerprint_hash="b" * 64,
            mac_address_hash="c" * 64
        )
        assert device.license == license
        assert license.devices.count() == 1

    def test_device_cascade_delete(self):
        license = License.objects.create()
        Device.objects.create(
            license=license,
            device_id="d" * 64,
            fingerprint_hash="e" * 64,
            mac_address_hash="f" * 64
        )
        license_id = license.id
        license.delete()
        assert Device.objects.filter(license_id=license_id).count() == 0


@pytest.mark.django_db
class TestActivationAPI:
    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def license(self):
        return License.objects.create()

    @pytest.fixture
    def device_data(self):
        return {
            'cpu_id': 'CPU-12345',
            'disk_serial': 'DISK-67890',
            'motherboard_id': 'MB-ABCDE',
            'mac_address': 'AA:BB:CC:DD:EE:FF'
        }

    def test_activate_success(self, client, license, device_data):
        response = client.post('/api/v1/activate/', {
            'license_key': license.key,
            **device_data
        })
        assert response.status_code == 200
        assert response.data['success'] is True
        license.refresh_from_db()
        assert license.status == License.Status.ACTIVE

    def test_activate_invalid_key(self, client, device_data):
        response = client.post('/api/v1/activate/', {
            'license_key': 'XXXX-XXXX-XXXX-XXXX',
            **device_data
        })
        assert response.status_code == 404

    def test_activate_already_active(self, client, license, device_data):
        client.post('/api/v1/activate/', {'license_key': license.key, **device_data})
        
        other_device = {
            'cpu_id': 'CPU-OTHER',
            'disk_serial': 'DISK-OTHER',
            'motherboard_id': 'MB-OTHER',
            'mac_address': 'FF:EE:DD:CC:BB:AA'
        }
        response = client.post('/api/v1/activate/', {
            'license_key': license.key,
            **other_device
        })
        assert response.status_code == 409

    def test_deactivate_success(self, client, license, device_data):
        activate_response = client.post('/api/v1/activate/', {
            'license_key': license.key,
            **device_data
        })
        device_id = activate_response.data['device_id']
        
        response = client.post('/api/v1/deactivate/', {
            'license_key': license.key,
            'device_id': device_id
        })
        assert response.status_code == 200
        license.refresh_from_db()
        assert license.status == License.Status.INACTIVE

    def test_validate_success(self, client, license, device_data):
        activate_response = client.post('/api/v1/activate/', {
            'license_key': license.key,
            **device_data
        })
        device_id = activate_response.data['device_id']
        
        response = client.post('/api/v1/validate/', {
            'license_key': license.key,
            'device_id': device_id
        })
        assert response.status_code == 200
        assert response.data['valid'] is True

    def test_validate_wrong_device(self, client, license, device_data):
        client.post('/api/v1/activate/', {'license_key': license.key, **device_data})
        
        response = client.post('/api/v1/validate/', {
            'license_key': license.key,
            'device_id': 'wrong-device-id'
        })
        assert response.status_code == 403
        assert response.data['valid'] is False


@pytest.mark.django_db
class TestAdminAPI:
    @pytest.fixture
    def admin_user(self, db):
        from django.contrib.auth.models import User
        return User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )

    @pytest.fixture
    def admin_client(self, admin_user):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        return client

    @pytest.fixture
    def unauth_client(self):
        return APIClient()

    def test_list_licenses(self, admin_client):
        License.objects.create()
        License.objects.create()
        response = admin_client.get('/api/v1/admin/licenses/')
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_list_licenses_unauthorized(self, unauth_client):
        response = unauth_client.get('/api/v1/admin/licenses/')
        assert response.status_code == 401

    def test_create_license(self, admin_client):
        response = admin_client.post('/api/v1/admin/licenses/')
        assert response.status_code == 201
        assert 'key' in response.data
        assert License.objects.count() == 1

    def test_get_license_detail(self, admin_client):
        license = License.objects.create()
        response = admin_client.get(f'/api/v1/admin/licenses/{license.id}/')
        assert response.status_code == 200
        assert response.data['key'] == license.key

    def test_revoke_license(self, admin_client):
        license = License.objects.create(status=License.Status.ACTIVE)
        Device.objects.create(
            license=license,
            device_id='a' * 64,
            fingerprint_hash='b' * 64,
            mac_address_hash='c' * 64
        )
        response = admin_client.delete(f'/api/v1/admin/licenses/{license.id}/revoke/')
        assert response.status_code == 200
        license.refresh_from_db()
        assert license.status == License.Status.REVOKED
        assert license.devices.count() == 0

    def test_list_devices(self, admin_client):
        license = License.objects.create()
        Device.objects.create(
            license=license,
            device_id='d' * 64,
            fingerprint_hash='e' * 64,
            mac_address_hash='f' * 64
        )
        response = admin_client.get('/api/v1/admin/devices/')
        assert response.status_code == 200
        assert len(response.data) == 1
