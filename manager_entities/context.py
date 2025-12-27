from .models import EntityMembership

def active_manager_processor(request):
    """
    Makes 'active_manager', 'user_role', and 'available_managers' 
    available to every template (including base.html).
    """
    if not request.user.is_authenticated:
        return {}

    # 1. Fetch all memberships for this user to populate the switcher dropdown
    # Using select_related('entity') improves performance (1 query instead of many)
    memberships = EntityMembership.objects.filter(user=request.user).select_related('entity')
    
    # 2. Identify the Active Entity from the Session
    active_id = request.session.get('active_entity_id')
    active_membership = None

    if active_id:
        active_membership = memberships.filter(entity_id=active_id).first()
    
    # 3. Fallback: If no session exists, pick the first entity they have access to
    if not active_membership and memberships.exists():
        active_membership = memberships.first()
        request.session['active_entity_id'] = active_membership.entity.id

    # 4. Return data to the Global Template Context
    return {
        'active_manager': active_membership.entity if active_membership else None,
        'user_role': active_membership.role if active_membership else None,
        'available_managers': [m.entity for m in memberships]
    }