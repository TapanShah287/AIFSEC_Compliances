# manager_entities/forms.py
from django import forms
from .models import ManagerEntity

# Common styling attributes for form widgets
form_widget_attrs = {
    'class': 'w-full p-2 border border-slate-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500'
}

class ManagerForm(forms.ModelForm):
    class Meta:
        model = ManagerEntity
        fields = [
            "name", "sebi_manager_registration_no", "cin", "pan", 
            "gstin", "registered_address", "contact_email", "contact_phone"
        ]
        widgets = {
            'name': forms.TextInput(attrs=form_widget_attrs),
            'sebi_manager_registration_no': forms.TextInput(attrs=form_widget_attrs),
            'cin': forms.TextInput(attrs=form_widget_attrs),
            'pan': forms.TextInput(attrs=form_widget_attrs),
            'gstin': forms.TextInput(attrs=form_widget_attrs),
            'registered_address': forms.Textarea(attrs={'rows': 3, **form_widget_attrs}),
            'contact_email': forms.EmailInput(attrs=form_widget_attrs),
            'contact_phone': forms.TextInput(attrs=form_widget_attrs),
        }