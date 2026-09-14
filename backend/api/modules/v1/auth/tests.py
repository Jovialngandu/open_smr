from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Organization, UserOrganizationRole, UserScopeAccess


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
