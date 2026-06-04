"""Alpaca market-data adapter — the SINGLE module where Alpaca specifics live.

This is the one concrete adapter behind the vendor-neutral ``MarketDataAdapter`` seam. This
iteration it implements only credential detection: ``is_available()`` reads the Alpaca API
key/secret from the ENVIRONMENT ONLY (never committed source, never the engine ``Config`` —
that dataclass holds engine thresholds, not secrets) and reports whether both are present. No
Alpaca SDK is imported and no network call is made; the real streaming / historical-replay
providers land later (J-11/J-12) behind this same seam.

Anti-goals served: *no secrets in source* (env-only; the names are documented with empty
values in ``apps/backend/.env.example``), *provider-agnostic engine* (vendor names confined
here), *no fabricated data* (absence of credentials => an honest unavailable, never a
synthesized read).
"""

from __future__ import annotations

import os

# Environment variable NAMES (never values). Documented with empty values in
# apps/backend/.env.example — the only committable env file.
ENV_API_KEY = "ALPACA_API_KEY"
ENV_API_SECRET = "ALPACA_API_SECRET"
# The market-data feed is configuration, not a secret. Alpaca's free feed is IEX.
ENV_FEED = "ALPACA_FEED"
DEFAULT_FEED = "iex"


def _env(name: str) -> str:
    """Return a trimmed environment value, or ``""`` when unset/blank (blank != configured)."""
    value = os.environ.get(name)
    return value.strip() if value else ""


class AlpacaAdapter:
    """Credential-detection adapter for Alpaca (this iteration: availability only)."""

    name = "alpaca"

    def is_available(self) -> bool:
        """``True`` only when BOTH the Alpaca key and secret are present (non-blank) in env."""
        return bool(_env(ENV_API_KEY)) and bool(_env(ENV_API_SECRET))

    @property
    def feed(self) -> str:
        """The configured market-data feed (defaults to the free IEX feed)."""
        return _env(ENV_FEED) or DEFAULT_FEED


def real_data_available() -> bool:
    """The single canonical source for the row-9 real-data availability state.

    Derived from the one concrete adapter's credential detection and evaluated fresh on each
    call (so it tracks the current environment). The API reads THIS to gate a real-mode watch;
    it is not recomputed in the UI — the UI learns availability from the API, never re-derives
    credential presence itself.
    """
    return AlpacaAdapter().is_available()
