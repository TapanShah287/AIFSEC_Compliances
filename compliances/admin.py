from django.contrib import admin
from .models import ComplianceTask, ComplianceDocument
admin.site.register(ComplianceTask)
admin.site.register(ComplianceDocument)
