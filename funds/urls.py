app_name = "funds"

from django.urls import path
from . import views

urlpatterns = [
    path("", views.portal_funds_list, name="portal-funds"),
    path("add/", views.fund_add, name="fund_add"),
    path("<int:pk>/", views.fund_detail, name="fund_detail"),
    path("<int:pk>/portfolio/", views.fund_portfolio, name="fund_portfolio"),
    path("<int:pk>/add-commitment/", views.add_investor_commitment, name="add-commitment"),
    path("<int:pk>/create-call/", views.create_capital_call, name="create-call"),
    path("<int:pk>/add-distribution/", views.add_distribution, name="add-distribution"),
    path("<int:pk>/generate-report/", views.generate_report, name="generate-report"),
    path("<int:pk>/add-receipt/", views.add_receipt, name="add-receipt"),
    path("<int:pk>/compliance-dashboard/", views.compliance_dashboard, name="compliance-dashboard"),
]
