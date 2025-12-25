from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'docgen'

router = DefaultRouter()
router.register(r'templates', views.DocumentTemplateViewSet)
router.register(r'documents', views.GeneratedDocumentViewSet)

urlpatterns = [
    # Portal UI
    path('hub/', views.docgen_dashboard, name='hub'),
    
    # API
    path('api/', include(router.urls)),
]