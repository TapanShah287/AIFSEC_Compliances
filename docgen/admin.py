
from django.contrib import admin
from .models import DocumentTemplate, GeneratedDocument

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "has_sample")
    search_fields = ("code", "name", "description")
    readonly_fields = ()
    def has_sample(self, obj):
        return bool(obj.sample_context)
    has_sample.boolean = True
    has_sample.short_description = "Sample Context"

@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "template", "created_at", "has_pdf")
    list_filter = ("template",)
    search_fields = ("template__code", "template__name", "file")
    readonly_fields = ("created_at",)
    def has_pdf(self, obj):
        return bool(obj.pdf_file)
    has_pdf.boolean = True
    has_pdf.short_description = "PDF Generated"
