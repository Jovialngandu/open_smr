from rest_framework import serializers
from api.models import EmailLog
from api.modules.v1.auth.serializers import UserProfileSerializer

class EmailLogSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    class Meta:
        model = EmailLog
        fields = ['id', 'user', 'email_type', 'recipient', 'subject', 'sent_at', 'status', 'error_message']
        read_only_fields = ['id', 'sent_at']