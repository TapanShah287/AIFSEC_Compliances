from django.urls import path
from . import views

app_name = "manager_entities"

urlpatterns = [
    # --- Entity Management ---
    path("", views.manager_list, name="manager_list"),
    path("create/", views.manager_create, name="manager_create"),
    path("settings/", views.settings_hub, name="settings_hub"),
    path("settings/users/create/", views.user_create, name="user_create"),
    path("<int:pk>/", views.manager_detail, name="manager_detail"),
    path("<int:pk>/update/", views.manager_update, name="manager_update"),

    # --- Multi-Manager Switching Logic ---
    # This endpoint is called by the dropdown in base.html
    path("switch/<int:pk>/", views.switch_manager, name="switch_manager"),

    # --- Role-Based Team Management ---
    # Allows Admins to invite/manage users for their specific entity
    path("<int:entity_pk>/team/", views.team_list, name="team_list"),
    path("<int:entity_pk>/team/add/", views.team_member_add, name="team_member_add"),
    path("membership/<int:pk>/remove/", views.team_member_remove, name="team_member_remove"),
]