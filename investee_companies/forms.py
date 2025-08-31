# investee_companies/forms.py
from django import forms
from datetime import date
from django.forms import inlineformset_factory
from .models import (
    InvesteeCompany, ValuationReport, ShareValuation,
    CorporateAction, CompanyFinancials, Shareholding
)

class InvesteeCompanyForm(forms.ModelForm):
    class Meta:
        model = InvesteeCompany
        fields = ['name', 'cin', 'incorporation_date']
        widgets = {
            'incorporation_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ValuationReportForm(forms.ModelForm):
    class Meta:
        model = ValuationReport
        fields = ['valuation_date', 'report_file']
        widgets = {
            'valuation_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the report file field not required
        self.fields['report_file'].required = False


class ShareValuationForm(forms.ModelForm):
    class Meta:
        model = ShareValuation
        fields = ["valuation_report", "share_capital", "per_share_value"]
        widgets = {
            "per_share_value": forms.NumberInput(attrs={"step": "0.01", "min": "0"})
        }
        labels = {
            "valuation_report": "Valuation report",
            "share_capital": "Share capital (class)",
            "per_share_value": "Per share value",
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)  # passed in from the view
        super().__init__(*args, **kwargs)

        if company is not None:
            # ✅ filter by the correct FK name on both models
            self.fields["valuation_report"].queryset = (
                ValuationReport.objects.filter(investee_company=company).order_by("-valuation_date")
            )
            self.fields["share_capital"].queryset = (
                Shareholding.objects.filter(investee_company=company).order_by("share_type")
            )

        # Optional: basic styling
        for name in ("valuation_report", "share_capital", "per_share_value"):
            self.fields[name].widget.attrs.setdefault("class", "w-full")

class CorporateActionForm(forms.ModelForm):
    class Meta:
        model = CorporateAction
        fields = ['action_type', 'action_date', 'details', 'share_type', 'ratio', 'from_share_type', 'to_share_type', 'number_of_shares_converted']
        widgets = {
            'action_date': forms.DateInput(attrs={'type': 'date'}),
        }

class CompanyFinancialsForm(forms.ModelForm):
    class Meta:
        model = CompanyFinancials
        fields = ['period_date', 'revenue', 'ebitda', 'net_income']
        widgets = {
            'period_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ShareholdingForm(forms.ModelForm):
    class Meta:
        model = Shareholding
        fields = ['investee_company','investor','holder_name','share_type','number_of_shares','face_value','acquisition_price','acquisition_date','certificate_or_demat']
        widgets = {
            'acquisition_date': forms.DateInput(attrs={'type':'date'}),
        }


class ShareholdingPatternForm(forms.ModelForm):
    """
    Minimal company shareholding pattern entry:
    - Who holds
    - What class
    - How many shares
    """
    class Meta:
        model = Shareholding
        fields = [
            "investee_company",   # FK (pre-filled by the view)
            "investor",           # optional FK to an Investor
            "holder_name",        # fallback text if no investor FK
            "share_type",         # Equity / Preference / ...
            "number_of_shares",   # integer/decimal as per model
        ]
        widgets = {
            "investee_company": forms.Select(attrs={"class": "hidden"}),  # we’ll set instance in the view
        }

    def clean(self):
        data = super().clean()
        # ensure at least one of investor or holder_name is provided
        if not data.get("investor") and not data.get("holder_name"):
            self.add_error("holder_name", "Provide either an Investor or a Holder name.")
        return data