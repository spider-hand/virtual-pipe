from drf_spectacular.utils import extend_schema
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import PipesetSerializer, PipesetValidationErrorSerializer


class PipesetView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    parser_classes = (JSONParser,)

    @extend_schema(
        operation_id="createPipeset",
        tags=["pipesets"],
        request=PipesetSerializer,
        responses={200: PipesetSerializer, 400: PipesetValidationErrorSerializer},
    )
    def post(self, request):
        serializer = PipesetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
