from rest_framework import serializers

from api.models import ChatConversation, ChatMessage


class ChatMessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=("user", "assistant"))
    content = serializers.CharField(trim_whitespace=True, min_length=1, max_length=4000)


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(trim_whitespace=True, min_length=1, max_length=2000)
    history = ChatMessageSerializer(many=True, required=False, allow_empty=True)
    context = serializers.CharField(required=False, allow_blank=True, max_length=20000)

    def validate_history(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("L'historique ne peut pas contenir plus de 10 messages.")

        total_length = sum(len(item.get("content", "")) for item in value)
        if total_length > 12000:
            raise serializers.ValidationError("L'historique est trop volumineux.")

        return value

    def validate(self, attrs):
        if isinstance(attrs.get("history"), list):
            for item in attrs["history"]:
                if item.get("role") == "system":
                    raise serializers.ValidationError({"history": "Le rôle 'system' n'est pas autorisé."})
        return attrs


class ChatResponseSerializer(serializers.Serializer):
    reply = serializers.CharField()


class ChatConversationCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=200)


class ChatConversationSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = [
            "id",
            "title",
            "is_archived",
            "created_at",
            "updated_at",
            "last_activity",
            "message_count",
        ]

    def get_message_count(self, obj):
        return obj.messages.count()


class ChatMessageOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "conversation_id", "role", "content", "created_at"]


class ChatConversationDetailSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = [
            "id",
            "title",
            "is_archived",
            "created_at",
            "updated_at",
            "last_activity",
            "messages",
        ]

    def get_messages(self, obj):
        return ChatMessageOutputSerializer(obj.messages.all(), many=True).data


class ChatMessageCreateSerializer(serializers.Serializer):
    message = serializers.CharField(trim_whitespace=True, min_length=1, max_length=2000)


class ChatSendMessageResponseSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField()
    user_message = ChatMessageOutputSerializer()
    assistant_message = ChatMessageOutputSerializer(required=False, allow_null=True)
    detail = serializers.CharField(required=False, allow_blank=True)
