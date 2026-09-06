import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from api.models.iso27001 import IsoControl


class Command(BaseCommand):
    help = "Charge le référentiel officiel ISO/IEC 27001:2022 (93 contrôles)."

    def handle(self, *args, **options):
        fixture_path = os.path.join(settings.BASE_DIR, 'api', 'fixtures', 'iso_27001_controls.json')

        if not os.path.exists(fixture_path):
            self.stderr.write(self.style.ERROR(f"Fichier fixture introuvable : {fixture_path}"))
            return

        with open(fixture_path, 'r', encoding='utf-8') as f:
            controls = json.load(f)

        created_count = 0
        updated_count = 0

        for item in controls:
            _, created = IsoControl.objects.update_or_create(
                code=item['code'],
                defaults={
                    'title': item['title'],
                    'theme': item['theme'],
                    'description': item['description'],
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"✓ Référentiel ISO 27001 prêt : {created_count} créés, {updated_count} mis à jour."
        ))