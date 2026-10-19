from uuid import UUID

from django.db.models import QuerySet

from api.models import Organization, OrganizationInvitation, UserOrganizationRole


def get_organization_by_id(org_id: UUID) -> Organization:
    """Récupère une organisation par son ID."""
    return Organization.objects.get(id=org_id)


def list_user_organizations(user) -> QuerySet[Organization]:
    """Rend la liste des organisations auxquelles un utilisateur appartient et où son accès est actif."""
    return Organization.objects.filter(
        user_roles__user=user,
        user_roles__is_active=True
    ).distinct()


def get_organization_members(org_id: UUID) -> QuerySet[UserOrganizationRole]:
    """Rend la liste des membres (avec leurs rôles) d'une organisation donnée."""
    return UserOrganizationRole.objects.filter(
        organization_id=org_id
    ).select_related('user')


def get_invitation_by_token(token: str) -> OrganizationInvitation:
    """Récupère une invitation via son token UUID."""
    return OrganizationInvitation.objects.select_related('organization', 'invited_by').get(token=token)


def get_pending_invitation_by_token(token: str) -> OrganizationInvitation:
    """Récupère une invitation PENDING active via token."""
    return OrganizationInvitation.objects.select_related('organization', 'invited_by').get(
        token=token,
        status=OrganizationInvitation.Status.PENDING,
    )