from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'templates', views.DocumentTemplateViewSet, basename='template')

urlpatterns = [
    path('', include(router.urls)),
    
    # RPC Style generation endpoints
    path('generate/kyc/<int:investor_id>/', views.generate_kyc_document, name='generate-kyc'),
    path('generate/commitment/<int:commitment_id>/', views.generate_commitment_letter, name='generate-commitment'),
]