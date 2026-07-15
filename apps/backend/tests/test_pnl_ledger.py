"""The append-only PnL ledger (era-3 capability 5, J-04) — Data Contract row 32.

Everything here is hermetic and keyless: backtest reports are produced by the REAL runner
(``BacktestJobManager.create`` + ``run_sync``) over the committed fixture dataset pair (read-only)
or freshly recorded reference-window datasets in a temp dir, ledger rows are composed by the ONE
writer module (``app.research.pnl_ledger``), and the markdown is a pure render of the stored rows.

Locked disciplines (each an anti-goal or a J-04 acceptance clause):
  * the founding row's per-split net R / net $ / n are VERBATIM copies of the persisted source
    backtest reports' aggregates (asserted by equality against the row-31 payloads fetched by
    report id — no recomputation tolerance);
  * the repository is append-only at the surface (no update/delete method; no UPDATE/DELETE SQL
    targets the table) — the ``verdict_events`` standard;
  * the founding baseline side is explicitly ``None`` (never fabricated zeros) with the
    config-owned founding id/title;
  * the seeding path is deterministic (identical row values across fresh stores, identity fields
    excepted) and idempotent (re-run → explicit no-op, ledger byte-identical);
  * the "insufficient sample" label is config-owned, exercised BOTH ways, and identical on the
    REST projection and the markdown render (ONE labeling function);
  * the markdown is a byte-level no-op on unchanged rows, dd-MM-yyyy dates, register verbatim,
    every $ beside its R and its n, train/hold-out separate, honest explicit empty state;
  * the labeling-only ``pnl_min_sample_size`` and the operational ``pnl_history_md_path`` are
    EXCLUDED from ``config_fingerprint`` (pinned both ways against a row-shaping counter-value).
"""

from __future__ import annotations

import dataclasses
import inspect
import json
from pathlib import Path

import pytest

from app.config import CONFIG, Config, STRATEGY_V1_ID
from app.research.backtests import (
    BacktestJobManager,
    PROFILE_DEFAULT,
    REGISTER,
    STATUS_DONE,
)
from app.research.datasets import DatasetStore
from app.research.pnl_baseline import seed_founding_row
from app.research.pnl_ledger import (
    LedgerCompositionError,
    append_strategy_comparison_row,
    append_validation_row,
    ledger_projection,
    render_history_markdown,
    write_history_markdown,
)
from app.research.store import DuplicateEnhancementError, JournalStore, PnlLedgerRecord

BACKEND_DIR = Path(__file__).resolve().parents[1]
# The committed miniature train + holdout dataset pair (recorded ONCE through the real record
# path) — the keyless CI substrate the founding row measures. READ-ONLY here.
FIXTURE_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets"


# --- shared substrate: the two fixture-pair backtest reports, run ONCE ------------------------------


def _run_backtest(jobs: BacktestJobManager, store: JournalStore, dstore: DatasetStore, dataset_id: str) -> dict:
    payload = jobs.create(
        {"dataset_id": dataset_id, "strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
    )
    jobs.run_sync(payload["id"], dataset_store=dstore)
    return store.get_backtest(payload["id"]).payload


@pytest.fixture(scope="module")
def reports_ctx(tmp_path_factory):
    """One journal store carrying a COMPLETED backtest report per fixture split (train, holdout).

    Module-scoped so the two real backtests run once; composition tests write DISTINCT enhancement
    ids and assert only rows they created."""
    store = JournalStore(str(tmp_path_factory.mktemp("pnl-journal") / "journal.db"), CONFIG)
    dstore = DatasetStore(FIXTURE_DATASET_DIR)
    records, errors = dstore.list()
    assert errors == [] and len(records) == 2
    by_split = {meta["split"]: meta for meta in records}
    jobs = BacktestJobManager(store, CONFIG)
    train_report = _run_backtest(jobs, store, dstore, by_split["train"]["id"])
    holdout_report = _run_backtest(jobs, store, dstore, by_split["holdout"]["id"])
    assert train_report["status"] == STATUS_DONE and holdout_report["status"] == STATUS_DONE
    yield store, dstore, train_report, holdout_report
    store.close()


@pytest.fixture
def fresh_store(tmp_path):
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    yield store
    store.close()


def _ledger_row(enhancement_id: str = "e1", *, train_n: int = 5, holdout_n: int = 3) -> dict:
    """A hand-built STORED row payload for store/projection/render tests (the store serves rows
    verbatim; label/format logic never depends on how the row was composed)."""
    return {
        "enhancement_id": enhancement_id,
        "title": f"test enhancement {enhancement_id}",
        "founding": True,
        "baseline": None,
        "candidate": {
            "train": {"net_r": -1.25, "net_usd": -125.0, "n": train_n},
            "holdout": {"net_r": 0.5, "net_usd": 50.0, "n": holdout_n},
        },
        "provenance": {
            "strategy_id": STRATEGY_V1_ID,
            "profile": PROFILE_DEFAULT,
            "config_fingerprint": "fp-test",
            "train": {"backtest_id": "bt-train", "dataset_id": "ds-train", "dataset_checksum": "ck-train"},
            "holdout": {"backtest_id": "bt-holdout", "dataset_id": "ds-holdout", "dataset_checksum": "ck-holdout"},
        },
        "created_wall_ts": 1767225600.0,  # 2026-01-01T00:00:00Z
        "created_utc": "2026-01-01T00:00:00.000000Z",
    }


def _append(store: JournalStore, payload: dict) -> None:
    store.append_pnl_ledger_row(
        PnlLedgerRecord(
            enhancement_id=payload["enhancement_id"],
            payload=payload,
            created_wall_ts=payload["created_wall_ts"],
        )
    )


# --- the repository is append-only (the verdict_events standard, store.py) -------------------------


def test_pnl_ledger_repository_is_append_only_at_the_surface():
    # The append-only discipline is a REPOSITORY-level guarantee: the store exposes NO
    # update/delete method for ledger rows. Assert the surface, not just behaviour.
    public = {n for n in dir(JournalStore) if not n.startswith("_")}
    for forbidden in (
        "update_pnl_ledger_row",
        "delete_pnl_ledger_row",
        "edit_pnl_ledger_row",
        "remove_pnl_ledger_row",
        "set_pnl_ledger_row",
        "update_pnl_ledger",
        "delete_pnl_ledger",
    ):
        assert forbidden not in public, f"repository must not expose {forbidden}"
    # No public pnl method is a mutator other than the one append.
    for name in public:
        if "pnl" in name:
            assert not any(
                verb in name for verb in ("update", "delete", "edit", "remove", "set")
            ), f"mutating pnl method {name!r} must not exist"
    assert "append_pnl_ledger_row" in public


def test_no_update_or_delete_sql_targets_the_pnl_ledger_table():
    # No UPDATE/DELETE SQL targets pnl_ledger anywhere in the app source (migration bookkeeping
    # only touches schema_version). The scan is proven non-vacuous by requiring the INSERT.
    seen_insert = False
    for path in (BACKEND_DIR / "app").rglob("*.py"):
        src = path.read_text()
        assert "UPDATE pnl_ledger" not in src, f"UPDATE targets pnl_ledger in {path.name}"
        assert "DELETE FROM pnl_ledger" not in src, f"DELETE targets pnl_ledger in {path.name}"
        if "INSERT INTO pnl_ledger" in src:
            seen_insert = True
    assert seen_insert, "expected the one INSERT INTO pnl_ledger append in the app source"


def test_duplicate_enhancement_id_is_an_explicit_refusal(fresh_store):
    _append(fresh_store, _ledger_row("e-dup"))
    with pytest.raises(DuplicateEnhancementError) as excinfo:
        _append(fresh_store, _ledger_row("e-dup"))
    assert "e-dup" in str(excinfo.value)
    # One honest row per enhancement — the refusal appended/changed nothing.
    assert [r.enhancement_id for r in fresh_store.list_pnl_ledger()] == ["e-dup"]


def test_rows_survive_store_reload_verbatim_in_insertion_order(tmp_path):
    db = str(tmp_path / "journal.db")
    first = _ledger_row("e-a")
    second = _ledger_row("e-b", train_n=9)
    store = JournalStore(db, CONFIG)
    try:
        _append(store, first)
        _append(store, second)
    finally:
        store.close()
    reopened = JournalStore(db, CONFIG)
    try:
        rows = reopened.list_pnl_ledger()
        assert [r.enhancement_id for r in rows] == ["e-a", "e-b"]  # insertion order
        assert rows[0].payload == first and rows[1].payload == second  # verbatim
        assert reopened.get_pnl_ledger_row("e-a").payload == first
        assert reopened.get_pnl_ledger_row("missing") is None
    finally:
        reopened.close()


# --- row composition: verbatim copies of the persisted row-31 aggregates ---------------------------


def test_founding_row_values_equal_the_source_reports_exactly(reports_ctx):
    store, dstore, train_report, holdout_report = reports_ctx
    row = append_validation_row(
        store,
        CONFIG,
        enhancement_id="e-verbatim",
        title="verbatim copy proof",
        candidate_train_report_id=train_report["id"],
        candidate_holdout_report_id=holdout_report["id"],
    )
    # Served-verbatim: the appended payload IS the stored payload.
    assert store.get_pnl_ledger_row("e-verbatim").payload == row
    # Per-split net R / net $ / n equal the PERSISTED source aggregates EXACTLY (fetched by
    # report id — no recomputation tolerance).
    for split, report in (("train", train_report), ("holdout", holdout_report)):
        agg = store.get_backtest(report["id"]).payload["result"]["aggregates"]
        assert row["candidate"][split] == {
            "net_r": agg["net_r"],
            "net_usd": agg["net_usd"],
            "n": agg["n"],
        }
        prov = row["provenance"][split]
        dataset = report["result"]["dataset"]
        assert prov == {
            "backtest_id": report["id"],
            "dataset_id": dataset["id"],
            "dataset_checksum": dataset["checksum"],
        }
        assert dataset["split"] == split  # never pooled: each side measures its own frozen split
    # Shared provenance stamps, copied from the reports (which agree).
    assert row["provenance"]["strategy_id"] == STRATEGY_V1_ID
    assert row["provenance"]["profile"] == PROFILE_DEFAULT
    assert row["provenance"]["config_fingerprint"] == train_report["result"]["config_fingerprint"]
    # Train and hold-out stay separate: the exact key sets carry NO pooled/combined figure.
    assert set(row["candidate"]) == {"train", "holdout"}
    assert set(row) == {
        "enhancement_id", "title", "founding", "baseline", "candidate", "provenance",
        "created_wall_ts", "created_utc",
    }
    # Founding honesty: the baseline side is explicitly None — never fabricated zeros.
    assert row["founding"] is True and row["baseline"] is None
    assert isinstance(row["created_wall_ts"], float) and row["created_utc"].endswith("Z")


def test_composition_refuses_missing_incomplete_or_wrong_split_reports(reports_ctx):
    store, dstore, train_report, holdout_report = reports_ctx

    def _attempt(eid, train_id, holdout_id):
        return append_validation_row(
            store, CONFIG, enhancement_id=eid, title="refusal",
            candidate_train_report_id=train_id, candidate_holdout_report_id=holdout_id,
        )

    # Unknown source report id → explicit error, NO partial row.
    with pytest.raises(LedgerCompositionError):
        _attempt("e-missing", "no-such-report", holdout_report["id"])
    # A non-terminal (queued, never run) report → explicit error, NO partial row.
    queued = BacktestJobManager(store, CONFIG).create(
        {"dataset_id": "d-x", "strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
    )
    with pytest.raises(LedgerCompositionError):
        _attempt("e-queued", queued["id"], holdout_report["id"])
    # Split honesty: a hold-out report passed as the TRAIN side (and vice versa) → explicit error.
    with pytest.raises(LedgerCompositionError):
        _attempt("e-swapped", holdout_report["id"], train_report["id"])
    for eid in ("e-missing", "e-queued", "e-swapped"):
        assert store.get_pnl_ledger_row(eid) is None, "a refused composition must append nothing"


def test_composition_refuses_reports_from_different_fingerprints(reports_ctx, tmp_path):
    # Never pool across fingerprints: the two source reports must agree on strategy / profile /
    # config_fingerprint — a mismatch is an explicit refusal, never a silently mixed row.
    store, dstore, train_report, _ = reports_ctx
    other_config = dataclasses.replace(CONFIG, strategy_dollars_per_r=200.0)
    assert other_config.config_fingerprint() != CONFIG.config_fingerprint()
    records, _errors = dstore.list()
    holdout_meta = next(m for m in records if m["split"] == "holdout")
    other_jobs = BacktestJobManager(store, other_config)
    other_report = _run_backtest(other_jobs, store, dstore, holdout_meta["id"])
    with pytest.raises(LedgerCompositionError) as excinfo:
        append_validation_row(
            store, CONFIG, enhancement_id="e-mixed", title="mixed fingerprints",
            candidate_train_report_id=train_report["id"],
            candidate_holdout_report_id=other_report["id"],
        )
    assert "fingerprint" in str(excinfo.value)
    assert store.get_pnl_ledger_row("e-mixed") is None


def test_duplicate_enhancement_refusal_via_the_validation_path(reports_ctx):
    store, dstore, train_report, holdout_report = reports_ctx
    kwargs = dict(
        enhancement_id="e-once", title="one honest row per enhancement",
        candidate_train_report_id=train_report["id"],
        candidate_holdout_report_id=holdout_report["id"],
    )
    append_validation_row(store, CONFIG, **kwargs)
    before = store.get_pnl_ledger_row("e-once").payload
    with pytest.raises(DuplicateEnhancementError):
        append_validation_row(store, CONFIG, **kwargs)
    assert store.get_pnl_ledger_row("e-once").payload == before  # untouched by the refusal


# --- the founding seeding path: config-owned marker, idempotent, deterministic ----------------------


def _seed(tmp_path: Path, name: str, config: Config = CONFIG):
    store = JournalStore(str(tmp_path / f"{name}.db"), config)
    dstore = DatasetStore(tmp_path / f"{name}-datasets")
    created, row = seed_founding_row(store, dstore, config)
    return store, dstore, created, row


def test_seed_founding_row_records_the_frozen_fixture_pair_and_appends_once(tmp_path):
    store, dstore, created, row = _seed(tmp_path, "seed")
    try:
        assert created is True
        # The founding marker id/title come from CONFIG — never inline literals.
        assert row["enhancement_id"] == CONFIG.pnl_founding_enhancement_id
        assert row["title"] == CONFIG.pnl_founding_enhancement_title
        assert row["founding"] is True and row["baseline"] is None
        # The datasets were recorded through the REAL keyless reference path and are the SAME
        # frozen content as the committed fixture pair (content-addressed equality).
        committed = {m["split"]: m for m in DatasetStore(FIXTURE_DATASET_DIR).list()[0]}
        seeded = {m["split"]: m for m in dstore.list()[0]}
        for split in ("train", "holdout"):
            assert seeded[split]["checksum"] == committed[split]["checksum"]
            assert row["provenance"][split]["dataset_checksum"] == committed[split]["checksum"]
        # The measured values are verbatim copies of the seeded reports' persisted aggregates.
        for split in ("train", "holdout"):
            report = store.get_backtest(row["provenance"][split]["backtest_id"]).payload
            assert report["status"] == STATUS_DONE
            agg = report["result"]["aggregates"]
            assert row["candidate"][split] == {"net_r": agg["net_r"], "net_usd": agg["net_usd"], "n": agg["n"]}
        assert [r.enhancement_id for r in store.list_pnl_ledger()] == [row["enhancement_id"]]
    finally:
        store.close()


def test_seed_rerun_is_an_explicit_no_op_and_the_ledger_is_byte_identical(tmp_path):
    store, dstore, created, _ = _seed(tmp_path, "rerun")
    try:
        assert created is True
        before = json.dumps([r.payload for r in store.list_pnl_ledger()], sort_keys=True)
        backtests_before = len(store.list_backtests(limit=100))
        created_again, row_again = seed_founding_row(store, dstore, CONFIG)
        assert created_again is False  # the honest "already present" no-op
        assert row_again["enhancement_id"] == CONFIG.pnl_founding_enhancement_id
        after = json.dumps([r.payload for r in store.list_pnl_ledger()], sort_keys=True)
        assert after == before  # byte-identical — no duplicate row, no mutation
        # The no-op ran NO new backtests and recorded NO new datasets.
        assert len(store.list_backtests(limit=100)) == backtests_before
        assert len(dstore.list()[0]) == 2
    finally:
        store.close()


def _strip_identity(row: dict) -> dict:
    """Drop the run-identity fields (timestamps, per-run uuids) — the deterministic remainder
    mirrors the backtest result-payload separation."""
    stripped = json.loads(json.dumps(row))
    stripped.pop("created_wall_ts")
    stripped.pop("created_utc")
    for split in ("train", "holdout"):
        stripped["provenance"][split].pop("backtest_id")
        stripped["provenance"][split].pop("dataset_id")
    return stripped


def test_seeding_is_deterministic_across_fresh_stores(tmp_path):
    store_a, _, created_a, row_a = _seed(tmp_path, "det-a")
    store_b, _, created_b, row_b = _seed(tmp_path, "det-b")
    try:
        assert created_a is True and created_b is True
        assert json.dumps(_strip_identity(row_a), sort_keys=True) == json.dumps(
            _strip_identity(row_b), sort_keys=True
        )
    finally:
        store_a.close()
        store_b.close()


# --- the ONE serving projection: register + config-owned insufficient-sample labels ----------------


def test_projection_serves_rows_verbatim_with_register_and_labels_both_ways(fresh_store):
    _append(fresh_store, _ledger_row("e-label", train_n=5, holdout_n=3))
    # min = 5: train (n=5) unlabeled, holdout (n=3) labeled — the marker keeps n present.
    config = dataclasses.replace(CONFIG, pnl_min_sample_size=5)
    projection = ledger_projection(fresh_store, config)
    assert projection["register"] == REGISTER
    assert projection["min_sample_size"] == 5
    (row,) = projection["rows"]
    assert row["candidate"]["train"]["insufficient_sample"] is False
    assert row["candidate"]["holdout"]["insufficient_sample"] is True
    assert row["candidate"]["holdout"]["n"] == 3  # n still present beside the label
    # The stored values are served verbatim (the marker is the only addition).
    assert row["candidate"]["train"]["net_r"] == -1.25
    assert row["candidate"]["train"]["net_usd"] == -125.0
    # BOTH ways: a minimum at/below every n labels nothing…
    relaxed = ledger_projection(fresh_store, dataclasses.replace(CONFIG, pnl_min_sample_size=1))
    (row_relaxed,) = relaxed["rows"]
    assert row_relaxed["candidate"]["train"]["insufficient_sample"] is False
    assert row_relaxed["candidate"]["holdout"]["insufficient_sample"] is False
    # …and a minimum above every n labels everything.
    strict = ledger_projection(fresh_store, dataclasses.replace(CONFIG, pnl_min_sample_size=99))
    (row_strict,) = strict["rows"]
    assert row_strict["candidate"]["train"]["insufficient_sample"] is True
    assert row_strict["candidate"]["holdout"]["insufficient_sample"] is True
    # The projection never mutates the STORED row (labels are presentation, applied at read).
    stored = fresh_store.get_pnl_ledger_row("e-label").payload
    assert "insufficient_sample" not in stored["candidate"]["train"]


def test_projection_of_an_empty_ledger_is_an_honest_empty_list(fresh_store):
    projection = ledger_projection(fresh_store, CONFIG)
    assert projection["rows"] == []
    assert projection["register"] == REGISTER


# --- the markdown: a pure, deterministic render of the SAME projection -----------------------------


def test_markdown_regeneration_with_unchanged_rows_is_a_byte_level_no_op(fresh_store, tmp_path):
    _append(fresh_store, _ledger_row("e-md"))
    first = render_history_markdown(fresh_store, CONFIG)
    second = render_history_markdown(fresh_store, CONFIG)
    assert first == second  # byte-identical — no wall-clock, no environment-dependent formatting
    target = tmp_path / "reports" / "pnl" / "pnl-history.md"
    path_a = write_history_markdown(fresh_store, CONFIG, path=target)
    bytes_a = path_a.read_bytes()
    bytes_b = write_history_markdown(fresh_store, CONFIG, path=target).read_bytes()
    assert bytes_a == bytes_b == first.encode("utf-8")
    # Appending a row then regenerating CHANGES the file.
    _append(fresh_store, _ledger_row("e-md-2"))
    assert write_history_markdown(fresh_store, CONFIG, path=target).read_bytes() != bytes_a


def test_markdown_carries_register_dates_and_every_dollar_beside_its_r_and_n(fresh_store):
    _append(fresh_store, _ledger_row("e-format", train_n=5, holdout_n=3))
    config = dataclasses.replace(CONFIG, pnl_min_sample_size=5)
    md = render_history_markdown(fresh_store, config)
    # The register string appears VERBATIM (the one REGISTER constant).
    assert REGISTER in md
    # Dates render dd-MM-yyyy (foundation invariant 12) from the stored timestamp — the hand-built
    # row is stamped 2026-01-01T00:00:00Z.
    assert "01-01-2026" in md
    # Every $ figure sits beside its R figure and its n: each split renders on one line carrying
    # net R, net $, and n together; train and hold-out are separate lines (never pooled).
    train_lines = [l for l in md.splitlines() if "| train" in l and "candidate" in l]
    holdout_lines = [l for l in md.splitlines() if "| holdout" in l and "candidate" in l]
    assert len(train_lines) == 1 and len(holdout_lines) == 1
    assert "-1.25" in train_lines[0] and "-125.0" in train_lines[0] and "| 5 |" in train_lines[0]
    assert "0.5" in holdout_lines[0] and "50.0" in holdout_lines[0] and "| 3 |" in holdout_lines[0]
    # The label logic is IDENTICAL to REST (the same projection): holdout labeled, train not.
    assert "insufficient sample" in holdout_lines[0]
    assert "insufficient sample" not in train_lines[0]
    # The founding baseline side is explicit prose — never fabricated zeros.
    assert "no prior incumbent" in md
    # Train and hold-out are never pooled into a combined figure.
    assert "pooled" not in md.lower() or "never pooled" in md.lower()


def test_markdown_empty_ledger_renders_an_honest_explicit_empty_state(fresh_store):
    md = render_history_markdown(fresh_store, CONFIG)
    assert REGISTER in md
    assert "ledger is empty" in md
    render_again = render_history_markdown(fresh_store, CONFIG)
    assert md == render_again


def test_render_function_carries_no_wall_clock_or_environment_dependence():
    src = inspect.getsource(render_history_markdown)
    for forbidden in ("time.time", "datetime.now", "os.environ", "astimezone"):
        assert forbidden not in src, f"render must not depend on {forbidden}"


# --- source-scan discipline over the new modules (the iter-3 pattern) -------------------------------


def test_ledger_writer_composes_from_persisted_reports_only():
    src = (BACKEND_DIR / "app" / "research" / "pnl_ledger.py").read_text()
    # The register string is the ONE existing constant — never a second copy of the literal.
    assert "from .backtests import" in src and "REGISTER" in src
    assert "not indicative of live results" not in src
    # The writer copies persisted row-31 aggregates VERBATIM — it never recomputes trades, R, or $:
    # no runner, no engine, no dataset access, no replay.
    for forbidden in ("BacktestRunner", "TapeEngine", ".replay(", "_aggregate", "DatasetStore",
                      "r_basis", "json.load(", "read_text"):
        assert forbidden not in src, f"pnl_ledger.py must not carry {forbidden}"


def test_seeding_cli_uses_only_the_public_job_and_dataset_apis():
    src = (BACKEND_DIR / "app" / "research" / "pnl_baseline.py").read_text()
    # Backtests run ONLY through BacktestJobManager's public API…
    assert "BacktestJobManager" in src and ".create(" in src and ".run_sync(" in src
    # …and datasets ONLY through the public record/list path (row 30).
    assert "record_from_source" in src
    for forbidden in ("BacktestRunner", "TapeEngine", ".replay(", "_aggregate", "._load",
                      "json.load(", "read_text"):
        assert forbidden not in src, f"pnl_baseline.py must not carry {forbidden}"


# --- config fingerprint discipline (pinned BOTH ways) -----------------------------------------------


def test_labeling_and_path_knobs_are_excluded_from_the_fingerprint():
    base = Config().config_fingerprint()
    # The labeling-only minimum (the documented analytics_min_sample_size EXCLUSION rationale):
    # it changes what a surface CHOOSES to show, never any persisted research value.
    assert Config(pnl_min_sample_size=99).config_fingerprint() == base
    # The operational markdown target path (the journal_db_path / dataset_dir discipline).
    assert Config(pnl_history_md_path="/somewhere/else.md").config_fingerprint() == base


def test_row_shaping_founding_values_still_move_the_fingerprint():
    # The counter-test: values persisted VERBATIM into ledger rows are row-shaping and MUST move
    # the fingerprint (the never-pool honesty mechanism) — the exclusion above is not a blanket.
    base = Config().config_fingerprint()
    assert Config(pnl_founding_enhancement_id="other-id").config_fingerprint() != base


# ==================================================================================================
# The 3-way strategy-comparison append (era-5B J-08) — ``append_strategy_comparison_row``. Every
# test above this marker exercises ``append_validation_row``/the two-way row shape UNMODIFIED —
# proof by construction that writer (and its row shape) is byte-for-byte untouched. This section
# feeds ``append_strategy_comparison_row`` a HAND-BUILT, report-shaped dict (the
# ``test_edge_report.py`` ``_cell()`` / ``test_surviving_train_cells_...`` precedent: what is under
# test here is the COMPOSITION/labeling logic, never PnL math, which is already exhaustively
# proven in ``test_edge_report.py``) — never the committed ``reports/pnl/pnl-history.md`` file,
# which every test below writes to an explicit ``tmp_path`` target instead.
# ==================================================================================================


def _comparison_cell(
    strategy_id: str, band_class: str, band_side: str, reaction: str, feed: str,
    *, n: int, net_r: float, net_usd: float, null_net_r: float = -1.0, null_net_usd: float = -100.0,
) -> dict:
    return {
        "strategy_id": strategy_id,
        "band_class": band_class,
        "band_side": band_side,
        "reaction": reaction,
        "feed": feed,
        "dataset_ids": ["ds-1"],
        "measurement": {
            "n": n, "gross_r": net_r, "net_r": net_r, "gross_usd": net_usd, "net_usd": net_usd,
            "win_rate": 1.0 if n else None, "max_drawdown_r": 0.0 if n else None,
        },
        "null_baseline": {
            "n": 100, "gross_r": null_net_r, "net_r": null_net_r, "gross_usd": null_net_usd,
            "net_usd": null_net_usd, "win_rate": 0.4, "max_drawdown_r": 1.0,
        },
        "insufficient_sample": n < CONFIG.pnl_min_sample_size,
    }


def _comparison_report(train_cells: list[dict], holdout_cells: list[dict]) -> dict:
    """A hand-built ``run_strategy_comparison_report``-SHAPED dict — never a real backtest sweep;
    see this section's own header comment for why this is a legitimate, precedented technique for
    testing composition logic in isolation."""
    return {
        "register": REGISTER,
        "pnl_min_sample_size": CONFIG.pnl_min_sample_size,
        "train": {"cells": train_cells},
        "holdout": {"cells": holdout_cells},
        "surviving_train_cells": [],
    }


def test_append_strategy_comparison_row_composes_cells_verbatim_with_basis_added(fresh_store):
    train_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=3.0, net_usd=300.0)
    holdout_cell = _comparison_cell(
        "structure_tape_map", "B", "support", "rejected", "iex", n=2, net_r=-0.5, net_usd=-50.0
    )
    report = _comparison_report([train_cell], [holdout_cell])

    row = append_strategy_comparison_row(
        fresh_store, CONFIG, enhancement_id="e-3way", title="3-way test", report=report
    )

    assert fresh_store.get_pnl_ledger_row("e-3way").payload == row  # served-verbatim
    assert row["kind"] == "strategy_comparison"
    assert row["register"] == REGISTER
    assert row["pnl_min_sample_size"] == CONFIG.pnl_min_sample_size
    assert row["config_fingerprint"] == CONFIG.config_fingerprint()
    assert row["assumptions"] == {
        "fees": {
            "per_share": CONFIG.strategy_fee_per_share,
            "min_per_trade": CONFIG.strategy_fee_min_per_trade,
        },
        "slippage": {"spread_fraction": CONFIG.strategy_slippage_spread_fraction},
        "dollars_per_r": CONFIG.strategy_dollars_per_r,
    }
    (train_out,) = row["cells"]["train"]
    (holdout_out,) = row["cells"]["holdout"]
    # Every source field survives verbatim, PLUS the added `basis`.
    assert train_out == {**train_cell, "basis": "train"}
    assert holdout_out == {**holdout_cell, "basis": "holdout"}
    # measurement/null_baseline/insufficient_sample are the SOURCE cell's own values, unchanged.
    assert train_out["measurement"]["net_r"] == 3.0
    assert train_out["insufficient_sample"] is False  # n=6 >= 5
    assert holdout_out["insufficient_sample"] is True  # n=2 < 5
    assert holdout_out["null_baseline"]["net_r"] == -1.0


def test_append_never_pools_train_and_holdout(fresh_store):
    train_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=1.0, net_usd=100.0)
    holdout_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=2.0, net_usd=200.0)
    report = _comparison_report([train_cell], [holdout_cell])

    row = append_strategy_comparison_row(
        fresh_store, CONFIG, enhancement_id="e-split", title="split test", report=report
    )

    assert len(row["cells"]["train"]) == 1
    assert len(row["cells"]["holdout"]) == 1
    assert row["cells"]["train"][0]["measurement"]["net_r"] == 1.0
    assert row["cells"]["holdout"][0]["measurement"]["net_r"] == 2.0  # NEVER summed/averaged
    assert "cells" not in row or set(row["cells"].keys()) == {"train", "holdout"}  # no pooled 3rd key


def test_append_never_pools_feeds(fresh_store):
    sim_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=1.0, net_usd=100.0)
    iex_cell = _comparison_cell("v1", "A", "resistance", "broke", "iex", n=6, net_r=9.0, net_usd=900.0)
    report = _comparison_report([sim_cell, iex_cell], [])

    row = append_strategy_comparison_row(
        fresh_store, CONFIG, enhancement_id="e-feeds", title="feed test", report=report
    )

    assert len(row["cells"]["train"]) == 2  # two DISTINCT entries — never merged
    feeds = {c["feed"]: c["measurement"]["net_r"] for c in row["cells"]["train"]}
    assert feeds == {"sim": 1.0, "iex": 9.0}


def test_append_refuses_a_report_missing_a_split_section(fresh_store):
    malformed = {"register": REGISTER, "pnl_min_sample_size": 5, "train": {"cells": []}}  # no "holdout"
    with pytest.raises(LedgerCompositionError, match="holdout"):
        append_strategy_comparison_row(
            fresh_store, CONFIG, enhancement_id="e-bad", title="bad", report=malformed
        )
    assert fresh_store.list_pnl_ledger() == []  # nothing appended on the honest refusal


def test_append_duplicate_enhancement_id_is_refused(fresh_store):
    report = _comparison_report([], [])
    append_strategy_comparison_row(fresh_store, CONFIG, enhancement_id="e-dup3", title="t", report=report)
    with pytest.raises(DuplicateEnhancementError):
        append_strategy_comparison_row(fresh_store, CONFIG, enhancement_id="e-dup3", title="t2", report=report)
    assert len(fresh_store.list_pnl_ledger()) == 1


def test_empty_report_appends_an_honest_all_empty_row(fresh_store):
    """An all-empty (or, equivalently, all-``insufficient_sample``) comparison report is a VALID
    outcome to record, never refused — the identical "empty is honest, not an error" discipline
    ``edge_report.py`` itself already establishes for the source report."""
    report = _comparison_report([], [])
    row = append_strategy_comparison_row(
        fresh_store, CONFIG, enhancement_id="e-empty", title="empty", report=report
    )
    assert row["cells"] == {"train": [], "holdout": []}


# --- projection: the new row shape passes through verbatim, unlabeled --------------------------


def test_projection_serves_the_new_row_shape_verbatim_without_baseline_candidate_labeling(fresh_store):
    """``ledger_projection`` needs NO change for the new row shape (see
    ``append_strategy_comparison_row``'s own docstring): its per-row ``baseline``/``candidate``
    labeling loop finds neither key on a NEW row and silently skips both — the row is served
    exactly as stored, cells' own ``insufficient_sample`` untouched by the projection."""
    train_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=2, net_r=1.0, net_usd=100.0)
    report = _comparison_report([train_cell], [])
    append_strategy_comparison_row(fresh_store, CONFIG, enhancement_id="e-proj", title="t", report=report)

    projection = ledger_projection(fresh_store, CONFIG)

    (row,) = projection["rows"]
    assert row["kind"] == "strategy_comparison"
    assert row["cells"]["train"][0]["insufficient_sample"] is True  # n=2 < 5, from the SOURCE cell
    assert "baseline" not in row and "candidate" not in row


# --- markdown: the new branch, and old rows staying byte-identical alongside it -----------------


def test_regenerating_markdown_from_an_unchanged_comparison_row_is_a_byte_level_no_op(fresh_store):
    train_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=1.0, net_usd=100.0)
    report = _comparison_report([train_cell], [])
    append_strategy_comparison_row(fresh_store, CONFIG, enhancement_id="e-md3", title="md test", report=report)

    first = render_history_markdown(fresh_store, CONFIG)
    second = render_history_markdown(fresh_store, CONFIG)

    assert first == second
    assert "md test" in first
    assert "strategy" in first and "class" in first  # the new per-cell table header


def test_existing_two_way_rows_render_unchanged_alongside_a_new_3way_row(fresh_store, tmp_path):
    """The critical non-regression proof: an OLD (two-way) row and a NEW (3-way) row in the SAME
    ledger each render through their OWN branch. Two independent checks:
      1. the OLD row's rendered SECTION (from its own heading up to the next row's heading) is
         BYTE-IDENTICAL to what a ledger containing ONLY that old row renders (proving the new
         branch's mere presence in the source never perturbs the old branch's own output);
      2. the NEW row's section additionally exists, with its own distinct per-cell table shape.
    """
    old_row = _ledger_row("e-old", train_n=5, holdout_n=3)
    _append(fresh_store, old_row)
    train_cell = _comparison_cell("v1", "A", "resistance", "broke", "sim", n=6, net_r=1.0, net_usd=100.0)
    append_strategy_comparison_row(
        fresh_store, CONFIG, enhancement_id="e-new", title="new 3way", report=_comparison_report([train_cell], [])
    )

    combined_md = render_history_markdown(fresh_store, CONFIG)

    only_old_store = JournalStore(str(tmp_path / "only-old.db"), CONFIG)
    try:
        _append(only_old_store, old_row)
        only_old_md = render_history_markdown(only_old_store, CONFIG)
    finally:
        only_old_store.close()

    # (1) The OLD row's own section renders byte-identically whether or not a NEW row follows it
    # in the SAME ledger: `only_old_md` (one row only) is everything render_history_markdown
    # produces for that row; `combined_md` must carry that EXACT text as its prefix, immediately
    # followed by the new row's own heading (never anything perturbed at the boundary).
    assert combined_md.startswith(only_old_md)
    assert combined_md[len(only_old_md):].startswith("\n## 2. new 3way")
    assert "insufficient sample" in only_old_md  # holdout_n=3 < 5, the OLD label logic unchanged
    # (2) The NEW row's own section follows, with its own distinct per-cell table shape.
    assert "## 2. new 3way" in combined_md
    assert "e-new" in combined_md
    assert "strategy | class | side | reaction | feed" in combined_md


def test_committed_pnl_history_file_is_not_a_default_target_of_these_tests(fresh_store):
    """A guardrail against accidentally writing the REAL committed file: every test in this
    section calls ``render_history_markdown`` (pure, in-memory) or, when writing to disk, passes
    an explicit ``tmp_path`` target — never bare ``write_history_markdown(store, config)``. This
    test only documents/pins that discipline; it does not itself touch the filesystem."""
    src = Path(__file__).read_text()
    # Every call in THIS test module either omits write_history_markdown entirely or passes an
    # explicit path=... — never the bare two-arg form that would target the committed file.
    assert "write_history_markdown(fresh_store, CONFIG)\n" not in src
    assert "write_history_markdown(store, CONFIG)\n" not in src
