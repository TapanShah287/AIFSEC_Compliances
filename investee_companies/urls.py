app_name = 'investee_companies'
from django.urls import path, include, re_path
from . import views as ic_views
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet
from .views_detail_safe import investee_company_detail_json
from .views_detail_safe import investee_company_shareholding_snapshot_json
from .views_api import company_shareholding_api

router = DefaultRouter()
router.register(r"", CompanyViewSet, basename="company")

urlpatterns = [
    # Redirect DRF detail /<id>/ → template detail /company/<id>/
    re_path(r'^(?P<pk>\d+)/$', ic_views.redirect_company_detail, name='company_router_redirect'),
    
    # Template pages
    path('company/<int:company_id>/', ic_views.investee_company_detail, name='investee_company_detail'),
    path('company/<int:company_id>/shareholding-pattern/', ic_views.company_shareholding_pattern, name='company_shareholding_pattern'),
    path('company/<int:company_id>/cap-table/', ic_views.company_cap_table, name='company_cap_table'),
    path('company/<int:company_id>/add-shareholding/', ic_views.add_shareholding, name='add_shareholding'),
    path('company/<int:company_id>/add-share-valuation/', ic_views.add_share_valuation, name='add_share_valuation'),
    path("company/<int:company_id>/json/", investee_company_detail_json, name="api_company_detail_json"),
    path("company/<int:company_id>/shareholding-snapshot/", investee_company_shareholding_snapshot_json, name="company_shareholding_snapshot_json"),

    path("<int:pk>/shareholding/", company_shareholding_api, name="company-shareholding"),

    # Router LAST so it doesn't shadow the above
    path("", include(router.urls)),
]