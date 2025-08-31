from django.urls import path
from .views import compliance_tasks

app_name = "compliances"

urlpatterns = [
    path("tasks/", compliance_tasks, name="tasks"),   # /api/compliance/tasks/
]
