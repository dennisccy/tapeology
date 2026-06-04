"""The vendor-neutral market-data adapter interface (provider-agnostic anti-goal).

A ``MarketDataAdapter`` is the single seam behind which a concrete vendor (its SDK and its
credential names) is allowed to live. The engine, API, and existing providers depend only on
this interface, so swapping or adding a vendor is one new adapter module — vendor specifics
never leak outward.

This iteration an adapter implements only credential detection: ``is_available()`` reports
whether the vendor's credentials are configured in the environment (no network call, no
fabrication). The streaming / historical-fetch methods land with the real providers
(J-11/J-12) behind this same seam; the interface does not preclude adding them.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class MarketDataAdapter(Protocol):
    """Vendor-neutral seam the API reads to decide real-data availability.

    ``name`` identifies the vendor for diagnostics; ``is_available()`` is ``True`` only when
    the vendor's credentials are present in the environment — it never reaches the network and
    never fabricates an answer.
    """

    name: str

    def is_available(self) -> bool:
        ...
