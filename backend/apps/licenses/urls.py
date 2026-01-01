from django.urls import path

from .views import ActivateView, DeactivateView, ValidateView
from .admin_views import (
    AdminLicenseListCreateView,
    AdminLicenseDetailView,
    AdminLicenseRevokeView,
    AdminDeviceListView,
)

urlpatterns = [
    # Public activation endpoints
    path('activate/', ActivateView.as_view(), name='activate'),
    path('deactivate/', DeactivateView.as_view(), name='deactivate'),
    path('validate/', ValidateView.as_view(), name='validate'),
    
    # Admin endpoints
    path('admin/licenses/', AdminLicenseListCreateView.as_view(), name='admin-license-list'),
    path('admin/licenses/<int:id>/', AdminLicenseDetailView.as_view(), name='admin-license-detail'),
    path('admin/licenses/<int:id>/revoke/', AdminLicenseRevokeView.as_view(), name='admin-license-revoke'),
    path('admin/devices/', AdminDeviceListView.as_view(), name='admin-device-list'),
]
