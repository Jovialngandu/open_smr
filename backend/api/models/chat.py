import uuid

from django.conf import settings
from django.db import models
from django.utils.text import Truncator

from api.models.base import TimeStampedUUIDModel


class ChatConversation(TimeStampedUUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_conversations",
    )
    title = models.CharField(max_length=200, blank=True, default="Nouvelle conversation")
    is_archived = models.BooleanField(default=False, db_index=True)
    last_activity = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-last_activity", "-created_at"]
        indexes = [
            models.Index(fields=["user", "-last_activity"]),
            models.Index(fields=["user", "is_archived", "-last_activity"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.title}"

    def set_title_from_message(self, message_content: str) -> None:
        cleaned = (message_content or "").strip()
        if not cleaned:
            return

        derived_title = Truncator(cleaned).chars(80)
        if not self.title or self.title == "Nouvelle conversation":
            self.title = derived_title


class ChatMessage(TimeStampedUUIDModel):
    ROLE_CHOICES = [
        ("user", "user"),
        ("assistant", "assistant"),
    ]

    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, db_index=True)
    content = models.TextField()

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["conversation", "role", "created_at"]),
        ]

    def __str__(self):
        return f"{self.conversation_id} - {self.role}"
