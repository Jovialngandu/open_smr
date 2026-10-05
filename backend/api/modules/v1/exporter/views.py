from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response

from api.models import Scope
from .selectors import get_soa_export_data
from .utils import generate_soa_excel, generate_soa_pdf
from api.modules.v1.permissions import HasScopeAccessPermission

class SoaExportAPIView(APIView):
    permission_classes = [IsAuthenticated, HasScopeAccessPermission]

    def get(self, request, scope_id):
        scope = get_object_or_404(Scope, id=scope_id)
        self.check_object_permissions(request, scope)

        # Nettoyage et valeur par défaut
        export_format = request.query_params.get('file_type', 'pdf').lower()

        if export_format not in ['pdf', 'xlsx']:
            return Response(
                {"detail": "Format d'export invalide. Choisissez 'pdf' ou 'xlsx'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        soa_data, version_name = get_soa_export_data(scope_id)

        if export_format == 'xlsx':
            file_bytes = generate_soa_excel(soa_data, scope_name=scope.name, version_name=version_name)
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f"SoA_{scope.name}_{version_name}.xlsx"
        else:
            file_bytes = generate_soa_pdf(soa_data, scope_name=scope.name, version_name=version_name)
            content_type = 'application/pdf'
            filename = f"SoA_{scope.name}_{version_name}.pdf"

        response = HttpResponse(file_bytes, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response