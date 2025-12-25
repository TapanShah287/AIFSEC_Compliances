from rest_framework import serializers
from .models import DocumentTemplate, GeneratedDocument

class DocumentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTemplate
        fields = '__all__'

class GeneratedDocumentSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    file_url = serializers.FileField(source='generated_file', read_only=True)

    class Meta:
        model = GeneratedDocument
        fields = '__all__'