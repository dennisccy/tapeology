# Iteration diff (bounded)

Files changed: 12. Shown in full: 12.

```diff
diff --git a/README.md b/README.md
index 0eb756b..4238547 100644
--- a/README.md
+++ b/README.md
@@ -79,8 +79,9 @@ Current capabilities:
 - **Strategy registry and champion panel on the Structure page** — beneath the confluence-zones table, a Registry section shows the two trading strategies the system knows about, `v1` and `structure_tape`, each as a card listing its entry rule and its exit rules — stop distance, a reward target where the strategy defines one (only `structure_tape` does), the tape-state-flip exit, the time horizon, and the dataset-end exit. The `structure_tape` card additionally shows three small tables — stop distance, reward target, and simulated position size — each broken out by A/B/C confluence class. A Champion panel above the two cards names the strategy/profile pair currently favored (today `v1` on the `default` profile) and a caption confirms this agrees with the same champion shown on the Performance page. The section loads automatically as soon as the Structure page opens — no symbol or as-of time is required — every value is read verbatim from the backend with nothing calculated in the browser, and an explicit "registry unavailable" message replaces the whole section, with no guessed fallback, if the backend can't be reached.
 - **structure_tape-vs-v1 comparison on the Structure page** — beneath the Registry section, a Comparison section lets you choose a registered dataset and run both `structure_tape` and the champion strategy `v1` over it as an offline research job (it places nothing and never touches an order path); each side's progress is shown independently as it moves from Queued to Running (with a live count of events processed) to Done, and the two result cards populate automatically once both finish, with no manual refresh. It then shows both strategies' results side by side: trade count, net return in R and dollars, win rate, and maximum drawdown — a strategy that took zero trades shows an honest "no trades (n=0)" instead of a misleading zero — plus a per-class A/B/C breakdown of the same figures with an explicit "insufficient sample" label wherever a class has too few trades to trust. The always-visible "simulated — assumed fees/slippage — not indicative of live results" register is shown exactly as the backend serves it, never a rephrased copy. A read-only Champion panel beside the results confirms the champion is unaffected — this comparison never promotes a strategy or writes to the PnL ledger, no matter what it finds — and a Founding baseline panel shows the ledger's first recorded row for reference. Every number is read verbatim from the same backtest report the research API and command-line tool already serve. On the committed keyless sample data this honestly shows `structure_tape` arming too few (or zero) trades to trust a result, exactly the "not enough evidence yet" finding the underlying research tool already reports — the champion stays `v1` on `default`. No datasets registered, a comparison still running, a failed or cancelled run, and the backend being unreachable each show their own distinct, explicit message rather than a blank or guessed result.
 - **Tradable level map (research API)** — distills a symbol's raw support/resistance levels (which can number in the thousands for a heavily traded stock) down to at most 10 price "bands" total — the handful of price zones actually worth marking on a chart. Each band carries its price range, whether it is support or resistance, a quality score, how many underlying levels back it up, whether it sits on a psychologically "round" price, and an inherited A/B/C conviction class where one applies. The map for any given day is built using only data fully available before that trading day started — mirroring how a trader marks up charts before the open — with weekends and market holidays handled automatically by falling back to whichever trading day actually closed last. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
-- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /research/tradability`, `GET /meta/ui-routes`.
-- **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
+- **Touch-event scanner and case-study registry (research API)** — walks every stored trading session in a 12-symbol panel's recorded price history and checks each session's actual price action against that session's own tradable level map, built strictly from data available before the session opened, so a later session's data can never change an earlier one's already-recorded result. Every genuine touch of a band is logged with its outcome — rejected and turned away, broken straight through, or chopped near the wall with no clear outcome — together with how far price moved by two later checkpoints. Run against real, freshly fetched price history for the full panel, the registry already holds several hundred touch events across all 12 symbols, a healthy mix of breakouts, rejections, and chops, with identical requests always returning byte-identical results. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
+- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /meta/ui-routes`.
+- **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
 
 This project embeds the [`incredible_auto_dev`](https://github.com/dennisccy/incredible_auto_dev)
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 1c1fffd..b10d90d 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1274,6 +1274,46 @@ class Config:
     # magic number either.
     setups_5m_fetch_retention_days: int = 60
 
+    # --- Era 5B: event-window tape recording (capability 3, J-03) -- RESEARCH DEFAULTS, the SAME
+    # sr_pivot_lookback discipline: every research value lives in config with its rationale
+    # documented HERE, no literal in scripts/record_event_windows.py or research/setups.py.
+    # Namespaced recording_* so it never collides with the tradability_*/setups_* families above
+    # (read-only inputs the recording driver consumes VERBATIM -- it selects from compute_setups'
+    # own events, never a second scan) nor the datasets.py SPLIT_TRAIN/SPLIT_HOLDOUT vocabulary it
+    # reuses unmodified.
+    #
+    # RECORDING WINDOW PADDING: goal.md's own pinned "touch -60 min ... +90 min" spec -- wide
+    # enough before the touch to capture the tape's approach to the wall, wider after (90 vs 60)
+    # because the REACTION (what the tape says AFTER a rejection/break) is the entire point of
+    # J-03's "tape-at-the-wall" join. A single config-owned pair, never a per-event literal.
+    recording_pre_touch_minutes: float = 60.0
+    recording_post_touch_minutes: float = 90.0
+    # TOP-RANKED EVENT-SELECTION CAP: the recording driver's own operational ceiling on how many
+    # events it POSTs /research/datasets for in one run (goal.md: "top-ranked scan events"). 15
+    # mirrors the SAME scale as the J-02 scan's own ">= 15 events" registry-size floor
+    # (setups_panel_symbols has 12 members) -- comfortably above the J-03 ">= 10 windows across
+    # >= 5 symbols" credentialed headline even after the pinned AAPL event and the driver's own
+    # one-best-per-symbol-first selection spread consume part of the budget. Governs ONLY the
+    # operational driver script's own POST count -- it never shapes any persisted tape/backtest/
+    # PnL value, so it is EXCLUDED from config_fingerprint below (the bar_timeframes /
+    # setups_panel_symbols rationale).
+    recording_event_selection_cap: int = 15
+    # SPLIT-ASSIGNMENT RATIO: the NEW config-owned deterministic seeded rule this iteration adds
+    # (no pre-existing "seeded split rule" exists in the codebase to reuse verbatim -- confirmed by
+    # a direct grep across app/ and tests/; see the plan's own architecture notes). A pure sha256
+    # digest of each recorded event's OWN stable id (the setups.py _event_id idiom, reused as a
+    # technique) is mapped into [0, 1) and compared against this ratio -- deterministic and
+    # reproducible (the identical event id always resolves to the identical split, every run), no
+    # wall-clock, no unseeded randomness (the deterministic-and-seeded anti-goal). 0.2 is the
+    # conventional 80/20 train/holdout research proportion, sized so a recording run of >= 10
+    # events still plausibly populates BOTH splits (an all-one-split run would starve J-04's
+    # hold-out cells before they even exist). Governs ONLY which frozen split TAG a NEWLY recorded
+    # dataset gets -- it never re-derives or alters any EXISTING dataset's frozen tag (structural
+    # immutability; datasets.py has no update path at all), so it is EXCLUDED from
+    # config_fingerprint below (the tradability_*/setups_* "separate additive computation"
+    # rationale).
+    recording_holdout_fraction: float = 0.2
+
     # --- Structure-and-tape era: the `structure_tape` STRATEGY (era-4 capability 4, J-04; Data
     # Contract row 41) -- RESEARCH DEFAULTS, the SAME ``sr_pivot_lookback`` discipline: every
     # research value lives in config with its rationale documented HERE, no literal in
@@ -1664,6 +1704,22 @@ class Config:
             "setups_reaction_threshold_bps",
             "setups_max_events_per_band_per_session",
             "setups_5m_fetch_retention_days",
+            # The event-window recording driver's padding / selection-cap / split-ratio parameters
+            # (era-5B capability 3, J-03): the IDENTICAL tradability_*/setups_* rationale directly
+            # above -- the recording driver and the tape-timeline join are a SEPARATE, additive
+            # capability over compute_setups' and DatasetStore's frozen output (never stamped
+            # with, or compared across, a config_fingerprint anywhere; a recorded dataset's OWN
+            # provenance is its stored metadata, never this fingerprint), so two journals identical
+            # in every FINGERPRINTED threshold but configured with different recording padding, a
+            # different selection cap, or a different split ratio MUST share a fingerprint (else
+            # every temp-config test of these brand-new, unrelated parameters would mint a
+            # different fingerprint and falsely fragment the tape/backtest/PnL pools those OTHER
+            # thresholds exist to protect). Pinned by a fingerprint-stability test + the
+            # real-threshold counter-test in tests/test_setups.py.
+            "recording_pre_touch_minutes",
+            "recording_post_touch_minutes",
+            "recording_event_selection_cap",
+            "recording_holdout_fraction",
             "journal_list_default_limit",
             "journal_list_max_limit",
             "analytics_min_sample_size",
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index 961bfde..f063d13 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -50,7 +50,7 @@ from .bars import (
     EmptyBarWindowError,
 )
 from .levels import compute_levels
-from .setups import BROKE, CHOPPED, REJECTED, compute_setups
+from .setups import BROKE, CHOPPED, REJECTED, compute_setups, enrich_with_tape_timeline
 from .tradability import compute_tradability
 from .datasets import (
     VALID_SOURCE_KINDS as DATASET_SOURCE_KINDS,
@@ -1889,14 +1889,22 @@ def list_setups(
 
 
 @router.get("/setups/{setup_id}")
-def get_setup(setup_id: str, store: BarStore = Depends(get_bar_store)) -> dict:
+def get_setup(
+    setup_id: str,
+    store: BarStore = Depends(get_bar_store),
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+) -> dict:
     """One touch event's drill-in -- band, reaction, forward returns, and the ``tape_timeline``
-    field (present but honestly empty until J-03 records) -- served VERBATIM. 404 for an unknown
-    id (never a fabricated event)."""
+    field, served VERBATIM. 404 for an unknown id (never a fabricated event). The tape join
+    (era-5B J-03) happens ONLY here, never inside ``compute_setups``'s shared scan loop
+    (``list_setups`` above stays byte-identical, unenriched): a recorded ``DatasetStore`` dataset
+    whose window covers this event's ``touch_ts`` is replayed through the frozen ``TapeEngine`` and
+    joined onto ``tape_timeline``; an event with no recorded dataset keeps it honestly empty."""
     events = compute_setups(store, CONFIG)["events"]
     event = next((e for e in events if e["id"] == setup_id), None)
     if event is None:
         raise HTTPException(status_code=404, detail=f"no setup event with id '{setup_id}'")
+    event = enrich_with_tape_timeline(event, dataset_store, CONFIG)
     return {"event": event}
 
 
diff --git a/apps/backend/app/research/setups.py b/apps/backend/app/research/setups.py
index 194788e..8ffc759 100644
--- a/apps/backend/app/research/setups.py
+++ b/apps/backend/app/research/setups.py
@@ -16,8 +16,9 @@ module. ``research/studies.py`` owns an UNRELATED, pre-existing concept: a live
 OCCURRENCE (``level_break`` / ``failed_move_fade`` / ``absorption_reversal`` / ``trend_continuation``)
 checked against the frozen ``TapeEngine``'s live STATE. THIS module's "event" is a completely
 different thing: a STORED 2026-dated 5m bar's OHLC range intersecting a tradable-map BAND, checked
-purely against historical bars -- no engine, no live state, no tape at all (the tape join is J-03,
-out of scope here; every event's ``tape_timeline`` field is present but honestly empty until then).
+purely against historical bars -- no engine, no live state, no tape at all (a recorded event's
+``tape_timeline`` field is joined on by ``enrich_with_tape_timeline`` below, era-5B J-03; an event
+with no recorded dataset keeps an honestly empty ``tape_timeline``).
 The two vocabularies happen to share the English word "setup"; they are never conflated, never
 share config, and never share code.
 
@@ -72,6 +73,30 @@ identity fields, never ``uuid4`` or any other unseeded/wall-clock source -- and
 sorted by an explicit total order). Panel symbols are walked in the config-owned order; sessions
 within a symbol are walked oldest-first; each session's bands are read in ``compute_tradability``'s
 own served order.
+
+**Tape-at-the-wall join (era-5B capability 4, J-03).** ``enrich_with_tape_timeline`` -- called
+ONLY from the ``GET /research/setups/{id}`` route, NEVER from ``compute_setups``'s shared scan
+loop above (a per-event ``DatasetStore`` lookup inside that loop would add an O(events) dataset
+scan to the already-slow full-panel list route, and would entangle the join with the scan's own
+determinism guarantees) -- matches a recorded ``DatasetStore`` dataset to ONE event by ``symbol``
+equality plus the dataset's own ``[window_start_utc, window_end_utc]`` containing the event's
+``touch_ts`` (``DatasetStore``'s meta schema is frozen with no "associated event" field, so this
+containment test is the only available join key; ties -- more than one dataset's window covering
+the same touch -- break on the earliest ``created_utc``, then id, for determinism). A match is
+replayed through the FROZEN ``TapeEngine`` via ``DatasetStore.replay`` VERBATIM -- this module
+never constructs a second engine and never reimplements classification -- and the per-tick
+snapshot stream is collapsed to STATE-TRANSITION entries only, mirroring
+``engine.history.HistoryBuffer.note_state``'s own idiom (a marker only when ``tape_state``
+CHANGES) rather than one row per raw tick, and -- the SAME idiom -- a transition into a state
+outside ``Config.history_marker_states`` (i.e. ``unclear``) is not marked: an "uncertain" read is
+not itself a meaningful "the tape said X" call, and reusing ``history_marker_states`` (rather than
+a second hardcoded "unclear" literal) keeps "which states count as meaningful" owned in exactly
+one place. Each recorded window's replay uses LOGICAL per-window timestamps (``HistoricalProvider``'s
+"logical, not wall-clock" scheme), so a timeline entry's real UTC instant is reconstructed as the
+dataset's OWN stamped ``epoch_anchor`` plus the snapshot's logical timestamp -- the identical
+``epoch_anchor + logical_ts`` reconstruction ``serializers.serialize_history``'s chart projection
+already uses, never a raw logical offset (which would misread as a bogus near-1970 date). An event
+with no matching recorded dataset keeps its honestly empty ``tape_timeline`` -- never fabricated.
 """
 
 from __future__ import annotations
@@ -82,6 +107,7 @@ from datetime import date, datetime, timezone
 from ..config import Config
 from ..providers.adapters.base import RawBar
 from .bars import BarStore
+from .datasets import DatasetStore, parse_utc_epoch
 from .tradability import RESISTANCE, SUPPORT, compute_tradability
 
 REJECTED = "rejected"
@@ -288,3 +314,72 @@ def compute_setups(store: BarStore, config: Config) -> dict:
                     ))
     events.sort(key=_event_sort_key)
     return {"events": events}
+
+
+# --- Tape-at-the-wall join (era-5B capability 4, J-03) -- see the module docstring's own section
+# for the full design. Called ONLY from the GET /research/setups/{id} route, never from
+# compute_setups' shared scan loop above. -----------------------------------------------------
+
+
+def _matching_dataset(symbol: str, touch_ts: str, dataset_store: DatasetStore) -> dict | None:
+    """The recorded ``DatasetStore`` dataset whose window covers ``touch_ts`` for ``symbol``, or
+    ``None``. Match = symbol equality + ``[window_start_utc, window_end_utc]`` containing
+    ``touch_ts`` (inclusive both ends). Every timestamp is parsed to an epoch via the SAME
+    ``parse_utc_epoch`` the ``/research/datasets`` route itself uses -- a deliberately NUMERIC
+    comparison, never a lexicographic string one: two otherwise-equal ISO instants stamped at
+    different fractional-second precision (a real possibility -- a caller-supplied window bound
+    need not carry the same microsecond precision this module's own ``_iso`` always emits for
+    ``touch_ts``) can sort in the WRONG order as plain strings (``"...:00Z"`` > ``"...:00.000001Z"``
+    lexicographically, since ``"Z" > "."`` in ASCII), so this join never risks that. Datasets
+    already known-healthy: ``DatasetStore.list()`` verifies every file's checksum and separates any
+    corrupt file into its own ``errors`` return before this function ever sees a candidate. Ties
+    (more than one dataset's window covering the same touch) break on the earliest ``created_utc``,
+    then ``id`` -- deterministic, never insertion-order happenstance."""
+    touch_epoch = parse_utc_epoch(touch_ts)
+    records, _errors = dataset_store.list()
+    candidates = [
+        r for r in records
+        if r["symbol"] == symbol
+        and parse_utc_epoch(r["window_start_utc"]) <= touch_epoch <= parse_utc_epoch(r["window_end_utc"])
+    ]
+    if not candidates:
+        return None
+    return min(candidates, key=lambda r: (r["created_utc"], r["id"]))
+
+
+def _tape_timeline(dataset_meta: dict, dataset_store: DatasetStore, config: Config) -> list[dict]:
+    """The five-state timeline for one matched dataset: replay it through the FROZEN ``TapeEngine``
+    via ``DatasetStore.replay`` (never reimplemented here) and collapse the per-tick snapshot
+    stream to state-TRANSITION entries only -- the ``HistoryBuffer.note_state`` idiom (a marker
+    only when ``tape_state`` changes, and only into a state ``Config.history_marker_states`` marks
+    as meaningful -- a transition into ``unclear`` is not itself a meaningful "the tape said X"
+    call, mirrored here rather than inventing a second "which states matter" concept). Real UTC
+    instants are reconstructed as the dataset's own ``epoch_anchor`` plus each snapshot's LOGICAL
+    timestamp (``HistoricalProvider``'s "logical, not wall-clock" replay scheme) -- the identical
+    reconstruction ``serializers.serialize_history`` already uses for chart markers."""
+    epoch_anchor = dataset_meta["epoch_anchor"]
+    meaningful = frozenset(config.history_marker_states)
+    prev_state: str | None = None
+    timeline: list[dict] = []
+    for snapshot in dataset_store.replay(dataset_meta["id"], config):
+        if snapshot.tape_state != prev_state:
+            if snapshot.tape_state in meaningful:
+                timeline.append({
+                    "timestamp": _iso(epoch_anchor + snapshot.timestamp) if epoch_anchor is not None else None,
+                    "state": snapshot.tape_state,
+                    "confidence": snapshot.confidence,
+                })
+            prev_state = snapshot.tape_state
+    return timeline
+
+
+def enrich_with_tape_timeline(event: dict, dataset_store: DatasetStore, config: Config) -> dict:
+    """Join the tape-at-the-wall timeline onto ONE event's drill-in (era-5B J-03). Returns a NEW
+    dict (never mutates ``event``) with ``tape_timeline`` replaced by the matched dataset's replay,
+    or the event UNCHANGED (still an honestly empty ``tape_timeline``) when no recorded dataset
+    matches. Every other field is served verbatim -- this function never touches band, reaction,
+    or forward-return values (single source of truth: ``compute_setups`` owns those alone)."""
+    dataset = _matching_dataset(event["symbol"], event["touch_ts"], dataset_store)
+    if dataset is None:
+        return event
+    return {**event, "tape_timeline": _tape_timeline(dataset, dataset_store, config)}
diff --git a/apps/backend/tests/test_setups.py b/apps/backend/tests/test_setups.py
index 9da859d..9997213 100644
--- a/apps/backend/tests/test_setups.py
+++ b/apps/backend/tests/test_setups.py
@@ -32,7 +32,8 @@ import pytest
 from app.config import CONFIG, Config
 from app.providers.adapters.base import RawBar
 from app.research.bars import BarStore
-from app.research.setups import BROKE, CHOPPED, REJECTED, compute_setups
+from app.research.datasets import DatasetStore
+from app.research.setups import BROKE, CHOPPED, REJECTED, compute_setups, enrich_with_tape_timeline
 
 FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"
 
@@ -540,3 +541,233 @@ def test_aapl_frozen_tradability_and_levels_output_is_byte_identical_to_before(t
 
     assert json.dumps(levels_before, sort_keys=True) == json.dumps(levels_after, sort_keys=True)
     assert json.dumps(tradability_before, sort_keys=True) == json.dumps(tradability_after, sort_keys=True)
+
+
+# --- Tape-at-the-wall join (era-5B capability 4, J-03): a committed real-tick dataset joined
+# onto a synthetic PG touch event -----------------------------------------------------------------
+#
+# ONE synthetic PG event whose touch lands inside the REAL committed PG SIP reference window
+# (tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json, 2026-06-09T17:00-17:10). Bars are
+# ENGINEERED (the test_tradability.py/test_setups.py synthetic-fixture precedent: full control
+# over exact expected numbers), but the recorded TICK data the join replays is REAL, never
+# fabricated: tests/fixtures/datasets_j03/ was generated ONCE, through the real record path, by
+# scripts/generate_setups_join_fixture.py (see that script's own docstring for provenance) --
+# never hand-crafted JSON.
+
+FIXTURE_DATASETS_J03_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"
+
+_PG_SESSION_BASE = datetime(2026, 6, 9, 17, 0, 0, tzinfo=timezone.utc).timestamp()
+
+
+def _pg_5m(offset_seconds: float, o: float, h: float, l: float, c: float, v: int) -> RawBar:
+    return RawBar("PG", "5m", _PG_SESSION_BASE + offset_seconds, o, h, l, c, v)
+
+
+_PG_DAILY_BASIS = RawBar(
+    "PG", "1d", datetime(2026, 6, 8, tzinfo=timezone.utc).timestamp(),
+    100.0, 110.00, 90.00, 100.00, 1_000,
+)
+# Touch bar at 17:02:30Z -- 30s inside the committed fixture's own recorded [17:02:00, 17:03:00)
+# window -- touching the lone resistance level (2026-06-08's daily high, 110.00).
+_PG_TOUCH_BAR = _pg_5m(150.0, 109.80, 110.05, 109.70, 110.02, 5_000)
+_PG_REACTION_BAR_1 = _pg_5m(450.0, 110.02, 110.10, 109.00, 109.20, 4_000)  # +1 horizon
+_PG_REACTION_BAR_2 = _pg_5m(750.0, 109.20, 109.30, 108.50, 108.80, 3_000)  # +2 horizon -- REJECTED
+
+
+def _pg_join_config() -> Config:
+    return Config(setups_panel_symbols=("PG",), setups_forward_return_horizons_bars=(1, 2))
+
+
+def _seed_pg_join_bars(store: BarStore) -> None:
+    store.record(
+        symbol="PG", timeframe="1d", window_start_utc="2026-06-08T00:00:00Z",
+        window_end_utc="2026-06-09T00:00:00Z", feed="sip", bars=[_PG_DAILY_BASIS],
+    )
+    store.record(
+        symbol="PG", timeframe="5m", window_start_utc="2026-06-09T17:00:00Z",
+        window_end_utc="2026-06-09T17:15:00Z", feed="sip",
+        bars=[_PG_TOUCH_BAR, _PG_REACTION_BAR_1, _PG_REACTION_BAR_2],
+    )
+
+
+def _pg_join_event(bar_store: BarStore) -> dict:
+    result = compute_setups(bar_store, _pg_join_config())
+    assert len(result["events"]) == 1, "the engineered PG fixture must emit exactly one event"
+    return result["events"][0]
+
+
+def test_pg_join_event_has_the_expected_shape_before_any_join(tmp_path):
+    """Verified by direct computation against the engineered fixture (never hand-derived) -- the
+    UN-enriched event compute_setups emits, before the join runs at all."""
+    bar_store = BarStore(tmp_path / "bars")
+    _seed_pg_join_bars(bar_store)
+    event = _pg_join_event(bar_store)
+
+    assert event["id"] == "77e4900ec3089ded"
+    assert event["symbol"] == "PG"
+    assert event["session_date"] == "2026-06-09"
+    assert event["touch_ts"] == "2026-06-09T17:02:30.000000Z"
+    assert event["reaction"] == REJECTED
+    assert event["band"] == {
+        "side": "resistance",
+        "price_low": 110.0,
+        "price_high": 110.0,
+        "class": None,
+        "quality_score": 27.0,
+        "round_number": False,
+        "member_count": 1,
+        "members": [
+            {
+                "price": 110.0, "strength": 4.0, "timeframe": "1d",
+                "touch_count": 1, "type": "prior-period-extreme",
+            },
+        ],
+    }
+    assert event["forward_returns"] == [
+        {"horizon_bars": 1, "return_fraction": pytest.approx(-0.007453190329031024)},
+        {"horizon_bars": 2, "return_fraction": pytest.approx(-0.011088892928558435)},
+    ]
+    assert event["tape_timeline"] == [], "un-joined -- honestly empty, exactly like every other event"
+
+
+def test_join_path_matches_the_committed_fixture_and_returns_the_exact_five_state_timeline(tmp_path):
+    """J-03's headline join-path proof: the committed real-tick fixture
+    (tests/fixtures/datasets_j03/) covers the engineered touch's own [17:02:00, 17:03:00) window,
+    so ``enrich_with_tape_timeline`` matches it by symbol + window containment, replays it through
+    the FROZEN ``TapeEngine``, and returns the EXACT state/confidence/order sequence -- verified by
+    direct computation against the real committed fixture (never hand-derived), collapsed from
+    1,963 raw trade+quote events down to 4 meaningful state-transition entries (the
+    ``HistoryBuffer.note_state`` idiom this module's join mirrors)."""
+    bar_store = BarStore(tmp_path / "bars")
+    _seed_pg_join_bars(bar_store)
+    event = _pg_join_event(bar_store)
+
+    dataset_store = DatasetStore(FIXTURE_DATASETS_J03_DIR)
+    enriched = enrich_with_tape_timeline(event, dataset_store, _pg_join_config())
+
+    # Every OTHER field is served verbatim -- the join touches tape_timeline alone.
+    unchanged = {k: v for k, v in enriched.items() if k != "tape_timeline"}
+    assert unchanged == {k: v for k, v in event.items() if k != "tape_timeline"}
+
+    assert enriched["tape_timeline"] == [
+        {
+            "timestamp": "2026-06-09T17:02:08.926045Z", "state": "seller_control",
+            "confidence": pytest.approx(0.600948859073259),
+        },
+        {
+            "timestamp": "2026-06-09T17:02:10.313400Z", "state": "seller_control",
+            "confidence": pytest.approx(0.6186718843924585),
+        },
+        {
+            "timestamp": "2026-06-09T17:02:13.893943Z", "state": "seller_control",
+            "confidence": pytest.approx(0.6827213366979764),
+        },
+        {
+            "timestamp": "2026-06-09T17:02:55.616940Z", "state": "seller_control",
+            "confidence": pytest.approx(0.7506461682283672),
+        },
+    ]
+    # Chronological order (never insertion-order happenstance).
+    timestamps = [entry["timestamp"] for entry in enriched["tape_timeline"]]
+    assert timestamps == sorted(timestamps)
+
+
+def test_join_path_is_deterministic_across_repeat_calls(tmp_path):
+    bar_store = BarStore(tmp_path / "bars")
+    _seed_pg_join_bars(bar_store)
+    event = _pg_join_event(bar_store)
+    dataset_store = DatasetStore(FIXTURE_DATASETS_J03_DIR)
+
+    first = enrich_with_tape_timeline(event, dataset_store, _pg_join_config())
+    second = enrich_with_tape_timeline(event, dataset_store, _pg_join_config())
+    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
+
+
+def test_unmatched_event_keeps_an_honestly_empty_tape_timeline(tmp_path):
+    """An event with NO recorded dataset covering its touch -- here, a differently-timed touch (3h
+    later) the committed fixture's [17:02, 17:03) window does not cover -- stays honestly empty,
+    never fabricated. Verified by direct computation: an otherwise-identical fixture, time-shifted,
+    still emits exactly one REJECTED event -- only ``touch_ts``/``id`` differ."""
+    bar_store = BarStore(tmp_path / "bars")
+    bar_store.record(
+        symbol="PG", timeframe="1d", window_start_utc="2026-06-08T00:00:00Z",
+        window_end_utc="2026-06-09T00:00:00Z", feed="sip", bars=[_PG_DAILY_BASIS],
+    )
+    late_offset = 3 * 3600  # three hours later than the committed fixture's own window
+    bar_store.record(
+        symbol="PG", timeframe="5m", window_start_utc="2026-06-09T17:00:00Z",
+        window_end_utc="2026-06-09T21:00:00Z", feed="sip",
+        bars=[
+            _pg_5m(late_offset + 150.0, 109.80, 110.05, 109.70, 110.02, 5_000),
+            _pg_5m(late_offset + 450.0, 110.02, 110.10, 109.00, 109.20, 4_000),
+            _pg_5m(late_offset + 750.0, 109.20, 109.30, 108.50, 108.80, 3_000),
+        ],
+    )
+    event = _pg_join_event(bar_store)
+    assert event["touch_ts"] == "2026-06-09T20:02:30.000000Z"
+    assert event["reaction"] == REJECTED
+
+    dataset_store = DatasetStore(FIXTURE_DATASETS_J03_DIR)  # the SAME real committed fixture
+    enriched = enrich_with_tape_timeline(event, dataset_store, _pg_join_config())
+    assert enriched == event, "no matching dataset -> the event is returned completely unchanged"
+    assert enriched["tape_timeline"] == []
+
+
+def test_empty_dataset_store_leaves_every_event_honestly_empty(tmp_path):
+    bar_store = BarStore(tmp_path / "bars")
+    _seed_pg_join_bars(bar_store)
+    event = _pg_join_event(bar_store)
+
+    empty_dataset_store = DatasetStore(tmp_path / "no-datasets-here")
+    enriched = enrich_with_tape_timeline(event, empty_dataset_store, _pg_join_config())
+    assert enriched == event
+    assert enriched["tape_timeline"] == []
+
+
+# --- Single source of truth: the join reuses the frozen TapeEngine/DatasetStore.replay, and stays
+# confined to the detail route's own wiring -- never inside compute_setups' shared scan loop ------
+
+
+def test_setups_join_reuses_dataset_store_replay_never_a_second_tape_engine():
+    """era-5B J-03 critical anti-goal (mirrors
+    ``test_setups_module_reuses_compute_tradability_verbatim_never_a_second_map_engine``): the tape
+    join must replay through the FROZEN ``TapeEngine`` via ``DatasetStore.replay`` -- never
+    construct a second engine, never reimplement classification."""
+    from app.research import setups as setups_module
+
+    src = inspect.getsource(setups_module)
+    assert "dataset_store.replay(" in src
+    assert "TapeEngine(" not in src, "setups.py must never construct a second TapeEngine"
+    assert "TapeStateClassifier" not in src, "setups.py must never reimplement classification"
+
+    import_lines = [
+        line.strip() for line in src.splitlines() if line.strip().startswith(("import ", "from "))
+    ]
+    dataset_imports = [
+        line for line in import_lines
+        if line.endswith(".datasets import DatasetStore, parse_utc_epoch")
+    ]
+    assert dataset_imports, "setups.py must import DatasetStore (+ parse_utc_epoch) from .datasets"
+
+
+def test_compute_setups_itself_never_touches_the_dataset_store():
+    """Architecture guard: the join lives ONLY in ``enrich_with_tape_timeline``, called ONLY from
+    the ``GET /research/setups/{id}`` route -- ``compute_setups``'s own shared scan loop (used by
+    BOTH the list and detail routes) must stay completely free of any ``DatasetStore`` reference,
+    so the join never adds an O(events) dataset-store scan to the already-slow full-panel list
+    route."""
+    src = inspect.getsource(compute_setups)
+    assert "dataset" not in src.lower(), "compute_setups must never reference the dataset store"
+
+
+# --- Config: the recording constants are excluded from config_fingerprint -----------------------
+
+
+def test_recording_config_fields_are_excluded_from_config_fingerprint():
+    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
+    assert Config(recording_pre_touch_minutes=1.0).config_fingerprint() == CONFIG.config_fingerprint()
+    assert Config(recording_post_touch_minutes=1.0).config_fingerprint() == CONFIG.config_fingerprint()
+    assert Config(recording_event_selection_cap=1).config_fingerprint() == CONFIG.config_fingerprint()
+    assert Config(recording_holdout_fraction=0.99).config_fingerprint() == CONFIG.config_fingerprint()
+    # ...while a real classifier threshold still moves it (the counter-test).
+    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()
diff --git a/apps/backend/tests/test_setups_api.py b/apps/backend/tests/test_setups_api.py
index 3e59af3..2c3a7ac 100644
--- a/apps/backend/tests/test_setups_api.py
+++ b/apps/backend/tests/test_setups_api.py
@@ -23,6 +23,7 @@ from app.config import CONFIG
 from app.main import app, get_market_adapter, manager
 from app.providers.adapters.base import RawBar
 from app.research.bars import BarStore
+from app.research.datasets import DatasetStore
 from app.research.routes import ResearchRegistry, set_registry
 from app.research.setups import compute_setups
 from app.research.store import JournalStore
@@ -31,11 +32,20 @@ YAHOO_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "yahoo"
 AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"
 AAPL_5M_SETUPS_FIXTURE = "AAPL_5m_20260615_20260630.json"
 
+# The committed J-03 tape-at-the-wall join fixture (see test_setups.py's own header + generation
+# script scripts/generate_setups_join_fixture.py for provenance).
+FIXTURE_DATASETS_J03_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"
+
 
 @pytest.fixture
 def ctx(tmp_path, monkeypatch):
     bar_dir = tmp_path / "bars"
     monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_dir))
+    # Era-5B J-03: get_setup now also depends on the DatasetStore. Point it at an EMPTY temp dir by
+    # default (the test_datasets_api.py ctx precedent) so this file's route-level assertions never
+    # accidentally read a real operator's local (gitignored) recorded datasets -- hermetic by
+    # construction, exactly like the bar-dir override directly above.
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
     store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
     registry = ResearchRegistry(store, CONFIG)
     set_registry(registry)
@@ -256,3 +266,97 @@ def test_get_setup_unknown_id_on_an_empty_store_is_still_404_never_an_error(ctx)
     client, _bar_dir = ctx  # nothing seeded
     r = client.get("/research/setups/anything")
     assert r.status_code == 404
+
+
+# --- Tape-at-the-wall join through the REAL route (era-5B capability 4, J-03) -------------------
+#
+# ``list_setups``/``get_setup`` read the process-global ``CONFIG`` (this file's own header
+# docstring), so ``setups_panel_symbols`` cannot be overridden per-request -- every route-level
+# event here is necessarily a REAL shipped-panel symbol (AAPL). No committed REAL tick fixture
+# exists for any shipped panel symbol (only the era-3 PG/F reference captures, neither in the
+# panel), so a route-level proof of "a REAL committed dataset ENRICHES a REAL panel event" is only
+# reachable with real Alpaca credentials (J-03's own operator-gated headline) -- exactly what
+# ``test_setups.py``'s module-level tests already prove keylessly for the join MECHANISM itself
+# (bypassing the route's fixed panel via a directly-passed ``Config(setups_panel_symbols=("PG",))``).
+# What IS honestly provable here, keyless, through the REAL route: the join is correctly wired
+# (never crashes, never silently mismatches) and correctly SYMBOL-SCOPED (a real recorded dataset
+# for an off-panel symbol never leaks into an on-panel event's timeline).
+
+
+def test_get_setup_pinned_aapl_event_through_the_real_route_is_keyless_honest_empty(ctx):
+    """The pinned AAPL 2026-06-22 event's drill-in, read through the REAL detail route: keyless (no
+    Alpaca credentials, no recorded AAPL dataset in this hermetic dataset dir), so
+    ``tape_timeline`` is honestly empty -- the credentialed recording (J-03's operator-gated
+    headline) is what fills this in for real."""
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+    listed = client.get(
+        "/research/setups", params={"symbol": "AAPL", "reaction": "rejected"}
+    ).json()["events"]
+    pinned = next(
+        e for e in listed
+        if e["session_date"] == "2026-06-22" and e["band"]["side"] == "resistance"
+        and e["band"]["price_low"] <= 300.48 and e["band"]["price_high"] >= 302.07
+    )
+
+    r = client.get(f"/research/setups/{pinned['id']}")
+    assert r.status_code == 200
+    event = r.json()["event"]
+    assert event["reaction"] == "rejected"
+    assert event["tape_timeline"] == []
+
+
+def test_get_setup_detail_stays_unenriched_when_no_dataset_matches_the_symbol(ctx, monkeypatch):
+    """A REAL recorded dataset (the committed J-03 fixture) sits in the dataset store, but its
+    symbol ("PG") matches no AAPL event -- ``GET /research/setups/{id}`` must stay byte-identical
+    to the list entry (the join is correctly symbol-scoped, never a blind "first dataset found"
+    attach)."""
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASETS_J03_DIR))
+
+    listed = client.get("/research/setups").json()["events"]
+    assert listed
+    target = listed[0]
+
+    r = client.get(f"/research/setups/{target['id']}")
+    assert r.status_code == 200
+    assert r.json() == {"event": target}
+    assert r.json()["event"]["tape_timeline"] == []
+
+
+def test_list_setups_never_enriches_even_when_a_matching_dataset_exists(ctx, monkeypatch):
+    """The LIST route (``GET /research/setups``) must stay UN-enriched no matter what the dataset
+    store holds -- the join lives ONLY in the detail route (architecture guard: a per-event dataset
+    lookup inside the shared scan would regress the already-slow full-panel list route)."""
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASETS_J03_DIR))
+
+    events = client.get("/research/setups").json()["events"]
+    assert events
+    assert all(e["tape_timeline"] == [] for e in events)
+
+
+def test_get_setup_rest_matches_direct_module_join_byte_for_byte(ctx, monkeypatch):
+    """``GET /research/setups/{id}``'s enriched output matches a direct ``compute_setups`` +
+    ``enrich_with_tape_timeline`` call byte-for-byte -- single source of truth, no second
+    computation path (the ``test_list_setups_rest_matches_module_output_byte_for_byte`` precedent,
+    extended to the join)."""
+    client, bar_dir = ctx
+    _seed_aapl(bar_dir)
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASETS_J03_DIR))
+
+    listed = client.get("/research/setups").json()["events"]
+    target = listed[0]
+    r = client.get(f"/research/setups/{target['id']}")
+    assert r.status_code == 200
+
+    from app.research.setups import enrich_with_tape_timeline
+
+    direct_events = compute_setups(BarStore(bar_dir), CONFIG)["events"]
+    direct_event = next(e for e in direct_events if e["id"] == target["id"])
+    direct_enriched = enrich_with_tape_timeline(
+        direct_event, DatasetStore(FIXTURE_DATASETS_J03_DIR), CONFIG
+    )
+    assert r.json() == {"event": direct_enriched}
diff --git a/apps/backend/scripts/generate_setups_join_fixture.py b/apps/backend/scripts/generate_setups_join_fixture.py
new file mode 100644
index 0000000..0abefab
--- /dev/null
+++ b/apps/backend/scripts/generate_setups_join_fixture.py
@@ -0,0 +1,70 @@
+"""Generate the ONE committed tape-at-the-wall join-path fixture (era-5B J-03) -- ONCE.
+
+Produced through the REAL record path (``record_from_source`` -> ``DatasetStore``, checksum
+computed at registration) from the SAME committed keyless PG SIP reference window
+``generate_dataset_fixtures.py`` already uses for the era-3 J-02 train/holdout pair -- never
+hand-crafted JSON -- sliced to a NEW, disjoint sub-window and committed under
+``tests/fixtures/datasets_j03/`` (a directory of its own, so this fixture is never confused with,
+or accidentally pooled with, the era-3 pair). CI then proves the tape-at-the-wall join
+end-to-end -- record -> register -> replay through the frozen ``TapeEngine`` -> collapse to a
+state-transition timeline -- with no credentials (``tests/test_setups.py``).
+
+The window (2026-06-09T17:02:00Z .. 17:03:00Z) is a ONE-MINUTE slice of the reference capture,
+disjoint from BOTH the existing committed train (17:00:00-17:01:00) and holdout (17:05:00-
+17:05:45) windows (nothing here is ever pooled with, or judged on, data those already use), dense
+enough to carry a real, non-trivial tape-state read (~1,960 real trade+quote events).
+
+Run from ``apps/backend``:  ``.venv/bin/python scripts/generate_setups_join_fixture.py``
+
+The script REFUSES to run if the fixture directory already holds a dataset -- the committed
+fixture is frozen at its one generation (regenerating would mint a new id/timestamp and re-pin
+the join-path test's exact-value assertions for no reason). Delete the directory first if a
+regeneration is genuinely intended.
+"""
+
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from app.config import CONFIG  # noqa: E402
+from app.research.datasets import SPLIT_TRAIN, DatasetStore, record_from_source  # noqa: E402
+
+FIXTURE_DATASET_DIR = BACKEND_DIR / "tests" / "fixtures" / "datasets_j03"
+
+# Disjoint from the era-3 J-02 pair's 17:00:00-17:01:00 (train) / 17:05:00-17:05:45 (holdout).
+WINDOW_START, WINDOW_END = "2026-06-09T17:02:00Z", "2026-06-09T17:03:00Z"
+
+
+def main() -> int:
+    store = DatasetStore(FIXTURE_DATASET_DIR)
+    existing, errors = store.list()
+    if existing or errors:
+        print(
+            f"REFUSED: {FIXTURE_DATASET_DIR} already holds {len(existing)} dataset(s) "
+            f"(+{len(errors)} unreadable) — the committed fixture is frozen at its one generation."
+        )
+        return 1
+    meta = record_from_source(
+        store,
+        source_kind="reference",
+        source_id="PG_SIP_REFERENCE",
+        split=SPLIT_TRAIN,
+        start=WINDOW_START,
+        end=WINDOW_END,
+        config=CONFIG,
+    )
+    counts = meta["event_counts"]
+    print(
+        f"id={meta['id']} {meta['symbol']} {meta['window_start_utc']} .. {meta['window_end_utc']}"
+        f" feed={meta['data_feed']} trades={counts['trades']} quotes={counts['quotes']}"
+        f" checksum={meta['checksum']}"
+    )
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/scripts/record_event_windows.py b/apps/backend/scripts/record_event_windows.py
new file mode 100644
index 0000000..36ec3ca
--- /dev/null
+++ b/apps/backend/scripts/record_event_windows.py
@@ -0,0 +1,228 @@
+"""Event-window tape recording driver (era-5B capability 3, J-03) -- the operator/integration
+script that selects top-ranked band-touch events from ``GET /research/setups`` and records each
+event's window (config-owned padding) into a registered ``DatasetStore`` dataset, via the
+EXISTING ``POST /research/datasets`` route (``source_kind="historical"``) -- the SAME seam era-3's
+studies runner already uses, driven in-process through a real ``TestClient`` against the real app
+(the ``scripts/populate_panel_bars.py`` precedent: no new production HTTP path).
+
+Selection (config-owned, deterministic, pre-registered -- no post-hoc tuning to manufacture
+survivors): the PINNED AAPL 2026-06-22 ~300 event is ALWAYS included when present in the scan;
+remaining events are then picked ONE-BEST-PER-SYMBOL-FIRST (by descending band ``quality_score``,
+walked in the config-owned panel order) to maximise SYMBOL SPREAD -- goal.md's ">= 5 symbols"
+headline -- before any leftover ``Config.recording_event_selection_cap`` budget fills with the
+next-best events overall.
+
+Each selected event's window is ``touch_ts`` +/- the config-owned padding
+(``Config.recording_pre_touch_minutes`` / ``recording_post_touch_minutes``), and its split tag is
+assigned by a NEW config-owned deterministic rule (``Config.recording_holdout_fraction`` -- see
+``config.py``'s own field docstring for the full rationale: a pure sha256 digest of the event's
+own stable id, no wall-clock, no unseeded randomness).
+
+CREDENTIALS. When Alpaca credentials are absent, ``POST /research/datasets``'s EXISTING
+historical-record validation returns an explicit 422 "unavailable" -- this script counts and
+reports that as BLOCKED (never fixture-substituted, never silently retried as something else),
+mirroring ``populate_panel_bars.py``'s own OK/SKIP/FAIL counter discipline. Recording is explicit
+and logged -- this script is the ONE place that act happens; nothing here is ambient or scheduled.
+
+Live network (when credentialed), keyless to SCAN (``GET /research/setups`` reads only already-
+stored bars). Writes into the REAL project dataset store (``apps/backend/.data/datasets``, or the
+``TAPEOLOGY_DATASET_DIR`` override if set). Run from ``apps/backend``:
+
+    .venv/bin/python scripts/record_event_windows.py
+    .venv/bin/python scripts/record_event_windows.py --dry-run
+"""
+
+from __future__ import annotations
+
+import argparse
+import hashlib
+import sys
+from datetime import datetime, timedelta, timezone
+from pathlib import Path
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from app.env import load_env  # noqa: E402
+
+load_env()
+
+from fastapi.testclient import TestClient  # noqa: E402
+
+from app.config import CONFIG, Config  # noqa: E402
+from app.main import app  # noqa: E402
+from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN  # noqa: E402
+from app.research.tradability import RESISTANCE  # noqa: E402
+
+# The pinned AAPL 2026-06-22 ~300 test (goal.md's ground-truth case) -- the SAME band-containment
+# check tests/test_setups.py's own pinned-event lookup uses. ALWAYS selected when present.
+_PINNED_SYMBOL = "AAPL"
+_PINNED_SESSION_DATE = "2026-06-22"
+_PINNED_PRICE_LOW_MAX = 300.48
+_PINNED_PRICE_HIGH_MIN = 302.07
+
+
+def _is_pinned_event(event: dict) -> bool:
+    return (
+        event["symbol"] == _PINNED_SYMBOL
+        and event["session_date"] == _PINNED_SESSION_DATE
+        and event["band"]["side"] == RESISTANCE
+        and event["band"]["price_low"] <= _PINNED_PRICE_LOW_MAX
+        and event["band"]["price_high"] >= _PINNED_PRICE_HIGH_MIN
+    )
+
+
+def _rank_key(event: dict) -> tuple:
+    """Descending band ``quality_score``, tie-broken by the event's own stable id -- deterministic,
+    never insertion-order happenstance (``tradability.py``'s own ``_rank_sort_key`` idiom, reused
+    as a technique for a different collection)."""
+    return (-event["band"]["quality_score"], event["id"])
+
+
+def select_recording_events(events: list[dict], config: Config) -> list[dict]:
+    """Select at most ``config.recording_event_selection_cap`` events to record: the pinned AAPL
+    2026-06-22 event ALWAYS first (when present), then one best-quality event per DISTINCT symbol
+    (config-owned panel order) to maximise symbol spread, then the next-best remaining events
+    overall fill any leftover cap budget. Pure + deterministic: an identical ``events`` input
+    always yields the identical selection."""
+    cap = config.recording_event_selection_cap
+    selected: list[dict] = [e for e in events if _is_pinned_event(e)]
+    selected_ids = {e["id"] for e in selected}
+
+    by_symbol: dict[str, list[dict]] = {}
+    for e in events:
+        if e["id"] in selected_ids:
+            continue
+        by_symbol.setdefault(e["symbol"], []).append(e)
+    for candidates in by_symbol.values():
+        candidates.sort(key=_rank_key)
+
+    # Pass 1: one best event per distinct symbol, in config-owned panel order (symbol spread).
+    for symbol in config.setups_panel_symbols:
+        if len(selected) >= cap:
+            break
+        candidates = by_symbol.get(symbol) or []
+        if candidates:
+            best = candidates[0]
+            selected.append(best)
+            selected_ids.add(best["id"])
+
+    # Pass 2: fill any remaining cap budget with the next-best events overall.
+    remaining = sorted((e for e in events if e["id"] not in selected_ids), key=_rank_key)
+    for e in remaining:
+        if len(selected) >= cap:
+            break
+        selected.append(e)
+        selected_ids.add(e["id"])
+
+    return selected
+
+
+def _iso(dt: datetime) -> str:
+    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
+
+
+def event_window(event: dict, config: Config) -> tuple[str, str]:
+    """The event's recording window (``touch_ts`` -/+ the config-owned padding), as ISO-8601 UTC
+    strings the ``/research/datasets`` route accepts verbatim."""
+    touch = datetime.fromisoformat(event["touch_ts"].replace("Z", "+00:00"))
+    start = touch - timedelta(minutes=config.recording_pre_touch_minutes)
+    end = touch + timedelta(minutes=config.recording_post_touch_minutes)
+    return _iso(start), _iso(end)
+
+
+def split_for_event(event_id: str, config: Config) -> str:
+    """Deterministic train/holdout split assignment (``config.py``'s own
+    ``recording_holdout_fraction`` docstring has the full rationale): a pure sha256 digest of the
+    event's OWN stable id, mapped into ``[0, 1)`` and compared against the config-owned holdout
+    fraction. No wall-clock, no unseeded randomness -- an identical event id always resolves to the
+    identical split, every run."""
+    digest = hashlib.sha256(f"recording-split|{event_id}".encode("utf-8")).hexdigest()
+    fraction = int(digest[:8], 16) / 0xFFFFFFFF
+    return SPLIT_HOLDOUT if fraction < config.recording_holdout_fraction else SPLIT_TRAIN
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(
+        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
+    )
+    parser.add_argument(
+        "--dry-run", action="store_true",
+        help="print the selected events + windows without recording anything",
+    )
+    args = parser.parse_args()
+
+    with TestClient(app) as client:
+        setups_response = client.get("/research/setups")
+        if setups_response.status_code != 200:
+            print(f"FAIL: GET /research/setups returned HTTP {setups_response.status_code}")
+            return 1
+        events = setups_response.json()["events"]
+        print(f"scanned {len(events)} events across the panel")
+
+        selected = select_recording_events(events, CONFIG)
+        pinned_included = any(_is_pinned_event(e) for e in selected)
+        print(
+            f"selected {len(selected)} events across "
+            f"{len({e['symbol'] for e in selected})} symbols "
+            f"(pinned AAPL 2026-06-22 included: {pinned_included})"
+        )
+
+        recorded = blocked = skipped = failed = 0
+        for event in selected:
+            start, end = event_window(event, CONFIG)
+            split = split_for_event(event["id"], CONFIG)
+            if args.dry_run:
+                print(
+                    f"DRY  {event['symbol']:6s} {event['session_date']} touch={event['touch_ts']} "
+                    f"window=[{start} .. {end}) split={split}"
+                )
+                continue
+            body = {
+                "source_kind": "historical", "source_id": event["symbol"],
+                "split": split, "start": start, "end": end,
+            }
+            response = client.post("/research/datasets", json=body)
+            if response.status_code == 200:
+                meta = response.json()["dataset"]
+                print(
+                    f"OK      {event['symbol']:6s} {event['session_date']} touch={event['touch_ts']}: "
+                    f"dataset={meta['id']} feed={meta['data_feed']} split={meta['split']} "
+                    f"events={meta['event_counts']['total']}"
+                )
+                recorded += 1
+            elif response.status_code == 422 and "unavailable" in response.json().get("detail", ""):
+                print(
+                    f"BLOCKED {event['symbol']:6s} {event['session_date']}: real-data provider "
+                    f"unavailable -- Alpaca credentials not configured"
+                )
+                blocked += 1
+            elif response.status_code == 409:
+                print(f"SKIP    {event['symbol']:6s} {event['session_date']}: already registered")
+                skipped += 1
+            else:
+                print(
+                    f"FAIL    {event['symbol']:6s} {event['session_date']}: "
+                    f"HTTP {response.status_code} {response.json()}"
+                )
+                failed += 1
+
+    if args.dry_run:
+        return 0
+
+    print(
+        f"\n{recorded} recorded, {blocked} blocked (no credentials), "
+        f"{skipped} already-registered, {failed} failed"
+    )
+    if blocked and not recorded:
+        print(
+            "Alpaca credentials are not configured in this environment -- the credentialed "
+            "recording is honestly BLOCKED (never simulated). Set ALPACA_API_KEY / "
+            "ALPACA_API_SECRET (and TAPEOLOGY_LIVE_INTEGRATION=1 for the integration test) to "
+            "run for real."
+        )
+    return 1 if failed else 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/fixtures/datasets_j03/5232fa672b7b4077a5117d34b14c807d.json b/apps/backend/tests/fixtures/datasets_j03/5232fa672b7b4077a5117d34b14c807d.json
new file mode 100644
index 0000000..2883973
--- /dev/null
+++ b/apps/backend/tests/fixtures/datasets_j03/5232fa672b7b4077a5117d34b14c807d.json
@@ -0,0 +1 @@
+{"file_checksum": "e4b227a7143155544b3163f74df322cdc31d37e72637a33917184b5109eeebbf", "record": {"meta": {"id": "5232fa672b7b4077a5117d34b14c807d", "symbol": "PG", "window_start_utc": "2026-06-09T17:02:00Z", "window_end_utc": "2026-06-09T17:03:00Z", "data_feed": "sip", "event_counts": {"trades": 577, "quotes": 1386, "total": 1963}, "checksum": "0cd24ae2abf4357776910a36940d04170a20ae939f15465fb18d9e8afcc294e1", "split": "train", "source": "historical PG dataset", "source_kind": "reference", "source_id": "PG_SIP_REFERENCE", "epoch_anchor": 1781024520.00241, "created_utc": "2026-07-14T12:04:32.334687Z"}, "events": [{"type": "quote", "ts": 0.0, "bid": 148.98, "ask": 149.04, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 0.08151912689208984, "bid": 148.98, "ask": 149.04, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 0.10336613655090332, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 0.10367703437805176, "bid": 148.98, "ask": 149.03, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 0.10371208190917969, "bid": 148.98, "ask": 149.03, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 1.2920351028442383, "bid": 148.98, "ask": 149.03, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 1.2921149730682373, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 1.35329008102417, "bid": 148.98, "ask": 149.04, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 1.3533170223236084, "price": 149.01, "size": 3, "side": "unknown"}, {"type": "quote", "ts": 1.3534209728240967, "bid": 148.98, "ask": 149.04, "bid_size": 500, "ask_size": 200}, {"type": "trade", "ts": 1.4137001037597656, "price": 149.01, "size": 134, "side": "unknown"}, {"type": "quote", "ts": 1.747107982635498, "bid": 148.98, "ask": 149.04, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 1.7548460960388184, "bid": 148.98, "ask": 149.04, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 1.7554631233215332, "bid": 148.98, "ask": 149.04, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 1.7557380199432373, "bid": 148.98, "ask": 149.04, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 1.756059169769287, "bid": 148.98, "ask": 149.03, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 1.7576329708099365, "bid": 148.98, "ask": 149.03, "bid_size": 400, "ask_size": 100}, {"type": "trade", "ts": 2.763399124145508, "price": 148.98, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 2.764815092086792, "bid": 148.98, "ask": 149.03, "bid_size": 500, "ask_size": 100}, {"type": "trade", "ts": 2.8172671794891357, "price": 149.005, "size": 4, "side": "unknown"}, {"type": "quote", "ts": 2.869739055633545, "bid": 148.98, "ask": 149.03, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 2.9494340419769287, "bid": 148.98, "ask": 149.03, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 2.9497451782226562, "bid": 148.98, "ask": 149.03, "bid_size": 300, "ask_size": 100}, {"type": "trade", "ts": 2.9497859477996826, "price": 149.005, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 2.951158046722412, "bid": 148.98, "ask": 149.03, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 3.117690086364746, "bid": 148.98, "ask": 149.04, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 3.124847173690796, "bid": 148.98, "ask": 149.04, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 3.125408172607422, "bid": 148.98, "ask": 149.04, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 3.2746331691741943, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "trade", "ts": 3.3808679580688477, "price": 149.01, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 3.4243040084838867, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 3.4243900775909424, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "trade", "ts": 3.936840057373047, "price": 148.9965, "size": 3, "side": "unknown"}, {"type": "trade", "ts": 3.9432060718536377, "price": 148.9965, "size": 7, "side": "unknown"}, {"type": "trade", "ts": 4.104582071304321, "price": 149.0315, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 4.580170154571533, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 4.580355167388916, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 4.580816984176636, "bid": 148.98, "ask": 149.04, "bid_size": 600, "ask_size": 200}, {"type": "quote", "ts": 4.581187009811401, "bid": 148.99, "ask": 149.04, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 4.581619024276733, "bid": 148.99, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 4.581714153289795, "bid": 148.99, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 4.58199405670166, "bid": 148.99, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "trade", "ts": 4.673951148986816, "price": 149.0, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 4.683228015899658, "price": 149.0, "size": 15, "side": "unknown"}, {"type": "quote", "ts": 4.6832451820373535, "bid": 149.0, "ask": 149.04, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 4.683727025985718, "bid": 149.0, "ask": 149.04, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 4.684288024902344, "bid": 148.99, "ask": 149.04, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 4.6843931674957275, "bid": 148.99, "ask": 149.04, "bid_size": 500, "ask_size": 400}, {"type": "quote", "ts": 4.684604167938232, "bid": 148.99, "ask": 149.04, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 4.694556951522827, "bid": 148.99, "ask": 149.04, "bid_size": 500, "ask_size": 400}, {"type": "quote", "ts": 4.891491174697876, "bid": 148.99, "ask": 149.04, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 5.01831316947937, "bid": 148.99, "ask": 149.04, "bid_size": 300, "ask_size": 400}, {"type": "quote", "ts": 5.767837047576904, "bid": 148.99, "ask": 149.04, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 5.768197059631348, "bid": 148.99, "ask": 149.04, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 5.828346014022827, "bid": 148.99, "ask": 149.04, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 6.245233058929443, "bid": 148.99, "ask": 149.04, "bid_size": 500, "ask_size": 100}, {"type": "trade", "ts": 6.462010145187378, "price": 148.9657, "size": 4, "side": "unknown"}, {"type": "quote", "ts": 6.511547088623047, "bid": 148.99, "ask": 149.04, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 6.604523181915283, "bid": 148.99, "ask": 149.04, "bid_size": 400, "ask_size": 600}, {"type": "trade", "ts": 6.691910028457642, "price": 149.0329, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 6.868601083755493, "bid": 148.99, "ask": 149.04, "bid_size": 400, "ask_size": 100}, {"type": "trade", "ts": 7.0340399742126465, "price": 148.9997, "size": 3, "side": "unknown"}, {"type": "quote", "ts": 7.95415997505188, "bid": 148.99, "ask": 149.04, "bid_size": 400, "ask_size": 100}, {"type": "trade", "ts": 7.954161167144775, "price": 149.0, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 7.954344987869263, "bid": 148.99, "ask": 149.03, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 7.954836130142212, "bid": 148.99, "ask": 149.03, "bid_size": 400, "ask_size": 500}, {"type": "quote", "ts": 7.95623517036438, "bid": 148.99, "ask": 149.03, "bid_size": 400, "ask_size": 100}, {"type": "trade", "ts": 7.999142169952393, "price": 149.0, "size": 94, "side": "unknown"}, {"type": "trade", "ts": 7.999243974685669, "price": 149.01, "size": 17, "side": "unknown"}, {"type": "trade", "ts": 7.9994730949401855, "price": 149.01, "size": 14, "side": "unknown"}, {"type": "quote", "ts": 7.999868154525757, "bid": 148.99, "ask": 149.03, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 7.999928951263428, "bid": 148.99, "ask": 149.04, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 8.002009153366089, "bid": 148.99, "ask": 149.04, "bid_size": 400, "ask_size": 200}, {"type": "trade", "ts": 8.01658010482788, "price": 149.0495, "size": 2, "side": "unknown"}, {"type": "quote", "ts": 8.123372077941895, "bid": 148.99, "ask": 149.03, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 8.123979091644287, "bid": 148.99, "ask": 149.03, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 8.124906063079834, "bid": 148.99, "ask": 149.03, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 8.12610411643982, "bid": 148.99, "ask": 149.04, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 8.146016120910645, "bid": 148.99, "ask": 149.04, "bid_size": 400, "ask_size": 200}, {"type": "trade", "ts": 8.541885137557983, "price": 149.02, "size": 9, "side": "unknown"}, {"type": "quote", "ts": 8.684553146362305, "bid": 148.99, "ask": 149.03, "bid_size": 400, "ask_size": 500}, {"type": "trade", "ts": 8.684677124023438, "price": 148.99, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 8.684683084487915, "price": 148.99, "size": 27, "side": "unknown"}, {"type": "trade", "ts": 8.684689044952393, "price": 148.99, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 8.68476915359497, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 500}, {"type": "trade", "ts": 8.684771060943604, "price": 148.99, "size": 400, "side": "unknown"}, {"type": "trade", "ts": 8.684771060943604, "price": 148.99, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 8.684774160385132, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 500}, {"type": "trade", "ts": 8.684777021408081, "price": 148.99, "size": 4, "side": "unknown"}, {"type": "trade", "ts": 8.684777021408081, "price": 148.99, "size": 50, "side": "unknown"}, {"type": "quote", "ts": 8.684789180755615, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 8.684792041778564, "price": 148.99, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 8.684792041778564, "price": 148.99, "size": 97, "side": "unknown"}, {"type": "trade", "ts": 8.684795141220093, "price": 148.99, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 8.684798955917358, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 8.68480396270752, "price": 148.99, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 8.684813976287842, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 8.684828042984009, "price": 148.99, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 8.684844017028809, "bid": 148.98, "ask": 149.01, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 8.684844017028809, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 300}, {"type": "trade", "ts": 8.684885025024414, "price": 148.99, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 8.68489408493042, "bid": 148.98, "ask": 149.01, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 8.68493914604187, "bid": 148.98, "ask": 149.01, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 8.684944152832031, "bid": 148.98, "ask": 149.01, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 8.684945106506348, "price": 148.99, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 8.684954166412354, "price": 148.99, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 8.68502402305603, "bid": 148.98, "ask": 149.01, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 8.685029029846191, "bid": 148.98, "ask": 149.01, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 8.685049057006836, "bid": 148.98, "ask": 149.01, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 8.685054063796997, "bid": 148.98, "ask": 149.0, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 8.685129165649414, "bid": 148.98, "ask": 149.0, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 8.685213088989258, "price": 148.99, "size": 94, "side": "unknown"}, {"type": "quote", "ts": 8.685490131378174, "bid": 148.98, "ask": 149.0, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 8.685525178909302, "bid": 148.98, "ask": 149.0, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 8.685811042785645, "bid": 148.98, "ask": 149.0, "bid_size": 600, "ask_size": 100}, {"type": "quote", "ts": 8.685826063156128, "bid": 148.98, "ask": 149.0, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 8.686102151870728, "bid": 148.98, "ask": 149.0, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 8.686450958251953, "price": 148.99, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 8.691374063491821, "bid": 148.98, "ask": 149.0, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 8.720417022705078, "price": 149.0, "size": 57, "side": "unknown"}, {"type": "trade", "ts": 8.720424175262451, "price": 149.0, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 8.720673084259033, "price": 149.0, "size": 25, "side": "unknown"}, {"type": "trade", "ts": 8.720673084259033, "price": 149.0, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 8.72067403793335, "bid": 148.98, "ask": 149.01, "bid_size": 100, "ask_size": 400}, {"type": "trade", "ts": 8.720685005187988, "price": 149.0, "size": 16, "side": "unknown"}, {"type": "quote", "ts": 8.720694065093994, "bid": 148.99, "ask": 149.01, "bid_size": 100, "ask_size": 400}, {"type": "trade", "ts": 8.72097110748291, "price": 149.0, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 8.721065044403076, "bid": 148.99, "ask": 149.03, "bid_size": 100, "ask_size": 900}, {"type": "quote", "ts": 8.721179962158203, "bid": 148.99, "ask": 149.03, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 8.721250057220459, "bid": 148.98, "ask": 149.03, "bid_size": 300, "ask_size": 500}, {"type": "quote", "ts": 8.72130012512207, "bid": 148.98, "ask": 149.03, "bid_size": 400, "ask_size": 500}, {"type": "quote", "ts": 8.721315145492554, "bid": 148.98, "ask": 149.02, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 8.721366167068481, "bid": 148.98, "ask": 149.03, "bid_size": 400, "ask_size": 500}, {"type": "quote", "ts": 8.721390962600708, "bid": 148.98, "ask": 149.03, "bid_size": 600, "ask_size": 500}, {"type": "quote", "ts": 8.721390962600708, "bid": 148.98, "ask": 149.03, "bid_size": 700, "ask_size": 500}, {"type": "quote", "ts": 8.721476078033447, "bid": 148.98, "ask": 149.04, "bid_size": 600, "ask_size": 500}, {"type": "quote", "ts": 8.72148609161377, "bid": 148.98, "ask": 149.04, "bid_size": 400, "ask_size": 500}, {"type": "quote", "ts": 8.721827030181885, "bid": 148.98, "ask": 149.04, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 8.722689151763916, "bid": 148.98, "ask": 149.03, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 8.722723960876465, "bid": 148.98, "ask": 149.03, "bid_size": 400, "ask_size": 500}, {"type": "trade", "ts": 8.722975969314575, "price": 149.0, "size": 166, "side": "unknown"}, {"type": "quote", "ts": 8.722984075546265, "bid": 148.98, "ask": 149.03, "bid_size": 400, "ask_size": 100}, {"type": "trade", "ts": 8.723082065582275, "price": 149.0, "size": 33, "side": "unknown"}, {"type": "quote", "ts": 8.726317167282104, "bid": 148.99, "ask": 149.03, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 8.726793050765991, "price": 149.0, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 8.727856159210205, "bid": 148.99, "ask": 149.03, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 8.732607126235962, "bid": 148.99, "ask": 149.03, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 8.739293098449707, "bid": 148.99, "ask": 149.03, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 8.817348957061768, "bid": 148.99, "ask": 149.03, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 8.817398071289062, "price": 149.01, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 8.844539165496826, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 8.845105171203613, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 8.845335960388184, "bid": 148.98, "ask": 149.03, "bid_size": 300, "ask_size": 100}, {"type": "trade", "ts": 8.851993083953857, "price": 149.005, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 8.859835147857666, "price": 149.005, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 8.86770510673523, "price": 149.005, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 8.873002052307129, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 8.873027086257935, "bid": 148.98, "ask": 149.03, "bid_size": 300, "ask_size": 100}, {"type": "trade", "ts": 8.87421202659607, "price": 149.005, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 8.874324083328247, "price": 149.005, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 8.875566005706787, "price": 149.005, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 8.87912917137146, "price": 149.005, "size": 91, "side": "unknown"}, {"type": "trade", "ts": 8.923635005950928, "price": 149.005, "size": 195, "side": "unknown"}, {"type": "quote", "ts": 8.953834056854248, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 9.058573007583618, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 300}, {"type": "quote", "ts": 9.479735136032104, "bid": 148.98, "ask": 149.03, "bid_size": 300, "ask_size": 400}, {"type": "quote", "ts": 9.480172157287598, "bid": 148.98, "ask": 149.03, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 9.48039197921753, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 400}, {"type": "quote", "ts": 9.4809730052948, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 9.483083009719849, "bid": 148.99, "ask": 149.04, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 9.66295599937439, "bid": 148.99, "ask": 149.04, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 10.067650079727173, "bid": 148.99, "ask": 149.04, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 10.067738056182861, "price": 149.015, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 10.067798137664795, "price": 149.015, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 10.068271160125732, "bid": 148.99, "ask": 149.04, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 10.06830096244812, "bid": 148.99, "ask": 149.04, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 10.077883958816528, "bid": 148.99, "ask": 149.04, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 10.09220814704895, "bid": 148.99, "ask": 149.03, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 10.09318995475769, "bid": 148.99, "ask": 149.04, "bid_size": 100, "ask_size": 400}, {"type": "trade", "ts": 10.212632179260254, "price": 149.015, "size": 37, "side": "unknown"}, {"type": "trade", "ts": 10.31099009513855, "price": 148.9679, "size": 7, "side": "unknown"}, {"type": "trade", "ts": 11.000723123550415, "price": 149.02, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 11.00136399269104, "price": 149.015, "size": 3, "side": "unknown"}, {"type": "trade", "ts": 11.004184007644653, "price": 149.02, "size": 24, "side": "unknown"}, {"type": "quote", "ts": 11.005265951156616, "bid": 148.98, "ask": 149.04, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 11.126153945922852, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 400}, {"type": "quote", "ts": 11.172147989273071, "bid": 148.98, "ask": 149.05, "bid_size": 300, "ask_size": 400}, {"type": "quote", "ts": 11.172484159469604, "bid": 148.99, "ask": 149.05, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 11.172654151916504, "bid": 148.99, "ask": 149.05, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 11.173120975494385, "bid": 148.99, "ask": 149.05, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 11.266167163848877, "bid": 148.98, "ask": 149.05, "bid_size": 300, "ask_size": 400}, {"type": "quote", "ts": 11.792484045028687, "bid": 148.98, "ask": 149.04, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 11.792840003967285, "bid": 148.98, "ask": 149.04, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 11.793522119522095, "bid": 148.98, "ask": 149.04, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 11.795676946640015, "bid": 148.98, "ask": 149.04, "bid_size": 200, "ask_size": 500}, {"type": "trade", "ts": 11.815323114395142, "price": 149.0488, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 11.852391958236694, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 11.853064060211182, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 11.853154182434082, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 11.85335898399353, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 11.853374004364014, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 11.854331970214844, "bid": 148.98, "ask": 149.04, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 11.875406980514526, "bid": 148.98, "ask": 149.04, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 12.19991397857666, "bid": 148.98, "ask": 149.04, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 12.219436168670654, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 12.24763298034668, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 12.247828006744385, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 12.318089962005615, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 12.318135023117065, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 12.318161010742188, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 600}, {"type": "trade", "ts": 12.384235143661499, "price": 149.005, "size": 10, "side": "unknown"}, {"type": "quote", "ts": 12.421151161193848, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 12.421241044998169, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 12.421471118927002, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 12.422168016433716, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 12.52657699584961, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 12.527383089065552, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 12.52743411064148, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 12.529348134994507, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 12.71950101852417, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 12.787362098693848, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 12.78800916671753, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 400}, {"type": "trade", "ts": 12.829646110534668, "price": 149.0479, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 12.840955018997192, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 800}, {"type": "quote", "ts": 13.019068956375122, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 13.020297050476074, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 13.086609125137329, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 13.486817121505737, "bid": 148.98, "ask": 149.03, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 13.613147974014282, "bid": 148.98, "ask": 149.02, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 13.613178014755249, "price": 148.99, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 13.61339807510376, "bid": 148.98, "ask": 149.02, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 13.61393404006958, "bid": 148.98, "ask": 149.02, "bid_size": 100, "ask_size": 400}, {"type": "trade", "ts": 13.620516061782837, "price": 149.0, "size": 3, "side": "unknown"}, {"type": "trade", "ts": 13.888024091720581, "price": 148.98, "size": 70, "side": "unknown"}, {"type": "quote", "ts": 13.88802695274353, "bid": 148.98, "ask": 149.02, "bid_size": 100, "ask_size": 400}, {"type": "trade", "ts": 13.88802695274353, "price": 148.98, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 13.888051986694336, "bid": 148.98, "ask": 149.01, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 13.888054132461548, "price": 148.98, "size": 5, "side": "unknown"}, {"type": "trade", "ts": 13.888081073760986, "price": 148.98, "size": 25, "side": "unknown"}, {"type": "quote", "ts": 13.888092041015625, "bid": 148.98, "ask": 149.01, "bid_size": 100, "ask_size": 300}, {"type": "trade", "ts": 13.888102054595947, "price": 148.98, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 13.888102054595947, "price": 148.98, "size": 33, "side": "unknown"}, {"type": "trade", "ts": 13.888111114501953, "price": 148.98, "size": 55, "side": "unknown"}, {"type": "quote", "ts": 13.88811206817627, "bid": 148.97, "ask": 149.01, "bid_size": 100, "ask_size": 300}, {"type": "trade", "ts": 13.888113975524902, "price": 148.98, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 13.88811707496643, "bid": 148.97, "ask": 148.99, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 13.888132095336914, "bid": 148.97, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 13.888147115707397, "bid": 148.97, "ask": 148.99, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 13.88815712928772, "bid": 148.97, "ask": 148.99, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 13.888167142868042, "bid": 148.97, "ask": 148.99, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 13.888172149658203, "bid": 148.97, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 13.888174057006836, "price": 148.98, "size": 43, "side": "unknown"}, {"type": "quote", "ts": 13.888192176818848, "bid": 148.97, "ask": 148.99, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 13.88820195198059, "bid": 148.97, "ask": 148.98, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 13.888336181640625, "price": 148.98, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 13.888373136520386, "bid": 148.96, "ask": 148.98, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 13.888583183288574, "bid": 148.96, "ask": 148.98, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 13.888676166534424, "price": 148.98, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 13.888678073883057, "bid": 148.96, "ask": 148.98, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 13.888679027557373, "price": 148.98, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 13.888762950897217, "bid": 148.96, "ask": 148.98, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 13.888762950897217, "price": 148.98, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 13.888766050338745, "price": 148.98, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 13.888767957687378, "bid": 148.96, "ask": 148.99, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 13.888772964477539, "bid": 148.96, "ask": 148.99, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 13.888803958892822, "bid": 148.97, "ask": 148.99, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 13.888833999633789, "bid": 148.97, "ask": 148.99, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 13.888844013214111, "bid": 148.97, "ask": 148.99, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 13.8888840675354, "bid": 148.97, "ask": 148.99, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 13.888944149017334, "bid": 148.97, "ask": 148.99, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 13.889084100723267, "bid": 148.97, "ask": 148.99, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 13.889163970947266, "bid": 148.97, "ask": 148.99, "bid_size": 100, "ask_size": 600}, {"type": "trade", "ts": 13.889230012893677, "price": 148.99, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 13.889233112335205, "price": 148.99, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 13.889235019683838, "bid": 148.96, "ask": 148.99, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 13.889255046844482, "bid": 148.97, "ask": 148.99, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 13.889255046844482, "bid": 148.97, "ask": 148.99, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 13.889265060424805, "bid": 148.97, "ask": 148.99, "bid_size": 300, "ask_size": 600}, {"type": "quote", "ts": 13.889445066452026, "bid": 148.97, "ask": 148.99, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 13.889525175094604, "bid": 148.97, "ask": 148.99, "bid_size": 300, "ask_size": 600}, {"type": "quote", "ts": 13.889636039733887, "bid": 148.97, "ask": 149.0, "bid_size": 300, "ask_size": 600}, {"type": "quote", "ts": 13.889806032180786, "bid": 148.97, "ask": 149.0, "bid_size": 200, "ask_size": 600}, {"type": "trade", "ts": 13.889831066131592, "price": 148.98, "size": 5, "side": "unknown"}, {"type": "trade", "ts": 13.88983416557312, "price": 148.98, "size": 10, "side": "unknown"}, {"type": "quote", "ts": 13.889836072921753, "bid": 148.97, "ask": 149.0, "bid_size": 100, "ask_size": 600}, {"type": "trade", "ts": 13.88983702659607, "price": 148.98, "size": 10, "side": "unknown"}, {"type": "trade", "ts": 13.88983702659607, "price": 148.98, "size": 25, "side": "unknown"}, {"type": "quote", "ts": 13.889841079711914, "bid": 148.97, "ask": 149.0, "bid_size": 500, "ask_size": 600}, {"type": "quote", "ts": 13.88986611366272, "bid": 148.97, "ask": 149.0, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 13.889925956726074, "bid": 148.96, "ask": 149.0, "bid_size": 500, "ask_size": 600}, {"type": "quote", "ts": 13.889935970306396, "bid": 148.96, "ask": 149.0, "bid_size": 500, "ask_size": 300}, {"type": "quote", "ts": 13.890522956848145, "bid": 148.96, "ask": 149.0, "bid_size": 500, "ask_size": 500}, {"type": "trade", "ts": 13.891533136367798, "price": 148.98, "size": 120, "side": "unknown"}, {"type": "trade", "ts": 13.908576965332031, "price": 148.98, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 14.019129037857056, "bid": 148.96, "ask": 149.0, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.0191490650177, "bid": 148.96, "ask": 149.0, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 14.022037982940674, "price": 148.98, "size": 10, "side": "unknown"}, {"type": "trade", "ts": 14.031423091888428, "price": 149.0, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 14.050563097000122, "bid": 148.96, "ask": 149.0, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 14.051536083221436, "bid": 148.96, "ask": 149.0, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 14.066020011901855, "bid": 148.96, "ask": 149.0, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 14.092242956161499, "bid": 148.96, "ask": 149.0, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 14.092242956161499, "price": 148.97, "size": 69, "side": "unknown"}, {"type": "quote", "ts": 14.092278003692627, "bid": 148.96, "ask": 148.99, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 14.09381103515625, "bid": 148.96, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 14.094428062438965, "bid": 148.96, "ask": 148.99, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 14.094999074935913, "bid": 148.96, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 14.095875978469849, "bid": 148.96, "ask": 148.99, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 14.098437070846558, "bid": 148.96, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.108657121658325, "bid": 148.96, "ask": 148.98, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 14.11330795288086, "bid": 148.96, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.119930028915405, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.128950119018555, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.131325960159302, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.131345987319946, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.135857105255127, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 14.179360151290894, "price": 148.955, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 14.179380178451538, "bid": 148.93, "ask": 148.98, "bid_size": 200, "ask_size": 500}, {"type": "trade", "ts": 14.179425954818726, "price": 148.97, "size": 43, "side": "unknown"}, {"type": "trade", "ts": 14.179429054260254, "price": 148.97, "size": 13, "side": "unknown"}, {"type": "trade", "ts": 14.179433107376099, "price": 148.97, "size": 10, "side": "unknown"}, {"type": "trade", "ts": 14.179433107376099, "price": 148.97, "size": 25, "side": "unknown"}, {"type": "quote", "ts": 14.179465055465698, "bid": 148.94, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.179480075836182, "bid": 148.93, "ask": 148.98, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 14.179686069488525, "bid": 148.93, "ask": 148.98, "bid_size": 300, "ask_size": 500}, {"type": "quote", "ts": 14.179986953735352, "bid": 148.94, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.180176973342896, "bid": 148.93, "ask": 148.98, "bid_size": 600, "ask_size": 500}, {"type": "quote", "ts": 14.180217027664185, "bid": 148.93, "ask": 148.98, "bid_size": 700, "ask_size": 500}, {"type": "quote", "ts": 14.18047308921814, "bid": 148.93, "ask": 148.98, "bid_size": 600, "ask_size": 500}, {"type": "quote", "ts": 14.230266094207764, "bid": 148.93, "ask": 148.98, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 14.53134298324585, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 14.54006814956665, "price": 148.955, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 14.576821088790894, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.576881170272827, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.57708215713501, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.680217027664185, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 14.682422161102295, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.790729999542236, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 14.790740013122559, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 14.790760040283203, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 700}, {"type": "trade", "ts": 14.798266172409058, "price": 148.95, "size": 15, "side": "unknown"}, {"type": "quote", "ts": 14.812286138534546, "bid": 148.93, "ask": 148.97, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 14.812477111816406, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 14.835411071777344, "bid": 148.93, "ask": 148.97, "bid_size": 100, "ask_size": 600}, {"type": "trade", "ts": 15.010020971298218, "price": 148.95, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 15.010113954544067, "price": 148.95, "size": 14, "side": "unknown"}, {"type": "quote", "ts": 15.011505126953125, "bid": 148.93, "ask": 148.97, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 15.137601137161255, "bid": 148.93, "ask": 148.97, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 15.137616157531738, "bid": 148.93, "ask": 148.97, "bid_size": 100, "ask_size": 300}, {"type": "trade", "ts": 15.137669086456299, "price": 148.93, "size": 57, "side": "unknown"}, {"type": "quote", "ts": 15.137670993804932, "bid": 148.93, "ask": 148.95, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 15.137675046920776, "price": 148.93, "size": 5, "side": "unknown"}, {"type": "trade", "ts": 15.137678146362305, "price": 148.93, "size": 77, "side": "unknown"}, {"type": "trade", "ts": 15.137684106826782, "price": 148.93, "size": 88, "side": "unknown"}, {"type": "quote", "ts": 15.137686014175415, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 15.137691020965576, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.137701034545898, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 15.137714147567749, "price": 148.93, "size": 12, "side": "unknown"}, {"type": "quote", "ts": 15.137716054916382, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.137761116027832, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.137845993041992, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 15.137931108474731, "bid": 148.9, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 15.137938976287842, "price": 148.935, "size": 50, "side": "unknown"}, {"type": "quote", "ts": 15.137961149215698, "bid": 148.9, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 15.137963056564331, "price": 148.93, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 15.13796615600586, "price": 148.94, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 15.13802194595337, "bid": 148.92, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 15.138122081756592, "bid": 148.92, "ask": 148.94, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 15.138221979141235, "bid": 148.92, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 15.138221979141235, "price": 148.93, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 15.138221979141235, "price": 148.93, "size": 25, "side": "unknown"}, {"type": "quote", "ts": 15.138297080993652, "bid": 148.92, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.13856315612793, "bid": 148.92, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.13856816291809, "bid": 148.92, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.13856816291809, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.138718128204346, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 15.138723134994507, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 15.138787984848022, "bid": 148.9, "ask": 148.94, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 15.138828039169312, "bid": 148.9, "ask": 148.95, "bid_size": 400, "ask_size": 800}, {"type": "quote", "ts": 15.138904094696045, "bid": 148.92, "ask": 148.95, "bid_size": 400, "ask_size": 800}, {"type": "quote", "ts": 15.138914108276367, "bid": 148.92, "ask": 148.95, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 15.138949155807495, "bid": 148.9, "ask": 148.95, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 15.139660120010376, "bid": 148.9, "ask": 148.95, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 15.14260196685791, "bid": 148.9, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 15.142709016799927, "price": 148.92, "size": 200, "side": "unknown"}, {"type": "quote", "ts": 15.144106149673462, "bid": 148.9, "ask": 148.94, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 15.145194053649902, "bid": 148.89, "ask": 148.94, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 15.14833116531372, "bid": 148.89, "ask": 148.93, "bid_size": 400, "ask_size": 100}, {"type": "trade", "ts": 15.148380041122437, "price": 148.91, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 15.148966073989868, "price": 148.91, "size": 5, "side": "unknown"}, {"type": "quote", "ts": 15.148972988128662, "bid": 148.89, "ask": 148.93, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 15.149208068847656, "bid": 148.89, "ask": 148.93, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 15.149424076080322, "bid": 148.89, "ask": 148.94, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 15.149930000305176, "bid": 148.89, "ask": 148.94, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 15.150084972381592, "bid": 148.89, "ask": 148.94, "bid_size": 300, "ask_size": 600}, {"type": "quote", "ts": 15.158766031265259, "bid": 148.89, "ask": 148.94, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 15.158866167068481, "bid": 148.89, "ask": 148.94, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 15.159067153930664, "bid": 148.89, "ask": 148.94, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 15.159157037734985, "bid": 148.89, "ask": 148.94, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 15.187834978103638, "bid": 148.89, "ask": 148.94, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 15.188507080078125, "bid": 148.89, "ask": 148.95, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 15.189223051071167, "bid": 148.89, "ask": 148.95, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 15.20122218132019, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.201246976852417, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 15.201632976531982, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 15.221089124679565, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 15.251010179519653, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.25127100944519, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.33823299407959, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.340834140777588, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.341104984283447, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.341130018234253, "bid": 148.87, "ask": 148.94, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 15.34147596359253, "bid": 148.87, "ask": 148.94, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 15.341756105422974, "bid": 148.87, "ask": 148.94, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 15.518491983413696, "bid": 148.87, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.519253969192505, "bid": 148.87, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 15.569749116897583, "bid": 148.87, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 16.032235145568848, "bid": 148.87, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 16.136543035507202, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 16.154510974884033, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 16.1897189617157, "bid": 148.87, "ask": 148.93, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 16.189743995666504, "bid": 148.87, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 16.29885196685791, "price": 148.9, "size": 42, "side": "unknown"}, {"type": "trade", "ts": 16.347836017608643, "price": 148.9, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 16.348067045211792, "price": 148.9, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 16.348416090011597, "price": 148.9, "size": 38, "side": "unknown"}, {"type": "quote", "ts": 16.34938406944275, "bid": 148.87, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 16.791506052017212, "bid": 148.87, "ask": 148.93, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 16.907884120941162, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 16.924894094467163, "price": 148.9, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 17.53413414955139, "bid": 148.88, "ask": 148.93, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 17.827978134155273, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 17.947623014450073, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 17.94790506362915, "price": 148.9703, "size": 8, "side": "unknown"}, {"type": "trade", "ts": 17.947923183441162, "price": 148.9703, "size": 8, "side": "unknown"}, {"type": "quote", "ts": 17.947954177856445, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 17.9480881690979, "price": 148.9703, "size": 8, "side": "unknown"}, {"type": "quote", "ts": 17.974682092666626, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.009766101837158, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.021955013275146, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.02254605293274, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 18.048253059387207, "price": 149.0448, "size": 50, "side": "unknown"}, {"type": "quote", "ts": 18.074831008911133, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.081356048583984, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.1523699760437, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.210798978805542, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.410359144210815, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 18.41069507598877, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 18.410725116729736, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 18.410840034484863, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 18.41091012954712, "bid": 148.88, "ask": 148.95, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 18.411537170410156, "bid": 148.88, "ask": 148.95, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.41154718399048, "bid": 148.88, "ask": 148.95, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.411622047424316, "bid": 148.88, "ask": 148.95, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 18.423741102218628, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.42410707473755, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.43932795524597, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 18.439383029937744, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 18.448806047439575, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.81825017929077, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 18.832935094833374, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 19.012853145599365, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 19.013038158416748, "bid": 148.88, "ask": 148.94, "bid_size": 200, "ask_size": 500}, {"type": "trade", "ts": 19.01435112953186, "price": 148.9315, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 19.25095009803772, "bid": 148.88, "ask": 148.94, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 19.252689123153687, "bid": 148.88, "ask": 148.94, "bid_size": 200, "ask_size": 500}, {"type": "trade", "ts": 19.419255018234253, "price": 148.91, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 19.517637014389038, "price": 148.88, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 19.533671140670776, "price": 148.88, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 19.699525117874146, "price": 148.91, "size": 4, "side": "unknown"}, {"type": "quote", "ts": 19.721038103103638, "bid": 148.88, "ask": 148.94, "bid_size": 500, "ask_size": 500}, {"type": "quote", "ts": 19.724020957946777, "bid": 148.88, "ask": 148.94, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 20.21646809577942, "bid": 148.88, "ask": 148.93, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 20.216613054275513, "bid": 148.88, "ask": 148.93, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 20.48775815963745, "bid": 148.88, "ask": 148.92, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 20.48807406425476, "bid": 148.88, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 20.488770961761475, "bid": 148.88, "ask": 148.91, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 20.48961305618286, "bid": 148.88, "ask": 148.91, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 20.495376110076904, "bid": 148.88, "ask": 148.91, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 20.54291009902954, "bid": 148.88, "ask": 148.91, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 20.574615001678467, "bid": 148.88, "ask": 148.91, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 20.58033299446106, "bid": 148.88, "ask": 148.91, "bid_size": 200, "ask_size": 600}, {"type": "trade", "ts": 20.903200149536133, "price": 148.895, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 21.542888164520264, "price": 148.895, "size": 62, "side": "unknown"}, {"type": "quote", "ts": 21.549846172332764, "bid": 148.88, "ask": 148.91, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 21.823121070861816, "bid": 148.88, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 21.83304500579834, "bid": 148.88, "ask": 148.91, "bid_size": 200, "ask_size": 600}, {"type": "trade", "ts": 22.143535137176514, "price": 148.88, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 22.143619060516357, "bid": 148.88, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 22.143619060516357, "bid": 148.88, "ask": 148.91, "bid_size": 100, "ask_size": 600}, {"type": "trade", "ts": 22.143619060516357, "price": 148.88, "size": 200, "side": "unknown"}, {"type": "quote", "ts": 22.14362406730652, "bid": 148.87, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 22.143625020980835, "price": 148.88, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 22.143644094467163, "bid": 148.87, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 22.143649101257324, "bid": 148.87, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 22.143684148788452, "bid": 148.87, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 22.14415717124939, "price": 148.88, "size": 96, "side": "unknown"}, {"type": "quote", "ts": 22.144606113433838, "bid": 148.87, "ask": 148.89, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 22.145872116088867, "price": 148.88, "size": 5, "side": "unknown"}, {"type": "trade", "ts": 22.145872116088867, "price": 148.88, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 22.146085023880005, "price": 148.88, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 22.14610004425049, "bid": 148.87, "ask": 148.9, "bid_size": 100, "ask_size": 1100}, {"type": "trade", "ts": 22.146196126937866, "price": 148.88, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 22.14625310897827, "price": 148.88, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 22.146310091018677, "price": 148.88, "size": 50, "side": "unknown"}, {"type": "quote", "ts": 22.146566152572632, "bid": 148.87, "ask": 148.9, "bid_size": 100, "ask_size": 1000}, {"type": "quote", "ts": 22.146571159362793, "bid": 148.87, "ask": 148.9, "bid_size": 100, "ask_size": 600}, {"type": "trade", "ts": 22.149213075637817, "price": 148.885, "size": 58, "side": "unknown"}, {"type": "trade", "ts": 22.149230003356934, "price": 148.89, "size": 10, "side": "unknown"}, {"type": "trade", "ts": 22.149233102798462, "price": 148.89, "size": 10, "side": "unknown"}, {"type": "trade", "ts": 22.14923596382141, "price": 148.89, "size": 5, "side": "unknown"}, {"type": "trade", "ts": 22.14923906326294, "price": 148.89, "size": 4, "side": "unknown"}, {"type": "quote", "ts": 22.149858951568604, "bid": 148.87, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 22.149944067001343, "bid": 148.87, "ask": 148.9, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 22.150259971618652, "bid": 148.87, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 22.15029001235962, "bid": 148.87, "ask": 148.9, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 22.15069603919983, "bid": 148.87, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 22.151051998138428, "bid": 148.87, "ask": 148.9, "bid_size": 500, "ask_size": 100}, {"type": "trade", "ts": 22.151113033294678, "price": 148.885, "size": 56, "side": "unknown"}, {"type": "trade", "ts": 22.152655124664307, "price": 148.885, "size": 56, "side": "unknown"}, {"type": "quote", "ts": 22.15347695350647, "bid": 148.87, "ask": 148.91, "bid_size": 500, "ask_size": 500}, {"type": "trade", "ts": 22.1539089679718, "price": 148.89, "size": 56, "side": "unknown"}, {"type": "quote", "ts": 22.15443515777588, "bid": 148.87, "ask": 148.91, "bid_size": 500, "ask_size": 500}, {"type": "quote", "ts": 22.154515027999878, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 22.15461015701294, "bid": 148.87, "ask": 148.91, "bid_size": 600, "ask_size": 500}, {"type": "quote", "ts": 22.154710054397583, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 22.155131101608276, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 22.163691997528076, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 22.189270973205566, "price": 148.88, "size": 50, "side": "unknown"}, {"type": "quote", "ts": 22.203952074050903, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 22.21394109725952, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 22.21416711807251, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 22.21461796760559, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 22.53308606147766, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 22.542643070220947, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 22.543235063552856, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 22.54483914375305, "bid": 148.87, "ask": 148.92, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 22.577401161193848, "bid": 148.87, "ask": 148.92, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 22.577577114105225, "bid": 148.87, "ask": 148.92, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 22.57759714126587, "bid": 148.87, "ask": 148.92, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 22.57760715484619, "bid": 148.87, "ask": 148.92, "bid_size": 100, "ask_size": 400}, {"type": "trade", "ts": 22.57764506340027, "price": 148.89, "size": 50, "side": "unknown"}, {"type": "quote", "ts": 22.577666997909546, "bid": 148.87, "ask": 148.92, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 22.577707052230835, "bid": 148.87, "ask": 148.93, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 22.577742099761963, "bid": 148.87, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 22.57800817489624, "bid": 148.87, "ask": 148.93, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 22.578192949295044, "bid": 148.87, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 22.57821297645569, "bid": 148.87, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 22.578333139419556, "bid": 148.87, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 22.578444004058838, "bid": 148.87, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 22.57849907875061, "bid": 148.87, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 22.582208156585693, "bid": 148.87, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 22.8507821559906, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 22.851047039031982, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 22.85941195487976, "bid": 148.87, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 22.859718084335327, "bid": 148.87, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 23.70383095741272, "price": 148.9, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 23.731929063796997, "bid": 148.87, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 23.732124090194702, "bid": 148.87, "ask": 148.93, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 24.35943603515625, "price": 148.9, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 24.359552145004272, "bid": 148.87, "ask": 148.94, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 24.359718084335327, "bid": 148.87, "ask": 148.94, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 24.360931158065796, "bid": 148.87, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 24.593279123306274, "bid": 148.87, "ask": 148.94, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 24.593351125717163, "price": 148.9, "size": 38, "side": "unknown"}, {"type": "quote", "ts": 24.59338903427124, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 24.593424081802368, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 24.593503952026367, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 24.593537092208862, "price": 148.9, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 24.593613147735596, "price": 148.9, "size": 24, "side": "unknown"}, {"type": "quote", "ts": 24.59366011619568, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 24.593940019607544, "price": 148.9, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 24.594002962112427, "price": 148.9, "size": 38, "side": "unknown"}, {"type": "quote", "ts": 24.594030141830444, "bid": 148.88, "ask": 148.95, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 24.59406614303589, "bid": 148.88, "ask": 148.95, "bid_size": 200, "ask_size": 600}, {"type": "trade", "ts": 24.59407615661621, "price": 148.9, "size": 24, "side": "unknown"}, {"type": "quote", "ts": 24.5941960811615, "bid": 148.88, "ask": 148.95, "bid_size": 500, "ask_size": 600}, {"type": "trade", "ts": 24.594475984573364, "price": 148.9, "size": 38, "side": "unknown"}, {"type": "quote", "ts": 24.59451198577881, "bid": 148.88, "ask": 148.95, "bid_size": 200, "ask_size": 600}, {"type": "trade", "ts": 24.594527006149292, "price": 148.9, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 24.594545125961304, "price": 148.9, "size": 24, "side": "unknown"}, {"type": "quote", "ts": 24.59456205368042, "bid": 148.88, "ask": 148.95, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 24.594587087631226, "bid": 148.88, "ask": 148.95, "bid_size": 400, "ask_size": 700}, {"type": "quote", "ts": 24.594642162322998, "bid": 148.88, "ask": 148.95, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 24.59612011909485, "bid": 148.88, "ask": 148.94, "bid_size": 400, "ask_size": 200}, {"type": "trade", "ts": 24.60525608062744, "price": 148.91, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 24.605647087097168, "price": 148.91, "size": 28, "side": "unknown"}, {"type": "trade", "ts": 24.60593295097351, "price": 148.91, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 24.605939149856567, "price": 148.9, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 24.605972051620483, "price": 148.91, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 24.608323097229004, "price": 148.91, "size": 200, "side": "unknown"}, {"type": "trade", "ts": 24.608366012573242, "price": 148.91, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 24.60839009284973, "price": 148.91, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 24.60839295387268, "price": 148.91, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 24.60879611968994, "price": 148.91, "size": 37, "side": "unknown"}, {"type": "trade", "ts": 24.609373092651367, "price": 148.91, "size": 38, "side": "unknown"}, {"type": "quote", "ts": 24.61116600036621, "bid": 148.88, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 24.634729146957397, "price": 148.8799, "size": 141, "side": "unknown"}, {"type": "trade", "ts": 24.63890314102173, "price": 148.91, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 24.768646955490112, "price": 148.91, "size": 37, "side": "unknown"}, {"type": "trade", "ts": 24.76953101158142, "price": 148.91, "size": 37, "side": "unknown"}, {"type": "quote", "ts": 25.02342200279236, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 25.03064513206482, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 25.144878149032593, "price": 148.88, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 25.205870151519775, "price": 148.91, "size": 10, "side": "unknown"}, {"type": "quote", "ts": 25.28068995475769, "bid": 148.9, "ask": 148.94, "bid_size": 500, "ask_size": 200}, {"type": "trade", "ts": 25.286663055419922, "price": 148.92, "size": 40, "side": "unknown"}, {"type": "trade", "ts": 25.28924012184143, "price": 148.92, "size": 46, "side": "unknown"}, {"type": "quote", "ts": 25.290593147277832, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 25.30258011817932, "price": 148.92, "size": 200, "side": "unknown"}, {"type": "quote", "ts": 25.52979803085327, "bid": 148.88, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 25.529852151870728, "price": 148.895, "size": 200, "side": "unknown"}, {"type": "trade", "ts": 25.529852151870728, "price": 148.91, "size": 120, "side": "unknown"}, {"type": "quote", "ts": 25.529853105545044, "bid": 148.88, "ask": 148.91, "bid_size": 100, "ask_size": 400}, {"type": "trade", "ts": 25.529903173446655, "price": 148.91, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 25.52991509437561, "price": 148.895, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 25.529927015304565, "price": 148.91, "size": 424, "side": "unknown"}, {"type": "quote", "ts": 25.529927968978882, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 25.53001308441162, "bid": 148.9, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 25.53007411956787, "price": 148.92, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 25.530117988586426, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 25.53028917312622, "bid": 148.89, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 25.530313968658447, "bid": 148.88, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 25.53031897544861, "bid": 148.88, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 25.53036904335022, "bid": 148.9, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 25.530473947525024, "bid": 148.88, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 25.530488967895508, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 25.530490159988403, "price": 148.91, "size": 28, "side": "unknown"}, {"type": "quote", "ts": 25.53049397468567, "bid": 148.89, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 25.53050398826599, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 25.530508995056152, "bid": 148.9, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 25.53063416481018, "price": 148.91, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 25.530879974365234, "price": 148.9025, "size": 200, "side": "unknown"}, {"type": "quote", "ts": 25.53090500831604, "bid": 148.9, "ask": 148.94, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 25.531025171279907, "bid": 148.9, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 25.53114604949951, "bid": 148.9, "ask": 148.94, "bid_size": 600, "ask_size": 200}, {"type": "quote", "ts": 25.531346082687378, "bid": 148.9, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 25.533857107162476, "price": 148.91, "size": 200, "side": "unknown"}, {"type": "trade", "ts": 25.538350105285645, "price": 148.91, "size": 200, "side": "unknown"}, {"type": "trade", "ts": 25.541309118270874, "price": 148.92, "size": 132, "side": "unknown"}, {"type": "trade", "ts": 25.56588315963745, "price": 148.92, "size": 200, "side": "unknown"}, {"type": "trade", "ts": 25.568271160125732, "price": 148.92, "size": 9, "side": "unknown"}, {"type": "trade", "ts": 25.569504022598267, "price": 148.92, "size": 200, "side": "unknown"}, {"type": "trade", "ts": 25.571221113204956, "price": 148.92, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 25.628653049468994, "bid": 148.9, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 25.805192947387695, "bid": 148.9, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 25.80534315109253, "bid": 148.9, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 25.994322061538696, "price": 148.94, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 25.994397163391113, "price": 148.92, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 25.994397163391113, "price": 148.94, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 25.99440312385559, "price": 148.94, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 25.99447798728943, "bid": 148.9, "ask": 148.94, "bid_size": 400, "ask_size": 200}, {"type": "trade", "ts": 25.99471616744995, "price": 148.94, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 25.99472212791443, "price": 148.94, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 25.994734048843384, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 25.994879007339478, "bid": 148.91, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 25.994919061660767, "bid": 148.92, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 25.99525499343872, "bid": 148.91, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 25.99545407295227, "price": 148.94, "size": 14, "side": "unknown"}, {"type": "trade", "ts": 25.99545407295227, "price": 148.94, "size": 10, "side": "unknown"}, {"type": "quote", "ts": 25.995516061782837, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 25.996011972427368, "bid": 148.92, "ask": 148.94, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 26.19222402572632, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 26.19240403175354, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 26.19254207611084, "price": 148.93, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 26.192559957504272, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 26.192559957504272, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 26.192574977874756, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 26.19258999824524, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 26.19263505935669, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 26.193286180496216, "bid": 148.91, "ask": 148.94, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 26.19894504547119, "bid": 148.91, "ask": 148.94, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 26.199406147003174, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 26.449932098388672, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 26.66870403289795, "price": 148.925, "size": 3, "side": "unknown"}, {"type": "trade", "ts": 27.625954151153564, "price": 148.93, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 27.62649703025818, "bid": 148.91, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 27.626533031463623, "bid": 148.91, "ask": 148.94, "bid_size": 700, "ask_size": 200}, {"type": "quote", "ts": 27.626623153686523, "bid": 148.91, "ask": 148.94, "bid_size": 600, "ask_size": 200}, {"type": "trade", "ts": 27.633974075317383, "price": 148.925, "size": 38, "side": "unknown"}, {"type": "quote", "ts": 27.634592056274414, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 27.806182146072388, "price": 148.9358, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 27.846560955047607, "bid": 148.91, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 27.863168001174927, "price": 148.94, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 27.898487091064453, "price": 148.94, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 27.89937710762024, "price": 148.95, "size": 10, "side": "unknown"}, {"type": "trade", "ts": 27.8993980884552, "price": 148.95, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 27.8994460105896, "price": 148.94, "size": 216, "side": "unknown"}, {"type": "quote", "ts": 27.899446964263916, "bid": 148.91, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 27.899446964263916, "bid": 148.92, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 27.899449110031128, "price": 148.96, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 27.8994619846344, "bid": 148.92, "ask": 148.94, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 27.89946699142456, "bid": 148.93, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 27.899477005004883, "bid": 148.93, "ask": 148.96, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 27.899688005447388, "bid": 148.93, "ask": 148.96, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 27.899753093719482, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 600}, {"type": "trade", "ts": 27.899842977523804, "price": 148.95, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 27.899846076965332, "price": 148.96, "size": 5, "side": "unknown"}, {"type": "quote", "ts": 27.899988174438477, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 27.900012969970703, "bid": 148.93, "ask": 148.99, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 27.900022983551025, "price": 148.94, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 27.90010905265808, "bid": 148.93, "ask": 148.99, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 27.900114059448242, "bid": 148.93, "ask": 148.99, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 27.900119066238403, "bid": 148.93, "ask": 148.99, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 27.900134086608887, "bid": 148.93, "ask": 148.99, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 27.900139093399048, "bid": 148.93, "ask": 148.96, "bid_size": 500, "ask_size": 500}, {"type": "quote", "ts": 27.900174140930176, "bid": 148.93, "ask": 148.99, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 27.90022897720337, "bid": 148.93, "ask": 148.97, "bid_size": 500, "ask_size": 600}, {"type": "quote", "ts": 27.900269031524658, "bid": 148.93, "ask": 148.98, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 27.90064001083374, "bid": 148.93, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 27.902660131454468, "bid": 148.93, "ask": 148.99, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 27.907330989837646, "bid": 148.93, "ask": 148.99, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 27.93309211730957, "bid": 148.92, "ask": 148.99, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 27.9331271648407, "bid": 148.92, "ask": 148.99, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 27.933202028274536, "bid": 148.92, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 27.93372917175293, "bid": 148.92, "ask": 148.99, "bid_size": 700, "ask_size": 200}, {"type": "quote", "ts": 27.93380904197693, "bid": 148.92, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 27.935718059539795, "bid": 148.92, "ask": 148.98, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 27.94371199607849, "bid": 148.92, "ask": 148.98, "bid_size": 700, "ask_size": 100}, {"type": "quote", "ts": 27.99971103668213, "bid": 148.92, "ask": 148.99, "bid_size": 700, "ask_size": 200}, {"type": "quote", "ts": 28.212641954421997, "bid": 148.92, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 28.22414517402649, "bid": 148.92, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 28.22419500350952, "bid": 148.92, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 28.22423505783081, "bid": 148.92, "ask": 148.98, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 28.224440097808838, "bid": 148.91, "ask": 148.98, "bid_size": 600, "ask_size": 100}, {"type": "quote", "ts": 28.224931955337524, "bid": 148.91, "ask": 148.98, "bid_size": 500, "ask_size": 100}, {"type": "trade", "ts": 28.24257206916809, "price": 148.945, "size": 1000, "side": "unknown"}, {"type": "quote", "ts": 28.31740713119507, "bid": 148.92, "ask": 148.98, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 28.31759214401245, "bid": 148.92, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 28.318554162979126, "bid": 148.92, "ask": 148.99, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 28.319677114486694, "bid": 148.92, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 28.61167001724243, "price": 148.955, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 28.725268125534058, "bid": 148.92, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 28.725568056106567, "bid": 148.91, "ask": 148.99, "bid_size": 600, "ask_size": 200}, {"type": "quote", "ts": 28.72589898109436, "bid": 148.91, "ask": 148.99, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 28.797755002975464, "bid": 148.91, "ask": 148.98, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 28.875420093536377, "bid": 148.91, "ask": 148.99, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 29.092931985855103, "bid": 148.92, "ask": 148.99, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 29.092936992645264, "bid": 148.92, "ask": 148.98, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 29.093494176864624, "bid": 148.92, "ask": 148.98, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 29.094079971313477, "bid": 148.92, "ask": 148.98, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 29.117220163345337, "bid": 148.92, "ask": 148.98, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 29.178781986236572, "bid": 148.91, "ask": 148.98, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 29.205530166625977, "bid": 148.91, "ask": 148.99, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 29.324273109436035, "bid": 148.91, "ask": 148.97, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 29.327380180358887, "bid": 148.91, "ask": 148.97, "bid_size": 500, "ask_size": 700}, {"type": "quote", "ts": 29.327681064605713, "bid": 148.91, "ask": 148.97, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 29.42440104484558, "bid": 148.91, "ask": 148.97, "bid_size": 500, "ask_size": 200}, {"type": "trade", "ts": 29.424407958984375, "price": 148.92, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 29.424612045288086, "bid": 148.91, "ask": 148.95, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 29.424662113189697, "bid": 148.91, "ask": 148.97, "bid_size": 500, "ask_size": 200}, {"type": "trade", "ts": 29.42466402053833, "price": 148.95, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 29.42467713356018, "bid": 148.91, "ask": 148.96, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 29.424692153930664, "bid": 148.91, "ask": 148.96, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 29.42471218109131, "bid": 148.93, "ask": 148.96, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 29.424719095230103, "price": 148.94, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 29.424726963043213, "bid": 148.93, "ask": 148.96, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 29.424731969833374, "bid": 148.93, "ask": 148.96, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 29.42476201057434, "bid": 148.93, "ask": 148.96, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 29.4249370098114, "bid": 148.93, "ask": 148.96, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 29.424947023391724, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 29.425003051757812, "bid": 148.93, "ask": 148.97, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 29.425093173980713, "bid": 148.93, "ask": 148.97, "bid_size": 300, "ask_size": 700}, {"type": "quote", "ts": 29.425213098526, "bid": 148.93, "ask": 148.97, "bid_size": 300, "ask_size": 600}, {"type": "quote", "ts": 29.42525315284729, "bid": 148.93, "ask": 148.96, "bid_size": 300, "ask_size": 600}, {"type": "quote", "ts": 29.42525815963745, "bid": 148.93, "ask": 148.96, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 29.425454139709473, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 29.42548418045044, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 29.425774097442627, "bid": 148.93, "ask": 148.98, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 29.426416158676147, "bid": 148.93, "ask": 148.98, "bid_size": 500, "ask_size": 600}, {"type": "quote", "ts": 29.426932096481323, "bid": 148.93, "ask": 148.98, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 29.427008152008057, "bid": 148.93, "ask": 148.98, "bid_size": 500, "ask_size": 600}, {"type": "quote", "ts": 29.431813955307007, "bid": 148.93, "ask": 148.98, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 29.50182008743286, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 29.50258708000183, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 29.52707600593567, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 29.553115129470825, "price": 148.95, "size": 8, "side": "unknown"}, {"type": "quote", "ts": 29.847398042678833, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 29.87376117706299, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 29.89192509651184, "price": 148.9851, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 29.891978979110718, "price": 148.9804, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 29.89204216003418, "price": 148.9749, "size": 8, "side": "unknown"}, {"type": "trade", "ts": 29.897308111190796, "price": 148.9838, "size": 5, "side": "unknown"}, {"type": "quote", "ts": 29.926005125045776, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 29.93748712539673, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 29.940685033798218, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 30.000025987625122, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 30.315868139266968, "price": 148.97, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 30.506777048110962, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 30.535972118377686, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 30.752698183059692, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 30.753043174743652, "bid": 148.93, "ask": 148.98, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 30.75325918197632, "bid": 148.93, "ask": 148.98, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 30.75416612625122, "bid": 148.93, "ask": 148.98, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 30.754266023635864, "bid": 148.93, "ask": 148.98, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 30.76366901397705, "bid": 148.93, "ask": 148.98, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 30.764184951782227, "bid": 148.93, "ask": 148.98, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 31.237065076828003, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 31.237085103988647, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 31.237360954284668, "bid": 148.93, "ask": 148.97, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 31.24962615966797, "price": 148.93, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 31.249698162078857, "price": 148.93, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 31.24970006942749, "bid": 148.91, "ask": 148.97, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 31.249701023101807, "price": 148.93, "size": 200, "side": "unknown"}, {"type": "quote", "ts": 31.24970507621765, "bid": 148.91, "ask": 148.96, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 31.249720096588135, "bid": 148.91, "ask": 148.96, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 31.249755144119263, "bid": 148.91, "ask": 148.95, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 31.2497661113739, "bid": 148.91, "ask": 148.95, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 31.249961137771606, "bid": 148.91, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 31.249966144561768, "bid": 148.91, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 31.24997615814209, "bid": 148.91, "ask": 148.95, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 31.249986171722412, "bid": 148.91, "ask": 148.94, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 31.250030994415283, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 31.25030207633972, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 31.25033712387085, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 31.250367164611816, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 31.250482082366943, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 31.25069808959961, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 31.25091314315796, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 700}, {"type": "trade", "ts": 31.250916004180908, "price": 148.91, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 31.25095796585083, "bid": 148.91, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 31.25098204612732, "price": 148.91, "size": 76, "side": "unknown"}, {"type": "quote", "ts": 31.251033067703247, "bid": 148.91, "ask": 148.92, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 31.251080989837646, "price": 148.92, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 31.251084089279175, "bid": 148.91, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 31.25115394592285, "bid": 148.91, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 31.25151515007019, "bid": 148.91, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 31.25151515007019, "bid": 148.91, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 31.2516450881958, "bid": 148.91, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 31.25168514251709, "bid": 148.91, "ask": 148.93, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 31.251760005950928, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 800}, {"type": "quote", "ts": 31.251790046691895, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 31.251885175704956, "bid": 148.91, "ask": 148.93, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 31.252151012420654, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 400}, {"type": "trade", "ts": 31.305755138397217, "price": 148.93, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 31.305757999420166, "price": 148.93, "size": 51, "side": "unknown"}, {"type": "quote", "ts": 31.306074142456055, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 31.30632495880127, "bid": 148.91, "ask": 148.95, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 31.30646014213562, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 31.30650496482849, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 31.306535005569458, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 31.306666135787964, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 31.306705951690674, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 31.306720972061157, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 31.3072669506073, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 31.356845140457153, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 31.357226133346558, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 31.357782125473022, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 31.369425058364868, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 31.3999240398407, "price": 149.1566, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 31.558218955993652, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 31.558429956436157, "bid": 148.91, "ask": 148.97, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 31.558825969696045, "bid": 148.91, "ask": 148.97, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 31.55885100364685, "bid": 148.91, "ask": 148.97, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 31.55889105796814, "bid": 148.91, "ask": 148.97, "bid_size": 100, "ask_size": 700}, {"type": "trade", "ts": 31.704230070114136, "price": 148.913, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 31.739089012145996, "price": 148.94, "size": 5, "side": "unknown"}, {"type": "trade", "ts": 31.898516178131104, "price": 148.9701, "size": 4, "side": "unknown"}, {"type": "trade", "ts": 31.90364408493042, "price": 148.9462, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 31.90371012687683, "price": 148.983, "size": 2, "side": "unknown"}, {"type": "quote", "ts": 32.333850145339966, "bid": 148.91, "ask": 148.97, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 32.33387994766235, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 32.33456206321716, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 32.33459711074829, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 32.33503794670105, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 32.35200810432434, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 32.353471994400024, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 33.08902716636658, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 33.08902907371521, "price": 148.91, "size": 89, "side": "unknown"}, {"type": "trade", "ts": 33.0890531539917, "price": 148.91, "size": 11, "side": "unknown"}, {"type": "trade", "ts": 33.08914017677307, "price": 148.91, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 33.08918809890747, "bid": 148.91, "ask": 148.95, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 33.08924317359924, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 33.089648962020874, "bid": 148.91, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 33.08971405029297, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 33.08972406387329, "bid": 148.91, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 33.089784145355225, "bid": 148.91, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 33.0898220539093, "price": 148.91, "size": 199, "side": "unknown"}, {"type": "quote", "ts": 33.090054988861084, "bid": 148.91, "ask": 148.93, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 33.09017515182495, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 33.090381145477295, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 33.090681076049805, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 33.09165406227112, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 33.092350006103516, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 33.093528032302856, "bid": 148.9, "ask": 148.92, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 33.09358811378479, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 33.09409999847412, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 33.09415006637573, "bid": 148.9, "ask": 148.92, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 33.09417510032654, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 33.09972310066223, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 33.0999481678009, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 33.10508108139038, "price": 148.915, "size": 4, "side": "unknown"}, {"type": "trade", "ts": 33.107645988464355, "price": 148.915, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 33.13302707672119, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 33.13378405570984, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 33.16094899177551, "bid": 148.9, "ask": 148.93, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 33.19508504867554, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 33.19508504867554, "price": 148.9, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 33.195160150527954, "bid": 148.88, "ask": 148.92, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 33.19521999359131, "bid": 148.88, "ask": 148.92, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 33.19522500038147, "bid": 148.88, "ask": 148.92, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 33.19554114341736, "bid": 148.88, "ask": 148.92, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 33.19554615020752, "bid": 148.86, "ask": 148.92, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 33.19555616378784, "bid": 148.86, "ask": 148.92, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 33.19563603401184, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 33.19571113586426, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 33.19590711593628, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 33.196022033691406, "bid": 148.86, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 33.19729495048523, "bid": 148.86, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 33.19785499572754, "price": 148.88, "size": 7, "side": "unknown"}, {"type": "trade", "ts": 33.19785809516907, "price": 148.885, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 33.197957038879395, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 33.21090817451477, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 33.37890005111694, "price": 148.9, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 33.524327993392944, "bid": 148.86, "ask": 148.91, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 33.67934203147888, "bid": 148.86, "ask": 148.91, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 33.679672956466675, "bid": 148.86, "ask": 148.91, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 33.682114124298096, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 33.68326711654663, "price": 148.89, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 33.68422317504883, "price": 148.89, "size": 5, "side": "unknown"}, {"type": "trade", "ts": 33.68504095077515, "price": 148.89, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 33.68581700325012, "price": 148.89, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 33.686042070388794, "price": 148.89, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 33.68631601333618, "price": 148.89, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 33.686355113983154, "price": 148.9, "size": 28, "side": "unknown"}, {"type": "trade", "ts": 33.70354104042053, "price": 148.89, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 33.704034090042114, "price": 148.89, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 33.87983012199402, "price": 148.89, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 33.87993812561035, "price": 148.89, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 33.88000512123108, "bid": 148.87, "ask": 148.91, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 34.10528612136841, "bid": 148.86, "ask": 148.91, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 34.12086796760559, "bid": 148.86, "ask": 148.91, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 34.1240611076355, "bid": 148.86, "ask": 148.91, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 34.13037610054016, "bid": 148.86, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 34.130407094955444, "price": 148.88, "size": 81, "side": "unknown"}, {"type": "quote", "ts": 34.130431175231934, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 34.130431175231934, "bid": 148.86, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 34.13068604469299, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 34.130712032318115, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 34.13337802886963, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 34.133679151535034, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 34.15811204910278, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 34.15821409225464, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 34.15823197364807, "price": 148.86, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 34.1582350730896, "price": 148.86, "size": 80, "side": "unknown"}, {"type": "quote", "ts": 34.1582670211792, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 34.158267974853516, "price": 148.88, "size": 8, "side": "unknown"}, {"type": "trade", "ts": 34.15831017494202, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 34.1583890914917, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 34.15886902809143, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 34.15929698944092, "price": 148.88, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 34.1599280834198, "price": 148.88, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 34.167837142944336, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 34.175132036209106, "price": 148.86, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 34.17514109611511, "price": 148.86, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 34.17514395713806, "price": 148.86, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 34.17517113685608, "price": 148.86, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 34.17576718330383, "price": 148.86, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 34.1758029460907, "price": 148.86, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 34.17583894729614, "price": 148.86, "size": 36, "side": "unknown"}, {"type": "trade", "ts": 34.1783709526062, "price": 148.89, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 34.179177045822144, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 34.179404973983765, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "quote", "ts": 34.17942714691162, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 34.1794331073761, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.1795289516449, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.17955017089844, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.17961597442627, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.17972707748413, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.1798141002655, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.17989897727966, "price": 148.86, "size": 5, "side": "unknown"}, {"type": "trade", "ts": 34.18162798881531, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.182584047317505, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.183128118515015, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.18400001525879, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.18643307685852, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.18841195106506, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.20142412185669, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.205366134643555, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.218595027923584, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.22901511192322, "price": 148.86, "size": 19, "side": "unknown"}, {"type": "trade", "ts": 34.269368171691895, "price": 148.9992, "size": 5, "side": "unknown"}, {"type": "quote", "ts": 34.35260009765625, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 34.352625131607056, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 34.35675501823425, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 34.97986912727356, "price": 148.86, "size": 5, "side": "unknown"}, {"type": "quote", "ts": 35.25517797470093, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.29687714576721, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.30902099609375, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 35.4304039478302, "price": 148.8815, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 35.431477069854736, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.45543909072876, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.456912994384766, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.457679986953735, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.4577100276947, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 35.71978306770325, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.720375061035156, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.74243211746216, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 35.74371004104614, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 35.74699306488037, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 35.75100803375244, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 35.76516604423523, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 35.765191078186035, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.850720167160034, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 35.8513970375061, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 35.85564208030701, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.85623812675476, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.87390995025635, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 35.874502182006836, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 35.896389961242676, "price": 148.855, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 35.95210099220276, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 35.95305895805359, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 35.953258991241455, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 35.959028005599976, "bid": 148.82, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 35.95909810066223, "price": 148.855, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 35.95916295051575, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 35.95959401130676, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 35.95975399017334, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 400}, {"type": "trade", "ts": 35.96013617515564, "price": 148.85, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 35.96013808250427, "price": 148.85, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 35.96015000343323, "price": 148.85, "size": 38, "side": "unknown"}, {"type": "quote", "ts": 35.96017503738403, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 35.96020817756653, "price": 148.86, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 35.960214138031006, "price": 148.86, "size": 2, "side": "unknown"}, {"type": "quote", "ts": 35.96023607254028, "bid": 148.83, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 35.960241079330444, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 35.96025896072388, "price": 148.85, "size": 38, "side": "unknown"}, {"type": "quote", "ts": 35.96027112007141, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 35.96027112007141, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 35.96027612686157, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 35.96085214614868, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 35.96085214614868, "bid": 148.83, "ask": 148.88, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 35.96089696884155, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 35.961092948913574, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 35.9612979888916, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 35.96136808395386, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 35.97156810760498, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 35.98613214492798, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 500}, {"type": "trade", "ts": 35.98635506629944, "price": 148.855, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 35.98639798164368, "bid": 148.82, "ask": 148.89, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 35.98690915107727, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 35.98694396018982, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 35.999183177948, "bid": 148.82, "ask": 148.89, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 35.999850034713745, "bid": 148.82, "ask": 148.89, "bid_size": 100, "ask_size": 400}, {"type": "trade", "ts": 36.0009880065918, "price": 148.85, "size": 60, "side": "unknown"}, {"type": "quote", "ts": 36.003227949142456, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 36.01365804672241, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 36.015252113342285, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 36.019477128982544, "bid": 148.82, "ask": 148.89, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 36.0200080871582, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 36.02126097679138, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 36.021281003952026, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 36.021361112594604, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 36.021366119384766, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 400}, {"type": "trade", "ts": 36.02139711380005, "price": 148.85, "size": 4, "side": "unknown"}, {"type": "trade", "ts": 36.021399974823, "price": 148.85, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 36.02227807044983, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 36.02247405052185, "bid": 148.84, "ask": 148.87, "bid_size": 600, "ask_size": 500}, {"type": "quote", "ts": 36.02275896072388, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 36.02462410926819, "bid": 148.82, "ask": 148.87, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 36.02522015571594, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 36.02570104598999, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 36.02575206756592, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 36.0262131690979, "bid": 148.82, "ask": 148.87, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 36.02678418159485, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 36.026813983917236, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 36.02849817276001, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 36.06577205657959, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 36.20775508880615, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 36.29016613960266, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 36.346354961395264, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 36.346364974975586, "bid": 148.82, "ask": 148.87, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 36.346940994262695, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 36.347076177597046, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 36.347437143325806, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 36.367764949798584, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 36.411839962005615, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 36.56629300117493, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 36.59461998939514, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 36.7304790019989, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 36.819863080978394, "price": 149.1513, "size": 5, "side": "unknown"}, {"type": "quote", "ts": 36.82124996185303, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 36.85466408729553, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 36.904733180999756, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 36.90488409996033, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 37.01315116882324, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 37.01365804672241, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 37.01391315460205, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 37.014199018478394, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 37.01434898376465, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 37.01447510719299, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 37.014480113983154, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 37.0147750377655, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 37.23420715332031, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 37.234233140945435, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 37.23433303833008, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 37.23527002334595, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 37.23542499542236, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 600}, {"type": "trade", "ts": 37.23556709289551, "price": 148.8301, "size": 30, "side": "unknown"}, {"type": "quote", "ts": 37.235625982284546, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 37.406818151474, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 37.40777111053467, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 37.40798616409302, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 37.40806603431702, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 37.52021312713623, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 37.5243980884552, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 37.52447295188904, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 37.525020122528076, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 37.52508997917175, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 37.52564096450806, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 37.52849316596985, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 37.69611716270447, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 38.14200806617737, "price": 148.8443, "size": 31, "side": "unknown"}, {"type": "trade", "ts": 38.153347969055176, "price": 148.8443, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 38.709705114364624, "price": 148.966, "size": 45, "side": "unknown"}, {"type": "trade", "ts": 38.71064305305481, "price": 148.966, "size": 67, "side": "unknown"}, {"type": "trade", "ts": 38.71068501472473, "price": 148.966, "size": 44, "side": "unknown"}, {"type": "quote", "ts": 38.7959840297699, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 38.7961151599884, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 38.7963650226593, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 38.796661138534546, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 38.796741008758545, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 38.79690217971802, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 38.796972036361694, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 38.796972036361694, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 38.79700207710266, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 38.79711198806763, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 38.79713702201843, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 38.81616711616516, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 38.84432911872864, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 600}, {"type": "trade", "ts": 39.26886510848999, "price": 148.865, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 39.26930618286133, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 39.26945114135742, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 39.26948118209839, "bid": 148.84, "ask": 148.91, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 39.26979207992554, "bid": 148.84, "ask": 148.91, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 39.27005314826965, "bid": 148.84, "ask": 148.91, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 39.270097970962524, "bid": 148.84, "ask": 148.91, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 39.324684143066406, "price": 148.875, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 39.38341212272644, "bid": 148.84, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 39.38458514213562, "bid": 148.84, "ask": 148.92, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 39.384649991989136, "bid": 148.84, "ask": 148.92, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 39.38466501235962, "bid": 148.84, "ask": 148.92, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 39.38519215583801, "bid": 148.84, "ask": 148.92, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 39.506641149520874, "bid": 148.84, "ask": 148.92, "bid_size": 600, "ask_size": 500}, {"type": "quote", "ts": 39.50687599182129, "bid": 148.85, "ask": 148.92, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 39.53474307060242, "bid": 148.85, "ask": 148.92, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 39.534953117370605, "bid": 148.84, "ask": 148.92, "bid_size": 600, "ask_size": 500}, {"type": "quote", "ts": 39.54432511329651, "bid": 148.84, "ask": 148.92, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 39.568703174591064, "bid": 148.84, "ask": 148.92, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 39.832115173339844, "bid": 148.84, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 39.913654088974, "bid": 148.84, "ask": 148.91, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 39.91505813598633, "bid": 148.84, "ask": 148.91, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 39.91516304016113, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 39.91597008705139, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 39.91658115386963, "bid": 148.84, "ask": 148.91, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 39.97159695625305, "bid": 148.84, "ask": 148.91, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 40.03440713882446, "bid": 148.84, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.04361915588379, "bid": 148.85, "ask": 148.91, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.04557800292969, "bid": 148.85, "ask": 148.92, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 40.045714139938354, "bid": 148.85, "ask": 148.92, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 40.050971031188965, "bid": 148.83, "ask": 148.92, "bid_size": 200, "ask_size": 500}, {"type": "trade", "ts": 40.064733028411865, "price": 148.875, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 40.064733028411865, "price": 148.875, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 40.0648410320282, "price": 148.875, "size": 38, "side": "unknown"}, {"type": "quote", "ts": 40.064964056015015, "bid": 148.85, "ask": 148.92, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 40.06536507606506, "bid": 148.85, "ask": 148.92, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 40.06548094749451, "bid": 148.86, "ask": 148.92, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 40.06552600860596, "bid": 148.86, "ask": 148.92, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.06781601905823, "bid": 148.86, "ask": 148.92, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.07620596885681, "bid": 148.86, "ask": 148.92, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.086265087127686, "bid": 148.86, "ask": 148.93, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.08630013465881, "bid": 148.86, "ask": 148.92, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.08632516860962, "bid": 148.86, "ask": 148.93, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.086395025253296, "bid": 148.86, "ask": 148.93, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.08642506599426, "bid": 148.86, "ask": 148.93, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.0869619846344, "bid": 148.87, "ask": 148.93, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 40.08700203895569, "bid": 148.87, "ask": 148.93, "bid_size": 500, "ask_size": 500}, {"type": "quote", "ts": 40.08710217475891, "bid": 148.86, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 40.08748817443848, "bid": 148.86, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 40.09355902671814, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.09355902671814, "price": 148.87, "size": 36, "side": "unknown"}, {"type": "trade", "ts": 40.09358596801758, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.09358596801758, "price": 148.87, "size": 96, "side": "unknown"}, {"type": "trade", "ts": 40.09362006187439, "price": 148.87, "size": 114, "side": "unknown"}, {"type": "trade", "ts": 40.09363508224487, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.0936381816864, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.0936381816864, "price": 148.87, "size": 70, "side": "unknown"}, {"type": "trade", "ts": 40.09364104270935, "price": 148.87, "size": 70, "side": "unknown"}, {"type": "quote", "ts": 40.09364295005798, "bid": 148.86, "ask": 148.91, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 40.09364414215088, "price": 148.87, "size": 4, "side": "unknown"}, {"type": "trade", "ts": 40.093647956848145, "price": 148.87, "size": 25, "side": "unknown"}, {"type": "trade", "ts": 40.093647956848145, "price": 148.87, "size": 60, "side": "unknown"}, {"type": "trade", "ts": 40.0936541557312, "price": 148.87, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 40.0936541557312, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.093656063079834, "price": 148.87, "size": 70, "side": "unknown"}, {"type": "trade", "ts": 40.09365916252136, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.09365916252136, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.09366202354431, "price": 148.87, "size": 26, "side": "unknown"}, {"type": "trade", "ts": 40.09366202354431, "price": 148.87, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 40.09366512298584, "price": 148.87, "size": 54, "side": "unknown"}, {"type": "trade", "ts": 40.09366512298584, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.09367108345032, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.09367108345032, "price": 148.87, "size": 150, "side": "unknown"}, {"type": "trade", "ts": 40.093674182891846, "price": 148.87, "size": 70, "side": "unknown"}, {"type": "trade", "ts": 40.093674182891846, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.093674182891846, "price": 148.87, "size": 33, "side": "unknown"}, {"type": "trade", "ts": 40.093674182891846, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.093677043914795, "price": 148.87, "size": 58, "side": "unknown"}, {"type": "quote", "ts": 40.093688011169434, "bid": 148.86, "ask": 148.91, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.093698024749756, "bid": 148.86, "ask": 148.91, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.09370803833008, "bid": 148.86, "ask": 148.92, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09371304512024, "bid": 148.86, "ask": 148.92, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09372806549072, "bid": 148.86, "ask": 148.92, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.093738079071045, "bid": 148.84, "ask": 148.91, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.093738079071045, "bid": 148.84, "ask": 148.92, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.093738079071045, "bid": 148.85, "ask": 148.92, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09380316734314, "bid": 148.84, "ask": 148.92, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09385299682617, "bid": 148.84, "ask": 148.91, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.093929052352905, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 40.093932151794434, "price": 148.86, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 40.093932151794434, "price": 148.86, "size": 25, "side": "unknown"}, {"type": "quote", "ts": 40.09397315979004, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 40.09398698806763, "price": 148.87, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 40.09398913383484, "bid": 148.84, "ask": 148.91, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 40.093990087509155, "price": 148.87, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.093992948532104, "price": 148.87, "size": 12, "side": "unknown"}, {"type": "quote", "ts": 40.09399914741516, "bid": 148.83, "ask": 148.91, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09400916099548, "bid": 148.83, "ask": 148.91, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 40.09402012825012, "price": 148.86, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 40.09402298927307, "bid": 148.83, "ask": 148.91, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 40.0940260887146, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.0940260887146, "price": 148.86, "size": 9, "side": "unknown"}, {"type": "quote", "ts": 40.09402894973755, "bid": 148.84, "ask": 148.91, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09402894973755, "bid": 148.85, "ask": 148.91, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.094099044799805, "bid": 148.85, "ask": 148.91, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.094099044799805, "bid": 148.85, "ask": 148.91, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.094144105911255, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 40.09415817260742, "price": 148.87, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 40.094184160232544, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 40.09420609474182, "price": 148.87, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 40.09420895576477, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.09421396255493, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09426403045654, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.09434413909912, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09440517425537, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 40.09443807601929, "price": 148.86, "size": 3, "side": "unknown"}, {"type": "trade", "ts": 40.09443807601929, "price": 148.86, "size": 3, "side": "unknown"}, {"type": "quote", "ts": 40.094460010528564, "bid": 148.84, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.09447002410889, "bid": 148.84, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.094630002975464, "bid": 148.84, "ask": 148.88, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09470009803772, "bid": 148.84, "ask": 148.88, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09470009803772, "bid": 148.84, "ask": 148.88, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 40.095046043395996, "bid": 148.86, "ask": 148.88, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 40.09512114524841, "bid": 148.86, "ask": 148.88, "bid_size": 500, "ask_size": 300}, {"type": "quote", "ts": 40.09519600868225, "bid": 148.84, "ask": 148.88, "bid_size": 500, "ask_size": 300}, {"type": "quote", "ts": 40.09520602226257, "bid": 148.84, "ask": 148.88, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09520602226257, "bid": 148.84, "ask": 148.88, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 40.09551215171814, "bid": 148.84, "ask": 148.88, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09551215171814, "bid": 148.85, "ask": 148.88, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 40.0964241027832, "bid": 148.84, "ask": 148.88, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 40.096503019332886, "price": 148.87, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 40.09650707244873, "price": 148.87, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.09650707244873, "price": 148.87, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.09650897979736, "price": 148.87, "size": 3, "side": "unknown"}, {"type": "trade", "ts": 40.09650897979736, "price": 148.87, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 40.096534967422485, "bid": 148.84, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.096534967422485, "bid": 148.84, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.09653997421265, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 40.09654498100281, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 40.096665143966675, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09668016433716, "bid": 148.85, "ask": 148.88, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09668517112732, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.09671998023987, "bid": 148.85, "ask": 148.88, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 40.0967230796814, "price": 148.86, "size": 16, "side": "unknown"}, {"type": "trade", "ts": 40.0967230796814, "price": 148.86, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 40.096726179122925, "price": 148.85, "size": 8, "side": "unknown"}, {"type": "trade", "ts": 40.096729040145874, "price": 148.85, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.096729040145874, "price": 148.85, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 40.09672999382019, "bid": 148.84, "ask": 148.88, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 40.0967321395874, "price": 148.85, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.0967321395874, "price": 148.85, "size": 14, "side": "unknown"}, {"type": "trade", "ts": 40.09673500061035, "price": 148.85, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.09673500061035, "price": 148.85, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.09673500061035, "price": 148.85, "size": 87, "side": "unknown"}, {"type": "trade", "ts": 40.096750020980835, "price": 148.85, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 40.09677505493164, "bid": 148.85, "ask": 148.88, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 40.09679913520813, "price": 148.85, "size": 13, "side": "unknown"}, {"type": "quote", "ts": 40.096800088882446, "bid": 148.84, "ask": 148.88, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 40.09680104255676, "price": 148.85, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 40.09680509567261, "bid": 148.84, "ask": 148.87, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.09682011604309, "bid": 148.84, "ask": 148.86, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 40.09683418273926, "price": 148.85, "size": 69, "side": "unknown"}, {"type": "quote", "ts": 40.096835136413574, "bid": 148.84, "ask": 148.86, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.096840143203735, "bid": 148.84, "ask": 148.86, "bid_size": 400, "ask_size": 100}, {"type": "trade", "ts": 40.096858978271484, "price": 148.85, "size": 13, "side": "unknown"}, {"type": "trade", "ts": 40.096858978271484, "price": 148.85, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 40.09686517715454, "bid": 148.84, "ask": 148.86, "bid_size": 400, "ask_size": 200}, {"type": "trade", "ts": 40.0968701839447, "price": 148.85, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 40.09689116477966, "price": 148.86, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 40.09689998626709, "bid": 148.84, "ask": 148.85, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 40.09693002700806, "bid": 148.84, "ask": 148.85, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 40.09695100784302, "bid": 148.84, "ask": 148.85, "bid_size": 400, "ask_size": 100}, {"type": "trade", "ts": 40.09695100784302, "price": 148.85, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 40.09695506095886, "price": 148.85, "size": 4, "side": "unknown"}, {"type": "trade", "ts": 40.09696316719055, "price": 148.85, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 40.09697103500366, "bid": 148.84, "ask": 148.86, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 40.09701108932495, "bid": 148.84, "ask": 148.86, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 40.09701108932495, "bid": 148.84, "ask": 148.86, "bid_size": 400, "ask_size": 100}, {"type": "trade", "ts": 40.09702396392822, "price": 148.85, "size": 94, "side": "unknown"}, {"type": "quote", "ts": 40.097031116485596, "bid": 148.85, "ask": 148.86, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.097110986709595, "bid": 148.85, "ask": 148.86, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 40.09715914726257, "price": 148.85, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 40.09716796875, "price": 148.85, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 40.09718298912048, "price": 148.85, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 40.09718608856201, "price": 148.85, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.09718894958496, "price": 148.85, "size": 8, "side": "unknown"}, {"type": "trade", "ts": 40.09718894958496, "price": 148.85, "size": 4, "side": "unknown"}, {"type": "trade", "ts": 40.097193002700806, "price": 148.85, "size": 8, "side": "unknown"}, {"type": "trade", "ts": 40.09719800949097, "price": 148.85, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.09719800949097, "price": 148.85, "size": 22, "side": "unknown"}, {"type": "trade", "ts": 40.097201108932495, "price": 148.85, "size": 58, "side": "unknown"}, {"type": "quote", "ts": 40.09723615646362, "bid": 148.85, "ask": 148.86, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 40.09724402427673, "price": 148.85, "size": 16, "side": "unknown"}, {"type": "quote", "ts": 40.09738206863403, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.09746217727661, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 40.097517013549805, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.09767699241638, "bid": 148.85, "ask": 148.86, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 40.09770703315735, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.097777128219604, "bid": 148.85, "ask": 148.86, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 40.097793102264404, "bid": 148.85, "ask": 148.86, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 40.09782314300537, "bid": 148.85, "ask": 148.87, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 40.097843170166016, "bid": 148.85, "ask": 148.87, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 40.0978729724884, "bid": 148.85, "ask": 148.87, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 40.09791803359985, "bid": 148.85, "ask": 148.87, "bid_size": 400, "ask_size": 100}, {"type": "trade", "ts": 40.097939014434814, "price": 148.85, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 40.097941160202026, "price": 148.85, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 40.097944021224976, "price": 148.85, "size": 10, "side": "unknown"}, {"type": "trade", "ts": 40.097947120666504, "price": 148.85, "size": 5, "side": "unknown"}, {"type": "quote", "ts": 40.09816312789917, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.0981981754303, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 40.09823298454285, "price": 148.85, "size": 31, "side": "unknown"}, {"type": "quote", "ts": 40.09823417663574, "bid": 148.84, "ask": 148.87, "bid_size": 800, "ask_size": 200}, {"type": "trade", "ts": 40.09823799133301, "price": 148.85, "size": 10, "side": "unknown"}, {"type": "quote", "ts": 40.09829902648926, "bid": 148.84, "ask": 148.87, "bid_size": 800, "ask_size": 300}, {"type": "quote", "ts": 40.09833908081055, "bid": 148.84, "ask": 148.87, "bid_size": 800, "ask_size": 200}, {"type": "quote", "ts": 40.098418951034546, "bid": 148.84, "ask": 148.87, "bid_size": 800, "ask_size": 100}, {"type": "quote", "ts": 40.09856414794922, "bid": 148.84, "ask": 148.87, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 40.09856414794922, "bid": 148.84, "ask": 148.87, "bid_size": 800, "ask_size": 400}, {"type": "trade", "ts": 40.1009521484375, "price": 148.86, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 40.1009521484375, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.10095715522766, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.10096001625061, "price": 148.86, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 40.10099005699158, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 40.10116100311279, "bid": 148.85, "ask": 148.88, "bid_size": 100, "ask_size": 900}, {"type": "quote", "ts": 40.10122609138489, "bid": 148.85, "ask": 148.88, "bid_size": 200, "ask_size": 900}, {"type": "quote", "ts": 40.10150098800659, "bid": 148.85, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.10164213180542, "bid": 148.85, "ask": 148.88, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 40.102153062820435, "bid": 148.85, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 40.10231304168701, "price": 148.865, "size": 38, "side": "unknown"}, {"type": "trade", "ts": 40.10231900215149, "price": 148.87, "size": 13, "side": "unknown"}, {"type": "trade", "ts": 40.102571964263916, "price": 148.87, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 40.102571964263916, "price": 148.87, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.102571964263916, "price": 148.87, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 40.10257911682129, "bid": 148.85, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 40.10261416435242, "bid": 148.86, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.10262894630432, "bid": 148.86, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.10262894630432, "bid": 148.86, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.102648973464966, "bid": 148.86, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 40.10271716117859, "price": 148.86, "size": 33, "side": "unknown"}, {"type": "quote", "ts": 40.10271906852722, "bid": 148.86, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 40.10271906852722, "price": 148.86, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 40.1027250289917, "bid": 148.86, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.1027250289917, "bid": 148.86, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 40.102725982666016, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.102725982666016, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.102725982666016, "price": 148.86, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 40.10272812843323, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "quote", "ts": 40.102729082107544, "bid": 148.86, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 40.10273218154907, "price": 148.86, "size": 15, "side": "unknown"}, {"type": "trade", "ts": 40.10273218154907, "price": 148.86, "size": 18, "side": "unknown"}, {"type": "trade", "ts": 40.10273218154907, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 40.102734088897705, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.102734088897705, "bid": 148.86, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 40.102734088897705, "price": 148.86, "size": 25, "side": "unknown"}, {"type": "trade", "ts": 40.102734088897705, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 40.10280418395996, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.10284996032715, "bid": 148.86, "ask": 148.87, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.10284996032715, "bid": 148.84, "ask": 148.87, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 40.10297513008118, "bid": 148.86, "ask": 148.87, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.10297513008118, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 200}, {"type": "trade", "ts": 40.10297513008118, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 40.1029851436615, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 40.10299015045166, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 300}, {"type": "quote", "ts": 40.10301494598389, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 40.10302495956421, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 300}, {"type": "quote", "ts": 40.10312008857727, "bid": 148.85, "ask": 148.87, "bid_size": 600, "ask_size": 300}, {"type": "quote", "ts": 40.103190183639526, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 300}, {"type": "quote", "ts": 40.1032350063324, "bid": 148.86, "ask": 148.87, "bid_size": 400, "ask_size": 300}, {"type": "quote", "ts": 40.10329604148865, "bid": 148.86, "ask": 148.87, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 40.10330104827881, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 40.10335111618042, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 40.10340595245361, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 400}, {"type": "trade", "ts": 40.103410959243774, "price": 148.85, "size": 3, "side": "unknown"}, {"type": "quote", "ts": 40.10347104072571, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 200}, {"type": "trade", "ts": 40.1038031578064, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.1038031578064, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "quote", "ts": 40.10380697250366, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 100}, {"type": "trade", "ts": 40.10380816459656, "price": 148.86, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 40.10380816459656, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.10380816459656, "price": 148.86, "size": 33, "side": "unknown"}, {"type": "trade", "ts": 40.10382294654846, "price": 148.87, "size": 2, "side": "unknown"}, {"type": "quote", "ts": 40.10383200645447, "bid": 148.85, "ask": 148.88, "bid_size": 500, "ask_size": 400}, {"type": "trade", "ts": 40.10398507118225, "price": 148.85, "size": 4, "side": "unknown"}, {"type": "quote", "ts": 40.10400700569153, "bid": 148.85, "ask": 148.87, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 40.10402703285217, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 40.10407209396362, "bid": 148.85, "ask": 148.88, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 40.104143142700195, "bid": 148.85, "ask": 148.88, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 40.10445308685303, "bid": 148.85, "ask": 148.88, "bid_size": 600, "ask_size": 400}, {"type": "trade", "ts": 40.10465908050537, "price": 148.85, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 40.10524010658264, "bid": 148.85, "ask": 148.87, "bid_size": 600, "ask_size": 100}, {"type": "quote", "ts": 40.10526514053345, "bid": 148.85, "ask": 148.88, "bid_size": 600, "ask_size": 400}, {"type": "trade", "ts": 40.10526704788208, "price": 148.87, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.10526704788208, "price": 148.87, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 40.10527205467224, "price": 148.87, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.10527205467224, "price": 148.87, "size": 50, "side": "unknown"}, {"type": "trade", "ts": 40.10527515411377, "price": 148.87, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 40.105295181274414, "bid": 148.86, "ask": 148.88, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 40.10552096366882, "bid": 148.86, "ask": 148.88, "bid_size": 200, "ask_size": 400}, {"type": "trade", "ts": 40.105666160583496, "price": 148.86, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 40.105666160583496, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "quote", "ts": 40.10567116737366, "bid": 148.86, "ask": 148.88, "bid_size": 100, "ask_size": 400}, {"type": "trade", "ts": 40.105672121047974, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.105672121047974, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 40.10567498207092, "price": 148.86, "size": 15, "side": "unknown"}, {"type": "trade", "ts": 40.10567498207092, "price": 148.86, "size": 15, "side": "unknown"}, {"type": "quote", "ts": 40.105695962905884, "bid": 148.85, "ask": 148.88, "bid_size": 600, "ask_size": 400}, {"type": "trade", "ts": 40.10569715499878, "price": 148.86, "size": 25, "side": "unknown"}, {"type": "trade", "ts": 40.10569715499878, "price": 148.86, "size": 8, "side": "unknown"}, {"type": "quote", "ts": 40.10572099685669, "bid": 148.85, "ask": 148.87, "bid_size": 600, "ask_size": 100}, {"type": "quote", "ts": 40.105767011642456, "bid": 148.85, "ask": 148.87, "bid_size": 600, "ask_size": 200}, {"type": "quote", "ts": 40.10581707954407, "bid": 148.85, "ask": 148.87, "bid_size": 600, "ask_size": 400}, {"type": "quote", "ts": 40.105857133865356, "bid": 148.85, "ask": 148.87, "bid_size": 700, "ask_size": 400}, {"type": "quote", "ts": 40.10591197013855, "bid": 148.85, "ask": 148.87, "bid_size": 600, "ask_size": 200}, {"type": "quote", "ts": 40.10591197013855, "bid": 148.85, "ask": 148.87, "bid_size": 700, "ask_size": 200}, {"type": "quote", "ts": 40.10599207878113, "bid": 148.86, "ask": 148.87, "bid_size": 600, "ask_size": 200}, {"type": "quote", "ts": 40.10603213310242, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.106067180633545, "bid": 148.86, "ask": 148.87, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 40.10622811317444, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 40.106388092041016, "bid": 148.85, "ask": 148.87, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 40.10639309883118, "bid": 148.85, "ask": 148.87, "bid_size": 200, "ask_size": 500}, {"type": "trade", "ts": 40.10647511482239, "price": 148.87, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 40.10647511482239, "price": 148.87, "size": 12, "side": "unknown"}, {"type": "trade", "ts": 40.10647797584534, "price": 148.87, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 40.10647797584534, "price": 148.87, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 40.106508016586304, "bid": 148.86, "ask": 148.87, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 40.106749057769775, "bid": 148.86, "ask": 148.89, "bid_size": 100, "ask_size": 900}, {"type": "quote", "ts": 40.10704016685486, "bid": 148.86, "ask": 148.89, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 40.10714507102966, "bid": 148.86, "ask": 148.89, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 40.10730504989624, "bid": 148.87, "ask": 148.89, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 40.10735011100769, "bid": 148.86, "ask": 148.89, "bid_size": 400, "ask_size": 400}, {"type": "trade", "ts": 40.108721017837524, "price": 148.87, "size": 18, "side": "unknown"}, {"type": "trade", "ts": 40.111634969711304, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 40.118558168411255, "price": 148.875, "size": 49, "side": "unknown"}, {"type": "quote", "ts": 40.11868214607239, "bid": 148.86, "ask": 148.9, "bid_size": 400, "ask_size": 900}, {"type": "quote", "ts": 40.11892795562744, "bid": 148.86, "ask": 148.9, "bid_size": 400, "ask_size": 500}, {"type": "quote", "ts": 40.11900305747986, "bid": 148.86, "ask": 148.89, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 40.11900305747986, "bid": 148.86, "ask": 148.9, "bid_size": 400, "ask_size": 500}, {"type": "quote", "ts": 40.11913800239563, "bid": 148.86, "ask": 148.9, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 40.11919903755188, "bid": 148.86, "ask": 148.9, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 40.119469165802, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 40.119469165802, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 40.12004995346069, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 40.1200749874115, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 500}, {"type": "quote", "ts": 40.13201403617859, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 40.141993045806885, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 500}, {"type": "trade", "ts": 40.14208912849426, "price": 148.87, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 40.154502153396606, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 500}, {"type": "trade", "ts": 40.154824018478394, "price": 148.89, "size": 75, "side": "unknown"}, {"type": "quote", "ts": 40.16834497451782, "bid": 148.86, "ask": 148.91, "bid_size": 600, "ask_size": 500}, {"type": "trade", "ts": 40.16855216026306, "price": 148.88, "size": 3, "side": "unknown"}, {"type": "trade", "ts": 40.16855216026306, "price": 148.88, "size": 25, "side": "unknown"}, {"type": "trade", "ts": 40.168583154678345, "price": 148.88, "size": 38, "side": "unknown"}, {"type": "quote", "ts": 40.16918706893921, "bid": 148.86, "ask": 148.91, "bid_size": 700, "ask_size": 500}, {"type": "quote", "ts": 40.16920304298401, "bid": 148.86, "ask": 148.91, "bid_size": 700, "ask_size": 400}, {"type": "quote", "ts": 40.1692430973053, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.1692430973053, "bid": 148.86, "ask": 148.91, "bid_size": 700, "ask_size": 100}, {"type": "quote", "ts": 40.16969895362854, "bid": 148.86, "ask": 148.91, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 40.16987895965576, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 100}, {"type": "trade", "ts": 40.180039167404175, "price": 148.86, "size": 26, "side": "unknown"}, {"type": "quote", "ts": 40.196367025375366, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 100}, {"type": "quote", "ts": 40.19674301147461, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 40.19864797592163, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 40.19865298271179, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 700}, {"type": "quote", "ts": 40.199289083480835, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 600}, {"type": "quote", "ts": 40.22120118141174, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 40.22134208679199, "bid": 148.86, "ask": 148.91, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 40.22168207168579, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 40.24187517166138, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.248852014541626, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.24887704849243, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.249123096466064, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.5495879650116, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.552359104156494, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.729411125183105, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.80282497406006, "bid": 148.86, "ask": 148.91, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 40.860042095184326, "bid": 148.86, "ask": 148.92, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 41.05876612663269, "price": 148.89, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 41.096513986587524, "bid": 148.86, "ask": 148.92, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 41.096670150756836, "bid": 148.86, "ask": 148.92, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 41.243613958358765, "bid": 148.86, "ask": 148.91, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 41.27155613899231, "bid": 148.86, "ask": 148.91, "bid_size": 300, "ask_size": 600}, {"type": "quote", "ts": 41.27172112464905, "bid": 148.86, "ask": 148.91, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 41.27343511581421, "bid": 148.86, "ask": 148.92, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 41.27349495887756, "bid": 148.86, "ask": 148.91, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 41.27366614341736, "bid": 148.86, "ask": 148.92, "bid_size": 300, "ask_size": 200}, {"type": "trade", "ts": 41.27459001541138, "price": 148.87, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 41.324877977371216, "bid": 148.86, "ask": 148.92, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 41.32510805130005, "bid": 148.86, "ask": 148.92, "bid_size": 300, "ask_size": 500}, {"type": "quote", "ts": 41.60535502433777, "bid": 148.86, "ask": 148.91, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 41.6062171459198, "bid": 148.86, "ask": 148.91, "bid_size": 300, "ask_size": 500}, {"type": "quote", "ts": 41.607601165771484, "bid": 148.86, "ask": 148.91, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 41.608628034591675, "bid": 148.86, "ask": 148.91, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 41.643229961395264, "bid": 148.86, "ask": 148.91, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 41.64345097541809, "bid": 148.86, "ask": 148.92, "bid_size": 300, "ask_size": 600}, {"type": "quote", "ts": 41.64388704299927, "bid": 148.86, "ask": 148.92, "bid_size": 300, "ask_size": 500}, {"type": "quote", "ts": 41.654643058776855, "bid": 148.86, "ask": 148.92, "bid_size": 300, "ask_size": 200}, {"type": "trade", "ts": 41.86735796928406, "price": 148.89, "size": 22, "side": "unknown"}, {"type": "quote", "ts": 42.170390129089355, "bid": 148.86, "ask": 148.9, "bid_size": 300, "ask_size": 100}, {"type": "trade", "ts": 42.196046113967896, "price": 149.1426, "size": 5, "side": "unknown"}, {"type": "quote", "ts": 42.35332012176514, "bid": 148.86, "ask": 148.9, "bid_size": 300, "ask_size": 600}, {"type": "quote", "ts": 42.354273080825806, "bid": 148.86, "ask": 148.9, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 42.354933977127075, "bid": 148.86, "ask": 148.9, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 42.38372302055359, "bid": 148.86, "ask": 148.9, "bid_size": 300, "ask_size": 100}, {"type": "trade", "ts": 42.42188310623169, "price": 148.88, "size": 200, "side": "unknown"}, {"type": "trade", "ts": 43.41076302528381, "price": 148.87, "size": 15, "side": "unknown"}, {"type": "quote", "ts": 43.4107871055603, "bid": 148.86, "ask": 148.9, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 43.410802125930786, "bid": 148.86, "ask": 148.9, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 43.41081714630127, "bid": 148.86, "ask": 148.89, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 43.41084694862366, "bid": 148.86, "ask": 148.9, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 43.410876989364624, "bid": 148.86, "ask": 148.89, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 43.41145896911621, "bid": 148.86, "ask": 148.89, "bid_size": 300, "ask_size": 700}, {"type": "quote", "ts": 43.411519050598145, "bid": 148.86, "ask": 148.89, "bid_size": 300, "ask_size": 600}, {"type": "trade", "ts": 43.41161108016968, "price": 148.86, "size": 2, "side": "unknown"}, {"type": "quote", "ts": 43.41196012496948, "bid": 148.86, "ask": 148.89, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 43.41770815849304, "bid": 148.86, "ask": 148.89, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 43.41856002807617, "bid": 148.86, "ask": 148.89, "bid_size": 300, "ask_size": 700}, {"type": "trade", "ts": 43.703943967819214, "price": 148.86, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 43.703943967819214, "price": 148.86, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 43.704015016555786, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 700}, {"type": "trade", "ts": 43.704018115997314, "price": 148.86, "size": 300, "side": "unknown"}, {"type": "quote", "ts": 43.70407009124756, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.70414996147156, "bid": 148.85, "ask": 148.87, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 43.70421600341797, "price": 148.86, "size": 73, "side": "unknown"}, {"type": "trade", "ts": 43.70421600341797, "price": 148.86, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 43.70425510406494, "bid": 148.84, "ask": 148.87, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 43.70434617996216, "bid": 148.84, "ask": 148.87, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 43.7045111656189, "bid": 148.83, "ask": 148.87, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 43.7046160697937, "bid": 148.83, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.704631090164185, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.70483708381653, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.704862117767334, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.70489716529846, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 43.70534801483154, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 43.70889115333557, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.709222078323364, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.71429896354675, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 700}, {"type": "trade", "ts": 43.71529817581177, "price": 148.845, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 43.717812061309814, "price": 148.86, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 43.71781516075134, "price": 148.86, "size": 25, "side": "unknown"}, {"type": "trade", "ts": 43.717836141586304, "price": 148.86, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 43.71785807609558, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 43.71786308288574, "bid": 148.83, "ask": 148.87, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 43.71786308288574, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 43.71789813041687, "bid": 148.83, "ask": 148.87, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 43.71789813041687, "bid": 148.84, "ask": 148.87, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 43.718459129333496, "bid": 148.84, "ask": 148.87, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 43.718499183654785, "bid": 148.84, "ask": 148.87, "bid_size": 600, "ask_size": 600}, {"type": "quote", "ts": 43.71851396560669, "bid": 148.84, "ask": 148.87, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 43.71861004829407, "bid": 148.84, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.720394134521484, "bid": 148.83, "ask": 148.87, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 43.72094011306763, "bid": 148.83, "ask": 148.87, "bid_size": 500, "ask_size": 600}, {"type": "quote", "ts": 43.7443311214447, "bid": 148.83, "ask": 148.87, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 43.74450612068176, "bid": 148.83, "ask": 148.87, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.754470109939575, "bid": 148.83, "ask": 148.87, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 43.76786208152771, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 600}, {"type": "trade", "ts": 43.7700731754303, "price": 148.845, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 43.820603132247925, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 600}, {"type": "trade", "ts": 43.820605993270874, "price": 148.86, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 43.820605993270874, "price": 148.86, "size": 11, "side": "unknown"}, {"type": "quote", "ts": 43.82060694694519, "bid": 148.82, "ask": 148.87, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 43.820631980895996, "bid": 148.82, "ask": 148.87, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 43.82066202163696, "bid": 148.83, "ask": 148.87, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 43.82069706916809, "bid": 148.83, "ask": 148.87, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 43.8210129737854, "bid": 148.83, "ask": 148.87, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 43.82114911079407, "bid": 148.83, "ask": 148.88, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 43.82117414474487, "bid": 148.84, "ask": 148.88, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 43.82125401496887, "bid": 148.84, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.82129406929016, "bid": 148.84, "ask": 148.88, "bid_size": 700, "ask_size": 100}, {"type": "quote", "ts": 43.82133412361145, "bid": 148.84, "ask": 148.88, "bid_size": 600, "ask_size": 100}, {"type": "quote", "ts": 43.82137417793274, "bid": 148.83, "ask": 148.88, "bid_size": 600, "ask_size": 100}, {"type": "quote", "ts": 43.82141399383545, "bid": 148.83, "ask": 148.88, "bid_size": 600, "ask_size": 600}, {"type": "quote", "ts": 43.82176995277405, "bid": 148.83, "ask": 148.88, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 43.82232117652893, "bid": 148.83, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.82240605354309, "bid": 148.83, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.82242202758789, "bid": 148.83, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.83173418045044, "bid": 148.83, "ask": 148.88, "bid_size": 700, "ask_size": 100}, {"type": "quote", "ts": 43.898277044296265, "bid": 148.83, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.937806129455566, "bid": 148.83, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.938477993011475, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.93872809410095, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 43.93877410888672, "bid": 148.83, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.94715404510498, "bid": 148.83, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.94718313217163, "bid": 148.83, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 43.94718313217163, "bid": 148.84, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.947219133377075, "bid": 148.84, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.94728899002075, "bid": 148.84, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 43.94829607009888, "bid": 148.84, "ask": 148.89, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 43.94906806945801, "bid": 148.84, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 44.04072117805481, "bid": 148.84, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 44.040971994400024, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 44.11950898170471, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 44.120140075683594, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 700}, {"type": "quote", "ts": 44.42732095718384, "bid": 148.82, "ask": 148.89, "bid_size": 100, "ask_size": 700}, {"type": "trade", "ts": 44.67942214012146, "price": 149.0232, "size": 200, "side": "unknown"}, {"type": "quote", "ts": 44.702471017837524, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 44.703418016433716, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 44.70365905761719, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 44.70369911193848, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 44.70462107658386, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 44.84949612617493, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.085211992263794, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.08523201942444, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.085262060165405, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.08527207374573, "bid": 148.82, "ask": 148.88, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.08528208732605, "bid": 148.82, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.085582971572876, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 45.08590316772461, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 45.086385011672974, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 45.11867713928223, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 45.118741035461426, "price": 148.87, "size": 10, "side": "unknown"}, {"type": "quote", "ts": 45.11874198913574, "bid": 148.82, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.11876201629639, "bid": 148.83, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.118812084198, "bid": 148.84, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.118812084198, "bid": 148.84, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.11881709098816, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.11883211135864, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.119112968444824, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.119457960128784, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 45.119529008865356, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 45.11959409713745, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.12886595726013, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.16881608963013, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.16884112358093, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.16886615753174, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.168890953063965, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.169517040252686, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.177546977996826, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.177842140197754, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.178889989852905, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.17918610572815, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.1802179813385, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.35103416442871, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.35108017921448, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.35171103477478, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.37066602706909, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.38028407096863, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.38071012496948, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.39142608642578, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.40995502471924, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 45.41040110588074, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.41054606437683, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 45.73961901664734, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.013911962509155, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 46.02004313468933, "price": 148.87, "size": 35, "side": "unknown"}, {"type": "trade", "ts": 46.022250175476074, "price": 148.87, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 46.023895025253296, "price": 148.87, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 46.02607607841492, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.11789417266846, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 46.11840605735779, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 46.1693069934845, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.16945195198059, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.174620151519775, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.17463517189026, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.184231996536255, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.205312967300415, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.205984115600586, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.20615005493164, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.206170082092285, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 46.25699210166931, "price": 148.8301, "size": 3, "side": "unknown"}, {"type": "quote", "ts": 46.25772213935852, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.2577919960022, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.25844407081604, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.2663631439209, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.27291297912598, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.31361508369446, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 46.358572006225586, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.35870814323425, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.45359802246094, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.52088403701782, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.956655979156494, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 46.96819806098938, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 47.022886991500854, "price": 149.0047, "size": 2, "side": "unknown"}, {"type": "quote", "ts": 47.02396607398987, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 47.024537086486816, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 47.145209074020386, "bid": 148.82, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 47.14581608772278, "bid": 148.82, "ask": 148.9, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 47.263010025024414, "bid": 148.82, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 47.29852914810181, "price": 149.141, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 47.38875603675842, "price": 148.86, "size": 5, "side": "unknown"}, {"type": "quote", "ts": 47.68066906929016, "bid": 148.82, "ask": 148.9, "bid_size": 100, "ask_size": 300}, {"type": "trade", "ts": 47.72920894622803, "price": 148.8887, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 47.73876214027405, "bid": 148.82, "ask": 148.9, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 47.74876618385315, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 47.749407052993774, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 47.78398513793945, "bid": 148.82, "ask": 148.9, "bid_size": 100, "ask_size": 300}, {"type": "trade", "ts": 48.05236601829529, "price": 148.82, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 48.108558177948, "price": 149.141, "size": 4, "side": "unknown"}, {"type": "trade", "ts": 48.12456798553467, "price": 148.86, "size": 132, "side": "unknown"}, {"type": "quote", "ts": 48.15438103675842, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 48.21202802658081, "bid": 148.82, "ask": 148.9, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 48.21243405342102, "bid": 148.82, "ask": 148.9, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 48.213001012802124, "bid": 148.82, "ask": 148.9, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 48.27926516532898, "price": 148.8887, "size": 14, "side": "unknown"}, {"type": "quote", "ts": 48.35364508628845, "bid": 148.82, "ask": 148.9, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 48.35377097129822, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 48.43866300582886, "bid": 148.82, "ask": 148.9, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 48.49121308326721, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 48.54666996002197, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 300}, {"type": "quote", "ts": 48.54693007469177, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 48.59234309196472, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 49.27778506278992, "bid": 148.84, "ask": 148.9, "bid_size": 100, "ask_size": 300}, {"type": "trade", "ts": 49.30834412574768, "price": 148.87, "size": 3, "side": "unknown"}, {"type": "trade", "ts": 49.318917989730835, "price": 148.84, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 49.39426517486572, "price": 148.87, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 49.93408203125, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 49.93736410140991, "bid": 148.82, "ask": 148.9, "bid_size": 200, "ask_size": 300}, {"type": "trade", "ts": 49.9991660118103, "price": 148.86, "size": 57, "side": "unknown"}, {"type": "quote", "ts": 50.266602993011475, "bid": 148.83, "ask": 148.9, "bid_size": 100, "ask_size": 300}, {"type": "trade", "ts": 50.26685810089111, "price": 148.84, "size": 100, "side": "unknown"}, {"type": "quote", "ts": 50.26698398590088, "bid": 148.83, "ask": 148.9, "bid_size": 300, "ask_size": 300}, {"type": "quote", "ts": 50.281233072280884, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 50.31102895736694, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 50.311079025268555, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 50.312561988830566, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 50.31258201599121, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 800}, {"type": "quote", "ts": 50.31269812583923, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 50.31271314620972, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 600}, {"type": "trade", "ts": 50.315088987350464, "price": 148.8302, "size": 300, "side": "unknown"}, {"type": "quote", "ts": 50.32267618179321, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 50.33504605293274, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 50.91754198074341, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 51.083582162857056, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 51.084028005599976, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 51.08415913581848, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 51.08561706542969, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 51.08818316459656, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 51.089436054229736, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 51.0894660949707, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 51.08987212181091, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 51.09005308151245, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 51.10414099693298, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 51.58520698547363, "price": 148.9174, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 51.62591314315796, "bid": 148.83, "ask": 148.9, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 51.62612295150757, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 51.6262640953064, "bid": 148.83, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 51.62629413604736, "bid": 148.83, "ask": 148.88, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 51.67322516441345, "bid": 148.83, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 52.005632162094116, "bid": 148.83, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 52.251347064971924, "bid": 148.83, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 52.39280915260315, "price": 148.8729, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 52.62472414970398, "price": 148.855, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 52.62924408912659, "price": 148.83, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 53.40692210197449, "bid": 148.83, "ask": 148.88, "bid_size": 200, "ask_size": 100}, {"type": "trade", "ts": 53.70204401016235, "price": 149.0019, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 53.721065044403076, "bid": 148.83, "ask": 148.89, "bid_size": 200, "ask_size": 400}, {"type": "trade", "ts": 53.96250009536743, "price": 148.87, "size": 13, "side": "unknown"}, {"type": "quote", "ts": 53.96255397796631, "bid": 148.84, "ask": 148.89, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 53.962865114212036, "bid": 148.84, "ask": 148.89, "bid_size": 200, "ask_size": 400}, {"type": "trade", "ts": 53.96314001083374, "price": 148.84, "size": 3, "side": "unknown"}, {"type": "quote", "ts": 53.963205099105835, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 1000}, {"type": "trade", "ts": 53.96323609352112, "price": 148.84, "size": 3, "side": "unknown"}, {"type": "quote", "ts": 53.96344614028931, "bid": 148.84, "ask": 148.9, "bid_size": 200, "ask_size": 600}, {"type": "quote", "ts": 53.96402716636658, "bid": 148.84, "ask": 148.9, "bid_size": 600, "ask_size": 600}, {"type": "trade", "ts": 53.96422600746155, "price": 148.87, "size": 7, "side": "unknown"}, {"type": "quote", "ts": 53.96425795555115, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 600}, {"type": "quote", "ts": 53.964564085006714, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 53.96467900276184, "bid": 148.85, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 53.964776039123535, "price": 148.88, "size": 14, "side": "unknown"}, {"type": "quote", "ts": 53.96481394767761, "bid": 148.85, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "quote", "ts": 53.96485495567322, "bid": 148.86, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 53.96499013900757, "bid": 148.86, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 53.96499013900757, "price": 148.88, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 53.965110063552856, "bid": 148.86, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 53.96561098098755, "bid": 148.86, "ask": 148.9, "bid_size": 600, "ask_size": 200}, {"type": "quote", "ts": 53.96561598777771, "bid": 148.86, "ask": 148.9, "bid_size": 600, "ask_size": 700}, {"type": "quote", "ts": 53.9660120010376, "bid": 148.86, "ask": 148.9, "bid_size": 500, "ask_size": 700}, {"type": "trade", "ts": 53.96833109855652, "price": 148.88, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 53.968384981155396, "price": 148.86, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 53.969465017318726, "bid": 148.86, "ask": 148.9, "bid_size": 500, "ask_size": 200}, {"type": "quote", "ts": 53.969825983047485, "bid": 148.86, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 53.973488092422485, "price": 148.86, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 53.97351813316345, "price": 148.86, "size": 2, "side": "unknown"}, {"type": "quote", "ts": 53.973801136016846, "bid": 148.86, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 53.97398614883423, "bid": 148.86, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 53.97435998916626, "price": 148.86, "size": 11, "side": "unknown"}, {"type": "trade", "ts": 53.974364042282104, "price": 148.86, "size": 6, "side": "unknown"}, {"type": "trade", "ts": 53.974364042282104, "price": 148.86, "size": 12, "side": "unknown"}, {"type": "quote", "ts": 53.97436809539795, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 53.974369049072266, "price": 148.86, "size": 3, "side": "unknown"}, {"type": "trade", "ts": 53.974369049072266, "price": 148.86, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 53.974372148513794, "price": 148.86, "size": 33, "side": "unknown"}, {"type": "trade", "ts": 53.974372148513794, "price": 148.86, "size": 33, "side": "unknown"}, {"type": "quote", "ts": 53.97439217567444, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 53.9743971824646, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 53.97440195083618, "bid": 148.84, "ask": 148.9, "bid_size": 1200, "ask_size": 300}, {"type": "quote", "ts": 53.97440195083618, "bid": 148.84, "ask": 148.9, "bid_size": 1200, "ask_size": 200}, {"type": "quote", "ts": 53.97440695762634, "bid": 148.84, "ask": 148.9, "bid_size": 1200, "ask_size": 400}, {"type": "quote", "ts": 53.974416971206665, "bid": 148.84, "ask": 148.89, "bid_size": 1200, "ask_size": 100}, {"type": "quote", "ts": 53.97451210021973, "bid": 148.85, "ask": 148.89, "bid_size": 600, "ask_size": 100}, {"type": "quote", "ts": 53.97472810745239, "bid": 148.84, "ask": 148.89, "bid_size": 1200, "ask_size": 100}, {"type": "quote", "ts": 53.97498917579651, "bid": 148.84, "ask": 148.89, "bid_size": 600, "ask_size": 100}, {"type": "quote", "ts": 53.975104093551636, "bid": 148.84, "ask": 148.89, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 53.975104093551636, "bid": 148.84, "ask": 148.89, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 53.97519397735596, "bid": 148.84, "ask": 148.89, "bid_size": 600, "ask_size": 500}, {"type": "quote", "ts": 53.9752140045166, "bid": 148.84, "ask": 148.89, "bid_size": 200, "ask_size": 500}, {"type": "trade", "ts": 53.975701093673706, "price": 148.87, "size": 54, "side": "unknown"}, {"type": "quote", "ts": 53.97629714012146, "bid": 148.84, "ask": 148.89, "bid_size": 500, "ask_size": 500}, {"type": "trade", "ts": 53.97866916656494, "price": 148.84, "size": 15, "side": "unknown"}, {"type": "trade", "ts": 54.0016450881958, "price": 148.88, "size": 3, "side": "unknown"}, {"type": "trade", "ts": 54.0016450881958, "price": 148.88, "size": 11, "side": "unknown"}, {"type": "trade", "ts": 54.001646995544434, "price": 148.88, "size": 15, "side": "unknown"}, {"type": "quote", "ts": 54.00167202949524, "bid": 148.85, "ask": 148.89, "bid_size": 100, "ask_size": 500}, {"type": "trade", "ts": 54.00167417526245, "price": 148.88, "size": 38, "side": "unknown"}, {"type": "quote", "ts": 54.00171208381653, "bid": 148.85, "ask": 148.89, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 54.00195813179016, "bid": 148.85, "ask": 148.9, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 54.0021231174469, "bid": 148.85, "ask": 148.9, "bid_size": 300, "ask_size": 700}, {"type": "quote", "ts": 54.002148151397705, "bid": 148.85, "ask": 148.9, "bid_size": 200, "ask_size": 700}, {"type": "quote", "ts": 54.00226807594299, "bid": 148.85, "ask": 148.9, "bid_size": 200, "ask_size": 300}, {"type": "quote", "ts": 54.00238394737244, "bid": 148.85, "ask": 148.9, "bid_size": 400, "ask_size": 300}, {"type": "quote", "ts": 54.00245904922485, "bid": 148.85, "ask": 148.9, "bid_size": 400, "ask_size": 700}, {"type": "quote", "ts": 54.00288009643555, "bid": 148.85, "ask": 148.9, "bid_size": 400, "ask_size": 300}, {"type": "quote", "ts": 54.07954716682434, "bid": 148.84, "ask": 148.9, "bid_size": 400, "ask_size": 300}, {"type": "quote", "ts": 54.48920202255249, "bid": 148.84, "ask": 148.9, "bid_size": 300, "ask_size": 300}, {"type": "quote", "ts": 54.48931312561035, "bid": 148.84, "ask": 148.9, "bid_size": 600, "ask_size": 300}, {"type": "trade", "ts": 55.04350304603577, "price": 148.89, "size": 4, "side": "unknown"}, {"type": "trade", "ts": 55.103854179382324, "price": 148.87, "size": 4, "side": "unknown"}, {"type": "trade", "ts": 55.13168501853943, "price": 148.87, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 55.2026150226593, "bid": 148.84, "ask": 148.9, "bid_size": 600, "ask_size": 200}, {"type": "trade", "ts": 55.494553089141846, "price": 148.87, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 55.614530086517334, "bid": 148.85, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 55.61478614807129, "bid": 148.85, "ask": 148.9, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 55.6152069568634, "bid": 148.85, "ask": 148.9, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 55.6152069568634, "bid": 148.85, "ask": 148.9, "bid_size": 600, "ask_size": 200}, {"type": "quote", "ts": 55.61536717414856, "bid": 148.85, "ask": 148.9, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 55.64936304092407, "bid": 148.85, "ask": 148.9, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 55.667662143707275, "bid": 148.85, "ask": 148.9, "bid_size": 400, "ask_size": 200}, {"type": "quote", "ts": 55.750399112701416, "bid": 148.85, "ask": 148.9, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 55.75344109535217, "bid": 148.85, "ask": 148.9, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 56.59272313117981, "bid": 148.85, "ask": 148.9, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 56.787201166152954, "bid": 148.85, "ask": 148.9, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 56.79455900192261, "bid": 148.86, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 56.79457712173462, "price": 148.9, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 56.794594049453735, "bid": 148.87, "ask": 148.9, "bid_size": 200, "ask_size": 200}, {"type": "trade", "ts": 56.79461908340454, "price": 148.89, "size": 3, "side": "unknown"}, {"type": "quote", "ts": 56.79463005065918, "bid": 148.89, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "trade", "ts": 56.794646978378296, "price": 148.9, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 56.79464912414551, "price": 148.9, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 56.79465198516846, "price": 148.9, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 56.79465198516846, "price": 148.9, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 56.79466700553894, "price": 148.9, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 56.79467010498047, "price": 148.9, "size": 99, "side": "unknown"}, {"type": "trade", "ts": 56.79470896720886, "price": 148.89, "size": 14, "side": "unknown"}, {"type": "quote", "ts": 56.7947940826416, "bid": 148.89, "ask": 148.9, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 56.79509496688843, "bid": 148.89, "ask": 148.9, "bid_size": 300, "ask_size": 200}, {"type": "trade", "ts": 56.795494079589844, "price": 148.9, "size": 217, "side": "unknown"}, {"type": "quote", "ts": 56.7955060005188, "bid": 148.89, "ask": 148.93, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 56.79561114311218, "bid": 148.89, "ask": 148.93, "bid_size": 300, "ask_size": 500}, {"type": "quote", "ts": 56.795711040496826, "bid": 148.89, "ask": 148.93, "bid_size": 500, "ask_size": 500}, {"type": "quote", "ts": 56.79609704017639, "bid": 148.89, "ask": 148.93, "bid_size": 300, "ask_size": 500}, {"type": "trade", "ts": 56.79785513877869, "price": 148.91, "size": 2, "side": "unknown"}, {"type": "trade", "ts": 56.798381090164185, "price": 148.9, "size": 14, "side": "unknown"}, {"type": "quote", "ts": 56.79851317405701, "bid": 148.88, "ask": 148.93, "bid_size": 1000, "ask_size": 500}, {"type": "quote", "ts": 56.79941010475159, "bid": 148.88, "ask": 148.93, "bid_size": 500, "ask_size": 500}, {"type": "quote", "ts": 56.79955005645752, "bid": 148.88, "ask": 148.93, "bid_size": 500, "ask_size": 100}, {"type": "quote", "ts": 56.799575090408325, "bid": 148.88, "ask": 148.93, "bid_size": 500, "ask_size": 100}, {"type": "trade", "ts": 56.8077871799469, "price": 148.9, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 56.80919313430786, "bid": 148.88, "ask": 148.93, "bid_size": 500, "ask_size": 500}, {"type": "trade", "ts": 56.80988907814026, "price": 148.9, "size": 4, "side": "unknown"}, {"type": "quote", "ts": 56.84700798988342, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 56.847119092941284, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 56.89544916152954, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 56.895468950271606, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 500}, {"type": "quote", "ts": 56.90662503242493, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 57.021543979644775, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 57.08424997329712, "price": 148.9, "size": 6, "side": "unknown"}, {"type": "quote", "ts": 57.0957350730896, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 57.099244117736816, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 57.099611043930054, "price": 148.91, "size": 20, "side": "unknown"}, {"type": "quote", "ts": 57.0996150970459, "bid": 148.88, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 57.099684953689575, "bid": 148.88, "ask": 148.93, "bid_size": 200, "ask_size": 100}, {"type": "quote", "ts": 57.10000514984131, "bid": 148.89, "ask": 148.93, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 57.100176095962524, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 57.10021615028381, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 57.10021615028381, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 57.100265979766846, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 200}, {"type": "quote", "ts": 57.100451946258545, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 57.100492000579834, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 57.10076713562012, "bid": 148.89, "ask": 148.94, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 57.16965103149414, "bid": 148.89, "ask": 148.94, "bid_size": 300, "ask_size": 100}, {"type": "trade", "ts": 58.002416133880615, "price": 148.94, "size": 4, "side": "unknown"}, {"type": "trade", "ts": 58.74817609786987, "price": 148.93, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 58.74905514717102, "bid": 148.89, "ask": 148.95, "bid_size": 300, "ask_size": 100}, {"type": "trade", "ts": 58.74905705451965, "price": 148.93, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 58.74906301498413, "price": 148.94, "size": 100, "side": "unknown"}, {"type": "trade", "ts": 58.74906301498413, "price": 148.94, "size": 20, "side": "unknown"}, {"type": "trade", "ts": 58.74906611442566, "price": 148.94, "size": 5, "side": "unknown"}, {"type": "quote", "ts": 58.74914002418518, "bid": 148.9, "ask": 148.95, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 58.749226093292236, "bid": 148.9, "ask": 148.96, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 58.7492401599884, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 58.74927496910095, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 58.74940609931946, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 100}, {"type": "trade", "ts": 58.74940609931946, "price": 148.94, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 58.75118613243103, "price": 148.935, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 58.75295400619507, "bid": 148.91, "ask": 148.96, "bid_size": 100, "ask_size": 100}, {"type": "quote", "ts": 58.75335502624512, "bid": 148.91, "ask": 148.96, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 58.75351595878601, "bid": 148.91, "ask": 148.95, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 58.75403714179993, "bid": 148.91, "ask": 148.96, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 58.755210161209106, "bid": 148.91, "ask": 148.96, "bid_size": 300, "ask_size": 400}, {"type": "quote", "ts": 58.75579595565796, "bid": 148.91, "ask": 148.96, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 58.76373505592346, "bid": 148.91, "ask": 148.98, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 58.763790130615234, "bid": 148.91, "ask": 148.98, "bid_size": 300, "ask_size": 200}, {"type": "quote", "ts": 58.7639000415802, "bid": 148.91, "ask": 148.97, "bid_size": 300, "ask_size": 400}, {"type": "quote", "ts": 58.76567006111145, "bid": 148.91, "ask": 148.97, "bid_size": 300, "ask_size": 100}, {"type": "quote", "ts": 58.76766896247864, "bid": 148.91, "ask": 148.97, "bid_size": 300, "ask_size": 600}, {"type": "trade", "ts": 58.77075695991516, "price": 148.94, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 58.77084708213806, "price": 148.94, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 58.772075176239014, "bid": 148.91, "ask": 148.97, "bid_size": 300, "ask_size": 100}, {"type": "trade", "ts": 58.7752890586853, "price": 148.935, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 58.776894092559814, "price": 148.94, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 58.77836012840271, "bid": 148.91, "ask": 148.97, "bid_size": 300, "ask_size": 500}, {"type": "quote", "ts": 58.79510998725891, "bid": 148.91, "ask": 148.97, "bid_size": 300, "ask_size": 100}, {"type": "trade", "ts": 58.79513907432556, "price": 148.94, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 58.802587032318115, "bid": 148.91, "ask": 148.96, "bid_size": 300, "ask_size": 400}, {"type": "trade", "ts": 58.80334496498108, "price": 148.94, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 58.88153004646301, "bid": 148.91, "ask": 148.96, "bid_size": 300, "ask_size": 600}, {"type": "quote", "ts": 58.88155007362366, "bid": 148.91, "ask": 148.96, "bid_size": 300, "ask_size": 400}, {"type": "trade", "ts": 58.923535108566284, "price": 148.935, "size": 1, "side": "unknown"}, {"type": "quote", "ts": 58.98024010658264, "bid": 148.9, "ask": 148.96, "bid_size": 100, "ask_size": 400}, {"type": "quote", "ts": 58.98050618171692, "bid": 148.89, "ask": 148.96, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 59.018962144851685, "bid": 148.89, "ask": 148.96, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 59.055103063583374, "bid": 148.89, "ask": 148.96, "bid_size": 200, "ask_size": 400}, {"type": "quote", "ts": 59.05516815185547, "bid": 148.89, "ask": 148.96, "bid_size": 200, "ask_size": 500}, {"type": "quote", "ts": 59.125837087631226, "bid": 148.89, "ask": 148.96, "bid_size": 200, "ask_size": 400}, {"type": "trade", "ts": 59.178617000579834, "price": 148.925, "size": 11, "side": "unknown"}, {"type": "quote", "ts": 59.17924404144287, "bid": 148.89, "ask": 148.96, "bid_size": 400, "ask_size": 400}, {"type": "trade", "ts": 59.1825749874115, "price": 148.925, "size": 41, "side": "unknown"}, {"type": "trade", "ts": 59.252257108688354, "price": 148.925, "size": 51, "side": "unknown"}, {"type": "trade", "ts": 59.314454078674316, "price": 148.96, "size": 1, "side": "unknown"}, {"type": "trade", "ts": 59.34711694717407, "price": 148.9215, "size": 13, "side": "unknown"}, {"type": "quote", "ts": 59.858004093170166, "bid": 148.89, "ask": 148.96, "bid_size": 400, "ask_size": 700}, {"type": "quote", "ts": 59.88846206665039, "bid": 148.89, "ask": 148.96, "bid_size": 400, "ask_size": 400}, {"type": "quote", "ts": 59.9046151638031, "bid": 148.89, "ask": 148.96, "bid_size": 600, "ask_size": 400}, {"type": "quote", "ts": 59.91258406639099, "bid": 148.89, "ask": 148.96, "bid_size": 400, "ask_size": 400}]}}
\ No newline at end of file
diff --git a/apps/backend/tests/test_event_recording_integration.py b/apps/backend/tests/test_event_recording_integration.py
new file mode 100644
index 0000000..23e1d8b
--- /dev/null
+++ b/apps/backend/tests/test_event_recording_integration.py
@@ -0,0 +1,133 @@
+"""Operator/gated REAL Alpaca historical-fetch + event-window recording check (era-5B J-03) --
+out-of-loop, not hermetic. Per ``.claude/core.md`` (External Integration Testing) the hermetic
+suite alone is NOT sufficient evidence the real credentialed recording works. This is the runnable
+proof that ``record_event_windows.py``'s selection + window + split logic, driven against the REAL
+``GET /research/setups`` scan and the REAL ``POST /research/datasets`` route, registers genuine
+event-window datasets through the real Alpaca historical-fetch seam -- and that a recorded event's
+drill-in (``GET /research/setups/{id}``) then shows a real, non-empty five-state tape timeline.
+
+Distinct from ``test_live_integration.py`` (that file is Alpaca LIVE-SOCKET specific); this one
+exercises the HISTORICAL fetch/record path, never streaming.
+
+Gated: it requires real credentials + an explicit opt-in, so it is SKIPPED in the autonomous loop
+(no opt-in) and never makes a network call by accident.
+
+Run it (operator, creds in ``apps/backend/.env``, real panel bars already populated via
+``scripts/populate_panel_bars.py``):
+
+    TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest tests/test_event_recording_integration.py -v -s
+"""
+
+from __future__ import annotations
+
+import os
+import sys
+from pathlib import Path
+
+import pytest
+from fastapi.testclient import TestClient
+
+SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
+sys.path.insert(0, str(SCRIPTS_DIR))
+
+import record_event_windows as driver  # noqa: E402
+
+from app.config import CONFIG
+from app.main import app
+from app.providers.adapters.alpaca import AlpacaAdapter
+from app.research.datasets import DatasetStore
+
+pytestmark = pytest.mark.integration
+
+
+def test_real_credentialed_event_window_recording_and_tape_join(tmp_path, monkeypatch):
+    if os.environ.get("TAPEOLOGY_LIVE_INTEGRATION") != "1":
+        pytest.skip(
+            "gated: set TAPEOLOGY_LIVE_INTEGRATION=1 to run the real credentialed recording check"
+        )
+    adapter = AlpacaAdapter()
+    if not adapter.is_available():
+        pytest.skip("gated: Alpaca credentials not configured in the environment")
+
+    # A FRESH, isolated dataset dir so this run never mutates any committed fixture and stays
+    # independently re-runnable; the REAL (already-populated) bar store is read unmodified.
+    dataset_dir = tmp_path / "datasets"
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(dataset_dir))
+
+    with TestClient(app) as client:
+        setups_response = client.get("/research/setups")
+        assert setups_response.status_code == 200
+        events = setups_response.json()["events"]
+        assert events, (
+            "the real bar store must already hold scannable panel bars for this check -- run "
+            "scripts/populate_panel_bars.py first"
+        )
+
+        selected = driver.select_recording_events(events, CONFIG)
+        assert selected, "the real scan must produce at least one selectable event"
+        pinned_selected = next((e for e in selected if driver._is_pinned_event(e)), None)
+
+        recorded_metas: list[dict] = []
+        for event in selected:
+            start, end = driver.event_window(event, CONFIG)
+            split = driver.split_for_event(event["id"], CONFIG)
+            body = {
+                "source_kind": "historical", "source_id": event["symbol"],
+                "split": split, "start": start, "end": end,
+            }
+            response = client.post("/research/datasets", json=body)
+            assert response.status_code in (200, 422, 409), (
+                f"unexpected status {response.status_code} for {event['symbol']} "
+                f"{event['session_date']}: {response.text}"
+            )
+            if response.status_code == 200:
+                recorded_metas.append((event, response.json()["dataset"]))
+                print(
+                    f"recorded {event['symbol']} {event['session_date']} touch={event['touch_ts']} "
+                    f"-> dataset {response.json()['dataset']['id']} "
+                    f"(feed={response.json()['dataset']['data_feed']}, split={split})"
+                )
+            else:
+                print(
+                    f"NOT recorded {event['symbol']} {event['session_date']}: "
+                    f"HTTP {response.status_code} {response.json().get('detail')}"
+                )
+
+        assert recorded_metas, "at least one real event window must record successfully"
+        symbols_recorded = {event["symbol"] for event, _meta in recorded_metas}
+        print(
+            f"\n{len(recorded_metas)} datasets recorded across {len(symbols_recorded)} symbols: "
+            f"{sorted(symbols_recorded)}"
+        )
+
+        # Every recorded dataset is genuinely registered, checksummed, feed-stamped, split-frozen.
+        store = DatasetStore(dataset_dir)
+        for _event, meta in recorded_metas:
+            fetched = store.get(meta["id"])
+            assert fetched["checksum"] == meta["checksum"]
+            assert fetched["split"] in ("train", "holdout")
+            assert fetched["data_feed"]  # honestly feed-stamped, never blank
+
+        # If the pinned AAPL 2026-06-22 event recorded successfully, its drill-in must now show a
+        # real, non-empty five-state tape timeline through the REAL route.
+        pinned_recorded = next(
+            (meta for event, meta in recorded_metas if event.get("id") == (pinned_selected or {}).get("id")),
+            None,
+        )
+        if pinned_recorded is not None:
+            detail = client.get(f"/research/setups/{pinned_selected['id']}")
+            assert detail.status_code == 200
+            timeline = detail.json()["event"]["tape_timeline"]
+            assert timeline, "the pinned AAPL 2026-06-22 event must show a real tape timeline once recorded"
+            for entry in timeline:
+                assert entry["state"] in (
+                    "buyer_control", "seller_control", "bid_absorption", "ask_absorption",
+                )
+                assert isinstance(entry["confidence"], float)
+                assert entry["timestamp"]
+            print(f"pinned AAPL 2026-06-22 tape_timeline: {timeline}")
+        else:
+            print(
+                "pinned AAPL 2026-06-22 event was not among this run's recorded datasets "
+                "(already registered earlier, or not selected this run) -- see the dataset list above"
+            )
diff --git a/apps/backend/tests/test_no_credential_in_artifacts.py b/apps/backend/tests/test_no_credential_in_artifacts.py
new file mode 100644
index 0000000..e8a675c
--- /dev/null
+++ b/apps/backend/tests/test_no_credential_in_artifacts.py
@@ -0,0 +1,145 @@
+"""No-credential-in-artifacts gate (era-5B J-03 acceptance) -- Alpaca credential VALUES must never
+appear literal in any source file, fixture, log, test artifact, or report (goal.md's "keys never
+committed, never logged" CRITICAL anti-goal).
+
+Distinct from the EXISTING ``test_alpaca_credential_names_confined_to_one_module``
+(``test_real_data_gate.py``), which polices WHERE the two env-var NAMES ("ALPACA_API_KEY" /
+"ALPACA_API_SECRET") may appear as CODE under ``app/`` -- referencing a NAME is normal and
+required (the adapter reads it; this iteration's own dev handoff must document that the keys were
+present/absent). This gate instead polices two DIFFERENT, complementary things:
+
+  1. **J-03's own new CODE never carries generic secret-shaped vocabulary.** The recording driver
+     only ever calls ``adapter.is_available()`` through the EXISTING neutral seam (architecture
+     fact: it never reads ``ALPACA_API_KEY``/``ALPACA_API_SECRET`` directly) -- so J-03's code has
+     no legitimate reason to contain a lowercase ``api_key`` / ``api_secret`` / ``token``
+     assignment-shaped literal anywhere. The two env-var NAME strings themselves (uppercase,
+     ``ALPACA_API_KEY`` / ``ALPACA_API_SECRET``) are DELIBERATELY NOT forbidden in code: the
+     recording driver's own operator-facing guidance message legitimately prints them by name (so
+     an operator knows what to set), and the dev handoff is REQUIRED to document them by name --
+     exactly the same "a NAME reference is normal, a VALUE never is" distinction
+     ``test_alpaca_credential_names_confined_to_one_module`` already draws for ``app/``. The
+     committed tick-FIXTURE (pure market data, unlike code/docs) has no legitimate reason to
+     contain ANY of these strings in ANY casing, so it is checked against the FULL set -- the
+     EXACT existing ``test_real_gme_sip_fixture_carries_no_credentials`` precedent, reused
+     verbatim. Unlike ``test_no_execution_path.py`` (which deliberately EXCLUDES ``fixtures/``
+     from its scan), this gate's whole reason to exist is to include exactly the surface that scan
+     skips.
+  2. **If this environment currently has REAL credentials configured, their literal VALUES never
+     appear anywhere in the scanned tree.** The strongest possible check -- run only when there is
+     a real secret to compare against (never fabricated); the two env-var NAME strings themselves
+     are explicitly NOT forbidden here (the dev handoff is REQUIRED to document whether the keys
+     were configured, by name, per the DoD -- forbidding the name would conflict with that).
+
+Proven non-vacuous (a file-count floor + named paths) and signal-bearing (a seeded temp file
+containing a credential-shaped string trips the SAME matcher) -- the ``test_no_execution_path.py``
+discipline, applied to secrets.
+"""
+
+from __future__ import annotations
+
+import os
+from pathlib import Path
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+
+# This gate itself names every pattern as data (the test_no_execution_path.py SELF-exemption
+# precedent) -- it is scanning/policing code, not a candidate for the credential scan.
+SELF = Path(__file__).resolve()
+
+# J-03's own new/modified CODE surfaces (script + join code + config + tests) -- an explicit list,
+# not a directory walk, so this gate's scope is exactly what THIS iteration introduces, never an
+# accidental sweep over unrelated pre-existing files (which legitimately reference the env-var
+# NAMES elsewhere in the suite via monkeypatch, and are already policed by
+# test_alpaca_credential_names_confined_to_one_module).
+J03_CODE_FILES = tuple(
+    p for p in (
+        BACKEND_DIR / "scripts" / "record_event_windows.py",
+        BACKEND_DIR / "scripts" / "generate_setups_join_fixture.py",
+        BACKEND_DIR / "app" / "research" / "setups.py",
+        BACKEND_DIR / "app" / "research" / "routes.py",
+        BACKEND_DIR / "app" / "config.py",
+        BACKEND_DIR / "tests" / "test_setups.py",
+        BACKEND_DIR / "tests" / "test_setups_api.py",
+        BACKEND_DIR / "tests" / "test_record_event_windows.py",
+        BACKEND_DIR / "tests" / "test_event_recording_integration.py",
+        SELF,
+    ) if p != SELF
+)
+J03_FIXTURE_DIR = BACKEND_DIR / "tests" / "fixtures" / "datasets_j03"
+
+# CODE: only the lowercase generic-secret vocabulary (the env-var NAMES are legitimate prose there
+# -- operator guidance + the dev handoff's required disclosure).
+CODE_FORBIDDEN_SUBSTRINGS = ("api_key", "api_secret", "token")
+# FIXTURE (pure market data -- no legitimate string in ANY casing): the FULL set
+# test_real_gme_sip_fixture_carries_no_credentials already uses for the era-3 committed fixture,
+# reused verbatim here (a proven, existing precedent, not a new invention).
+FIXTURE_FORBIDDEN_SUBSTRINGS = ("api_key", "api_secret", "ALPACA_API_KEY", "ALPACA_API_SECRET", "token")
+
+
+def _code_files() -> list[Path]:
+    return [p for p in J03_CODE_FILES if p.exists()]
+
+
+def _fixture_files() -> list[Path]:
+    if not J03_FIXTURE_DIR.exists():
+        return []
+    return sorted(p for p in J03_FIXTURE_DIR.iterdir() if p.is_file())
+
+
+def test_scan_is_not_vacuous():
+    code_files = _code_files()
+    assert len(code_files) >= 9
+    names = {p.name for p in code_files}
+    assert "record_event_windows.py" in names
+    assert "setups.py" in names
+    fixture_files = _fixture_files()
+    assert J03_FIXTURE_DIR.exists(), "the committed J-03 tick-fixture directory must exist"
+    assert any(p.suffix == ".json" for p in fixture_files), "the committed tick-fixture must be scanned"
+
+
+def test_matcher_catches_a_seeded_counter_example(tmp_path):
+    seeded = tmp_path / "seeded.py"
+    seeded.write_text('api_secret = "abc123"  # a hardcoded credential value')
+    text = seeded.read_text()
+    assert any(forbidden in text for forbidden in CODE_FORBIDDEN_SUBSTRINGS)
+
+    seeded_fixture = tmp_path / "seeded.json"
+    seeded_fixture.write_text('{"ALPACA_API_KEY": "abc123", "token": "xyz"}')
+    fixture_text = seeded_fixture.read_text()
+    assert any(forbidden in fixture_text for forbidden in FIXTURE_FORBIDDEN_SUBSTRINGS)
+
+
+def test_j03_surfaces_carry_no_credential_shaped_literal():
+    offenders: list[str] = []
+    for path in _code_files():
+        text = path.read_text(errors="ignore")
+        for forbidden in CODE_FORBIDDEN_SUBSTRINGS:
+            if forbidden in text:
+                offenders.append(f"{path.relative_to(BACKEND_DIR)}: {forbidden!r}")
+    for path in _fixture_files():
+        text = path.read_text(errors="ignore")
+        for forbidden in FIXTURE_FORBIDDEN_SUBSTRINGS:
+            if forbidden in text:
+                offenders.append(f"{path.relative_to(BACKEND_DIR)}: {forbidden!r}")
+    assert offenders == [], (
+        "credential-shaped literal found in a J-03 surface — the keys-never-committed-or-logged "
+        f"anti-goal is violated: {offenders}"
+    )
+
+
+def test_real_credential_values_if_configured_never_appear_in_j03_surfaces():
+    """Defense in depth on an operator's credentialed machine: IF real Alpaca credentials are
+    configured in this environment, their literal VALUES must never appear anywhere in J-03's own
+    surfaces. The env-var NAMES themselves are deliberately NOT checked here (the dev handoff must
+    document them by name, per the DoD) -- only the secret VALUES. An honest no-op (nothing to
+    compare against) when no credentials are configured -- never fabricated."""
+    key = os.environ.get("ALPACA_API_KEY", "").strip()
+    secret = os.environ.get("ALPACA_API_SECRET", "").strip()
+    if not key and not secret:
+        return  # nothing configured in this environment -- nothing to check a value against
+    for path in _code_files() + _fixture_files():
+        text = path.read_text(errors="ignore")
+        if key:
+            assert key not in text, f"the real ALPACA_API_KEY value leaked into {path}"
+        if secret:
+            assert secret not in text, f"the real ALPACA_API_SECRET value leaked into {path}"
diff --git a/apps/backend/tests/test_record_event_windows.py b/apps/backend/tests/test_record_event_windows.py
new file mode 100644
index 0000000..7b57fd1
--- /dev/null
+++ b/apps/backend/tests/test_record_event_windows.py
@@ -0,0 +1,191 @@
+"""Pure-function unit tests for the event-window recording driver (era-5B capability 3, J-03) --
+``scripts/record_event_windows.py``.
+
+Imports the script as a module (``sys.path`` insertion onto ``scripts/``, mirroring the script's
+OWN insertion onto the backend root) rather than inventing a package. Operator scripts elsewhere in
+this codebase carry no companion test file at all (``populate_panel_bars.py`` /
+``capture_alpaca_fixture.py`` / ``generate_bar_fixtures.py`` / ``generate_dataset_fixtures.py``) --
+but THIS script introduces two genuinely novel, pure, safety-critical rules this iteration invents
+(the symbol-spread event selection and the deterministic split-assignment digest), so -- unlike
+those precedents, which only drive an already-tested route -- they earn direct unit coverage here
+rather than being exercised only by an operator's own eyeball run. The route-driving `main()` loop
+itself stays uncovered (mirrors the precedent scripts exactly): it is thin argparse + TestClient
+wiring over the ALREADY thoroughly tested ``POST /research/datasets`` route.
+"""
+
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
+sys.path.insert(0, str(SCRIPTS_DIR))
+
+import record_event_windows as driver  # noqa: E402
+
+from app.config import Config  # noqa: E402
+from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN  # noqa: E402
+
+
+def _event(
+    symbol: str, quality: float, event_id: str, session_date: str = "2026-06-10",
+    side: str = "resistance", price_low: float = 100.0, price_high: float = 100.0,
+    touch_ts: str = "2026-06-10T15:00:00.000000Z",
+) -> dict:
+    return {
+        "id": event_id,
+        "symbol": symbol,
+        "session_date": session_date,
+        "touch_ts": touch_ts,
+        "band": {
+            "side": side, "price_low": price_low, "price_high": price_high, "quality_score": quality,
+        },
+    }
+
+
+PINNED_EVENT = _event(
+    "AAPL", quality=5.0, event_id="pinned-aapl", session_date="2026-06-22",
+    price_low=300.0, price_high=302.5, touch_ts="2026-06-22T13:30:00.000000Z",
+)
+
+
+# --- select_recording_events: the pinned event, then symbol-spread, then next-best fill ----------
+
+
+def test_pinned_event_is_always_selected_first():
+    events = [PINNED_EVENT, _event("MSFT", 99.0, "b")]
+    config = Config(recording_event_selection_cap=1)
+    selected = driver.select_recording_events(events, config)
+    assert selected == [PINNED_EVENT], "the pinned event wins even against a higher-quality rival"
+
+
+def test_selection_spreads_across_symbols_before_a_second_event_from_one_symbol():
+    events = [
+        PINNED_EVENT,
+        _event("MSFT", 50.0, "msft-best"),
+        _event("MSFT", 40.0, "msft-second"),  # a SECOND, lower-quality MSFT event
+        _event("NVDA", 10.0, "nvda-only"),  # NVDA's only (lower-quality-than-MSFT) event
+    ]
+    config = Config(recording_event_selection_cap=3)  # room for pinned + 2 more
+    selected = driver.select_recording_events(events, config)
+    assert {e["id"] for e in selected} == {"pinned-aapl", "msft-best", "nvda-only"}, (
+        "NVDA's only event must be picked (symbol spread) before MSFT's second, lower-quality one"
+    )
+
+
+def test_selection_fills_remaining_budget_with_next_best_after_one_per_symbol():
+    events = [
+        PINNED_EVENT,
+        _event("MSFT", 50.0, "msft-best"),
+        _event("MSFT", 40.0, "msft-second"),
+        _event("NVDA", 10.0, "nvda-only"),
+    ]
+    config = Config(recording_event_selection_cap=4)  # room for all four
+    selected = driver.select_recording_events(events, config)
+    assert {e["id"] for e in selected} == {"pinned-aapl", "msft-best", "nvda-only", "msft-second"}
+
+
+def test_selection_respects_the_cap():
+    events = [_event(f"SYM{i}", float(i), f"id{i}") for i in range(20)]
+    config = Config(recording_event_selection_cap=5)
+    selected = driver.select_recording_events(events, config)
+    assert len(selected) == 5
+
+
+def test_selection_is_deterministic_across_repeat_calls():
+    events = [PINNED_EVENT, _event("MSFT", 50.0, "b"), _event("NVDA", 50.0, "c")]
+    config = Config(recording_event_selection_cap=2)
+    first = driver.select_recording_events(events, config)
+    second = driver.select_recording_events(events, config)
+    assert [e["id"] for e in first] == [e["id"] for e in second]
+
+
+def test_selection_on_no_events_is_an_honest_empty_list():
+    assert driver.select_recording_events([], Config()) == []
+
+
+def test_pinned_event_absent_is_never_fabricated():
+    events = [_event("MSFT", 50.0, "b")]
+    selected = driver.select_recording_events(events, Config(recording_event_selection_cap=5))
+    assert all(e["id"] != "pinned-aapl" for e in selected)
+
+
+def test_shipped_default_selection_cap_is_config_sourced():
+    cap = Config().recording_event_selection_cap
+    assert isinstance(cap, int) and cap > 0
+
+
+# --- event_window: touch_ts +/- the config-owned pre/post padding --------------------------------
+
+
+def test_event_window_applies_the_configured_pre_post_padding():
+    event = _event("AAPL", 1.0, "x", touch_ts="2026-06-22T13:30:00.000000Z")
+    config = Config(recording_pre_touch_minutes=60.0, recording_post_touch_minutes=90.0)
+    start, end = driver.event_window(event, config)
+    assert start == "2026-06-22T12:30:00Z"
+    assert end == "2026-06-22T15:00:00Z"
+
+
+def test_event_window_uses_the_shipped_default_padding_of_60_and_90_minutes():
+    event = _event("AAPL", 1.0, "x", touch_ts="2026-06-22T13:30:00.000000Z")
+    start, end = driver.event_window(event, Config())
+    assert start == "2026-06-22T12:30:00Z"
+    assert end == "2026-06-22T15:00:00Z"
+
+
+def test_event_window_is_symmetric_around_a_zero_padding_config():
+    event = _event("AAPL", 1.0, "x", touch_ts="2026-06-22T13:30:00.000000Z")
+    start, end = driver.event_window(event, Config(recording_pre_touch_minutes=0.0, recording_post_touch_minutes=0.0))
+    assert start == end == "2026-06-22T13:30:00Z"
+
+
+# --- split_for_event: the NEW deterministic, config-owned seeded split rule ----------------------
+
+
+def test_split_assignment_is_deterministic_across_repeat_calls():
+    config = Config(recording_holdout_fraction=0.2)
+    first = driver.split_for_event("some-stable-event-id", config)
+    second = driver.split_for_event("some-stable-event-id", config)
+    assert first == second
+    assert first in (SPLIT_TRAIN, SPLIT_HOLDOUT)
+
+
+def test_split_assignment_ratio_zero_always_trains_ratio_one_always_holds_out():
+    for event_id in ("a", "b", "c", "d", "e", "77e4900ec3089ded"):
+        assert driver.split_for_event(event_id, Config(recording_holdout_fraction=0.0)) == SPLIT_TRAIN
+        assert driver.split_for_event(event_id, Config(recording_holdout_fraction=1.0)) == SPLIT_HOLDOUT
+
+
+def test_split_assignment_distribution_is_roughly_the_configured_fraction():
+    """Not exact-value (the digest's own bit distribution is not hand-derivable), but a real
+    statistical sanity check over many distinct ids -- proven non-trivial (both splits appear) and
+    roughly matching the configured ratio, never all-one-split. Verified by direct computation:
+    500 synthetic ids at a 0.2 ratio produced exactly 100 holdout assignments."""
+    config = Config(recording_holdout_fraction=0.2)
+    ids = [f"synthetic-event-{i}" for i in range(500)]
+    holdout_count = sum(1 for i in ids if driver.split_for_event(i, config) == SPLIT_HOLDOUT)
+    assert 50 < holdout_count < 150, f"expected roughly 20% of 500 -- got {holdout_count}"
+
+
+def test_split_assignment_never_reads_wall_clock_or_unseeded_randomness():
+    """Static guard (the deterministic-and-seeded anti-goal): split_for_event's own source must
+    never reference a randomness/time module that would break reproducibility."""
+    import inspect
+
+    src = inspect.getsource(driver.split_for_event)
+    for forbidden in ("random.", "time.time(", "datetime.now(", "uuid.uuid4("):
+        assert forbidden not in src, f"{forbidden!r} found in split_for_event -- not deterministic"
+
+
+# --- No magic numbers: every recording parameter is config-sourced -------------------------------
+
+
+def test_recording_parameters_are_config_sourced_no_magic_numbers():
+    import inspect
+
+    src = inspect.getsource(driver)
+    assert "config.recording_pre_touch_minutes" in src
+    assert "config.recording_post_touch_minutes" in src
+    assert "config.recording_event_selection_cap" in src
+    assert "config.recording_holdout_fraction" in src
+    assert "config.setups_panel_symbols" in src
```
