from django import forms
from .models import ComplianceTask, ComplianceDocument
from funds.models import Fund

# Common styling
STYLE = {'class': 'w-full p-2 border border-gray-300 rounded'}

class ComplianceTaskForm(forms.ModelForm):
    class Meta:
        model = ComplianceTask
        fields = ['fund', 'title', 'topic', 'jurisdiction', 'due_date', 'priority', 'status', 'description', 'assigned_to']
        
        widgets = {
            'fund': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'
            }),
            'topic': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'
            }),
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
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If we are editing an existing task
        if self.instance and self.instance.pk:
            # Topic must be here because it is missing from the Detail View HTML
            optional_fields = ['fund', 'title', 'jurisdiction', 'topic', 'priority']
            
            for field in optional_fields:
                if field in self.fields:
                    self.fields[field].required = False
            
            if 'fund' in self.fields:
                self.fields['fund'].disabled = True

        # Mapping for the 'Create' view logic
        self.fields['fund'].queryset = Fund.objects.all().order_by('name')
        fund_map = {f.id: f.jurisdiction for f in self.fields['fund'].queryset}
        self.fields['fund'].widget.attrs['data-jurisdiction-map'] = fund_map


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