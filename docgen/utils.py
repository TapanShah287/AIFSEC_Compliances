import io
from django.utils import timezone
from django.template import Template, Context

def render_to_pdf(template_html, context_dict):
    """
    Renders HTML string to PDF bytes using xhtml2pdf.
    Safe import ensures server starts even if library is missing.
    """
    try:
        from xhtml2pdf import pisa
    except ImportError:
        raise ImportError("Please run: pip install xhtml2pdf")

    template = Template(template_html)
    context = Context(context_dict)
    html = template.render(context)
    
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        result.seek(0)
        return result
    return None

def render_docx(template_path, context_dict):
    """
    Renders DOCX template to bytes using docxtpl.
    """
    try:
        from docxtpl import DocxTemplate
    except ImportError:
        raise ImportError("Please run: pip install docxtpl")

    doc = DocxTemplate(template_path)
    doc.render(context_dict)
    
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

def get_transaction_context(txn):
    """
    Extracts data from CapitalCall/Distribution models for the template.
    """
    return {
        'ref_no': getattr(txn, 'reference', f"TXN-{txn.id}"),
        'date': timezone.now().strftime("%d-%b-%Y"),
        'fund_name': txn.fund.name,
        'investor_name': txn.investor.name,
        'investor_pan': getattr(txn.investor, 'pan', 'N/A'),
        'amount': f"{getattr(txn, 'amount_called', getattr(txn, 'gross_amount', 0)):,.2f}",
        'currency': txn.fund.currency.symbol,
    }