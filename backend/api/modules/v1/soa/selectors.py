from uuid import UUID

from django.db.models import QuerySet

from api.models import IsoControl, SoaEntry, SoaVersion


def list_iso_controls() -> QuerySet[IsoControl]:
    """
    Retourne tous les contrôles ISO disponibles.
    """
    return IsoControl.objects.all().order_by("code")


def get_soa_entries_by_scope(
    scope_id: UUID,
) -> QuerySet[SoaEntry]:
    """
    Retourne toutes les entrées SoA associées à un scope.
    """
    return (
        SoaEntry.objects
        .filter(scope_id=scope_id)
        .select_related(
            "scope",
            "iso_control",
        )
        .order_by("iso_control__code")
    )


def list_soa_versions(
    scope_id: UUID,
) -> QuerySet[SoaVersion]:
    """
    Retourne les versions historiques de la SoA d'un scope.
    """
    return (
        SoaVersion.objects
        .filter(scope_id=scope_id)
        .select_related(
            "scope",
            "approved_by",
        )
        .order_by("-created_at")
    )