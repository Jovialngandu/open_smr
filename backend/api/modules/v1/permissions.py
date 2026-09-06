from rest_framework.permissions import BasePermission
from api.models import UserOrganizationRole


class IsAccountActive(BasePermission):
    """Vérifie que l'utilisateur est actif aux niveaux global et organisationnel."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not request.user.is_active:
            return False

        # Si l'utilisateur est un superadmin, accès direct
        if request.user.is_superuser:
            return True

        # Vérification du statut au niveau organisationnel
        active_role = UserOrganizationRole.objects.filter(user=request.user, is_active=True).exists()
        return active_role


class HasRole(BasePermission):
    """Permission générique basée sur les rôles RBAC."""
    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        user_role = UserOrganizationRole.objects.filter(
            user=request.user, 
            is_active=True
        ).first()

        if not user_role:
            return False

        return user_role.role in self.allowed_roles


class IsAdminRole(HasRole):
    allowed_roles = ['ADMIN']


class IsRssiRole(HasRole):
    allowed_roles = ['ADMIN', 'RSSI']


class IsRiskOwnerRole(HasRole):
    allowed_roles = ['ADMIN', 'RSSI', 'RISK_OWNER']


class IsAuditorRole(HasRole):
    allowed_roles = ['ADMIN', 'RSSI', 'AUDITOR']