from rest_framework import serializers
from api.models import Scope, UserScopeAccess
from api.modules.v1.auth.serializers import SimpleUserSerializer, UserProfileSerializer


class ScopeInputSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField(required=True)
    name = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")


    def validate(self, attrs):
        organization_id = attrs.get('organization_id')
        name = attrs.get('name')

        if Scope.objects.filter(organization_id=organization_id, name=name).exists():
            raise serializers.ValidationError({
                "name": "Un périmètre avec ce nom existe déjà pour cette organisation."
            })
        return attrs

class ScopeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)


class ScopeOutputSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(source='organization.id', read_only=True)

    class Meta:
        model = Scope
        fields = ['id', 'organization_id', 'name', 'description', 'created_at', 'updated_at']


class UserScopeAccessSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = UserScopeAccess
        # 'user' DOIT figurer dans cette liste
        fields = ['id', 'scope', 'user_organization_role', 'user', 'granted_by', 'granted_at']

    def get_user(self, obj):
        user = obj.user_organization_role.user
        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": getattr(user, 'first_name', ''),
            "last_name": getattr(user, 'last_name', '')
        }


class GrantAccessInputSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)


class RemoveAccessInputSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    

class RisksByLevelSerializer(serializers.Serializer):
    high = serializers.IntegerField()
    medium = serializers.IntegerField()
    low = serializers.IntegerField()

class SoaCompletionSerializer(serializers.Serializer):
    total_applicable = serializers.IntegerField()
    implemented = serializers.IntegerField()
    percentage = serializers.FloatField()

class ScopeDashboardMetricsSerializer(serializers.Serializer):
    risks_by_level = RisksByLevelSerializer()
    soa_completion = SoaCompletionSerializer()
    overdue_tasks_count = serializers.IntegerField()