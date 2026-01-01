# License Client SDK

A Python SDK for integrating license management into your tools.

## Installation

```bash
pip install license-client
```

Or install from source:

```bash
cd sdk
pip install -e .
```

## Quick Start

```python
from license_client import LicenseClient

# Initialize client
client = LicenseClient("https://your-license-server.com")

# Activate a license
try:
    result = client.activate("XXXX-XXXX-XXXX-XXXX")
    print(f"License activated! Device ID: {result['device_id']}")
except Exception as e:
    print(f"Activation failed: {e}")

# Validate license
if client.is_valid():
    print("License is valid!")
else:
    print("License is not valid")
```

## Usage Examples

### Basic Usage with Caching

```python
from license_client import LicenseClient

# Use cache file to persist activation
client = LicenseClient(
    server_url="https://your-license-server.com",
    cache_file="~/.myapp/license.json"
)

# First run: activate
if not client.is_valid():
    client.activate("XXXX-XXXX-XXXX-XXXX")

# Subsequent runs: automatically loaded from cache
```

### Enforce License at Startup

```python
from license_client import LicenseClient, LicenseError

client = LicenseClient(
    server_url="https://your-license-server.com",
    license_key="XXXX-XXXX-XXXX-XXXX",
    cache_file="~/.myapp/license.json"
)

try:
    client.require_valid_license()
except LicenseError as e:
    print(f"License required: {e}")
    exit(1)

# Your application code here
```

### Handling Specific Errors

```python
from license_client import (
    LicenseClient,
    InvalidLicenseError,
    LicenseAlreadyActiveError,
    LicenseRevokedError,
    DeviceNotAuthorizedError,
    NetworkError,
)

client = LicenseClient("https://your-license-server.com")

try:
    client.activate("XXXX-XXXX-XXXX-XXXX")
except InvalidLicenseError:
    print("The license key is invalid")
except LicenseAlreadyActiveError:
    print("This license is already in use on another device")
except LicenseRevokedError:
    print("This license has been revoked by the administrator")
except NetworkError:
    print("Could not connect to the license server")
```

### Deactivation

```python
# Deactivate to transfer license to another device
client.deactivate()
```

## API Reference

### LicenseClient

#### Constructor

```python
LicenseClient(
    server_url: str,
    license_key: Optional[str] = None,
    cache_file: Optional[str] = None,
    timeout: int = 30
)
```

- `server_url`: Base URL of the license server
- `license_key`: Pre-configured license key
- `cache_file`: Path to store activation data locally
- `timeout`: Request timeout in seconds

#### Methods

| Method | Description |
|--------|-------------|
| `activate(license_key)` | Activate a license on this device |
| `deactivate()` | Deactivate the license from this device |
| `validate()` | Validate the license is active |
| `is_valid()` | Check if valid without raising exceptions |
| `require_valid_license()` | Raise exception if license is invalid |

### DeviceFingerprint

Access device hardware identifiers:

```python
from license_client import DeviceFingerprint

fp = DeviceFingerprint()
print(f"CPU ID: {fp.cpu_id}")
print(f"Disk Serial: {fp.disk_serial}")
print(f"Motherboard ID: {fp.motherboard_id}")
print(f"MAC Address: {fp.mac_address}")
print(f"Device ID: {fp.device_id}")
```

## License

MIT License
