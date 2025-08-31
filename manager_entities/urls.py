app_name = "manager_entities"

from django.urls import path
from . import views

urlpatterns = [
    path("<int:pk>/", views.manager_detail, name="manager_detail"),
]
