from django.contrib import admin
from .models import ManagerEntity, EntityMembership

@admin.register(ManagerEntity)
class ManagerEntityAdmin(admin.ModelAdmin):
    list_display = ("name", "sebi_manager_registration_no", "pan", "gstin")
    search_fields = ("name", "sebi_manager_registration_no", "pan", "gstin")

@admin.register(EntityMembership)
class EntityMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "entity", "role")
    list_filter = ("entity", "role")
    search_fields = ("user__username", "entity__name")