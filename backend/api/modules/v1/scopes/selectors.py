from uuid import UUID
from django.db.models import QuerySet
from rest_framework.exceptions import NotFound, PermissionDenied

from api.models import Scope, UserScopeAccess


def get_scope_by_id(*, scope_id: UUID, user) -> Scope:
    """Récupère un scope par son ID en vérifiant que l'utilisateur y a accès."""
    try:
        scope = Scope.objects.select_related('organization').get(id=scope_id)
    except Scope.DoesNotExist:
        raise NotFound("Périmètre (Scope) introuvable.")

    is_org_admin = user.org_roles.filter(
        organization=scope.organization, role='ADMIN', is_active=True
    ).exists()

    if not is_org_admin:
        has_access = UserScopeAccess.objects.filter(
            scope=scope, user_organization_role__user=user, user_organization_role__is_active=True
        ).exists()
        if not has_access:
            raise PermissionDenied("Vous n'avez pas accès à ce périmètre (Scope).")

    return scope


def list_scopes_by_organization(*, organization_id: UUID, user) -> QuerySet[Scope]:
    """Liste tous les scopes d'une organisation accessibles par l'utilisateur."""
    is_org_admin = user.org_roles.filter(
        organization_id=organization_id, role='ADMIN', is_active=True
    ).exists()

    if is_org_admin:
        return Scope.objects.filter(organization_id=organization_id)

    accessible_scope_ids = UserScopeAccess.objects.filter(
        user_organization_role__user=user,
        scope__organization_id=organization_id,
        user_organization_role__is_active=True
    ).values_list('scope_id', flat=True)

    return Scope.objects.filter(id__in=accessible_scope_ids)


def list_user_accessible_scopes(*, user) -> QuerySet[Scope]:
    """Liste tous les scopes auxquels l'utilisateur a accès."""
    admin_org_ids = user.org_roles.filter(
        role='ADMIN', is_active=True
    ).values_list('organization_id', flat=True)

    explicit_scope_ids = UserScopeAccess.objects.filter(
        user_organization_role__user=user,
        user_organization_role__is_active=True
    ).values_list('scope_id', flat=True)

    return Scope.objects.filter(
        organization_id__in=admin_org_ids
    ) | Scope.objects.filter(id__in=explicit_scope_ids)