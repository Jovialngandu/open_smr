from django.urls import path
from .views import (
    MemberStatusToggleAPI,
    OrganizationDetailAPI,
    OrganizationInvitationAcceptAPI,
    OrganizationInvitationCreateAPI,
    OrganizationInvitationDeclineAPI,
    OrganizationListCreateAPI,
    OrganizationMembersAPI,
)

urlpatterns = [
    path('', OrganizationListCreateAPI.as_view(), name='org-list-create'),
    path('<uuid:pk>/', OrganizationDetailAPI.as_view(), name='org-detail'),
    path('<uuid:org_id>/members/', OrganizationMembersAPI.as_view(), name='org-members'),
    path('<uuid:org_id>/members/<uuid:role_id>/toggle-status/', MemberStatusToggleAPI.as_view(), name='org-member-toggle'),
    path('<uuid:org_id>/invitations/', OrganizationInvitationCreateAPI.as_view(), name='org-invitation-create'),
    path('invitations/accept/', OrganizationInvitationAcceptAPI.as_view(), name='org-invitation-accept'),
    path('invitations/decline/', OrganizationInvitationDeclineAPI.as_view(), name='org-invitation-decline'),
]