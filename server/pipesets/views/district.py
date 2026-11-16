import logging
import unicodedata

import duckdb
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pipesets.district_catalog import list_prefectures, search_districts
from pipesets.serializers.district import (
    DistrictSearchErrorSerializer,
    DistrictSerializer,
    PrefectureSearchErrorSerializer,
    PrefectureSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    operation_id="searchDistricts",
    tags=["districts"],
    parameters=[
        OpenApiParameter("q", str, description="Japanese or romanized place name")
    ],
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
    operation_id="listPrefectures",
    tags=["prefectures"],
    responses={
        200: PrefectureSerializer(many=True),
        503: PrefectureSearchErrorSerializer,
    },
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def prefectures(request):
    try:
        entries = list_prefectures()
    except duckdb.Error:
        logger.exception("Could not query the prefecture catalog")
    else:
        if entries is not None:
            return Response(PrefectureSerializer(entries, many=True).data)

    return Response({"detail": "Prefecture search is unavailable."}, status=503)
