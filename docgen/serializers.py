from rest_framework import serializers
from .models import DocumentTemplate, GeneratedDocument

class DocumentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTemplate
        fields = ['id', 'name', 'code', 'description']

class GeneratedDocumentSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    file_url = serializers.FileField(source='generated_file', read_only=True)

    class Meta:
        model = GeneratedDocument
        fields = ['id', 'template_name', 'file_url', 'created_at']