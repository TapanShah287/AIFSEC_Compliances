from django.urls import path
from . import views

app_name = "compliances"

urlpatterns = [
    # Dashboard
    path("", views.dashboard_view, name="portal-home"),
    
    # Task Management
    path("new/", views.task_create_view, name="task_create"),
    path("<int:pk>/", views.task_detail_view, name="task_detail"),

    # Generators
    path("generate/purchase/<int:pk>/", views.generate_from_purchase, name="generate_purchase"),
    path("generate/redemption/<int:pk>/", views.generate_from_redemption, name="generate_redemption"),
]