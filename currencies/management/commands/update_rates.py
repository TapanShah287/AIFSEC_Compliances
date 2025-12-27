import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from currencies.models import Currency, ExchangeRate

class Command(BaseCommand):
    help = 'Fetches latest exchange rates from Frankfurter API'

    def handle(self, *args, **kwargs):
        # 1. Identify your Base Currency (e.g., INR)
        base_currency = Currency.objects.filter(is_base=True).first()
        if not base_currency:
            self.stdout.write(self.style.ERROR('No Base Currency defined in system.'))
            return

        # 2. Identify all target currencies we need rates for
        target_currencies = Currency.objects.filter(is_base=False)
        symbols = ",".join([c.code for c in target_currencies])

        if not symbols:
            self.stdout.write(self.style.WARNING('No target currencies found to update.'))
            return

        # 3. Call the API
        url = f"https://api.frankfurter.dev/v1/latest?base={base_currency.code}&symbols={symbols}"
        
        try:
            response = requests.get(url)
            data = response.json()
            rates = data.get('rates', {})

            for code, rate_value in rates.items():
                currency = target_currencies.get(code=code)
                
                # We store 1 unit of foreign currency = X units of Base
                # API gives 1 Base = Y foreign. So we invert it: 1/Y
                actual_rate = 1 / float(rate_value)

                ExchangeRate.objects.update_or_create(
                    currency=currency,
                    date=timezone.now().date(),
                    defaults={'rate': actual_rate}
                )
                self.stdout.write(self.style.SUCCESS(f'Updated {code}: {actual_rate}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'API Error: {str(e)}'))