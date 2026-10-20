from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Organization, OrganizationInvitation, UserOrganizationRole, UserScopeAccess


User = get_user_model()


class OrganizationRegistrationTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Organisation commune', code='COMMUNE-01')

    def test_registration_can_join_an_existing_organization_as_risk_owner(self):
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'nouveau.membre',
            'email': 'membre@example.com',
            'password': 'MotDePasseSolide123!',
            'first_name': 'Nouveau',
            'last_name': 'Membre',
            'join_organization_code': 'commune-01',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='nouveau.membre')
        role = UserOrganizationRole.objects.get(user=user, organization=self.organization)
        self.assertEqual(role.role, 'RISK_OWNER')
        self.assertFalse(UserScopeAccess.objects.filter(user_organization_role=role).exists())

    def test_registration_rejects_create_and_join_at_the_same_time(self):
        response = self.client.post('/api/v1/auth/register/', {
            'username': 'choix.invalide',
            'email': 'invalide@example.com',
            'password': 'MotDePasseSolide123!',
            'organization_name': 'Nouvelle organisation',
            'join_organization_code': 'COMMUNE-01',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='choix.invalide').exists())

    def test_authenticated_user_can_delete_own_account(self):
        user = User.objects.create_user(
            username='selfdelete',
            email='selfdelete@example.com',
            password='MotDePasseSolide123!',
            is_active=True,
        )
        self.client.force_authenticate(user=user)

        response = self.client.delete('/api/v1/auth/me/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=user.id).exists())


class UserSearchPublicApiTests(APITestCase):
    def setUp(self):
        self.user_1 = User.objects.create_user(
            username='alice.dev',
            email='alice@example.com',
            password='MotDePasseSolide123!',
            is_active=True,
        )
        self.user_2 = User.objects.create_user(
            username='bob.admin',
            email='bob@example.com',
            password='MotDePasseSolide123!',
            is_active=True,
        )
        self.user_3 = User.objects.create_user(
            username='charlie',
            email='charlie@company.fr',
            password='MotDePasseSolide123!',
            is_active=True,
        )

    def test_public_user_search_filters_by_username_or_email(self):
        response = self.client.get('/api/v1/users/search/', {'q': 'alice'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'alice.dev')
        self.assertEqual(response.data[0]['email'], 'alice@example.com')

    def test_public_user_search_matches_email(self):
        response = self.client.get('/api/v1/users/search/', {'q': 'company.fr'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'charlie')

    def test_public_user_search_without_q_returns_empty_list(self):
        response = self.client.get('/api/v1/users/search/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class OIDCGoogleAuthTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Google Org', code='GOOGLE-ORG')
        self.existing_user = User.objects.create_user(
            username='google.user',
            email='google.user@example.com',
            password='StrongPassword123!',
            first_name='Google',
            last_name='User',
            is_active=True,
        )
        UserOrganizationRole.objects.create(
            user=self.existing_user,
            organization=self.organization,
            role='RISK_OWNER',
            is_active=True,
        )

    @patch('api.modules.v1.auth.backend.GoogleOIDCProvider.verify_id_token')
    def test_oidc_callback_signs_in_existing_user(self, mock_verify):
        mock_verify.return_value = {
            'email': 'google.user@example.com',
            'first_name': 'Google',
            'last_name': 'User',
            'sub': 'google-123',
        }

        response = self.client.post(
            reverse('auth_oidc_callback'),
            {'id_token': 'valid-google-token'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'google.user@example.com')
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    @patch('api.modules.v1.auth.backend.GoogleOIDCProvider.verify_id_token')
    def test_oidc_callback_creates_user_from_pending_invitation(self, mock_verify):
        invited_user_email = 'invited.google@example.com'
        invitation = OrganizationInvitation.objects.create(
            organization=self.organization,
            invited_by=self.existing_user,
            invited_user_email=invited_user_email,
            role='AUDITOR',
            expires_at=timezone.now() + timedelta(days=7),
        )
        mock_verify.return_value = {
            'email': invited_user_email,
            'first_name': 'Invited',
            'last_name': 'Google',
            'sub': 'google-456',
        }

        response = self.client.post(
            reverse('auth_oidc_callback'),
            {'id_token': 'valid-google-token-for-invited-user'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(email=invited_user_email)
        self.assertTrue(UserOrganizationRole.objects.filter(
            user=user,
            organization=self.organization,
            role='AUDITOR',
            is_active=True,
        ).exists())
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, OrganizationInvitation.Status.ACCEPTED)
        self.assertIn('access', response.data)

    @patch('api.modules.v1.auth.backend.GoogleOIDCProvider.verify_id_token')
    def test_oidc_callback_rejects_forged_token(self, mock_verify):
        mock_verify.side_effect = ValueError('Invalid Google OIDC token')

        response = self.client.post(
            reverse('auth_oidc_callback'),
            {'id_token': 'forged-token'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
