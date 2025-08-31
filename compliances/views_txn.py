from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import ComplianceTaskForm, ComplianceDocumentForm
from .models import ComplianceTask
from .services import generate_for_purchase, generate_for_redemption
from transactions.models import PurchaseTransaction, RedemptionTransaction

@login_required
def generate_from_purchase(request, pk):
    purchase = get_object_or_404(PurchaseTransaction, pk=pk)
    tasks = generate_for_purchase(purchase, assigned_to=request.user)
    messages.success(request, f"Created {len(tasks)} compliance task(s) for purchase #{purchase.id}.")
    return redirect(reverse('compliances:compliance_list', args=[purchase.fund_id]))

@login_required
def generate_from_redemption(request, pk):
    redemption = get_object_or_404(RedemptionTransaction, pk=pk)
    tasks = generate_for_redemption(redemption, assigned_to=request.user)
    messages.success(request, f"Created {len(tasks)} compliance task(s) for redemption #{redemption.id}.")
    return redirect(reverse('compliances:compliance_list', args=[redemption.fund_id]))

@login_required
def task_detail(request, pk):
    task = get_object_or_404(ComplianceTask, pk=pk)
    if request.method == 'POST':
        if 'file' in request.FILES:
            dform = ComplianceDocumentForm(request.POST, request.FILES)
            if dform.is_valid():
                doc = dform.save(commit=False)
                doc.task = task
                doc.uploaded_by = request.user
                doc.save()
                messages.success(request, 'Document uploaded.')
                return redirect(request.path)
        form = ComplianceTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated.')
            return redirect(request.path)
    else:
        form = ComplianceTaskForm(instance=task)
        dform = ComplianceDocumentForm()
    return render(request, 'compliances/task_detail.html', {'task': task, 'form': form, 'dform': dform})

@login_required
@require_POST
def bulk_complete(request):
    ids = request.POST.getlist("task_ids")
    qs = ComplianceTask.objects.filter(pk__in=ids)
    count = 0
    for t in qs:
        if t.status != 'COMPLETED':
            t.status = 'COMPLETED'
            t.save()
            count += 1
    messages.success(request, f"Marked {count} task(s) as completed.")
    return redirect(request.META.get("HTTP_REFERER", reverse('compliances:compliance_index')))
