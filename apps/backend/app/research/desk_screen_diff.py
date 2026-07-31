"""Screen comparison (Era B "The Desk", J-20) -- discloses how the screen the operator is currently
viewing differs from the screen recorded immediately before it. The Data Contract's "Screen
comparison" row's ONE owner, served by ``GET /research/desk/screen/compare``.

THIS MODULE computes NOTHING new about tradable structure and reads NO store of any kind -- it is a
pure, stateless read over exactly two ALREADY-RECORDED, immutable snapshots fetched through
``desk_screen.ScreenStore.list()`` (the SAME ``(records, errors)`` read ``GET /research/desk/screen``
already performs for its ``?id=``/``?date=``/no-param branches). Every per-symbol field in the
response is copied VERBATIM from one of the two snapshots' own recorded rows; ``rank_change`` is a
plain integer subtraction of two already-recorded 1-based positions (the ``basis_age_days``
precedent, ``desk_screen.py:388`` -- arithmetic over recorded values, never a new measurement). No
``compute_tradability`` call, no ``BarStore``/``bar_index``/dataset read, no re-rank, no re-score --
structurally impossible, since this module's only input is the two records themselves (it never
receives a store reference of any kind, mirroring ``desk_screen._bar_store_signature``'s own
"cannot call what it never received" argument).

**Base resolution (goal.md J-20 step 2).** The default base for a compare snapshot is the recorded
snapshot with the greatest ``screen_date`` STRICTLY earlier than the compare snapshot's own
``screen_date``, ties (two recordings of one earlier date) broken by the later ``created_utc`` --
exactly the record ``GET /research/desk/screen?date=<that earlier date>`` already serves
(``matching[-1]``, ``desk_routes.py:381``), reusing ``ScreenStore.list()``'s own
``(created_utc, id)``-ascending sort so the two reads can never disagree. An explicit ``base=<id>``
overrides it. No earlier ``screen_date`` exists -> an honest ``base: null`` / ``base_resolution:
"none_earlier"`` -- and, since there is then nothing to compare against, ``rows`` is empty rather
than reporting every compare row as "entered" against a nonexistent base (a comparison needs TWO
sides; "no earlier screen" is its own honest state, not "compare vs. nothing"). An unknown ``id`` (of
either kind) is an honest ``null`` at HTTP 200 (the ``?id=`` convention, mirrored) -- never a 404 or
a fabricated body. A snapshot compared with itself raises ``ScreenDiffSelfCompareError`` -- an
honest refusal, never a silent zero-diff no-op.

**Row construction (goal.md J-20 step 1).** Walked TWICE, each in a snapshot's own served rank
order (never re-sorted): first every symbol ranked in the COMPARE snapshot (``"compared"`` when the
base snapshot also ranked it, ``"entered"`` otherwise, carrying the base's own recorded skip
``reason`` when its skip list names the symbol and an honest ``null`` when it does not mention the
symbol at all); then every symbol ranked in the BASE snapshot that the compare snapshot's ranked set
did NOT already cover (``"left"``, the mirror image, carrying the COMPARE snapshot's own recorded
skip reason where it has one). ``rank_change`` is only ever set on a ``"compared"`` row.

**Disclose, never judge (goal.md J-20 step 4).** ``rows`` carries no ordering by size of change --
compare-ranked rows keep the compare snapshot's own served order, left rows are appended after in
the base snapshot's own served order. ``counts``/``identical`` are plain tallies/equality checks,
never a threshold, significance number, or "notable" framing.

**No new ``Config`` field, no new store.** This module persists nothing -- no store, no file, no
cache, no index. It takes a already-constructed ``ScreenStore`` and two ids; nothing here resolves
a storage directory of its own.
"""

from __future__ import annotations

from .desk_screen import ScreenStore

# The four fields copied verbatim onto every "compared"/"entered"/"left" row, alongside `symbol`.
# Kept as a tuple (not hardcoded per-field below) so the compare/base row-projection helper and its
# call sites can never drift out of sync with each other.
_DISCLOSED_FIELDS = ("side", "band_class", "distance_bps", "basis_as_of")


class ScreenDiffSelfCompareError(Exception):
    """A compare request named the SAME snapshot id as both the compare and the base -- an honest
    refusal (goal.md J-20 step 2: "a snapshot compared with itself is an honest refusal, never a
    silent no-op"), never a silent zero-diff body."""

    def __init__(self, snapshot_id: str) -> None:
        self.snapshot_id = snapshot_id
        super().__init__(
            f"cannot compare snapshot '{snapshot_id}' with itself -- a comparison requires two "
            f"distinct recorded snapshots"
        )


def _snapshot_meta(record: dict) -> dict:
    """The Data Contract's `compare`/`base` shape -- id/pins/created_utc/counts copied verbatim off
    a full `ScreenStore.list()` record (never re-derived; `ranked_count`/`skipped_count` are plain
    `len()`s of that SAME record's own `rows`/`skipped` lists)."""
    return {
        "id": record["id"],
        "screen_date": record["screen_date"],
        "as_of": record["as_of"],
        "created_utc": record["created_utc"],
        "bar_store_signature": record["bar_store_signature"],
        "universe_snapshot_id": record["universe_snapshot_id"],
        "ranked_count": len(record["rows"]),
        "skipped_count": len(record["skipped"]),
    }


def _resolve_default_base(records: list[dict], compare_record: dict) -> dict | None:
    """goal.md J-20 step 2: the recorded snapshot with the greatest `screen_date` STRICTLY earlier
    than `compare_record`'s own `screen_date`, ties broken by the later `created_utc` -- exactly
    `desk_routes.get_screen`'s own `?date=` branch's `matching[-1]` (`records` is already sorted
    `(created_utc, id)` ascending by `ScreenStore.list()`, so the LAST of a same-date group is
    always the latest-recorded one). `None` when no strictly-earlier `screen_date` exists at all."""
    earlier = [r for r in records if r["screen_date"] < compare_record["screen_date"]]
    if not earlier:
        return None
    newest_date = max(r["screen_date"] for r in earlier)
    matching = [r for r in earlier if r["screen_date"] == newest_date]
    return matching[-1]


def _empty_counts() -> dict:
    return {"compared": 0, "rank_changed": 0, "side_changed": 0, "entered": 0, "left": 0}


def _not_found_response() -> dict:
    """`?id=` (the compare snapshot) did not resolve to any recorded snapshot -- an honest
    `compare: null` at HTTP 200 (never a 404/500/fabricated body), mirroring `GET
    /research/desk/screen?id=`'s own unknown-id convention."""
    return {
        "compare": None,
        "base": None,
        "base_resolution": None,
        "rows": [],
        "identical": False,
        "counts": _empty_counts(),
    }


def _diff_rows(compare_record: dict, base_record: dict) -> tuple[list[dict], dict, bool]:
    """The row walk (goal.md J-20 step 1) -- compare-ranked rows first, in the compare snapshot's
    OWN served order, then base-only ("left") rows in the base snapshot's OWN served order. Returns
    `(rows, counts, identical)`."""
    compare_rank_by_symbol = {row["symbol"]: i + 1 for i, row in enumerate(compare_record["rows"])}
    base_rank_by_symbol = {row["symbol"]: i + 1 for i, row in enumerate(base_record["rows"])}
    base_row_by_symbol = {row["symbol"]: row for row in base_record["rows"]}
    compare_row_by_symbol = {row["symbol"]: row for row in compare_record["rows"]}
    base_skip_reason_by_symbol = {s["symbol"]: s["reason"] for s in base_record["skipped"]}
    compare_skip_reason_by_symbol = {s["symbol"]: s["reason"] for s in compare_record["skipped"]}

    rows: list[dict] = []

    for crow in compare_record["rows"]:
        symbol = crow["symbol"]
        brow = base_row_by_symbol.get(symbol)
        if brow is not None:
            status = "compared"
            base_rank = base_rank_by_symbol[symbol]
            # Sign convention: compare_rank - base_rank. Positive == the symbol's 1-based position
            # moved to a HIGHER (worse) number since the base recording; negative == a LOWER
            # (better) number. Purely descriptive (goal.md step 4: "never gives a direction a
            # valence") -- the sign is not rendered as an arrow/colour anywhere.
            rank_change = compare_rank_by_symbol[symbol] - base_rank
            skip_reason = None
        else:
            status = "entered"
            base_rank = None
            rank_change = None
            skip_reason = base_skip_reason_by_symbol.get(symbol)
        row = {
            "symbol": symbol,
            "status": status,
            "compare_rank": compare_rank_by_symbol[symbol],
            "base_rank": base_rank,
            "rank_change": rank_change,
            "skip_reason": skip_reason,
        }
        for field in _DISCLOSED_FIELDS:
            row[f"compare_{field}"] = crow.get(field)
            row[f"base_{field}"] = brow.get(field) if brow is not None else None
        rows.append(row)

    for brow in base_record["rows"]:
        symbol = brow["symbol"]
        if symbol in compare_rank_by_symbol:
            continue  # already emitted above as "compared"
        row = {
            "symbol": symbol,
            "status": "left",
            "compare_rank": None,
            "base_rank": base_rank_by_symbol[symbol],
            "rank_change": None,
            "skip_reason": compare_skip_reason_by_symbol.get(symbol),
        }
        for field in _DISCLOSED_FIELDS:
            row[f"compare_{field}"] = None
            row[f"base_{field}"] = brow.get(field)
        rows.append(row)

    compared_rows = [r for r in rows if r["status"] == "compared"]
    counts = {
        "compared": len(compared_rows),
        "rank_changed": sum(1 for r in compared_rows if r["rank_change"] != 0),
        "side_changed": sum(1 for r in compared_rows if r["compare_side"] != r["base_side"]),
        "entered": sum(1 for r in rows if r["status"] == "entered"),
        "left": sum(1 for r in rows if r["status"] == "left"),
    }
    identical = (
        counts["entered"] == 0
        and counts["left"] == 0
        and all(
            r["rank_change"] == 0 and all(r[f"compare_{f}"] == r[f"base_{f}"] for f in _DISCLOSED_FIELDS)
            for r in compared_rows
        )
    )
    return rows, counts, identical


def compute_screen_diff(store: ScreenStore, compare_id: str, base_id: str | None = None) -> dict:
    """The comparison's ONE computation (goal.md J-20): read exactly two recorded snapshots via
    ``store.list()`` and return the Data Contract's ``{compare, base, base_resolution, rows,
    identical, counts}`` shape. Raises ``ScreenDiffSelfCompareError`` when ``base_id == compare_id``
    (checked BEFORE any lookup, so a self-compare is refused even if the id happens not to resolve).
    ``compare_id`` unresolved -> ``_not_found_response()`` (honest, HTTP-200-shaped null). An
    explicit ``base_id`` that does not resolve is treated identically to "no earlier snapshot"
    (``base: null``) but keeps ``base_resolution: "explicit"``, distinguishing "asked for a specific
    base that does not exist" from "asked for the default and none exists"."""
    if base_id is not None and base_id == compare_id:
        raise ScreenDiffSelfCompareError(compare_id)

    records, _errors = store.list()
    by_id = {r["id"]: r for r in records}

    compare_record = by_id.get(compare_id)
    if compare_record is None:
        return _not_found_response()

    if base_id is not None:
        base_record = by_id.get(base_id)
        base_resolution = "explicit"
    else:
        base_record = _resolve_default_base(records, compare_record)
        base_resolution = "default_prior_date" if base_record is not None else "none_earlier"

    compare_meta = _snapshot_meta(compare_record)
    base_meta = _snapshot_meta(base_record) if base_record is not None else None

    if base_record is None:
        rows: list[dict] = []
        counts = _empty_counts()
        identical = False
    else:
        rows, counts, identical = _diff_rows(compare_record, base_record)

    return {
        "compare": compare_meta,
        "base": base_meta,
        "base_resolution": base_resolution,
        "rows": rows,
        "identical": identical,
        "counts": counts,
    }
