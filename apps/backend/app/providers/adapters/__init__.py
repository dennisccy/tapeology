"""Vendor-data adapter seam: the one place a concrete market-data vendor may appear.

The engine, API, providers, and historical layer depend only on the vendor-neutral
``MarketDataAdapter`` interface in ``base`` — never on a vendor SDK or vendor credential names.
A second vendor is therefore a single new adapter module beside ``alpaca``, plus a one-line
change to ``get_adapter`` here. ``get_adapter`` is the neutral accessor the API uses so that
``main.py`` never names a concrete vendor (only this seam and the adapter module do).
"""

from __future__ import annotations

from .alpaca import AlpacaAdapter, real_data_available
from .base import MarketDataAdapter


def get_adapter() -> MarketDataAdapter:
    """Return the configured concrete market-data adapter (the current vendor)."""
    return AlpacaAdapter()


__all__ = ["MarketDataAdapter", "get_adapter", "real_data_available"]
