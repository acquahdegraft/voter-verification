from django.urls import path
from . import views

urlpatterns = [
    path("", views.voters, name="voters"),
    path("voter/<int:voter_id>/", views.voter, name="voter"),
    path("voter/register/", views.voter_forms, name="voter_forms"),
]