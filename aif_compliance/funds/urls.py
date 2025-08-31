from django.urls import path
from django.views.generic import TemplateView

# Minimal URL config for funds app to satisfy includes during CI
urlpatterns = [
    # placeholder view for portal/funds
    path('', TemplateView.as_view(template_name='portal/funds.html'), name='funds-portal'),
]
