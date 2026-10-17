"""Invoice generation module."""

from typing import List, Dict, Any
from billing.pricing import calculate_discounted_price, calculate_tax

def generate_invoice(order_id: str, customer_id: str, items: List[Dict[str, Any]], discount_rate: float = 0.0, region: str = "US") -> Dict[str, Any]:
    """
    Generate an itemized invoice for an order with discounts and tax.
    Direct caller of calculate_discounted_price and calculate_tax.
    """
    processed_items = []
    subtotal = 0.0

    for item in items:
        base_price = float(item.get("price", 0.0))
        qty = int(item.get("quantity", 1))
        unit_discounted = calculate_discounted_price(base_price, discount_rate)
        line_total = round(unit_discounted * qty, 2)
        subtotal += line_total
        processed_items.append({
            "sku": item.get("sku"),
            "base_price": base_price,
            "unit_discounted": unit_discounted,
            "quantity": qty,
            "line_total": line_total
        })

    subtotal = round(subtotal, 2)
    tax = calculate_tax(subtotal, region)
    total_amount = round(subtotal + tax, 2)

    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "items": processed_items,
        "subtotal": subtotal,
        "tax": tax,
        "total_amount": total_amount,
        "status": "ISSUED"
    }
