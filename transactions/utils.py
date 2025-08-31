# transactions/utils.py
from decimal import Decimal

def calculate_fifo_cost_basis(redemption):
    """
    Calculates the cost basis for a given redemption transaction using the
    First-In, First-Out (FIFO) accounting method. This version is more robust
    by filtering prior redemptions based on date and PK.
    """
    # Lazily import models to avoid circular dependencies
    from .models import PurchaseTransaction, RedemptionTransaction

    # Base query for the specific security holding
    base_query = {
        'fund': redemption.fund,
        'investee_company': redemption.investee_company,
        'share_capital': redemption.share_capital,
        'status': 'posted', # Only consider posted transactions
    }

    # Get all relevant purchases up to the redemption date
    purchases = PurchaseTransaction.objects.filter(
        **base_query,
        purchase_date__lte=redemption.redemption_date
    ).order_by('purchase_date', 'id')

    # Get all prior redemptions for this security
    prior_redemptions = RedemptionTransaction.objects.filter(
        **base_query,
        redemption_date__lt=redemption.redemption_date
    ).order_by('redemption_date', 'id')
    
    # Also include redemptions on the same day but created earlier
    same_day_prior_redemptions = RedemptionTransaction.objects.filter(
        **base_query,
        redemption_date=redemption.redemption_date,
        id__lt=redemption.id
    ).order_by('id')

    # Create a mutable list of purchase lots
    purchase_lots = [{'qty': p.quantity, 'rate': p.purchase_rate} for p in purchases]

    # Account for shares sold in all prior redemptions
    all_prior_redemptions = list(prior_redemptions) + list(same_day_prior_redemptions)

    for prior_r in all_prior_redemptions:
        qty_to_deduct = prior_r.quantity
        for lot in purchase_lots:
            if lot['qty'] > 0:
                deducted_qty = min(lot['qty'], qty_to_deduct)
                lot['qty'] -= deducted_qty
                qty_to_deduct -= deducted_qty
                if qty_to_deduct == 0:
                    break

    # Calculate the cost basis for the current redemption
    cost_basis = Decimal('0.0')
    quantity_to_account_for = redemption.quantity
    
    for lot in purchase_lots:
        if quantity_to_account_for <= 0:
            break
        
        if lot['qty'] > 0:
            qty_from_this_lot = min(lot['qty'], quantity_to_account_for)
            cost_basis += qty_from_this_lot * lot['rate']
            quantity_to_account_for -= qty_from_this_lot

    # This check is important. If quantity_to_account_for is still greater than 0,
    # it means the redemption quantity was more than what was available based on posted purchases.
    # The model's clean method should prevent this, but this is a safeguard.
    if quantity_to_account_for > 0:
        # Handle this case, maybe log a warning or raise an exception
        # For now, we'll return the cost basis calculated so far.
        pass

    return cost_basis
