"""The PnL-history CLI (``app.research.pnl_history``) — era-5B J-08 additive ``--append-report``
+ ``--out`` flags. Every test here targets an explicit ``tmp_path`` output (via ``--out`` /
``path=``) and a ``tmp_path``-scoped journal DB (via ``TAPEOLOGY_JOURNAL_DB``) — NEVER the real
committed ``reports/pnl/pnl-history.md`` or the real operator journal (Key Test Scenario 9's
"never the committed file" discipline).

``append_strategy_comparison_row``'s own composition/labeling logic (cell shape, no-pooling,
``insufficient_sample`` verbatim, malformed-report refusal) is exhaustively covered in
``tests/test_pnl_ledger.py``; this file covers ONLY the CLI-level plumbing (argument handling, the
append-then-render sequencing, and that omitting the new flags reproduces the pre-J-08 behaviour
byte-for-byte).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from app.config import CONFIG, STRATEGY_V1_ID
from app.research import pnl_history
from app.research.pnl_history import append_strategy_comparison_and_render
from app.research.pnl_ledger import LedgerCompositionError, REGISTER
from app.research.store import DuplicateEnhancementError, JournalStore

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _report(train_cells: list[dict] | None = None, holdout_cells: list[dict] | None = None) -> dict:
    return {
        "register": REGISTER,
        "pnl_min_sample_size": CONFIG.pnl_min_sample_size,
        "train": {"cells": train_cells or []},
        "holdout": {"cells": holdout_cells or []},
        "surviving_train_cells": [],
    }


def _cell(*, n: int = 6, net_r: float = 1.0, net_usd: float = 100.0) -> dict:
    return {
        "strategy_id": STRATEGY_V1_ID,
        "band_class": "A",
        "band_side": "resistance",
        "reaction": "broke",
        "feed": "sim",
        "dataset_ids": ["ds-1"],
        "measurement": {
            "n": n, "gross_r": net_r, "net_r": net_r, "gross_usd": net_usd, "net_usd": net_usd,
            "win_rate": 1.0, "max_drawdown_r": 0.0,
        },
        "null_baseline": {
            "n": 100, "gross_r": -1.0, "net_r": -1.0, "gross_usd": -100.0, "net_usd": -100.0,
            "win_rate": 0.4, "max_drawdown_r": 1.0,
        },
        "insufficient_sample": n < CONFIG.pnl_min_sample_size,
    }


# --- append_strategy_comparison_and_render (the function J-08 adds) ----------------------------


def test_append_and_render_writes_the_new_row_and_regenerates_markdown(tmp_path):
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    out_path = tmp_path / "history.md"
    try:
        written = append_strategy_comparison_and_render(
            store, CONFIG,
            enhancement_id="e-cli-1", title="cli append test",
            report=_report([_cell()]), path=out_path,
        )
    finally:
        store.close()

    assert written == out_path
    text = out_path.read_text()
    assert "cli append test" in text
    assert "e-cli-1" in text
    assert "strategy | class | side | reaction | feed" in text


def test_append_and_render_raises_and_writes_nothing_on_a_malformed_report(tmp_path):
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    out_path = tmp_path / "history.md"
    try:
        with pytest.raises(LedgerCompositionError):
            append_strategy_comparison_and_render(
                store, CONFIG,
                enhancement_id="e-cli-bad", title="bad",
                report={"train": {"cells": []}},  # missing "holdout"
                path=out_path,
            )
    finally:
        store.close()
    assert store.list_pnl_ledger() == []  # nothing appended
    assert not out_path.exists()  # rendering never ran either — the honest refusal wrote nothing


def test_append_and_render_duplicate_enhancement_id_writes_nothing_new(tmp_path):
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    out_path = tmp_path / "history.md"
    try:
        append_strategy_comparison_and_render(
            store, CONFIG, enhancement_id="e-cli-dup", title="t1", report=_report([_cell()]), path=out_path
        )
        with pytest.raises(DuplicateEnhancementError):
            append_strategy_comparison_and_render(
                store, CONFIG, enhancement_id="e-cli-dup", title="t2", report=_report([_cell()]), path=out_path
            )
    finally:
        store.close()
    assert len(store.list_pnl_ledger()) == 1  # the refused second append changed nothing


# --- main() CLI wiring: every call targets --out (never the real committed path) ----------------


def test_main_without_append_flag_matches_the_pre_j08_render_only_behavior(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    out_path = tmp_path / "history.md"
    monkeypatch.setattr(sys, "argv", ["pnl_history", "--out", str(out_path)])

    exit_code = pnl_history.main()

    assert exit_code == 0
    assert out_path.exists()
    assert "ledger is empty" in out_path.read_text()  # honest empty state, nothing appended


def test_main_with_append_report_flag_appends_and_renders_in_one_step(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_report([_cell()])))
    out_path = tmp_path / "history.md"
    monkeypatch.setattr(
        sys, "argv",
        [
            "pnl_history", "--append-report", str(report_path),
            "--enhancement-id", "e-main-append", "--title", "main append test",
            "--out", str(out_path),
        ],
    )

    exit_code = pnl_history.main()

    assert exit_code == 0
    text = out_path.read_text()
    assert "main append test" in text
    assert "e-main-append" in text


def test_main_append_report_missing_required_flags_is_an_explicit_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_report([_cell()])))
    out_path = tmp_path / "history.md"
    monkeypatch.setattr(
        sys, "argv", ["pnl_history", "--append-report", str(report_path), "--out", str(out_path)]
    )  # --enhancement-id / --title both omitted

    exit_code = pnl_history.main()

    assert exit_code == 1
    assert "--enhancement-id" in capsys.readouterr().err
    assert not out_path.exists()  # nothing rendered on the argument-validation refusal


def test_main_append_report_malformed_json_file_is_an_explicit_error(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps({"train": {"cells": []}}))  # missing "holdout"
    out_path = tmp_path / "history.md"
    monkeypatch.setattr(
        sys, "argv",
        [
            "pnl_history", "--append-report", str(report_path),
            "--enhancement-id", "e-malformed", "--title", "t", "--out", str(out_path),
        ],
    )

    exit_code = pnl_history.main()

    assert exit_code == 1
    assert not out_path.exists()
