"""``GET /research/profiles`` (Data Contract row 33, serving side).

Row 33 declares BOTH values config-owned/store-owned and assigns them to ONE endpoint,
``GET /research/profiles`` — the champion summary on ``/performance`` (J-05) and the MCP
``get_endpoint`` proxy read it verbatim; no surface may infer the champion from ledger
provenance or carry its own copy (that would be the second-computation-path drift the
single-source-of-truth anti-goal bans).

J-07 turns the champion pointer from a hardcoded constant into the ONE persisted, movable
source (``JournalStore.get_champion_pointer`` — seeded to the founding ``v1``/``default`` pair,
moved ONLY by a hold-out survivor via ``app/research/pnl_scan.py``). This module still computes
NOTHING of its own: it projects ``Config.profile_registry()`` (itself built from
``Config.profile_definition`` per registered id — the ONE registry ``POST /research/backtests``'s
route validation ALSO consults, never a second allowlist) and reads the champion pointer VERBATIM
from the store.

  * the registry — ``default`` (the frozen legacy engine configuration every archived-era surface
    and the live cockpit run on, guarded by the byte-equivalence suite) plus every registered
    candidate (additive-only, self-documenting its base + override — never selectable by the live
    cockpit);
  * the champion pointer — the founding strategy ``v1`` on profile ``default`` until a genuine
    hold-out survivor moves it (J-07's promotion mechanics); read from the ONE persisted source,
    never re-derived from ledger rows or a second copy.

Disciplines locked here:
  * The registry values ARE the existing single-copy config-owned projection
    (``Config.profile_registry()`` in ``app/config.py``) — this module imports nothing and carries
    NO second copy of any id string or override value (asserted over its source). The champion
    pointer is read VERBATIM from the injected ``JournalStore`` — no id-literal fallback exists
    here either.
  * GET only — there is no write surface in this module; ``app/research/pnl_scan.py`` is the ONE
    caller of ``JournalStore.set_champion_pointer`` (source-scan-guard-enforced).
  * ONE registry source: this projection and the backtest route's validation both consult
    ``Config.profile_definition`` — never a second allowlist (registry/resolution unit tests live
    in ``tests/test_profile_equivalence.py``).

The route now depends on the app-provided ``ResearchRegistry`` (``registry.store`` /
``registry.config``) via FastAPI dependency-injection — the SAME seam every other research route
already uses — so tests inject a temp-path store through ``dependency_overrides`` / ``set_registry``
exactly like the sibling projections (``ledger_projection``, ``test_pnl_ledger_api.py``'s ``ctx``
fixture pattern).
"""

from __future__ import annotations

from ..config import Config
from .store import JournalStore


def profiles_projection(store: JournalStore, config: Config) -> dict:
    """The canonical row-33 payload, computed nowhere else: the profile registry (``default``
    plus every registered candidate — ``config.profile_registry()``) and the current champion
    pointer, read VERBATIM from the ONE persisted source (``store.get_champion_pointer()``). This
    module carries NO copy of any id literal or override value, and NO copy of the champion
    pointer's values — everything is a pure read of its two owners."""
    return {
        "profiles": config.profile_registry(),
        "champion": store.get_champion_pointer(),
    }
