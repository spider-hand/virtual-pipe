from django.urls import path

from pipesets.views import attribute_sets, create_pipeset, districts, get_pipeset_status

urlpatterns = [
    path("attribute-sets/", attribute_sets, name="attribute-sets"),
    path("districts/", districts, name="districts"),
    path("pipesets/", create_pipeset, name="pipesets"),
    path("pipesets/<uuid:id>/", get_pipeset_status, name="pipeset-status"),
]
