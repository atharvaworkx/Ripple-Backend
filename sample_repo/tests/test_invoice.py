"""Unit tests for invoice generation."""

from billing.invoice import generate_invoice

def test_generate_invoice_totals():
    """Verify invoice item lines and subtotal."""
    items = [
        {"sku": "LAPTOP", "price": 1000.0, "quantity": 1},
        {"sku": "MOUSE", "price": 25.0, "quantity": 2}
    ]
    invoice = generate_invoice("ORD-101", "CUST-1", items, discount_rate=0.10, region="US")
    assert invoice["order_id"] == "ORD-101"
    assert invoice["status"] == "ISSUED"
    assert len(invoice["items"]) == 2
    assert invoice["subtotal"] > 0
    assert invoice["tax"] > 0
    assert invoice["total_amount"] == round(invoice["subtotal"] + invoice["tax"], 2)
