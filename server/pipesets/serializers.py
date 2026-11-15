from datetime import date
from decimal import Decimal

from django.core.validators import RegexValidator
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework import serializers

from pipesets.models import AttributeSet, PipeSet


class DistrictSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    bounds = serializers.ListField(
        child=serializers.FloatField(), min_length=4, max_length=4
    )


class DistrictSearchErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class TextField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)


class UUIDTextField(serializers.UUIDField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")

        return super().to_internal_value(data)


class PipeSetCreateSerializer(serializers.Serializer):
    district_id = TextField(
        trim_whitespace=False,
        min_length=5,
        max_length=5,
        validators=[RegexValidator(r"\A[0-9]{5}\Z")],
    )
    attribute_set_id = UUIDTextField()


class PipeSetAcceptedSerializer(serializers.Serializer):
    id = serializers.UUIDField()


class PipeSetStatusSerializer(PipeSetAcceptedSerializer):
    status = serializers.ChoiceField(choices=PipeSet.Status.choices)
    failure_reason = serializers.CharField(required=False)


class PipeSetCreateErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class AttributeSerializer(serializers.Serializer):
    name = TextField(validators=[RegexValidator(r"\A[a-z][a-z0-9_]*\Z")])


class StringAttributeSerializer(AttributeSerializer):
    type = serializers.ChoiceField(choices=["string"])
    choices = serializers.ListField(child=TextField(), min_length=1)


class BooleanAttributeSerializer(AttributeSerializer):
    type = serializers.ChoiceField(choices=["boolean"])


class GeneratedIdAttributeSerializer(AttributeSerializer):
    type = serializers.ChoiceField(choices=["id"])
    id_format = serializers.ChoiceField(choices=["sequential", "uuid"])


class RangeAttributeSerializer(AttributeSerializer):
    def validate(self, attrs):
        lower = self.parse_bound(attrs["min"])
        upper = self.parse_bound(attrs["max"])
        if lower > upper:
            raise serializers.ValidationError(
                "The maximum must be at least the minimum."
            )
        return attrs


class IntegerAttributeSerializer(RangeAttributeSerializer):
    type = serializers.ChoiceField(choices=["integer"])
    min = TextField(validators=[RegexValidator(r"\A-?[0-9]+\Z")])
    max = TextField(validators=[RegexValidator(r"\A-?[0-9]+\Z")])
    parse_bound = Decimal


class DecimalAttributeSerializer(RangeAttributeSerializer):
    type = serializers.ChoiceField(choices=["decimal"])
    min = TextField(validators=[RegexValidator(r"\A-?[0-9]+\.[0-9]+\Z")])
    max = TextField(validators=[RegexValidator(r"\A-?[0-9]+\.[0-9]+\Z")])
    parse_bound = Decimal

    def validate(self, attrs):
        if len(attrs["min"].split(".")[1]) != len(attrs["max"].split(".")[1]):
            raise serializers.ValidationError(
                "Both bounds must have the same precision."
            )
        return super().validate(attrs)


class DateAttributeSerializer(RangeAttributeSerializer):
    type = serializers.ChoiceField(choices=["date"])
    min = TextField(validators=[RegexValidator(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")])
    max = TextField(validators=[RegexValidator(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")])

    @staticmethod
    def parse_bound(value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise serializers.ValidationError("Enter a valid calendar date.")


ATTRIBUTE_TYPES = {
    "string": StringAttributeSerializer,
    "integer": IntegerAttributeSerializer,
    "decimal": DecimalAttributeSerializer,
    "boolean": BooleanAttributeSerializer,
    "date": DateAttributeSerializer,
    "id": GeneratedIdAttributeSerializer,
}


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="AttributeDefinition",
        serializers=ATTRIBUTE_TYPES,
        resource_type_field_name="type",
        many=False,
    )
)
class AttributeDefinitionField(serializers.Field):
    def to_internal_value(self, data):
        attribute_type = data.get("type") if isinstance(data, dict) else None
        if not isinstance(attribute_type, str) or attribute_type not in ATTRIBUTE_TYPES:
            raise serializers.ValidationError(
                {"type": "Choose a supported attribute type."}
            )

        serializer = ATTRIBUTE_TYPES[attribute_type](data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def to_representation(self, instance):
        return instance


class AttributeSetSerializer(serializers.ModelSerializer):
    name = TextField(max_length=255)
    attributes = serializers.ListField(child=AttributeDefinitionField(), min_length=1)

    class Meta:
        model = AttributeSet
        fields = ("id", "name", "attributes")
        read_only_fields = ("id",)

    def validate_attributes(self, attributes):
        names = {attribute["name"] for attribute in attributes}
        if len(names) != len(attributes):
            raise serializers.ValidationError("Attribute names must be unique.")
        return attributes

    def create(self, validated_data):
        return AttributeSet.objects.create(**validated_data)


class AttributeSetCreateSerializer(AttributeSetSerializer):
    class Meta(AttributeSetSerializer.Meta):
        fields = ("name", "attributes")
        read_only_fields = ()
