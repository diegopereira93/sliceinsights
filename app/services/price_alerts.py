"""
Price Alerts Service.

Dataclass para representar alertas de queda de preço.
"""

from dataclasses import dataclass


@dataclass
class PriceAlert:
    """Representa um alerta de queda de preço."""
    product_id: str
    brand_name: str
    model_name: str
    previous_price: float
    current_price: float
    drop_pct: float
    product_url: str
