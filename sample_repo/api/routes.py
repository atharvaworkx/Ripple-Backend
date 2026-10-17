"""Web API endpoints exposing billing and checkout workflows."""

from typing import Dict, Any
from checkout.order_processor import OrderProcessor
from billing.invoice import generate_invoice

# Mock router decorator for AST extraction of route handlers
class Router:
    def __init__(self):
        self.routes = {}

    def post(self, path: str):
        def decorator(func):
            self.routes[f"POST:{path}"] = func
            return func
        return decorator

    def get(self, path: str):
        def decorator(func):
            self.routes[f"GET:{path}"] = func
            return func
        return decorator

api_router = Router()
processor = OrderProcessor()

@api_router.post("/api/v1/checkout/process")
def handle_checkout_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    HTTP endpoint for checkout operations.
    Downstream dependent on process_checkout and calculate_discounted_price.
    """
    customer_id = payload.get("customer_id", "guest")
    items = payload.get("items", [])
    coupon = payload.get("coupon_code")
    region = payload.get("region", "US")

    return processor.process_checkout(
        customer_id=customer_id,
        cart_items=items,
        coupon_code=coupon,
        region=region
    )

@api_router.get("/api/v1/billing/invoices/{order_id}")
def handle_get_invoice(order_id: str, customer_id: str = "cust_123") -> Dict[str, Any]:
    """
    HTTP endpoint to retrieve or regenerate invoice details.
    Downstream dependent on generate_invoice and calculate_discounted_price.
    """
    sample_items = [{"sku": "PROD-1", "price": 49.99, "quantity": 1}]
    return generate_invoice(order_id=order_id, customer_id=customer_id, items=sample_items)
