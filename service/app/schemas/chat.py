from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Le contenu du message ne peut pas être vide.")
        return cleaned


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)
    context: str = Field(default="", max_length=20000)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Le message utilisateur ne peut pas être vide.")
        return cleaned

    @field_validator("history")
    @classmethod
    def validate_history(cls, value: list[ChatMessage]) -> list[ChatMessage]:
        if len(value) > 10:
            raise ValueError("L'historique ne peut pas contenir plus de 10 messages.")

        total_length = sum(len(message.content) for message in value)
        if total_length > 12000:
            raise ValueError("L'historique est trop volumineux.")
        return value

    @field_validator("context")
    @classmethod
    def validate_context(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) > 20000:
            raise ValueError("Le contexte est trop volumineux.")
        return cleaned

    @model_validator(mode="after")
    def validate_history_not_system(self) -> "ChatRequest":
        for message in self.history:
            if message.role == "system":
                raise ValueError("Les rôles système ne sont pas autorisés.")
        return self

    model_config = {"validate_assignment": True}


class ChatResponse(BaseModel):
    reply: str = Field(min_length=1, max_length=12000)
    provider: str
    duration_ms: int = Field(ge=0)
