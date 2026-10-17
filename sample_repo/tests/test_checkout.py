"""Unit tests for checkout order processor."""

import pytest
from checkout.order_processor import OrderProcessor

@pytest.fixture
def processor():
    return OrderProcessor(currency="USD")

def test_process_checkout_empty_cart(processor):
    """Verify error on empty cart."""
    with pytest.raises(ValueError):
        processor.process_checkout("cust_1", [])

def test_process_checkout_success(processor):
    """Verify successful checkout computation."""
    items = [
        {"sku": "ITEM-A", "price": 100.0, "quantity": 1},
        {"sku": "ITEM-B", "price": 50.0, "quantity": 2}
    ]
    res = processor.process_checkout("cust_99", items, coupon_code="WELCOME10")
    assert res["status"] == "CONFIRMED"
    assert res["discount_applied"] is True
    assert res["invoice"]["subtotal"] > 0
