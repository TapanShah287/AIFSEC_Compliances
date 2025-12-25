from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from datetime import date, timedelta
import calendar


# Local Imports
from .models import ComplianceTask, ComplianceDocument
from .serializers import ComplianceTaskSerializer, ComplianceDocumentSerializer
from .forms import ComplianceTaskForm, ComplianceDocumentForm
from .services import generate_for_purchase, generate_for_redemption
from funds.models import Fund
from transactions.models import PurchaseTransaction, RedemptionTransaction
from django.utils import timezone



# ==========================================
# 1. API ViewSets (Used by api/urls.py)
# ==========================================

class ComplianceTaskViewSet(viewsets.ModelViewSet):
    queryset = ComplianceTask.objects.all().select_related('fund', 'assigned_to').order_by('due_date')
    serializer_class = ComplianceTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['fund', 'status', 'topic']

class ComplianceDocumentViewSet(viewsets.ModelViewSet):
    queryset = ComplianceDocument.objects.all().order_by('-uploaded_at')
    serializer_class = ComplianceDocumentSerializer
    permission_classes = [IsAuthenticated]


# ==========================================
# 2. Portal Views (HTML Interface)
# ==========================================

@login_required
def dashboard_view(request):
    """
    Main Compliance Dashboard.
    Calculates metrics in Python to ensure template performance and avoid syntax errors.
    """
    tasks = ComplianceTask.objects.all().order_by('due_date')
    
    # Calculate overdue count for pending/in-progress tasks
    # We exclude COMPLETED and CANCELLED to match the model's 'is_overdue' logic
    now = timezone.now().date()
    overdue_count = tasks.filter(
        due_date__lt=now
    ).exclude(status__in=['COMPLETED', 'CANCELLED']).count()
    
    return render(request, 'compliances/dashboard.html', {
        'tasks': tasks,
        'overdue_count': overdue_count,
    })

@login_required
def create_task(request):
    """
    Handles manual task creation.
    """
    if request.method == 'POST':
        form = ComplianceTaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f"Task '{task.title}' created successfully.")
            return redirect('compliances:task-list')
    else:
        form = ComplianceTaskForm()

    return render(request, 'compliances/task_form.html', {'form': form})

@login_required
def task_list_view(request):
    """
    Renders the List View of compliance tasks.
    """
    today = timezone.now().date()
    tasks = ComplianceTask.objects.all()

    # Calculate Summary Stats for the "Kanban-lite" header
    context = {
        'tasks': tasks,
        'overdue_count': tasks.filter(due_date__lt=today, status__in=['PENDING', 'IN_PROGRESS']).count(),
        'due_this_week': tasks.filter(due_date__range=[today, today + timedelta(days=7)]).count(),
        'upcoming_count': tasks.filter(due_date__gt=today + timedelta(days=7)).count(),
        'completed_count': tasks.filter(status='COMPLETED').count(),
        'current_tab': 'list'
    }
    return render(request, 'compliances/task_list.html', context)

@login_required
def task_detail_view(request, pk):
    """
    Detailed view for a specific task.
    Handles metadata updates and document evidence uploads.
    """
    task = get_object_or_404(ComplianceTask, pk=pk)
    documents = task.documents.all().order_by('-uploaded_at')
    
    task_form = ComplianceTaskUpdateForm(instance=task)
    doc_form = ComplianceDocumentForm()
    
    if request.method == 'POST':
        if 'update_task' in request.POST:
            task_form = ComplianceTaskUpdateForm(request.POST, instance=task)
            if task_form.is_valid():
                task_form.save()
                messages.success(request, "Workflow status updated.")
                return redirect('compliances:task_detail', pk=task.pk)
            
        elif 'upload_doc' in request.POST:
            doc_form = ComplianceDocumentForm(request.POST, request.FILES)
            if doc_form.is_valid():
                doc = doc_form.save(commit=False)
                doc.task = task
                doc.uploaded_by = request.user
                doc.save()
                
                if doc_form.cleaned_data.get('mark_complete'):
                    task.status = 'COMPLETED'
                    task.save()
                
                messages.success(request, "Evidence uploaded successfully.")
                return redirect('compliances:task_detail', pk=task.pk)
                    
    return render(request, 'compliances/task_detail.html', {
        'task': task,
        'documents': documents,
        'task_form': task_form,
        'doc_form': doc_form,
    })

@login_required
def generate_from_purchase(request, pk):
    """Automated task generation from a Purchase Transaction."""
    from transactions.models import PurchaseTransaction
    purchase = get_object_or_404(PurchaseTransaction, pk=pk)
    
    task, created = ComplianceTask.objects.get_or_create(
        fund=purchase.fund,
        purchase_transaction=purchase,
        topic='DOCUMENT',
        defaults={
            'description': f"Collect SHA and closing documents for investment in {purchase.investee_company.name}.",
            'due_date': timezone.now().date() + timezone.timedelta(days=7),
            'status': 'PENDING'
        }
    )
    
    if created:
        messages.success(request, "Compliance workflow initiated for this purchase.")
    else:
        messages.info(request, "A compliance task is already active for this transaction.")
        
    return redirect('compliances:task_detail', pk=task.pk)

@login_required
def generate_from_redemption(request, pk):
    """
    Automated task generation from a Redemption Transaction.
    FIXED: Added this missing view to resolve AttributeError in urls.py.
    """
    from transactions.models import RedemptionTransaction
    redemption = get_object_or_404(RedemptionTransaction, pk=pk)
    
    task, created = ComplianceTask.objects.get_or_create(
        fund=redemption.fund,
        redemption_transaction=redemption,
        topic='DOCUMENT',
        defaults={
            'description': f"Collect exit documents and redemption filings for {redemption.investee_company.name}.",
            'due_date': timezone.now().date() + timezone.timedelta(days=7),
            'status': 'PENDING'
        }
    )
    
    if created:
        messages.success(request, "Compliance workflow initiated for this redemption.")
    else:
        messages.info(request, "A compliance task is already active for this transaction.")
        
    return redirect('compliances:task_detail', pk=task.pk)

@login_required
def task_delete_view(request, pk):
    """Safely remove a compliance task."""
    task = get_object_or_404(ComplianceTask, pk=pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, "Compliance task removed.")
        return redirect('compliances:portal-home')
    return render(request, 'compliances/task_confirm_delete.html', {'task': task})

@login_required
def calendar_view(request):
    """
    Generates the grid logic for the Compliance Calendar.
    """
    # 1. Determine Month/Year to display
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # 2. Setup Calendar Iterator
    cal = calendar.Calendar(firstweekday=6) # 6 = Sunday
    month_days = cal.monthdatescalendar(year, month)
    
    # 3. Fetch Tasks for this date range
    # Get first and last date visible on the calendar grid
    start_date = month_days[0][0]
    end_date = month_days[-1][-1]
    
    tasks_in_range = ComplianceTask.objects.filter(
        due_date__range=[start_date, end_date]
    )

    # 4. Build the Grid Data Structure
    calendar_data = []
    for week in month_days:
        for day in week:
            # Find tasks for this specific day
            day_tasks = [t for t in tasks_in_range if t.due_date == day]
            
            calendar_data.append({
                'date': day,
                'is_today': (day == today),
                'is_current_month': (day.month == month),
                'tasks': day_tasks
            })

    # 5. Calculate Nav Links
    prev_date = date(year, month, 1) - timedelta(days=1)
    next_date = date(year, month, 28) + timedelta(days=4) # Jump to next month safely
    
    context = {
        'calendar_days': calendar_data,
        'current_month': date(year, month, 1),
        'prev_month': f"{prev_date.year}&month={prev_date.month}",
        'next_month': f"{next_date.year}&month={next_date.month}",
        'current_tab': 'calendar'
    }
    
    return render(request, 'compliances/calendar.html', context)