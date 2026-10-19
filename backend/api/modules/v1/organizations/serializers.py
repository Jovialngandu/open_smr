from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.models import Organization, OrganizationInvitation, UserOrganizationRole

User = get_user_model()


class OrganizationInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")


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


class OrganizationInvitationCreateSerializer(serializers.Serializer):
    invited_user_email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=OrganizationInvitation.Role.choices,
        required=False,
        default=OrganizationInvitation.Role.RISK_OWNER,
    )


class OrganizationInvitationSerializer(serializers.ModelSerializer):
    organization = OrganizationOutputSerializer(read_only=True)
    invited_by = UserSimpleSerializer(read_only=True)

    class Meta:
        model = OrganizationInvitation
        fields = [
            'id',
            'organization',
            'invited_by',
            'invited_user_email',
            'token',
            'role',
            'status',
            'created_at',
            'expires_at',
        ]


class OrganizationInvitationDecisionSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class OrganizationInvitationAcceptSerializer(OrganizationInvitationDecisionSerializer):
    pass


class OrganizationInvitationDeclineSerializer(OrganizationInvitationDecisionSerializer):
    pass