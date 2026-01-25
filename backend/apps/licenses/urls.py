from django.urls import path

from .views import ActivateView, DeactivateView, ValidateView, HealthCheckView
from .admin_views import (
    AdminLicenseListCreateView,
    AdminLicenseDetailView,
    AdminLicenseRevokeView,
    AdminLicenseDeactivateView,
    AdminDeviceListView,
    AdminDeleteUnusedLicensesView,
)

urlpatterns = [
    # Health check
    path('health/', HealthCheckView.as_view(), name='health'),
    
    # Public activation endpoints
    path('activate/', ActivateView.as_view(), name='activate'),
    path('deactivate/', DeactivateView.as_view(), name='deactivate'),
    path('validate/', ValidateView.as_view(), name='validate'),
    
    # Admin endpoints
    path('admin/licenses/', AdminLicenseListCreateView.as_view(), name='admin-license-list'),
    path('admin/licenses/unused/', AdminDeleteUnusedLicensesView.as_view(), name='admin-license-delete-unused'),
    path('admin/licenses/<int:id>/', AdminLicenseDetailView.as_view(), name='admin-license-detail'),
    path('admin/licenses/<int:id>/revoke/', AdminLicenseRevokeView.as_view(), name='admin-license-revoke'),
    path('admin/licenses/<int:id>/deactivate/', AdminLicenseDeactivateView.as_view(), name='admin-license-deactivate'),
    path('admin/devices/', AdminDeviceListView.as_view(), name='admin-device-list'),
]
