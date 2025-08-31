from django.contrib import admin
from .models import ManagerEntity
@admin.register(ManagerEntity)
class ManagerEntityAdmin(admin.ModelAdmin):
    list_display = ("name", "sebi_manager_registration_no", "pan", "gstin")
    search_fields = ("name", "sebi_manager_registration_no", "pan", "gstin")
