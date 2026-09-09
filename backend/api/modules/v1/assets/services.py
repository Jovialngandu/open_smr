from django.db import transaction
from django.contrib.auth import get_user_model

from api.models import Asset, Scope


User = get_user_model()


@transaction.atomic
def create_asset(
    *,
    scope: Scope,
    owner: User | None,
    name: str,
    category: str,
    description: str | None = None,
    confidentiality: int = 1,
    integrity: int = 1,
    availability: int = 1,
) -> Asset:
    """
    Crée un nouvel actif dans un scope donné.
    """

    asset = Asset.objects.create(
        scope=scope,
        owner=owner,
        name=name,
        category=category,
        description=description,
        confidentiality=confidentiality,
        integrity=integrity,
        availability=availability,
    )

    return asset


@transaction.atomic
def update_asset(
    *,
    asset: Asset,
    owner: User | None = None,
    name: str | None = None,
    category: str | None = None,
    description: str | None = None,
    confidentiality: int | None = None,
    integrity: int | None = None,
    availability: int | None = None,
) -> Asset:
    """
    Met à jour les informations d'un actif existant.
    """

    if owner is not None:
        asset.owner = owner

    if name is not None:
        asset.name = name

    if category is not None:
        asset.category = category

    if description is not None:
        asset.description = description

    if confidentiality is not None:
        asset.confidentiality = confidentiality

    if integrity is not None:
        asset.integrity = integrity

    if availability is not None:
        asset.availability = availability

    asset.save()

    return asset


@transaction.atomic
def delete_asset(*, asset: Asset) -> None:
    """
    Effectue une suppression logique (Soft Delete) de l'actif.
    """

    asset.delete()