# funds/utils.py
from manager_entities.models import ManagerEntity

def get_current_manager_entity(request):
    """Returns the ManagerEntity for the current environment."""
    # For now: first manager. Later: per-user mapping
    return ManagerEntity.objects.first()

class ManagerEntityMixin:
    """Mixin to auto-provide manager_entity to all views."""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['manager_entity'] = get_current_manager_entity(self.request)
        return context
