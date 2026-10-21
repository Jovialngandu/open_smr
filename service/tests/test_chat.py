import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import ChatRequest
from app.services.providers.gemini_chat import GeminiChatProvider, GeminiProviderError


class ChatEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"X-Service-Key": "test-service-key"}

    @patch("app.core.security.settings.service_api_key", "test-service-key")
    def test_chat_requires_service_key(self):
        response = self.client.post(
            "/chat",
            json={"message": "Bonjour"},
        )

        self.assertEqual(response.status_code, 401)

    @patch("app.core.security.settings.service_api_key", "test-service-key")
    @patch("app.services.chat_service.GeminiChatProvider.respond")
    def test_chat_valid_request_returns_schema(self, mock_respond):
        mock_respond.return_value = {
            "reply": "Bonjour, je peux vous aider.",
            "duration_ms": 123,
        }

        response = self.client.post(
            "/chat",
            json={
                "message": "Bonjour",
                "history": [
                    {"role": "user", "content": "Bonjour"},
                    {"role": "assistant", "content": "Bonjour !"},
                ],
                "context": "Actif : Serveur principal",
            },
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["reply"], "Bonjour, je peux vous aider.")
        self.assertIn("gemini:", payload["provider"])
        self.assertGreaterEqual(payload["duration_ms"], 0)

    @patch("app.core.security.settings.service_api_key", "test-service-key")
    @patch("app.services.chat_service.GeminiChatProvider.respond")
    def test_chat_maps_temporary_provider_error_to_503(self, mock_respond):
        mock_respond.side_effect = GeminiProviderError(
            "temporary unavailable",
            kind="temporary_unavailable",
            status_code=503,
            retryable=True,
        )

        response = self.client.post(
            "/chat",
            json={"message": "Que faire ?"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            "Le service de chat IA est momentanément indisponible.",
        )
        self.assertNotIn("temporary unavailable", response.text.lower())

    @patch("app.core.security.settings.service_api_key", "test-service-key")
    @patch("app.services.chat_service.GeminiChatProvider.respond")
    def test_chat_maps_rate_limit_error_to_429(self, mock_respond):
        mock_respond.side_effect = GeminiProviderError(
            "rate limit",
            kind="rate_limit",
            status_code=429,
            retryable=True,
        )

        response = self.client.post(
            "/chat",
            json={"message": "Que faire ?"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(
            response.json()["detail"],
            "Trop de demandes pour le service de chat IA. Réessayez plus tard.",
        )
        self.assertNotIn("rate limit", response.text.lower())

    @patch("app.core.security.settings.service_api_key", "test-service-key")
    @patch("app.services.chat_service.GeminiChatProvider.respond")
    def test_chat_maps_auth_or_config_error_to_500(self, mock_respond):
        mock_respond.side_effect = GeminiProviderError(
            "auth error",
            kind="auth_or_config",
            status_code=401,
            retryable=False,
        )

        response = self.client.post(
            "/chat",
            json={"message": "Que faire ?"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["detail"],
            "Le service de chat IA n'est pas configuré correctement.",
        )
        self.assertNotIn("auth error", response.text.lower())

    @patch("app.core.security.settings.service_api_key", "test-service-key")
    def test_chat_rejects_empty_message(self):
        response = self.client.post(
            "/chat",
            json={"message": "   "},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 422)

    @patch("app.core.security.settings.service_api_key", "test-service-key")
    def test_chat_rejects_invalid_history_role(self):
        response = self.client.post(
            "/chat",
            json={
                "message": "Test",
                "history": [{"role": "system", "content": "x"}],
            },
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 422)

    @patch("app.core.security.settings.service_api_key", "test-service-key")
    def test_chat_rejects_overlong_history(self):
        response = self.client.post(
            "/chat",
            json={
                "message": "Test",
                "history": [
                    {"role": "user", "content": "A" * 4001},
                ],
            },
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 422)


class ChatSchemaTests(unittest.TestCase):
    def test_chat_request_validates_total_history_length(self):
        long_history = [{"role": "user", "content": "A" * 5000}]

        with self.assertRaises(ValueError):
            ChatRequest(message="Bonjour", history=long_history)


class SentinelKnowledgeTests(unittest.TestCase):
    def test_reference_context_is_grounded_in_verified_project_facts(self):
        from app.services.project_knowledge import OPENSMR_REFERENCE_CONTEXT

        self.assertIn("OpenSMR", OPENSMR_REFERENCE_CONTEXT)
        self.assertIn("ISO/IEC 27001:2022", OPENSMR_REFERENCE_CONTEXT)
        self.assertIn("Django REST Framework", OPENSMR_REFERENCE_CONTEXT)
        self.assertIn("FastAPI", OPENSMR_REFERENCE_CONTEXT)
        self.assertIn("Faits confirmés", OPENSMR_REFERENCE_CONTEXT)
        self.assertIn("Inconnus", OPENSMR_REFERENCE_CONTEXT)

    @patch("app.services.providers.gemini_chat.genai.Client")
    def test_provider_prompt_includes_project_reference_context(self, mock_client):
        mock_generate = Mock(return_value=SimpleNamespace(text="Réponse test"))
        mock_client.return_value.models = SimpleNamespace(generate_content=mock_generate)

        provider = GeminiChatProvider()
        provider.respond(ChatRequest(message="Qu'est-ce qu'OpenSMR ?", history=[]))

        prompt = mock_generate.call_args.kwargs["contents"]

        self.assertIn("OpenSMR", prompt)
        self.assertIn("ISO/IEC 27001:2022", prompt)
        self.assertIn("Django REST Framework", prompt)
        self.assertIn("FastAPI", prompt)
        self.assertNotIn("connaître l'équipe", prompt.lower())


if __name__ == "__main__":
    unittest.main()
