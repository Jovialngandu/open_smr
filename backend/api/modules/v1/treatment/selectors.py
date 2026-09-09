from typing import Optional
from django.db.models import QuerySet
from api.models.iso27001 import TreatmentTask, Evidence


def list_tasks_by_risk(*, risk_id: str) -> QuerySet[TreatmentTask]:
    """Liste les tâches liées à un risque via FK risk."""
    return TreatmentTask.objects.filter(risk_id=risk_id).select_related(
        'risk', 'iso_control', 'assignee'
    ).order_by('-created_at')


def list_tasks_by_assignee(*, user_id: str) -> QuerySet[TreatmentTask]:
    """Liste toutes les tâches assignées à un utilisateur donné."""
    return TreatmentTask.objects.filter(assignee_id=user_id).select_related(
        'risk', 'iso_control', 'assignee'
    ).prefetch_related('evidences').order_by('due_date', '-created_at')


def get_task_by_id(*, task_id: str) -> Optional[TreatmentTask]:
    """Récupère une tâche par sa clé primaire (UUID) avec ses détails."""
    try:
        return TreatmentTask.objects.select_related(
            'risk', 'iso_control', 'assignee'
        ).prefetch_related('evidences').get(id=task_id)
    except TreatmentTask.DoesNotExist:
        return None


def get_task_evidences(*, task_id: str) -> QuerySet[Evidence]:
    """Liste les preuves associées à une tâche via FK task."""
    return Evidence.objects.filter(task_id=task_id).select_related('uploaded_by').order_by('-created_at')