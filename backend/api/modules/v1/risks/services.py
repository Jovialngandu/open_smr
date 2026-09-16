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
def update_risk(
    *,
    risk: Risk,
    threat_description: str | None = None,
    likelihood: int | None = None,
    impact: int | None = None,
    status: str | None = None,
) -> Risk:
    """
    Met à jour les informations modifiables d'un risque.
    Le score est recalculé automatiquement par le modèle
    à partir de likelihood et impact.
    """

    if threat_description is not None:
        risk.threat_description = threat_description

    if likelihood is not None:
        risk.likelihood = likelihood

    if impact is not None:
        risk.impact = impact

    if status is not None:
        risk.status = status

    risk.save()

    return risk