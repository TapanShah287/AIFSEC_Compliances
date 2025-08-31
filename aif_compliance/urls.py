from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.conf import settings 
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic.base import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- APIs ---
    path("api/transactions/recent/", RedirectView.as_view(url="/api/transactions/feed/", permanent=False)),
        path("api/funds/", include("aif_compliance.funds.api_urls")),           # ✅ DRF endpoints only
        path("api/transactions/", include("aif_compliance.transactions.urls")),
        path("api/companies/", include("aif_compliance.investee_companies.urls")),
        path("api/investors/", include("aif_compliance.investors.urls")),
        path("api/compliance/", include("aif_compliance.compliances.urls")),
        path("api/docgen/", include("aif_compliance.docgen.urls")),

    # --- Auth ---
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # --- Portal ---
    path("portal/", TemplateView.as_view(template_name="portal/dashboard.html"), name="portal-home"),
        path("portal/funds/", include("aif_compliance.funds.urls")),            # ✅ Portal views only
    path("portal/manager_entities/", include("aif_compliance.manager_entities.urls")),
    # The rest of the portal routes are TemplateViews and do not use include(), so no change needed

    # Root → Login
    path("", lambda request: redirect("login", permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 