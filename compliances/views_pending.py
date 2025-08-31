from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import ComplianceTask
from funds.models import Fund
from .forms import ComplianceTaskUpdateForm

CATEGORIES = [
    ("MCA", "MCA Filings"),
    ("DOCUMENT", "Documents"),
    ("SEBI", "SEBI Compliances"),
    ("TAX", "Tax Compliances"),
]

@login_required
def pending_list(request):
    qs = (ComplianceTask.objects
          .select_related("fund", "purchase_transaction", "redemption_transaction")
          .order_by("due_date", "pk"))
    qs = qs.filter(Q(status__iexact="PENDING") | Q(status=""))

    fund_id = request.GET.get("fund")
    category = request.GET.get("category")
    q = request.GET.get("q")

    if fund_id:
        qs = qs.filter(fund_id=fund_id)
    if category:
        qs = qs.filter(topic__iexact=category)
    if q:
        qs = qs.filter(Q(description__icontains=q) | Q(notes__icontains=q))

    funds = Fund.objects.order_by("name").all()

    return render(request, "compliances/pending_list.html", {
        "tasks": qs,
        "funds": funds,
        "categories": CATEGORIES,
        "active_fund": int(fund_id) if fund_id else None,
        "active_category": category or "",
        "query": q or "",
    })

@login_required
def task_edit(request, pk):
    obj = get_object_or_404(ComplianceTask, pk=pk)
    if request.method == "POST":
        form = ComplianceTaskUpdateForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Compliance task updated.")
            next_url = request.GET.get("next") or "compliances:pending"
            return redirect(next_url)
    else:
        form = ComplianceTaskUpdateForm(instance=obj)
    return render(request, "compliances/task_form.html", {"form": form, "task": obj})
