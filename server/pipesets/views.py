import logging
import unicodedata
from uuid import UUID

import duckdb
from django.contrib.gis.db.models import Extent
from django.db import IntegrityError, transaction
from django.db.models import Case, F, When
from drf_spectacular.types import OpenApiTypes
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

from pipesets.district_catalog import (
    get_district,
    get_prefecture,
    list_prefectures,
    search_districts,
)
from pipesets.exports import (
    EXPORT_CONTENT_TYPES,
    GEOMETRY_COLUMN,
    PipeSetExportResponse,
)
from pipesets.models import AttributeSet, PipeSet, RoadDataSetup
from pipesets.road_data import REGIONS, get_coverage, has_cached_extract
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
    PrefectureSearchErrorSerializer,
    PrefectureSerializer,
    RoadDataSerializer,
    RoadDataSetupRequestSerializer,
    RoadDataSetupSerializer,
)
from pipesets.tasks import generate_pipeset, prepare_road_data

logger = logging.getLogger(__name__)


@extend_schema(
    operation_id="getRoadData", tags=["road-data"], responses=RoadDataSerializer
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def road_data(request):
    setup = RoadDataSetup.objects.order_by("-pk").first()
    return Response(
        RoadDataSerializer(
            {
                "regions": REGIONS,
                "cached_regions": [
                    region for region in REGIONS if has_cached_extract(region)
                ],
                "setup": setup,
                **get_coverage(),
            }
        ).data
    )


@extend_schema(
    operation_id="createRoadDataSetup",
    tags=["road-data"],
    request=RoadDataSetupRequestSerializer,
    responses={
        202: RoadDataSetupSerializer,
        400: OpenApiResponse(description="Invalid region."),
        409: OpenApiResponse(
            description="A setup is already active or the region is already active."
        ),
        503: OpenApiResponse(description="The setup queue is unavailable."),
    },
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def road_data_setups(request):
    serializer = RoadDataSetupRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    region = serializer.validated_data["region"]
    if region == get_coverage()["active_region"]:
        return Response(
            {"detail": "The selected region is already active."}, status=409
        )

    try:
        with transaction.atomic(durable=True):
            setup = RoadDataSetup.objects.create(region=region)
    except IntegrityError as exc:
        if (
            getattr(getattr(exc.__cause__, "diag", None), "constraint_name", None)
            != "only_one_active_road_data_setup"
        ):
            raise

        return Response({"detail": "A setup is already active."}, status=409)

    try:
        prepare_road_data.apply_async(args=[setup.pk], retry=False)
    except OperationalError:
        logger.exception("Could not queue road data setup %s", setup.pk)
        RoadDataSetup.objects.filter(
            pk=setup.pk, status=RoadDataSetup.Status.QUEUED
        ).update(
            status=RoadDataSetup.Status.FAILED, failure=RoadDataSetup.Failure.QUEUE
        )
        return Response({"detail": "The setup queue is unavailable."}, status=503)

    return Response(RoadDataSetupSerializer(setup).data, status=202)


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
def pipesets(request):
    if request.method == "GET":
        sets = (
            PipeSet.objects.filter(status=PipeSet.Status.SUCCEEDED)
            .select_related("attribute_set")
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
    district_id = serializer.validated_data.get("district_id", "")
    prefecture_id = serializer.validated_data.get("prefecture_id", "")
    attribute_set_id = serializer.validated_data["attribute_set_id"]

    attribute_set = AttributeSet.objects.filter(pk=attribute_set_id).first()
    if attribute_set is None:
        return Response({"detail": "Attribute set not found."}, status=404)

    area_name = "Prefecture" if prefecture_id else "District"
    try:
        area = (
            get_prefecture(prefecture_id)
            if prefecture_id
            else get_district(district_id)
        )
    except OSError, duckdb.Error:
        logger.exception("Could not query the %s catalog", area_name.lower())
        return Response(
            {"detail": f"The {area_name.lower()} catalog is unavailable."}, status=503
        )

    if area is None:
        return Response({"detail": f"{area_name} not found."}, status=404)

    with transaction.atomic(durable=True):
        pipeset = PipeSet.objects.create(
            name=serializer.validated_data["name"],
            district_id=district_id,
            prefecture_id=prefecture_id,
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
    operation_id="downloadPipeSet",
    tags=["pipesets"],
    parameters=[
        OpenApiParameter(
            "file_format",
            str,
            required=True,
            enum=list(EXPORT_CONTENT_TYPES),
            description="File format to download.",
        ),
        OpenApiParameter(
            "id", UUID, location=OpenApiParameter.PATH, description="The pipe-set ID."
        ),
        OpenApiParameter(
            "Content-Disposition",
            str,
            location=OpenApiParameter.HEADER,
            response=[200],
            description="Attachment filename based on the saved pipe-set name.",
        ),
    ],
    responses={
        **{
            (200, content_type): OpenApiTypes.BINARY
            for content_type in EXPORT_CONTENT_TYPES.values()
        },
        400: OpenApiResponse(description="Missing or unsupported file format."),
        404: OpenApiResponse(description="Pipe set not found."),
        409: OpenApiResponse(description="Pipe set cannot be exported."),
    },
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def download_pipeset(request, id):
    file_format = request.query_params.get("file_format")
    if file_format not in EXPORT_CONTENT_TYPES:
        return Response({"detail": "Choose csv or parquet."}, status=400)

    pipeset = PipeSet.objects.select_related("attribute_set").filter(pk=id).first()
    if pipeset is None:
        return Response({"detail": "Pipe set not found."}, status=404)

    if pipeset.status != PipeSet.Status.SUCCEEDED:
        return Response({"detail": "Pipe set is not ready for export."}, status=409)

    definitions = pipeset.attribute_set.attributes if pipeset.attribute_set else []
    if any(definition["name"] == GEOMETRY_COLUMN for definition in definitions):
        return Response({"detail": "The geometry column is reserved."}, status=409)

    return PipeSetExportResponse(pipeset, definitions, file_format)


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
