from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvestorCommitmentViewSet

router = DefaultRouter()
router.register(r"commitments", InvestorCommitmentViewSet, basename="commitment")

urlpatterns = [
    # API routes
    path("", include(router.urls)),
]
