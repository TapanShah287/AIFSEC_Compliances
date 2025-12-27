from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.models import User

from .models import ManagerEntity, EntityMembership
from .forms import ManagerForm, PortalUserCreationForm

@login_required
def switch_manager(request, pk):
    # Security: Verify user has access to this specific entity
    if request.user.memberships.filter(entity_id=pk).exists():
        request.session['active_entity_id'] = pk
        messages.success(request, f"Context switched to {ManagerEntity.objects.get(pk=pk).name}")
    else:
        messages.error(request, "Access denied to this entity.")
    
    # This ensures you return to the page you were on, or dashboard if referer is missing
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:home'))

@login_required
def manager_list(request):
    """
    Shows only the entities where the user has an active membership.
    """
    q = (request.GET.get("q") or "").strip()
    
    # Filter: User should only see entities they belong to
    qs = ManagerEntity.objects.filter(members__user=request.user)
    
    if q:
        qs = qs.filter(
            Q(name__icontains=q) | 
            Q(sebi_manager_registration_no__icontains=q) | 
            Q(pan__icontains=q)
        )
    
    page = Paginator(qs.order_by("name"), 25).get_page(request.GET.get("page"))
    return render(request, "manager_entities/manager_list.html", {
        "managers": page.object_list, 
        "page_obj": page, 
        "is_paginated": page.paginator.num_pages > 1
    })

@login_required
def manager_detail(request, pk):
    # Security: Ensure user is a member of this specific entity
    obj = get_object_or_404(ManagerEntity, pk=pk, members__user=request.user)
    return render(request, "manager_entities/manager_detail.html", {"manager": obj})

@login_required
def manager_create(request):
    if request.method == "POST":
        form = ManagerForm(request.POST)
        if form.is_valid():
            obj = form.save()
            
            # ATTACH USER TO ENTITY AUTOMATICALLY
            EntityMembership.objects.create(
                user=request.user,
                entity=obj,
                role='ADMIN'
            )
            
            # Set as active session immediately
            request.session['active_entity_id'] = obj.pk
            
            return redirect(reverse("manager_entities:manager_detail", args=[obj.pk]))
    else:
        form = ManagerForm()
    return render(request, "manager_entities/manager_form.html", {"form": form})

@login_required
def manager_update(request, pk):
    # Security: Only 'ADMIN' role should be able to update entity details
    membership = get_object_or_404(EntityMembership, entity_id=pk, user=request.user)
    if membership.role != 'ADMIN':
        messages.error(request, "Only Admins can update entity details.")
        return redirect('manager_entities:manager_detail', pk=pk)

    obj = get_object_or_404(ManagerEntity, pk=pk)
    if request.method == "POST":
        form = ManagerForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Entity details updated.")
            return redirect(reverse("manager_entities:manager_detail", args=[obj.pk]))
    else:
        form = ManagerForm(instance=obj)
    return render(request, "manager_entities/manager_form.html", {"form": form, "manager": obj})

@login_required
def settings_hub(request):
    # 1. Get the active entity ID from the session
    active_id = request.session.get('active_entity_id')
    
    # 2. Check if the user has an ADMIN role for this active entity
    is_admin = EntityMembership.objects.filter(
        user=request.user, 
        entity_id=active_id, 
        role='ADMIN'
    ).exists()
    
    # 3. Security enforcement
    if not is_admin:
        messages.error(request, "Access Denied. You need Administrative privileges for this entity.")
        return redirect('manager_entities:manager_list')
        
    return render(request, "manager_entities/settings_hub.html")
    
# --- Team Management Views ---

@login_required
def team_list(request, entity_pk):
    entity = get_object_or_404(ManagerEntity, pk=entity_pk)
    
    # Get all current memberships
    memberships = EntityMembership.objects.filter(entity=entity).select_related('user')
    
    # Get IDs of people who are ALREADY members
    current_ids = memberships.values_list('user_id', flat=True)
    
    # Get system users who are NOT in this team yet
    all_users = User.objects.exclude(id__in=current_ids).order_by('username')
    
    return render(request, "manager_entities/team_list.html", {
        "entity": entity,
        "memberships": memberships,
        "all_users": all_users,
    })

@login_required
def team_member_add(request, entity_pk):
    """Adds a user to the entity's team by their username."""
    entity = get_object_or_404(ManagerEntity, pk=entity_pk)
    
    if request.method == "POST":
        username = request.POST.get('username')
        role = request.POST.get('role')
        
        try:
            user_to_add = User.objects.get(username=username)
            # Create or update membership
            membership, created = EntityMembership.objects.update_or_create(
                user=user_to_add,
                entity=entity,
                defaults={'role': role}
            )
            messages.success(request, f"User {username} added as {role}.")
        except User.DoesNotExist:
            messages.error(request, f"User '{username}' not found in the system.")
            
        return redirect('manager_entities:team_list', entity_pk=entity_pk)

    return render(request, "manager_entities/team_member_form.html", {"entity": entity})

@login_required
def team_member_remove(request, pk):
    """Removes a user from an entity."""
    membership = get_object_or_404(EntityMembership, pk=pk)
    entity_id = membership.entity.id
    
    # Logic: Don't let users delete themselves if they are the last admin
    membership.delete()
    messages.success(request, "Team member removed.")
    return redirect('manager_entities:team_list', entity_pk=entity_id)

def check_admin_access(request):
    """Helper to check if the user is an ADMIN for the active entity."""
    active_id = request.session.get('active_entity_id')
    return EntityMembership.objects.filter(
        user=request.user, 
        entity_id=active_id, 
        role='ADMIN'
    ).exists()

@login_required
def settings_hub(request):
    if not check_admin_access(request):
        messages.error(request, "Access Denied: Administrative privileges required.")
        return redirect('manager_entities:manager_list')
    return render(request, "manager_entities/settings_hub.html")

@login_required
def user_create(request):
    if not check_admin_access(request):
        return redirect('manager_entities:manager_list')

    if request.method == "POST":
        form = PortalUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} created. You can now add them to an entity team.")
            return redirect('manager_entities:settings_hub')
    else:
        form = PortalUserCreationForm()
    
    return render(request, "manager_entities/user_form.html", {"form": form})