from uuid import UUID
from django.db.models import QuerySet
from rest_framework.exceptions import NotFound, PermissionDenied

from api.models import Scope, UserScopeAccess
from django.utils import timezone
from api.models import Risk, SoaEntry, TreatmentTask, Scope
from django.db.models import Q, Count, F, IntegerField, ExpressionWrapper


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
    
    
def get_scope_dashboard_metrics(scope_id):
    # Risques calculés sur score = likelihood * impact
    # HIGH >= 15, MEDIUM >= 8, LOW < 8 (Ajuste les seuils selon tes règles métiers)
    risks_query = Risk.objects.filter(asset__scope_id=scope_id).annotate(
        calculated_score=ExpressionWrapper(F('likelihood') * F('impact'), output_field=IntegerField())
    )
    
    risk_counts = risks_query.aggregate(
        high=Count('id', filter=Q(calculated_score__gte=15)),
        medium=Count('id', filter=Q(calculated_score__gte=8, calculated_score__lt=15)),
        low=Count('id', filter=Q(calculated_score__lt=8))
    )

    # Métriques SoA
    soa_total = SoaEntry.objects.filter(scope_id=scope_id, is_applicable=True).count()
    soa_implemented = SoaEntry.objects.filter(
        scope_id=scope_id, is_applicable=True, implementation_status='IMPLEMENTED'
    ).count()
    soa_percentage = round((soa_implemented / soa_total * 100), 2) if soa_total > 0 else 0.0

    # Tâches en retard
    overdue_tasks_count = TreatmentTask.objects.filter(
        risk__asset__scope_id=scope_id,
        due_date__lt=timezone.now().date()
    ).exclude(status='COMPLETED').count()

    return {
        "risks_by_level": {
            "high": risk_counts['high'] or 0,
            "medium": risk_counts['medium'] or 0,
            "low": risk_counts['low'] or 0,
        },
        "soa_completion": {
            "total_applicable": soa_total,
            "implemented": soa_implemented,
            "percentage": soa_percentage,
        },
        "overdue_tasks_count": overdue_tasks_count,
    }