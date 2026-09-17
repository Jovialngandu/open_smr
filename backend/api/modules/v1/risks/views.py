from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, OpenApiParameter

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from api.models import Asset, Scope
from api.modules.v1.permissions import (
    IsAccountActive,
    check_scope_access,
)

from .selectors import (
    get_risk_by_id,
    list_risks_by_scope,
    list_risks_by_asset,
)
from .serializers import (
    RiskCreateSerializer,
    RiskUpdateSerializer,
    RiskOutputSerializer,
)
from .services import (
    create_risk,
    update_risk,
)




class RiskListCreateAPI(APIView):

    permission_classes = [IsAccountActive]
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="scope_id",
                type=str,
                required=False,
                description="Filtrer les risques par scope",
            ),
            OpenApiParameter(
                name="asset_id",
                type=str,
                required=False,
                description="Filtrer les risques par actif",
            ),
        ],
        responses=RiskOutputSerializer(many=True),
    )
    def get(self, request):
        scope_id = request.query_params.get("scope_id")
        asset_id = request.query_params.get("asset_id")

        if asset_id:
            asset = get_object_or_404(
                Asset,
                id=asset_id,
            )

            check_scope_access(
                request.user,
                asset.scope,
            )

            risks = list_risks_by_asset(asset_id)

        elif scope_id:
            scope = get_object_or_404(
                Scope,
                id=scope_id,
            )

            check_scope_access(
                request.user,
                scope,
            )

            risks = list_risks_by_scope(scope_id)

        else:
            return Response(
                {
                    "detail": (
                        "Vous devez fournir "
                        "scope_id ou asset_id."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RiskOutputSerializer(
            risks,
            many=True,
        )

        return Response(serializer.data)

    @extend_schema(
        request=RiskCreateSerializer,
        responses={201: RiskOutputSerializer},
    )
    def post(self, request):
        serializer = RiskCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        asset = get_object_or_404(
            Asset,
            id=data["asset_id"],
        )

        check_scope_access(
            request.user,
            asset.scope,
        )

        risk = create_risk(
            asset=asset,
            code=data["code"],
            threat_description=data[
                "threat_description"
            ],
            likelihood=data["likelihood"],
            impact=data["impact"],
            status=data["status"],
        )

        output = RiskOutputSerializer(risk)

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )


class RiskDetailAPI(APIView):
    permission_classes = [IsAccountActive]
    @extend_schema(
        responses=RiskOutputSerializer,
    )
    def get(self, request, pk):
        risk = get_risk_by_id(pk)

        check_scope_access(
            request.user,
            risk.asset.scope,
        )

        serializer = RiskOutputSerializer(risk)

        return Response(serializer.data)



    @extend_schema(
        request=RiskUpdateSerializer,
        responses=RiskOutputSerializer,
    )
    def patch(self, request, pk):
        risk = get_risk_by_id(pk)

        check_scope_access(
            request.user,
            risk.asset.scope,
        )

        serializer = RiskUpdateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        risk = update_risk(
            risk=risk,
            **serializer.validated_data,
        )

        output = RiskOutputSerializer(risk)

        return Response(output.data)

    