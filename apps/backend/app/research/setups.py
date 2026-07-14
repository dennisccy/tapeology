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
purely against historical bars -- no engine, no live state, no tape at all (the tape join is J-03,
out of scope here; every event's ``tape_timeline`` field is present but honestly empty until then).
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
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone

from ..config import Config
from ..providers.adapters.base import RawBar
from .bars import BarStore
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
) -> tuple[str, list[dict]] | None:
    """The touch's reaction label + forward-return list, or ``None`` when NO bar at all follows the
    touch (nothing to react with -- the event is excluded, never fabricated). Reaction is decided
    from the CLOSE at the shortest configured horizon (never an intrabar wick, never volume) versus
    each band edge widened by ``Config.setups_reaction_threshold_bps``; every configured horizon is
    then reported, honestly ``None`` for any horizon reaching past the end of the store."""
    if touch_index >= len(all_bars) - 1:
        return None
    horizons = config.setups_forward_return_horizons_bars
    touch_close = all_bars[touch_index].close
    threshold = config.setups_reaction_threshold_bps / 10_000.0

    reaction_index = min(touch_index + horizons[0], len(all_bars) - 1)
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
    return reaction, forward_returns


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


def compute_setups(store: BarStore, config: Config) -> dict:
    """The canonical ``GET /research/setups`` + MCP ``setups`` computation (single source of
    truth) -- see module docstring for the full algorithm. Returns ``{"events": [...]}``; an empty
    list is an honest "nothing scanned yet / nothing touched", never an error."""
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
                    reaction, forward_returns = outcome
                    events.append(_event(
                        symbol, session_date_value, band, five_min_bars[touch_index],
                        reaction, forward_returns,
                    ))
    events.sort(key=_event_sort_key)
    return {"events": events}
