from django.urls import path
from . import views

app_name = 'compliances'

urlpatterns = [
    path('tasks/', views.task_list_view, name='task-list'),
    path('tasks/add/', views.create_task, name='task-create'), # Keep this name
    path('calendar/', views.calendar_view, name='calendar'),
    path('reports/', views.compliance_reports_view, name='reports'),
    # Add the detail path so the "Edit" icons work too
    path('tasks/<int:pk>/', views.task_detail_view, name='task-detail'), 
]