from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Organization, Scope, UserOrganizationRole, UserScopeAccess

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