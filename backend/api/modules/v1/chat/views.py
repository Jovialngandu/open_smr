import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import ChatConversation, ChatMessage
from api.modules.v1.chat.serializers import (
    ChatConversationCreateSerializer,
    ChatConversationDetailSerializer,
    ChatConversationSerializer,
    ChatMessageCreateSerializer,
    ChatMessageOutputSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatSendMessageResponseSerializer,
)
from api.modules.v1.permissions import IsAccountActive
from services.scoring.client import AIServiceError, chat

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Chat"],
    request=ChatRequestSerializer,
    responses={200: ChatResponseSerializer, 400: None, 401: None, 429: None, 503: None, 504: None},
)
class ChatView(APIView):
    permission_classes = [IsAuthenticated, IsAccountActive]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = serializer.validated_data

        try:
            result = chat(
                message=payload["message"],
                history=payload.get("history", []),
                context=payload.get("context", ""),
            )
        except AIServiceError as exc:
            logger.warning(
                "Chat AI service error status=%s detail=%s",
                getattr(exc, "status_code", 503),
                exc.message,
            )
            return Response(
                {"detail": exc.message},
                status=exc.status_code or status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception:
            logger.exception("Unexpected chat gateway failure")
            return Response(
                {"detail": "Le service de chat IA est actuellement indisponible."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response = ChatResponseSerializer(result)
        return Response(response.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Chat"], request=ChatConversationCreateSerializer, responses={200: ChatConversationSerializer, 201: ChatConversationSerializer})
class ChatConversationListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAccountActive]

    def get(self, request):
        conversations = ChatConversation.objects.filter(user=request.user).order_by("-last_activity", "-created_at")
        serializer = ChatConversationSerializer(conversations, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ChatConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title = (serializer.validated_data.get("title") or "").strip() or "Nouvelle conversation"
        conversation = ChatConversation.objects.create(user=request.user, title=title)
        return Response(ChatConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Chat"], responses={200: ChatConversationDetailSerializer, 404: None})
class ChatConversationDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAccountActive]

    def get(self, request, conversation_id):
        conversation = get_object_or_404(ChatConversation.objects.filter(user=request.user), id=conversation_id)
        return Response(ChatConversationDetailSerializer(conversation).data, status=status.HTTP_200_OK)


@extend_schema(tags=["Chat"], request=ChatMessageCreateSerializer, responses={201: ChatSendMessageResponseSerializer, 400: None, 401: None, 404: None, 503: None, 504: None})
class ChatConversationMessageCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAccountActive]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(ChatConversation.objects.filter(user=request.user), id=conversation_id)
        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_message = serializer.validated_data["message"]
        if conversation.title == "Nouvelle conversation":
            conversation.set_title_from_message(raw_message)
            conversation.save(update_fields=["title", "last_activity", "updated_at"])

        user_message = ChatMessage.objects.create(
            conversation=conversation,
            role="user",
            content=raw_message,
        )

        history = list(
            ChatMessage.objects.filter(conversation=conversation)
            .exclude(id=user_message.id)
            .order_by("-created_at")[:10]
        )
        history.reverse()

        ai_history = [{"role": item.role, "content": item.content} for item in history]
        try:
            result = chat(
                message=raw_message,
                history=ai_history,
                context=f"Conversation: {conversation.title}",
            )
        except AIServiceError as exc:
            logger.warning(
                "Chat AI service error for conversation=%s status=%s detail=%s",
                conversation.id,
                getattr(exc, "status_code", 503),
                exc.message,
            )
            payload = {
                "conversation_id": conversation.id,
                "user_message": ChatMessageOutputSerializer(user_message).data,
                "detail": exc.message,
            }
            return Response(payload, status=exc.status_code or status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception("Unexpected failure while generating persisted chat reply")
            payload = {
                "conversation_id": conversation.id,
                "user_message": ChatMessageOutputSerializer(user_message).data,
                "detail": "Le service de chat IA est actuellement indisponible.",
            }
            return Response(payload, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        assistant_content = result.get("reply", "").strip()
        assistant_message = ChatMessage.objects.create(
            conversation=conversation,
            role="assistant",
            content=assistant_content,
        )

        payload = {
            "conversation_id": conversation.id,
            "user_message": ChatMessageOutputSerializer(user_message).data,
            "assistant_message": ChatMessageOutputSerializer(assistant_message).data,
        }
        return Response(payload, status=status.HTTP_201_CREATED)
