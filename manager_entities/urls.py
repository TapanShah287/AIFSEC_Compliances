from django.urls import path
from . import views

app_name = "manager_entities"

urlpatterns = [
    path("", views.manager_list, name="manager_list"),
    path("create/", views.manager_create, name="manager_create"),
    path("<int:pk>/", views.manager_detail, name="manager_detail"),
    path("<int:pk>/update/", views.manager_update, name="manager_update"),
]