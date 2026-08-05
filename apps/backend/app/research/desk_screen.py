"""The screen: pinned inputs, append-only snapshot, deterministic rank (Era B "The Desk", Key
Capability 3, J-03) -- the Data Contract's "Screen snapshots, rank rows, skip rows" row's ONE
owner, served by ``GET /research/desk/screen``.

THIS MODULE computes NOTHING about tradable structure itself -- it is a pure ORCHESTRATION lens
over three already-canonical owners: ``compute_tradability`` (``tradability.py:381`` -- bands,
class, quality score, verbatim), ``desk_coverage.get_desk_coverage`` (per-member coverage badge,
verbatim reuse -- also the source of ``bar_store_signature``, see below), and ``DatasetStore.list``
(tick-evidence presence, verbatim). Two new desk-owned values are computed HERE and only here:
``distance_bps`` (a plain arithmetic derivation from a band's own edge price and a reference close
this module resolves) and the cross-symbol rank order.

**The append-only store** (``ScreenStore``) mirrors ``desk_universe.UniverseStore``'s discipline
exactly: a checksum-verified load on every read, ``record`` as the only mutation, no update/delete
function anywhere (immutability is structural, not policed). UNLIKE the universe store (which dedups
on parsed CONTENT), a screen dedups on its own 5-pin KEY -- ``(screen_date, as_of,
universe_snapshot_id, config_fingerprint, bar_store_signature)`` -- because the key alone
deterministically determines the content (the row computation is a pure function of those five
pins), so keying on the pins is equivalent to keying on content while being resolvable BEFORE the
(potentially ~100-member) walk ever runs.

**``as_of`` translation (T-6, goal-desk-iter-3 NOTES).** ``as_of`` is a deterministic function of
the operator-given ``screen_date`` alone -- ``f"{screen_date}T23:59:59Z"`` -- reusing ``/structure``'s
own plain-date convention rather than inventing a new one. ``compute_tradability``'s basis
resolution is a CALENDAR-DATE comparison, so any ``as_of`` inside ``screen_date``'s own UTC day
resolves the identical prior-session basis -- never ``datetime.now()``.

**``bar_store_signature`` (T-4, TC-15).** A checksum over the sorted ``(symbol, timeframe,
latest_window_end_utc)`` tuples read ENTIRELY from ``desk_coverage.get_desk_coverage``'s own
per-member x per-timeframe output (already ``bar_index``-backed, already proven index-fast in J-02)
-- never a ``BarStore``/JSON-file re-hash (the era-5C 31.4s mistake T-4 exists to prevent).
``_bar_store_signature`` below takes the ALREADY-fetched coverage payload and touches no store at
all, so it is structurally incapable of issuing a ``BarStore`` call.

**Reference close price (TC-19).** ``compute_tradability``/``compute_levels`` serve no
``current_price``/close field (adding one would break their existing exact-dict-equality tests --
a "Frozen foundations" violation), so this module resolves it itself: the ONE daily bar in
``BarStore.merged_bars(symbol, "1d")`` whose OWN timestamp matches ``basis_as_of`` verbatim (a
value ``compute_tradability`` already returns) -- comparing via the SAME ISO-formatting function on
both sides (never parsing ``basis_as_of`` back to a float, which would risk a microsecond
round-trip mismatch). Never re-deriving WHICH bar is the basis; never touching ``tradability.py``'s
or ``levels.py``'s return shape.

**Best-band selection + cross-symbol rank (assumptions.md iter-3, entry 1).** Per symbol, the
"best" band minimizes ``(class rank A=3/B=2/C=1/null=0 -- DESCENDING preference, distance_bps
ascending, quality_score descending)``, iterating ``compute_tradability``'s own already-deterministic
served band order so an exact tie resolves identically every run (Python's ``min`` keeps the FIRST
of equal-key items). The SAME tuple, plus ``symbol`` ascending as the final tie-break, orders the
screen's final ``rows`` list (TC-14) -- one rule serves both jobs.

**Skip reasons -- exactly two, never conflated.** ``"no_bars"`` = ``compute_tradability``'s own
``no_bar_series_for_symbol: true``; ``"no_basis"`` = a daily series exists but no session resolves
(``basis_as_of: null``, ``bands: []``). Both honest, distinct absences -- a skip row's ``coverage``
still reflects whichever pinned timeframes genuinely have bars (never a fabricated all-false).

**Basis disclosure (goal-desk-iter-9, J-08).** Every RANKED row also carries ``basis_as_of``
(copied VERBATIM from ``result["basis_as_of"]`` -- the SAME value
``_resolve_reference_close_and_history`` already consumes to find the reference close, so this
costs zero additional
``BarStore``/``compute_tradability`` work) and ``basis_age_days`` (a plain calendar-date
difference between that value and the row's own ``as_of``, mirroring ``_distance_bps``'s "plain
arithmetic derivation" style -- see ``_basis_age_days`` below). Skip rows never carry these fields
-- a skip row's own ``reason`` already means no basis resolved at all. A snapshot recorded BEFORE
this addition simply has ranked rows that OMIT these two keys entirely; ``ScreenStore`` performs no
row-shape validation or enrichment (a plain checksum-verified passthrough), so
``GET /research/desk/screen`` serves that absence VERBATIM -- never defaulted, never backfilled
(the append-only rail applies to row CONTENT, not just to the snapshot as a whole).

**History disclosure (goal-desk-iter-15, J-11).** Every RANKED row also carries
``history_sessions`` (the count of daily bars at or before ``basis_as_of``, derived in the SAME
``store.merged_bars(symbol, "1d")`` ascending walk ``_resolve_reference_close_and_history`` already
performs to resolve the reference close -- zero additional ``BarStore`` read) and ``history_start``
(the earliest of those bars' own timestamp, formatted through the identical ``_iso`` function
``basis_as_of`` itself uses). Skip rows never carry these fields, matching the basis-disclosure
precedent exactly. A snapshot recorded BEFORE this addition simply has ranked rows that OMIT these
two keys entirely -- the SAME append-only-row-content discipline the basis fields established:
never defaulted, never backfilled, never present as ``null``.

**Reference-close disclosure (goal-desk-iter-17, J-13).** Every RANKED row also carries
``reference_close`` -- copied VERBATIM from the SAME ``close`` local
``_resolve_reference_close_and_history`` already returns and this module already uses to call
``_select_best_band``/``_distance_bps`` (zero new ``BarStore`` read, zero new accessor, zero
re-derivation of which bar is the basis -- that stays ``compute_tradability``'s and
``_resolve_reference_close_and_history``'s exclusive decision, unchanged). Skip rows never carry
this field, matching the basis/history-disclosure precedent exactly. A snapshot recorded BEFORE
this addition simply has ranked rows that OMIT this key entirely -- the SAME append-only-row-content
discipline the basis/history fields established: never defaulted, never backfilled, never present
as ``null``.

**Opposite-band disclosure (goal-desk-iter-18, J-14; tie-break corrected goal-desk-iter-19).**
Every RANKED row also carries ``opposite_band`` -- the band GENUINELY NEAREST to price on the side
the row's own selected ``best`` band did NOT choose, selected from the SAME ``result["bands"]``
list ``_select_best_band`` already ran over (zero new ``BarStore`` read, zero second
``compute_tradability`` call), ranked by its OWN distance-first tuple -- ``(distance_bps ascending,
class rank DESCENDING, quality_score descending)`` -- via ``min``'s own first-of-tie stability (see
``_select_opposite_band`` below) -- ``None`` when ``compute_tradability`` returned no band on that
other side at all, never an invented or wrong-side band. **goal-desk-iter-19 correction:** iter-18
shipped this selector delegating straight to ``_select_best_band``'s class-first tuple, which
diverged from goal.md J-14 step 1's own distance-first wording on 2 of 63 real screen rows
(HONA/META) -- ``_select_opposite_band`` now carries its OWN tie-break key, distinct from
``_select_best_band``'s (whose same-side, class-first selection is unchanged). It also carries
``bands_by_class`` -- a plain count of ``result["bands"]`` under
the four fixed keys ``"A"``/``"B"``/``"C"``/``"unclassified"`` (a band with ``class: None`` counts
under ``"unclassified"``), all four always present even at zero -- no grade, threshold, or quality
number, a count only. Skip rows never carry either field, matching the basis/history/reference-close
precedent exactly. A snapshot recorded BEFORE this addition simply has ranked rows that OMIT these
two keys entirely -- the SAME append-only-row-content discipline the basis/history/reference-close
fields established: never defaulted, never backfilled (``opposite_band`` ITSELF may legitimately be
recorded as ``null`` on a NEW row, when the canonical return holds no band on the other side -- that
is distinct from the ROW omitting the key entirely, which only a pre-iteration snapshot ever does).

**Wall-composition disclosure (goal-desk-iter-23, J-15).** Every RANKED row also carries
``band_member_count`` (int) and ``band_round_number`` (bool) -- copied VERBATIM from the SAME
``best`` band dict ``_select_best_band`` already returns (that band's own ``member_count``/
``round_number`` keys, ``tradability.py:343`` -- zero second ``compute_tradability`` call, zero
second ``BarStore`` read, zero touch to ``_select_best_band``/``_select_opposite_band``/
``_row_rank_key``) -- plus ``band_member_timeframes`` (dict[str, int]), a plain per-timeframe tally
of that SAME band's own ``members`` list (see ``_band_member_timeframes`` above). The band's own
``members`` list itself is NEVER copied onto the row -- no member price/``touch_count``/``strength``
is copied, only the count/flag/tally. Skip rows never carry any of the three, matching the basis/
history/reference-close/opposite-band precedent exactly. A snapshot recorded BEFORE this addition
simply has ranked rows that OMIT these three keys entirely -- the SAME append-only-row-content
discipline the prior disclosures established: never defaulted, never backfilled, never present as
``null``.

**No new ``Config`` field.** The screen store's directory resolves via ``resolve_desk_screen_dir``
below -- a bare ``TAPEOLOGY_DESK_SCREEN_DIR``-env-var-or-sibling-of-``desk_universe_dir_resolved()``
default (the ``edge_report_cache.resolve_cache_db_path`` pattern) -- never a ``desk_screen_dir``
``Config`` field. This keeps ``config_fingerprint()`` untouched this iteration.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..config import Config
from .bar_index import BarIndex
from .bars import BarStore
from .datasets import DatasetStore
from .desk_coverage import DESK_TOPUP_TIMEFRAMES, get_desk_coverage
from .desk_universe import UniverseStore
from .tradability import compute_tradability

# The two band sides `compute_tradability` serves. Only `RESISTANCE` is referenced by name below
# (`_distance_bps` treats anything else as the support case) -- no `SUPPORT` constant is defined
# since nothing in this module ever compares against it.
RESISTANCE = "resistance"

# Class rank for both the within-symbol "best band" selection and the cross-symbol final rank
# (assumptions.md iter-3 entry 1) -- a band with no inherited class ranks lowest, never highest
# (an honest absence is never preferred over a graded band).
_CLASS_RANK: dict[str | None, int] = {"A": 3, "B": 2, "C": 1, None: 0}

# The screen store's own env-var override (the ``TAPEOLOGY_DESK_UNIVERSE_DIR``/
# ``TAPEOLOGY_EDGE_REPORT_CACHE_DB`` pattern) -- see ``resolve_desk_screen_dir``.
_SCREEN_DIR_ENV = "TAPEOLOGY_DESK_SCREEN_DIR"


class ScreenIntegrityError(Exception):
    """An on-disk screen snapshot file failed its checksum verification on load -- corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated snapshot)."""


class ScreenAlreadyRecorded(Exception):
    """A screen with this EXACT 5-pin key (``screen_date``, ``as_of``, ``universe_snapshot_id``,
    ``config_fingerprint``, ``bar_store_signature``) is already registered. Screen snapshots are
    immutable and append-only -- there is no update/re-record path anywhere in this module; a new
    run under the identical pins reuses the existing snapshot, never a second file."""

    def __init__(self, existing_id: str) -> None:
        self.existing_id = existing_id
        super().__init__(
            f"a screen with this exact key is already recorded as snapshot '{existing_id}' "
            f"-- screen snapshots are immutable and are never re-recorded"
        )


def resolve_desk_screen_dir(desk_universe_dir_resolved: str) -> str:
    """The screen store's directory: the ``TAPEOLOGY_DESK_SCREEN_DIR`` env var if set, else a file
    co-located as a SIBLING of the CALLER's own already-resolved universe directory (the
    ``edge_report_cache.resolve_cache_db_path`` pattern -- takes a plain string, never imports
    ``config.py``'s singleton, so the caller resolves its own universe directory first exactly as
    ``desk_routes.py`` already does). Deliberately NOT a ``desk_screen_dir`` Config field (see the
    module docstring) -- this is an operational storage-location knob, the Constraints' own
    explicit sanction for "worker counts, timeouts, store dirs"."""
    override = os.environ.get(_SCREEN_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "screen")


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum in this module hashes (stable across
    processes: sorted keys, no whitespace) -- the SAME encoding ``research/desk_universe.py`` /
    ``research/bars.py`` hash."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _iso(epoch: float) -> str:
    """The SAME epoch -> ISO formatting ``tradability.py``'s own ``_iso`` uses -- kept as a local
    copy (this project's own convention: each module owns its tiny formatting helper rather than
    sharing one -- see ``bars.py._iso_utc``, ``desk_universe.py._iso_utc_now``) so a reference
    close is matched by comparing ISO strings on BOTH sides, never by parsing ``basis_as_of`` back
    to a float (which would risk a microsecond round-trip mismatch)."""
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def screen_as_of(screen_date: str) -> str:
    """T-6: ``as_of`` is a deterministic function of ``screen_date`` ALONE, never
    ``datetime.now()`` -- see the module docstring's "as_of translation" section."""
    return f"{screen_date}T23:59:59Z"


# --- bar_store_signature (T-4, TC-15) ------------------------------------------------------------


def _bar_store_signature(coverage: dict) -> str:
    """T-4: a checksum over the sorted ``(symbol, timeframe, latest_window_end_utc)`` tuples,
    derived ENTIRELY from an ALREADY-FETCHED ``desk_coverage.get_desk_coverage`` payload -- this
    function receives no store reference of any kind, so it is structurally incapable of issuing a
    ``BarStore`` call (TC-15)."""
    tuples = sorted(
        (member["symbol"], timeframe, member["per_timeframe"][timeframe]["latest_window_end_utc"])
        for member in coverage["members"]
        for timeframe in DESK_TOPUP_TIMEFRAMES
    )
    return _sha256(_canonical(tuples))[:16]


def compute_bar_store_signature(universe_store: UniverseStore, bar_index: BarIndex) -> str:
    """The standalone accessor: fetches coverage (index-only, T-4) and derives the signature from
    it. Exposed separately from ``compute_screen`` so a caller (or a test) can resolve the 5-pin
    key's ``bar_store_signature`` component WITHOUT running the full per-member walk -- the SAME
    cheap-resolution property ``DeskTopupComputeManager.trigger`` already relies on for
    ``pairs_total`` (known synchronously, before any background work starts)."""
    return _bar_store_signature(get_desk_coverage(universe_store, bar_index))


# --- the date-scoped completeness pins (one snapshot per date) ------------------------------------


# The timeframe whose presence decides whether a member is rankable AT ALL: `compute_tradability`
# resolves its basis from the DAILY series alone (`tradability.py`'s `_select_daily_series`), so
# `no_bar_series_for_symbol` -- the `"no_bars"` skip reason -- is precisely "no 1d series".
_DAILY_TIMEFRAME = "1d"


def _clamp_to_as_of(latest_window_end_utc: str | None, as_of: str) -> str | None:
    """``min(latest_window_end_utc, as_of)`` -- an honest ``None`` stays ``None`` (a member with no
    bars at all is never given a fabricated coverage instant).

    Compared as INSTANTS, never as strings: ``bar_index`` records ``window_end_utc`` at mixed
    precision (``2026-07-25T00:00:00Z`` alongside ``2026-07-14T09:32:06.885430Z``), and a lexical
    compare puts ``...T23:59:59.500000Z`` BEFORE ``...T23:59:59Z`` (``'.'`` sorts under ``'Z'``) --
    the one same-second case where string order and chronological order disagree. The RETURNED value
    is always one of the two inputs verbatim, never a reformatted instant, so the signature below
    stays a hash of values this codebase actually wrote."""
    if latest_window_end_utc is None:
        return None
    if _epoch(latest_window_end_utc) <= _epoch(as_of):
        return latest_window_end_utc
    return as_of


def screen_coverage_signature(coverage: dict, as_of: str) -> str:
    """``_bar_store_signature`` CLAMPED to ONE screen's own ``as_of``: a checksum over the sorted
    ``(symbol, timeframe, min(latest_window_end_utc, as_of))`` tuples of an ALREADY-FETCHED
    ``get_desk_coverage`` payload. Like ``_bar_store_signature`` it receives no store reference of
    any kind, so it is structurally incapable of issuing a ``BarStore`` call.

    **Why the clamp is the whole "one snapshot per date" fix.** A screen for date ``D`` can only
    ever consume bars at or before ``as_of(D)``, so bars that arrive AFTER ``D`` cannot change a
    single one of its rows -- yet they DO move ``bar_store_signature`` (which hashes every member's
    unclamped latest instant), and the 5-pin key therefore read every re-run of an older date as a
    brand-new key and wrote a second file for it. Clamped, the value is MONOTONE and settles: while
    bars are still arriving for ``D`` or the sessions before it the signature genuinely moves (a
    re-walk is warranted -- that is the ``63 ranked/38 skipped`` -> ``100/1`` case the live store
    recorded), and once every member's coverage passes ``D`` every tuple is pinned at ``as_of`` and
    no later top-up can ever move it again -- the date settles at exactly one snapshot, forever.

    Recorded as a snapshot's own sixth pin. A snapshot recorded BEFORE this addition simply OMITS
    the key entirely -- the SAME append-only-row-content discipline the row disclosures established
    (never defaulted, never backfilled, never present as ``null``); ``desk_screen_decision`` handles
    that absence explicitly rather than guessing a value for it."""
    tuples = sorted(
        (
            member["symbol"],
            timeframe,
            _clamp_to_as_of(member["per_timeframe"][timeframe]["latest_window_end_utc"], as_of),
        )
        for member in coverage["members"]
        for timeframe in DESK_TOPUP_TIMEFRAMES
    )
    return _sha256(_canonical(tuples))[:16]


def rankable_member_count(coverage: dict) -> int:
    """How many of the latest universe's members COULD rank at all right now: those whose ``1d``
    series exists (see ``_DAILY_TIMEFRAME``). Derived from the SAME already-fetched coverage payload
    -- zero store reads. This is a CEILING, not a prediction: a member with a daily series whose
    every session falls after the screen date resolves no basis and is honestly skipped
    (``"no_basis"``), which is why ``desk_screen_decision`` counts those skips as resolved."""
    return sum(
        1
        for member in coverage["members"]
        if member["per_timeframe"][_DAILY_TIMEFRAME]["has_bars"]
    )


def resolve_screen_pins(universe_store: UniverseStore, bar_index: BarIndex, as_of: str) -> dict:
    """Every cheaply-resolvable pin for ONE screen date, from a SINGLE coverage fetch:
    ``{"bar_store_signature", "screen_coverage_signature", "rankable_member_count"}``. The one
    accessor both the compute path and the pins route call, so neither pays for a second
    (index-only, but still per-member) coverage read and neither can drift from the other. Same
    cheap-resolution property ``compute_bar_store_signature`` already had -- resolvable BEFORE the
    ~100-member walk ever starts."""
    coverage = get_desk_coverage(universe_store, bar_index)
    return {
        "bar_store_signature": _bar_store_signature(coverage),
        "screen_coverage_signature": screen_coverage_signature(coverage, as_of),
        "rankable_member_count": rankable_member_count(coverage),
    }


# --- best-band selection + distance_bps (assumptions.md iter-3, entry 1) -------------------------


def _distance_bps(band: dict, close: float) -> float:
    """``abs(edge_price - close) / close * 10000``, where ``edge_price`` is the near edge to price
    -- ``price_low`` for a resistance band (support from below), ``price_high`` for a support band
    (resistance from above). Correct by construction: ``compute_tradability``'s own side split
    already guarantees ``price_low``/``price_high`` are the closest member on the relevant side."""
    edge_price = band["price_low"] if band["side"] == RESISTANCE else band["price_high"]
    return abs(edge_price - close) / close * 10_000.0


def _select_best_band(bands: list[dict], close: float) -> dict:
    """The symbol's single "best" band: minimizes ``(class rank DESCENDING preference, distance_bps
    ascending, quality_score descending)`` over ``bands`` in ``compute_tradability``'s own served
    order -- ``min`` returns the FIRST of any exactly-tied items, so a tie resolves identically
    every run without a second, invented tie-break."""

    def key(band: dict) -> tuple[int, float, float]:
        return (-_CLASS_RANK[band["class"]], _distance_bps(band, close), -band["quality_score"])

    return min(bands, key=key)


def _select_opposite_band(bands: list[dict], close: float, best_side: str) -> dict | None:
    """The band GENUINELY NEAREST to price on the side ``best_side`` did NOT select
    (goal-desk-iter-18, J-14; tie-break corrected goal-desk-iter-19) -- filtered from the SAME
    ``bands`` list ``_select_best_band`` already ran over, then selected by its OWN distance-first
    tie-break tuple ``(distance_bps ascending, class rank DESCENDING preference, quality_score
    descending)`` via ``min``'s own first-of-tie stability (goal.md J-14 step 1, verbatim: "distance
    ascending, then class rank descending ... then band_score descending, resolved by min's
    first-of-tie stability over compute_tradability's own served order"). Deliberately its OWN
    local key -- NOT a delegation to ``_select_best_band`` (whose class-first tuple governs only the
    row's own same-side selection and is otherwise unchanged) -- because the two rules diverge
    whenever a closer, lower-class opposite-side band competes with a farther, higher-class one
    (iter-18 shipped the class-first delegation, which the iter-18 evaluator measured diverging on
    2 of 63 real screen rows: HONA/META). ``None`` when no band exists on the other side at all --
    never a guessed or wrong-side substitute."""
    opposite_side_bands = [band for band in bands if band["side"] != best_side]
    if not opposite_side_bands:
        return None

    def key(band: dict) -> tuple[float, int, float]:
        return (_distance_bps(band, close), -_CLASS_RANK[band["class"]], -band["quality_score"])

    return min(opposite_side_bands, key=key)


def _band_member_timeframes(members: list[dict]) -> dict[str, int]:
    """A plain per-timeframe tally of a SINGLE band's own ``members`` list (goal-desk-iter-23,
    J-15) -- mirrors ``_bands_by_class``'s "plain dict tally" construction style, but UNLIKE that
    precedent never fabricates a zero for an absent timeframe: only timeframes actually present
    among ``members`` appear as keys at all. Key order is first-seen while walking ``members`` in
    ``compute_tradability``'s own already-sorted order (``tradability.py:364``'s
    ``sorted(..., key=itemgetter("price", "timeframe", "type"))``) -- Python dict insertion order
    is stable, so this order is deterministic and reproducible across runs without any extra sort
    of its own. Values always sum to ``len(members)`` (== the SAME band's own ``member_count``) by
    construction -- every member increments exactly one key."""
    tally: dict[str, int] = {}
    for member in members:
        timeframe = member["timeframe"]
        tally[timeframe] = tally.get(timeframe, 0) + 1
    return tally


def _bands_by_class(bands: list[dict]) -> dict[str, int]:
    """A plain per-class count of ``bands`` (goal-desk-iter-18, J-14) -- a band with ``class: None``
    counts under ``"unclassified"``; all four keys are always present, even at zero. A count only --
    no grade, threshold, weight, or quality number."""
    counts = {"A": 0, "B": 0, "C": 0, "unclassified": 0}
    for band in bands:
        key = band["class"] if band["class"] is not None else "unclassified"
        counts[key] += 1
    return counts


def _row_rank_key(row: dict) -> tuple[int, float, float, str]:
    """The FINAL cross-symbol ``rows`` order (TC-14): the identical selection tuple above, plus
    ``symbol`` ascending as the final tie-break."""
    return (-_CLASS_RANK[row["band_class"]], row["distance_bps"], -row["band_score"], row["symbol"])


# --- reference close price + history disclosure (TC-19; goal-desk-iter-15, J-11) ------------------


def _resolve_reference_close_and_history(
    store: BarStore, symbol: str, basis_as_of: str
) -> tuple[float, int, str]:
    """The ONE daily bar in ``store.merged_bars(symbol, "1d")`` whose own timestamp -- formatted
    through the SAME ``_iso`` function ``tradability.py`` uses -- matches ``basis_as_of`` verbatim,
    PLUS (goal-desk-iter-15, J-11 -- see the module docstring's "History disclosure" section) the
    two history-depth fields derived from that SAME ascending walk: ``history_sessions`` (how many
    bars were walked up to and including the match -- ``merged_bars`` is already ascending, so this
    is simply a running count, never a second pass or a separate counting read) and
    ``history_start`` (the FIRST bar's own timestamp seen in this same walk, formatted through the
    identical ``_iso``). Never re-derives WHICH bar is the basis (that stays
    ``compute_tradability``'s exclusive decision); never touches ``tradability.py``'s or
    ``levels.py``'s return shape; issues exactly the ONE ``store.merged_bars`` call this function
    already issued before J-11 (TC-6 -- zero extra store read).

    Structurally this bar always exists: ``basis_as_of`` is itself derived from a bar
    ``compute_tradability`` read via this EXACT accessor (``tradability.py``'s own
    ``_select_daily_series`` calls ``BarStore.merged_bars(symbol, "1d")``), and the store is
    immutable between the two reads within one screen computation -- a missing match is an
    unreachable internal-invariant failure, surfaced loudly (never a fabricated close or history)."""
    history_sessions = 0
    history_start: str | None = None
    for bar in store.merged_bars(symbol, "1d"):
        history_sessions += 1
        bar_iso = _iso(bar.epoch)
        if history_start is None:
            history_start = bar_iso
        if bar_iso == basis_as_of:
            return bar.close, history_sessions, history_start
    raise RuntimeError(
        f"internal invariant violated: no daily bar for {symbol!r} matches basis_as_of "
        f"{basis_as_of!r} -- compute_tradability's own basis bar must always be present in "
        f"merged_bars(symbol, '1d')"
    )


# --- basis disclosure (goal-desk-iter-9, J-08) -----------------------------------------------------


def _basis_age_days(basis_as_of: str, as_of: str) -> int:
    """``basis_age_days``: a plain calendar-date difference between ``basis_as_of`` (a ranked row's
    own reference session -- ``compute_tradability``'s own already-resolved value, zero new read)
    and ``as_of`` (the screen's own as-of) -- the ``_distance_bps`` precedent's "plain arithmetic
    derivation" style, never a second bar read. Calendar DATES, not a raw hour delta:
    ``basis_as_of`` carries the prior session's own bar-timestamp time-of-day (e.g. ``04:00:00``
    UTC) while ``as_of`` is always ``screen_as_of``'s fixed ``23:59:59Z`` -- comparing the raw
    instants would inflate the count by a fraction of a day for every symbol, so both sides are
    reduced to a UTC calendar date first, the SAME ``.replace("Z", "+00:00")`` parsing style
    ``_epoch`` above already uses."""
    basis_date = datetime.fromisoformat(basis_as_of.replace("Z", "+00:00")).date()
    as_of_date = datetime.fromisoformat(as_of.replace("Z", "+00:00")).date()
    return (as_of_date - basis_date).days


# --- the row computation (the SOLE walker; the manager and the CLI both call this) ----------------


def compute_screen(
    universe_store: UniverseStore,
    bar_store: BarStore,
    bar_index: BarIndex,
    dataset_store: DatasetStore,
    config: Config,
    screen_date: str,
    *,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> dict:
    """Walk the LATEST universe snapshot's members, as of ``screen_date``'s session close,
    computing one ranked row (or an honest skip) per member via the canonical owners
    (``compute_tradability``, ``desk_coverage.get_desk_coverage``, ``DatasetStore.list``). Returns
    the full snapshot content MINUS the store-assigned ``id``/``created_utc`` (``ScreenStore.record``
    assigns those): ``{screen_date, as_of, universe_snapshot_id, config_fingerprint,
    bar_store_signature, rows, skipped}``. Each RANKED row additionally carries ``basis_as_of``/
    ``basis_age_days`` (goal-desk-iter-9, J-08), ``history_sessions``/``history_start``
    (goal-desk-iter-15, J-11), ``reference_close`` (goal-desk-iter-17, J-13),
    ``opposite_band``/``bands_by_class`` (goal-desk-iter-18, J-14), and ``band_member_count``/
    ``band_round_number``/``band_member_timeframes`` (goal-desk-iter-23, J-15) -- see the module
    docstring's "Basis disclosure", "History disclosure", "Reference-close disclosure",
    "Opposite-band disclosure", and "Wall-composition disclosure" sections; skip rows never carry
    any of the ten.

    ``progress``, if given, is called after EACH member with ``{"symbol": symbol}`` (the caller
    tracks its own done/total counters -- the ``desk_topup_compute.run_topup`` precedent).
    ``should_abort``, if given and it returns ``True`` before a member starts, stops the walk early
    -- ``rows``/``skipped`` are simply shorter than the full member list; a cooperative stop, never
    a raise. No universe snapshot registered yet -> an honest empty walk (``universe_snapshot_id``
    is ``None``, both lists empty) -- never an error."""
    as_of = screen_as_of(screen_date)
    as_of_epoch = _epoch(as_of)

    universe_records, _universe_errors = universe_store.list()
    universe_snapshot_id = universe_records[-1]["id"] if universe_records else None
    members = list(universe_records[-1]["members"]) if universe_records else []

    coverage_payload = get_desk_coverage(universe_store, bar_index)
    coverage_by_symbol = {m["symbol"]: m["per_timeframe"] for m in coverage_payload["members"]}
    bar_store_signature = _bar_store_signature(coverage_payload)
    coverage_signature = screen_coverage_signature(coverage_payload, as_of)

    dataset_records, _dataset_errors = dataset_store.list()
    tick_symbols = {meta["symbol"] for meta in dataset_records}

    config_fingerprint = config.config_fingerprint()

    rows: list[dict] = []
    skipped: list[dict] = []
    for symbol in members:
        if should_abort is not None and should_abort():
            break
        coverage = coverage_by_symbol[symbol]
        tick_evidence = symbol in tick_symbols
        result = compute_tradability(bar_store, symbol, as_of_epoch, config)

        if result["no_bar_series_for_symbol"]:
            skipped.append(
                {"symbol": symbol, "skipped": True, "reason": "no_bars",
                 "coverage": coverage, "tick_evidence": tick_evidence}
            )
        elif result["basis_as_of"] is None:
            skipped.append(
                {"symbol": symbol, "skipped": True, "reason": "no_basis",
                 "coverage": coverage, "tick_evidence": tick_evidence}
            )
        else:
            close, history_sessions, history_start = _resolve_reference_close_and_history(
                bar_store, symbol, result["basis_as_of"]
            )
            best = _select_best_band(result["bands"], close)
            opposite = _select_opposite_band(result["bands"], close, best["side"])
            rows.append(
                {
                    "symbol": symbol,
                    "side": best["side"],
                    "band_class": best["class"],
                    "distance_bps": _distance_bps(best, close),
                    "band_score": best["quality_score"],
                    "price_low": best["price_low"],
                    "price_high": best["price_high"],
                    "coverage": coverage,
                    "tick_evidence": tick_evidence,
                    "basis_as_of": result["basis_as_of"],
                    "basis_age_days": _basis_age_days(result["basis_as_of"], as_of),
                    "history_sessions": history_sessions,
                    "history_start": history_start,
                    "reference_close": close,
                    "opposite_band": (
                        {
                            "side": opposite["side"],
                            "band_class": opposite["class"],
                            "price_low": opposite["price_low"],
                            "price_high": opposite["price_high"],
                            "band_score": opposite["quality_score"],
                            "distance_bps": _distance_bps(opposite, close),
                        }
                        if opposite is not None
                        else None
                    ),
                    "bands_by_class": _bands_by_class(result["bands"]),
                    "band_member_count": best["member_count"],
                    "band_round_number": best["round_number"],
                    "band_member_timeframes": _band_member_timeframes(best["members"]),
                }
            )

        if progress is not None:
            progress({"symbol": symbol})

    rows.sort(key=_row_rank_key)
    # `skipped` is already symbol-ascending by construction (walked in `members`' own sorted
    # order, per `desk_universe.UniverseStore.record`'s `sorted(normalized_to_raw)` -- never
    # reordered here, so no redundant second sort is needed.

    return {
        "screen_date": screen_date,
        "as_of": as_of,
        "universe_snapshot_id": universe_snapshot_id,
        "config_fingerprint": config_fingerprint,
        "bar_store_signature": bar_store_signature,
        "screen_coverage_signature": coverage_signature,
        "rows": rows,
        "skipped": skipped,
    }


# --- the store (frozen JSON, one file per snapshot, structurally immutable) ----------------------


class ScreenStore:
    """File-based store rooted at the config-owned screen directory -- the ONE reader/writer.
    Mirrors ``desk_universe.UniverseStore``'s discipline exactly: every load verifies a
    whole-record checksum (``ScreenIntegrityError`` on any mismatch); ``record`` refuses an
    identical 5-pin key (``ScreenAlreadyRecorded``, never a second file for the same key).

    **One snapshot per date.** The immutability guarantee is narrower than it was: no method
    rewrites a file IN PLACE (``record`` still only ever creates), but a date is no longer allowed
    to accumulate copies. ``prune_superseded`` is the ONE removal path -- it deletes the OTHER files
    for a date once a fresher snapshot for that date has been written, and can never touch the file
    it was told to keep. The compute path always writes the replacement BEFORE pruning, so an
    interrupted supersede leaves two copies (the old behaviour) and never zero."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, screen_id: str) -> Path:
        return self._root / f"{screen_id}.json"

    def _load(self, path: Path) -> dict:
        """Load ONE snapshot file, verifying its whole-record checksum. Raises
        ``ScreenIntegrityError`` for any parse/shape/checksum failure -- explicit, never silent."""
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise ScreenIntegrityError(
                f"screen snapshot file '{path.name}' is not parseable ({exc}) -- corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise ScreenIntegrityError(
                f"screen snapshot file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise ScreenIntegrityError(
                f"screen snapshot file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise ScreenIntegrityError(
                f"screen snapshot file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every registered screen's full content (each file verified), oldest first, plus an
        EXPLICIT error row per file that failed verification -- a corrupt file is surfaced, never
        silently hidden and never served as data. Fresh copies of the nested ``rows``/``skipped``
        lists on every call (the ``desk_universe.UniverseStore.list`` per-row-copy discipline), so
        a caller mutating a returned record can never poison a later read."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                meta = self._load(path)
                records.append(
                    {**meta, "rows": [dict(r) for r in meta["rows"]], "skipped": [dict(s) for s in meta["skipped"]]}
                )
            except ScreenIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
        return records, errors

    def find_by_key(
        self, screen_date: str, as_of: str, universe_snapshot_id: str | None,
        config_fingerprint: str, bar_store_signature: str,
    ) -> dict | None:
        """The already-recorded snapshot matching this EXACT 5-pin key, or ``None`` -- the
        append-only dedup lookup ``record`` itself uses, also usable standalone by a caller that
        wants to check before paying for a walk."""
        records, _errors = self.list()
        key = (screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature)
        for record in records:
            record_key = (
                record["screen_date"], record["as_of"], record["universe_snapshot_id"],
                record["config_fingerprint"], record["bar_store_signature"],
            )
            if record_key == key:
                return record
        return None

    def find_by_date(self, screen_date: str) -> dict | None:
        """The NEWEST registered snapshot for one ``screen_date``, or ``None``. After
        ``prune_superseded`` there is at most one per date anyway; "newest" is the honest tie-break
        while a date still carries pre-cleanup copies (``list`` is already ``created_utc``-ascending,
        so the last match is the newest). This -- not ``find_by_key`` -- is what
        ``desk_screen_decision`` asks "is this date already complete?" about."""
        records, _errors = self.list()
        matching = [record for record in records if record["screen_date"] == screen_date]
        return matching[-1] if matching else None

    def prune_superseded(self, screen_date: str, keep_id: str) -> list[str]:
        """Delete every OTHER registered snapshot for ``screen_date``, keeping ``keep_id``. Returns
        the removed ids (oldest first) -- an empty list when the date already held only the one.

        The store's ONE removal path, and deliberately a narrow one:

        * it refuses (``ValueError``) when ``keep_id`` is not itself a registered snapshot for this
          date -- a supersede can only ever run AFTER its replacement is safely on disk, so a
          missing ``keep_id`` means the caller is about to delete a date's last copy;
        * it never touches ``keep_id``'s own file, and never any date but this one;
        * a file that failed its integrity check is not registered (``list`` withholds it and
          surfaces it in ``errors``), so it is never in the removal set either -- a damaged snapshot
          keeps being surfaced honestly rather than being quietly swept away by a supersede."""
        records, _errors = self.list()
        matching = [record for record in records if record["screen_date"] == screen_date]
        if not any(record["id"] == keep_id for record in matching):
            raise ValueError(
                f"refusing to prune screen date {screen_date!r}: the snapshot to keep "
                f"({keep_id!r}) is not registered for that date -- a supersede runs only after its "
                f"replacement is on disk, never before"
            )
        removed: list[str] = []
        for record in matching:
            if record["id"] == keep_id:
                continue
            self._path(record["id"]).unlink()
            removed.append(record["id"])
        return removed

    def record(
        self,
        *,
        screen_date: str,
        as_of: str,
        universe_snapshot_id: str | None,
        config_fingerprint: str,
        bar_store_signature: str,
        rows: list[dict],
        skipped: list[dict],
        screen_coverage_signature: str | None = None,
    ) -> dict:
        """Persist ONE new screen snapshot (record + register in a single explicit action). A
        snapshot already registered under this EXACT 5-pin key raises the 409-style
        ``ScreenAlreadyRecorded`` (there is no update/re-record path at all -- a recorded file is
        never rewritten). A file already sitting at this key's own deterministic path but failing
        its integrity check raises ``ScreenIntegrityError`` -- never a silent overwrite (see below).

        ``screen_coverage_signature`` is the date-scoped completeness pin (see the function of that
        name above). It is NOT part of the key or the id checksum -- it is a pure function of the
        SAME coverage payload ``bar_store_signature`` is derived from, plus ``as_of`` (itself a pure
        function of ``screen_date``), so it is fully determined by the five pins and adds no
        distinguishing power. Omitting it (the default) writes a snapshot in the pre-addition shape
        -- the key ABSENT from ``meta`` entirely, never ``null`` -- which is what every snapshot
        recorded before this addition looks like on disk and what a test planting a legacy record
        wants; the compute path always passes a real value."""
        existing = self.find_by_key(
            screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature
        )
        if existing is not None:
            raise ScreenAlreadyRecorded(existing["id"])

        checksum = _sha256(
            _canonical([screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature])
        )[:12]
        screen_id = f"screen-{screen_date}-{checksum}"
        # A file already at this key's own path, with `find_by_key` reporting no match, means
        # exactly one thing: that file failed its integrity check (`list` surfaces it in
        # `integrity_errors` and withholds it from `records`), because the path is a pure function
        # of the 5-pin key we just searched by. Writing here would SILENTLY overwrite a
        # corrupted/tampered snapshot and erase the very integrity error the store had been
        # honestly surfacing -- both a rewrite ("snapshots are append-only ... never rewritten")
        # and a silence. Refuse loudly instead; a human decides what happens to the damaged file.
        if self._path(screen_id).exists():
            raise ScreenIntegrityError(
                f"screen snapshot file '{self._path(screen_id).name}' already exists on disk but "
                f"failed its integrity check -- refusing to overwrite it (screen snapshots are "
                f"append-only and are never rewritten). Move or remove the damaged file "
                f"explicitly before re-recording this key."
            )
        meta = {
            "id": screen_id,
            "screen_date": screen_date,
            "as_of": as_of,
            "universe_snapshot_id": universe_snapshot_id,
            "config_fingerprint": config_fingerprint,
            "bar_store_signature": bar_store_signature,
            "created_utc": _iso_utc_now(),
            "rows": list(rows),
            "skipped": list(skipped),
        }
        if screen_coverage_signature is not None:
            meta["screen_coverage_signature"] = screen_coverage_signature
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(screen_id).write_text(json.dumps(payload))
        return dict(meta)
