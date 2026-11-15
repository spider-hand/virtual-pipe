from django.urls import path

from pipesets.views import create_attribute_set, districts

urlpatterns = [
    path("attribute-sets/", create_attribute_set, name="attribute-sets"),
    path("districts/", districts, name="districts"),
]
