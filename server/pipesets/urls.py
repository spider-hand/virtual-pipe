from django.urls import path

from pipesets.views import attribute_sets, districts, get_pipeset_status, pipesets

urlpatterns = [
    path("attribute-sets/", attribute_sets, name="attribute-sets"),
    path("districts/", districts, name="districts"),
    path("pipesets/", pipesets, name="pipesets"),
    path("pipesets/<uuid:id>/", get_pipeset_status, name="pipeset-status"),
]
