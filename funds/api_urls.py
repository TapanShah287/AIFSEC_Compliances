from rest_framework.routers import DefaultRouter
from .views import FundViewSet

router = DefaultRouter()
# register Fund API at root (so it's /api/funds/ not /api/funds/api/)
router.register(r"", FundViewSet, basename="fund-api")

urlpatterns = router.urls
