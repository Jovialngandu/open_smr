from django.core.management.base import BaseCommand
from api.models import IsoControl
from backend.services.search.embeddings.selectors import get_embedding_provider


class Command(BaseCommand):
    help = "Génère et stocke les embeddings vectoriels pour les contrôles ISO 27001"

    def handle(self, *args, **options):
        provider = get_embedding_provider()
        controls = IsoControl.objects.all()

        if not controls.exists():
            self.stdout.write(self.style.WARNING("Aucun contrôle ISO trouvé en BDD."))
            return

        self.stdout.write(f"Début de la vectorisation de {controls.count()} contrôles ISO...")

        count = 0
        for control in controls:
            # Texte enrichi pour la représentation vectorielle
            text_to_embed = f"{control.code} {control.title} {control.description} Synonymes et risques associés : {control.keywords}"
            
            try:
                vector = provider.get_embedding(text_to_embed)
                control.embedding = vector
                control.save(update_fields=['embedding'])
                count += 1
                self.stdout.write(f"[{count}/{controls.count()}] Vectorisé : {control.code}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur sur {control.code}: {e}"))

        self.stdout.write(self.style.SUCCESS(f" Vectorisation terminée ! {count} contrôles mis à jour."))