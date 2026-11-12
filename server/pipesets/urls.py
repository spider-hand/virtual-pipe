from django.urls import path

from pipesets.views import districts

urlpatterns = [
    path("districts/", districts, name="districts"),
]
