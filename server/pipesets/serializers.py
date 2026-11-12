from rest_framework import serializers


class DistrictSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    bounds = serializers.ListField(
        child=serializers.FloatField(), min_length=4, max_length=4
    )


class DistrictSearchErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()
