from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# DRF Imports
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# Local Imports
from .models import DocumentTemplate, GeneratedDocument
from .forms import GenerateNoticeForm
from .utils import render_docx, render_to_pdf, get_transaction_context
from .serializers import DocumentTemplateSerializer, GeneratedDocumentSerializer

# Transaction Imports
from transactions.models import CapitalCall, Distribution

# --- PORTAL VIEWS ---

@login_required
def docgen_dashboard(request):
    """
    The main UI for generating documents.
    """
    recent_docs = GeneratedDocument.objects.order_by('-created_at')[:5]
    
    if request.method == 'POST':
        form = GenerateNoticeForm(request.POST)
        if form.is_valid():
            try:
                # 1. Extract Data
                txn_type = form.cleaned_data['transaction_type']
                txn_id = form.cleaned_data['transaction_id']
                template = form.cleaned_data['template']
                
                # 2. Fetch Transaction Object
                if txn_type == 'CALL':
                    obj = get_object_or_404(CapitalCall, pk=txn_id)
                else:
                    obj = get_object_or_404(Distribution, pk=txn_id)
                
                # 3. Build Context
                context = get_transaction_context(obj)
                
                # 4. Generate Content (Safe Logic)
                file_content = None
                ext = ""
                
                if template.type == 'DOCX' and template.file:
                    stream = render_docx(template.file.path, context)
                    file_content = stream.read()
                    ext = ".docx"
                elif template.type == 'HTML':
                    stream = render_to_pdf(template.html_content, context)
                    if stream:
                        file_content = stream.read()
                        ext = ".pdf"
                    else:
                        raise Exception("PDF Engine returned empty content.")
                
                # 5. Save Record
                if file_content:
                    doc = GeneratedDocument.objects.create(
                        template=template,
                        created_by=request.user,
                        fund=obj.fund,
                        investor=obj.investor
                    )
                    doc.generated_file.save(f"{template.code}_{obj.id}{ext}", ContentFile(file_content))
                    messages.success(request, f"Document Generated: {doc.generated_file.name}")
                
            except Exception as e:
                # Catches ImportErrors or missing files
                messages.error(request, f"Generation Failed: {str(e)}")
            
            return redirect('docgen:hub')
    else:
        form = GenerateNoticeForm()

    return render(request, 'docgen/dashboard.html', {
        'form': form, 
        'recent_docs': recent_docs
    })

# --- API VIEWSETS (Required for your api/urls.py) ---

class DocumentTemplateViewSet(viewsets.ModelViewSet):
    queryset = DocumentTemplate.objects.all()
    serializer_class = DocumentTemplateSerializer
    permission_classes = [IsAuthenticated]

class GeneratedDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GeneratedDocument.objects.all()
    serializer_class = GeneratedDocumentSerializer
    permission_classes = [IsAuthenticated]