"""The touch-event scanner + case-study registry (era-5B capability 2, J-02) -- Data Contract row
"Touch events + reaction labels (`rejected`/`broke`/`chopped`) + forward returns + case registry"'s
SOLE owner.

THIS MODULE is a scanner over the frozen ``compute_tradability`` output (era-5B J-01), never a
second map/levels engine: for each config-owned panel symbol and each SESSION present in that
symbol's stored ``"5m"`` bar series, it calls ``compute_tradability`` ONCE to obtain that session's
own morning tradable map (bands read VERBATIM -- no pivot/zone/band re-derivation of any kind),
then scans that session's OWN 5m bars for band touches, classifies each touch's reaction, and
records forward returns. ``GET /research/setups`` / ``GET /research/setups/{id}`` and the
read-only MCP ``setups`` tool all serve this module's output VERBATIM (single source of truth --
no second computation path, mirroring ``tradability.py``'s own MCP/REST discipline).

Two DIFFERENT "setup" vocabularies exist in this codebase -- READ THIS before touching either
module. ``research/studies.py`` owns an UNRELATED, pre-existing concept: a live TAPE-ARMING
OCCURRENCE (``level_break`` / ``failed_move_fade`` / ``absorption_reversal`` / ``trend_continuation``)
checked against the frozen ``TapeEngine``'s live STATE. THIS module's "event" is a completely
different thing: a STORED 2026-dated 5m bar's OHLC range intersecting a tradable-map BAND, checked
purely against historical bars -- no engine, no live state, no tape at all (a recorded event's
``tape_timeline`` field is joined on by ``enrich_with_tape_timeline`` below, era-5B J-03; an event
with no recorded dataset keeps an honestly empty ``tape_timeline``).
The two vocabularies happen to share the English word "setup"; they are never conflated, never
share config, and never share code.

**The central per-session risk (why ``as_of`` must be threaded PER SESSION).** A session's own
morning map must derive ONLY from bars completed strictly before that session -- the identical
morning-markup discipline ``compute_tradability`` itself enforces internally via its own
``_resolve_basis`` / ``_PriorSessionBarView``. This module's OWN, narrower obligation is choosing
the RIGHT ``as_of_epoch`` to pass ``compute_tradability`` for EACH session it walks: this module
uses that session's OWN first stored 5m bar's epoch (``_session_date`` of any bar strictly inside a
session's calendar date resolves the SAME basis, since ``compute_tradability``'s own resolver keys
off the calendar date alone -- never the clock time within it). A single SHARED/fixed ``as_of``
across the whole walk (e.g. one derived from the scan's overall latest date) would silently hand
EVERY session the SAME (latest) map -- a critical no-lookahead violation one level up from the
``_PriorSessionBarView`` hazard ``tradability.py`` already guards internally. Proven by
``tests/test_setups.py``'s consecutive-session no-lookahead test: shifting how far a scan's
underlying store extends (removing later sessions from the ``"5m"`` series) never changes an
already-emitted earlier event -- the ``test_tradability.py``
``test_no_lookahead_bars_after_the_basis_never_affect_the_result`` technique, applied one layer up.

**Touch detection + the re-arm rule.** Within one session's own 5m bars (chronological order), a
band is "touched" by the first bar whose ``[low, high]`` range intersects the band's
``[price_low, price_high]`` (the identical range-intersection test ``tradability.py``'s own
``_recency_score`` uses). Once touched, the band does not "re-arm" for a NEW touch event until
price fully exits the band's range on some LATER bar -- and even then, at most
``Config.setups_max_events_per_band_per_session`` events are ever emitted for one (band, session)
pair (pinned at 1 by the DoD's own "first touch per band per session" wording: a choppy afternoon
bouncing on the same band never double- or triple-counts). A session whose morning map is empty
(``compute_tradability`` returns no bands -- no derivable basis, or no series at all) contributes
NO events for that session, never a fabricated one; a symbol with no ``"5m"`` series at all
contributes no events for any session.

**Reaction classification + forward returns (config-owned, pre-registered).** From the touch bar
forward (STRICTLY after it -- never including the touch bar itself), this module reads the closing
price ``Config.setups_forward_return_horizons_bars[0]`` bars later (capped at the last bar actually
in the store -- never lookahead beyond what is stored, and never fabricated when the store runs
out) and compares it against each band edge widened by ``Config.setups_reaction_threshold_bps``:
closing decisively beyond the FAR edge (through the level, in the touch's own direction) reads
``broke``; decisively back beyond the NEAR edge (failing back off the level) reads ``rejected``;
neither reads ``chopped`` -- a deliberately CLOSE-based (never a fleeting intrabar wick, never
volume-weighted) test, so a single loud, shallow poke that fully reverts by the reaction horizon
reads ``chopped``, not ``rejected`` (``tests/test_setups.py``'s intraday-density regression guard).
An event with NO bar at all after the touch (the touch is the very last bar anywhere in the store)
is honestly excluded -- there is nothing to react with, so nothing is fabricated. Forward returns
are reported at EVERY configured horizon as ``(close_at_horizon - touch_bar.close) / touch_bar.close``;
a horizon that reaches past the end of the store reports an honest ``None`` for that one field,
never a fabricated number -- the event itself is still emitted as long as AT LEAST the first
(shortest, reaction-defining) horizon has a real bar to read.

**Deterministic + honest.** Pure function of the store's stored bars + config: identical inputs
produce byte-identical output (every event carries a STABLE id -- a sha256 digest of its own
identity fields, never ``uuid4`` or any other unseeded/wall-clock source -- and the served list is
sorted by an explicit total order). Panel symbols are walked in the config-owned order; sessions
within a symbol are walked oldest-first; each session's bands are read in ``compute_tradability``'s
own served order.

**Tape-at-the-wall join (era-5B capability 4, J-03).** ``enrich_with_tape_timeline`` -- called
ONLY from the ``GET /research/setups/{id}`` route, NEVER from ``compute_setups``'s shared scan
loop above (a per-event ``DatasetStore`` lookup inside that loop would add an O(events) dataset
scan to the already-slow full-panel list route, and would entangle the join with the scan's own
determinism guarantees) -- matches a recorded ``DatasetStore`` dataset to ONE event by ``symbol``
equality plus the dataset's own ``[window_start_utc, window_end_utc]`` containing the event's
``touch_ts`` (``DatasetStore``'s meta schema is frozen with no "associated event" field, so this
containment test is the only available join key; ties -- more than one dataset's window covering
the same touch -- break on the earliest ``created_utc``, then id, for determinism). A match is
replayed through the FROZEN ``TapeEngine`` via ``DatasetStore.replay`` VERBATIM -- this module
never constructs a second engine and never reimplements classification -- and the per-tick
snapshot stream is collapsed to STATE-TRANSITION entries only, mirroring
``engine.history.HistoryBuffer.note_state``'s own idiom (a marker only when ``tape_state``
CHANGES) rather than one row per raw tick, and -- the SAME idiom -- a transition into a state
outside ``Config.history_marker_states`` (i.e. ``unclear``) is not marked: an "uncertain" read is
not itself a meaningful "the tape said X" call, and reusing ``history_marker_states`` (rather than
a second hardcoded "unclear" literal) keeps "which states count as meaningful" owned in exactly
one place. Each recorded window's replay uses LOGICAL per-window timestamps (``HistoricalProvider``'s
"logical, not wall-clock" scheme), so a timeline entry's real UTC instant is reconstructed as the
dataset's OWN stamped ``epoch_anchor`` plus the snapshot's logical timestamp -- the identical
``epoch_anchor + logical_ts`` reconstruction ``serializers.serialize_history``'s chart projection
already uses, never a raw logical offset (which would misread as a bogus near-1970 date). An event
with no matching recorded dataset keeps its honestly empty ``tape_timeline`` -- never fabricated.

**B1 -- additive recency-boundary disclosure (era-5B iter-5).** A touch inside the store's MOST
RECENT stored session may not yet have ``Config.setups_forward_return_horizons_bars[0]`` bars of
history past it -- the store simply has not accumulated that much real data yet, the SAME shape
every freshly-fetched panel symbol's latest session is in until enough later bars arrive. Rather
than silently pairing a definitive ``reaction`` label with a horizon-0 ``forward_returns`` entry of
``None`` with no explanation, every event additively carries ``effective_reaction_horizon_bars``
(the bar count the reaction close was ACTUALLY read at -- equal to the full configured
``horizons[0]`` whenever the store held enough bars) and ``reaction_boundary_truncated`` (``True``
exactly when it did not). Neither field ever changes ``reaction`` itself or excludes the event --
see ``_reaction_and_forward_returns``'s own docstring for the exact boundary condition.

**B3 -- a process-local memoized scan (era-5B iter-5; made atomic in iter-6; gained a durable
sibling tier at era-fast_wall J-06).** ``GET /research/setups``, ``GET /research/setups/{id}``, and
``edge_report.run_strategy_comparison_report`` each call ``compute_setups(store, config)``
independently; on the populated 12-symbol panel the underlying scan takes minutes, so without a
cache a single page load could trigger it multiple times over. The PUBLIC ``compute_setups`` below
is now a two-tier, byte-identical memoizing wrapper around the real scan (renamed
``_run_full_panel_scan``) -- see its own docstring for the full caching contract (content-keyed,
rebuildable, never a second source of truth -- the ``bar_index.py`` precedent). iter-6 (era-5B)
hardened the in-process hot-slot publish to a single atomic ``(key, result)`` tuple rebind (see the
``_SCAN_CACHE`` block comment below) once that iteration became the first caller to fire all three
consumers concurrently from one browser page load. era-fast_wall J-06 additionally gave
``compute_setups`` a DURABLE sibling tier (``setups_scan_cache.py``'s ``SetupsScanCache``, consulted
only on a hot-slot miss) so a backend restart -- or simply a freshly-constructed but content-equal
``Config`` object -- never re-pays the scan either; see ``compute_setups``'s own docstring below for
the exact three-tier order.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone

from ..config import Config
from ..providers.adapters.base import RawBar
from .bars import BarStore
from .datasets import DatasetStore, parse_utc_epoch
from .edge_report_cache import _config_content_hash
from .setups_scan_cache import SetupsScanCache, resolve_scan_cache_db_path, scan_cache_key
from .tradability import RESISTANCE, SUPPORT, compute_tradability

REJECTED = "rejected"
BROKE = "broke"
CHOPPED = "chopped"

# The ONE stored timeframe this scanner ever reads bars from directly (compute_tradability, called
# per session, reads whatever OTHER timeframes -- "1d" for basis resolution, plus any others stored
# -- it needs on its own). Not a Config field: it is a structural fact about WHICH series this
# module walks session-by-session (the goal.md-mandated granularity), never a tunable research
# parameter -- the identical ``tradability.py`` rationale for ``_DAILY_TIMEFRAME``.
_SCAN_TIMEFRAME = "5m"


def _iso(epoch: float) -> str:
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _session_date(epoch: float) -> date:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).date()


def _select_5m_series(store: BarStore, symbol: str) -> list[RawBar] | None:
    """The winning ``"5m"`` series for ``symbol``, sorted ascending by epoch -- the EXACT SAME
    most-recently-created tie-break ``tradability.py``'s own ``_select_daily_series`` uses (applied
    here to ``"5m"`` instead of ``"1d"``), so a symbol with more than one registered ``"5m"`` series
    resolves to one unambiguous choice. ``None`` when no ``"5m"`` series exists for ``symbol`` at
    all (no series, or series but none is ``"5m"``) -- an honest "nothing to scan", never a crash."""
    records, _integrity_errors = store.list()
    chosen: dict | None = None
    for record in records:
        if record["symbol"] != symbol or record["timeframe"] != _SCAN_TIMEFRAME:
            continue
        if chosen is None or record["created_utc"] > chosen["created_utc"]:
            chosen = record
    if chosen is None:
        return None
    return sorted(store.load_bars(chosen["id"]), key=lambda b: b.epoch)


def _group_sessions(bars: list[RawBar]) -> list[tuple[date, int, list[RawBar]]]:
    """Groups ALREADY-ascending-sorted ``bars`` into ``(session_date, start_index, session_bars)``
    triples, oldest session first. ``start_index`` is that session's first bar's position in the
    FULL ``bars`` list -- carried through so reaction/forward-return lookups can read bars from
    LATER sessions without a second pass over the series."""
    sessions: list[tuple[date, int, list[RawBar]]] = []
    current_date: date | None = None
    current_bars: list[RawBar] = []
    current_start = 0
    for index, bar in enumerate(bars):
        bar_date = _session_date(bar.epoch)
        if bar_date != current_date:
            if current_bars:
                sessions.append((current_date, current_start, current_bars))
            current_date = bar_date
            current_start = index
            current_bars = []
        current_bars.append(bar)
    if current_bars:
        sessions.append((current_date, current_start, current_bars))
    return sessions


def _touches(price_low: float, price_high: float, session_bars: list[RawBar], max_events: int) -> list[int]:
    """LOCAL (within-``session_bars``) indices of up to ``max_events`` band touches. A touch is any
    bar whose ``[low, high]`` range intersects ``[price_low, price_high]``; the band re-arms for
    the NEXT touch only once a LATER bar fully exits that range (never two touches counted while
    price is still inside/overlapping the band from the prior one)."""
    indices: list[int] = []
    armed = True
    for index, bar in enumerate(session_bars):
        inside = bar.low <= price_high and bar.high >= price_low
        if inside and armed:
            indices.append(index)
            armed = False
            if len(indices) >= max_events:
                break
        elif not inside:
            armed = True
    return indices


def _reaction_and_forward_returns(
    all_bars: list[RawBar], touch_index: int, side: str, price_low: float, price_high: float, config: Config,
) -> tuple[str, list[dict], int, bool] | None:
    """The touch's reaction label + forward-return list + the B1 recency-boundary disclosure, or
    ``None`` when NO bar at all follows the touch (nothing to react with -- the event is excluded,
    never fabricated). Reaction is decided from the CLOSE at the shortest configured horizon (never
    an intrabar wick, never volume) versus each band edge widened by
    ``Config.setups_reaction_threshold_bps``; every configured horizon is then reported, honestly
    ``None`` for any horizon reaching past the end of the store.

    **B1 -- additive recency-boundary disclosure (era-5B iter-5).** When the store does not YET
    hold ``horizons[0]`` bars past the touch (a touch inside the most-recent stored session), the
    reaction is still read from whatever close IS available -- honest, never suppressed -- but its
    horizon is a TRUNCATED sub-horizon of the configured one. This is disclosed, never hidden: the
    returned ``effective_reaction_horizon_bars`` is the bar count the reaction close was ACTUALLY
    read at (``== horizons[0]`` whenever untruncated), and ``reaction_boundary_truncated`` is
    ``True`` exactly when ``touch_index + horizons[0] >= len(all_bars)``. Neither value ever
    changes the ``reaction`` label itself -- a caller decides how to present a truncated-horizon
    label; this function only discloses the truncation honestly."""
    if touch_index >= len(all_bars) - 1:
        return None
    horizons = config.setups_forward_return_horizons_bars
    touch_close = all_bars[touch_index].close
    threshold = config.setups_reaction_threshold_bps / 10_000.0

    reaction_index = min(touch_index + horizons[0], len(all_bars) - 1)
    effective_reaction_horizon_bars = reaction_index - touch_index
    reaction_boundary_truncated = touch_index + horizons[0] >= len(all_bars)
    reaction_close = all_bars[reaction_index].close
    if side == RESISTANCE:
        broke_level = price_high * (1.0 + threshold)
        reject_level = price_low * (1.0 - threshold)
        far_break, far_reject = reaction_close >= broke_level, reaction_close <= reject_level
    else:
        assert side == SUPPORT
        broke_level = price_low * (1.0 - threshold)
        reject_level = price_high * (1.0 + threshold)
        far_break, far_reject = reaction_close <= broke_level, reaction_close >= reject_level
    reaction = BROKE if far_break else REJECTED if far_reject else CHOPPED

    forward_returns: list[dict] = []
    for horizon in horizons:
        target_index = touch_index + horizon
        if target_index >= len(all_bars):
            forward_returns.append({"horizon_bars": horizon, "return_fraction": None})
        else:
            forward_returns.append({
                "horizon_bars": horizon,
                "return_fraction": (all_bars[target_index].close - touch_close) / touch_close,
            })
    return reaction, forward_returns, effective_reaction_horizon_bars, reaction_boundary_truncated


def _event_id(symbol: str, session_date_iso: str, band: dict, touch_ts: str) -> str:
    """A STABLE, deterministic id (sha256 of the event's own identity fields) -- never ``uuid4`` or
    any other unseeded/wall-clock source, so repeat scans reproduce the identical id for the
    identical event (the determinism DoD clause)."""
    payload = "|".join((
        symbol, session_date_iso, band["side"],
        repr(band["price_low"]), repr(band["price_high"]), touch_ts,
    ))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _event(
    symbol: str, session_date_value: date, band: dict, touch_bar: RawBar, reaction: str, forward_returns: list[dict],
    effective_reaction_horizon_bars: int, reaction_boundary_truncated: bool,
) -> dict:
    session_date_iso = session_date_value.isoformat()
    touch_ts = _iso(touch_bar.epoch)
    return {
        "id": _event_id(symbol, session_date_iso, band, touch_ts),
        "symbol": symbol,
        "session_date": session_date_iso,
        "band": band,
        "touch_ts": touch_ts,
        "touch_open": touch_bar.open,
        "touch_high": touch_bar.high,
        "touch_low": touch_bar.low,
        "touch_close": touch_bar.close,
        "touch_volume": touch_bar.volume,
        "reaction": reaction,
        "forward_returns": forward_returns,
        # B1 (era-5B iter-5): additive recency-boundary disclosure -- see
        # `_reaction_and_forward_returns`'s own docstring. Never mutates `reaction` above, never
        # excludes an event -- a truncated-horizon label is disclosed, not suppressed.
        "effective_reaction_horizon_bars": effective_reaction_horizon_bars,
        "reaction_boundary_truncated": reaction_boundary_truncated,
        # Present-but-empty until J-03 records the real tape and joins its five-state timeline
        # onto this event (goal.md capability 4) -- never omitted, never fabricated meanwhile.
        "tape_timeline": [],
    }


def _event_sort_key(event: dict) -> tuple:
    """A total order over the served list (symbol, session, side, price, touch time) so the JSON is
    never perturbed by scan-order happenstance -- the ``levels.py``/``tradability.py``
    byte-identical-determinism discipline."""
    return (
        event["symbol"], event["session_date"], event["band"]["side"],
        event["band"]["price_low"], event["touch_ts"],
    )


# --- B3 (era-5B iter-5): a process-local, rebuildable, byte-identical memoization of the ONE
# full-panel scan `compute_setups` performs -- see the module docstring's own B3 note.
# `GET /research/setups`, `GET /research/setups/{id}`, and
# `edge_report.run_strategy_comparison_report` each call `compute_setups(store, config)`
# independently (routes.py's `list_setups`/`get_setup`, `edge_report.py`'s
# `run_strategy_comparison_report`); on the populated 12-symbol store the underlying scan takes
# minutes, so without this layer a single page load could trigger it several times over, well past
# browser-QA timeouts. This is the SAME "rebuildable accelerator, never a second source of truth"
# contract `bar_index.py` lives under (see that module's own docstring). THIS slot itself stays
# PROCESS-LOCAL and in-memory only -- never SQLite/disk-persisted, and never itself read by anything
# outside this module -- but era-fast_wall J-06 gave `compute_setups` a DURABLE sibling tier
# (`setups_scan_cache.py`'s `SetupsScanCache`, consulted only on a miss here) so a process restart
# no longer loses everything this slot remembered; see `compute_setups`'s own docstring below for
# the full three-tier order. `compute_setups`'s own signature is UNCHANGED, so every caller
# (routes.py, edge_report.py) needs zero changes -- only ITS body differs (a cache check wrapping
# the real scan, renamed `_run_full_panel_scan` below).
#
# Keyed on (a) a deterministic hash of the config's ENTIRE field CONTENT (era-fast_wall J-06 --
# `edge_report_cache._config_content_hash`, imported and reused verbatim, never re-derived a second
# time; NOT `config.config_fingerprint()` alone, whose own documented exclusion set drops exactly the
# `setups_*`/`tradability_*`/`sr_*` families this scan and `compute_tradability` read -- see
# `edge_report_cache.py`'s "why it is FOUR parts" docstring section for the identical reasoning
# proven necessary for the sibling report cache) and (b) a deterministic content signature over
# `store.list()` (sorted `(symbol, timeframe, id, checksum)` tuples -- `bars.py` already exposes a
# per-series `checksum` in every list record, so this reuses an existing value rather than hashing
# raw bars). Content-hashing `config` (rather than the OLD `id(config)` identity key, which never
# survived a restart and never recognised a freshly-constructed but content-equal `Config` as the
# SAME scan) is itself now possible because `_config_content_hash` uses `dataclasses.asdict` + a
# canonical-JSON encoding rather than hashing `Config` directly (`Config` carries plain `dict`
# fields, e.g. `tradability_quality_weights`, so it is not hashable on its own). Any change to
# EITHER component -- a config field genuinely read by this scan, or the store's registered series
# set -- changes the key and busts BOTH tiers; an untouched (config content, store content) pair
# always replays the identical cached result, hot-slot or durable. A single most-recent SLOT (not an
# unbounded dict) remains intentional for the IN-PROCESS tier: this codebase runs ONE bar store
# behind ONE process, so there is never more than one "current" scan worth remembering in-process,
# and a single slot cannot grow unbounded across a long-lived process or an entire test suite's run
# -- the DURABLE tier (unlike this slot) can and does hold more than one row, one per distinct key
# ever published.
#
# --- Atomic publish (era-5B iter-6 B3 hardening; both tiers covered since era-fast_wall J-06) ----
# The slot is ONE immutable ``(key, result)`` tuple (or ``None`` before anything is ever cached) --
# NEVER a two-key mutable dict written in two separate statements. iter-6 (era-5B) is the first
# caller to fire ``/setups`` + ``/setups/{id}`` + ``/edge-report`` concurrently from a single page
# load (a FastAPI sync route handler runs in a thread pool), and the PRIOR two-write dict form
# (``_SCAN_CACHE["key"] = key`` THEN ``_SCAN_CACHE["result"] = result``) had a genuine torn-read
# window: a late-arriving reader could observe a freshly-published ``key`` paired with the SLOT'S
# STILL-STALE (possibly ``None``, on a first-ever cold cache) ``result``, since the two writes are
# not one atomic step. Publishing a single already-built ``(key, result)`` tuple removes that window
# by construction: CPython rebinds a module-level name via one bytecode store, so a concurrent
# reader always observes EITHER the entire previous publish (fully paired) or nothing yet (a safe
# cache miss that recomputes) -- never a half-written pairing. Readers likewise take exactly ONE
# local reference to the slot (`cached = _SCAN_CACHE`) before inspecting it, so a rebind by another
# thread mid-check can never be observed as two different values within the same read. era-fast_wall
# J-06 preserves this exactly: `compute_setups` still rebinds `_SCAN_CACHE` via ONE single statement
# regardless of WHICH tier answered (a durable hit republished to the hot slot, or a full miss
# freshly scanned and published to both layers) -- see
# ``tests/test_setups.py``'s ``test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes``
# structural guard, unmodified and still passing. See
# ``tests/test_setups.py``'s
# ``test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair`` for the regression
# proof.
_SCAN_CACHE: tuple[tuple, dict] | None = None


def _reset_scan_cache_for_tests() -> None:
    """Test-only: clears the module-level in-process hot slot (`_SCAN_CACHE`) -- mirrors
    `bars.py`/`datasets.py`'s own `_reset_verified_cache_for_tests` precedent (era-fast_wall J-06).
    Never called from any production code path; exists so a test can genuinely simulate "hot slot
    cleared, as if the process had just restarted" (`SetupsScanCache`'s own durable tier is already
    isolated per-test by its stat/path-derived location -- this only ever needs to reset the
    in-process half)."""
    global _SCAN_CACHE
    _SCAN_CACHE = None


def _store_signature(store: BarStore) -> tuple:
    """A deterministic fingerprint of everything ``compute_setups`` can possibly read from
    ``store``: every HEALTHY series' ``(symbol, timeframe, id, checksum)``, sorted for
    order-independence. A corrupt file (``store.list()``'s own ``errors`` return) is excluded --
    ``compute_setups`` itself never reads a corrupt file's content either (``_select_5m_series``
    only ever sees ``records``), so a corrupt file's mere presence/absence can never change the
    scan's OWN output and is rightly left out of what busts the cache."""
    records, _errors = store.list()
    return tuple(sorted(
        (record["symbol"], record["timeframe"], record["id"], record["checksum"])
        for record in records
    ))


def compute_setups(store: BarStore, config: Config) -> dict:
    """The canonical ``GET /research/setups`` + MCP ``setups`` computation (single source of
    truth) -- see module docstring for the full algorithm. Returns ``{"events": [...]}``; an empty
    list is an honest "nothing scanned yet / nothing touched", never an error.

    era-fast_wall J-06 -- a three-tier lookup: the in-process hot slot (below; unchanged atomic
    discipline) -> the durable ``SetupsScanCache`` (``setups_scan_cache.py``, a restart-surviving
    sibling of this slot) -> the real scan (``_run_full_panel_scan``), run at most once per
    genuinely new key. Keyed on ``config``'s CONTENT (a hash over every field, reused verbatim from
    ``edge_report_cache._config_content_hash`` -- never re-derived a second time -- rather than its
    object identity, so a freshly-constructed but content-equal ``Config`` is a genuine cache HIT)
    together with a deterministic content signature over the store (``_store_signature`` below).
    Byte-identical whichever tier answers -- caching changes only whether/where the scan is
    recomputed, never what is returned.

    Atomic against concurrent callers (era-5B iter-6 B3 hardening, preserved): ``cached`` is read
    ONCE into a local (never re-read mid-function, so a concurrent rebind by another thread cannot
    be observed as two different values here), and every path below -- a durable hit republished to
    the hot slot, or a full miss freshly scanned and published to BOTH layers -- funnels through the
    SAME single rebind of the module-level slot, never two separate writes a reader could observe
    half-done. A racing miss on another thread only ever costs redundant, harmless recompute (the
    scan is a pure function of its inputs); it can never produce a torn key/result pairing."""
    global _SCAN_CACHE
    content_hash = _config_content_hash(config)
    store_signature = _store_signature(store)
    key = (content_hash, store_signature)

    cached = _SCAN_CACHE
    if cached is not None and cached[0] == key:
        return cached[1]

    durable = SetupsScanCache(resolve_scan_cache_db_path(str(store.root)))
    durable_key = scan_cache_key(config_content_hash=content_hash, store_signature=store_signature)
    persisted = durable.lookup(durable_key)
    if persisted is not None:
        result = persisted
    else:
        result = _run_full_panel_scan(store, config)
        durable.publish(durable_key, result)
    _SCAN_CACHE = (key, result)
    return result


def _run_full_panel_scan(store: BarStore, config: Config) -> dict:
    """The real, uncached full-panel scan -- unchanged algorithm from before B3, only renamed so
    the public ``compute_setups`` above can wrap it with the process-local cache. See the module
    docstring for the full algorithm; never called directly by any route or report -- only through
    ``compute_setups``."""
    events: list[dict] = []
    for symbol in config.setups_panel_symbols:
        five_min_bars = _select_5m_series(store, symbol)
        if not five_min_bars:
            continue  # no "5m" series for this symbol -- honestly zero events, never fabricated
        for session_date_value, start_index, session_bars in _group_sessions(five_min_bars):
            # The central risk (see module docstring): the as_of passed to compute_tradability is
            # resolved PER SESSION, from that session's OWN first bar -- never a shared/fixed value
            # across the whole walk, which would silently hand every session the SAME (latest) map.
            as_of_epoch = session_bars[0].epoch
            tradability = compute_tradability(store, symbol, as_of_epoch, config)
            for band in tradability["bands"]:
                local_indices = _touches(
                    band["price_low"], band["price_high"], session_bars,
                    config.setups_max_events_per_band_per_session,
                )
                for local_index in local_indices:
                    touch_index = start_index + local_index
                    outcome = _reaction_and_forward_returns(
                        five_min_bars, touch_index, band["side"],
                        band["price_low"], band["price_high"], config,
                    )
                    if outcome is None:
                        continue  # no bar at all follows the touch -- nothing to react with
                    reaction, forward_returns, effective_horizon, boundary_truncated = outcome
                    events.append(_event(
                        symbol, session_date_value, band, five_min_bars[touch_index],
                        reaction, forward_returns, effective_horizon, boundary_truncated,
                    ))
    events.sort(key=_event_sort_key)
    return {"events": events}


# --- Tape-at-the-wall join (era-5B capability 4, J-03) -- see the module docstring's own section
# for the full design. Called ONLY from the GET /research/setups/{id} route, never from
# compute_setups' shared scan loop above. -----------------------------------------------------


def _matching_dataset(symbol: str, touch_ts: str, dataset_store: DatasetStore) -> dict | None:
    """The recorded ``DatasetStore`` dataset whose window covers ``touch_ts`` for ``symbol``, or
    ``None``. Match = symbol equality + ``[window_start_utc, window_end_utc]`` containing
    ``touch_ts`` (inclusive both ends). Every timestamp is parsed to an epoch via the SAME
    ``parse_utc_epoch`` the ``/research/datasets`` route itself uses -- a deliberately NUMERIC
    comparison, never a lexicographic string one: two otherwise-equal ISO instants stamped at
    different fractional-second precision (a real possibility -- a caller-supplied window bound
    need not carry the same microsecond precision this module's own ``_iso`` always emits for
    ``touch_ts``) can sort in the WRONG order as plain strings (``"...:00Z"`` > ``"...:00.000001Z"``
    lexicographically, since ``"Z" > "."`` in ASCII), so this join never risks that. Datasets
    already known-healthy: ``DatasetStore.list()`` verifies every file's checksum and separates any
    corrupt file into its own ``errors`` return before this function ever sees a candidate. Ties
    (more than one dataset's window covering the same touch) break on the earliest ``created_utc``,
    then ``id`` -- deterministic, never insertion-order happenstance."""
    touch_epoch = parse_utc_epoch(touch_ts)
    records, _errors = dataset_store.list()
    candidates = [
        r for r in records
        if r["symbol"] == symbol
        and parse_utc_epoch(r["window_start_utc"]) <= touch_epoch <= parse_utc_epoch(r["window_end_utc"])
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda r: (r["created_utc"], r["id"]))


def _tape_timeline(dataset_meta: dict, dataset_store: DatasetStore, config: Config) -> list[dict]:
    """The five-state timeline for one matched dataset: replay it through the FROZEN ``TapeEngine``
    via ``DatasetStore.replay`` (never reimplemented here) and collapse the per-tick snapshot
    stream to state-TRANSITION entries only -- the ``HistoryBuffer.note_state`` idiom (a marker
    only when ``tape_state`` changes, and only into a state ``Config.history_marker_states`` marks
    as meaningful -- a transition into ``unclear`` is not itself a meaningful "the tape said X"
    call, mirrored here rather than inventing a second "which states matter" concept). Real UTC
    instants are reconstructed as the dataset's own ``epoch_anchor`` plus each snapshot's LOGICAL
    timestamp (``HistoricalProvider``'s "logical, not wall-clock" replay scheme) -- the identical
    reconstruction ``serializers.serialize_history`` already uses for chart markers."""
    epoch_anchor = dataset_meta["epoch_anchor"]
    meaningful = frozenset(config.history_marker_states)
    prev_state: str | None = None
    timeline: list[dict] = []
    for snapshot in dataset_store.replay(dataset_meta["id"], config):
        if snapshot.tape_state != prev_state:
            if snapshot.tape_state in meaningful:
                timeline.append({
                    "timestamp": _iso(epoch_anchor + snapshot.timestamp) if epoch_anchor is not None else None,
                    "state": snapshot.tape_state,
                    "confidence": snapshot.confidence,
                })
            prev_state = snapshot.tape_state
    return timeline


def enrich_with_tape_timeline(event: dict, dataset_store: DatasetStore, config: Config) -> dict:
    """Join the tape-at-the-wall timeline onto ONE event's drill-in (era-5B J-03). Returns a NEW
    dict (never mutates ``event``) with ``tape_timeline`` replaced by the matched dataset's replay,
    or the event UNCHANGED (still an honestly empty ``tape_timeline``) when no recorded dataset
    matches. Every other field is served verbatim -- this function never touches band, reaction,
    or forward-return values (single source of truth: ``compute_setups`` owns those alone)."""
    dataset = _matching_dataset(event["symbol"], event["touch_ts"], dataset_store)
    if dataset is None:
        return event
    return {**event, "tape_timeline": _tape_timeline(dataset, dataset_store, config)}
