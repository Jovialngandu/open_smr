# api/modules/v1/permissions.py
from rest_framework.permissions import BasePermission
from api.models import UserOrganizationRole, UserScopeAccess, TreatmentTask, Scope

class IsAccountActive(BasePermission):
    """
    Vérifie que le compte utilisateur global est actif (Django user.is_active).
    Permet aux utilisateurs sans organisation/scope d'accéder aux endpoints
    d'initialisation (ex: création d'organisation, liste de leurs orgs).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Le compte Django global doit être actif
        if not request.user.is_active:
            return False

        # Un superuser a un accès global
        if request.user.is_superuser:
            return True

        # Si l'utilisateur n'a aucune organisation, on le laisse quand même accéder 
        # aux fonctionnalités de base (ex: créer ou lister ses orgs).
        # On ne le bloque pas au niveau global.
        return True


class HasRole(BasePermission):
    """
    Permission RBAC dynamique par organisation.
    Si l'utilisateur n'a pas encore d'organisation ou de rôle pour l'organisation ciblée,
    l'accès aux ressources dépendantes de cette organisation est refusé.
    """
    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Récupération de l'org_id depuis les paramètres de l'URL (ex: /organizations/<org_id>/...)
        org_id = view.kwargs.get('org_id') or view.kwargs.get('pk')

        # Si l'action ne cible pas une organisation spécifique (ex: /organizations/ en POST ou GET),
        # on autorise tout utilisateur authentifié à interagir avec le point d'entrée.
        if not org_id:
            return True

        # Si un org_id est présent, l'utilisateur DOIT avoir un rôle actif au sein de CETTE organisation
        user_roles = UserOrganizationRole.objects.filter(
            user=request.user,
            organization_id=org_id,
            is_active=True
        ).values_list('role', flat=True)

        if not user_roles:
            return False

        # Vérification si le rôle dans l'organisation correspond aux autorisations requises
        return any(role in self.allowed_roles for role in user_roles)


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
    Vérifie les accès spécifiques à l'objet TreatmentTask (Assigné direct ou accès au Scope).
    Les accès globaux (Superuser, Admin Org) sont gérés par combinaison dans la vue.
    """
    def has_object_permission(self, request, view, obj: TreatmentTask):
        user = request.user

        # 1. Assignee direct de la tâche
        if obj.assignee_id == user.id:
            return True

        # 2. Accès au Scope de la tâche
        return UserScopeAccess.objects.filter(
            scope=obj.risk.asset.scope,
            user_organization_role__user=user,
            user_organization_role__is_active=True
        ).exists()




class HasScopeAccessPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        scope_id = view.kwargs.get('scope_id') or view.kwargs.get('pk')
        if not scope_id:
            return True

        # Si le scope n'existe pas du tout, laisse la vue gérer la 404
        if not Scope.objects.filter(id=scope_id).exists():
            return True

        # Accès si ADMIN/RSSI dans l'organisation parente
        is_org_admin_or_rssi = UserOrganizationRole.objects.filter(
            user=request.user,
            organization__scopes__id=scope_id,
            is_active=True,
            role__in=['ADMIN', 'RSSI']
        ).exists()

        if is_org_admin_or_rssi:
            return True

        # Accès si affectation directe dans UserScopeAccess
        return UserScopeAccess.objects.filter(
            scope_id=scope_id,
            user_organization_role__user=request.user,
            user_organization_role__is_active=True
        ).exists()