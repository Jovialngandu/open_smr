# api/management/commands/check_overdue_tasks.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import TreatmentTask
from api.modules.v1.emails.services import send_overdue_task_email

class Command(BaseCommand):
    help = "Vérifie les tâches en retard (due_date dépassée) et envoie des alertes aux assignés."

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Filtre sur les tâches non terminées dont l'échéance est dépassée
        overdue_tasks = TreatmentTask.objects.filter(
            due_date__lt=today,
            status__in=['TODO', 'IN_PROGRESS']
        ).select_related('assignee') 

        sent_count = 0
        self.stdout.write(f"Analyse des tâches... {overdue_tasks.count()} tâche(s) en retard trouvée(s).")

        for task in overdue_tasks:
            if task.assignee and task.assignee.email: 
                success = send_overdue_task_email(user=task.assignee, task=task)
                if success:
                    sent_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Traitement terminé. {sent_count} alerte(s) envoyée(s) avec succès.")
        )