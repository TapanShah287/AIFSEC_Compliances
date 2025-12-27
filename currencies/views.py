from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Currency, ExchangeRate
from .forms import CurrencyForm, ExchangeRateForm
from django.utils import timezone
from django.db.models import OuterRef, Subquery



@login_required
def currency_list(request):
    currencies = Currency.objects.all().order_by('-is_base', 'code')
    
    # Advanced trick: Get the absolute latest rate for each currency in one go
    latest_rate_query = ExchangeRate.objects.filter(
        currency=OuterRef('pk')
    ).order_by('-date', '-id') # Latest date, then latest entry
    
    currencies = currencies.annotate(
        current_rate=Subquery(latest_rate_query.values('rate')[:1]),
        last_updated=Subquery(latest_rate_query.values('date')[:1])
    )

    return render(request, 'currencies/currency_list.html', {
        'currencies': currencies,
    })

@login_required
def currency_create(request):
    if request.method == "POST":
        form = CurrencyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Currency added successfully.")
            return redirect('currencies:currency_list')
    else:
        form = CurrencyForm()
    return render(request, 'currencies/currency_form.html', {'form': form})

@login_required
def currency_edit(request, pk):
    currency = get_object_or_404(Currency, pk=pk)
    if request.method == "POST":
        form = CurrencyForm(request.POST, instance=currency)
        if form.is_valid():
            form.save()
            messages.success(request, "Currency updated.")
            return redirect('currencies:currency_list')
    else:
        form = CurrencyForm(instance=currency)
    return render(request, 'currencies/currency_form.html', {'form': form})

@login_required
def exchange_rate_update(request, currency_pk):
    # 1. Get the specific currency (e.g., USD)
    currency = get_object_or_404(Currency, pk=currency_pk)
    
    # 2. Check if a rate already exists for today to edit it
    today = timezone.now().date()
    instance = ExchangeRate.objects.filter(currency=currency, date=today).first()

    if request.method == "POST":
        # Pass both POST data and the instance (if it exists) to the form
        form = ExchangeRateForm(request.POST, instance=instance)
        if form.is_valid():
            new_rate = form.save(commit=False)
            new_rate.currency = currency  # Force link to this currency
            new_rate.save()
            return redirect('currencies:currency_list')
    else:
        # GET request: Create the form with the instance and initial data
        # 'form' is the key the template looks for
        form = ExchangeRateForm(instance=instance, initial={
            'currency': currency,
            'date': today
        })

    # CRITICAL: Ensure the dictionary key is 'form'
    return render(request, 'currencies/rate_form.html', {
        'form': form, 
        'currency': currency
    })

@login_required
def exchange_rate_history(request):
    """View to show the historical trend of all currency rates."""
    rates = ExchangeRate.objects.select_related('currency').all().order_by('-date', 'currency__code')
    
    return render(request, 'currencies/rate_history.html', {
        'rates': rates
    })

@login_required
def manual_rate_sync(request):
    from django.core.management import call_command
    try:
        call_command('update_rates')
        messages.success(request, "Exchange rates synchronized with global markets.")
    except Exception as e:
        messages.error(request, f"Sync failed: {str(e)}")
    return redirect('currencies:currency_list')