"""``desk_playbook_context`` — the READ-SIDE band-context lens: every already-recorded playbook
signal (and every baseline anchor drawn beside one) joined to the desk's OWN tradable band map at
that event's own session basis.

Why a separate module, read-side, at serve time only:

  * ``compute_playbook`` is guard-tested to make ZERO ``compute_tradability``/``compute_levels``
    calls (``tests/test_desk_playbook_guards.py``'s TC-7) — the book's intraday geometry and the
    desk's structural walls are different owners, and that separation is the reason a recorded
    signal means exactly one thing. This module never runs inside that walk; it reads what the
    walk already wrote. TC-7 stays green, unchanged.
  * A recorded playbook file is NEVER rewritten, backfilled, or superseded. Band context is
    therefore attached when a payload is SERVED, never written back — which is also why every
    already-recorded signal, including every one recorded before this module existed, carries band
    context the moment this ships. Nothing is re-detected and nothing is re-measured.
  * The constants below are deliberately NOT part of ``playbook_parameters()``: adding them would
    move ``playbook_input_signature`` and orphan the entire recorded corpus from its own evidence
    pool. They are pre-registered in ``docs/playbook-detector-spec.md`` §6 and served in this
    payload's own ``parameters`` block instead.

**GET NEVER COMPUTES (the era-5C "Fast Wall" rule, and here it is load-bearing).** One
``compute_tradability`` costs ~0.1-2.6s; the recorded corpus spans ~1,800 distinct
``(symbol, basis session)`` pairs, so computing a fold on demand would block a kept surface for
tens of minutes. Every read path in this module is therefore LOOKUP-ONLY against the durable
``TradabilityCache``: a pair whose map has not been computed yet buckets as ``not_computed`` — an
honest, DISTINCT state, never conflated with ``no_band_context`` ("a map was computed and it puts
no band anywhere near this price"). An explicit operator act fills the cache:

    python -m app.research.desk_playbook_context --warm            # every recorded record
    python -m app.research.desk_playbook_context --warm --date 2026-08-07

Warming is resumable and idempotent (each pair is published independently through the ONE
canonical ``compute_tradability`` path, and an already-cached pair is a ~2ms read).

**The distance definition** (spec §6, pre-registered): from the signal's own recorded ``entry``
(an anchor's ``entry_price``) — the price every forward measurement starts from, and the one field
signals and anchors both carry, so the lens is IDENTICAL on both sides of the comparison — to the
nearest EDGE of the nearest band, in bps. A price inside a band is 0.0 bps, not a negative number:
distance is served unsigned beside ``position`` (``inside``/``above_band``/``below_band``), two
plain facts rather than one encoded one. The nearest band is chosen across BOTH sides and ALL
classes (a ``class: null`` band is still a band; class is a quality projection, not an existence
test), tie-broken ``(distance, class rank, quality_score, price_low)``.

**The map as-of** is the event's own recorded instant. ``basis_day_key`` collapses every instant of
one UTC session date onto the identical prior-completed-daily basis, so this is byte-the-same map
the ``/structure`` drill-in chart already draws under the setup's shape — the caption and the chart
are mechanically incapable of disagreeing.

**Baseline-anchor attribution — positional, then VERIFIED, never guessed.** A recorded anchor
carries no symbol of its own. ``compute_playbook`` appends exactly one anchor per in-cap signal,
in walk order, into that signal's own pool, so ``baseline_anchors[pool][i]`` belongs to the i-th
in-cap signal of that pool. This module does not merely assume that: it attributes positionally
and then CHECKS the anchor's own recorded ``close_price`` against that signal's
``forward.close_price`` — both were measured on the same symbol's same session series, so they
must agree. Any pool whose counts or close prices disagree is attributed ``None`` and counted as
``n_anchors_unattributable``; its anchors bucket ``no_band_context``. (Verified across the whole
recorded corpus at authoring time: 234 pools, 1,790 anchors, zero disagreements.)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from .datasets import parse_utc_epoch
from .edge_report_cache import _canonical, _config_content_hash
from .tradability import basis_day_key, compute_tradability
from .tradability_cache import (
    TradabilityCache,
    resolve_tradability_cache_db_path,
    symbol_store_signature,
    tradability_cache_key,
)

__all__ = [
    "AT_BAND",
    "AWAY_FROM_BAND",
    "BandMapResolver",
    "CONTEXT_REGISTER",
    "NOT_COMPUTED",
    "NO_BAND_CONTEXT",
    "PLAYBOOK_CONTEXT_ALGORITHM_VERSION",
    "PLAYBOOK_CONTEXT_BUCKETS",
    "PLAYBOOK_CONTEXT_COMPARISON_BUCKETS",
    "PLAYBOOK_CONTEXT_DISTANCE_FROM",
    "PLAYBOOK_CONTEXT_NEAR_BAND_BPS",
    "PlaybookContextCache",
    "band_context_block",
    "cached_context",
    "context_for_record",
    "context_parameters",
    "playbook_context_cache_key",
    "record_band_context",
    "record_map_requests",
    "resolve_playbook_context_cache_db_path",
    "warm_contexts",
]

# --- Pre-registered constants (docs/playbook-detector-spec.md §6) --------------------------------
# Versioned so a change to the LENS invalidates every cached context row without touching one
# recorded byte -- the record's own `playbook_input_signature` is a different, untouched key.
PLAYBOOK_CONTEXT_ALGORITHM_VERSION = "playbook-band-context-v1"

# ADAPTATION (spec §6): one band-width. The desk already calls `tradability_band_width_bps` (70.0)
# "one wall" when it CLUSTERS levels into a band, so "within one band-width of a band's edge" is
# that same tolerance read outward. Echoed here as a pre-registered module constant and NEVER read
# from `Config`: a config tweak must not silently re-bucket already-served evidence, and this
# feature adds zero `Config` fields (the era's frozen-fingerprint anti-goal).
PLAYBOOK_CONTEXT_NEAR_BAND_BPS = 70.0

# Structural (shape, not a threshold): where distance is measured FROM.
PLAYBOOK_CONTEXT_DISTANCE_FROM = "entry"

AT_BAND = "at_band"
AWAY_FROM_BAND = "away_from_band"
NO_BAND_CONTEXT = "no_band_context"
NOT_COMPUTED = "not_computed"

# The complete per-event vocabulary: two measured locations plus two honest absences.
PLAYBOOK_CONTEXT_BUCKETS: tuple[str, ...] = (AT_BAND, AWAY_FROM_BAND, NO_BAND_CONTEXT, NOT_COMPUTED)

# The DECLARED comparison axis of the evidence split -- exactly the two buckets that name a
# measured location. The two absence states are EXCLUSIONS, counted in the split's own basis block
# the way `n_truncated`/`n_unmeasured` are already counted beside every cell, never served as
# distribution cells of their own (a distribution over "this is not known" describes nothing).
PLAYBOOK_CONTEXT_COMPARISON_BUCKETS: tuple[str, ...] = (AT_BAND, AWAY_FROM_BAND)

# Class rank for the nearest-band tie-break only -- never a re-grading (class stays `levels.py`'s).
_CLASS_RANK = {"A": 3, "B": 2, "C": 1}

CONTEXT_REGISTER = (
    "each already-recorded playbook signal joined, at serve time only, to the desk's own tradable "
    "band map for that symbol at that session's basis — the same map the structure chart draws. "
    "Distance is measured from the signal's own recorded entry price to the nearest edge of the "
    "nearest band, in bps, unsigned, with a price inside a band recorded as 0.0 and its side named "
    "separately; a signal within the pre-registered 70 bps of a band edge is bucketed at_band, "
    "which is a description of where the signal happened, not a filter, not a score, and not a "
    "claim that one location works better than another. Nothing here is re-detected, re-measured, "
    "or written back: no recorded file is modified by reading this. A map that has not been "
    "computed yet is bucketed not_computed and is never conflated with a computed map that puts no "
    "band near the price, which is bucketed no_band_context. A baseline anchor records no symbol "
    "of its own; it is attributed to the signal it was drawn beside, by recorded position, and "
    "that attribution is checked against the anchor's own recorded closing price before it is "
    "used — an anchor that cannot be attributed is counted, never guessed. This payload describes "
    "measurements of what already happened and carries no probability, no expectancy, and no "
    "forecast about what happens next"
)


def context_parameters() -> dict:
    """The lens's own pre-registered parameters, served on every payload that carries band context
    — the ``playbook_parameters()`` disclosure habit for this module's own constants (which are
    deliberately NOT in that blob; see the module docstring)."""
    return {
        "algorithm": PLAYBOOK_CONTEXT_ALGORITHM_VERSION,
        "near_band_bps": PLAYBOOK_CONTEXT_NEAR_BAND_BPS,
        "distance_from": PLAYBOOK_CONTEXT_DISTANCE_FROM,
        "buckets": list(PLAYBOOK_CONTEXT_BUCKETS),
        "comparison_buckets": list(PLAYBOOK_CONTEXT_COMPARISON_BUCKETS),
    }


# --- The geometry (pure functions -- no store, no cache, no clock) --------------------------------


def _band_distance_bps(band: dict, price: float) -> float:
    """Distance from ``price`` to the nearest EDGE of ``band``, in bps of ``price`` — ``0.0`` when
    the price sits inside the band (inclusive of both edges). The bps arithmetic is
    ``desk_screen``'s own convention (absolute price gap over the reference price, x10,000)
    generalized from a band's reference price to its nearest edge."""
    low = band["price_low"]
    high = band["price_high"]
    if low <= price <= high:
        return 0.0
    gap = low - price if price < low else price - high
    return abs(gap) / price * 10_000.0


def _position(band: dict, price: float) -> str:
    """Where ``price`` sits relative to ``band`` — the plain fact that replaces a signed distance."""
    if band["price_low"] <= price <= band["price_high"]:
        return "inside"
    return "below_band" if price < band["price_low"] else "above_band"


def _nearest_band(bands: list[dict], price: float) -> dict | None:
    """The nearest band to ``price`` across BOTH sides and ALL classes (``class: null`` included —
    class is a quality projection inherited from the zone engine, never a test of whether a band
    exists). Ties break ``(distance asc, class rank desc, quality_score desc, price_low asc)`` —
    the distance-first shape ``desk_screen._select_opposite_band`` already uses, so a tie can never
    resolve on dict ordering. ``None`` only when there are no bands at all."""
    if not bands:
        return None
    return min(
        bands,
        key=lambda band: (
            _band_distance_bps(band, price),
            -_CLASS_RANK.get(band.get("class") or "", 0),
            -(band.get("quality_score") or 0.0),
            band["price_low"],
        ),
    )


def _bucket(distance_bps: float) -> str:
    """``at_band`` iff within the pre-registered threshold INCLUSIVE — exactly 70.0 bps is at the
    band, the boundary a guard test pins so it can never drift silently."""
    return AT_BAND if distance_bps <= PLAYBOOK_CONTEXT_NEAR_BAND_BPS else AWAY_FROM_BAND


def _side_relation(side: str | None, band_side: str) -> str | None:
    """``aligned`` when the event's own side and the band's side agree in thesis (a long at a
    support wall, a short at a resistance wall), ``opposed`` otherwise. ``None`` when no side is
    known. A baseline anchor is given its POOL's side — the very side its own recorded measurement
    sign already used (``compute_playbook`` signs an anchor with its signal's side), so the two
    columns of the comparison are read the same way rather than one being blank."""
    if side is None:
        return None
    aligned = (side == "long" and band_side == "support") or (
        side == "short" and band_side == "resistance"
    )
    return "aligned" if aligned else "opposed"


def _band_summary(band: dict) -> dict:
    """The served subset of a band — every value copied VERBATIM from ``compute_tradability``'s own
    output (never re-derived). The full ``members`` list is deliberately not carried: the tradable
    map endpoint and the structure chart already own that detail, and this payload is a location
    disclosure, not a second home for the band itself."""
    return {
        "side": band["side"],
        "class": band["class"],
        "price_low": band["price_low"],
        "price_high": band["price_high"],
        "quality_score": band["quality_score"],
        "round_number": band["round_number"],
        "member_count": band["member_count"],
    }


def _basis_phrase(basis_as_of: str | None) -> str:
    return (
        f"map basis: the prior completed session {basis_as_of[:10]}"
        if basis_as_of
        else "map basis: none could be resolved"
    )


def _caption(bucket: str, price: float, band: dict | None, basis_as_of: str | None) -> str:
    """The one served sentence describing this event's location — rendered VERBATIM by the desk
    tables and the structure drill-in, so the two surfaces can never phrase the same fact two ways
    (the UI-recomputes-nothing rule applies to prose as much as to numbers)."""
    if bucket == NOT_COMPUTED:
        return (
            "the tradable band map for this symbol at this session's basis has not been computed "
            "yet, so no location is claimed for this signal"
        )
    if bucket == NO_BAND_CONTEXT or band is None:
        return (
            "no tradable band map is derivable for this symbol at this session's basis — recorded "
            f"as an honest absence, never a guess ({_basis_phrase(basis_as_of)})"
        )
    distance = _band_distance_bps(band, price)
    position = _position(band, price)
    klass = f"class {band['class']}" if band["class"] else "no inherited class"
    where = (
        f"sits inside the {band['side']} band"
        if position == "inside"
        else f"sits {distance:.1f} bps {'below' if position == 'below_band' else 'above'} the {band['side']} band"
    )
    threshold = (
        f"within the pre-registered {PLAYBOOK_CONTEXT_NEAR_BAND_BPS:.0f} bps disclosure threshold"
        if bucket == AT_BAND
        else f"beyond the pre-registered {PLAYBOOK_CONTEXT_NEAR_BAND_BPS:.0f} bps disclosure threshold"
    )
    return (
        f"entry {price:.2f} {where} {band['price_low']:.2f}–{band['price_high']:.2f} "
        f"({klass}) — {bucket}, {threshold}; {_basis_phrase(basis_as_of)}"
    )


def _unlocatable(reason: str) -> dict:
    """An event this lens cannot place at all — no recorded price, no recorded instant, or an
    unparseable one. An honest ``no_band_context``, never a ``not_computed`` (no amount of warming
    would help) and never a fabricated location. The tolerance mirrors ``_file_projection``'s own:
    an older or partial record is excluded from what it cannot support, never a crash."""
    return {
        "bucket": NO_BAND_CONTEXT,
        "distance_bps": None,
        "position": None,
        "side_relation": None,
        "band": None,
        "basis_as_of": None,
        "caption": reason,
    }


def _safe_epoch(value) -> float | None:
    """``parse_utc_epoch`` that answers ``None`` instead of raising for a missing/malformed
    instant — this module reads already-recorded data it does not own the shape of."""
    if not isinstance(value, str):
        return None
    try:
        return parse_utc_epoch(value)
    except (ValueError, TypeError):
        return None


def band_context_block(map_result: dict | None, price: float, side: str | None) -> dict:
    """One event's whole served ``band_context`` block. ``map_result is None`` means the map was
    never computed (lookup-only miss) — a DIFFERENT fact from a computed map with no bands, and the
    two are bucketed differently on purpose (module docstring)."""
    if not isinstance(price, (int, float)):
        return _unlocatable(
            "this event records no entry price, so no location relative to any band is derived"
        )
    if map_result is None:
        return {
            "bucket": NOT_COMPUTED,
            "distance_bps": None,
            "position": None,
            "side_relation": None,
            "band": None,
            "basis_as_of": None,
            "caption": _caption(NOT_COMPUTED, price, None, None),
        }
    basis_as_of = map_result.get("basis_as_of")
    band = _nearest_band(map_result.get("bands") or [], price)
    if band is None:
        return {
            "bucket": NO_BAND_CONTEXT,
            "distance_bps": None,
            "position": None,
            "side_relation": None,
            "band": None,
            "basis_as_of": basis_as_of,
            "caption": _caption(NO_BAND_CONTEXT, price, None, basis_as_of),
        }
    distance = _band_distance_bps(band, price)
    bucket = _bucket(distance)
    return {
        "bucket": bucket,
        "distance_bps": distance,
        "position": _position(band, price),
        "side_relation": _side_relation(side, band["side"]),
        "band": _band_summary(band),
        "basis_as_of": basis_as_of,
        "caption": _caption(bucket, price, band, basis_as_of),
    }


# --- Baseline-anchor attribution (positional, then verified -- see the module docstring) ----------


def _pools_in_record_order(record: dict) -> dict[str, list[dict]]:
    """Every signal grouped by its own ``"<setup_id>:<side>"`` pool, preserving record order —
    the SAME grouping and the SAME order ``desk_playbook_evidence._file_projection`` builds, so a
    per-pool list here is index-aligned with that module's own per-pool event list."""
    pools: dict[str, list[dict]] = {}
    for signal in record.get("signals") or []:
        pools.setdefault(f"{signal.get('setup_id')}:{signal.get('side')}", []).append(signal)
    return pools


def _attribute_anchors(record: dict) -> dict[str, list[dict | None]]:
    """Per pool, the SIGNAL each recorded anchor was drawn beside — or ``None`` where that cannot
    be established. Positional by construction, then verified against the anchor's own recorded
    ``close_price`` (module docstring). A pool that fails either check attributes every one of its
    anchors ``None``: a partial attribution within one pool would be the one shape that could pair
    an anchor with the wrong symbol's wall, so it is refused wholesale."""
    pools = _pools_in_record_order(record)
    attributed: dict[str, list[dict | None]] = {}
    for pool_key, anchors in (record.get("baseline_anchors") or {}).items():
        signals = [s for s in pools.get(pool_key, []) if s.get("forward") is not None]
        if len(anchors) > len(signals):
            attributed[pool_key] = [None] * len(anchors)
            continue
        candidate = signals[: len(anchors)]
        agrees = all(
            anchor.get("close_price") == signal["forward"].get("close_price")
            for anchor, signal in zip(anchors, candidate)
        )
        attributed[pool_key] = list(candidate) if agrees else [None] * len(anchors)
    return attributed


# --- Map resolution (lookup-only by default -- GET NEVER COMPUTES) --------------------------------


class BandMapResolver:
    """Resolves ``(symbol, instant)`` to ONE tradable map, through the durable ``TradabilityCache``
    the ``GET /research/tradability`` route already fills, with an in-process memo so a session's
    ~40 signals on one symbol pay a single lookup.

    ``compute=False`` (every serving path): a cache miss returns ``None`` — the honest
    ``not_computed`` state. ``compute=True`` (the operator warmer only): a miss computes through
    the ONE canonical ``compute_tradability`` and publishes it, byte-identically to what the
    tradability route would have published for the same key."""

    def __init__(self, bar_store, config, *, cache: TradabilityCache | None = None, compute: bool = False):
        self._store = bar_store
        self._config = config
        self._compute = compute
        self._cache = (
            cache
            if cache is not None
            else TradabilityCache(resolve_tradability_cache_db_path(str(bar_store.root)))
        )
        # `store.list()` costs ~1s and is identical for every symbol in one fold -- hoisted once
        # here rather than re-listed per event (the whole reason this is an object, not a function).
        records, _integrity_errors = bar_store.list()
        self._records = records
        self._config_hash = _config_content_hash(config)
        self._signatures: dict[str, tuple] = {}
        self._maps: dict[tuple[str, str], dict | None] = {}

    def _signature(self, symbol: str) -> tuple:
        if symbol not in self._signatures:
            self._signatures[symbol] = symbol_store_signature(self._records, symbol)
        return self._signatures[symbol]

    def map_key(self, symbol: str, as_of_epoch: float) -> str:
        """The tradability cache key for one ``(symbol, basis session)`` — the route's own four-part
        recipe, reused verbatim so a warm published by either caller serves the other."""
        return self.map_key_for_basis_day(symbol, basis_day_key(as_of_epoch))

    def map_key_for_basis_day(self, symbol: str, basis_day: str) -> str:
        """The same key from an ALREADY-resolved basis day — the form a caller holding
        ``record_map_requests`` output uses, so a context cache key can be rebuilt without parsing
        one event timestamp again."""
        return tradability_cache_key(
            symbol=symbol,
            basis_day=basis_day,
            store_signature=self._signature(symbol),
            config_content_hash=self._config_hash,
        )

    def resolve(self, symbol: str, as_of_epoch: float) -> dict | None:
        """The map, or ``None`` when it has not been computed (and this resolver may not compute)."""
        memo_key = (symbol, basis_day_key(as_of_epoch))
        if memo_key in self._maps:
            return self._maps[memo_key]
        key = self.map_key(symbol, as_of_epoch)
        result = self._cache.lookup(key)
        if result is None and self._compute:
            result = compute_tradability(self._store, symbol, as_of_epoch, self._config)
            self._cache.publish(key, result)
        self._maps[memo_key] = result
        return result


# --- The per-record join --------------------------------------------------------------------------


def _event_requests(record: dict, attributed: dict[str, list[dict | None]]) -> list[tuple[str, float]]:
    """Every ``(symbol, instant)`` this record needs a map for — used by the cache key (which must
    name the exact maps a context was built from) and by the warmer."""
    requests: list[tuple[str, float]] = []
    for signal in record.get("signals") or []:
        symbol = signal.get("symbol")
        epoch = _safe_epoch(signal.get("trigger_ts"))
        if symbol and epoch is not None:
            requests.append((symbol, epoch))
    for pool_key, anchors in (record.get("baseline_anchors") or {}).items():
        for anchor, signal in zip(anchors, attributed.get(pool_key, [])):
            if signal is None:
                continue
            symbol = signal.get("symbol")
            epoch = _safe_epoch(anchor.get("at_utc"))
            if symbol and epoch is not None:
                requests.append((symbol, epoch))
    return requests


def record_map_requests(record: dict) -> list[list[str]]:
    """The sorted, deduplicated ``[symbol, basis_day]`` pairs one record's own events need maps for
    — the ONLY thing a caller must know to rebuild this record's context cache key WITHOUT reading
    the record again. Extracted here (rather than in the evidence fold) so the key material and the
    context that key names are computed by the same module, from the same rule.

    Session-date-stable by construction: ``basis_day_key`` collapses every instant of one UTC
    calendar date onto one basis, so a record's whole set is normally a single day's worth of
    symbols — but it is derived per event rather than assumed, because an event's own recorded
    instant is the only thing entitled to name its own basis."""
    attributed = _attribute_anchors(record)
    pairs = {
        (symbol, basis_day_key(epoch)) for symbol, epoch in _event_requests(record, attributed)
    }
    return [list(pair) for pair in sorted(pairs)]


def record_band_context(record: dict, resolver: BandMapResolver) -> dict:
    """The whole served band-context payload for ONE recorded playbook record.

    ``signals`` is in RECORD ORDER and carries every signal — including one recorded without a
    ``forward`` block — each tagged ``measured``, so the evidence fold can filter to exactly the
    events ``_file_projection`` keeps while the drill-in can still caption any signal it is asked
    about. ``baseline_anchors`` mirrors the record's own per-pool lists, index-aligned."""
    attributed = _attribute_anchors(record)
    signals: list[dict] = []
    counts = {bucket: 0 for bucket in PLAYBOOK_CONTEXT_BUCKETS}
    for signal in record.get("signals") or []:
        price = signal.get("entry")
        symbol = signal.get("symbol")
        epoch = _safe_epoch(signal.get("trigger_ts"))
        if not symbol or epoch is None:
            context = _unlocatable(
                "this signal records no symbol or no trigger time, so no band map can be "
                "resolved for it and no location is claimed"
            )
        else:
            context = band_context_block(resolver.resolve(symbol, epoch), price, signal.get("side"))
        counts[context["bucket"]] += 1
        signals.append(
            {
                "symbol": symbol,
                "setup_id": signal.get("setup_id"),
                "side": signal.get("side"),
                "pool_key": f"{signal.get('setup_id')}:{signal.get('side')}",
                "trigger_ts": signal.get("trigger_ts"),
                "entry": price,
                "measured": signal.get("forward") is not None,
                "band_context": context,
            }
        )

    anchor_counts = {bucket: 0 for bucket in PLAYBOOK_CONTEXT_BUCKETS}
    n_unattributable = 0
    anchors_out: dict[str, list[dict]] = {}
    for pool_key, anchors in (record.get("baseline_anchors") or {}).items():
        pool_side = pool_key.rsplit(":", 1)[-1]
        rows: list[dict] = []
        owners = attributed.get(pool_key, [None] * len(anchors))
        for index, anchor in enumerate(anchors):
            owner = owners[index] if index < len(owners) else None
            price = anchor.get("entry_price")
            epoch = _safe_epoch(anchor.get("at_utc"))
            symbol = None if owner is None else owner.get("symbol")
            if owner is None:
                n_unattributable += 1
                # An anchor whose own signal is unknown is an honest ABSENCE of context, never a
                # not-yet-computed map: no amount of warming would resolve it.
                context = _unlocatable(
                    "this baseline anchor could not be attributed to the signal it was drawn "
                    "beside, so no symbol and no location are claimed for it"
                )
            elif not symbol or epoch is None:
                context = _unlocatable(
                    "this baseline anchor records no instant of its own, so no band map can be "
                    "resolved for it and no location is claimed"
                )
            else:
                context = band_context_block(resolver.resolve(symbol, epoch), price, pool_side)
            anchor_counts[context["bucket"]] += 1
            rows.append(
                {
                    "index": index,
                    "at_utc": anchor.get("at_utc"),
                    "entry_price": price,
                    "symbol": symbol,
                    "attribution": "unattributable" if owner is None else "positional_verified",
                    "band_context": context,
                }
            )
        anchors_out[pool_key] = rows

    return {
        "playbook_id": record.get("id"),
        "session_date": record.get("session_date"),
        "playbook_input_signature": record.get("playbook_input_signature"),
        "parameters": context_parameters(),
        "signals": signals,
        "baseline_anchors": anchors_out,
        "basis": {
            "n_signals": len(signals),
            "n_signals_at_band": counts[AT_BAND],
            "n_signals_away_from_band": counts[AWAY_FROM_BAND],
            "n_signals_no_band_context": counts[NO_BAND_CONTEXT],
            "n_signals_not_computed": counts[NOT_COMPUTED],
            "n_anchors": sum(len(rows) for rows in anchors_out.values()),
            "n_anchors_at_band": anchor_counts[AT_BAND],
            "n_anchors_away_from_band": anchor_counts[AWAY_FROM_BAND],
            "n_anchors_no_band_context": anchor_counts[NO_BAND_CONTEXT],
            "n_anchors_not_computed": anchor_counts[NOT_COMPUTED],
            "n_anchors_unattributable": n_unattributable,
        },
        "register": CONTEXT_REGISTER,
    }


# --- The durable per-record context cache ---------------------------------------------------------

_CACHE_DB_ENV = "TAPEOLOGY_PLAYBOOK_CONTEXT_CACHE_DB"
_BUSY_TIMEOUT_MS = 5000
CONTEXT_TABLE = "playbook_context_cache"

_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {CONTEXT_TABLE} (
    cache_key    TEXT PRIMARY KEY,
    context_json TEXT NOT NULL,
    created_utc  TEXT NOT NULL
)
"""


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def playbook_context_cache_key(
    *, playbook_id: str, file_size: int, file_mtime_ns: int, map_keys: list[tuple[str, str, str]]
) -> str:
    """The key for ONE record's whole context — sha256 of canonical JSON over four explicit parts:

      * the lens version (a change to the geometry invalidates every row),
      * the record's own file identity ``(id, size, mtime_ns)`` — the ``PlaybookEvidenceCache``
        stat-keying precedent, exact for a store whose files are never rewritten,
      * every ``(symbol, basis_day, tradability cache key)`` triple the context was actually built
        from, sorted. This is what makes invalidation COHERENT rather than merely plausible: those
        keys already fold in this symbol's store content, the whole config content, and
        ``LEVELS_ALGORITHM_VERSION``, so any change that could move a band moves this key too.

    Conservative by inheritance: a new recording of a symbol busts its map keys even when the new
    bars are dated AFTER the historical basis and therefore cannot change that basis's answer — a
    re-warm that recomputes an identical map, never a wrong one."""
    payload = {
        "algorithm": PLAYBOOK_CONTEXT_ALGORITHM_VERSION,
        "playbook_id": playbook_id,
        "file_size": file_size,
        "file_mtime_ns": file_mtime_ns,
        "map_keys": [list(item) for item in sorted(map_keys)],
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def resolve_playbook_context_cache_db_path(playbook_dir: str) -> str:
    """``TAPEOLOGY_PLAYBOOK_CONTEXT_CACHE_DB`` if set, else ``playbook_context_cache.db`` as a
    SIBLING of the playbook store's own directory — the ``resolve_tradability_cache_db_path``
    env-else-sibling shape for a different env var and filename, so a test pointing its store at a
    ``tmp_path`` gets a hermetic cache for free."""
    override = os.environ.get(_CACHE_DB_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(str(playbook_dir).rstrip("/")), "playbook_context_cache.db")


class PlaybookContextCache:
    """One durable row per (lens version, record file identity, exact maps used). Stores a
    REBUILDABLE RESULT ONLY and owns nothing — deleting the file loses nothing and fabricates
    nothing; the next warm republishes it. Carries no ``update``/``delete`` method by construction
    (the ``PlaybookEvidenceCache`` discipline), and every sqlite failure degrades to a miss rather
    than a crash (the ``TradabilityCache`` discipline)."""

    def __init__(self, db_path: str) -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            conn = self._connect()
            try:
                with conn:
                    conn.execute(_SCHEMA)
            finally:
                conn.close()
        except sqlite3.Error:
            pass

    @property
    def db_path(self) -> str:
        return self._db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self._db_path, check_same_thread=False, timeout=_BUSY_TIMEOUT_MS / 1000.0
        )
        conn.row_factory = sqlite3.Row
        if self._db_path != ":memory:":
            conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
        return conn

    def lookup(self, key: str) -> dict | None:
        try:
            conn = self._connect()
            try:
                row = conn.execute(
                    f"SELECT context_json FROM {CONTEXT_TABLE} WHERE cache_key=?", (key,)
                ).fetchone()
            finally:
                conn.close()
        except sqlite3.Error:
            return None
        return None if row is None else json.loads(row["context_json"])

    def publish(self, key: str, context: dict) -> None:
        """One atomic ``INSERT OR REPLACE``, stored WITHOUT ``sort_keys`` so a cached context serves
        byte-identically to a freshly built one. A publish failure is SWALLOWED — the caller is
        already holding the result it just built."""
        try:
            conn = self._connect()
            try:
                with conn:
                    conn.execute(
                        f"INSERT OR REPLACE INTO {CONTEXT_TABLE} "
                        "(cache_key, context_json, created_utc) VALUES (?,?,?)",
                        (key, json.dumps(context), _iso_utc_now()),
                    )
            finally:
                conn.close()
        except sqlite3.Error:
            pass


def context_for_record(
    record: dict,
    stat_size: int,
    stat_mtime_ns: int,
    resolver: BandMapResolver,
    cache: PlaybookContextCache | None = None,
) -> dict:
    """One ALREADY-LOADED record's context, through the durable cache: a hit is a single sqlite
    read, a miss builds it and publishes. Byte-identical either way."""
    return cached_context(
        playbook_id=record["id"],
        stat_size=stat_size,
        stat_mtime_ns=stat_mtime_ns,
        map_requests=record_map_requests(record),
        load_record=lambda: record,
        resolver=resolver,
        cache=cache,
    )


def cached_context(
    *,
    playbook_id: str,
    stat_size: int,
    stat_mtime_ns: int,
    map_requests: list[list[str]],
    load_record,
    resolver: BandMapResolver,
    cache: PlaybookContextCache | None = None,
) -> dict:
    """One record's context by KEY MATERIAL alone, loading the record only on a miss.

    ``load_record`` is a callable, not a record, on purpose: a warm cache must be able to answer
    without re-reading (and re-checksumming) a multi-megabyte playbook file, which is the whole
    reason a fold over ~45 records stays a handful of sqlite reads. ``map_requests`` is
    ``record_map_requests`` output, which a caller can carry in a cheaper projection."""
    key = playbook_context_cache_key(
        playbook_id=playbook_id,
        file_size=stat_size,
        file_mtime_ns=stat_mtime_ns,
        map_keys=sorted(
            {
                (symbol, basis_day, resolver.map_key_for_basis_day(symbol, basis_day))
                for symbol, basis_day in map_requests
            }
        ),
    )
    if cache is not None:
        hit = cache.lookup(key)
        if hit is not None and _is_complete(hit):
            return hit
    record = load_record()
    if record is None:
        return {}
    context = record_band_context(record, resolver)
    if cache is not None and _is_complete(context):
        cache.publish(key, context)
    return context


def _is_complete(context: dict) -> bool:
    """Whether every event in ``context`` actually resolved a map — i.e. the context contains no
    ``not_computed`` bucket.

    An INCOMPLETE context must never be persisted, and must never be trusted if some older code
    path did persist one. The reason is precise: this cache's key names the maps a context was
    built FROM, not whether those maps had been computed yet, so a row written by a lookup-only
    serving path (where every event honestly reads ``not_computed``) would keep that key forever
    and go on serving "no location known" long after the warmer computed the real maps. The
    absence would look permanent and measured when it was neither.

    Guarding BOTH sides — publish and lookup — also makes an already-poisoned database self-heal:
    a stale incomplete row is simply ignored and replaced the next time a complete context is
    built, with no manual surgery and no migration."""
    basis = context.get("basis") or {}
    return not (basis.get("n_signals_not_computed") or basis.get("n_anchors_not_computed"))


# --- The operator warmer (the ONLY path that computes a map) --------------------------------------


def warm_contexts(store, bar_store, config, *, date: str | None = None, log=print) -> dict:
    """Compute and publish every tradable map the recorded playbook corpus needs, then publish each
    record's context. The ONE path in this module that may compute — every serving path is
    lookup-only (module docstring). Resumable and idempotent: an already-published map is a ~2ms
    read, so re-running after an interruption resumes rather than restarts."""
    resolver = BandMapResolver(bar_store, config, compute=True)
    cache = PlaybookContextCache(resolve_playbook_context_cache_db_path(str(store.root)))
    paths = sorted(store.root.glob("*.json")) if store.root.exists() else []
    warmed = 0
    skipped = 0
    for path in paths:
        record = store.get(path.stem)
        if record is None:
            skipped += 1
            continue
        if date is not None and record["session_date"] != date:
            continue
        stat = path.stat()
        context = context_for_record(record, stat.st_size, stat.st_mtime_ns, resolver, cache)
        warmed += 1
        basis = context["basis"]
        log(
            f"[{warmed}/{len(paths)}] {record['session_date']} {record['id']} — "
            f"signals {basis['n_signals']} "
            f"(at_band {basis['n_signals_at_band']}, away {basis['n_signals_away_from_band']}, "
            f"no_band {basis['n_signals_no_band_context']}, "
            f"not_computed {basis['n_signals_not_computed']})"
        )
    return {"records_warmed": warmed, "records_skipped": skipped, "maps_resolved": len(resolver._maps)}


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Warm the playbook band-context caches — the operator act that lets every read path "
            "stay lookup-only. Resumable and idempotent."
        )
    )
    parser.add_argument("--warm", action="store_true", required=True, help="compute and publish")
    parser.add_argument("--date", default=None, help="only this session date (default: every one)")
    args = parser.parse_args(argv)

    from ..config import CONFIG
    from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
    from .routes import get_bar_store

    store = PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))
    result = warm_contexts(store, get_bar_store(), CONFIG, date=args.date)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover - operator entry point
    raise SystemExit(_main(sys.argv[1:]))
