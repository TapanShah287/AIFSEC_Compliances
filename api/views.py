from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

# Import your models
from funds.models import Fund
from investors.models import Investor
from investee_companies.models import InvesteeCompany

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_search(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return Response([])

    results = []

    # 1. Search Funds
    funds = Fund.objects.filter(name__icontains=query)[:3]
    for f in funds:
        results.append({
            'category': 'Fund',
            'title': f.name,
            'subtitle': f"Target: {f.target_corpus}",
            'url': f"/portal/funds/{f.id}/", # Hardcoded URL pattern match
            'icon': 'briefcase'
        })

    # 2. Search Investors
    investors = Investor.objects.filter(
        Q(name__icontains=query) | Q(pan__icontains=query)
    )[:5]
    for i in investors:
        results.append({
            'category': 'Investor',
            'title': i.name,
            'subtitle': i.email,
            'url': f"/portal/investors/{i.id}/",
            'icon': 'user'
        })

    # 3. Search Portfolio Companies
    companies = InvesteeCompany.objects.filter(name__icontains=query)[:3]
    for c in companies:
        results.append({
            'category': 'Asset',
            'title': c.name,
            'subtitle': c.sector,
            'url': f"/portal/companies/{c.id}/",
            'icon': 'building-2'
        })

    return Response(results)