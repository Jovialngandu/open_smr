from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.modules.v1.treatments.selectors import (
    list_tasks_by_risk,
    list_tasks_by_assignee,
    get_task_by_id,
    get_task_evidences
)
from api.modules.v1.treatments.services import (
    create_treatment_task,
    update_task_status,
    upload_evidence_file
)
from api.modules.v1.treatments.serializers import (
    TreatmentTaskSerializer,
    CreateTreatmentTaskSerializer,
    UpdateTaskStatusSerializer,
    EvidenceSerializer,
    EvidenceUploadSerializer
)
from api.modules.v1.permissions import IsAccountActive, IsAdminRole, CanUpdateTaskStatusPermission

class TreatmentTaskListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Lister toutes les tâches (de l'utilisateur connecté ou par risque)",
        parameters=[
            OpenApiParameter(name='risk_id', type=str, required=False, description="Filtrer par un risque spécifique"),
        ],
        responses={200: TreatmentTaskSerializer(many=True)}
    )
    def get(self, request):
        risk_id = request.query_params.get('risk_id')

        if risk_id:
            tasks = list_tasks_by_risk(risk_id=risk_id)
        else:
            # Récupère par défaut TOUTES les tâches de l'utilisateur connecté
            tasks = list_tasks_by_assignee(user_id=request.user.id)

        return Response(TreatmentTaskSerializer(tasks, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Créer une tâche de traitement",
        request=CreateTreatmentTaskSerializer,
        responses={201: TreatmentTaskSerializer}
    )
    def post(self, request):
        serializer = CreateTreatmentTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = create_treatment_task(
            title=serializer.validated_data['title'],
            description=serializer.validated_data['description'],
            risk_id=str(serializer.validated_data['risk'].id),
            iso_control_id=str(serializer.validated_data['iso_control'].id),
            assignee_id=str(serializer.validated_data['assignee'].id) if serializer.validated_data.get('assignee') else None,
            due_date=serializer.validated_data.get('due_date')
        )
        return Response(TreatmentTaskSerializer(task).data, status=status.HTTP_201_CREATED)


class TreatmentTaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtenir le détail d'une tâche de traitement par son ID",
        responses={200: TreatmentTaskSerializer}
    )
    def get(self, request, pk):
        task = get_task_by_id(task_id=pk)
        if not task:
            raise NotFound("Tâche de traitement introuvable.")
        return Response(TreatmentTaskSerializer(task).data, status=status.HTTP_200_OK)




class EvidenceUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Uploader un fichier de preuve pour une tâche",
        request=EvidenceUploadSerializer,
        responses={201: EvidenceSerializer}
    )
    def post(self, request):
        serializer = EvidenceUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        evidence = upload_evidence_file(
            task_id=str(serializer.validated_data['task_id']),
            file_path=serializer.validated_data['file_path'],
            description=serializer.validated_data.get('description'),
            uploaded_by=request.user
        )
        return Response(EvidenceSerializer(evidence).data, status=status.HTTP_201_CREATED)


class TaskEvidenceListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Lister les preuves d'une tâche",
        responses={200: EvidenceSerializer(many=True)}
    )
    def get(self, request, task_id):
        evidences = get_task_evidences(task_id=task_id)
        return Response(EvidenceSerializer(evidences, many=True).data, status=status.HTTP_200_OK)
    
    
# class TreatmentTaskStatusView(APIView):
#     permission_classes = [IsAuthenticated]

#     @extend_schema(
#         summary="Mettre à jour le statut d'une tâche",
#         request=UpdateTaskStatusSerializer,
#         responses={200: TreatmentTaskSerializer}
#     )
#     def patch(self, request, pk):
#         serializer = UpdateTaskStatusSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         task = update_task_status(
#             task_id=pk,
#             new_status=serializer.validated_data['status']
#         )
#         return Response(TreatmentTaskSerializer(task).data, status=status.HTTP_200_OK)



class TreatmentTaskStatusView(APIView):
    # Combinaison DRF : Compte actif AND (Admin de l'Org OR Assigné/Scope)
    permission_classes = [IsAccountActive & (IsAdminRole | CanUpdateTaskStatusPermission)]

    @extend_schema(
        summary="Mettre à jour le statut d'une tâche",
        request=UpdateTaskStatusSerializer,
        responses={200: TreatmentTaskSerializer}
    )
    def patch(self, request, pk):
        # 1. Récupération de l'objet
        task = get_task_by_id(task_id=pk)
        if not task:
            raise NotFound("Tâche de traitement introuvable.")

        # Injection dynamique de l'org_id pour les permissions globales (ex: IsAdminRole)
        self.kwargs['org_id'] = task.risk.asset.scope.organization_id

        # 2. Vérification des permissions objet (Déclenche has_object_permission)
        self.check_object_permissions(request, task)

        # 3. Validation des données du serializer
        serializer = UpdateTaskStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 4. Exécution du service de mise à jour
        updated_task = update_task_status(
            task_id=pk,
            new_status=serializer.validated_data['status']
        )
        return Response(TreatmentTaskSerializer(updated_task).data, status=status.HTTP_200_OK)
