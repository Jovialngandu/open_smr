import socket
from datetime import datetime  # <-- REQUIS pour convertir la string en objet date
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

from .selectors import email_log_list, email_log_get
from .serializers import EmailLogSerializer
from .services import send_email, send_overdue_task_email
from .exceptions import EmailServiceError

class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Consultation des logs d'emails (read-only) pour Open SMR.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EmailLogSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        org_id = self.request.query_params.get('organization_id') or getattr(self.request, 'organization_id', None)
        return email_log_list(user_id=user_id, organization_id=org_id)

    @action(detail=False, methods=['post'], url_path='test-overdue-task')
    def test_overdue_task_email(self, request):
        """
        Endpoint pour tester l'envoi d'une alerte de tâche en retard (Due Date).
        """
        user = request.user
        
        # 1. Récupération des données du payload
        task_title = request.data.get('task_title', 'Évaluation de la conformité ISO 27001')
        raw_due_date = request.data.get('due_date', '2026-10-01')

        # 2. Conversion de la chaîne de caractères en véritable objet date pour le .strftime()
        try:
            if isinstance(raw_due_date, str):
                parsed_due_date = datetime.strptime(raw_due_date, "%Y-%m-%d").date()
            else:
                parsed_due_date = raw_due_date
        except ValueError:
            return Response(
                {"detail": "Le format de la date doit être YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Objet factice (Mock) adapté
        class MockTask:
            id = 999
            title = task_title
            due_date = parsed_due_date  # C'est maintenant un vrai objet date
            organization = getattr(user, 'current_organization', None)

        mock_task = MockTask()

        try:
            success = send_overdue_task_email(user=user, task=mock_task)
            if success:
                return Response({
                    'success': True,
                    'message': f"Alerte de tâche en retard envoyée avec succès à {user.email}"
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': "Échec de l'envoi de l'e-mail. Vérifiez les logs du serveur Django pour plus de détails."
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            raise EmailServiceError(f"Erreur lors du test de notification de tâche : {str(e)}")

    @action(detail=False, methods=['get'], url_path='test-port')
    def test_port(self, request):
        try:
            socket.create_connection(("smtp-relay.brevo.com", 587), timeout=5)
            return Response({'detail': "Port 587 (SMTP) est OUVERT"})
        except Exception as e:
            return Response({
                'detail': f"Port 587 (SMTP) BLOQUÉ ({e}). L'utilisation de l'API REST Brevo v3 (port 443) est recommandée sur Render/PaaS."
            }, status=status.HTTP_400_BAD_REQUEST)
