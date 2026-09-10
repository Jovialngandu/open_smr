from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from api.models import Organization, UserOrganizationRole
from api.modules.v1.organizations.helpers import generate_unique_org_code

User = get_user_model()


class OrganizationTests(APITestCase):

    def setUp(self):
        # Création des utilisateurs et organisations de base
        self.user_a = User.objects.create_user(
            username="user_a",
            email="usera@example.com",
            password="Password123!",
            is_active=True
        )
        self.user_b = User.objects.create_user(
            username="user_b",
            email="userb@example.com",
            password="Password123!",
            is_active=True
        )
        self.org_a = Organization.objects.create(name="Company A", code="COMP-A")
        UserOrganizationRole.objects.create(
            user=self.user_a,
            organization=self.org_a,
            role='ADMIN',
            is_active=True
        )

    # 1. HELPER GENERATION CODE UNIQUE
    def test_generate_unique_org_code_format(self):
        code = generate_unique_org_code("Organisation Test DGI")
        self.assertTrue(code.startswith("ORGANIS") or code.startswith("ORG"))
        self.assertIn("-", code)
        self.assertTrue(code.isupper())

    # 2. INSCRIPTION + CREATION AUTOMATIQUE D'ORGANISATION
    def test_register_with_organization_auto_code(self):
        url = "/api/v1/auth/register/"
        payload = {
            "username": "newadmin",
            "email": "admin@newco.com",
            "password": "StrongPassword123!",
            "organization_name": "NewCo Enterprise"
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)

        org = Organization.objects.filter(name="NewCo Enterprise").first()
        self.assertIsNotNone(org)
        self.assertIsNotNone(org.code)

        user = User.objects.get(email="admin@newco.com")
        role = UserOrganizationRole.objects.get(user=user, organization=org)
        self.assertEqual(role.role, 'ADMIN')
        self.assertTrue(role.is_active)

    # 3. GESTION DES DOUBLONS DE CODE (RETOUR 400 PROPRE)
    def test_register_duplicate_organization_code_returns_400(self):
        url = "/api/v1/auth/register/"
        payload = {
            "username": "anotheruser",
            "email": "another@example.com",
            "password": "StrongPassword123!",
            "organization_name": "Duplicate Company",
            "organization_code": self.org_a.code
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("organization_code", response.data)

    # 4. ISOLATION MULTI-TENANT & PERMISSIONS RBAC
    def test_user_cannot_access_other_organization_details(self):
        self.client.force_authenticate(user=self.user_b)
        url = reverse('org-detail', kwargs={'pk': self.org_a.id})

        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_list_user_organizations_only_returns_own_orgs(self):
        org_b = Organization.objects.create(name="Company B", code="COMP-B")
        UserOrganizationRole.objects.create(user=self.user_b, organization=org_b, role='ADMIN', is_active=True)

        self.client.force_authenticate(user=self.user_a)
        url = reverse('org-list-create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.org_a.id))

    # 5. BASCULE DE STATUT D'UN MEMBRE
    def test_toggle_member_active_status(self):
        role_b = UserOrganizationRole.objects.create(
            user=self.user_b,
            organization=self.org_a,
            role='AUDITOR',
            is_active=True
        )

        self.client.force_authenticate(user=self.user_a)
        url = reverse('org-member-toggle', kwargs={'org_id': self.org_a.id, 'role_id': role_b.id})

        response = self.client.patch(url, {'is_active': False}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        role_b.refresh_from_db()
        self.assertFalse(role_b.is_active)