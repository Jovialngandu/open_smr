from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models.iso27001 import IsoControl, SoaEntry
from api.models.organization import Scope


@receiver(post_save, sender=Scope)
def auto_create_soa_entries_for_scope(sender, instance, created, **kwargs):
    if created:
        controls = IsoControl.objects.all()
        soa_entries = [
            SoaEntry(
                scope=instance,
                iso_control=control,
                is_applicable=True,
                implementation_status='NOT_IMPLEMENTED',
                justification="Initialisation automatique du périmètre."
            )
            for control in controls
        ]
        SoaEntry.objects.bulk_create(soa_entries)