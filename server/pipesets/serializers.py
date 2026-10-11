import math

from rest_framework import serializers

from .models import Pipeset


class AttributeDefinitionSerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.ChoiceField(choices=("string", "number", "boolean", "category"))
    min = serializers.IntegerField(
        required=False, min_value=-(2**53 - 1), max_value=2**53 - 1
    )
    max = serializers.IntegerField(
        required=False, min_value=-(2**53 - 1), max_value=2**53 - 1
    )
    categories = serializers.ListField(
        child=serializers.CharField(allow_blank=True), required=False
    )

    def validate(self, value):
        if value["name"] in {"id", "pipeset_id", "geometry"}:
            raise serializers.ValidationError({"name": "This name is reserved."})
        kind = value["type"]
        if kind in {"string", "number"}:
            if "min" not in value or "max" not in value:
                raise serializers.ValidationError("Minimum and maximum are required.")
            if value["min"] > value["max"]:
                raise serializers.ValidationError("Minimum must not exceed maximum.")
            if kind == "string" and value["min"] < 0:
                raise serializers.ValidationError(
                    "String lengths must be non-negative."
                )
            value.pop("categories", None)
        else:
            value.pop("min", None)
            value.pop("max", None)
            if kind == "category":
                categories = list(
                    dict.fromkeys(item for item in value.get("categories", []) if item)
                )
                if not categories:
                    raise serializers.ValidationError(
                        {"categories": "At least one category is required."}
                    )
                value["categories"] = categories
            else:
                value.pop("categories", None)
        return value


class PipesetSerializer(serializers.Serializer):
    attribute_definitions = AttributeDefinitionSerializer(
        many=True, required=False, default=list
    )

    def validate_attribute_definitions(self, value):
        names = [field["name"] for field in value]
        if len(names) != len(set(names)):
            raise serializers.ValidationError("Field names must be unique.")
        return value

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
    attribute_definitions = AttributeDefinitionSerializer(many=True, read_only=True)
    count = serializers.IntegerField(read_only=True, min_value=0)
    bbox = serializers.ListField(child=serializers.FloatField(), read_only=True)

    class Meta:
        model = Pipeset
        fields = ("id", "name", "count", "bbox", "status", "attribute_definitions")
        read_only_fields = fields


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class PipesetValidationErrorSerializer(serializers.Serializer):
    name = serializers.ListField(child=serializers.CharField(), required=False)
    bbox = serializers.JSONField(required=False)
    attribute_definitions = serializers.JSONField(required=False)
    non_field_errors = serializers.ListField(
        child=serializers.CharField(), required=False
    )
