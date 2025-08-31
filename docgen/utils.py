import io, os, shutil, subprocess
from django.core.files.base import ContentFile
def render_docx_from_template(template_path, context):
    try:
        from docxtpl import DocxTemplate
    except ModuleNotFoundError as e:
        raise RuntimeError("docxtpl is not installed. Please `pip install docxtpl`.") from e
    doc = DocxTemplate(template_path); doc.render(context)
    out = io.BytesIO(); doc.save(out); out.seek(0); return out.getvalue()
def render_pdf_from_docx(docx_path, pdf_path):
    soffice = shutil.which("libreoffice") or shutil.which("soffice")
    if soffice:
        outdir = os.path.dirname(pdf_path); os.makedirs(outdir, exist_ok=True)
        cmd = [soffice, "--headless", "--convert-to", "pdf", "--outdir", outdir, docx_path]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        produced = os.path.join(outdir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
        if produced != pdf_path and os.path.exists(produced): os.replace(produced, pdf_path)
        return pdf_path
    try:
        from docx2pdf import convert
        convert(docx_path, pdf_path); return pdf_path
    except Exception as e:
        raise RuntimeError("PDF conversion failed. Install LibreOffice on server or docx2pdf on desktop.") from e
def build_purchase_context(purchase, extras=None):
    extras = extras or {}; fund=purchase.fund; company=purchase.investee_company
    ctx = {"fund_name": fund.name, "fund_category": getattr(fund,"get_category_display",lambda: getattr(fund,"category",""))(), "fund_manager": getattr(getattr(fund,"manager",None),"name",""), "investee_company": getattr(company,"name",""), "units": float(purchase.number_of_shares), "price_per_unit": float(purchase.price_per_share), "amount": float(purchase.number_of_shares * purchase.price_per_share), "purchase_date": purchase.purchase_date.strftime("%d-%b-%Y") if purchase.purchase_date else ""}
    ctx.update(extras or {}); return ctx
def build_redemption_context(redemption, extras=None):
    extras = extras or {}; fund=redemption.fund; purchase=redemption.purchase_transaction; company=purchase.investee_company if purchase else None
    ctx = {"fund_name": fund.name, "investee_company": getattr(company,"name",""), "units": float(redemption.number_of_shares), "price_per_unit": float(redemption.price_per_share), "amount": float(redemption.number_of_shares * redemption.price_per_share), "redemption_date": redemption.redemption_date.strftime("%d-%b-%Y") if redemption.redemption_date else ""}
    ctx.update(extras or {}); return ctx
