from django.urls import path
from . import views

app_name = 'currencies'

urlpatterns = [
    # Main Currency List (accessed from General Settings)
    path('', views.currency_list, name='currency_list'),
    
    # Currency Management
    path('add/', views.currency_create, name='currency_create'),
    path('<int:pk>/edit/', views.currency_edit, name='currency_edit'),
    path('sync/', views.manual_rate_sync, name='manual_sync'),
    
    # Exchange Rate Management
    path('<int:currency_pk>/rates/update/', views.exchange_rate_update, name='exchange_rate_update'),
    path('rates/history/', views.exchange_rate_history, name='exchange_rate_history'),
]