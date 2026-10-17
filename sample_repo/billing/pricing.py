# Sample E-Commerce Billing Engine
# Demonstrates realistic python code structure with mathematical operations,
# invoice generation, checkout pipelines, and API endpoints.

import math
from typing import Dict, Any, List

def calculate_discounted_price(base_price: float, discount_rate: float, currency: str = "USD") -> float:
    """
    Calculate the net price after applying percentage discount.
    
    SEEDED REGRESSION SCENARIO:
    A developer modified this function to truncate using int(x * 100) / 100
    instead of proper round(x, 2), causing subtle penny-rounding discrepancies
    in multi-item orders and failing strict precision tests.
    """
    if base_price < 0:
        raise ValueError("Base price cannot be negative")
    if not (0.0 <= discount_rate <= 1.0):
        raise ValueError("Discount rate must be between 0.0 and 1.0")

    # REGRESSION INTRODUCED: Truncation bug instead of round()
    # Old code: return round(base_price * (1.0 - discount_rate), 2)
    discounted = base_price * (1.0 - discount_rate)
    return math.floor(discounted * 100) / 100.0


def calculate_tax(subtotal: float, region: str = "US") -> float:
    """Calculate regional sales tax."""
    rates = {
        "US": 0.0825,
        "EU": 0.20,
        "UK": 0.20,
        "CA": 0.13,
    }
    rate = rates.get(region, 0.05)
    return round(subtotal * rate, 2)
