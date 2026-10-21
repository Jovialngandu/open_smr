from django.urls import path

from .views import (
    ChatConversationDetailView,
    ChatConversationListCreateView,
    ChatConversationMessageCreateView,
    ChatView,
)

urlpatterns = [
    path("", ChatView.as_view(), name="chat"),
    path("conversations/", ChatConversationListCreateView.as_view(), name="chat-conversations-list-create"),
    path("conversations/<uuid:conversation_id>/", ChatConversationDetailView.as_view(), name="chat-conversation-detail"),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        ChatConversationMessageCreateView.as_view(),
        name="chat-conversation-messages",
    ),
]
