from rest_framework import serializers

from api.models import IsoControl, Risk


class RiskCreateSerializer(serializers.Serializer):
    asset_id = serializers.UUIDField()
    threat_description = serializers.CharField()

    likelihood = serializers.IntegerField(min_value=1, max_value=5)
    impact = serializers.IntegerField(min_value=1, max_value=5)

    status = serializers.ChoiceField(
        choices=[
            "OPEN",
            "IN_MITIGATION",
            "ACCEPTED",
            "CLOSED",
        ],
        default="OPEN",
    )


class RiskUpdateSerializer(serializers.Serializer):
    threat_description = serializers.CharField(required=False)

    likelihood = serializers.IntegerField(min_value=1, max_value=5, required=False)
    impact = serializers.IntegerField(min_value=1, max_value=5, required=False)

    status = serializers.ChoiceField(
        choices=[
            "OPEN",
            "IN_MITIGATION",
            "ACCEPTED",
            "CLOSED",
        ],
        required=False,
    )


class RiskOutputSerializer(serializers.ModelSerializer):
    score = serializers.IntegerField(read_only=True)
    asset = serializers.SerializerMethodField()

    class Meta:
        model = Risk
        fields = [
            "id",
            "asset",
            "code",
            "threat_description",
            "likelihood",
            "impact",
            "score",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_asset(self, obj):
        return {
            "id": str(obj.asset.id),
            "name": obj.asset.name,
            "category": obj.asset.category,
            "scope_id": str(obj.asset.scope_id),
        }


class IsoControlSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    code = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    theme = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)


class RiskAIAssessmentRequestSerializer(serializers.Serializer):
    asset_id = serializers.UUIDField()
    threat_description = serializers.CharField(min_length=5, max_length=5000)


class RiskAIAssessmentOutputSerializer(serializers.Serializer):
    likelihood = serializers.IntegerField(min_value=1, max_value=5)
    impact = serializers.IntegerField(min_value=1, max_value=5)
    justification = serializers.CharField()
    provider = serializers.CharField()
