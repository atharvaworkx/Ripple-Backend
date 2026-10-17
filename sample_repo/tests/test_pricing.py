"""Unit tests for billing pricing functions."""

import pytest
from billing.pricing import calculate_discounted_price, calculate_tax

def test_calculate_discounted_price_standard():
    """Verify standard discount calculation."""
    result = calculate_discounted_price(100.0, 0.20)
    assert result == 80.0

def test_calculate_discounted_price_zero_discount():
    """Verify price when discount is 0%."""
    result = calculate_discounted_price(50.0, 0.0)
    assert result == 50.0

def test_calculate_discounted_price_invalid_inputs():
    """Verify negative price or out-of-range discount raises ValueError."""
    with pytest.raises(ValueError):
        calculate_discounted_price(-10.0, 0.1)
    with pytest.raises(ValueError):
        calculate_discounted_price(10.0, 1.5)

def test_pricing_rounding_precision():
    """
    CRITICAL REGRESSION TEST:
    Verify financial 2-decimal half-up rounding.
    10.05 discounted by 5% is 10.05 * 0.95 = 9.5475.
    Correct expected price is 9.55.
    Truncation floor bug incorrectly yields 9.54!
    """
    result = calculate_discounted_price(10.05, 0.05)
    assert result == 9.55, f"Expected 9.55 but got {result}. Possible floor truncation regression!"

def test_calculate_tax_us_region():
    """Verify regional tax computation."""
    tax = calculate_tax(100.0, "US")
    assert tax == 8.25
