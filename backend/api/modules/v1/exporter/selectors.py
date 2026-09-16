from api.models import SoaEntry, SoaVersion

def get_soa_export_data(scope_id):
    entries = SoaEntry.objects.filter(
        scope_id=scope_id
    ).select_related('iso_control').order_by('iso_control__code')

    # Priorité à la dernière version approuvée, sinon la plus récente
    version = SoaVersion.objects.filter(
        scope_id=scope_id, status='APPROVED'
    ).order_by('-created_at').first()

    if not version:
        version = SoaVersion.objects.filter(
            scope_id=scope_id
        ).order_by('-created_at').first()

    version_name = version.version_number if version else "Draft"

    return entries, version_name