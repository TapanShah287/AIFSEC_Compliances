from django.apps import AppConfig

class FundsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'funds'

    def ready(self):
        import funds.signals  # This "wakes up" the listener
        
class CompliancesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'compliances'
