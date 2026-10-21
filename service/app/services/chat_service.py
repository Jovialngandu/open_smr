import time

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.providers.gemini_chat import GeminiChatProvider


class ChatService:
    def __init__(self) -> None:
        self.provider = GeminiChatProvider()

    def respond(self, data: ChatRequest) -> ChatResponse:
        start = time.perf_counter()
        result = self.provider.respond(data)
        elapsed_ms = max(0, int((time.perf_counter() - start) * 1000))

        return ChatResponse(
            reply=result["reply"],
            provider=f"gemini:{settings.gemini_model}",
            duration_ms=result["duration_ms"] + elapsed_ms,
        )


chat_service = ChatService()
