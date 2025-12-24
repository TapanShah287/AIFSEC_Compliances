import io
from django.core.files.base import ContentFile
from docxtpl import DocxTemplate

def render_docx(template_path, context):
    """
    Renders a DOCX template with the given context dict.
    Returns: BytesIO object of the generated file.
    """
    doc = DocxTemplate(template_path)
    doc.render(context)
    
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

def get_investor_context(investor):
    """
    Flattens Investor model into a dictionary for templates.
    e.g., {{ investor.name }}, {{ investor.pan }}
    """
    return {
        'id': investor.id,
        'name': investor.name,
        'type': investor.get_investor_type_display(),
        'pan': investor.pan or "N/A",
        'email': investor.email,
        'phone': investor.phone or "",
        'address': "Address Placeholder", # Extend model if needed
        'today': timezone.now().strftime("%d-%b-%Y")
    }

def get_commitment_context(commitment):
    """
    Flattens a Commitment object.
    """
    from django.utils import timezone
    return {
        'ref_no': f"COM-{commitment.id}",
        'date': commitment.commitment_date.strftime("%d-%b-%Y"),
        'amount': f"{commitment.amount_committed:,.2f}",
        'amount_words': "Rupees ... Only", # You can add a number-to-words lib here
        'fund_name': commitment.fund.name,
        'investor': get_investor_context(commitment.investor)
    }