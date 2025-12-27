from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from dashboard.views import dashboard_view
from django.conf import settings 
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")), 
    
    # --- Authentication ---
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # --- Portal Home ---
    path("portal/", dashboard_view, name="portal-home"),
    
    # Placeholder for transactions to prevent NoReverseMatch in base.html
    path("portal/transactions/", TemplateView.as_view(template_name="transactions/transactions_list.html"), name="portal-transactions"),

    # --- App Includes (Namespaced) ---
    path("portal/funds/", include("funds.urls")),
    path("portal/investors/", include("investors.urls")), 
    path("portal/companies/", include("investee_companies.urls")),
    path("portal/compliance/", include("compliances.urls")),
    path('portal/managers/', include("manager_entities.urls")),
    path('portal/settings/currencies/', include('currencies.urls')),


    # NEW: Transactions App URLs
    path('portal/txn/', include('transactions.urls')), 
    path("portal/docgen/", include("docgen.urls")),

    # Root -> Dashboard
    path("", TemplateView.as_view(template_name="dashboard/dashboard.html"), name="index"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)