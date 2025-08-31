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
    path("api/funds/", include("funds.api_urls")),           # ✅ DRF endpoints only
    path("api/transactions/", include("transactions.urls")),
    path("api/transactions/recent/", RedirectView.as_view(url="/api/transactions/feed/", permanent=False)),
    path("api/companies/", include("investee_companies.urls")),
    path("api/investors/", include("investors.urls")),
    path("api/compliance/", include("compliances.urls")),
    path("api/docgen/", include("docgen.urls")),

    # --- Auth ---
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # --- Portal ---
    path("portal/", TemplateView.as_view(template_name="portal/dashboard.html"), name="portal-home"),
    path("portal/funds/", include("funds.urls")),            # ✅ Portal views only
    path("portal/manager_entities/", include("manager_entities.urls")),
    path("portal/investors/", TemplateView.as_view(template_name="portal/investors.html"), name="portal-investors"),
    path("portal/investors/onboard/", TemplateView.as_view(template_name="portal/investor_onboard.html"), name="portal-investor-onboard"),
    path("portal/investors/<int:pk>/", TemplateView.as_view(template_name="portal/investor_detail.html"), name="portal-investor-detail"),
    path("portal/companies/", TemplateView.as_view(template_name="portal/companies.html"), name="portal-companies"),
    path("portal/companies/add/", TemplateView.as_view(template_name="portal/company_add.html"), name="portal-company-add"),
    path("portal/companies/<int:pk>/", TemplateView.as_view(template_name="portal/company_detail.html"), name="portal-company-detail"),
    path("portal/transactions/", TemplateView.as_view(template_name="portal/transactions.html"), name="portal-transactions"),
    path("portal/compliance/", TemplateView.as_view(template_name="portal/compliance.html"), name="portal-compliance"),

    # Root → Login
    path("", lambda request: redirect("login", permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 