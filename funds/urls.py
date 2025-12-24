from django.urls import path
from . import views

app_name = 'funds'

urlpatterns = [
    # --- Management ---
    path('', views.portal_funds_list, name='portal-funds'),
    path('add/', views.fund_add, name='fund_add'),
    path('<int:pk>/', views.fund_detail, name='fund_detail'),
    
    # --- Reporting ---
    path('<int:pk>/portfolio/', views.fund_portfolio, name='fund_portfolio'),
    path('<int:pk>/performance/', views.fund_performance, name='performance-report'),
    path('<int:pk>/activity/', views.activity_log, name='activity-log'),

    # --- Compliance ---
    path('<int:pk>/stewardship/log/', views.log_stewardship_engagement, name='log_stewardship'),
    path('<int:pk>/migrate/ai-only/', views.migrate_to_ai_only, name='migrate_ai_only'),

    # --- Transactions (Wrapper Routes) ---
    path('<int:pk>/commitment/add/', views.add_commitment, name='add-commitment'),
    path('<int:pk>/call/create/', views.create_capital_call, name='create-call'),
    path('<int:pk>/receipt/add/', views.add_receipt, name='add-receipt'),
    path('<int:pk>/distribution/add/', views.add_distribution, name='add-distribution'),
]