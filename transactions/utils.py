from decimal import Decimal

def calculate_fifo_cost_basis(redemption):
    """
    Calculates cost basis for a redemption using FIFO method.
    Matches redemptions against the earliest available purchase lots.
    """
    # Import inside function to avoid circular import with models.py
    from .models import PurchaseTransaction, RedemptionTransaction

    # 1. Get all purchases for this specific stock/fund combo, ordered by date
    purchases = PurchaseTransaction.objects.filter(
        fund=redemption.fund,
        investee_company=redemption.investee_company,
        share_capital=redemption.share_capital,
        trade_date__lte=redemption.trade_date
    ).order_by('trade_date', 'id')

    # 2. Get all PRIOR redemptions to see what has already been sold
    prior_redemptions = RedemptionTransaction.objects.filter(
        fund=redemption.fund,
        investee_company=redemption.investee_company,
        share_capital=redemption.share_capital,
        trade_date__lte=redemption.trade_date
    ).exclude(id=redemption.id).order_by('trade_date', 'id')

    # Calculate total quantity sold before this transaction
    total_sold_previously = sum(r.quantity for r in prior_redemptions)
    
    # 3. Simulate FIFO consumption
    remaining_qty_to_sell = redemption.quantity
    cost_basis = Decimal('0.00')

    current_purchase_idx = 0
    # Fast-forward through purchases that were already fully sold
    while total_sold_previously > 0 and current_purchase_idx < len(purchases):
        p = purchases[current_purchase_idx]
        if p.quantity <= total_sold_previously:
            total_sold_previously -= p.quantity
            current_purchase_idx += 1
        else:
            # This purchase is partially sold
            # We don't increment index because some of this lot is available for *current* redemption
            # Temporarily reduce the quantity of this object in memory (not db)
            p.quantity -= total_sold_previously
            total_sold_previously = 0

    # 4. Calculate Cost Basis for CURRENT redemption
    while remaining_qty_to_sell > 0 and current_purchase_idx < len(purchases):
        p = purchases[current_purchase_idx]
        qty_taken = min(p.quantity, remaining_qty_to_sell)
        
        cost_basis += qty_taken * p.price
        remaining_qty_to_sell -= qty_taken
        current_purchase_idx += 1

    return cost_basis

def calculate_fifo_gain(redemption):
    """
    Calculates cost basis for a redemption using FIFO method.
    Matches redemptions against the earliest available purchase lots.
    Returns: (cost_basis, realized_gain)
    """
    # Import inside function to avoid circular import with models.py
    from .models import PurchaseTransaction, RedemptionTransaction

    # 1. Get all purchases for this specific asset, ordered by date
    purchases = list(PurchaseTransaction.objects.filter(
        fund=redemption.fund,
        investee_company=redemption.investee_company,
        share_class=redemption.share_class,
        transaction_date__lte=redemption.transaction_date
    ).order_by('transaction_date', 'id'))

    # 2. Calculate how much has already been sold PRIOR to this transaction
    prior_redemptions = RedemptionTransaction.objects.filter(
        fund=redemption.fund,
        investee_company=redemption.investee_company,
        share_class=redemption.share_class,
        transaction_date__lte=redemption.transaction_date
    ).exclude(id=redemption.id)

    total_sold_previously = prior_redemptions.aggregate(Sum('quantity'))['quantity__sum'] or Decimal('0.00')
    
    # 3. FIFO Consumption Logic
    remaining_qty_to_sell = redemption.quantity
    cost_basis = Decimal('0.00')

    # Fast-forward through purchases that were already fully sold
    for p in purchases:
        if remaining_qty_to_sell <= 0:
            break
            
        available_in_lot = p.quantity
        
        if total_sold_previously >= available_in_lot:
            # This lot was fully consumed by previous redemptions
            total_sold_previously -= available_in_lot
            continue
        elif total_sold_previously > 0:
            # This lot was partially consumed previously
            available_in_lot -= total_sold_previously
            total_sold_previously = Decimal('0.00')

        # Now take from what's left in this lot for the CURRENT sale
        qty_taken = min(available_in_lot, remaining_qty_to_sell)
        cost_basis += qty_taken * p.price_per_share
        remaining_qty_to_sell -= qty_taken

    # 4. Calculate Gain
    sale_proceeds = redemption.quantity * redemption.price_per_share
    realized_gain = sale_proceeds - cost_basis

    return cost_basis, realized_gain