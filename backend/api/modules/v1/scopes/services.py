from uuid import UUID
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from api.models import Scope, UserScopeAccess, UserOrganizationRole, Organization

User = get_user_model()


@transaction.atomic
def create_scope(
    *, 
    organization_id: UUID, 
    name: str, 
    description: str = "", 
    created_by_user
) -> Scope:
    """
    Crée un Scope et l'associe au rôle de son créateur.
    Note: La génération des 93 entrées SoaEntry est gérée automatiquement via signals.py.
    """
    try:
        org = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        raise ValidationError({"organization_id": "Organisation introuvable."})

    try:
        scope = Scope.objects.create(
            organization=org,
            name=name,
            description=description
        )
    except IntegrityError:
        raise ValidationError({"name": "Un périmètre avec ce nom existe déjà pour cette organisation."})

    user_org_role = UserOrganizationRole.objects.filter(
        user=created_by_user,
        organization=org,
        is_active=True
    ).first()

    if user_org_role:
        UserScopeAccess.objects.get_or_create(
            scope=scope,
            user_organization_role=user_org_role,
            defaults={'granted_by': created_by_user}
        )

    return scope


@transaction.atomic
def update_scope(*, scope: Scope, name: str = None, description: str = None) -> Scope:
    """Met à jour les informations d'un Scope."""
    try:
        if name is not None:
            scope.name = name
        if description is not None:
            scope.description = description

        scope.save()
        return scope
    except IntegrityError:
        raise ValidationError({"name": "Un périmètre avec ce nom existe déjà pour cette organisation."})


@transaction.atomic
def grant_scope_access(*, scope: Scope, user_id: UUID, granted_by_user) -> tuple[UserScopeAccess, bool]:
    """
    Accorde ou met à jour l'accès d'un utilisateur à un Scope via son UserOrganizationRole.
    Retourne un tuple (access, created).
    """
    user_org_role = UserOrganizationRole.objects.filter(
        user_id=user_id,
        organization=scope.organization,
        is_active=True
    ).first()

    if not user_org_role:
        raise ValidationError({"user_id": "L'utilisateur n'a pas de rôle actif dans cette organisation."})

    access, created = UserScopeAccess.objects.update_or_create(
        scope=scope,
        user_organization_role=user_org_role,
        defaults={'granted_by': granted_by_user}
    )

    return access, created


@transaction.atomic
def revoke_scope_access(*, scope: Scope, user_id: UUID) -> None:
    """Révoque l'accès d'un utilisateur à un Scope."""
    UserScopeAccess.objects.filter(
        scope=scope,
        user_organization_role__user_id=user_id
    ).delete()