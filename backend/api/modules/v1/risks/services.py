from django.db import transaction
from django.utils import timezone
from api.models import Asset, Risk


def generate_risk_code(asset: Asset) -> str:
    """
    Génère un identifiant unique au format RSK-YYYY-XXX basé sur l'année
    et le nombre de risques existants dans le scope de l'actif.
    """
    current_year = timezone.now().year
    prefix = f"RSK-{current_year}"

    # Compte le nombre de risques déjà créés dans le même scope cette année
    count = Risk.objects.filter(
        asset__scope=asset.scope,
        created_at__year=current_year
    ).count() + 1

    return f"{prefix}-{count:03d}"


@transaction.atomic
def create_risk(
    *,
    asset: Asset,
    threat_description: str,
    likelihood: int,
    impact: int,
    status: str = "OPEN",
) -> Risk:
    """
    Crée un risque associé à un actif avec un code généré automatiquement.
    """
    code = generate_risk_code(asset)

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