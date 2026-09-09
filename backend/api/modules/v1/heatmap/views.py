from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.modules.v1.heatmap.selectors import get_heatmap_matrix_data
from api.modules.v1.heatmap.serializers import HeatmapMatrixSerializer


class HeatmapView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtenir la matrice Heatmap 5x5 des risques",
        parameters=[
            OpenApiParameter(
                name='scope_id',
                type=str,
                required=True,
                description="ID du périmètre (Scope) pour filtrer la matrice des risques"
            ),
        ],
        responses={200: HeatmapMatrixSerializer}
    )
    def get(self, request):
        scope_id = request.query_params.get('scope_id')

        if not scope_id:
            raise ValidationError({'scope_id': "Le paramètre 'scope_id' est obligatoire."})

        data = get_heatmap_matrix_data(scope_id=scope_id)
        serializer = HeatmapMatrixSerializer(data)

        return Response(serializer.data, status=status.HTTP_200_OK)