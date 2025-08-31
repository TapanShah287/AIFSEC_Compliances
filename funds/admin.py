from django.contrib import admin
from .models import Fund, Document, ActivityLog
admin.site.register(Fund)
admin.site.register(Document)
admin.site.register(ActivityLog)
