from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, ValidationError
from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from api.models.iso27001 import TreatmentTask, Evidence, Risk, IsoControl,SoaEntry

User = get_user_model()


def create_treatment_task(
    *,
    title: str,
    description: str,
    risk_id: str,
    iso_control_id: str,
    assignee_id: str = None,
    due_date=None
) -> TreatmentTask:
    """Crée une tâche de traitement du risque d'après le modèle TreatmentTask."""
    if not Risk.objects.filter(id=risk_id).exists():
        raise NotFound("Risque non trouvé.")
        
    if not IsoControl.objects.filter(id=iso_control_id).exists():
        raise NotFound("Mesure de sécurité (IsoControl) non trouvée.")

    task = TreatmentTask(
        title=title,
        description=description,
        risk_id=risk_id,
        iso_control_id=iso_control_id,
        assignee_id=assignee_id,
        due_date=due_date,
        status='TODO'
    )
    task.full_clean()
    task.save()
    return task


@transaction.atomic
def update_task_status(*, task_id: str, new_status: str) -> TreatmentTask:
    """
    Met à jour le statut d'une tâche et synchronise le statut d'implémentation
    du contrôle SoA associé uniquement si toutes les tâches liées sont terminées.
    """
    try:
        task = TreatmentTask.objects.select_related('risk__asset__scope', 'iso_control').get(id=task_id)
    except TreatmentTask.DoesNotExist:
        raise NotFound("Tâche de traitement introuvable.")

    valid_statuses = [choice[0] for choice in TreatmentTask.STATUS_CHOICES]
    if new_status not in valid_statuses:
        raise ValidationError(f"Statut invalide : {new_status}. Choix possibles: {valid_statuses}")

    # Mise à jour des champs de la tâche
    task.status = new_status
    if new_status == 'COMPLETED':
        task.completed_at = timezone.now()
    else:
        task.completed_at = None

    task.save()

    # Evaluation et synchronisation automatique du SoA
    _sync_soa_implementation_status(scope=task.risk.asset.scope, iso_control=task.iso_control)

    return task


def upload_evidence_file(
    *,
    task_id: str,
    file_path,
    description: str = None,
    uploaded_by: User
) -> Evidence:
    """Création d'une preuve liée à une tâche (modèle Evidence)."""
    try:
        task = TreatmentTask.objects.get(id=task_id)
    except TreatmentTask.DoesNotExist:
        raise NotFound("Tâche de traitement introuvable.")

    evidence = Evidence(
        task=task,
        uploaded_by=uploaded_by,
        file_path=file_path,
        description=description
    )
    evidence.full_clean()
    evidence.save()
    return evidence

def _sync_soa_implementation_status(*, scope, iso_control) -> None:
    """
    Vérifie l'état de l'ensemble des tâches pour un (Scope, IsoControl)
    et aligne le statut de la SoaEntry.
    """
    if not scope or not iso_control:
        return

    # Récupération de toutes les tâches rattachées à ce contrôle pour ce périmètre
    related_tasks = TreatmentTask.objects.filter(
        risk__asset__scope=scope,
        iso_control=iso_control
    )

    total_tasks = related_tasks.count()
    if total_tasks == 0:
        return

    completed_tasks = related_tasks.filter(status='COMPLETED').count()

    # Si TOUTES les tâches sont COMPLETED -> IMPLEMEMTED
    if completed_tasks == total_tasks:
        SoaEntry.objects.filter(
            scope=scope,
            iso_control=iso_control
        ).update(implementation_status='IMPLEMENTED')
    
    # Si une ou plusieurs tâches ne sont pas finies alors que c'était marqué IMPLEMENTED -> IN_PROGRESS
    else:
        SoaEntry.objects.filter(
            scope=scope,
            iso_control=iso_control,
            implementation_status='IMPLEMENTED'
        ).update(implementation_status='IN_PROGRESS')