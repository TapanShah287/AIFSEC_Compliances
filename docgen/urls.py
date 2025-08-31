from django.urls import path
from . import views

app_name = "docgen"
urlpatterns = [
    path("kyc/<int:investor_id>/", views.generate_kyc_for_investor, name="generate-kyc"),
    path("commitment/<int:commitment_id>/", views.generate_commitment_agreement, name="generate-commitment"),
]
