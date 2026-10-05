from uuid import UUID

from django.db.models import QuerySet

from api.models import Risk


def get_risk_by_id(risk_id: UUID) -> Risk:
    """
    Retourne un risque à partir de son identifiant.
    """
    return (
        Risk.objects
        .select_related(
            "asset",
            "asset__scope",
            "asset__owner",
        )
        .get(id=risk_id)
    )


def list_risks_by_scope(scope_id: UUID) -> QuerySet[Risk]:
    """
    Retourne tous les risques liés à un périmètre.
    """
    return (
        Risk.objects
        .filter(asset__scope_id=scope_id)
        .select_related(
            "asset",
            "asset__scope",
            "asset__owner",
        )
        .order_by("-created_at")
    )


def list_risks_by_asset(asset_id: UUID) -> QuerySet[Risk]:
    """
    Retourne tous les risques liés à un actif.
    """
    return (
        Risk.objects
        .filter(asset_id=asset_id)
        .select_related(
            "asset",
            "asset__scope",
            "asset__owner",
        )
        .order_by("-created_at")
    )