from django.contrib import admin
from .models import DocumentTemplate, GeneratedDocument

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'type', 'created_at')
    list_filter = ('type',)
    search_fields = ('name', 'code')

@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ('template', 'fund', 'investor', 'created_at')
    readonly_fields = ('created_at', 'generated_file')