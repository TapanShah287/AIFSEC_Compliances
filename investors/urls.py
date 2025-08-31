from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvestorViewSet, InvestorKYCView, InvestorDocumentViewSet, portal_investor_detail

router = DefaultRouter()
router.register(r"", InvestorViewSet, basename="investor")
router.register(r"documents", InvestorDocumentViewSet, basename="investor-document")

urlpatterns = [
    # API routes
    path("kyc/<int:pk>/", InvestorKYCView.as_view(), name="investor-kyc"),
    path("", include(router.urls)),

    # Portal route (template)
    path("portal/<int:pk>/", portal_investor_detail, name="portal-investor-detail"),
]
