from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import (
    Asset,
    Organization,
    Risk,
    Scope,
    UserOrganizationRole,
    UserScopeAccess,
)


User = get_user_model()


class RiskAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Création de l'utilisateur de test
        self.user = User.objects.create_user(
            username="risktester",
            password="Test123456",
        )

        # Création de l'organisation
        self.organization = Organization.objects.create(
            name="Risk Test Organization",
            code="RISK-ORG",
        )

        # Création du scope
        self.scope = Scope.objects.create(
            organization=self.organization,
            name="Risk Test Scope",
        )

        # Attribution du rôle ADMIN
        self.role = UserOrganizationRole.objects.create(
            user=self.user,
            organization=self.organization,
            role="ADMIN",
            is_active=True,
        )

        # Autorisation d'accès au scope
        UserScopeAccess.objects.create(
            user_organization_role=self.role,
            scope=self.scope,
            granted_by=self.user,
        )

        # Création d'un actif
        self.asset = Asset.objects.create(
            scope=self.scope,
            owner=self.user,
            name="Serveur principal",
            category="HARDWARE",
            description="Serveur utilisé pour les tests",
            confidentiality=3,
            integrity=3,
            availability=3,
        )

        # Création d'un risque initial
        self.risk = Risk.objects.create(
            asset=self.asset,
            code="RISK-001",
            threat_description="Accès non autorisé",
            likelihood=4,
            impact=5,
            status="OPEN",
        )

        # Authentification de l'utilisateur
        self.client.force_authenticate(user=self.user)

    def test_list_risks_by_scope(self):
        response = self.client.get(
            "/api/v1/risks/",
            {
                "scope_id": str(self.scope.id),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["code"],
            "RISK-001",
        )

    def test_list_risks_by_asset(self):
        response = self.client.get(
            "/api/v1/risks/",
            {
                "asset_id": str(self.asset.id),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        self.assertEqual(
            response.data[0]["code"],
            "RISK-001",
        )

    def test_create_risk(self):
        data = {
            "asset_id": str(self.asset.id),
            "code": "RISK-002",
            "threat_description": "Panne du serveur",
            "likelihood": 3,
            "impact": 4,
            "status": "OPEN",
        }

        response = self.client.post(
            "/api/v1/risks/",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            response.data["code"],
            "RISK-002",
        )

        # 3 × 4 = 12
        self.assertEqual(
            response.data["score"],
            12,
        )

        self.assertTrue(
            Risk.objects.filter(
                code="RISK-002"
            ).exists()
        )

    def test_update_risk_status(self):
        response = self.client.patch(
            f"/api/v1/risks/{self.risk.id}/",
            {
                "status": "IN_MITIGATION",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.risk.refresh_from_db()

        self.assertEqual(
            self.risk.status,
            "IN_MITIGATION",
        )

    def test_invalid_likelihood(self):
        data = {
            "asset_id": str(self.asset.id),
            "code": "RISK-003",
            "threat_description": "Test invalid likelihood",
            "likelihood": 8,
            "impact": 4,
            "status": "OPEN",
        }

        response = self.client.post(
            "/api/v1/risks/",
            data,
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        