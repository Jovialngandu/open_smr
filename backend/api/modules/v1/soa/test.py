from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import (
    Organization,
    Scope,
    UserOrganizationRole,
    UserScopeAccess,
    IsoControl,
    SoaEntry,
    SoaVersion,
)


User = get_user_model()


class SoaAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Utilisateur
        self.user = User.objects.create_user(
            username="xenos_test",
            password="Test123456"
        )

        # Organisation
        self.organization = Organization.objects.create(
            name="Organisation Test",
            code="ORG-TEST",
            description="Organisation utilisée pour les tests"
        )

        # Scope
        self.scope = Scope.objects.create(
            organization=self.organization,
            name="Scope Test",
            description="Périmètre utilisé pour les tests"
        )

        # Rôle utilisateur dans l'organisation
        self.role = UserOrganizationRole.objects.create(
            user=self.user,
            organization=self.organization,
            role="ADMIN",
            is_active=True,
        )

        # Accès au scope
        UserScopeAccess.objects.create(
            user_organization_role=self.role,
            scope=self.scope,
            granted_by=self.user,
        )

        # Contrôle ISO
        self.control = IsoControl.objects.create(
            code="A.5.1",
            title="Politique de sécurité",
            theme="ORGANIZATIONAL",
            description="Contrôle de test",
        )

        # Entrée SoA
        self.entry = SoaEntry.objects.create(
            scope=self.scope,
            iso_control=self.control,
            is_applicable=True,
            justification="Applicable",
            implementation_status="NOT_IMPLEMENTED",
        )

        # Authentification directe pour les tests
        self.client.force_authenticate(user=self.user)

    def test_list_soa_entries(self):
        response = self.client.get(
            "/api/v1/soa/entries/",
            {"scope_id": str(self.scope.id)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["iso_control"]["code"],
            "A.5.1",
        )

    def test_update_soa_entry(self):
        response = self.client.patch(
            f"/api/v1/soa/entries/{self.entry.id}/",
            {
                "is_applicable": True,
                "justification": "Mise en œuvre commencée",
                "implementation_status": "IN_PROGRESS",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.entry.refresh_from_db()

        self.assertEqual(
            self.entry.implementation_status,
            "IN_PROGRESS",
        )

        self.assertEqual(
            self.entry.justification,
            "Mise en œuvre commencée",
        )

    def test_create_soa_version(self):
        response = self.client.post(
            "/api/v1/soa/versions/",
            {
                "scope_id": str(self.scope.id),
                "version_number": "1.0",
                "title": "Version initiale",
                "status": "DRAFT",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            SoaVersion.objects.count(),
            1,
        )

        version = SoaVersion.objects.first()

        self.assertEqual(
            version.version_number,
            "1.0",
        )

        self.assertEqual(
            len(version.snapshot_data),
            1,
        )

        self.assertEqual(
            version.snapshot_data[0]["control_code"],
            "A.5.1",
        )

    def test_list_soa_versions(self):
        SoaVersion.objects.create(
            scope=self.scope,
            version_number="1.0",
            title="Version test",
            snapshot_data=[],
            status="DRAFT",
        )

        response = self.client.get(
            "/api/v1/soa/versions/",
            {"scope_id": str(self.scope.id)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["version_number"],
            "1.0",
        )
        