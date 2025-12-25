from django.urls import path
from . import views

app_name = 'compliances'

urlpatterns = [
    path('tasks/', views.task_list_view, name='task-list'),
    path('tasks/add/', views.create_task, name='task-create'), # New URL
    path('calendar/', views.calendar_view, name='calendar'),
]