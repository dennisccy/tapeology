# goal-i_will_be_super_rich-iter-4 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-4
**Date:** 2026-06-04
**Frontend Present:** yes (verification-focused — no frontend code change expected)

## Phase Goal

Close the last two failing journeys: a Live watch of a real US symbol streams the vendor's real-time trades+quotes through the **same** engine with status reading **live** (J-12), and a feed gap beyond `stale_gap_seconds` honestly flips status to **stale** (fabricating no trades) then recovers to **live** (J-15) — with zero regressions and no anti-goal violation (vendor SDK confined to `alpaca.py`, no execution/order code, SSOT preserved).

## Test Cases

### TC-01 — Hermetic async live pipeline populates snapshot with `live` status (J-12)

**Type:** api (pytest, hermetic)
**Preconditions:** `FakeLiveProvider`/`FakeAdapter` async test doubles exist behind the provider seam; backend test env.

**Steps:**
1. Run the J-12 hermetic async test: a test-only `FakeLiveProvider` feeds real-shaped quotes+trades through `watch_with_async_provider` → engine → snapshot.
2. Inspect the resulting snapshot and REST/WS projections.

**Expected outcome:** Snapshot populates; `stream_status == "live"`; tape state + confidence classify; the REST projection equals the WS/`summary` projection.
**Pass criteria:** Test passes asserting `stream_status == "live"`, a non-empty classified state + confidence, and REST-projection == WS-projection (single source of truth) — no recompute in API/UI.

### TC-02 — Stale → recover state machine, no fabricated trades (J-15)

**Type:** api (pytest, hermetic)
**Preconditions:** `stale_gap_seconds` overridable to a small value; async fake feeder.

**Steps:**
1. Override `CONFIG.stale_gap_seconds` to a small value.
2. Feed an event (status → `live`), then withhold events past the timeout, then resume feeding.
3. Capture `stream_status` at each phase and the recent-trades count before/after the lull.

**Expected outcome:** `live` → (gap > timeout) → `stale` → (resume) → `live`; recent-trades count is identical before and after the gap.
**Pass criteria:** Status transitions are exactly live→stale→live AND recent-trades count is **unchanged across the lull** (no synthesized trades during the gap).

### TC-03 — Live lifecycle: stop/switch closes vendor socket, no orphan (iter-0 leak lesson)

**Type:** api (pytest, hermetic)
**Preconditions:** `FakeAdapter.stream_live` records `close`/`unsubscribe` invocations.

**Steps:**
1. Start a live watch via the async seam.
2. Call `stop()` (and separately a source-or-symbol switch).
3. Assert the fake vendor socket's close/unsubscribe was invoked and the feeder task was cancelled.
4. `GET /watch/{ticker}/state` after stop.

**Expected outcome:** Feeder cancelled; vendor socket closed/unsubscribed exactly; no orphaned watch.
**Pass criteria:** Close/unsubscribe assertion passes for both stop and switch; post-stop `…/state` returns **404**; no leaked task.

### TC-04 — Live + no credentials → `provider_unavailable` (503, no engine)

**Type:** api
**Preconditions:** Adapter `is_available()` returns False (no creds).

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/watch/AAPL -H 'Content-Type: application/json' -d '{"source":"live"}'` (or the project's live-source param shape).

**Expected outcome:** Request refused with explicit `provider_unavailable`; no engine/watch created; no fabricated cockpit.
**Pass criteria:** HTTP **503** with error code `provider_unavailable`; no `/state` resource created; no sim fall-back.

### TC-05 — Live + market closed → `market_closed` (409 + next_open, no second clock)

**Type:** api
**Preconditions:** Creds available; `adapter.get_market_clock()` reports `is_open is False` (reuse iter-3 gate / fake clock).

**Steps:**
1. POST a live watch for a symbol while the market-clock pre-flight reports closed.

**Expected outcome:** Refused via the **existing** clock owner with the next open time; no engine started; no fabricated data.
**Pass criteria:** HTTP **409** with code `market_closed` and a `next_open` value; no engine/watch created; reuses the row-8 clock (no second clock).

### TC-06 — Live happy path starts a watch (intended change from `provider_not_implemented`)

**Type:** api (pytest, hermetic async seam)
**Preconditions:** Creds available; clock open; async fake seam wired in test.

**Steps:**
1. Update/execute the `test_real_data_gate.py` live+creds+open-market case to drive the started watch via the fake async seam.
2. Inspect the response body.

**Expected outcome:** The Live branch no longer returns `provider_not_implemented`; it returns a started watch.
**Pass criteria:** Response is `{ticker, scenario: "live <SYM>", status: "watching"}` (HTTP 200); `scenario` equals `live <SYM>` verbatim; no 503 `provider_not_implemented`.

### TC-07 — Vendor confinement: live SDK + names only in `alpaca.py`; sync path 0-diff

**Type:** artifact (git grep + diff)
**Preconditions:** Iteration diff available against the iter-3 baseline.

**Steps:**
1. `git grep -nE 'import alpaca|StockDataStream|Alpaca' -- apps/backend/app | grep -v 'adapters/alpaca.py'`
2. `git diff --stat <iter-3-base> -- apps/backend/app/tape_engine.py apps/backend/app/providers/simulated.py apps/backend/app/providers/historical.py apps/backend/app/serializers* apps/backend/app/providers/base.py`
3. Confirm no order/account/position/trading call appears in `alpaca.py`'s live method.

**Expected outcome:** Vendor SDK/names appear only in `adapters/alpaca.py`; engine, classifier, serializers, and sync providers (`simulated.py`, `historical.py`, sync `Provider`) are unchanged; no execution-path call.
**Pass criteria:** grep at step 1 returns **no matches**; engine/classifier/serializers/simulated/historical show **0-line diff** (base.py changes are additive async-only); no broker/order/account/position symbol in the adapter live method.

### TC-08 — `stale_gap_seconds` is a config field, no magic numbers

**Type:** artifact
**Preconditions:** `app/config.py` modified.

**Steps:**
1. Verify `stale_gap_seconds` exists as a named field in `app/config.py`.
2. Grep the live feeder/watchdog/adapter for inline numeric timeout literals.

**Expected outcome:** The stale timeout (and any new live tunable) is config-driven.
**Pass criteria:** `stale_gap_seconds` present in config; the watchdog reads it from `CONFIG`; no inline timeout literal in engine/feeder/adapter code.

### TC-09 — Operator/gated real Alpaca live socket check exists and is documented honestly

**Type:** artifact
**Preconditions:** Dev handoff written.

**Steps:**
1. Confirm a runnable `@pytest.mark.integration` test or documented operator script connects to the **real** Alpaca live WebSocket during market hours.
2. Read `docs/handoffs/goal-i_will_be_super_rich-iter-4-dev.md`.

**Expected outcome:** A real (non-mocked) integration mechanism is provided; the handoff states explicitly whether it was run and the outcome.
**Pass criteria:** Integration check file/script present; handoff explicitly records run/not-run status (e.g. "not run: off-hours/market closed") with no minimizing — honest per core.md.

### TC-10 — Backend suite green with new tests, no regressions

**Type:** api (pytest)
**Preconditions:** All iter-4 code committed.

**Steps:**
1. Run the backend test command from `.claude/project-template.md` in the backend dir.

**Expected outcome:** Full suite passes including the new async live tests; iter-3 baseline (118 passed, exit 0) is met or exceeded.
**Pass criteria:** Exit 0; pass count ≥ 118 + new tests; **0 failures**, no regressions.

### TC-11 — Browser no-regression: SIM-BUYER → buyer_control (J-01/J-02)

**Type:** browser
**Preconditions:** Frontend running on :3000 (isolated `.next`); backend on :8000.

**Steps:**
1. Navigate to `http://localhost:3000`.
2. Select SIM, choose SIM-BUYER scenario, press Watch.
3. Observe the cockpit tape state.

**Expected outcome:** Cockpit renders and classifies `buyer_control`.
**Pass criteria:** Tape state reads `buyer_control` with the confidence bar populated; screenshot saved under `reports/qa/<phase>-evidence/`.

### TC-12 — Browser no-regression: mode selector + Live controls reveal (J-10) and symbol search (J-13)

**Type:** browser
**Preconditions:** Frontend running.

**Steps:**
1. Open `/`, reveal the data-source/mode selector.
2. Select Live; observe the symbol-search field and `MarketStatusIndicator` render.
3. Type a symbol into the search box (J-13).

**Expected outcome:** Mode selector reveals; Live exposes symbol search + market-status indicator; typing fills the search box.
**Pass criteria:** Live controls + `MarketStatusIndicator` visible; symbol-search box accepts/fills the typed symbol; screenshot saved.

### TC-13 — Browser no-regression: historical AAPL replay populates (J-11)

**Type:** browser
**Preconditions:** Frontend + backend running; historical fixture present.

**Steps:**
1. Select Historical, enter AAPL (committed fixture window), press Watch.
2. Observe the cockpit.

**Expected outcome:** Historical replay streams and the cockpit populates with values.
**Pass criteria:** Cockpit shows non-empty state/features for the AAPL historical replay; screenshot saved.

### TC-14 — Browser no-regression: honest non-cockpit states (J-14)

**Type:** browser
**Preconditions:** Frontend running; a path that yields an explicit honest state (e.g. provider unavailable / market closed / unknown symbol).

**Steps:**
1. Trigger an honest-failure path (e.g. Live with closed market or unavailable provider, or an unknown symbol).
2. Observe the rendered state.

**Expected outcome:** An explicit distinct state renders (provider unavailable / market closed-with-next-open / no-data / error) — never a fabricated cockpit.
**Pass criteria:** The honest non-cockpit state renders with its explicit message; no synthesized tape; screenshot saved.

### TC-15 — Browser: Live status dot color semantics render from canonical snapshot (J-12/J-15 UI)

**Type:** browser
**Preconditions:** Frontend running; a live watch can be driven (hermetic/fake-backed or operator). If a real live feed is unavailable in-loop, verify the controls/dot render and rely on TC-01/TC-02 for the live/stale flip evidence.

**Steps:**
1. Start (or simulate via available path) a Live watch; observe the TopBar status dot and watched-source label.
2. Confirm the dot maps `live`→emerald, `stale`→amber, `closed`→rose from `snapshot.stream_status`, and the label shows `live <SYM>`.

**Expected outcome:** The dot reads the canonical `snapshot.stream_status` and renders the correct color; the watched-source label includes `live <SYM>`.
**Pass criteria:** Dot color matches the snapshot status (emerald=live / amber=stale); label shows `live <SYM>`; no recomputation in the UI. (Live feed itself is operator/gated — not a browser-against-live-market assertion.)

## Summary

Total test cases: 15
- API tests: 7 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-10)
- Browser tests: 5 (TC-11, TC-12, TC-13, TC-14, TC-15)
- Artifact checks: 3 (TC-07, TC-08, TC-09)

**Notes:** The live feed itself (J-12/J-15 against the real Alpaca socket) is operator/gated and out-of-loop — likely not runnable in-loop (market closed today, 2026-06-04). The primary in-loop evidence is the hermetic async fake (TC-01, TC-02, TC-03). Per `.claude/core.md`, the mocked suite alone is not sufficient evidence the real integration works (TC-09 verifies a real, runnable, honestly-documented gated check exists). Browser checks that get SKIPPED because the frontend is not running must NOT cause a FAIL; functional-test-case failures ARE blockers.
