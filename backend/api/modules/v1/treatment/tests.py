from datetime import date
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.organization import Scope, Organization
from api.models.iso27001 import Asset, Risk, IsoControl, SoaEntry, TreatmentTask, Evidence

User = get_user_model()


class TreatmentTaskApiTests(APITestCase):

    def setUp(self):
        # Création des utilisateurs
        self.user = User.objects.create_user(
            username="user_test",
            email="user@example.com",
            password="Password123!"
        )
        self.other_user = User.objects.create_user(
            username="other_user",
            email="other@example.com",
            password="Password123!"
        )

        # Création de l'organisation
        self.organization = Organization.objects.create(
            name="Entreprise Test"
        )

        # Création des entités ISO 27001
        self.scope = Scope.objects.create(
            organization=self.organization,
            name="Périmètre SI principal"
        )
        self.asset = Asset.objects.create(
            scope=self.scope,
            owner=self.user,
            name="Serveur Web",
            category="HARDWARE"
        )
        self.risk = Risk.objects.create(
            asset=self.asset,
            code="RISK-001",
            threat_description="Accès non autorisé",
            likelihood=3,
            impact=4
        )
        self.iso_control = IsoControl.objects.create(
            code="A.5.1",
            title="Politiques de sécurité de l'information",
            theme="ORGANIZATIONAL",
            description="Définir et réviser les politiques"
        )
        self.soa_entry = SoaEntry.objects.create(
            scope=self.scope,
            iso_control=self.iso_control,
            is_applicable=True,
            implementation_status='NOT_IMPLEMENTED'
        )

        # Première tâche de traitement de test
        self.task = TreatmentTask.objects.create(
            risk=self.risk,
            iso_control=self.iso_control,
            assignee=self.user,
            title="Rédiger la politique",
            description="Description de la tâche",
            due_date=date.today()
        )

        # URLs
        self.url_list_create = reverse('treatment-tasks-list')
        self.url_detail = reverse('treatment-task-detail', kwargs={'pk': self.task.id})
        self.url_status = reverse('treatment-task-update-status', kwargs={'pk': self.task.id})

    def test_list_tasks_for_authenticated_user(self):
        """Vérifie que l'utilisateur reçoit uniquement ses tâches assignées par défaut."""
        TreatmentTask.objects.create(
            risk=self.risk,
            iso_control=self.iso_control,
            assignee=self.other_user,
            title="Tâche autre user",
            description="Desc"
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_list_create)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.task.id))

    def test_filter_tasks_by_risk_id(self):
        """Vérifie le filtrage des tâches par `risk_id`."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"{self.url_list_create}?risk_id={self.risk.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['risk_code'], "RISK-001")

    def test_get_task_detail(self):
        """Vérifie la récupération du détail d'une tâche par son ID."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_detail)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Rédiger la politique")
        self.assertEqual(response.data['iso_control_code'], "A.5.1")

    def test_create_treatment_task(self):
        """Vérifie la création d'une nouvelle tâche de traitement."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'title': 'Nouvelle tâche',
            'description': 'Mettre en place la revue d acces',
            'risk': str(self.risk.id),
            'iso_control': str(self.iso_control.id),
            'assignee': str(self.user.id),
            'due_date': str(date.today())
        }
        response = self.client.post(self.url_list_create, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Nouvelle tâche')
        self.assertEqual(response.data['status'], 'TODO')

    def test_multi_task_soa_synchronization(self):
        """
        Vérifie que :
        1. Le SoaEntry ne passe à 'IMPLEMENTED' QUE lorsque TOUTES les tâches rattachées sont 'COMPLETED'.
        2. La réouverture d'une tâche repasse le SoaEntry à 'IN_PROGRESS'.
        """
        self.client.force_authenticate(user=self.user)

        # Création d'une deuxième tâche liée au même contrôle ISO et même Scope
        second_task = TreatmentTask.objects.create(
            risk=self.risk,
            iso_control=self.iso_control,
            assignee=self.user,
            title="Valider la politique",
            description="Deuxième étape obligatoire"
        )
        url_status_second = reverse('treatment-task-update-status', kwargs={'pk': second_task.id})

        # Step 1: Compléter la 1ère tâche -> La SoA doit rester inchangée (ou passer à IN_PROGRESS)
        response = self.client.patch(self.url_status, data={'status': 'COMPLETED'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.soa_entry.refresh_from_db()
        self.assertNotEqual(
            self.soa_entry.implementation_status, 
            'IMPLEMENTED', 
            "La SoA ne doit pas être IMPLEMENTED tant que la 2ème tâche reste en TODO/IN_PROGRESS"
        )

        # Step 2: Compléter la 2ème tâche -> Toutes les tâches sont COMPLETED, la SoA doit basculer à IMPLEMENTED
        response = self.client.patch(url_status_second, data={'status': 'COMPLETED'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.soa_entry.refresh_from_db()
        self.assertEqual(
            self.soa_entry.implementation_status, 
            'IMPLEMENTED', 
            "La SoA doit passer à IMPLEMENTED car toutes les tâches sont finies"
        )

        # Step 3: Réouvrir la 1ère tâche (COMPLETED -> IN_PROGRESS) -> La SoA doit repasser à IN_PROGRESS
        response = self.client.patch(self.url_status, data={'status': 'IN_PROGRESS'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.soa_entry.refresh_from_db()
        self.assertEqual(
            self.soa_entry.implementation_status, 
            'IN_PROGRESS', 
            "La SoA doit repasser à IN_PROGRESS lorsqu'une tâche est réouverte"
        )


class EvidenceApiTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user_test",
            email="user@example.com",
            password="Password123!"
        )
        self.organization = Organization.objects.create(name="Entreprise Test")
        self.scope = Scope.objects.create(organization=self.organization, name="Périmètre SI")
        self.asset = Asset.objects.create(scope=self.scope, owner=self.user, name="Serveur", category="HARDWARE")
        self.risk = Risk.objects.create(asset=self.asset, code="R-1", threat_description="T", likelihood=1, impact=1)
        self.iso_control = IsoControl.objects.create(code="A.5.1", title="Politique", theme="ORGANIZATIONAL", description="D")
        
        self.task = TreatmentTask.objects.create(
            risk=self.risk,
            iso_control=self.iso_control,
            assignee=self.user,
            title="Tâche de preuve",
            description="Test upload"
        )

        self.url_upload = reverse('treatment-evidence-upload')
        self.url_list_evidences = reverse('treatment-task-evidences-list', kwargs={'task_id': self.task.id})

    def test_upload_evidence_file(self):
        """Vérifie l'upload d'un fichier de preuve pour une tâche."""
        self.client.force_authenticate(user=self.user)
        
        test_file = SimpleUploadedFile(
            "preuve_audit.pdf",
            b"Contenu du fichier de preuve",
            content_type="application/pdf"
        )
        payload = {
            'task_id': str(self.task.id),
            'file_path': test_file,
            'description': 'Procès verbal de validation'
        }

        response = self.client.post(self.url_upload, data=payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], 'Procès verbal de validation')
        self.assertTrue(Evidence.objects.filter(task=self.task).exists())

    def test_get_task_evidences_list(self):
        """Vérifie la récupération de la liste des preuves d'une tâche."""
        test_file = SimpleUploadedFile("doc.txt", b"Contenu", content_type="text/plain")
        Evidence.objects.create(
            task=self.task,
            uploaded_by=self.user,
            file_path=test_file,
            description="Preuve existante"
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_list_evidences)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['description'], "Preuve existante")
        self.assertEqual(response.data[0]['uploaded_by_email'], self.user.email)