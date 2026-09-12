from django.db import transaction

from api.models import SoaEntry, SoaVersion, Scope


@transaction.atomic
def update_soa_entry(
    *,
    soa_entry: SoaEntry,
    is_applicable: bool | None = None,
    justification: str | None = None,
    implementation_status: str | None = None,
) -> SoaEntry:
    """
    Met à jour une entrée de la Déclaration d'Applicabilité (SoA).
    """

    if is_applicable is not None:
        soa_entry.is_applicable = is_applicable

    if justification is not None:
        soa_entry.justification = justification

    if implementation_status is not None:
        soa_entry.implementation_status = implementation_status

    soa_entry.save()

    return soa_entry


@transaction.atomic
def create_soa_snapshot_version(
    *,
    scope: Scope,
    version_number: str,
    title: str,
    approved_by=None,
    status: str = "DRAFT",
) -> SoaVersion:
    """
    Crée une version figée (snapshot) de la SoA d'un scope.
    """

    entries = (
        SoaEntry.objects
        .filter(scope=scope)
        .select_related("iso_control")
        .order_by("iso_control__code")
    )

    snapshot_data = []

    for entry in entries:
        snapshot_data.append(
            {
                "entry_id": str(entry.id),
                "control_code": entry.iso_control.code,
                "control_title": entry.iso_control.title,
                "control_theme": entry.iso_control.theme,
                "is_applicable": entry.is_applicable,
                "justification": entry.justification,
                "implementation_status": entry.implementation_status,
            }
        )

    soa_version = SoaVersion.objects.create(
        scope=scope,
        approved_by=approved_by,
        version_number=version_number,
        title=title,
        snapshot_data=snapshot_data,
        status=status,
    )

    return soa_version

