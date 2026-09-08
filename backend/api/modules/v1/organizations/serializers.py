from rest_framework import serializers
from api.models import Organization, UserOrganizationRole
from django.contrib.auth import get_user_model

User = get_user_model()


class OrganizationInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=50)
    description = serializers.CharField(required=False, allow_blank=True)


class OrganizationOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'code', 'description', 'created_at']


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class MemberRoleAssignmentSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserOrganizationRole
        fields = ['id', 'user', 'user_id', 'role', 'is_active', 'joined_at']


class ToggleActiveStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()