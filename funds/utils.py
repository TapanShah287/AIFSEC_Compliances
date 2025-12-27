# funds/utils.py
from manager_entities.models import ManagerEntity

def get_current_manager_entity(request):
    active_id = request.session.get('active_entity_id')
    if active_id:
        return ManagerEntity.objects.filter(id=active_id).first()
    
    # Fallback to the first associated entity if session is empty
    first_membership = request.user.memberships.first()
    if first_membership:
        request.session['active_entity_id'] = first_membership.entity.id
        return first_membership.entity
    return None

class ManagerEntityMixin:
    """Mixin to auto-provide manager_entity to all views."""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['manager_entity'] = get_current_manager_entity(self.request)
        return context
