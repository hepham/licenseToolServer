# Python Style Guide

## Standard
- Follow PEP 8
- Use Black formatter (line length: 88)
- Use isort for import sorting

## Naming Conventions
- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants

## Imports
```python
# Standard library
import os
import sys

# Third-party
from django.db import models
from rest_framework import serializers

# Local
from .models import License
```

## Docstrings
- Use Google-style docstrings
```python
def activate_license(license_key: str, device_id: str) -> bool:
    """Activate a license for a specific device.

    Args:
        license_key: The license key to activate.
        device_id: The unique device identifier.

    Returns:
        True if activation successful, False otherwise.
    """
```

## Type Hints
- Use type hints for function signatures
- Use `Optional[]` for nullable types

## Django Specific
- Models: singular nouns (`License`, `Device`)
- Views: descriptive action names (`LicenseActivationView`)
- Serializers: append `Serializer` suffix
