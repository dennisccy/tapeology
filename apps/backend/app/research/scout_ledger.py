"""``scout_ledger.py`` -- Era "The Rapid Microscope" J-04: the hash-chained, append-only

exploratory candidate ledger (``docs/rapid-validation-spec.md`` section 5.1/5.2). Every variant
the Scout ever evaluates -- survivors and kills alike -- lands here as one permanent row; nothing
is ever deleted or rewritten (the "denominator never shrinks" anti-goal, made mechanical).

**A genuinely new pattern, not a copy of ``desk_playbook_log.py``.** That module's rows each carry
an INDEPENDENT ``sha256(canonical(record))`` -- a per-row checksum, not a literal chain: deleting a
row, or reordering two rows, leaves every remaining row's own checksum verifying fine. Spec section
5.2 asks for "hash-chained", and TR-11 requires a chain-verification failure to land AT the tampered
row -- so THIS ledger's ``row_hash`` commits to the PREVIOUS row's own ``row_hash`` as well as its
own content (a genuine link, the git-commit-chain idiom): editing row *k* in place changes its
recomputed content hash away from its own stored ``row_hash`` (caught at *k*, directly, no need to
consult any other row); deleting a MID-FILE row, or reordering rows, breaks the ``prev_hash``
pointer at the first row whose predecessor no longer matches (also caught at that row, directly).
Both failure modes report a single, unambiguous ``failed_at_row`` index -- never merely "the file
changed somewhere".

**The chain alone cannot see its own missing tail -- so a durable head anchor closes that hole
(iter-4 audit fix).** Truncating the LAST rows of a hash chain leaves every surviving row perfectly
self-consistent: this is a property of linked chains generally, not a bug in this one, and it is
exactly the erasure the era's own critical anti-goal ("The denominator never shrinks ... kills are
never deleted") must be able to detect. ``append_row`` therefore also maintains
``chain_head.json`` -- ``{"row_count", "head_hash"}`` for the ledger as last written -- and
``verify_chain`` compares the file against it: fewer rows than the anchor claims is
``tail_truncated`` (reported at the first missing index), and an anchor that is itself missing on a
non-empty ledger is ``head_anchor_missing`` -- an honest "this ledger's completeness cannot be
certified", never a silent pass. The anchor is written AFTER the row it commits to, so a crash
between the two leaves the ledger LONGER than the anchor (benign, and still verified against the
anchored prefix), never falsely short.

**One global chain, not one per family.** "The ledger" is spoken of throughout the spec in the
singular -- a single evidentiary trail every registered variant of every family lands in, in true
append order. A family's own ``variants_tried`` (the union-N denominator, TR-11) is a QUERY over
this one file (every row whose ``family_id`` matches), never a second, separately-chained store.

**This module enforces NO business rule.** ``append_row`` hash-chains and persists whatever
content it is given -- it does not know about ``SCOUT_MAX_VARIANTS_PER_FAMILY`` (the 24-variant
grid bound) or the registration-ordering rule (TR-9). Those are ``scout.py``'s job, at the
REGISTRATION boundary, before it ever calls ``append_row``. This split is deliberate: it lets a
test exercise the union-N arithmetic in isolation (TC-2, mirroring the spec's own illustrative
"v1 N=40 + v2 N=25 => 65" example, which is a union-N ILLUSTRATION and pointedly exceeds the
24-variant cap -- a fact that would make no sense if this primitive enforced that cap itself) while
a SEPARATE, dedicated test (TC-9) proves the cap is enforced at the actual production entry point
(``scout.register_and_screen_candidate``). Logged here as the iteration's own interpretation call,
the same class of judgment ``micro_join.py``'s own docstring already documents for a technique
mirrored rather than imported.

**``superseded`` rows are never rewritten either.** A candidate that is later superseded is not
edited -- decision ``"superseded"`` is stamped onto a row at APPEND time (this module has no path
that could ever revisit an already-written row), and that row's ``superseded_by`` field names the
candidate_id of whatever row replaces it (which appears LATER in the same file, append order).
Nothing in this iteration's registered grid actually triggers a real supersession (that is a J-05
walk-forward concept -- geometry voiding, per-origin refits); this module supports the DATA SHAPE
so a future caller has somewhere to put it, tested directly (TC-4) by planting both rows through
this module's own public ``append_row``.

**Storage dir -- no new ``Config`` field.** ``resolve_scout_ledger_dir`` mirrors
``micro_snapshots.resolve_micro_snapshots_dir`` exactly: the ``TAPEOLOGY_MICRO_SCOUT_DIR`` env var
if set, else a ``micro_scout`` SIBLING of the caller's own already-resolved dataset directory (the
``TAPEOLOGY_MICRO_*`` family, goal.md Constraints) -- an operational storage-location knob, never a
value that shapes a served result, so ``config_fingerprint()`` stays untouched."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

__all__ = [
    "KILL_REASONS",
    "SCOUT_DECISION_SURVIVE",
    "CLOSED_DECISIONS",
    "ScoutLedgerIntegrityError",
    "resolve_scout_ledger_dir",
    "compute_family_root_id",
    "compute_spec_hash",
    "derive_family_id",
    "distinct_variant_count",
    "ScoutLedger",
]

# docs/rapid-validation-spec.md section 1 -- transcribed verbatim (the CLOSED kill vocabulary; free
# text goes in `notes`, never in `decision`/`reason`). `"superseded"` is itself a member: a row can
# be marked `decision == "superseded"` when a later row replaces it (module docstring).
KILL_REASONS: tuple[str, ...] = (
    "killed_null",
    "killed_direction",
    "killed_insufficient_n",
    "killed_concentration",
    "killed_economic",
    "killed_fragile",
    "superseded",
)
SCOUT_DECISION_SURVIVE = "survive"
CLOSED_DECISIONS: tuple[str, ...] = (SCOUT_DECISION_SURVIVE,) + KILL_REASONS

_LEDGER_DIR_ENV = "TAPEOLOGY_MICRO_SCOUT_DIR"

# The durable tail anchor (module docstring) -- a SIBLING of ledger.jsonl inside the same resolved
# scout-ledger directory, alongside the operational `runs.jsonl` build-run log that already lives
# there. Never a Config field: an on-disk file name, not a value that shapes a served result.
_HEAD_ANCHOR_NAME = "chain_head.json"


def resolve_scout_ledger_dir(dataset_dir_resolved: str) -> str:
    """``TAPEOLOGY_MICRO_SCOUT_DIR`` if set, else a ``micro_scout`` SIBLING of the caller's
    already-resolved dataset directory -- the ``resolve_micro_snapshots_dir`` pattern verbatim."""
    override = os.environ.get(_LEDGER_DIR_ENV)
    if override:
        return override
    return str(Path(dataset_dir_resolved).parent / "micro_scout")


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding this module hashes -- the identical sorted-keys, no-
    whitespace shape every sibling store/ledger in this codebase hashes (``desk_playbook_log.py``,
    ``micro_features.py``, ...)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def compute_family_root_id(
    feature_family_name: str, structure_context_kind: str, outcome_horizon_family: str
) -> str:
    """spec section 5.1 (r2): ``sha256(canonical(feature_family_name, structure_context_kind,
    outcome_horizon_family))[:16]`` -- COMPUTED, never declared, so a renamed or re-parameterized
    family with the SAME triple always resolves to the SAME root (TR-20's rename-attack refusal --
    a J-06/vault concern this iteration only computes and records, never acts on)."""
    return _sha256(
        _canonical(
            {
                "feature_family_name": feature_family_name,
                "structure_context_kind": structure_context_kind,
                "outcome_horizon_family": outcome_horizon_family,
            }
        )
    )[:16]


def compute_spec_hash(spec_fields: dict) -> str:
    """The frozen candidate spec's own content hash -- a PURE function of its fields, deliberately
    EXCLUDING any wall-clock-derived value (``registered_at`` is never part of ``spec_fields``): two
    genuinely separate registration acts of the identical candidate definition (e.g. the manager run
    and the CLI run of the SAME grid, TC-11) must compute the identical ``spec_hash`` even though
    their own ``registered_at`` timestamps necessarily differ."""
    return _sha256(_canonical(spec_fields))


def derive_family_id(feature_name: str, structure_context_kind: str, horizon_key: str) -> str:
    """The grid-registration grouping key (SCOUT_MAX_VARIANTS_PER_FAMILY's own bucket and
    ``variants_tried``'s own denominator) -- deliberately FINER-GRAINED than ``family_root_id``:
    a specific feature name + a specific horizon_key (e.g. ``trades_20`` vs ``trades_100``) are
    different grid-management families here, even though they may share one coarser
    ``family_root_id`` lineage (module docstring)."""
    return f"{feature_name}__{structure_context_kind}__{horizon_key}"


def distinct_variant_count(rows: list[dict]) -> int:
    """The union-N denominator over ``rows``: how many DISTINCT variants they represent, counted by
    ``candidate_id`` (which is itself ``cand-<spec_hash[:16]>`` -- a pure content hash of the frozen
    candidate spec, so two rows carrying the same one are the same variant definition evaluated
    twice, never two things tried).

    **iter-4 audit fix.** This was ``len(rows)``, i.e. a count of ledger ROWS, which made
    ``variants_tried`` a count of EVALUATIONS instead: re-running the identical grid (the
    operator-triggered ``POST /research/desk/micro/scout/compute``, which registers the identical
    ``spec_hash``es every time) inflated a family's served denominator by the grid's own width on
    every run, so the best-of-N disclosure's own sentence ("with n=24 variants tried in this
    family") stated a number no one had ever tried -- and, worse, drove every family into
    ``SCOUT_MAX_VARIANTS_PER_FAMILY`` after 12 identical runs, permanently refusing the default grid
    with no recovery an append-only ledger is allowed to offer. Counting variants, not
    evaluations, is both the spec's own word ("union-N") and the statistically correct
    multiple-comparisons denominator. Every row is still permanently on record either way -- this
    changes only the COUNT, never what is kept (the denominator still never shrinks).

    A row with no ``candidate_id`` at all (the spec's own illustrative TR-11 rows, and any row
    planted through this storage primitive directly) has no variant identity to deduplicate on and
    counts individually -- the honest reading of "one row, one unknown variant"."""
    seen: set[str] = set()
    anonymous = 0
    for row in rows:
        candidate_id = row.get("candidate_id")
        if candidate_id is None:
            anonymous += 1
        else:
            seen.add(candidate_id)
    return len(seen) + anonymous


class ScoutLedgerIntegrityError(Exception):
    """A ledger line failed to parse as JSON -- corrupted or tampered at the file level (distinct
    from a ``verify_chain()`` content/link mismatch, which is a well-formed-but-tampered row)."""


class ScoutLedger:
    """File-based store rooted at the resolved scout-ledger directory -- the ONE reader/writer of
    ``ledger.jsonl``. Enforces no business rule (module docstring); a caller wanting
    ``SCOUT_MAX_VARIANTS_PER_FAMILY``/TR-9 enforcement uses ``scout.py``'s registration entry point,
    which calls ``append_row`` only after both checks pass."""

    def __init__(self, root_dir: str | Path) -> None:
        self._root = Path(root_dir)
        self._path = self._root / "ledger.jsonl"
        self._head_path = self._root / _HEAD_ANCHOR_NAME

    @property
    def path(self) -> Path:
        return self._path

    def _read_raw(self) -> list[dict]:
        """Every row, append order, parsed but NOT chain-verified -- ``verify_chain()`` is the
        explicit tamper check; a caller just wanting the data (``all_rows``/``rows_for_family``)
        reads it directly, exactly like ``micro_snapshots.read_snapshot_rows``'s "plain reader"
        precedent."""
        if not self._path.exists():
            return []
        rows: list[dict] = []
        text = self._path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError as exc:
                raise ScoutLedgerIntegrityError(
                    f"scout ledger line {line_no} of '{self._path}' is not parseable JSON ({exc}) "
                    "-- corrupted or tampered"
                ) from exc
        return rows

    def all_rows(self) -> list[dict]:
        """Every permanent row ever appended, in append order -- kills, supersessions, and
        survivors alike (never filtered, never deleted; the module docstring's "denominator never
        shrinks" rail, mechanically)."""
        return self._read_raw()

    def rows_for_family(self, family_id: str) -> list[dict]:
        """Every row of ONE ``family_id``, append order -- the union across every ``grid_version``
        ever registered for it (TR-11)."""
        return [row for row in self._read_raw() if row.get("family_id") == family_id]

    def variants_tried_for_family(self, family_id: str) -> int:
        """The family's current union-N denominator -- ``distinct_variant_count(rows_for_family
        (...))`` (see that function's own docstring for why it counts VARIANTS, not rows), identical
        to the ``variants_tried`` value ``append_row`` embeds on that family's own most recent row
        (TC-2)."""
        return distinct_variant_count(self.rows_for_family(family_id))

    def append_row(self, fields: dict) -> dict:
        """Persist ONE new permanent row: hash-chains ``fields`` onto whatever is currently on disk
        (``prev_hash`` = the CURRENT last row's own ``row_hash``, or ``None`` for the very first row
        ever appended to this ledger) and stamps this row's own running ``variants_tried`` for its
        ``family_id`` (``distinct_variant_count`` as of this row -- no cap enforcement here). ALWAYS
        a genuinely new row -- no content-keyed dedup exists in this store (the
        ``PlaybookRunStore.record`` precedent), so the identical ``fields`` appended twice still
        yields two permanent rows with two distinct ``row_hash``es (their ``row_index`` and
        ``prev_hash`` differ even when every other field, ``variants_tried`` included, is
        identical -- re-evaluating a variant already on record adds an evaluation, never a variant)."""
        existing = self._read_raw()
        prev_hash = existing[-1]["row_hash"] if existing else None
        family_id = fields.get("family_id")
        family_rows = [row for row in existing if row.get("family_id") == family_id]
        variants_tried = distinct_variant_count([*family_rows, fields])
        content = {
            **fields,
            "row_index": len(existing),
            "prev_hash": prev_hash,
            "variants_tried": variants_tried,
        }
        row_hash = _sha256(_canonical(content))
        row = {**content, "row_hash": row_hash}
        self._root.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True))
            fh.write("\n")
        # The tail anchor, written AFTER the row it commits to (module docstring): a crash between
        # the two leaves the ledger longer than the anchor -- benign -- never falsely short.
        self._head_path.write_text(
            json.dumps({"row_count": len(existing) + 1, "head_hash": row_hash}, sort_keys=True),
            encoding="utf-8",
        )
        return dict(row)

    def verify_chain(self) -> dict:
        """Walks every row in append order, recomputing each row's own content hash (catches an
        in-place edit AT that row, TC-3) and re-checking its ``prev_hash`` against the PRECEDING
        row's actually-stored ``row_hash`` (catches a deletion/reordering at the first row whose
        link no longer resolves). Returns ``{"ok": True, "failed_at_row": None, "reason": None}`` on
        a clean chain, else ``{"ok": False, "failed_at_row": <int>, "reason": <str>}`` -- never
        raises, so a caller can report the failure rather than crash on it."""
        rows = self._read_raw()
        prev_stored: str | None = None
        for i, row in enumerate(rows):
            content = {k: v for k, v in row.items() if k != "row_hash"}
            recomputed = _sha256(_canonical(content))
            if recomputed != row.get("row_hash"):
                return {"ok": False, "failed_at_row": i, "reason": "content_hash_mismatch"}
            if row.get("prev_hash") != prev_stored:
                return {"ok": False, "failed_at_row": i, "reason": "prev_hash_mismatch"}
            prev_stored = row["row_hash"]
        return self._verify_tail(rows)

    def _verify_tail(self, rows: list[dict]) -> dict:
        """The durable-head-anchor half of ``verify_chain`` (module docstring): the walk above
        cannot see rows that are simply GONE from the end, so the anchor is what catches them."""
        anchor = self._read_head_anchor()
        if anchor is None:
            if not rows:
                return {"ok": True, "failed_at_row": None, "reason": None}
            return {"ok": False, "failed_at_row": None, "reason": "head_anchor_missing"}
        anchored_count = anchor.get("row_count", 0)
        if len(rows) < anchored_count:
            return {"ok": False, "failed_at_row": len(rows), "reason": "tail_truncated"}
        if anchored_count > 0 and rows[anchored_count - 1].get("row_hash") != anchor.get("head_hash"):
            return {"ok": False, "failed_at_row": anchored_count - 1, "reason": "head_hash_mismatch"}
        return {"ok": True, "failed_at_row": None, "reason": None}

    def _read_head_anchor(self) -> dict | None:
        """``None`` when no anchor exists (an honest absence, reported as ``head_anchor_missing``
        by ``_verify_tail`` for a non-empty ledger) or when it is unreadable -- an anchor that
        cannot be parsed certifies nothing, which is the same answer as having none."""
        if not self._head_path.exists():
            return None
        try:
            parsed = json.loads(self._head_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return parsed if isinstance(parsed, dict) else None
