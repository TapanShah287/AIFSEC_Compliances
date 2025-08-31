# transactions/tests.py
from django.test import TestCase
from decimal import Decimal
from your_app.models import Fund, InvesteeCompany, ShareType, PurchaseTransaction, RedemptionTransaction

class FifoCalculationTest(TestCase):

    def setUp(self):
        # Create common objects like Fund, Company, ShareType
        self.fund = Fund.objects.create(...)
        self.company = InvesteeCompany.objects.create(...)
        self.share_type = ShareType.objects.create(...)

    def test_simple_fifo_gain(self):
        """Test a simple purchase and full redemption."""
        # Arrange: Create transactions
        PurchaseTransaction.objects.create(
            fund=self.fund, investee_company=self.company, share_type=self.share_type,
            quantity=100, purchase_rate=10, purchase_date='2025-01-01'
        )
        redemption = RedemptionTransaction.objects.create(
            fund=self.fund, investee_company=self.company, share_type=self.share_type,
            quantity=100, redemption_rate=15, redemption_date='2025-02-01'
        )

        # Act: Access the calculated properties
        cost_basis = redemption.cost_basis
        realized_gain = redemption.realized_gain

        # Assert: Check if the calculations are correct
        self.assertEqual(cost_basis, Decimal('1000')) # 100 * 10
        self.assertEqual(realized_gain, Decimal('500')) # (100 * 15) - 1000