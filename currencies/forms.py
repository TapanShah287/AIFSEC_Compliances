from django import forms
from .models import Currency, ExchangeRate

class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ['code', 'symbol', 'name', 'is_base']
        widgets = {
            'code': forms.TextInput(attrs={
                'placeholder': 'e.g. USD',
                'class': 'w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold text-slate-700 focus:ring-2 focus:ring-indigo-500 outline-none transition-all'
            }),
            'symbol': forms.TextInput(attrs={
                'placeholder': 'e.g. $',
                'class': 'w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold text-slate-700 focus:ring-2 focus:ring-indigo-500 outline-none transition-all'
            }),
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g. US Dollar',
                'class': 'w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold text-slate-700 focus:ring-2 focus:ring-indigo-500 outline-none transition-all'
            }),
            'is_base': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500'
            }),
        }

class ExchangeRateForm(forms.ModelForm):
    class Meta:
        model = ExchangeRate
        fields = ['currency', 'date', 'rate']
        widgets = {
            'currency': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-100 border border-slate-200 rounded-xl text-sm font-bold text-slate-500 outline-none appearance-none cursor-not-allowed',
                'readonly': 'readonly',
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 focus:ring-2 focus:ring-indigo-500 outline-none transition-all'
            }),
            'rate': forms.NumberInput(attrs={
                'step': '0.000001',
                'placeholder': '0.000000',
                'class': 'w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 focus:ring-2 focus:ring-indigo-500 outline-none transition-all'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We lock the currency field if we are updating a specific one
        if self.instance and self.instance.pk:
            self.fields['currency'].disabled = True