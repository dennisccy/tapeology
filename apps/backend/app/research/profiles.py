"""The indicator-profile registry + champion pointer (Data Contract row 33) — serving side.

Row 33 declares BOTH values config-owned and assigns them to ONE endpoint,
``GET /research/profiles`` — the champion summary on ``/performance`` (J-05) and the MCP
``get_endpoint`` proxy read it verbatim; no surface may infer the champion from ledger
provenance or carry its own copy (that would be the second-computation-path drift the
single-source-of-truth anti-goal bans).

Landed MINIMALLY at J-05: no promotion has ever happened and no candidate is registered yet, so
the served values are the config-owned INITIAL state, built from the existing single-copy
constants (``STRATEGY_V1_ID`` in ``app/config.py``; ``PROFILE_DEFAULT`` in
``app/research/backtests.py`` — imported, never re-declared):

  * the registry — exactly one profile, the frozen ``default`` (the legacy engine configuration
    every archived-era surface and the live cockpit run on, guarded by the byte-equivalence
    suite);
  * the champion pointer — strategy ``v1`` on profile ``default``, the founding champion.

What is deliberately NOT here (later journeys own it): candidate-profile registration or
definition (J-06), and champion-movement/promotion mechanics — only a hold-out survivor may ever
move the pointer (J-07). The registry is config-owned, so there is NO write surface anywhere:
the route is GET-only and any other verb is an automatic 405.
"""

from __future__ import annotations

from ..config import STRATEGY_V1_ID
from .backtests import PROFILE_DEFAULT


def profiles_projection() -> dict:
    """The canonical row-33 payload, computed nowhere else: the profile registry (today exactly
    the frozen ``default``) and the current champion pointer (the founding strategy + profile —
    no promotion exists yet). The flag key is ``is_default`` (not the id string itself) so this
    module carries NO copy of the id literal — the ids come only from the imported constants."""
    return {
        "profiles": [{"id": PROFILE_DEFAULT, "frozen": True, "is_default": True}],
        "champion": {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT},
    }
