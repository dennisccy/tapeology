"""``micro_chain_ledger.py`` -- Era "The Rapid Microscope" J-05: the ONE hash-chained,

append-only, tail-anchored ledger primitive shared by this iteration's TWO new ledgers
(``micro_accessor.ExposureRegistry`` and ``walkforward_ledger.WalkForwardLedger``).

**Why a shared primitive now, when ``scout_ledger.py`` already has this exact pattern.**
``scout_ledger.py``'s own hash-chain-plus-tail-anchor mechanics (iter-4 audit fix B2) are a
Do-Not-Redo module this iteration must not touch. But THIS iteration needs the identical
tamper-evident discipline TWICE more -- the §6.7 exposure registry and the fold/sequence/voiding
ledger -- and duplicating the ~60-line mechanic a second AND third time inside two unrelated
files would be the exact "second, independently-valued copy" anti-pattern this codebase's own
conventions warn against elsewhere (e.g. ``micro_readiness.py``'s docstring on
``WF_TRAIN_MIN_SESSIONS``). Factoring ONE shared primitive for these two NEW, same-iteration call
sites is the "third occurrence" the simplicity bar allows -- ``scout_ledger.py`` stays byte-
untouched and does not import this module; this module does not import ``scout_ledger.py`` either
(no coupling introduced between them).

**The mechanic, copied faithfully from ``scout_ledger.py``'s own iter-4-audited design (not
imported, since that module is Do-Not-Redo and deliberately un-generic -- it stamps a
Scout-specific ``variants_tried`` onto every row, which this shared primitive must NOT do):** each
row's ``row_hash`` commits to its own content AND the previous row's own ``row_hash`` (a genuine
link -- content-hash mismatch is caught directly at the tampered row; a prev_hash mismatch is
caught at the first row whose predecessor no longer matches, also directly). A durable
``chain_head.json`` tail anchor (``{"row_count", "head_hash"}``), written AFTER the row it commits
to, closes the chain's own blind spot -- a hash chain by itself cannot see rows simply MISSING
from its own end (iter-4 audit fix B2's own lesson, applied here from day one rather than
retrofitted after an audit finds it a second time)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

__all__ = ["HashChainedLedgerIntegrityError", "HashChainedLedger"]

_HEAD_ANCHOR_NAME = "chain_head.json"


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding this module hashes -- the identical sorted-keys,
    no-whitespace shape every sibling store/ledger in this codebase hashes (``scout_ledger.py``,
    ``desk_playbook_log.py``, ``micro_features.py``, ...)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class HashChainedLedgerIntegrityError(Exception):
    """A ledger line failed to parse as JSON -- corrupted or tampered at the file level (distinct
    from a ``verify_chain()`` content/link mismatch, which is a well-formed-but-tampered row)."""


class HashChainedLedger:
    """File-based store rooted at ``root_dir / filename`` -- the ONE reader/writer of that one
    JSONL file. Enforces no business rule of its own (the ``scout_ledger.ScoutLedger`` split):
    ``append_row`` hash-chains and persists whatever content dict it is given; a caller wanting a
    domain-specific derived field (e.g. a running denominator) stamps it onto ``fields`` itself,
    BEFORE calling ``append_row`` -- this primitive never inspects field content beyond the
    ``row_hash``/``prev_hash``/``row_index`` it manages."""

    def __init__(self, root_dir: str | Path, filename: str) -> None:
        self._root = Path(root_dir)
        self._path = self._root / filename
        self._head_path = self._root / f"{filename}.{_HEAD_ANCHOR_NAME}"

    @property
    def path(self) -> Path:
        return self._path

    def _read_raw(self) -> list[dict]:
        """Every row, append order, parsed but NOT chain-verified -- ``verify_chain()`` is the
        explicit tamper check; a caller just wanting the data reads this (or ``all_rows``)
        directly, exactly like ``micro_snapshots.read_snapshot_rows``'s "plain reader" precedent."""
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
                raise HashChainedLedgerIntegrityError(
                    f"ledger line {line_no} of '{self._path}' is not parseable JSON ({exc}) -- "
                    "corrupted or tampered"
                ) from exc
        return rows

    def all_rows(self) -> list[dict]:
        """Every permanent row ever appended, in append order -- never filtered, never deleted."""
        return self._read_raw()

    def append_row(self, fields: dict) -> dict:
        """Persist ONE new permanent row: hash-chains ``fields`` onto whatever is currently on
        disk (``prev_hash`` = the CURRENT last row's own ``row_hash``, or ``None`` for the very
        first row) and stamps ``row_index``. ALWAYS a genuinely new row -- no content-keyed dedup
        exists in this store, so identical ``fields`` appended twice yields two permanent rows with
        two distinct ``row_hash``es (their ``row_index``/``prev_hash`` differ)."""
        existing = self._read_raw()
        prev_hash = existing[-1]["row_hash"] if existing else None
        content = {**fields, "row_index": len(existing), "prev_hash": prev_hash}
        row_hash = _sha256(_canonical(content))
        row = {**content, "row_hash": row_hash}
        self._root.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True))
            fh.write("\n")
        # The tail anchor, written AFTER the row it commits to (module docstring): a crash between
        # the two leaves the ledger LONGER than the anchor -- benign -- never falsely short.
        self._head_path.write_text(
            json.dumps({"row_count": len(existing) + 1, "head_hash": row_hash}, sort_keys=True),
            encoding="utf-8",
        )
        return dict(row)

    def verify_chain(self) -> dict:
        """Walks every row in append order, recomputing each row's own content hash (catches an
        in-place edit AT that row) and re-checking its ``prev_hash`` against the PRECEDING row's
        actually-stored ``row_hash`` (catches a deletion/reordering at the first row whose link no
        longer resolves), THEN checks the durable tail anchor (catches a tail truncation the chain
        walk alone cannot see). Returns ``{"ok": True, "failed_at_row": None, "reason": None}`` on
        a clean, complete chain, else ``{"ok": False, "failed_at_row": <int|None>, "reason": <str>}``
        -- never raises, so a caller can report the failure rather than crash on it."""
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
        if not self._head_path.exists():
            return None
        try:
            parsed = json.loads(self._head_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return parsed if isinstance(parsed, dict) else None
