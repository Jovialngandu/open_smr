from rest_framework import serializers


class HeatmapCellSerializer(serializers.Serializer):
    likelihood = serializers.IntegerField(min_value=1, max_value=5)
    impact = serializers.IntegerField(min_value=1, max_value=5)
    score = serializers.IntegerField()
    count = serializers.IntegerField()


class HeatmapMatrixSerializer(serializers.Serializer):
    scope_id = serializers.UUIDField()
    total_risks = serializers.IntegerField()
    matrix = HeatmapCellSerializer(many=True)