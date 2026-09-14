from rest_framework import serializers

from api.models import Asset


class AssetSerializer(serializers.ModelSerializer):
    """
    Serializer utilisé pour afficher les informations d'un actif.
    """

    criticality = serializers.IntegerField(read_only=True)
    owner = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = [
            "id",
            "scope",
            "owner",
            "name",
            "category",
            "description",
            "confidentiality",
            "integrity",
            "availability",
            "criticality",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "scope",
            "owner",
            "criticality",
            "created_at",
            "updated_at",
        ]

    def get_owner(self, obj):
        if obj.owner is None:
            return None

        return {
            "id": obj.owner.id,
            "username": obj.owner.username,
            "email": obj.owner.email,
        }


class AssetCreateSerializer(serializers.Serializer):
    """
    Serializer utilisé lors de la création d'un actif.
    """

    scope_id = serializers.UUIDField()

    owner_id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )

    name = serializers.CharField(
        max_length=255
    )

    category = serializers.ChoiceField(
        choices=Asset.CATEGORY_CHOICES
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    confidentiality = serializers.IntegerField(
        min_value=1,
        max_value=3,
        default=1,
    )

    integrity = serializers.IntegerField(
        min_value=1,
        max_value=3,
        default=1,
    )

    availability = serializers.IntegerField(
        min_value=1,
        max_value=3,
        default=1,
    )


class AssetUpdateSerializer(serializers.Serializer):
    """
    Serializer utilisé lors de la modification d'un actif.
    """

    owner_id = serializers.IntegerField(
        required=False,
        allow_null=True,
    )

    name = serializers.CharField(
        max_length=255,
        required=False,
    )

    category = serializers.ChoiceField(
        choices=Asset.CATEGORY_CHOICES,
        required=False,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    confidentiality = serializers.IntegerField(
        min_value=1,
        max_value=3,
        required=False,
    )

    integrity = serializers.IntegerField(
        min_value=1,
        max_value=3,
        required=False,
    )

    availability = serializers.IntegerField(
        min_value=1,
        max_value=3,
        required=False,
    )
    