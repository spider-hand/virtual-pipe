from django.urls import path

from pipesets.views.district import districts, prefectures
from pipesets.views.pipeset import (
    attribute_sets,
    download_pipeset,
    get_pipeset_status,
    pipesets,
)
from pipesets.views.road import road_data, road_data_setups

urlpatterns = [
    path("road-data/", road_data, name="road-data"),
    path("road-data/setups/", road_data_setups, name="road-data-setups"),
    path("attribute-sets/", attribute_sets, name="attribute-sets"),
    path("districts/", districts, name="districts"),
    path("prefectures/", prefectures, name="prefectures"),
    path("pipesets/", pipesets, name="pipesets"),
    path("pipesets/<uuid:id>/", get_pipeset_status, name="pipeset-status"),
    path("pipesets/<uuid:id>/export/", download_pipeset, name="pipeset-export"),
]
