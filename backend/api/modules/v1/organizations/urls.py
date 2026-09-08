from django.urls import path
from .views import (
    OrganizationListCreateAPI,
    OrganizationDetailAPI,
    OrganizationMembersAPI,
    MemberStatusToggleAPI
)

urlpatterns = [
    path('', OrganizationListCreateAPI.as_view(), name='org-list-create'),
    path('<uuid:pk>/', OrganizationDetailAPI.as_view(), name='org-detail'),
    path('<uuid:org_id>/members/', OrganizationMembersAPI.as_view(), name='org-members'),
    path('<uuid:org_id>/members/<uuid:role_id>/toggle-status/', MemberStatusToggleAPI.as_view(), name='org-member-toggle'),
]