from django.urls import path, include
from rest_framework import routers

from investors.views import InvestorViewSet, InvestorKYCView
from investee_companies.views import CompanyViewSet, ShareValuationViewSet, CompanyFinancialsViewSet, CorporateActionViewSet
from funds.views import FundViewSet
from transactions.views import (
    PurchaseViewSet, RedemptionViewSet, InvestorCommitmentViewSet, CapitalCallViewSet,
    DrawdownReceiptViewSet, DistributionViewSet, InvestorUnitIssueViewSet
)
from compliances.views import ComplianceTaskViewSet, ComplianceDocumentViewSet

router = routers.DefaultRouter()
router.register(r"investors", InvestorViewSet, basename="investor")
router.register(r"companies", CompanyViewSet, basename="company")
router.register(r"companies/valuations", ShareValuationViewSet, basename="sharevaluation")
router.register(r"companies/financials", CompanyFinancialsViewSet, basename="companyfinancials")
router.register(r"companies/corporate-actions", CorporateActionViewSet, basename="corporateaction")
router.register(r"funds", FundViewSet, basename="fund")

router.register(r"transactions/purchases", PurchaseViewSet, basename="purchase")
router.register(r"transactions/redemptions", RedemptionViewSet, basename="redemption")
router.register(r"transactions/commitments", InvestorCommitmentViewSet, basename="investorcommitment")
router.register(r"drawdowns/calls", CapitalCallViewSet, basename="capitalcall")
router.register(r"drawdowns/receipts", DrawdownReceiptViewSet, basename="drawdownreceipt")
router.register(r"distributions", DistributionViewSet, basename="distribution")
router.register(r"unit-issues", InvestorUnitIssueViewSet, basename="unitissue")

router.register(r"compliance/tasks", ComplianceTaskViewSet, basename="compliance-task")
router.register(r"compliance/documents", ComplianceDocumentViewSet, basename="compliance-document")

urlpatterns = [
    path("", include(router.urls)),
    path("investors/<int:pk>/kyc/", InvestorKYCView.as_view(), name="investor-kyc"),
]
