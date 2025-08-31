from rest_framework import viewsets
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Investor, InvestorDocument
from transactions.models import InvestorCommitment
from .serializers import InvestorSerializer, InvestorDocumentSerializer

class InvestorViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = InvestorSerializer
    lookup_value_regex = r"\d+" 

    def get_queryset(self):
        return Investor.objects.all().select_related("kyc_status").order_by("id")

class InvestorKYCView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        inv = get_object_or_404(Investor, pk=pk)
        return Response({"id": inv.id, "kyc_status": getattr(inv, "kyc_status", None)})
    def put(self, request, pk):
        inv = get_object_or_404(Investor, pk=pk)
        status_val = request.data.get("status")
        if status_val is not None and hasattr(inv, "kyc_status"):
            inv.kyc_status = status_val
            inv.save()
        return Response({"id": inv.id, "kyc_status": getattr(inv, "kyc_status", None)})

class InvestorDocumentViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = InvestorDocumentSerializer
    parser_classes = [MultiPartParser, FormParser]   # accept file uploads

    def get_queryset(self):
        qs = InvestorDocument.objects.select_related("investor")
        inv = self.request.query_params.get("investor")
        if inv:
            qs = qs.filter(investor_id=inv)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["enforce_matrix"] = True
        return ctx
    
        REQUIRED_DOCS = {"IND": {"ACCOUNT_FORM","PAN","AADHAR"}, "NON-IND": {"MOA","AOA","COI","ACCOUNT_FORM"}}

    @action(detail=True, methods=["get"], url_path="required-docs")
    def required_docs(self, request, pk=None):
        investor = self.get_object()
        inv_type = getattr(getattr(investor, "kyc_status", None), "investor_type", "IND")
        required = REQUIRED_DOCS[inv_type]
        have = set(investor.documents.values_list("doc_type", flat=True))
        missing = sorted(list(required - have))
        return Response({"investor_type": inv_type, "required": sorted(list(required)), "missing": missing})

@login_required
def portal_investor_detail(request, pk):
    investor = get_object_or_404(Investor, pk=pk)

    # All commitments of this investor (with fund linked)
    commitments = investor.commitments.select_related("fund").all()

    # Total commitment
    total_commitment = commitments.aggregate(total=Sum("amount_committed"))["total"] or 0

    return render(request, "investors/investor_detail.html", {
        "investor": investor,
        "commitments": commitments,
        "total_commitment": total_commitment,
    })