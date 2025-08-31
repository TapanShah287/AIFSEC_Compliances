from django.urls import path
from django.views.generic import TemplateView

# Minimal URL config for transactions app used during CI/test runs
urlpatterns = [
    path('', TemplateView.as_view(template_name='portal/transactions.html'), name='transactions-portal'),
]
