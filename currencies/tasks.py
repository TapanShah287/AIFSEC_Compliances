from django.tasks import task
from django.core.management import call_command

@task()
def auto_update_fx_rates():
    call_command('update_rates')