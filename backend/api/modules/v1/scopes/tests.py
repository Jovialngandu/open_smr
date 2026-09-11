from datetime import timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import (
    Asset,
    IsoControl,
    Organization,
    Risk,
    Scope,
    SoaEntry,
    TreatmentTask,
    UserOrganizationRole,
    UserScopeAccess,
)

User = get_user_model()


class ScopeAccessTests(APITestCase):

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin_scope',
            email='admin@example.com',
            password='Password123!',
            is_active=True
        )
        self.target_user = User.objects.create_user(
            username='member_scope',
            email='member@example.com',
            password='Password123!',
            is_active=True
        )

        self.organization = Organization.objects.create(
            name='Entreprise Demo',
            code='ORG-DEMO-001'
        )

        self.admin_role = UserOrganizationRole.objects.create(
            user=self.admin_user,
            organization=self.organization,
            role='ADMIN',
            is_active=True
        )

        self.target_role = UserOrganizationRole.objects.create(
            user=self.target_user,
            organization=self.organization,
            role='AUDITOR',
            is_active=True
        )

        self.scope = Scope.objects.create(
            organization=self.organization,
            name='Périmètre ISO 27001',
            description='Scope de test pour audit'
        )

        # Asset
        self.asset = Asset.objects.create(
            scope=self.scope,
            owner=self.admin_user,
            name='Serveur Base de Données',
            category='HARDWARE',
            confidentiality=3,
            integrity=3,
            availability=2
        )

        # Risques (High: 5*5=25, Medium: 3*3=9, Low: 1*1=1)
        self.risk_high = Risk.objects.create(
            asset=self.asset,
            code='RISK-001',
            threat_description='Injection SQL',
            likelihood=5,
            impact=5,
            status='OPEN'
        )
        self.risk_medium = Risk.objects.create(
            asset=self.asset,
            code='RISK-002',
            threat_description='Panne Électrique',
            likelihood=3,
            impact=3,
            status='IN_MITIGATION'
        )
        self.risk_low = Risk.objects.create(
            asset=self.asset,
            code='RISK-003',
            threat_description='Erreur de Saisie',
            likelihood=1,
            impact=1,
            status='OPEN'
        )

        # Contrôles ISO & Entrées SoA
        self.control1 = IsoControl.objects.create(
            code='A.5.1',
            title='Politiques de sécurité',
            theme='ORGANIZATIONAL',
            description='Politiques ISO'
        )
        self.control2 = IsoControl.objects.create(
            code='A.5.2',
            title='Rôles et responsabilités',
            theme='ORGANIZATIONAL',
            description='Rôles ISO'
        )

        SoaEntry.objects.create(
            scope=self.scope,
            iso_control=self.control1,
            is_applicable=True,
            implementation_status='IMPLEMENTED'
        )
        SoaEntry.objects.create(
            scope=self.scope,
            iso_control=self.control2,
            is_applicable=True,
            implementation_status='IN_PROGRESS'
        )

        # Tâches (1 en retard, 1 valide)
        TreatmentTask.objects.create(
            risk=self.risk_high,
            iso_control=self.control1,
            assignee=self.admin_user,
            title='Corriger la faille SQL',
            description='Correctif applicatif',
            due_date=timezone.now().date() - timedelta(days=5),
            status='IN_PROGRESS'
        )
        TreatmentTask.objects.create(
            risk=self.risk_medium,
            iso_control=self.control2,
            assignee=self.admin_user,
            title='Acheter un onduleur',
            description='Achat matériel',
            due_date=timezone.now().date() + timedelta(days=5),
            status='TODO'
        )

        self.client.force_authenticate(user=self.admin_user)

    def test_grant_scope_access_success(self):
        url = reverse('scope-access', kwargs={'pk': self.scope.pk})
        payload = {'user_id': self.target_user.id}

        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            UserScopeAccess.objects.filter(
                scope=self.scope,
                user_organization_role=self.target_role
            ).exists()
        )

    def test_list_scope_accesses(self):
        UserScopeAccess.objects.create(
            scope=self.scope,
            user_organization_role=self.target_role,
            granted_by=self.admin_user
        )

        url = reverse('scope-access', kwargs={'pk': self.scope.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        self.assertEqual(response.data[0]['user']['id'], str(self.target_user.id))

    def test_delete_scope_success(self):
        url = reverse('scope-detail', kwargs={'pk': self.scope.pk})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Scope.objects.filter(pk=self.scope.pk).exists())

    def test_get_dashboard_metrics_success(self):
        url = reverse('scope-dashboard-metrics', kwargs={'scope_id': self.scope.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['risks_by_level']['high'], 1)
        self.assertEqual(response.data['risks_by_level']['medium'], 1)
        self.assertEqual(response.data['risks_by_level']['low'], 1)

        self.assertEqual(response.data['soa_completion']['total_applicable'], 2)
        self.assertEqual(response.data['soa_completion']['implemented'], 1)
        self.assertEqual(response.data['soa_completion']['percentage'], 50.0)

        self.assertEqual(response.data['overdue_tasks_count'], 1)

    def test_get_dashboard_metrics_forbidden_user(self):
        unauthorized_user = User.objects.create_user(
            username='unauthorized',
            email='unauthorized@example.com',
            password='Password123!',
            is_active=True
        )
        self.client.force_authenticate(user=unauthorized_user)

        url = reverse('scope-dashboard-metrics', kwargs={'scope_id': self.scope.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_dashboard_metrics_not_found(self):
        import uuid
        fake_id = uuid.uuid4()

        url = reverse('scope-dashboard-metrics', kwargs={'scope_id': fake_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)