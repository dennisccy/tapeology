"""Vendor-data adapter seam: the one place a concrete market-data vendor may appear.

The engine, API, and the existing providers depend only on the vendor-neutral
``MarketDataAdapter`` interface in ``base`` — never on a vendor SDK or vendor credential
names. A second vendor is therefore a single new adapter module beside ``alpaca``.
"""
