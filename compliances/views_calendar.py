import calendar as cal
from datetime import date
from django.shortcuts import render
from django.utils.timezone import localdate
from .models import ComplianceTask
def calendar_view(request):
    today = localdate()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    month_cal = cal.Calendar(firstweekday=0).monthdatescalendar(year, month)
    start = date(year, month, 1)
    end = date(year+1, 1, 1) if month == 12 else date(year, month+1, 1)
    tasks = ComplianceTask.objects.select_related("fund").filter(due_date__gte=start, due_date__lt=end)
    tasks_by_day = {}
    for t in tasks:
        tasks_by_day.setdefault(t.due_date, []).append(t)
    context = {"year": year, "month": month, "month_name": start.strftime("%B"), "weeks": month_cal, "tasks_by_day": tasks_by_day}
    return render(request, "compliances/calendar.html", context)
