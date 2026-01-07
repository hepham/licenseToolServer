from rest_framework import serializers

from .models import License, Device


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'device_id', 'activated_at']
        read_only_fields = ['id', 'device_id', 'activated_at']


class LicenseSerializer(serializers.ModelSerializer):
    device = DeviceSerializer(read_only=True)

    class Meta:
        model = License
        fields = ['id', 'key', 'status', 'created_at', 'updated_at', 'device']
        read_only_fields = ['id', 'key', 'created_at', 'updated_at']


class LicenseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = ['id', 'key', 'status', 'created_at']
        read_only_fields = ['id', 'key', 'status', 'created_at']


class ActivationRequestSerializer(serializers.Serializer):
    license_key = serializers.CharField(max_length=19)
    cpu_id = serializers.CharField(max_length=255, required=False, default="", allow_blank=True)
    disk_serial = serializers.CharField(max_length=255, required=False, default="", allow_blank=True)
    motherboard_id = serializers.CharField(max_length=255, required=False, default="", allow_blank=True)
    
    def validate(self, data):
        hardware_fields = ['cpu_id', 'disk_serial', 'motherboard_id']
        non_empty_count = sum(1 for f in hardware_fields if data.get(f, "").strip())
        if non_empty_count == 0:
            raise serializers.ValidationError("At least one hardware identifier is required")
        return data


class ActivationResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    license_key = serializers.CharField(required=False)
    device_id = serializers.CharField(required=False)


class ValidationRequestSerializer(serializers.Serializer):
    license_key = serializers.CharField(max_length=19)
    device_id = serializers.CharField(max_length=64)


class ValidationResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    message = serializers.CharField()


class DeactivationRequestSerializer(serializers.Serializer):
    license_key = serializers.CharField(max_length=19)
    device_id = serializers.CharField(max_length=64)
