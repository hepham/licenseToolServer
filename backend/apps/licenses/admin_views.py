from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import License, Device
from .serializers import (
    LicenseSerializer,
    LicenseCreateSerializer,
    DeviceSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=['Admin'],
        summary='List all licenses',
        description='Get a list of all licenses with their status and device information.',
    ),
    create=extend_schema(
        tags=['Admin'],
        summary='Generate new license',
        description='Generate a new license key. The key is automatically generated in XXXX-XXXX-XXXX-XXXX format.',
        request=None,
        responses={201: LicenseSerializer},
    ),
)
class AdminLicenseListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/admin/licenses - List all licenses
    POST /api/v1/admin/licenses - Generate new license
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = License.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LicenseCreateSerializer
        return LicenseSerializer

    def create(self, request, *args, **kwargs):
        license_obj = License.objects.create()
        serializer = LicenseSerializer(license_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    retrieve=extend_schema(
        tags=['Admin'],
        summary='Get license details',
        description='Get detailed information about a specific license including its device.',
    ),
)
class AdminLicenseDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/v1/admin/licenses/{id} - Get license details
    DELETE /api/v1/admin/licenses/{id} - Delete a license
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = License.objects.all()
    serializer_class = LicenseSerializer
    lookup_field = 'id'

    @extend_schema(
        tags=['Admin'],
        summary='Delete a license',
        description='Permanently delete a license and all associated device activations.',
        responses={
            204: OpenApiResponse(description='License deleted successfully'),
            404: OpenApiResponse(description='License not found'),
        }
    )
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class AdminLicenseRevokeView(APIView):
    """
    DELETE /api/v1/admin/licenses/{id}/revoke - Revoke a license
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        tags=['Admin'],
        summary='Revoke a license',
        description='Revoke a license and remove all associated device activations.',
        responses={
            200: OpenApiResponse(description='License revoked successfully'),
            404: OpenApiResponse(description='License not found'),
        }
    )
    def delete(self, request, id):
        try:
            license_obj = License.objects.get(id=id)
        except License.DoesNotExist:
            return Response(
                {'error': 'License not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        license_obj.devices.all().delete()
        license_obj.status = License.Status.REVOKED
        license_obj.save()

        return Response(
            {'message': 'License revoked successfully'},
            status=status.HTTP_200_OK
        )


class AdminLicenseDeactivateView(APIView):
    """
    POST /api/v1/admin/licenses/{id}/deactivate - Deactivate a license (reset to INACTIVE)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        tags=['Admin'],
        summary='Deactivate a license',
        description='Deactivate a license, removing device binding and setting status to INACTIVE.',
        responses={
            200: OpenApiResponse(description='License deactivated successfully'),
            404: OpenApiResponse(description='License not found'),
            400: OpenApiResponse(description='License is not active'),
        }
    )
    def post(self, request, id):
        try:
            license_obj = License.objects.get(id=id)
        except License.DoesNotExist:
            return Response(
                {'error': 'License not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if license_obj.status != License.Status.ACTIVE:
            return Response(
                {'error': 'License is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        license_obj.devices.all().delete()
        license_obj.status = License.Status.INACTIVE
        license_obj.save()

        return Response(
            {'message': 'License deactivated successfully'},
            status=status.HTTP_200_OK
        )


@extend_schema_view(
    list=extend_schema(
        tags=['Admin'],
        summary='List all devices',
        description='Get a list of all activated devices.',
    ),
)
class AdminDeviceListView(generics.ListAPIView):
    """
    GET /api/v1/admin/devices - List all devices
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Device.objects.select_related('license').all()
    serializer_class = DeviceSerializer


class AdminDeviceDetailSerializer(DeviceSerializer):
    license_key = LicenseSerializer(source='license', read_only=True)

    class Meta(DeviceSerializer.Meta):
        fields = ['id', 'device_id', 'activated_at', 'license_key']


class AdminDeleteUnusedLicensesView(APIView):
    """
    DELETE /api/v1/admin/licenses/unused - Delete all unused (inactive) licenses
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        tags=['Admin'],
        summary='Delete unused licenses',
        description='Delete all licenses that have never been activated (status = inactive).',
        responses={
            200: OpenApiResponse(description='Unused licenses deleted successfully'),
        }
    )
    def delete(self, request):
        deleted_count, _ = License.objects.filter(status=License.Status.INACTIVE).delete()
        return Response(
            {'message': f'{deleted_count} unused license(s) deleted successfully', 'deleted_count': deleted_count},
            status=status.HTTP_200_OK
        )
