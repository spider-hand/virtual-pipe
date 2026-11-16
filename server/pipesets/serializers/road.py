from rest_framework import serializers

from pipesets.models.road import RoadDataSetup
from pipesets.road_data import REGIONS


class RoadDataSetupRequestSerializer(serializers.Serializer):
    region = serializers.ChoiceField(choices=REGIONS)


class RoadDataSetupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    region = serializers.ChoiceField(choices=REGIONS)
    status = serializers.ChoiceField(choices=RoadDataSetup.Status.choices)
    failure = serializers.ChoiceField(
        choices=RoadDataSetup.Failure.choices, allow_null=True
    )


class RoadDataSerializer(serializers.Serializer):
    regions = serializers.ListField(child=serializers.ChoiceField(choices=REGIONS))
    cached_regions = serializers.ListField(
        child=serializers.ChoiceField(choices=REGIONS)
    )
    has_roads = serializers.BooleanField()
    active_region = serializers.ChoiceField(choices=REGIONS, allow_null=True)
    setup = RoadDataSetupSerializer(allow_null=True)
