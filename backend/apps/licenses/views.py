from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import License, Device
from .serializers import (
    ActivationRequestSerializer,
    ActivationResponseSerializer,
    ValidationRequestSerializer,
    ValidationResponseSerializer,
    DeactivationRequestSerializer,
)
from .utils import generate_device_id, hash_fingerprint


class ActivationThrottle(AnonRateThrottle):
    rate = '10/minute'


class ActivateView(APIView):
    """
    POST /api/v1/activate
    Activate a license on a device.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ActivationThrottle]

    @extend_schema(
        tags=['License Activation'],
        summary='Activate a license',
        description='Activate a license key on the requesting device using hardware fingerprint.',
        request=ActivationRequestSerializer,
        responses={
            200: OpenApiResponse(response=ActivationResponseSerializer, description='License activated successfully'),
            400: OpenApiResponse(description='Invalid request data'),
            403: OpenApiResponse(description='License has been revoked'),
            404: OpenApiResponse(description='Invalid license key'),
            409: OpenApiResponse(description='License already activated on another device'),
        }
    )
    def post(self, request):
        serializer = ActivationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'message': 'Invalid request data'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        license_key = data['license_key']
        
        try:
            license_obj = License.objects.get(key=license_key)
        except License.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Invalid license key'},
                status=status.HTTP_404_NOT_FOUND
            )

        if license_obj.status == License.Status.REVOKED:
            return Response(
                {'success': False, 'message': 'This license has been revoked'},
                status=status.HTTP_403_FORBIDDEN
            )

        if license_obj.status == License.Status.ACTIVE:
            return Response(
                {'success': False, 'message': 'This license is already activated on another device'},
                status=status.HTTP_409_CONFLICT
            )

        device_id = generate_device_id(
            data['cpu_id'],
            data['disk_serial'],
            data['motherboard_id'],
            data['mac_address']
        )

        if Device.objects.filter(device_id=device_id).exists():
            return Response(
                {'success': False, 'message': 'This device already has an active license'},
                status=status.HTTP_409_CONFLICT
            )

        fingerprint_data = f"{data['cpu_id']}:{data['disk_serial']}:{data['motherboard_id']}"
        
        Device.objects.create(
            license=license_obj,
            device_id=device_id,
            fingerprint_hash=hash_fingerprint(fingerprint_data),
            mac_address_hash=hash_fingerprint(data['mac_address'])
        )

        license_obj.status = License.Status.ACTIVE
        license_obj.save()

        return Response({
            'success': True,
            'message': 'License activated successfully',
            'license_key': license_key,
            'device_id': device_id
        }, status=status.HTTP_200_OK)


class DeactivateView(APIView):
    """
    POST /api/v1/deactivate
    Deactivate a license from a device.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ActivationThrottle]

    @extend_schema(
        tags=['License Activation'],
        summary='Deactivate a license',
        description='Deactivate a license from the current device to allow activation on another device.',
        request=DeactivationRequestSerializer,
        responses={
            200: OpenApiResponse(response=ActivationResponseSerializer, description='License deactivated successfully'),
            400: OpenApiResponse(description='Missing required fields'),
            404: OpenApiResponse(description='Invalid license key or device not found'),
        }
    )
    def post(self, request):
        license_key = request.data.get('license_key')
        device_id = request.data.get('device_id')

        if not license_key or not device_id:
            return Response(
                {'success': False, 'message': 'license_key and device_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            license_obj = License.objects.get(key=license_key)
        except License.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Invalid license key'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            device = Device.objects.get(license=license_obj, device_id=device_id)
        except Device.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Device not found for this license'},
                status=status.HTTP_404_NOT_FOUND
            )

        device.delete()
        license_obj.status = License.Status.INACTIVE
        license_obj.save()

        return Response({
            'success': True,
            'message': 'License deactivated successfully'
        }, status=status.HTTP_200_OK)


class ValidateView(APIView):
    """
    POST /api/v1/validate
    Validate a license is active on the requesting device.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ActivationThrottle]

    @extend_schema(
        tags=['License Activation'],
        summary='Validate a license',
        description='Check if a license is valid and active on the specified device.',
        request=ValidationRequestSerializer,
        responses={
            200: OpenApiResponse(response=ValidationResponseSerializer, description='License is valid'),
            400: OpenApiResponse(description='Invalid request data or license not active'),
            403: OpenApiResponse(description='License revoked or device not authorized'),
            404: OpenApiResponse(description='Invalid license key'),
        }
    )
    def post(self, request):
        serializer = ValidationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'valid': False, 'message': 'Invalid request data'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        license_key = data['license_key']
        device_id = data['device_id']

        try:
            license_obj = License.objects.get(key=license_key)
        except License.DoesNotExist:
            return Response(
                {'valid': False, 'message': 'Invalid license key'},
                status=status.HTTP_404_NOT_FOUND
            )

        if license_obj.status == License.Status.REVOKED:
            return Response(
                {'valid': False, 'message': 'License has been revoked'},
                status=status.HTTP_403_FORBIDDEN
            )

        if license_obj.status != License.Status.ACTIVE:
            return Response(
                {'valid': False, 'message': 'License is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        device_exists = Device.objects.filter(
            license=license_obj,
            device_id=device_id
        ).exists()

        if not device_exists:
            return Response(
                {'valid': False, 'message': 'License is not activated on this device'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response({
            'valid': True,
            'message': 'License is valid'
        }, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    """
    GET /api/v1/health
    Simple health check endpoint for load balancers and monitoring.
    """
    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(
        tags=['Health'],
        summary='Health check',
        description='Returns OK if the service is running.',
        responses={200: OpenApiResponse(description='Service is healthy')}
    )
    def get(self, request):
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)
