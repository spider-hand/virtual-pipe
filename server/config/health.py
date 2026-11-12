from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok"])


@extend_schema(
    operation_id="getHealth", tags=["health"], responses={200: HealthResponseSerializer}
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    return Response(HealthResponseSerializer({"status": "ok"}).data)
