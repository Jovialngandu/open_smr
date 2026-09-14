from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from api.models import (
    UserOrganizationRole,
    UserScopeAccess,
    TreatmentTask,
    Scope,
    Risk,
)


def check_scope_access(user, scope):
    """
    Vérifie que l'utilisateur possède un accès actif au scope donné.
    Les superusers ont un accès global.
    """
    if user.is_superuser:
        return

    has_access = UserScopeAccess.objects.filter(
        user_organization_role__user=user,
        user_organization_role__is_active=True,
        scope=scope,
    ).exists()

    if not has_access:
        raise PermissionDenied(
            "Vous n'avez pas accès à ce périmètre."
        )


def user_can_access_scope(user, scope_id, allowed_roles=None):
    if user.is_superuser:
        return True

    role_query = UserOrganizationRole.objects.filter(
        user=user,
        organization__scopes__id=scope_id,
        is_active=True
    )

    if allowed_roles:
        role_query = role_query.filter(role__in=allowed_roles)

    if role_query.filter(role__in=['ADMIN', 'RSSI']).exists():
        return True

    return UserScopeAccess.objects.filter(
        scope_id=scope_id,
        user_organization_role__user=user,
        user_organization_role__is_active=True,
        **(
            {'user_organization_role__role__in': allowed_roles}
            if allowed_roles
            else {}
        ),
    ).exists()


class IsAccountActive(BasePermission):
    """
    Vérifie que le compte utilisateur global est actif.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.user.is_active:
            return False

        if request.user.is_superuser:
            return True

        return True


class HasRole(BasePermission):
    """
    Permission RBAC dynamique par organisation.
    """

    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        org_id = view.kwargs.get('org_id') or view.kwargs.get('pk')

        if not org_id:
            return True

        user_roles = UserOrganizationRole.objects.filter(
            user=request.user,
            organization_id=org_id,
            is_active=True
        ).values_list('role', flat=True)

        if not user_roles:
            return False

        return any(
            role in self.allowed_roles
            for role in user_roles
        )


class IsAdminRole(HasRole):
    allowed_roles = ['ADMIN']


class IsRssiRole(HasRole):
    allowed_roles = ['ADMIN', 'RSSI']


class IsRiskOwnerRole(HasRole):
    allowed_roles = ['ADMIN', 'RSSI', 'RISK_OWNER']


class IsAuditorRole(HasRole):
    allowed_roles = ['ADMIN', 'RSSI', 'AUDITOR']


class CanUpdateTaskStatusPermission(BasePermission):
    """
    Vérifie les accès spécifiques à TreatmentTask.
    """

    def has_object_permission(
        self,
        request,
        view,
        obj: TreatmentTask
    ):
        user = request.user

        if obj.assignee_id == user.id:
            return True

        return user_can_access_scope(
            user,
            obj.risk.asset.scope_id,
            ['ADMIN', 'RSSI']
        )


class CanCreateTreatmentTaskPermission(BasePermission):
    def has_permission(self, request, view):
        if (
            not request.user
            or not request.user.is_authenticated
            or not request.user.is_active
        ):
            return False

        risk_id = request.data.get('risk')

        risk = Risk.objects.select_related(
            'asset__scope'
        ).filter(
            id=risk_id
        ).first()

        return bool(
            risk and user_can_access_scope(
                request.user,
                risk.asset.scope_id,
                ['ADMIN', 'RSSI']
            )
        )


class HasRequestedScopeAccessPermission(BasePermission):
    def has_permission(self, request, view):
        if (
            not request.user
            or not request.user.is_authenticated
            or not request.user.is_active
        ):
            return False

        scope_id = request.query_params.get('scope_id')

        return (
            not scope_id
            or user_can_access_scope(
                request.user,
                scope_id
            )
        )


class HasScopeAccessPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        scope_id = (
            view.kwargs.get('scope_id')
            or view.kwargs.get('pk')
        )

        if not scope_id:
            return True

        if not Scope.objects.filter(id=scope_id).exists():
            return True

        is_org_admin_or_rssi = UserOrganizationRole.objects.filter(
            user=request.user,
            organization__scopes__id=scope_id,
            is_active=True,
            role__in=['ADMIN', 'RSSI']
        ).exists()

        if is_org_admin_or_rssi:
            return True

        return UserScopeAccess.objects.filter(
            scope_id=scope_id,
            user_organization_role__user=request.user,
            user_organization_role__is_active=True
        ).exists()


class CanManageScopeAccessPermission(BasePermission):
    """
    Réserve l'attribution des périmètres
    aux ADMIN et RSSI.
    """

    def has_permission(self, request, view):
        if (
            not request.user
            or not request.user.is_authenticated
            or not request.user.is_active
        ):
            return False

        if request.user.is_superuser:
            return True

        scope_id = view.kwargs.get('pk')

        if not scope_id:
            return False

        return UserOrganizationRole.objects.filter(
            user=request.user,
            organization__scopes__id=scope_id,
            is_active=True,
            role__in=['ADMIN', 'RSSI'],
        ).exists()