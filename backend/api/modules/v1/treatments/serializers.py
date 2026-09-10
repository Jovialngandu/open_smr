from rest_framework import serializers
from api.models.iso27001 import TreatmentTask, Evidence


class EvidenceSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.ReadOnlyField(source='uploaded_by.email')

    class Meta:
        model = Evidence
        fields = ['id', 'task', 'uploaded_by', 'uploaded_by_email', 'file_path', 'description', 'created_at']
        read_only_fields = ['id', 'uploaded_by', 'created_at']


class EvidenceUploadSerializer(serializers.Serializer):
    task_id = serializers.UUIDField(required=True)
    file_path = serializers.FileField(required=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class TreatmentTaskSerializer(serializers.ModelSerializer):
    assignee_email = serializers.ReadOnlyField(source='assignee.email')
    risk_code = serializers.ReadOnlyField(source='risk.code')
    iso_control_code = serializers.ReadOnlyField(source='iso_control.code')
    evidences = EvidenceSerializer(many=True, read_only=True)

    class Meta:
        model = TreatmentTask
        fields = [
            'id', 'title', 'description', 'status', 'risk', 'risk_code', 
            'iso_control', 'iso_control_code', 'assignee', 'assignee_email', 
            'due_date', 'completed_at', 'evidences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'completed_at', 'created_at', 'updated_at']


class CreateTreatmentTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentTask
        fields = ['title', 'description', 'risk', 'iso_control', 'assignee', 'due_date']


class UpdateTaskStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=TreatmentTask.STATUS_CHOICES)