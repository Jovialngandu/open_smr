from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import (
    Asset,
    Organization,
    Scope,
    UserOrganizationRole,
    UserScopeAccess,
)


User = get_user_model()


class AssetAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="assettester",
            password="Test123456",
            email="assettester@example.com",
        )

        self.other_user = User.objects.create_user(
            username="owner2",
            password="Test123456",
            email="owner2@example.com",
        )

        self.organization = Organization.objects.create(
            name="Asset Test Organization",
            code="ASSET-ORG",
        )

        self.scope = Scope.objects.create(
            organization=self.organization,
            name="Asset Test Scope",
        )

        self.role = UserOrganizationRole.objects.create(
            user=self.user,
            organization=self.organization,
            role="ADMIN",
            is_active=True,
        )

        UserScopeAccess.objects.create(
            user_organization_role=self.role,
            scope=self.scope,
            granted_by=self.user,
        )

        self.asset = Asset.objects.create(
            scope=self.scope,
            owner=self.user,
            name="Serveur principal",
            category="HARDWARE",
            description="Serveur de test",
            confidentiality=3,
            integrity=3,
            availability=3,
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_list_assets_by_scope(self):
        response = self.client.get(
            "/api/v1/assets/",
            {
                "scope_id": str(self.scope.id),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["name"],
            "Serveur principal",
        )

    def test_filter_assets_by_category(self):
        response = self.client.get(
            "/api/v1/assets/",
            {
                "scope_id": str(self.scope.id),
                "category": "HARDWARE",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_create_asset_without_owner_id(self):
        data = {
            "scope_id": str(self.scope.id),
            "name": "Application RH",
            "category": "SOFTWARE",
            "description": "Application de gestion RH",
            "confidentiality": 2,
            "integrity": 3,
            "availability": 2,
        }

        response = self.client.post(
            "/api/v1/assets/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        asset = Asset.objects.get(
            name="Application RH"
        )

        self.assertEqual(
            asset.owner,
            self.user,
        )

        self.assertEqual(
            response.data["owner"]["id"],
            self.user.id,
        )

    def test_create_asset_with_owner_id(self):
        data = {
            "scope_id": str(self.scope.id),
            "owner_id": self.other_user.id,
            "name": "Base de données",
            "category": "DATA",
            "description": "Base de données principale",
            "confidentiality": 3,
            "integrity": 3,
            "availability": 2,
        }

        response = self.client.post(
            "/api/v1/assets/",
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        asset = Asset.objects.get(
            name="Base de données"
        )

        self.assertEqual(
            asset.owner,
            self.other_user,
        )

        self.assertEqual(
            response.data["owner"]["id"],
            self.other_user.id,
        )

    def test_update_asset_owner(self):
        response = self.client.patch(
            f"/api/v1/assets/{self.asset.id}/",
            {
                "owner_id": self.other_user.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.asset.refresh_from_db()

        self.assertEqual(
            self.asset.owner,
            self.other_user,
        )

        self.assertEqual(
            response.data["owner"]["id"],
            self.other_user.id,
        )

    def test_remove_asset_owner(self):
        response = self.client.patch(
            f"/api/v1/assets/{self.asset.id}/",
            {
                "owner_id": None,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.asset.refresh_from_db()

        self.assertIsNone(
            self.asset.owner
        )

        self.assertIsNone(
            response.data["owner"]
        )

    def test_access_denied_without_scope_permission(self):
        outsider = User.objects.create_user(
            username="outsider",
            password="Test123456",
        )

        self.client.force_authenticate(
            user=outsider
        )

        response = self.client.get(
            "/api/v1/assets/",
            {
                "scope_id": str(self.scope.id),
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )