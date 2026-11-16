from rest_framework import serializers


class AreaSearchResultSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    label_en = serializers.CharField(
        allow_null=True, help_text="Romanized place name when available."
    )
    bounds = serializers.ListField(
        child=serializers.FloatField(), min_length=4, max_length=4
    )


class DistrictSerializer(AreaSearchResultSerializer):
    pass


class PrefectureSerializer(AreaSearchResultSerializer):
    pass


class DistrictSearchErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class PrefectureSearchErrorSerializer(DistrictSearchErrorSerializer):
    pass
