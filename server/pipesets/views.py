import logging
import unicodedata
from uuid import UUID

import duckdb
from django.contrib.gis.db.models import Extent
from django.db import transaction
from django.db.models import Case, F, When
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from kombu.exceptions import OperationalError
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pipesets.district_catalog import get_district, search_districts
from pipesets.models import AttributeSet, PipeSet
from pipesets.serializers import (
    AttributeSetCreateSerializer,
    AttributeSetSerializer,
    DistrictSearchErrorSerializer,
    DistrictSerializer,
    PipeSetAcceptedSerializer,
    PipeSetCreateErrorSerializer,
    PipeSetCreateSerializer,
    PipeSetStatusSerializer,
    PipeSetSummarySerializer,
)
from pipesets.tasks import generate_pipeset

logger = logging.getLogger(__name__)


@extend_schema(
    methods=["GET"],
    operation_id="listPipeSets",
    tags=["pipesets"],
    responses={200: PipeSetSummarySerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
    operation_id="createPipeSet",
    tags=["pipesets"],
    request=PipeSetCreateSerializer,
    responses={
        202: PipeSetAcceptedSerializer,
        400: OpenApiResponse(description="Invalid pipe set request."),
        404: PipeSetCreateErrorSerializer,
        503: PipeSetCreateErrorSerializer,
    },
)
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@never_cache
def pipesets(request):
    if request.method == "GET":
        sets = (
            PipeSet.objects.filter(status=PipeSet.Status.SUCCEEDED)
            .annotate(bounds=Extent("pipe__geometry"))
            .order_by(
                F("created_at").desc(nulls_last=True),
                Case(When(created_at__isnull=True, then="name")),
                "id",
            )
        )
        return Response(PipeSetSummarySerializer(sets, many=True).data)

    serializer = PipeSetCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    district_id = serializer.validated_data["district_id"]
    attribute_set_id = serializer.validated_data["attribute_set_id"]

    attribute_set = AttributeSet.objects.filter(pk=attribute_set_id).first()
    if attribute_set is None:
        return Response({"detail": "Attribute set not found."}, status=404)

    try:
        district = get_district(district_id)
    except OSError, duckdb.Error:
        logger.exception("Could not query the district catalog")
        return Response({"detail": "The district catalog is unavailable."}, status=503)

    if district is None:
        return Response({"detail": "District not found."}, status=404)

    with transaction.atomic(durable=True):
        pipeset = PipeSet.objects.create(
            name=serializer.validated_data["name"],
            district_id=district_id,
            attribute_set=attribute_set,
            status=PipeSet.Status.PENDING,
        )

    try:
        generate_pipeset.apply_async(args=[str(pipeset.id)], retry=False)
    except OperationalError:
        logger.exception("Could not queue generation for %s", pipeset.id)
        reason = "The generation queue is unavailable."
        PipeSet.objects.filter(pk=pipeset.id, status=PipeSet.Status.PENDING).update(
            status=PipeSet.Status.FAILED, failure_reason=reason
        )
        return Response({"detail": reason}, status=503)

    return Response(PipeSetAcceptedSerializer(pipeset).data, status=202)


@extend_schema(
    operation_id="getPipeSetStatus",
    tags=["pipesets"],
    parameters=[
        OpenApiParameter(
            "id",
            UUID,
            location=OpenApiParameter.PATH,
            description="The submitted pipe-set ID.",
        )
    ],
    responses={
        200: PipeSetStatusSerializer,
        404: OpenApiResponse(description="Pipe set not found."),
    },
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@never_cache
def get_pipeset_status(request, id):
    pipeset = (
        PipeSet.objects.filter(pk=id).values("id", "status", "failure_reason").first()
    )
    if pipeset is None:
        return Response({"detail": "Pipe set not found."}, status=404)

    if not pipeset["failure_reason"]:
        del pipeset["failure_reason"]

    return Response(PipeSetStatusSerializer(pipeset).data)


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
    methods=["GET"],
    operation_id="listAttributeSets",
    tags=["attribute-sets"],
    responses={200: AttributeSetSerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
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
@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def attribute_sets(request):
    if request.method == "GET":
        sets = AttributeSet.objects.order_by("name", "id")
        return Response(AttributeSetSerializer(sets, many=True).data)

    serializer = AttributeSetCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    attribute_set = serializer.save()
    return Response(
        AttributeSetSerializer(attribute_set).data, status=status.HTTP_201_CREATED
    )
