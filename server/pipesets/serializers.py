import math

from rest_framework import serializers

from .models import Pipeset


class PipesetSerializer(serializers.Serializer):
    name = serializers.CharField()
    bbox = serializers.ListField(
        child=serializers.FloatField(),
        min_length=4,
        max_length=4,
        help_text="[west, south, east, north]; longitude -180..180, latitude -90..90; west < east and south < north.",
    )

    def validate_bbox(self, value):
        if not all(math.isfinite(coordinate) for coordinate in value):
            raise serializers.ValidationError("Coordinates must be finite numbers.")

        west, south, east, north = value
        if not (-180 <= west <= 180 and -180 <= east <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        if not (-90 <= south <= 90 and -90 <= north <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        if west >= east or south >= north:
            raise serializers.ValidationError(
                "West must be less than east and south less than north."
            )
        return value


class PipesetResponseSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(read_only=True, min_value=0)
    bbox = serializers.ListField(child=serializers.FloatField(), read_only=True)

    class Meta:
        model = Pipeset
        fields = ("id", "name", "count", "bbox", "status")
        read_only_fields = fields


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class PipesetValidationErrorSerializer(serializers.Serializer):
    name = serializers.ListField(child=serializers.CharField(), required=False)
    bbox = serializers.JSONField(required=False)
    non_field_errors = serializers.ListField(
        child=serializers.CharField(), required=False
    )
