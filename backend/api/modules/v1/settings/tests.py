from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from api.models.support import UserPreference, SystemSetting

User = get_user_model()


class UserPreferenceApiTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user_test",
            email="user@example.com",
            password="Password123!"
        )
        self.url_me = reverse('user-preferences-me')

    def test_get_user_preferences_creates_default_if_not_exists(self):
        """Vérifie que le GET /settings/me/ crée des préférences par défaut si l'utilisateur n'en a pas encore."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url_me)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['language'], 'fr')
        self.assertEqual(response.data['theme'], 'LIGHT')
        self.assertTrue(UserPreference.objects.filter(user=self.user).exists())

    def test_update_user_preferences_patch(self):
        """Vérifie la mise à jour partielle via PATCH sur /settings/me/."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'theme': 'DARK',
            'email_notifications': False
        }
        response = self.client.patch(self.url_me, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['theme'], 'DARK')
        self.assertFalse(response.data['email_notifications'])
        
        pref = UserPreference.objects.get(user=self.user)
        self.assertEqual(pref.theme, 'DARK')
        self.assertFalse(pref.email_notifications)

    def test_unauthenticated_user_cannot_access_preferences(self):
        """Vérifie qu'un utilisateur non authentifié est rejeté (401)."""
        response = self.client.get(self.url_me)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SystemSettingApiTests(APITestCase):

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin_test",
            email="admin@example.com",
            password="AdminPassword123!"
        )
        self.normal_user = User.objects.create_user(
            username="normal_user",
            email="normal@example.com",
            password="Password123!"
        )
        self.setting = SystemSetting.objects.create(
            key="MAINTENANCE_MODE",
            value={"enabled": False},
            description="Mode maintenance global"
        )
        self.url_list = reverse('system-settings-list')

    def test_admin_can_list_system_settings(self):
        """Vérifie qu'un administrateur peut lister les paramètres système."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url_list)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['key'], "MAINTENANCE_MODE")

    def test_normal_user_cannot_access_system_settings(self):
        """Vérifie qu'un utilisateur non-admin ne peut pas accéder aux paramètres système (403)."""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_or_create_system_setting(self):
        """Vérifie qu'un admin peut mettre à jour un paramètre système par sa clé."""
        self.client.force_authenticate(user=self.admin_user)
        url_detail = reverse('system-settings-detail', kwargs={'key': 'MAINTENANCE_MODE'})
        
        payload = {
            'value': {'enabled': True, 'reason': 'Mise à jour BDD'},
            'description': 'Maintenance planifiée'
        }
        response = self.client.patch(url_detail, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['value']['enabled'])
        
        self.setting.refresh_from_db()
        self.assertTrue(self.setting.value['enabled'])
        self.assertEqual(self.setting.description, 'Maintenance planifiée')