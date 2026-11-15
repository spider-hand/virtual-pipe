from django.urls import path

from pipesets.views import attribute_sets, districts

urlpatterns = [
    path("attribute-sets/", attribute_sets, name="attribute-sets"),
    path("districts/", districts, name="districts"),
]
