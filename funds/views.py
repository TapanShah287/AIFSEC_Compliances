from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Fund
from .forms import FundForm
from transactions.models import InvestorCommitment, CapitalCall, Distribution
from .serializers import FundSerializer, InvestorCommitmentSerializer, CapitalCallSerializer, DistributionSerializer
from transactions.forms import InvestorCommitmentForm, CapitalCallForm, DistributionForm


# --- API Views (DRF) ---
class FundViewSet(viewsets.ModelViewSet):
    queryset = Fund.objects.all().order_by('name')
    serializer_class = FundSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def commitments(self, request, pk=None):
        fund = self.get_object()
        queryset = fund.commitments.select_related('investor')
        serializer = InvestorCommitmentSerializer(queryset, many=True)
        return Response(serializer.data)


# --- Portal Views ---

@login_required
def fund_add(request):
    if request.method == "POST":
        form = FundForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("funds:portal-funds")   # ✅ redirect to fund list
        else:
            # re-render page with errors
            return render(request, "portal/fund_add.html", {"form": form})
    else:
        form = FundForm()
    return render(request, "portal/fund_add.html", {"form": form})

@login_required
def fund_detail(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    commitments = fund.commitments.all()
    # TODO: Replace with actual query for investments & top investors
    investments = []  
    top_investors = commitments.values("investor__name").annotate(
        amount=Sum("amount_committed")
    ).order_by("-amount")[:5]

    return render(request, "funds/fund_detail.html", {
        "fund": fund,
        "commitments": commitments,
        "investments": investments,
        "top_investors": top_investors,
    })

@login_required
def fund_portfolio(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    return render(request, "portal/fund_portfolio.html", {"fund": fund})
        
@login_required
def portal_funds_list(request):
    query = request.GET.get("q", "")
    funds = Fund.objects.all().order_by("name")

    if query:
        funds = funds.filter(name__icontains=query)

    return render(request, "portal/funds.html", {"funds": funds})

@login_required
def add_investor_commitment(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    if request.method == 'POST':
        form = InvestorCommitmentForm(request.POST, fund=fund)
        if form.is_valid():
            commitment = form.save(commit=False)
            commitment.fund = fund
            commitment.save()
            messages.success(request, "Investor commitment added successfully.")
            return redirect('fund_detail', pk=fund.pk)
    else:
        form = InvestorCommitmentForm(fund=fund)
    return render(request, 'funds/add_commitment.html', {'form': form, 'fund': fund})

@login_required
def create_capital_call(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    # TODO: implement actual capital call creation
    return render(request, "portal/generic_message.html", {
        "title": "Create Capital Call",
        "message": f"Capital call form for fund {fund.name} (ID {pk}) not implemented yet."
    })

@login_required
def add_distribution(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    return render(request, "portal/generic_message.html", {
        "title": "Add Distribution",
        "message": f"Distribution form for fund {fund.name} (ID {pk}) not implemented yet."
    })

@login_required
def generate_report(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    return render(request, "portal/generic_message.html", {
        "title": "Generate Report",
        "message": f"Report generation for fund {fund.name} (ID {pk}) not implemented yet."
    })

@login_required
def add_receipt(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    # TODO: implement actual receipt logging later
    return render(request, "portal/generic_message.html", {
        "title": "Log Drawdown Receipt",
        "message": f"Receipt form for fund {fund.name} (ID {pk}) not implemented yet."
    })

@login_required
def compliance_dashboard(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    # TODO: replace with actual compliance integration
    return render(request, "portal/generic_message.html", {
        "title": "Compliance Dashboard",
        "message": f"Compliance dashboard for fund {fund.name} (ID {pk}) not implemented yet."
    })