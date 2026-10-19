from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Organization, OrganizationInvitation, UserOrganizationRole
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
        # Génération du code via le helper pour l'organisation de test
        self.org_a_code = generate_unique_org_code("Company A")
        self.org_a = Organization.objects.create(name="Company A", code=self.org_a_code)
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

    # 2. INSCRIPTION + CREATION AUTOMATIQUE D'ORGANISATION (SANS CODE ENVOYÉ)
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
        self.assertTrue(org.code.startswith("NEWCO"))

        user = User.objects.get(email="admin@newco.com")
        role = UserOrganizationRole.objects.get(user=user, organization=org)
        self.assertEqual(role.role, 'ADMIN')
        self.assertTrue(role.is_active)

    # 3. CREATION VIA API ENDPOINT (CODE GENERE AUTOMATIQUEMENT)
    def test_create_organization_api_auto_generates_code(self):
        self.client.force_authenticate(user=self.user_a)
        url = reverse('org-list-create')
        payload = {
            "name": "Tech Corp",
            "description": "Société technologique"
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("code", response.data)
        self.assertTrue(response.data["code"].startswith("TECHCO"))

    # 4. ISOLATION MULTI-TENANT & PERMISSIONS RBAC
    def test_user_cannot_access_other_organization_details(self):
        self.client.force_authenticate(user=self.user_b)
        url = reverse('org-detail', kwargs={'pk': self.org_a.id})

        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_list_user_organizations_only_returns_own_orgs(self):
        org_b_code = generate_unique_org_code("Company B")
        org_b = Organization.objects.create(name="Company B", code=org_b_code)
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

    def test_owner_can_delete_organization(self):
        self.client.force_authenticate(user=self.user_a)
        url = reverse('org-detail', kwargs={'pk': self.org_a.id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Organization.objects.filter(id=self.org_a.id).exists())

    def test_non_owner_cannot_delete_organization(self):
        self.client.force_authenticate(user=self.user_b)
        url = reverse('org-detail', kwargs={'pk': self.org_a.id})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Organization.objects.filter(id=self.org_a.id).exists())

    @patch('api.modules.v1.organizations.services.send_email')
    def test_create_organization_invitation_sends_email_and_creates_record(self, mock_send_email):
        mock_send_email.return_value = True
        self.client.force_authenticate(user=self.user_a)
        url = reverse('org-invitation-create', kwargs={'org_id': self.org_a.id})

        response = self.client.post(
            url,
            {'invited_user_email': 'newmember@example.com', 'role': 'AUDITOR'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invitation = OrganizationInvitation.objects.get(
            organization=self.org_a,
            invited_user_email='newmember@example.com',
            status=OrganizationInvitation.Status.PENDING,
        )
        self.assertEqual(invitation.role, 'AUDITOR')
        mock_send_email.assert_called_once()

    def test_accept_invitation_adds_user_to_organization_with_invited_role(self):
        invited_user = User.objects.create_user(
            username='new_member',
            email='newmember@example.com',
            password='Password123!',
            is_active=True,
        )
        invitation = OrganizationInvitation.objects.create(
            organization=self.org_a,
            invited_by=self.user_a,
            invited_user_email='newmember@example.com',
            role='AUDITOR',
            expires_at=timezone.now() + timedelta(days=7),
        )

        self.client.force_authenticate(user=invited_user)
        url = reverse('org-invitation-accept')
        response = self.client.post(url, {'token': str(invitation.token)}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(UserOrganizationRole.objects.filter(
            user=invited_user,
            organization=self.org_a,
            role='AUDITOR',
            is_active=True,
        ).exists())
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, OrganizationInvitation.Status.ACCEPTED)