from uuid import UUID
from django.db import transaction
from django.contrib.auth import get_user_model
from api.models import Organization, UserOrganizationRole
from .helpers import generate_unique_org_code

User = get_user_model()


@transaction.atomic
def create_organization(*, name: str, code: str = None, description: str = "", owner_user) -> Organization:
    """Crée une organisation et affecte le créateur en tant qu'ADMIN."""
    final_code = code if code else generate_unique_org_code(name)

    org = Organization.objects.create(
        name=name,
        code=final_code,
        description=description
    )

    UserOrganizationRole.objects.create(
        user=owner_user,
        organization=org,
        role='ADMIN',
        is_active=True
    )
    return org


@transaction.atomic
def update_organization(*, organization: Organization, name: str = None, description: str = None) -> Organization:
    """Met à jour les informations de l'organisation."""
    if name is not None:
        organization.name = name
    if description is not None:
        organization.description = description
    organization.save()
    return organization


@transaction.atomic
def assign_user_role(*, org_id: UUID, user_id: UUID, role: str) -> UserOrganizationRole:
    """Assigne ou met à jour le rôle d'un utilisateur dans une organisation."""
    user_role, created = UserOrganizationRole.objects.update_or_create(
        organization_id=org_id,
        user_id=user_id,
        defaults={'role': role, 'is_active': True}
    )
    return user_role


@transaction.atomic
def toggle_member_active_status(*, role_id: UUID, is_active: bool) -> UserOrganizationRole:
    """Active ou suspend l'accès d'un membre dans l'organisation."""
    user_role = UserOrganizationRole.objects.get(id=role_id)
    user_role.is_active = is_active
    user_role.save()
    return user_role