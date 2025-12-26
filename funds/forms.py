from django import forms
from .models import Fund, Document, StewardshipEngagement, NavSnapshot
from investors.models import Investor
from investee_companies.models import InvesteeCompany

# UI Helper
INPUT_STYLE = 'w-full px-4 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all'

class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        # Ensure these match your models.py attributes exactly
        fields = [
            'name', 
            'sebi_registration_number', 
            'category', 
            'date_of_inception', 
            'corpus', 
            'currency', 
            'manager_entity',
            'scheme_type',
            'jurisdiction'
        ]
        
        # Adding widgets ensures they are styled as inputs/dates rather than plain text
        widgets = {
            'date_of_inception': forms.DateInput(attrs={'type': 'date'}),
            'corpus': forms.NumberInput(attrs={'placeholder': 'Enter amount'}),
            'sebi_registration_number': forms.TextInput(attrs={'placeholder': 'SEBI/Reg No.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Automatically apply the styling class to all fields to save time
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 transition-all'
            })

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['investor', 'title', 'file', 'is_demat_advice']
        widgets = {
            'investor': forms.Select(attrs={'class': INPUT_STYLE}),
            'title': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Document Title'}),
            'file': forms.FileInput(attrs={'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
            'is_demat_advice': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded text-indigo-600 focus:ring-indigo-500'}),
        }

class StewardshipEngagementForm(forms.ModelForm):
    class Meta:
        model = StewardshipEngagement
        fields = ['investee_company', 'engagement_date', 'topic', 'description', 'status']
        widgets = {
            'investee_company': forms.Select(attrs={'class': INPUT_STYLE}),
            'engagement_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'topic': forms.TextInput(attrs={'class': INPUT_STYLE}),
            'description': forms.Textarea(attrs={'class': INPUT_STYLE, 'rows': 3}),
            'status': forms.Select(attrs={'class': INPUT_STYLE}),
        }

class NavSnapshotForm(forms.ModelForm):
    class Meta:
        model = NavSnapshot
        fields = ['as_on_date', 'nav_per_unit', 'aum', 'units_outstanding', 'is_first_close_nav']
        widgets = {
            'as_on_date': forms.DateInput(attrs={'class': INPUT_STYLE, 'type': 'date'}),
            'nav_per_unit': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.0001'}),
            'aum': forms.NumberInput(attrs={'class': INPUT_STYLE}),
            'units_outstanding': forms.NumberInput(attrs={'class': INPUT_STYLE, 'step': '0.0001'}),
            'is_first_close_nav': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded text-indigo-600'}),
        }