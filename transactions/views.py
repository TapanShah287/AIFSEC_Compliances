from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from .models import Transaction, InvestorCommitment
from .serializers import TransactionSerializer, InvestorCommitmentSerializer

class TransactionViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["investor"]    # ?investor=2
    ordering_fields = ["date", "amount", "created_at"]
    ordering = ["-date", "-created_at"]

    def get_queryset(self):
        qs = Transaction.objects.all().select_related("investor", "fund")
        investor_id = self.request.query_params.get("investor")
        if investor_id:
            qs = qs.filter(investor_id=investor_id)
        return qs

class InvestorCommitmentViewSet(viewsets.ModelViewSet):
    queryset = InvestorCommitment.objects.select_related("fund", "investor").all()
    serializer_class = InvestorCommitmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["investor", "fund"]
