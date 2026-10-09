
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter

from services.search.selectors import search_soa_controls

logger = logging.getLogger(__name__)


class SoaVectorSearchView(APIView):
    """Recherche sémantique de contrôles ISO 27001."""

    @extend_schema(
        summary="Recherche sémantique de contrôles ISO 27001",
        description=(
            "Recherche les contrôles ISO 27001 pertinents "
            "à partir d'un texte libre ou d'une description de risque."
        ),
        parameters=[
            OpenApiParameter(
                "query",
                str,
                description="Texte de recherche ou description du risque",
                required=True,
            ),
            OpenApiParameter(
                "top_k",
                int,
                description="Nombre de résultats (1 à 20, défaut : 5)",
                required=False,
            ),
        ],
    )
    def get(self, request):
        query_text = request.query_params.get("query", "").strip()

        if not query_text:
            return Response(
                {"error": "Le paramètre 'query' est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            top_k = int(request.query_params.get("top_k", 5))
        except (TypeError, ValueError):
            return Response(
                {"error": "top_k doit être un entier."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not 1 <= top_k <= 20:
            return Response(
                {"error": "top_k doit être compris entre 1 et 20."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            matched_controls = search_soa_controls(
                query_text,
                top_k=top_k,
            )
            
            data = [
				{
					"code": control.code,
					"title": control.title,
					"theme": control.theme,
					"description": control.description,
					"score": round(control.search_score, 4),
					"score_type": control.score_type,
				}
				for control in matched_controls
			]

            return Response(
                {"results": data},
                status=status.HTTP_200_OK,
            )

        except Exception:
            logger.exception("Erreur pendant la recherche sémantique SoA")

            return Response(
                {"error": "Une erreur interne est survenue pendant la recherche."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

