"""Screen-pin resolution (Era B "The Desk", goal-desk-iter-36, J-21) -- answers, for a
caller-supplied ``screen_date``, whether a screen run right now would reuse an already-recorded
snapshot or walk the universe fresh. The Data Contract's "Screen-pin resolution" row's ONE owner,
served by ``GET /research/desk/screen/pins``.

THIS MODULE computes NOTHING new -- every pin is resolved through the SAME accessor that already
owns it, in the SAME order ``run_screen_and_record`` resolves them
(``desk_screen_compute.py:155``-``:161``): ``desk_screen.screen_as_of`` (``as_of``),
``UniverseStore.list()``'s own latest record id and member count (``universe_snapshot_id``,
``members_total`` -- read the way ``DeskScreenComputeManager.trigger`` already reads it,
``len(records[-1]["members"])``), ``Config.config_fingerprint()`` (``config_fingerprint``), and
``desk_screen.compute_bar_store_signature`` over ``desk_coverage.get_desk_coverage``'s index-only
read (``bar_store_signature``) -- zero new derivation, zero second owner, no ``BarStore`` read of
any kind (T-4). The recorded-or-not answer comes from ``ScreenStore.find_by_key`` on exactly those
five pins -- the SAME lookup J-18's pre-check already makes (``desk_screen_compute.py:209``). This
resolution and a run's own therefore cannot disagree: same functions, same order, same immutable
stores.

**Honest empty (TC-5).** Before any universe snapshot is ever registered, there is nothing to
resolve a bar-store signature OVER -- ``desk_coverage.get_desk_coverage`` itself would report
``members: []``, and hashing a signature over zero pairs would misleadingly look like a real,
resolvable pin. This module reports the honest ``universe_snapshot_id: None``,
``bar_store_signature: None``, ``members_total: 0``, ``recorded: None`` instead of computing a
signature over nothing -- HTTP 200, never a 4xx/5xx (mirrors ``get_universe``/``get_coverage``'s
own honest-empty convention). ``run_screen_and_record`` never reaches this state itself (its own
caller, ``trigger_desk_screen_compute``, refuses with a 422 before a universe-less pin resolution
is ever attempted) -- this is the first caller that must answer it honestly rather than refuse,
since disclosure (unlike a run) has nothing destructive to refuse.

**Disclose, never judge (T-copy discipline).** The response states what the pins ARE and whether a
recording exists under them, and stops there -- no threshold, staleness, or confidence number; no
fresh/stale/current/behind/up-to-date judgement; no advice or prediction. A differing signature
proves exactly one thing: no recorded screen carries these pins, i.e. a run for this date would
walk rather than reuse.

**Persists nothing.** No store, no file, no cache, no index, no new ``Config`` field -- a pure
read over three already-constructed dependencies (``UniverseStore``, ``BarIndex``, ``ScreenStore``)
plus the process-wide ``Config``. Writes nothing, triggers nothing, recomputes nothing: zero
``compute_tradability`` calls, zero band selections, zero rank-key evaluations, zero bar reads
(structurally -- this module never imports ``compute_tradability`` and never receives a
``BarStore`` reference of any kind, mirroring ``desk_screen._bar_store_signature``'s own "cannot
call what it never received" argument)."""

from __future__ import annotations

from ..config import Config
from .bar_index import BarIndex
from .desk_screen import ScreenStore, compute_bar_store_signature, screen_as_of
from .desk_universe import UniverseStore


def resolve_desk_screen_pins(
    screen_date: str,
    universe_store: UniverseStore,
    bar_index: BarIndex,
    config: Config,
    screen_store: ScreenStore,
) -> dict:
    """The five pins a screen run for ``screen_date`` would resolve RIGHT NOW, plus whether a
    screen is already recorded under them -- see the module docstring. ``screen_date`` is the
    caller's own value (the page passes the SAME ``todayUtcDate()`` it already submits to the
    trigger, ``apps/frontend/app/desk/page.tsx:228``/``:2350``) -- nothing here calls ``now()``
    (T-6): identical inputs (this date, the pinned universe record, the index's rows as they stand)
    reproduce a byte-identical body, and the payload carries no wall-clock field of its own.

    Shape::

        {
          "screen_date": str, "as_of": str, "universe_snapshot_id": str | None,
          "config_fingerprint": str, "bar_store_signature": str | None,
          "members_total": int,
          "recorded": {
            "id": str, "screen_date": str, "created_utc": str, "bar_store_signature": str,
            "ranked_count": int, "skipped_count": int,
          } | None,
        }
    """
    as_of = screen_as_of(screen_date)
    config_fingerprint = config.config_fingerprint()
    universe_records, _universe_errors = universe_store.list()

    if not universe_records:
        # Honest empty (TC-5): nothing is registered to resolve a coverage signature over.
        return {
            "screen_date": screen_date,
            "as_of": as_of,
            "universe_snapshot_id": None,
            "config_fingerprint": config_fingerprint,
            "bar_store_signature": None,
            "members_total": 0,
            "recorded": None,
        }

    latest_universe = universe_records[-1]
    universe_snapshot_id = latest_universe["id"]
    members_total = len(latest_universe["members"])
    bar_store_signature = compute_bar_store_signature(universe_store, bar_index)

    existing = screen_store.find_by_key(
        screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature
    )
    recorded = None
    if existing is not None:
        recorded = {
            "id": existing["id"],
            "screen_date": existing["screen_date"],
            "created_utc": existing["created_utc"],
            "bar_store_signature": existing["bar_store_signature"],
            "ranked_count": len(existing["rows"]),
            "skipped_count": len(existing["skipped"]),
        }

    return {
        "screen_date": screen_date,
        "as_of": as_of,
        "universe_snapshot_id": universe_snapshot_id,
        "config_fingerprint": config_fingerprint,
        "bar_store_signature": bar_store_signature,
        "members_total": members_total,
        "recorded": recorded,
    }
