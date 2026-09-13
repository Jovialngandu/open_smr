from rest_framework import serializers

from api.models import Risk


class RiskCreateSerializer(serializers.Serializer):
    asset_id = serializers.UUIDField()
    code = serializers.CharField(max_length=50)
    threat_description = serializers.CharField()

    likelihood = serializers.IntegerField(
        min_value=1,
        max_value=5,
    )

    impact = serializers.IntegerField(
        min_value=1,
        max_value=5,
    )

    status = serializers.ChoiceField(
        choices=[
            "OPEN",
            "IN_MITIGATION",
            "ACCEPTED",
            "CLOSED",
        ],
        default="OPEN",
    )


class RiskStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            "OPEN",
            "IN_MITIGATION",
            "ACCEPTED",
            "CLOSED",
        ]
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

    