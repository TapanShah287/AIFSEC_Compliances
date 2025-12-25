from django import forms
from .models import ComplianceTask, ComplianceDocument

# Common styling
STYLE = {'class': 'w-full p-2 border border-gray-300 rounded'}

class ComplianceTaskForm(forms.ModelForm):
    class Meta:
        model = ComplianceTask
        # FIXED: Changed 'topic' -> 'title' and 'notes' -> 'description'
        fields = ['title', 'jurisdiction', 'due_date', 'priority', 'description', 'assigned_to']
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all',
                'placeholder': 'e.g. Quarterly TDS Filing'
            }),
            'jurisdiction': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all',
                'placeholder': 'Add details about the filing requirements...'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'
            }),
        }


class ComplianceDocumentForm(forms.ModelForm):
    # Defined explicitly because it is NOT in the database model
    mark_complete = forms.BooleanField(
        required=False, 
        label="Mark Task as Completed",
        widget=forms.CheckboxInput(attrs={'class': 'ml-2 rounded text-indigo-600 focus:ring-indigo-500'})
    )

    class Meta:
        model = ComplianceDocument
        # Only include fields that actually exist in the model
        fields = ["file", "remarks"] 
        widgets = {
            "remarks": forms.Textarea(attrs={"rows": 2, "placeholder": "Optional remarks...", **STYLE}),
            "file": forms.FileInput(attrs={'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-violet-50 file:text-violet-700 hover:file:bg-violet-100'})
        }