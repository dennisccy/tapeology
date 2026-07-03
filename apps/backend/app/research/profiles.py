"""``GET /research/profiles`` (Data Contract row 33, serving side).

Row 33 declares BOTH values config-owned and assigns them to ONE endpoint,
``GET /research/profiles`` — the champion summary on ``/performance`` (J-05) and the MCP
``get_endpoint`` proxy read it verbatim; no surface may infer the champion from ledger
provenance or carry its own copy (that would be the second-computation-path drift the
single-source-of-truth anti-goal bans).

J-06 registers the FIRST additive candidate profile beside the frozen ``default``. This module
still computes NOTHING of its own: it projects ``Config.profile_registry()`` (itself built from
``Config.profile_definition`` per registered id — the ONE registry ``POST /research/backtests``'s
route validation ALSO consults, never a second allowlist) and the config-owned champion pointer.

  * the registry — ``default`` (the frozen legacy engine configuration every archived-era surface
    and the live cockpit run on, guarded by the byte-equivalence suite) plus the ONE registered
    candidate (additive-only, self-documenting its base + override — never selectable by the live
    cockpit);
  * the champion pointer — strategy ``v1`` on profile ``default``, the founding champion, UNMOVED
    by J-06 (only a hold-out survivor may ever move it — J-07's promotion mechanics).

Disciplines locked here:
  * The payload values ARE the existing single-copy constants (``STRATEGY_V1_ID`` /
    ``PROFILE_DEFAULT`` in ``app/config.py``) plus the config-owned registry projection — this
    module imports them and carries NO second copy of any id string or override value (asserted
    over its source).
  * GET only — the registry is config-owned, so NO write surface exists: any non-GET verb is
    FastAPI's default 405 (no handler exists at all).

Uses a lifespan-less ``TestClient`` (the ``test_meta_routes.py`` precedent): the projection is
config-owned with no registry/engine/store dependency, so no injection is needed.
"""

from __future__ import annotations

from ..config import CONFIG, PROFILE_DEFAULT, STRATEGY_V1_ID


def profiles_projection() -> dict:
    """The canonical row-33 payload, computed nowhere else: the profile registry (``default``
    plus the registered J-06 candidate — ``Config.profile_registry()``) and the current champion
    pointer (the founding strategy + profile — no promotion exists yet, J-07). This module carries
    NO copy of any id literal or override value — everything comes from the config-owned source."""
    return {
        "profiles": CONFIG.profile_registry(),
        "champion": {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT},
    }
