"""``micro_chain_ledger.py`` (Era "The Rapid Microscope" J-05) -- the shared hash-chain +
tail-anchor primitive ``micro_accessor.ExposureRegistry`` and ``walkforward_ledger.
WalkForwardLedger`` both build on. Tested directly, once, here -- the iter-4 audit's own lesson
(``scout_ledger.py``'s B2 fix) applied to a NEW primitive from day one rather than re-discovered
per ledger that uses it."""

from __future__ import annotations

import json

from app.research.micro_chain_ledger import HashChainedLedger


def test_append_row_chains_and_stamps_row_index(tmp_path):
    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
    row0 = ledger.append_row({"value": "a"})
    row1 = ledger.append_row({"value": "b"})
    assert row0["row_index"] == 0
    assert row0["prev_hash"] is None
    assert row1["row_index"] == 1
    assert row1["prev_hash"] == row0["row_hash"]
    assert row0["row_hash"] != row1["row_hash"]


def test_identical_fields_appended_twice_yield_two_distinct_permanent_rows(tmp_path):
    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
    first = ledger.append_row({"value": "same"})
    second = ledger.append_row({"value": "same"})
    assert first["row_hash"] != second["row_hash"]
    assert len(ledger.all_rows()) == 2


def test_verify_chain_ok_on_a_clean_chain(tmp_path):
    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
    ledger.append_row({"value": "a"})
    ledger.append_row({"value": "b"})
    ledger.append_row({"value": "c"})
    assert ledger.verify_chain() == {"ok": True, "failed_at_row": None, "reason": None}


def test_verify_chain_ok_on_an_empty_ledger(tmp_path):
    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
    assert ledger.verify_chain() == {"ok": True, "failed_at_row": None, "reason": None}


def test_in_place_edit_of_a_row_is_caught_at_that_row(tmp_path):
    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
    ledger.append_row({"value": "a"})
    ledger.append_row({"value": "b"})
    ledger.append_row({"value": "c"})
    lines = ledger.path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[1])
    tampered["value"] = "TAMPERED"
    lines[1] = json.dumps(tampered, sort_keys=True)
    ledger.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = ledger.verify_chain()
    assert result == {"ok": False, "failed_at_row": 1, "reason": "content_hash_mismatch"}


def test_mid_file_deletion_is_caught_at_the_first_row_whose_link_breaks(tmp_path):
    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
    ledger.append_row({"value": "a"})
    ledger.append_row({"value": "b"})
    ledger.append_row({"value": "c"})
    lines = ledger.path.read_text(encoding="utf-8").splitlines()
    del lines[1]  # delete the middle row -- row 2's prev_hash no longer resolves
    ledger.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = ledger.verify_chain()
    assert result["ok"] is False
    assert result["reason"] == "prev_hash_mismatch"


def test_tail_truncation_is_caught_by_the_durable_anchor_even_though_the_chain_still_verifies(tmp_path):
    """The iter-4 audit's own B2 lesson: a hash chain alone cannot see rows simply MISSING from
    its own end -- every surviving row stays perfectly self-consistent. The durable tail anchor
    (written AFTER each row it commits to) is what catches it."""
    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
    ledger.append_row({"value": "a"})
    ledger.append_row({"value": "b"})
    ledger.append_row({"value": "c"})
    lines = ledger.path.read_text(encoding="utf-8").splitlines()
    del lines[-1]  # delete the LAST row -- the remaining chain is perfectly self-consistent
    ledger.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = ledger.verify_chain()
    assert result == {"ok": False, "failed_at_row": 2, "reason": "tail_truncated"}


def test_a_ledger_with_rows_but_no_anchor_file_reports_head_anchor_missing(tmp_path):
    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
    ledger.append_row({"value": "a"})
    ledger._head_path.unlink()  # simulate a ledger whose anchor file was never written/lost
    result = ledger.verify_chain()
    assert result == {"ok": False, "failed_at_row": None, "reason": "head_anchor_missing"}


def test_anchor_written_after_the_row_it_commits_to_a_shorter_chain_than_the_anchor_is_the_only_bad_state(tmp_path):
    """A crash BETWEEN writing the row and writing the anchor leaves the ledger LONGER than the
    anchor claims -- benign, and still verified against the anchored prefix (module docstring)."""
    ledger = HashChainedLedger(tmp_path, "rows.jsonl")
    ledger.append_row({"value": "a"})
    anchor_after_one = json.loads(ledger._head_path.read_text(encoding="utf-8"))
    ledger.append_row({"value": "b"})  # a "crash" here would leave the ledger 2 rows, anchor at 1
    ledger._head_path.write_text(json.dumps(anchor_after_one, sort_keys=True), encoding="utf-8")
    result = ledger.verify_chain()
    assert result == {"ok": True, "failed_at_row": None, "reason": None}


def test_two_independent_ledgers_in_the_same_root_dir_do_not_collide(tmp_path):
    a = HashChainedLedger(tmp_path, "a.jsonl")
    b = HashChainedLedger(tmp_path, "b.jsonl")
    a.append_row({"who": "a"})
    b.append_row({"who": "b"})
    b.append_row({"who": "b2"})
    assert len(a.all_rows()) == 1
    assert len(b.all_rows()) == 2
