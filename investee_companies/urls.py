from django.urls import path
from . import views

app_name = 'investee_companies'

urlpatterns = [
    path('', views.company_list_view, name='portal-list'),
    path('add/', views.company_add_view, name='portal-add'),
    path('<int:pk>/', views.company_detail_view, name='portal-detail'),
    path('<int:pk>/capital-structure/', views.manage_capital_structure, name='manage-capital'),
    path('<int:pk>/cap-table/', views.cap_table_view, name='cap-table'),
    path('<int:pk>/add-shareholder/', views.add_shareholding, name='add-shareholding'),
    path('<int:pk>/add-valuation/', views.add_valuation_report, name='add-valuation'),
    path('<int:pk>/corporate-action/', views.execute_corporate_action, name='add-corporate-action'),
]