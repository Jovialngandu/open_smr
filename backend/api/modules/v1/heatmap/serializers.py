from rest_framework import serializers


class HeatmapRiskItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    threat_description = serializers.CharField()
    status = serializers.CharField()


class HeatmapCellSerializer(serializers.Serializer):
    likelihood = serializers.IntegerField(min_value=1, max_value=5)
    impact = serializers.IntegerField(min_value=1, max_value=5)
    score = serializers.IntegerField()
    severity = serializers.ChoiceField(choices=['LOW', 'MEDIUM', 'HIGH'])
    count = serializers.IntegerField()
    risks = HeatmapRiskItemSerializer(many=True)


class HeatmapMatrixSerializer(serializers.Serializer):
    scope_id = serializers.UUIDField()
    total_risks = serializers.IntegerField()
    matrix = HeatmapCellSerializer(many=True)