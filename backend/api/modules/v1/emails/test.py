from unittest.mock import patch
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command
from django.contrib.auth import get_user_model

from api.models import (
    TreatmentTask,
    EmailLog,
    IsoControl,
    Organization,
    Scope,
    Asset,
    Risk
)
from api.modules.v1.emails.services import send_overdue_task_email

User = get_user_model()


class OverdueTasksTestCase(TestCase):
    def setUp(self):
        """Initialisation des données de test avec l'arborescence requise."""
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123"
        )
        self.today = timezone.now().date()

        # 1. Création de la hiérarchie obligatoire
        self.organization = Organization.objects.create(
            name="Test Org",
            code="ORG_TEST"
        )
        self.scope = Scope.objects.create(
            organization=self.organization,
            name="Test Scope"
        )
        self.asset = Asset.objects.create(
            scope=self.scope,
            name="Serveur Web",
            category="HARDWARE"
        )
        self.risk = Risk.objects.create(
            asset=self.asset,
            code="RISK-001",
            threat_description="Fuite de données",
            likelihood=3,
            impact=4
        )
        self.iso_control = IsoControl.objects.create(
            code="A.5.1",
            title="Politiques de sécurité",
            theme="ORGANIZATIONAL",
            description="Description du contrôle"
        )

        # 2. Tâche en retard et NON terminée (Doit déclencher un mail)
        self.overdue_task = TreatmentTask.objects.create(
            title="Tâche en retard",
            description="Mettre à jour le pare-feu",
            due_date=self.today - timedelta(days=2),
            status="TODO",
            assignee=self.user,
            risk=self.risk,
            iso_control=self.iso_control
        )

        # 3. Tâche en retard mais DÉJÀ TERMINÉE (Ne doit PAS déclencher de mail)
        self.completed_task = TreatmentTask.objects.create(
            title="Tâche terminée à temps",
            description="Corriger la vulnérabilité",
            due_date=self.today - timedelta(days=2),
            status="COMPLETED",
            assignee=self.user,
            risk=self.risk,
            iso_control=self.iso_control
        )

        # 4. Tâche DANS LES TEMPS (Ne doit PAS déclencher de mail)
        self.future_task = TreatmentTask.objects.create(
            title="Tâche future",
            description="Audit annuel",
            due_date=self.today + timedelta(days=3),
            status="IN_PROGRESS",
            assignee=self.user,
            risk=self.risk,
            iso_control=self.iso_control
        )

        # 5. Tâche en retard SANS ASSIGNÉ (Ne doit PAS crasher la commande)
        self.unassigned_task = TreatmentTask.objects.create(
            title="Tâche orpheline",
            description="Vérifier la sauvegarde",
            due_date=self.today - timedelta(days=1),
            status="TODO",
            assignee=None,
            risk=self.risk,
            iso_control=self.iso_control
        )

    @patch('api.modules.v1.emails.services.send_email')
    def test_send_overdue_task_email_service(self, mock_send_email):
        """Vérifie que la fonction de service prépare correctement le contexte."""
        mock_send_email.return_value = True

        result = send_overdue_task_email(user=self.user, task=self.overdue_task)

        self.assertTrue(result)
        mock_send_email.assert_called_once()
        _, kwargs = mock_send_email.call_args
        self.assertEqual(kwargs['recipient_email'], self.user.email)
        self.assertEqual(kwargs['email_type'], EmailLog.EmailType.OVERDUE_TASK_ALERT)

    @patch('api.modules.v1.emails.services.send_email')
    def test_check_overdue_tasks_command(self, mock_send_email):
        """Vérifie que la commande CLI filtre uniquement les tâches éligibles."""
        mock_send_email.return_value = True

        call_command('check_overdue_tasks')

        # Seule la tâche 1 (overdue_task) doit générer un envoi d'e-mail
        self.assertEqual(mock_send_email.call_count, 1)

    @patch('api.modules.v1.emails.providers.brevo.BrevoProvider.send')
    def test_email_log_creation_on_send(self, mock_brevo_send):
        """Vérifie qu'un enregistrement EmailLog est bien créé en BDD."""
        mock_brevo_send.return_value = True

        initial_log_count = EmailLog.objects.count()
        send_overdue_task_email(user=self.user, task=self.overdue_task)

        self.assertEqual(EmailLog.objects.count(), initial_log_count + 1)
        log = EmailLog.objects.latest('created_at')
        self.assertEqual(log.recipient, self.user.email)
        self.assertEqual(log.status, True)
        self.assertEqual(log.email_type, EmailLog.EmailType.OVERDUE_TASK_ALERT)