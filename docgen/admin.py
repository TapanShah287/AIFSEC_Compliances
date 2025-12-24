from django.contrib import admin
from .models import DocumentTemplate, GeneratedDocument

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')
    help_text = "Upload .docx files with jinja2 tags like {{ investor.name }}"

@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'template', 'created_at', 'investor', 'fund')
    list_filter = ('template', 'created_at')
    readonly_fields = ('created_at', 'generated_file')