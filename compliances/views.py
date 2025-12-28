from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from datetime import date, timedelta
import calendar
from django.db.models import Min
from django.urls import reverse


# Local Imports
from .models import ComplianceTask, ComplianceDocument
from .serializers import ComplianceTaskSerializer, ComplianceDocumentSerializer
from .forms import ComplianceTaskForm, ComplianceDocumentForm
#from .services import generate_for_purchase, generate_for_redemption
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
    Handles manual task creation with smart redirect and auto-fill.
    """
    # 1. Capture fund_id from URL (works for both GET and POST if form action is empty)
    fund_id = request.GET.get('fund')

    if request.method == 'POST':
        form = ComplianceTaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f"Task '{task.title}' created successfully.")
            
            # 2. Smart Redirect Logic
            # If we started with a specific fund, go back to that fund's filtered list
            if fund_id:
                base_url = reverse('compliances:task-list')
                return redirect(f"{base_url}?fund={fund_id}")
            
            # Otherwise, go to the main list
            return redirect('compliances:task-list')
    else:
        # 3. Auto-fill Logic
        # If fund_id is present, pre-select it in the dropdown
        initial_data = {}
        if fund_id:
            initial_data['fund'] = fund_id
            
        form = ComplianceTaskForm(initial=initial_data)

    return render(request, 'compliances/task_form.html', {'form': form})


@login_required
def task_list_view(request):
    """
    Focused List View logic for Multiple Funds:
    1. Always show ALL tasks that are PENDING/OVERDUE for dates <= Today.
    2. For future dates, show the earliest task for each Rule PER FUND.
    """
    fund_id = request.GET.get('fund')
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    next_30 = today + timedelta(days=30)
    
    # 1. Base Queryset
    base_qs = ComplianceTask.objects.all().select_related('compliance_master', 'fund')
    
    # Apply global filter if a specific fund is selected in the UI
    if fund_id:
        base_qs = base_qs.filter(fund_id=fund_id)

    overdue_count = base_qs.filter(due_date__lt=today).exclude(status='COMPLETED').count()
    due_this_week = base_qs.filter(due_date__range=[today, next_week]).exclude(status='COMPLETED').count()
    upcoming_count = base_qs.filter(due_date__range=[today, next_30]).exclude(status='COMPLETED').count()
    completed_count = base_qs.filter(status='COMPLETED').count()

    # 2. Get IDs for ALL Overdue or Pending tasks (Past or Present)
    # These must stay visible until completed.
    actionable_ids = base_qs.filter(
        due_date__lte=today
    ).exclude(status='COMPLETED').values_list('id', flat=True)

    # 3. Get IDs for the "Next Up" tasks for EACH Fund
    # We group by both 'fund' and 'compliance_master'
    future_earliest_ids = base_qs.filter(
        due_date__gt=today,
        status='PENDING'
    ).values('fund', 'compliance_master').annotate(
        earliest_id=Min('id')
    ).values_list('earliest_id', flat=True)

    # 4. Combine IDs and fetch final QuerySet
    final_ids = list(set(list(actionable_ids) + list(future_earliest_ids)))
    tasks = ComplianceTask.objects.filter(id__in=final_ids).order_by('due_date', 'fund__name')

    # Metrics for Dashboard
    context = {
        'tasks': tasks,
        'fund_id': fund_id,
        'overdue_count': base_qs.filter(due_date__lt=today).exclude(status='COMPLETED').count(),
        'total_active_funds': base_qs.values('fund').distinct().count(),
        'overdue_count': overdue_count,
        'due_this_week': due_this_week,
        'upcoming_count': upcoming_count,
        'completed_count': completed_count,
        'current_tab': 'list',
    }
    
    return render(request, 'compliances/task_list.html', context)


@login_required
def task_detail_view(request, pk):
    task = get_object_or_404(ComplianceTask, pk=pk)
    documents = task.documents.all().order_by('-uploaded_at')
    
    # Initialize forms
    task_form = ComplianceTaskForm(instance=task)
    doc_form = ComplianceDocumentForm()
    
    if request.method == 'POST':
        # HANDLE TASK METADATA UPDATE
        if 'update_task' in request.POST:
            task_form = ComplianceTaskForm(request.POST, instance=task)
            if task_form.is_valid():
                task_form.save()
                messages.success(request, "Task updated successfully!")
                return redirect('compliances:task-detail', pk=task.pk)
            else:
                messages.error(request, "Update failed. Please check the fields.")

        # HANDLE DOCUMENT UPLOAD
        elif 'upload_doc' in request.POST:
            doc_form = ComplianceDocumentForm(request.POST, request.FILES)
            if doc_form.is_valid():
                doc = doc_form.save(commit=False)
                doc.task = task
                doc.uploaded_by = request.user
                doc.save()
                
                # Check if user checked the 'Mark Complete' box in the form
                if doc_form.cleaned_data.get('mark_complete'):
                    task.status = 'COMPLETED'
                    task.save()
                
                messages.success(request, "Evidence uploaded successfully.")
                return redirect('compliances:task-detail', pk=task.pk)

    return render(request, 'compliances/task_detail.html', {
        'task': task,
        'documents': documents,
        'task_form': task_form,
        'doc_form': doc_form,
    })

@login_required
def initialize_fund_roadmap(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    count = generate_standard_aif_tasks(fund)
    messages.success(request, f"Roadmap initialized. {count} tasks added to calendar.")
    return redirect('compliances:calendar')

@login_required
def upload_compliance_evidence(request, task_id):
    task = get_object_or_404(ComplianceTask, id=task_id)
    if request.method == 'POST' and request.FILES.get('evidence_file'):
        ComplianceDocument.objects.create(
            task=task,
            title=request.POST.get('title', f"Evidence - {task.title}"),
            file=request.FILES['evidence_file'],
            uploaded_by=request.user,
            remarks=request.POST.get('remarks', '')
        )
        # Auto-mark task as completed upon evidence upload
        if 'complete_task' in request.POST:
            task.status = 'COMPLETED'
            task.completion_date = timezone.now().date()
            task.save()
            
        messages.success(request, "Compliance evidence successfully archived.")
    return redirect(request.META.get('HTTP_REFERER', 'compliances:dashboard'))

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
    Generates the grid logic for the Compliance Calendar with Year-Month boundary handling.
    """
    # 1. Determine Month/Year to display
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    fund_id = request.GET.get('fund')

    # 2. Setup Calendar Iterator
    cal = calendar.Calendar(firstweekday=6) # 6 = Sunday
    month_days = cal.monthdatescalendar(year, month)
    
    # 3. Fetch Tasks for this date range
    start_date = month_days[0][0]
    end_date = month_days[-1][-1]
    
    tasks_in_range = ComplianceTask.objects.filter(
        due_date__range=[start_date, end_date]
    )

    # Optional Fund Filtering
    if fund_id:
        tasks_in_range = tasks_in_range.filter(fund_id=fund_id)

    # 4. Build the Grid Data Structure
    calendar_data = []
    for week in month_days:
        for day in week:
            day_tasks = [t for t in tasks_in_range if t.due_date == day]
            calendar_data.append({
                'date': day,
                'is_today': (day == today),
                'is_current_month': (day.month == month),
                'tasks': day_tasks
            })

    # 5. Calculate Nav Links (Fixed logic to handle Year transitions)
    if month == 12:
        next_month_val, next_year_val = 1, year + 1
        prev_month_val, prev_year_val = 11, year
    elif month == 1:
        next_month_val, next_year_val = 2, year
        prev_month_val, prev_year_val = 12, year - 1
    else:
        next_month_val, next_year_val = month + 1, year
        prev_month_val, prev_year_val = month - 1, year

    fund_param = f"&fund={fund_id}" if fund_id else ""
    
    context = {
        'calendar_days': calendar_data,
        'current_month_date': date(year, month, 1),
        'prev_month_url': f"year={prev_year_val}&month={prev_month_val}{fund_param}",
        'next_month_url': f"year={next_year_val}&month={next_month_val}{fund_param}",
        'current_tab': 'calendar',
        'fund_id': fund_id,
    }
    
    return render(request, 'compliances/calendar.html', context)

from django.db.models import Count, Q

@login_required
def compliance_reports_view(request):
    """
    Enhanced Reporting View:
    1. Groups funds by Jurisdiction (SEBI/IFSCA).
    2. Flags 'At Risk' funds with overdue tasks.
    3. Optimized with Prefetching to prevent 'N+1' query issues.
    """
    # Use prefetch_related to get tasks efficiently for all funds at once
    funds = Fund.objects.all().prefetch_related('fund_compliance_tasks')
    
    total_tasks = ComplianceTask.objects.count()
    completed_tasks = ComplianceTask.objects.filter(status='COMPLETED').count()
    
    # We define 'Overdue' as any task past due_date that isn't completed
    today = timezone.now().date()
    overdue_qs = ComplianceTask.objects.filter(due_date__lt=today).exclude(status='COMPLETED')
    overdue_count = overdue_qs.count()
    
    reports_by_fund = []
    
    for fund in funds:
        # Calculate fund-specific stats
        fund_tasks = fund.fund_compliance_tasks.all()
        f_pending = fund_tasks.filter(due_date__lte=today).exclude(status='COMPLETED').count()
        f_completed = fund_tasks.filter(status='COMPLETED').count()
        
        reports_by_fund.append({
            'fund': fund,
            'jurisdiction': fund.get_jurisdiction_display(),
            'pending': f_pending,
            'completed': f_completed,
            # FLAG: If pending > 0, this fund is technically 'At Risk'
            'at_risk': f_pending > 0,
            'recent_tasks': fund_tasks.order_by('-due_date')[:5]
        })

    context = {
        'reports_by_fund': reports_by_fund,
        'total_tasks': total_tasks,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        'overdue_count': overdue_count,
        'today': today,
    }
    return render(request, 'compliances/reports.html', context)