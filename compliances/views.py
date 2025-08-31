from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .models import ComplianceTask, ComplianceDocument
from .serializers import ComplianceTaskSerializer, ComplianceDocumentSerializer

class ComplianceTaskViewSet(viewsets.ModelViewSet):
    queryset = ComplianceTask.objects.all().order_by('-due_date'); serializer_class = ComplianceTaskSerializer; permission_classes = [IsAuthenticated]
class ComplianceDocumentViewSet(viewsets.ModelViewSet):
    queryset = ComplianceDocument.objects.all().order_by('-uploaded_at'); serializer_class = ComplianceDocumentSerializer; permission_classes = [IsAuthenticated]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def compliance_tasks(request):
    # TODO: replace with real queryset + serializer
    # Example shape the portal can consume:
    data = {
        "results": [],   # put task dicts here
        "count": 0,
    }
    return Response(data)