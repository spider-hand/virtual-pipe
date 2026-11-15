import logging
import unicodedata

import duckdb
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pipesets.district_catalog import search_districts
from pipesets.serializers import (
    AttributeSetCreateSerializer,
    AttributeSetSerializer,
    DistrictSearchErrorSerializer,
    DistrictSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    operation_id="searchDistricts",
    tags=["districts"],
    parameters=[OpenApiParameter("q", str, description="Japanese place name")],
    responses={200: DistrictSerializer(many=True), 503: DistrictSearchErrorSerializer},
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def districts(request):
    query = "".join(
        unicodedata.normalize("NFKC", request.query_params.get("q", "")).split()
    )

    if not query:
        return Response([])

    try:
        matches = search_districts(query)
    except duckdb.Error:
        logger.exception("Could not query the district catalog")
    else:
        if matches is not None:
            return Response(DistrictSerializer(matches, many=True).data)

    return Response({"detail": "District search is unavailable."}, status=503)


@extend_schema(
    operation_id="createAttributeSet",
    tags=["attribute-sets"],
    request=AttributeSetCreateSerializer,
    responses={
        201: AttributeSetSerializer,
        400: OpenApiResponse(
            description="Validation errors keyed by field name, or an invalid JSON body."
        ),
    },
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def create_attribute_set(request):
    serializer = AttributeSetCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    attribute_set = serializer.save()
    return Response(
        AttributeSetSerializer(attribute_set).data, status=status.HTTP_201_CREATED
    )
