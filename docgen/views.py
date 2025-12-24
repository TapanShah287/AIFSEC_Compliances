from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DocumentTemplate, GeneratedDocument
from .serializers import DocumentTemplateSerializer, GeneratedDocumentSerializer
from .utils import render_docx, get_investor_context, get_commitment_context

# Import models from other apps (Safe imports)
from investors.models import Investor
from transactions.models import InvestorCommitment

class DocumentTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List available templates so the frontend knows what codes to send.
    """
    queryset = DocumentTemplate.objects.all()
    serializer_class = DocumentTemplateSerializer
    permission_classes = [IsAuthenticated]

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_kyc_document(request, investor_id):
    """
    Generates a KYC form for a specific investor.
    Requires a DocumentTemplate with code='KYC_FORM' to exist.
    """
    investor = get_object_or_404(Investor, pk=investor_id)
    template = DocumentTemplate.objects.filter(code='KYC_FORM').first()

    if not template:
        return Response({"error": "Template with code 'KYC_FORM' not found."}, status=404)

    # 1. Build Context
    context = {'investor': get_investor_context(investor)}

    # 2. Render
    try:
        file_stream = render_docx(template.file.path, context)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    # 3. Save Record
    filename = f"KYC_{investor.pan}_{investor.id}.docx"
    doc_record = GeneratedDocument.objects.create(
        template=template,
        created_by=request.user,
        investor=investor
    )
    doc_record.generated_file.save(filename, ContentFile(file_stream.read()))

    return Response(GeneratedDocumentSerializer(doc_record).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_commitment_letter(request, commitment_id):
    """
    Generates a Commitment Letter.
    Requires DocumentTemplate with code='COMMITMENT_LETTER'.
    """
    commitment = get_object_or_404(InvestorCommitment, pk=commitment_id)
    template = DocumentTemplate.objects.filter(code='COMMITMENT_LETTER').first()

    if not template:
        return Response({"error": "Template 'COMMITMENT_LETTER' not found."}, status=404)

    context = {'data': get_commitment_context(commitment)}

    try:
        file_stream = render_docx(template.file.path, context)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    filename = f"Commitment_{commitment.investor.name}_{commitment.id}.docx"
    doc_record = GeneratedDocument.objects.create(
        template=template,
        created_by=request.user,
        investor=commitment.investor,
        fund=commitment.fund
    )
    doc_record.generated_file.save(filename, ContentFile(file_stream.read()))

    return Response(GeneratedDocumentSerializer(doc_record).data)