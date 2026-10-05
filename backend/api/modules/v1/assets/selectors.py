from uuid import UUID

from django.db.models import QuerySet

from api.models import Asset


def get_asset_by_id(asset_id: UUID) -> Asset:
    """
    Récupère un actif à partir de son identifiant UUID.
    """
    return Asset.objects.get(id=asset_id)


def list_assets_by_scope(scope_id: UUID) -> QuerySet[Asset]:
    """
    Retourne tous les actifs appartenant à un scope donné.
    """
    return (
        Asset.objects
        .filter(scope_id=scope_id)
        .select_related("scope", "owner")
    )


def filter_assets_by_category(
    *,
    scope_id: UUID,
    category: str
) -> QuerySet[Asset]:
    """
    Retourne les actifs d'un scope appartenant
    à une catégorie spécifique.
    """
    return (
        Asset.objects
        .filter(
            scope_id=scope_id,
            category=category
        )
        .select_related("scope", "owner")
    )
