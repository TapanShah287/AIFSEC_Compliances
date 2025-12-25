from django import forms
from .models import DocumentTemplate

class DocumentTemplateForm(forms.ModelForm):
    """
    Form for Admin/Managers to upload new DOCX or HTML templates.
    """
    class Meta:
        model = DocumentTemplate
        fields = ['name', 'code', 'type', 'file', 'html_content', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'e.g. Capital Call Notice v1'}),
            'code': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg uppercase', 'placeholder': 'CAPITAL_CALL'}),
            'type': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'file': forms.FileInput(attrs={'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
            'html_content': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg font-mono text-xs', 'rows': 6, 'placeholder': 'Paste HTML here for PDF generation...'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'rows': 2}),
        }

class GenerateNoticeForm(forms.Form):
    """
    Form to select which Transaction + Which Template to use.
    """
    transaction_type = forms.ChoiceField(choices=[
        ('CALL', 'Capital Call'), 
        ('DIST', 'Distribution')
    ], widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}))
    
    transaction_id = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'Enter Transaction ID'})
    )
    
    template = forms.ModelChoiceField(
        queryset=DocumentTemplate.objects.all(),
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'})
    )