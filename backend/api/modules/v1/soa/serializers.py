from rest_framework import serializers

from api.models import SoaEntry, SoaVersion


class SoaEntryUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer utilisé pour modifier une entrée SoA.
    """

    class Meta:
        model = SoaEntry
        fields = [
            "is_applicable",
            "justification",
            "implementation_status",
        ]



class SoaVersionCreateSerializer(serializers.Serializer):
    scope_id = serializers.UUIDField()
    version_number = serializers.CharField(max_length=50)
    title = serializers.CharField(max_length=255)
    status = serializers.ChoiceField(
        choices=["DRAFT", "APPROVED"],
        default="DRAFT",
    )

class SoaVersionOutputSerializer(serializers.ModelSerializer):
    """
    Serializer utilisé pour afficher une version de la SoA.
    """

    approved_by = serializers.SerializerMethodField()

    class Meta:
        model = SoaVersion
        fields = [
            "id",
            "scope",
            "version_number",
            "title",
            "snapshot_data",
            "status",
            "approved_by",
            "created_at",
            "updated_at",
        ]

    def get_approved_by(self, obj):
        if obj.approved_by is None:
            return None

        return {
            "id": obj.approved_by.id,
            "username": obj.approved_by.username,
            "email": obj.approved_by.email,
        }