import logging

from django.db import IntegrityError, transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema
from kombu.exceptions import OperationalError
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pipesets.models.road import RoadDataSetup
from pipesets.road_data import REGIONS, get_coverage, has_cached_extract
from pipesets.serializers.road import (
    RoadDataSerializer,
    RoadDataSetupRequestSerializer,
    RoadDataSetupSerializer,
)
from pipesets.tasks.road import prepare_road_data

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
