from django.urls import path

from pipesets.views import (
    attribute_sets,
    districts,
    download_pipeset,
    get_pipeset_status,
    pipesets,
    prefectures,
)

urlpatterns = [
    path("attribute-sets/", attribute_sets, name="attribute-sets"),
    path("districts/", districts, name="districts"),
    path("prefectures/", prefectures, name="prefectures"),
    path("pipesets/", pipesets, name="pipesets"),
    path("pipesets/<uuid:id>/", get_pipeset_status, name="pipeset-status"),
    path("pipesets/<uuid:id>/export/", download_pipeset, name="pipeset-export"),
]
