from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.base import ContentFile
from pathlib import Path
from docxtpl import DocxTemplate
import io, datetime

from .models import DocumentTemplate, GeneratedDocument
from transactions.models import InvestorCommitment
from funds.models import Fund
from investors.models import Investor

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_kyc_for_investor(request, investor_id: int):
    investor = get_object_or_404(Investor, pk=investor_id)

    # 1) Find or load a DOCX template
    # Prefer DB template if present (admin upload with code='KYC_FORM')
    tpl_obj = DocumentTemplate.objects.filter(code="KYC_FORM").first()

    if tpl_obj and tpl_obj.file:
        tpl_path = tpl_obj.file.path
    else:
        # fallback to project file: aif_compliance/docgen_templates/kyc_form.docx
        fallback = Path(settings.BASE_DIR, "docgen_templates", "kyc_form.docx")
        if not fallback.exists():
            return Response({"detail": "KYC template missing. Upload one in Admin (DocumentTemplate code='KYC_FORM') or put docgen_templates/kyc_form.docx."}, status=400)
        tpl_path = str(fallback)

    # 2) Build context
    ctx = {
        "name": investor.name,
        "email": getattr(investor, "email", ""),
        "phone": getattr(investor, "phone", ""),
        "address": getattr(investor, "address", ""),
        "kyc_status": getattr(investor, "kyc_status", "PENDING"),
        "generated_on": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    # 3) Render DOCX
    tpl = DocxTemplate(tpl_path)
    tpl.render(ctx)
    buf = io.BytesIO()
    tpl.save(buf)
    buf.seek(0)

    # 4) Persist GeneratedDocument
    gen = GeneratedDocument(template=tpl_obj if tpl_obj else None, investor=investor)
    filename = f"kyc_{investor_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    gen.file.save(filename, ContentFile(buf.read()), save=True)

    # Optional: convert to PDF later if you have wkhtmltopdf/Office installed
    # gen.pdf_file.save(...)

    file_url = gen.file.url if hasattr(gen.file, "url") else f"{settings.MEDIA_URL}{gen.file.name}"
    return Response({"id": gen.id, "file_url": file_url})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_commitment_agreement(request, commitment_id: int):
    # 1) Load the commitment with related fund and investor
    commitment = get_object_or_404(
        InvestorCommitment.objects.select_related("fund", "investor"),
        pk=commitment_id
    )
    fund = commitment.fund
    investor = commitment.investor

    # 2) Pick template from DB if uploaded, else fallback file
    tpl_obj = DocumentTemplate.objects.filter(code="COMMITMENT_AGREEMENT").first()
    if tpl_obj and tpl_obj.file:
        tpl_path = tpl_obj.file.path
    else:
        tpl_path = str(Path(settings.BASE_DIR) / "docgen_templates" / "commitment_agreement.docx")
        if not Path(tpl_path).exists():
            return Response({"detail": "Commitment template missing."}, status=400)

    # 3) Build context for rendering
    context = {
        "fund_name": fund.name,
        "sebi_reg": fund.sebi_registration_number,
        "investor_name": investor.name,
        "commitment_date": commitment.commitment_date.strftime("%Y-%m-%d"),
        "amount_committed": f"{commitment.amount_committed:,.2f}",
    }

    # 4) Render DOCX using docxtpl
    tpl = DocxTemplate(tpl_path)
    tpl.render(context)
    buf = io.BytesIO()
    tpl.save(buf)
    buf.seek(0)

    # 5) Persist GeneratedDocument
    filename = f"commitment_{commitment.pk}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    gen = GeneratedDocument.objects.create(
        template=tpl_obj if tpl_obj else None,
        fund=fund,
        investor=investor,
        context=context,
    )
    gen.file.save(filename, ContentFile(buf.read()), save=True)

    # 6) Return file URL
    file_url = gen.file.url if hasattr(gen.file, "url") else f"{settings.MEDIA_URL}{gen.file.name}"
    return Response({
        "id": gen.id,
        "file_url": file_url,
        "context": context,
    })