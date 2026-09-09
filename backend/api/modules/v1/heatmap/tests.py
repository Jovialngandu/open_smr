from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.organization import Organization, Scope
from api.models.iso27001 import Asset, Risk

User = get_user_model()


class HeatmapApiTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="Password123!"
        )
        self.organization = Organization.objects.create(name="Org Test")
        self.scope = Scope.objects.create(organization=self.organization, name="Périmètre SI")
        
        self.asset = Asset.objects.create(
            scope=self.scope,
            owner=self.user,
            name="Base de données",
            category="SOFTWARE"
        )

        # Création de 2 risques dans la cellule (likelihood=3, impact=4)
        Risk.objects.create(
            asset=self.asset,
            code="R-01",
            threat_description="Fuite de données",
            likelihood=3,
            impact=4
        )
        Risk.objects.create(
            asset=self.asset,
            code="R-02",
            threat_description="Ransomware",
            likelihood=3,
            impact=4
        )

        # Création d'un risque dans la cellule (likelihood=5, impact=5)
        Risk.objects.create(
            asset=self.asset,
            code="R-03",
            threat_description="Incapacité majeure",
            likelihood=5,
            impact=5
        )

        self.url = reverse('heatmap-matrix')

    def test_heatmap_matrix_success(self):
        """Vérifie le calcul correct de la grille 5x5."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"{self.url}?scope_id={self.scope.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_risks'], 3)
        self.assertEqual(len(response.data['matrix']), 25)  # 5x5 cellules

        # Vérifier la cellule (3, 4) -> count = 2
        cell_3_4 = next(
            c for c in response.data['matrix']
            if c['likelihood'] == 3 and c['impact'] == 4
        )
        self.assertEqual(cell_3_4['count'], 2)
        self.assertEqual(cell_3_4['score'], 12)

    def test_heatmap_requires_scope_id(self):
        """Vérifie le rejet si scope_id est absent."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)