import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_service_key
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from app.services.providers.gemini_chat import GeminiProviderError

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(require_service_key)],
)


@router.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(payload: ChatRequest) -> ChatResponse:
    try:
        return chat_service.respond(payload)
    except GeminiProviderError as exc:
        logger.warning(
            "Chat provider error kind=%s status_code=%s retryable=%s attempts_available=%s",
            exc.kind,
            exc.status_code,
            exc.retryable,
            exc.attempts_available,
        )
        raise HTTPException(
            status_code=exc.http_status,
            detail=exc.http_detail,
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected chat generation failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Le service de chat IA est actuellement indisponible.",
        ) from exc
