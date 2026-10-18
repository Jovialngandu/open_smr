from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
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
		current_year = timezone.now().year

		self.user = User.objects.create_user(
			username="risktester",
			password="Test123456",
		)

		self.organization = Organization.objects.create(
			name="Risk Test Organization",
			code="RISK-ORG",
		)

		self.scope = Scope.objects.create(
			organization=self.organization,
			name="Risk Test Scope",
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
			description="Serveur utilisé pour les tests",
			confidentiality=3,
			integrity=3,
			availability=3,
		)

		self.initial_code = f"RSK-{current_year}-001"
		self.risk = Risk.objects.create(
			asset=self.asset,
			code=self.initial_code,
			threat_description="Accès non autorisé",
			likelihood=4,
			impact=5,
			status="OPEN",
		)

		self.client.force_authenticate(user=self.user)

	def test_list_risks_by_scope(self):
		response = self.client.get(
			"/api/v1/risks/",
			{"scope_id": str(self.scope.id)},
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]["code"], self.initial_code)

	def test_list_risks_by_asset(self):
		response = self.client.get(
			"/api/v1/risks/",
			{"asset_id": str(self.asset.id)},
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]["code"], self.initial_code)

	def test_create_risk(self):
		current_year = timezone.now().year
		expected_code = f"RSK-{current_year}-002"
		data = {
			"asset_id": str(self.asset.id),
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
		self.assertEqual(response.data["code"], expected_code)
		self.assertEqual(response.data["score"], 12)
		self.assertTrue(Risk.objects.filter(code=expected_code).exists())

	def test_update_risk_status(self):
		response = self.client.patch(
			f"/api/v1/risks/{self.risk.id}/",
			{"status": "IN_MITIGATION"},
			format="json",
		)
		self.assertEqual(response.status_code, 200)
		self.risk.refresh_from_db()
		self.assertEqual(self.risk.status, "IN_MITIGATION")

	def test_invalid_likelihood(self):
		data = {
			"asset_id": str(self.asset.id),
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

	def test_update_risk_fields_and_score(self):
		response = self.client.patch(
			f"/api/v1/risks/{self.risk.id}/",
			{
				"threat_description": "Menace mise à jour",
				"likelihood": 2,
				"impact": 3,
				"status": "IN_MITIGATION",
			},
			format="json",
		)
		self.assertEqual(response.status_code, 200)
		self.risk.refresh_from_db()
		self.assertEqual(self.risk.threat_description, "Menace mise à jour")
		self.assertEqual(self.risk.likelihood, 2)
		self.assertEqual(self.risk.impact, 3)
		self.assertEqual(self.risk.status, "IN_MITIGATION")
		self.assertEqual(response.data["score"], 6)

	def test_partial_update_risk(self):
		response = self.client.patch(
			f"/api/v1/risks/{self.risk.id}/",
			{"likelihood": 2},
			format="json",
		)
		self.assertEqual(response.status_code, 200)
		self.risk.refresh_from_db()
		self.assertEqual(self.risk.likelihood, 2)
		self.assertEqual(self.risk.impact, 5)
		self.assertEqual(response.data["score"], 10)

	def test_delete_risk_by_authorized_user(self):
		response = self.client.delete(f"/api/v1/risks/{self.risk.id}/")
		self.assertEqual(response.status_code, 204)
		self.assertFalse(Risk.objects.filter(id=self.risk.id).exists())

	def test_risk_owner_can_delete_risk(self):
		risk_owner = User.objects.create_user(username="risk_owner", password="Test123456")
		UserOrganizationRole.objects.create(
			user=risk_owner,
			organization=self.organization,
			role="RISK_OWNER",
			is_active=True,
		)
		UserScopeAccess.objects.create(
			user_organization_role=UserOrganizationRole.objects.get(user=risk_owner, organization=self.organization),
			scope=self.scope,
			granted_by=self.user,
		)
		self.client.force_authenticate(user=risk_owner)
		response = self.client.delete(f"/api/v1/risks/{self.risk.id}/")
		self.assertEqual(response.status_code, 204)
		self.assertFalse(Risk.objects.filter(id=self.risk.id).exists())

	def test_user_without_scope_access_cannot_delete_risk(self):
		outside_user = User.objects.create_user(username="outside_user", password="Test123456")
		self.client.force_authenticate(user=outside_user)
		response = self.client.delete(f"/api/v1/risks/{self.risk.id}/")
		self.assertEqual(response.status_code, 403)
		self.assertTrue(Risk.objects.filter(id=self.risk.id).exists())

	def test_user_with_scope_access_but_no_delete_role_cannot_delete_risk(self):
		member = User.objects.create_user(username="member_user", password="Test123456")
		member_role = UserOrganizationRole.objects.create(
			user=member,
			organization=self.organization,
			role="AUDITOR",
			is_active=True,
		)
		UserScopeAccess.objects.create(
			user_organization_role=member_role,
			scope=self.scope,
			granted_by=self.user,
		)
		self.client.force_authenticate(user=member)
		response = self.client.delete(f"/api/v1/risks/{self.risk.id}/")
		self.assertEqual(response.status_code, 403)
		self.assertTrue(Risk.objects.filter(id=self.risk.id).exists())

	def test_unauthenticated_user_cannot_access_risks(self):
		self.client.force_authenticate(user=None)
		response = self.client.get(
			"/api/v1/risks/",
			{"scope_id": str(self.scope.id)},
		)
		self.assertIn(response.status_code, [401, 403])

	def test_if_i_can_get_iso_control_suggestions(self):
		response = self.client.get(
			f"/api/v1/risks/{self.risk.id}/iso-control-suggestions/"
		)

		print(response.data)
		self.assertEqual(response.status_code, 200)
		self.assertIsInstance(response.data, list)

	@patch("api.modules.v1.risks.views.assess_risk")
	def test_ai_assessment_endpoint(self, mock_assess_risk):
		mock_assess_risk.return_value = {
			"likelihood": 4,
			"impact": 3,
			"justification": "Le risque est modéré.",
			"provider": "mock-llm",
		}

		response = self.client.post(
			"/api/v1/risks/assess-risk/",
			{
				"asset_id": str(self.asset.id),
				"threat_description": "Tentative de phishing ciblée",
			},
			format="json",
		)
  

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["likelihood"], 4)
		self.assertEqual(response.data["impact"], 3)
		self.assertEqual(response.data["provider"], "mock-llm")
		mock_assess_risk.assert_called_once()
