from django.db import models

from .utils import generate_license_key


class License(models.Model):
    """
    Represents a software license that can be activated on a single device.
    """
    class Status(models.TextChoices):
        INACTIVE = 'inactive', 'Inactive'
        ACTIVE = 'active', 'Active'
        REVOKED = 'revoked', 'Revoked'

    key = models.CharField(
        max_length=19,
        unique=True,
        db_index=True,
        help_text="License key in format XXXX-XXXX-XXXX-XXXX"
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.INACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'License'
        verbose_name_plural = 'Licenses'

    def __str__(self):
        return f"{self.key} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = generate_license_key()
        super().save(*args, **kwargs)

    @property
    def is_activated(self) -> bool:
        return self.status == self.Status.ACTIVE

    @property
    def device(self):
        return self.devices.first()


class Device(models.Model):
    """
    Represents a device that has activated a license.
    """
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        related_name='devices'
    )
    device_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Hashed device identifier"
    )
    fingerprint_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of hardware fingerprint"
    )
    mac_address_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of MAC address"
    )
    activated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-activated_at']
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'

    def __str__(self):
        return f"Device {self.device_id[:8]}... for {self.license.key}"
