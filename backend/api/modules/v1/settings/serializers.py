from rest_framework import serializers
from api.models.support  import UserPreference, SystemSetting


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['id', 'language', 'theme', 'timezone', 'email_notifications', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ['id', 'key', 'value', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'key', 'created_at', 'updated_at']


class UpdateSystemSettingInputSerializer(serializers.Serializer):
    value = serializers.JSONField(required=True)
    description = serializers.CharField(required=False, allow_null=True)