from django.urls import path
from api.modules.v1.treatment.views import (
    TreatmentTaskListView,
    TreatmentTaskDetailView,
    TreatmentTaskStatusView,
    EvidenceUploadView,
    TaskEvidenceListView
)

urlpatterns = [
    # Lister les tâches du user connecté (ou ?risk_id=uuid) / Créer une tâche
    path('tasks/', TreatmentTaskListView.as_view(), name='treatment-tasks-list'),
    
    # Détail d'une tâche spécifique par ID
    path('tasks/<uuid:pk>/', TreatmentTaskDetailView.as_view(), name='treatment-task-detail'),
    
    # Changer le statut d'une tâche
    path('tasks/<uuid:pk>/status/', TreatmentTaskStatusView.as_view(), name='treatment-task-update-status'),
    
    # Upload et listing des preuves (evidences)
    path('evidences/', EvidenceUploadView.as_view(), name='treatment-evidence-upload'),
    path('tasks/<uuid:task_id>/evidences/', TaskEvidenceListView.as_view(), name='treatment-task-evidences-list'),
]