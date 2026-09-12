from django.db import transaction

from api.models import Asset, Risk


@transaction.atomic
def create_risk(
    *,
    asset: Asset,
    code: str,
    threat_description: str,
    likelihood: int,
    impact: int,
    status: str = "OPEN",
) -> Risk:
    """
    Crée un risque associé à un actif.
    Le score brut est calculé automatiquement par le modèle :
    score = likelihood * impact
    """

    risk = Risk.objects.create(
        asset=asset,
        code=code,
        threat_description=threat_description,
        likelihood=likelihood,
        impact=impact,
        status=status,
    )

    return risk


@transaction.atomic
def update_risk_status(
    *,
    risk: Risk,
    status: str,
) -> Risk:
    """
    Met à jour le statut d'un risque.
    """

    risk.status = status
    risk.save(update_fields=["status", "updated_at"])

    return risk

