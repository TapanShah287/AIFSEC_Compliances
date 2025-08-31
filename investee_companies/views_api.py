# investee_companies/views_api.py
from collections import defaultdict
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models
from .models import InvesteeCompany, Shareholding
from .serializers import ShareholdingSerializer, CompanyShareholdingPatternSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def company_shareholding_api(request, pk: int):
    company = get_object_or_404(InvesteeCompany, pk=pk)
    qs = Shareholding.objects.filter(investee_company=company)

    # total shares across ALL classes
    total = qs.aggregate(total=models.Sum("number_of_shares"))["total"] or 0

    ser = ShareholdingSerializer(qs, many=True, context={"total_company_shares": total})
    return Response(ser.data)