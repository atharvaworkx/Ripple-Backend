"""Checkout and order processing service."""

import uuid
from typing import List, Dict, Any, Optional
from billing.pricing import calculate_discounted_price
from billing.invoice import generate_invoice

COUPON_CODES = {
    "WELCOME10": 0.10,
    "VIP25": 0.25,
    "FLASH50": 0.50,
}

class OrderProcessor:
    """Handles end-to-end checkout and payment preparation."""

    def __init__(self, currency: str = "USD"):
        self.currency = currency

    def resolve_discount(self, coupon_code: Optional[str]) -> float:
        """Resolve discount percentage from coupon code."""
        if not coupon_code:
            return 0.0
        return COUPON_CODES.get(coupon_code.upper(), 0.0)

    def process_checkout(self, customer_id: str, cart_items: List[Dict[str, Any]], coupon_code: Optional[str] = None, region: str = "US") -> Dict[str, Any]:
        """
        Process user checkout, validates items, computes discounts,
        and triggers downstream invoice generation.
        """
        if not cart_items:
            raise ValueError("Cart items cannot be empty")

        discount_rate = self.resolve_discount(coupon_code)
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        # Directly invokes generate_invoice, which in turn calls calculate_discounted_price
        invoice = generate_invoice(
            order_id=order_id,
            customer_id=customer_id,
            items=cart_items,
            discount_rate=discount_rate,
            region=region
        )

        return {
            "order_id": order_id,
            "customer_id": customer_id,
            "status": "CONFIRMED",
            "invoice": invoice,
            "currency": self.currency,
            "discount_applied": discount_rate > 0.0
        }
