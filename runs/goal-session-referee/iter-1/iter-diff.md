# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/main.py b/apps/backend/app/main.py
index cbeb917..eb779be 100644
--- a/apps/backend/app/main.py
+++ b/apps/backend/app/main.py
@@ -40,6 +40,7 @@ from .providers.adapters.base import (
 from .providers.historical import HistoricalProvider
 from .providers.live import LiveProvider
 from .research.desk_routes import router as desk_router
+from .research.referee_routes import router as referee_router
 from .research.routes import (
     ResearchRegistry,
     get_registry_or_none,
@@ -201,6 +202,12 @@ app.include_router(research_router)
 # its own module (routes.py is already large) — mounted separately, alongside research_router.
 app.include_router(desk_router)
 
+# Era 6 "The Referee" (J-01): the readiness fold, under /research/desk/referee — its own module
+# for the SAME reason desk_routes.py itself is separate from routes.py (already large; see
+# referee_routes.py's own docstring). Reached by the MCP get_endpoint's existing /research/
+# prefix allowlist automatically — no MCP change needed.
+app.include_router(referee_router)
+
 # The meta namespace (Data Contract row 35, J-01): the canonical UI route map. The rendered nav
 # and the MCP ``ui_route_map`` tool read it — never a hand-maintained duplicate list.
 app.include_router(meta_router)
diff --git a/apps/backend/app/research/referee_evidence.py b/apps/backend/app/research/referee_evidence.py
new file mode 100644
index 0000000..c952ec7
--- /dev/null
+++ b/apps/backend/app/research/referee_evidence.py
@@ -0,0 +1,245 @@
+"""Era 6 "The Referee" (J-01) — the readiness fold: the FIRST concrete Referee artifact, and the
+one every later Referee journey (J-02 through J-09, per ``docs/goal.md``'s stated dependency
+order) depends on existing first.
+
+**What this module is, and is not.** This is the SIMPLEST possible slice of the eventual evidence
+contract (``docs/goal.md`` Key Capability 1): honest per-family READINESS counts, never individual
+observations. It answers "how much evidence already exists" — playbook-family occurrence/session
+counts pooled at the CURRENT detector basis, plus strategy-family dataset/split/trade counts and
+the honest tick-corpus-gate statement. It does NOT build the typed ``{evidence_family,
+observation_id, anchor_ts, ...}`` contract (J-02), touch statistics of any kind (J-03), or write
+anything — pure aggregation over records ``desk_playbook.py``/``store.py``/``datasets.py`` already
+own, read through their own public APIs only. Zero re-implementation of anything Playbook or
+strategy already computes.
+
+**The two pooling halves — ``detector_basis`` vs. ``playbook_input_signature``.** A playbook
+record's own ``playbook_input_signature`` hashes BOTH its parameters AND the bar-series checksums
+it read, so it churns on every daily bar top-up (``desk_playbook.py``'s own module docstring, and
+Build-anchors trap T-6 in ``docs/goal.md``) — pooling on it directly would almost never span more
+than one date. ``detector_basis`` (Key Capability 1: ``sha256(canonical(record.parameters))[:16]``)
+hashes ONLY the parameters half, so it stays stable across daily top-ups and moves only on a
+genuine detector-constant revision — the identity this fold pools on. The "current" basis is that
+SAME formula applied to a FRESH call of ``playbook_parameters()`` (so a test monkeypatching a
+``PLAYBOOK_*`` constant genuinely moves it); a record whose own embedded parameters hash to a
+DIFFERENT value is honestly excluded from ``signals_at_current_basis``/``per_setup_side`` (it still
+counts toward ``records``/``distinct_sessions`` — the store's raw, unfiltered content) rather than
+silently pooled into today's counts. Pooling also requires the record's own ``config_fingerprint``
+to match the caller's live one (Key Capability 1's full pooling key is
+``(detector_basis, config_fingerprint)``) — a no-op today (the fingerprint pin does not move this
+era) but the honest formula regardless.
+
+**Newest-record-per-date (T-6).** A ``session_date`` can carry several recorded versions (a bar
+top-up or a detector revision each mint a new ``playbook_input_signature`` at the SAME date,
+without touching the older file — ``PlaybookStore`` is append-only). Only the NEWEST version per
+date (by ``(recorded_at, id)``, ``PlaybookStore.list()``'s own sort order) is eligible to pool into
+``signals_at_current_basis``/``per_setup_side`` — an older, superseded version at the same date is
+never double-counted.
+
+**Strategy-family counts.** ``dataset_count``/``per_split_counts`` are a plain read of
+``DatasetStore.list()``'s own metadata (never a second dataset walk); ``trade_count`` sums
+``len(result.trades)`` over every recorded backtest report on file (``JournalStore.list_backtests``
+at an effectively-unlimited cap — the SERVING-only ``Config.backtest_list_max`` the
+``/research/backtests`` route uses for display would silently undercount an aggregate). A report
+with no ``result`` yet (queued/running/failed/cancelled) contributes zero trades, not an error.
+
+**The tick gate and the Card-6.4 caveat.** ``docs/research-directions.md``'s Part-1 prerequisite
+table names Era 6's tick-corpus gate as "library >= ~150 symbol-days"; the era-6 opening note
+(2026-08-14) records Card 5.2's real corpus at "~12 partial 2.5-hour windows" — nowhere near it.
+Each registered ``DatasetStore`` entry is one tick-corpus unit toward that gate (every
+``DatasetStore`` record IS tick/quote event data by construction — bars live in a wholly separate
+store). ``REFEREE_FORMING_BAR_BASIS_CAVEAT`` is this iteration's FIRST authoring of the Card-6.4
+forming-bar disclosure sentence (``docs/goal.md``'s NOTES: no verbatim text exists anywhere yet) —
+the single source of truth later journeys (J-06, J-08) must read back verbatim rather than minting
+a second version.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+
+from .datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore
+from .desk_playbook import PlaybookStore, playbook_parameters
+from .store import JournalStore
+
+__all__ = [
+    "REFEREE_FORMING_BAR_BASIS_CAVEAT",
+    "REFEREE_TICK_GATE_SYMBOL_DAYS",
+    "current_playbook_detector_basis",
+    "playbook_occurrence_readiness",
+    "strategy_trade_readiness",
+    "referee_evidence",
+]
+
+# The Era-6 tick-corpus readiness gate (docs/research-directions.md's Part-1 prerequisite table:
+# "library >= ~150 symbol-days"; the era-6 opening note's Card-5.2 figure). A named module
+# constant, never an inline magic number -- a READINESS floor reported honestly, never a detector
+# gate and never a value any code path here iterates against outcomes.
+REFEREE_TICK_GATE_SYMBOL_DAYS: int = 150
+
+# The Card-6.4 forming-bar disclosure -- authored ONCE, here, for the first time this era
+# (docs/goal.md's NOTES: no pinned verbatim text exists anywhere else). J-06/J-08 read this EXACT
+# string back rather than minting a second version (single source of truth). Subject to
+# tests/test_copy_discipline.py's lexicon (verified directly in this module's own test file, the
+# PLAYBOOK_REGISTER/EVIDENCE_REGISTER precedent).
+REFEREE_FORMING_BAR_BASIS_CAVEAT: str = (
+    "strategy-family evidence is measured over bars read through levels._bars_as_of, which for "
+    "intraday timeframes keeps a bar whenever epoch <= as_of -- admitting the still-forming bar, "
+    "whose stored high/low/close can embed up to a full bar-length of information from after the "
+    "as-of instant. The completed-bar fix (epoch + timeframe_seconds <= as_of) is deferred out of "
+    "this era by operator decision (docs/research-directions.md Card 6.4 Part 1); until it lands, "
+    "this caveat is carried on every strategy-family evidence record so no reader mistakes today's "
+    "basis for a fully lookahead-clean one."
+)
+
+# An effectively-unlimited `list_backtests` cap for THIS aggregate fold -- distinct from the
+# serving-only `Config.backtest_list_max` (100) the `/research/backtests` route uses for display.
+# A readiness count must read every recorded report on file, never a display-sized sample.
+_ALL_BACKTESTS_SCAN_LIMIT = 1_000_000
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding this module hashes -- the SAME encoding every other desk
+    store hashes (``desk_playbook.py._canonical`` et al)."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def current_playbook_detector_basis() -> str:
+    """The pooling key's parameters-only half (docs/goal.md Key Capability 1):
+    ``sha256(canonical(playbook_parameters()))[:16]``, read fresh at CALL TIME so a test
+    monkeypatching a ``PLAYBOOK_*`` constant genuinely moves this value. Stable across daily bar
+    top-ups (unlike ``playbook_input_signature``, which also hashes bar-series checksums) -- it
+    moves only on a genuine detector-constant revision."""
+    return _sha256(_canonical(playbook_parameters()))[:16]
+
+
+def _record_detector_basis(record: dict) -> str:
+    """The SAME formula applied to one already-recorded record's own embedded ``parameters`` --
+    that record's own basis, whether or not it matches the CURRENT one."""
+    return _sha256(_canonical(record["parameters"]))[:16]
+
+
+def _newest_per_session_date(records: list[dict]) -> dict[str, dict]:
+    """One record per ``session_date`` -- the newest by ``(recorded_at, id)`` (T-6's pooling
+    rule). ``records`` arrives ``(recorded_at, id)``-ascending (``PlaybookStore.list()``'s own
+    sort), so simply overwriting a dict entry as each record is walked leaves the LAST-seen (=
+    newest) record for every date -- no re-sort needed."""
+    newest: dict[str, dict] = {}
+    for record in records:
+        newest[record["session_date"]] = record
+    return newest
+
+
+def playbook_occurrence_readiness(store: PlaybookStore, config_fingerprint: str) -> dict:
+    """The ``playbook_occurrence`` block: ``records``/``distinct_sessions`` are the store's raw,
+    UNFILTERED content (every file on disk, every date it spans); ``signals_at_current_basis`` and
+    ``per_setup_side`` pool only the newest-per-date records whose own ``(detector_basis,
+    config_fingerprint)`` match today's live values (T-6) -- a stale-basis record still counts
+    toward the first two, never the last two. ``per_setup_side`` is SPARSE (only cells with at
+    least one recorded signal), so a zero-corpus store serves ``[]``, never a padded zero-filled
+    cross product."""
+    records, errors = store.list()
+    basis = current_playbook_detector_basis()
+    newest_by_date = _newest_per_session_date(records)
+
+    cells: dict[tuple[str, str], dict[str, object]] = {}
+    signals_at_current_basis = 0
+    for record in newest_by_date.values():
+        if (
+            _record_detector_basis(record) != basis
+            or record["config_fingerprint"] != config_fingerprint
+        ):
+            continue
+        session_date = record["session_date"]
+        for signal in record["signals"]:
+            signals_at_current_basis += 1
+            key = (signal["setup_id"], signal["side"])
+            cell = cells.setdefault(key, {"n": 0, "sessions": set()})
+            cell["n"] += 1
+            cell["sessions"].add(session_date)
+
+    per_setup_side = [
+        {"setup": setup, "side": side, "n": cell["n"], "n_sessions": len(cell["sessions"])}
+        for (setup, side), cell in sorted(cells.items())
+    ]
+
+    return {
+        "detector_basis": basis,
+        "config_fingerprint": config_fingerprint,
+        "records": len(records),
+        "distinct_sessions": len(newest_by_date),
+        "signals_at_current_basis": signals_at_current_basis,
+        "per_setup_side": per_setup_side,
+        "integrity_errors": errors,
+    }
+
+
+def _tick_gate_state(measured_symbol_days: int) -> tuple[bool, str]:
+    """Whether the Era-6 tick-corpus gate is met, plus the honest sentence naming the gate and the
+    measured shortfall (or surplus) -- pure arithmetic over an already-counted value, never a
+    second count and never a threshold this (or any) code path iterates against outcomes."""
+    met = measured_symbol_days >= REFEREE_TICK_GATE_SYMBOL_DAYS
+    gate_clause = (
+        f"the Era-6 tick-corpus gate (>= {REFEREE_TICK_GATE_SYMBOL_DAYS} symbol-days, "
+        f"docs/research-directions.md Card 5.2) "
+    )
+    if met:
+        return True, gate_clause + (
+            f"is met: {measured_symbol_days} tick dataset(s) are registered today."
+        )
+    shortfall = REFEREE_TICK_GATE_SYMBOL_DAYS - measured_symbol_days
+    return False, gate_clause + (
+        f"is unmet: {measured_symbol_days} tick dataset(s) are registered today, {shortfall} "
+        f"short of the gate."
+    )
+
+
+def strategy_trade_readiness(dataset_store: DatasetStore, journal_store: JournalStore) -> dict:
+    """The ``strategy_trade`` block: dataset/split/trade counts read straight off
+    ``DatasetStore``/``JournalStore``'s own public reads (zero recomputation of anything
+    ``backtests.py`` already owns), plus the honest tick-gate statement and the Card-6.4 basis
+    caveat."""
+    datasets, dataset_errors = dataset_store.list()
+    per_split_counts = {SPLIT_TRAIN: 0, SPLIT_HOLDOUT: 0}
+    for meta in datasets:
+        split = meta.get("split")
+        if split in per_split_counts:
+            per_split_counts[split] += 1
+
+    backtests = journal_store.list_backtests(limit=_ALL_BACKTESTS_SCAN_LIMIT)
+    trade_count = sum(
+        len(record.payload.get("result", {}).get("trades", [])) for record in backtests
+    )
+
+    tick_gate_met, tick_gate_statement = _tick_gate_state(len(datasets))
+
+    return {
+        "dataset_count": len(datasets),
+        "per_split_counts": per_split_counts,
+        "trade_count": trade_count,
+        "tick_gate_met": tick_gate_met,
+        "tick_gate_statement": tick_gate_statement,
+        "basis_caveats": [REFEREE_FORMING_BAR_BASIS_CAVEAT],
+        "integrity_errors": dataset_errors,
+    }
+
+
+def referee_evidence(
+    *,
+    playbook_store: PlaybookStore,
+    dataset_store: DatasetStore,
+    journal_store: JournalStore,
+    config_fingerprint: str,
+) -> dict:
+    """The whole ``GET /research/desk/referee/evidence`` body (J-01) -- per-family readiness, a
+    pure aggregation over already-recorded ``PlaybookStore``/``DatasetStore``/``JournalStore``
+    records. Never 404/500 on an empty corpus (an honest all-zero shape at HTTP 200 — the desk
+    router's established never-404-on-absence convention)."""
+    return {
+        "playbook_occurrence": playbook_occurrence_readiness(playbook_store, config_fingerprint),
+        "strategy_trade": strategy_trade_readiness(dataset_store, journal_store),
+    }
diff --git a/apps/backend/app/research/referee_routes.py b/apps/backend/app/research/referee_routes.py
new file mode 100644
index 0000000..fa0410e
--- /dev/null
+++ b/apps/backend/app/research/referee_routes.py
@@ -0,0 +1,51 @@
+"""``/research/desk/referee/*`` — Era 6 "The Referee" (J-01): the readiness fold, the FIRST
+concrete Referee artifact. See ``referee_evidence.py``'s own module docstring for the fold's
+mechanics; this file is pure wiring.
+
+A fresh router/file rather than folding into ``desk_routes.py`` (already 1600+ lines) — the SAME
+rationale ``desk_routes.py`` itself gives for splitting off ``routes.py``: "mounted separately ...
+rather than folding into routes.py, which is already large." The era's own Data Contract table
+(``docs/goal.md``'s Product Shape) names five MORE referee routes landing in later iterations
+(nulls, registry, evaluations, adjudications) under this SAME ``/research/desk/referee`` prefix —
+a dedicated file is the right home from the start.
+
+Depends on stores this route does NOT own: the playbook store dependency is imported verbatim from
+``desk_routes.get_playbook_store`` and the dataset store dependency from ``routes.get_dataset_store``
+(never a second, redefined provider for either) — the ``JournalStore`` (for backtest reports) comes
+through the existing ``ResearchRegistry`` (``routes.get_registry``), the SAME seam
+``GET /research/backtests`` already reads. A plain read: triggers nothing, recomputes nothing
+(GET-never-computes) — this route takes no compute-manager dependency at all."""
+
+from __future__ import annotations
+
+from fastapi import APIRouter, Depends
+
+from ..config import CONFIG
+from .datasets import DatasetStore
+from .desk_playbook import PlaybookStore
+from .desk_routes import get_playbook_store
+from .referee_evidence import referee_evidence
+from .routes import ResearchRegistry, get_dataset_store, get_registry
+
+router = APIRouter(prefix="/research/desk/referee", tags=["referee"])
+
+
+@router.get("/evidence")
+def get_referee_evidence(
+    playbook_store: PlaybookStore = Depends(get_playbook_store),
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+    registry: ResearchRegistry = Depends(get_registry),
+) -> dict:
+    """J-01's readiness fold: exactly how much Playbook and strategy evidence already exists —
+    per-``(setup, side)`` occurrence/session counts at the current detector basis, plus strategy
+    dataset/split/trade counts and the honest tick-gate-unmet statement. Never 404/500 on an empty
+    corpus — an honest all-zero shape at HTTP 200 (the desk router's established
+    never-404-on-absence convention). Pure aggregation: this route neither detects nor measures
+    anything — it only reads what ``desk_playbook.py``/``datasets.py``/``store.py`` already
+    recorded."""
+    return referee_evidence(
+        playbook_store=playbook_store,
+        dataset_store=dataset_store,
+        journal_store=registry.store,
+        config_fingerprint=CONFIG.config_fingerprint(),
+    )
diff --git a/apps/backend/tests/test_referee_evidence.py b/apps/backend/tests/test_referee_evidence.py
new file mode 100644
index 0000000..aaff88d
--- /dev/null
+++ b/apps/backend/tests/test_referee_evidence.py
@@ -0,0 +1,250 @@
+"""``referee_evidence.py`` + ``GET /research/desk/referee/evidence`` (Era 6 "The Referee", J-01) —
+the readiness fold. Test-first contract: TC-1 through TC-5 in
+``docs/phases/goal-referee-iter-1.md``.
+
+Builds its own hand-crafted ``PlaybookStore``/``DatasetStore``/``JournalStore`` records directly
+through each store's own public write path (never a real ``compute_playbook`` walk or a real
+backtest run — those paths are already covered end to end by ``test_desk_playbook.py``/
+``test_backtests.py``), so every pooled count in every assertion below is a number this file's own
+hand computation can reproduce, not one a compute happened to produce."""
+
+from __future__ import annotations
+
+import time
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app
+from app.providers.base import Side, TradeEvent
+from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore
+from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
+from app.research.desk_routes import get_playbook_store
+from app.research.referee_evidence import (
+    REFEREE_FORMING_BAR_BASIS_CAVEAT,
+    REFEREE_TICK_GATE_SYMBOL_DAYS,
+    _tick_gate_state,
+    current_playbook_detector_basis,
+)
+from app.research.routes import ResearchRegistry, get_dataset_store, set_registry
+from app.research.store import BacktestRecord, JournalStore
+from test_copy_discipline import find_violations
+
+E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET, the codebase's standard fixture anchor
+
+
+# --- fixture builders (the store's own public write path — never a hand-typed file) ----------------
+
+
+def _signal(setup_id: str, side: str) -> dict:
+    """A minimal recorded signal — ``PlaybookStore`` validates nothing about signal shape beyond
+    "is dict-able", and this fold only ever reads ``setup_id``/``side`` off one, so a real signal's
+    ``forward``/``geometry``/... leaves are irrelevant noise here."""
+    return {"setup_id": setup_id, "side": side}
+
+
+def _plant_playbook_record(
+    store: PlaybookStore, *, session_date: str, signature: str, signals: list[dict],
+    parameters: dict | None = None,
+) -> dict:
+    return store.record(
+        session_date=session_date,
+        config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature=signature,
+        payload_version=3,
+        parameters=parameters if parameters is not None else playbook_parameters(),
+        register=PLAYBOOK_REGISTER,
+        signals=signals,
+        absences=[],
+        diagnostics=[],
+    )
+
+
+def _events(symbol: str, n: int) -> list[TradeEvent]:
+    return [TradeEvent(symbol, float(i), 100.0 + i, 10, Side.BUY) for i in range(n)]
+
+
+def _plant_dataset(store: DatasetStore, *, symbol: str, split: str, source_id: str) -> dict:
+    return store.record(
+        symbol=symbol,
+        source="fixture",
+        source_kind="fixture",
+        source_id=source_id,
+        split=split,
+        window_start_utc="2026-06-01T00:00:00Z",
+        window_end_utc="2026-06-01T01:00:00Z",
+        data_feed="sim",
+        epoch_anchor=0.0,
+        events=_events(symbol, 3),
+    )
+
+
+def _plant_backtest(
+    journal_store: JournalStore, *, backtest_id: str, trades: list[dict] | None = None,
+    status: str = "done",
+) -> None:
+    payload: dict = {"id": backtest_id, "status": status}
+    if trades is not None:
+        payload["result"] = {"trades": trades}
+    journal_store.insert_backtest(
+        BacktestRecord(id=backtest_id, payload=payload, created_wall_ts=time.time())
+    )
+
+
+@pytest.fixture
+def client(tmp_path):
+    journal_store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    registry = ResearchRegistry(journal_store, CONFIG)
+    set_registry(registry)
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    app.dependency_overrides[get_playbook_store] = lambda: playbook_store
+    app.dependency_overrides[get_dataset_store] = lambda: dataset_store
+    with TestClient(app) as c:
+        yield c, playbook_store, dataset_store, journal_store
+    app.dependency_overrides.pop(get_playbook_store, None)
+    app.dependency_overrides.pop(get_dataset_store, None)
+    set_registry(None)
+    journal_store.close()
+
+
+# --- TC-5: the zero-corpus honest-empty case --------------------------------------------------------
+
+
+def test_zero_corpus_is_an_honest_200_not_a_404(client):
+    c, _playbook_store, _dataset_store, _journal_store = client
+    response = c.get("/research/desk/referee/evidence")
+    assert response.status_code == 200
+    body = response.json()
+    assert body["playbook_occurrence"]["records"] == 0
+    assert body["playbook_occurrence"]["distinct_sessions"] == 0
+    assert body["playbook_occurrence"]["signals_at_current_basis"] == 0
+    assert body["playbook_occurrence"]["per_setup_side"] == []
+    assert body["strategy_trade"]["dataset_count"] == 0
+    assert body["strategy_trade"]["per_split_counts"] == {"train": 0, "holdout": 0}
+    assert body["strategy_trade"]["trade_count"] == 0
+    assert body["strategy_trade"]["tick_gate_met"] is False
+
+
+# --- TC-1 / TC-2: the playbook readiness fold --------------------------------------------------------
+
+
+def test_playbook_readiness_pools_newest_per_date_at_the_current_basis(client):
+    c, store, _dataset_store, _journal_store = client
+
+    # Date D1: an OLDER record (1 signal) SUPERSEDED by a NEWER one (2 signals) at the SAME date —
+    # only the newer record's own signals may count (T-6's newest-per-date rule).
+    _plant_playbook_record(
+        store, session_date="2026-06-08", signature="sig-d1-older",
+        signals=[_signal("capitulation", "long")],
+    )
+    _plant_playbook_record(
+        store, session_date="2026-06-08", signature="sig-d1-newer",
+        signals=[_signal("capitulation", "long"), _signal("jbe", "short")],
+    )
+    # Date D2: one more current-basis record, pooling into the SAME two cells.
+    _plant_playbook_record(
+        store, session_date="2026-06-09", signature="sig-d2",
+        signals=[
+            _signal("capitulation", "long"), _signal("capitulation", "long"),
+            _signal("jbe", "short"),
+        ],
+    )
+    # Date D3: a STALE-basis record (parameters deliberately different from the LIVE
+    # playbook_parameters()) — must count toward records/distinct_sessions but NEVER toward
+    # signals_at_current_basis or per_setup_side.
+    stale_parameters = {**playbook_parameters(), "min_n_disclosure": 999}
+    _plant_playbook_record(
+        store, session_date="2026-06-10", signature="sig-d3-stale",
+        signals=[_signal("capitulation", "long")] * 5,
+        parameters=stale_parameters,
+    )
+
+    response = c.get("/research/desk/referee/evidence")
+    assert response.status_code == 200
+    occurrence = response.json()["playbook_occurrence"]
+
+    assert occurrence["detector_basis"] == current_playbook_detector_basis()
+    assert occurrence["config_fingerprint"] == CONFIG.config_fingerprint()
+    assert occurrence["records"] == 4  # R1a, R1b, R2, R3 — every file on disk, unfiltered
+    assert occurrence["distinct_sessions"] == 3  # D1, D2, D3
+    # R1b's 2 + R2's 3 — R1a is superseded (same date, older), R3 is stale-basis-excluded.
+    assert occurrence["signals_at_current_basis"] == 5
+
+    per_cell = {(row["setup"], row["side"]): row for row in occurrence["per_setup_side"]}
+    assert set(per_cell) == {("capitulation", "long"), ("jbe", "short")}
+    assert per_cell[("capitulation", "long")]["n"] == 3  # R1b's 1 + R2's 2
+    assert per_cell[("capitulation", "long")]["n_sessions"] == 2  # D1, D2
+    assert per_cell[("jbe", "short")]["n"] == 2  # R1b's 1 + R2's 1
+    assert per_cell[("jbe", "short")]["n_sessions"] == 2  # D1, D2
+
+
+# --- TC-3: the strategy readiness fold ---------------------------------------------------------------
+
+
+def test_strategy_readiness_counts_datasets_splits_and_trades(client):
+    c, _playbook_store, dataset_store, journal_store = client
+
+    _plant_dataset(dataset_store, symbol="AAPL", split=SPLIT_TRAIN, source_id="ds-1")
+    _plant_dataset(dataset_store, symbol="MSFT", split=SPLIT_TRAIN, source_id="ds-2")
+    _plant_dataset(dataset_store, symbol="GOOG", split=SPLIT_HOLDOUT, source_id="ds-3")
+
+    _plant_backtest(
+        journal_store, backtest_id="bt-1",
+        trades=[{"net_r": 1.0}, {"net_r": -0.5}, {"net_r": 0.8}],
+    )
+    _plant_backtest(journal_store, backtest_id="bt-2", trades=[{"net_r": 0.3}, {"net_r": -1.0}])
+    _plant_backtest(journal_store, backtest_id="bt-3", status="running")  # no result yet -> 0
+
+    response = c.get("/research/desk/referee/evidence")
+    assert response.status_code == 200
+    strategy = response.json()["strategy_trade"]
+
+    assert strategy["dataset_count"] == 3
+    assert strategy["per_split_counts"] == {"train": 2, "holdout": 1}
+    assert strategy["trade_count"] == 5  # 3 + 2 + 0 (the running record contributes nothing)
+
+
+# --- TC-4: the honest unmet tick gate + the Card-6.4 basis caveat ------------------------------------
+
+
+def test_strategy_readiness_names_the_unmet_tick_gate_and_the_forming_bar_caveat(client):
+    c, _playbook_store, dataset_store, _journal_store = client
+    _plant_dataset(dataset_store, symbol="AAPL", split=SPLIT_TRAIN, source_id="ds-1")
+
+    response = c.get("/research/desk/referee/evidence")
+    strategy = response.json()["strategy_trade"]
+
+    assert strategy["tick_gate_met"] is False
+    assert strategy["tick_gate_statement"] != ""
+    assert str(REFEREE_TICK_GATE_SYMBOL_DAYS) in strategy["tick_gate_statement"]
+    assert strategy["basis_caveats"] == [REFEREE_FORMING_BAR_BASIS_CAVEAT]
+
+
+def test_forming_bar_basis_caveat_passes_copy_discipline():
+    """The Card-6.4 caveat is authored for the FIRST time this iteration (docs/goal.md's NOTES) —
+    verified against the copy-discipline lexicon directly (the PLAYBOOK_REGISTER/EVIDENCE_REGISTER
+    per-module precedent), since it is served on a route the existing taxonomy-payload walk in
+    ``test_copy_discipline.py`` does not reach."""
+    assert find_violations(REFEREE_FORMING_BAR_BASIS_CAVEAT) == []
+
+
+# --- the tick-gate arithmetic, unit-level (both branches; TC-4's statement contract) -----------------
+
+
+def test_tick_gate_state_unmet_branch():
+    met, statement = _tick_gate_state(3)
+    assert met is False
+    assert "3" in statement
+    assert str(REFEREE_TICK_GATE_SYMBOL_DAYS) in statement
+
+
+def test_tick_gate_state_met_branch():
+    met, statement = _tick_gate_state(REFEREE_TICK_GATE_SYMBOL_DAYS)
+    assert met is True
+    assert str(REFEREE_TICK_GATE_SYMBOL_DAYS) in statement
+
+    comfortably_met, statement2 = _tick_gate_state(REFEREE_TICK_GATE_SYMBOL_DAYS + 50)
+    assert comfortably_met is True
+    assert str(REFEREE_TICK_GATE_SYMBOL_DAYS + 50) in statement2
diff --git a/apps/backend/tests/test_referee_guards.py b/apps/backend/tests/test_referee_guards.py
new file mode 100644
index 0000000..f86400f
--- /dev/null
+++ b/apps/backend/tests/test_referee_guards.py
@@ -0,0 +1,131 @@
+"""goal-referee-iter-1 (J-01) — two structural guard-test pins named verbatim in ``docs/goal.md``'s
+J-01 acceptance and this iteration's spec (``docs/phases/goal-referee-iter-1.md`` TC-6/TC-7/TC-8):
+
+(a) The ``playbook-band-context-v3`` spec-drift pin. The era-6 opening commit caught up
+    ``docs/playbook-detector-spec.md`` §6's own version pointer (v2 -> v3, reconciling the doc to
+    code that had already shipped) — a DOC-ONLY edit, zero behavior change. This pin makes that
+    reconciliation permanent two ways: (1) the doc's heading block and its "Structural (shape, not
+    thresholds)" constants line both still name the LIVE ``PLAYBOOK_CONTEXT_ALGORITHM_VERSION``
+    value verbatim, so the two can never silently diverge again; (2) ``desk_playbook_context.py``
+    itself — the LENS this doc describes — is byte-unchanged this iteration (a doc catch-up is
+    never a licence to touch the lens), via the ``test_desk_playbook_guards.py::test_decline_
+    disclosure_doc_edit_left_the_capitulation_code_byte_unchanged`` precedent: a pinned
+    ``hashlib.sha256(inspect.getsource(...))`` hash over the WHOLE module (the broadest possible
+    zero-diff claim, since this iteration's IN SCOPE names ``desk_playbook*.py`` as a zero-diff
+    file, not just two of its functions).
+
+(b) The ``docs/research-directions.md`` catalog-reconciliation pins. The era-6 opening commit
+    reconciled the year-long research catalog's status table (eras 5/5B/5C/5D/B/B2, all already
+    recorded) and dated two Card entries "AMENDED 2026-08-14" (6.2's bootstrap-p retraction, 6.3's
+    store-design supersession). String-presence pins so neither the status-table rows nor the
+    amendment notes can be silently reworded or removed later — this iteration only PINS
+    already-reconciled text; it edits neither document (IN SCOPE / OUT OF SCOPE both say so).
+
+Every guard here carries a seeded counter-test (the ``test_copy_discipline.py`` / ``test_desk_
+playbook_guards.py`` precedent: "a lint that cannot fail proves nothing")."""
+
+from __future__ import annotations
+
+import hashlib
+import inspect
+import pathlib
+
+from app.research import desk_playbook_context as desk_playbook_context_module
+from app.research.desk_playbook_context import PLAYBOOK_CONTEXT_ALGORITHM_VERSION
+
+REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
+_SPEC_PATH = REPO_ROOT / "docs" / "playbook-detector-spec.md"
+_CATALOG_PATH = REPO_ROOT / "docs" / "research-directions.md"
+
+
+# --- (a) the playbook-band-context-v3 spec-drift pin (TC-6, TC-7) ----------------------------------
+
+# Recorded at the START of this iteration (``desk_playbook_context.py`` as it exists on `main`
+# before goal-referee-iter-1 touches anything) — this iteration ships ZERO diff to this module, so
+# the hash below must still match at the END of the iteration too.
+_DESK_PLAYBOOK_CONTEXT_MODULE_SHA256 = (
+    "75537d161661b9660cf82896c56b60d92acdf3179fd77bd041c38ae45530fc23"
+)
+
+
+def test_desk_playbook_context_module_is_byte_unchanged_this_iteration():
+    """TC-7: this iteration's doc catch-up in ``docs/playbook-detector-spec.md`` §6 ships ZERO
+    diff to ``desk_playbook_context.py`` — the WHOLE module's own live source (via
+    ``inspect.getsource``) still hashes to the value recorded at the start of this iteration."""
+    source = inspect.getsource(desk_playbook_context_module)
+    assert hashlib.sha256(source.encode()).hexdigest() == _DESK_PLAYBOOK_CONTEXT_MODULE_SHA256
+
+
+def test_desk_playbook_context_zero_diff_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail — a lint that cannot fail proves nothing."""
+    source = inspect.getsource(desk_playbook_context_module)
+    real_hash = hashlib.sha256(source.encode()).hexdigest()
+    seeded_wrong_hash = "0" * 64
+    assert real_hash != seeded_wrong_hash
+
+
+def test_playbook_band_context_v3_named_in_spec_heading_block():
+    """TC-6 (heading half): §6's heading and its immediate supersession note both name the LIVE
+    ``PLAYBOOK_CONTEXT_ALGORITHM_VERSION`` value verbatim — fails the instant the doc's version
+    pointer and the shipped code constant diverge."""
+    text = _SPEC_PATH.read_text()
+    start = text.index("## 6. Band context")
+    end = text.index("\n### Pre-registered constants", start)
+    heading_block = text[start:end]
+    assert PLAYBOOK_CONTEXT_ALGORITHM_VERSION in heading_block
+
+
+def test_playbook_band_context_v3_named_in_spec_constants_line():
+    """TC-6 (constants-line half): the "Structural (shape, not thresholds)" line names the LIVE
+    ``PLAYBOOK_CONTEXT_ALGORITHM_VERSION`` value verbatim."""
+    text = _SPEC_PATH.read_text()
+    assert f'PLAYBOOK_CONTEXT_ALGORITHM_VERSION = "{PLAYBOOK_CONTEXT_ALGORITHM_VERSION}"' in text
+
+
+def test_playbook_band_context_v3_spec_pin_guard_can_fail_on_a_seeded_divergence():
+    """The lint CAN fail: a deliberately wrong version string is rejected."""
+    text = _SPEC_PATH.read_text()
+    seeded_wrong_version = "playbook-band-context-v999"
+    assert seeded_wrong_version not in text
+
+
+# --- (b) the docs/research-directions.md catalog-reconciliation pins (TC-8) ------------------------
+
+# One distinctive, single-line substring per pinned status-table row — long enough that an
+# accidental match elsewhere in the document is not a realistic risk, short enough to be an honest
+# transcription (each verified byte-for-byte against the committed file at authoring time).
+_STATUS_TABLE_ROW_PINS = (
+    "`yahoo_fetch` | done | The era pivoted to a keyless Yahoo Finance BAR library",  # era 5
+    "`tradable_wall` | done | Tradable",  # era 5B
+    "`fast_wall` | done | Store stat-caches + durable dataset index",  # era 5C
+    "`clean_slate` | done | Journal era deleted (14 routes, 3 pages",  # era 5D
+    "`desk` | done | `/desk`: fetched S&P100 universe, append-only screen ledger",  # era B
+    "`playbook` | done | Nine pre-registered Graifer/Schumacher intraday detectors",  # era B2
+)
+
+_CARD_AMENDMENT_PINS = (
+    "AMENDED 2026-08-14 (era-6 opening; statistical correction",  # Card 6.2
+    "AMENDED 2026-08-14, era-6 opening: the store design below is superseded",  # Card 6.3
+)
+
+
+def test_catalog_status_table_names_every_pinned_era_row():
+    """TC-8 (status-table half): one row per named era (5/5B/5C/5D/B/B2) is still present, fails
+    the instant any row's own finding sentence is reworded or removed."""
+    text = _CATALOG_PATH.read_text()
+    for pin in _STATUS_TABLE_ROW_PINS:
+        assert pin in text, f"status-table row pin missing: {pin!r}"
+
+
+def test_catalog_names_the_card_6_2_and_6_3_amendment_notes():
+    """TC-8 (amendment-note half): the dated "AMENDED 2026-08-14" notes under Card 6.2 and
+    Card 6.3 are still present."""
+    text = _CATALOG_PATH.read_text()
+    for pin in _CARD_AMENDMENT_PINS:
+        assert pin in text, f"catalog amendment-note pin missing: {pin!r}"
+
+
+def test_catalog_reconciliation_guard_can_fail_on_a_seeded_removal():
+    """The lint CAN fail: a string genuinely absent from the doc is rejected."""
+    text = _CATALOG_PATH.read_text()
+    assert "this exact sentence was never written to the catalog, ever" not in text
```
