from django.urls import path, include
from rest_framework import routers

# Import ViewSets from your apps
from investors.views import InvestorViewSet, InvestorKYCView
from investee_companies.views import (
    CompanyViewSet, 
    ShareValuationViewSet, 
    CompanyFinancialsViewSet, 
    CorporateActionViewSet
)
from funds.views import FundViewSet
from . import views
from transactions.views import (
    PurchaseViewSet, 
    RedemptionViewSet, 
    InvestorCommitmentViewSet, 
    CapitalCallViewSet, 
    DrawdownReceiptViewSet, 
    DistributionViewSet, 
    InvestorUnitIssueViewSet
)
from compliances.views import ComplianceTaskViewSet, ComplianceDocumentViewSet
from docgen.views import DocumentTemplateViewSet

# --- Router Configuration ---
router = routers.DefaultRouter()

# Investors
router.register(r"investors", InvestorViewSet, basename="investor")

# Companies
router.register(r"companies", CompanyViewSet, basename="company")
router.register(r"companies/valuations", ShareValuationViewSet, basename="sharevaluation")
router.register(r"companies/financials", CompanyFinancialsViewSet, basename="companyfinancials")
router.register(r"companies/corporate-actions", CorporateActionViewSet, basename="corporateaction")

# Funds
router.register(r"funds", FundViewSet, basename="fund")

# Transactions & Drawdowns
router.register(r"transactions/purchases", PurchaseViewSet, basename="purchase")
router.register(r"transactions/redemptions", RedemptionViewSet, basename="redemption")
router.register(r"transactions/commitments", InvestorCommitmentViewSet, basename="investorcommitment")
router.register(r"transactions/unit-issues", InvestorUnitIssueViewSet, basename="unitissue")

router.register(r"drawdowns/calls", CapitalCallViewSet, basename="capitalcall")
router.register(r"drawdowns/receipts", DrawdownReceiptViewSet, basename="drawdownreceipt")
router.register(r"distributions", DistributionViewSet, basename="distribution")

# Compliance
router.register(r"compliance/tasks", ComplianceTaskViewSet, basename="compliance-task")
router.register(r"compliance/documents", ComplianceDocumentViewSet, basename="compliance-document")


# DocGen
router.register(r"docgen/templates", DocumentTemplateViewSet, basename="document-template")

urlpatterns = [
    # Router URLs
    path("", include(router.urls)),

    
    # Custom/Non-ViewSet URLs
    path("investors/<int:pk>/kyc/", InvestorKYCView.as_view(), name="investor-kyc"),
    path('search/', views.global_search, name='global-search'),
]