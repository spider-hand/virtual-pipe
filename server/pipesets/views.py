import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Pipeset
from .serializers import (
    ErrorResponseSerializer,
    PipesetResponseSerializer,
    PipesetSerializer,
    PipesetValidationErrorSerializer,
)
from .tasks import generate_pipes

logger = logging.getLogger(__name__)


class PipesetView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    parser_classes = (JSONParser,)

    @extend_schema(
        operation_id="createPipeset",
        tags=["pipesets"],
        request=PipesetSerializer,
        responses={
            202: PipesetResponseSerializer,
            400: PipesetValidationErrorSerializer,
            503: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        serializer = PipesetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pipeset = Pipeset.objects.create(**serializer.validated_data)
        try:
            transaction.on_commit(lambda: generate_pipes.delay(pipeset.pk))
        except Exception:
            logger.exception("Failed to enqueue pipeset %s", pipeset.pk)
            Pipeset.objects.filter(pk=pipeset.pk).update(status=Pipeset.Status.FAILED)
            return Response(
                {"detail": "Failed to enqueue pipeset generation."}, status=503
            )
        return Response(PipesetResponseSerializer(pipeset).data, status=202)


class PipesetDetailView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(
        operation_id="getPipeset",
        tags=["pipesets"],
        responses={200: PipesetResponseSerializer, 404: ErrorResponseSerializer},
    )
    def get(self, request, pipeset_id):
        pipeset = get_object_or_404(Pipeset, pk=pipeset_id)
        return Response(PipesetResponseSerializer(pipeset).data)
