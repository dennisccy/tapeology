# goal-i_will_be_super_rich-iter-2 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-2
**Date:** 2026-06-04
**Frontend Present:** yes

## Phase Goal

Wire the first real provider behind the seam: Historical replay (J-11) of real Alpaca trades+quotes through the **same** engine, plus `GET /symbols/search` (J-13), with every real-data failure surfacing an explicit, distinct non-cockpit state and never a fabricated tape (J-14) — without regressing the sim path J-01–J-10.

> **Endpoint note:** watches are `POST /watch/{ticker}` with a JSON body; canonical reads are `GET /tape/{ticker}/state|features|events|summary`. Historical body is expected to carry `mode:"historical"` plus `start`, `end`, `speed`. API tests assume backend on `http://localhost:8000`. Tests that would require real Alpaca network access are marked **operator-gated**; the in-loop J-11 evidence rests on the committed real fixture via DI.

## Test Cases

### TC-01 — Deterministic real-fixture replay populates every cockpit value
**Type:** artifact (pytest)
**Preconditions:** Committed **real** Alpaca fixture exists; `test_historical_provider.py` injects a fake adapter (DI) returning it.

**Steps:**
1. Run `cd apps/backend && .venv/bin/pytest tests/test_historical_provider.py -v`.
2. Inspect the replayed snapshot assertions.

**Expected outcome:** Replaying the fixture through `HistoricalProvider` + `TapeEngine` yields a snapshot with non-empty bid/ask/spread/last, recent trades (price/size/side), all feature readouts, a tape state + confidence, observations, and event log.
**Pass criteria:** Test passes; **every** listed cockpit field is asserted present and populated (not null/empty). If no real fixture was captured, the test scaffold exists and the dev handoff documents an escalation — **no synthesized fixture** is committed.

### TC-02 — Replay is deterministic / reproducible
**Type:** artifact (pytest)
**Preconditions:** Same fixture as TC-01.

**Steps:**
1. Run the replay twice within the test (or two identical runs).
2. Compare resulting state, confidence, and feature values.

**Expected outcome:** Two identical runs produce byte-identical state/confidence/features.
**Pass criteria:** Equality assertion passes; no wall-clock or randomness influences output.

### TC-03 — Timestamp → logical mapping (monotonic, quote-before-trade)
**Type:** artifact (pytest)
**Preconditions:** `test_historical_provider.py`.

**Steps:**
1. Build a `HistoricalProvider` over a fixture with interleaved quotes and trades sharing an instant.
2. Collect the yielded event stream.

**Expected outcome:** Logical timestamps are monotonic non-decreasing offsets from window start; at the same instant the quote is yielded before the trade; trades are emitted as `Side.UNKNOWN`.
**Pass criteria:** Assertions on ordering, monotonicity, and `Side.UNKNOWN` all pass.

### TC-04 — Historical watch populates the cockpit in the browser (SSOT)
**Type:** browser
**Preconditions:** Frontend on :3000, backend on :8000. Operator creds OR fixture-backed historical watch reachable.

**Steps:**
1. Navigate to `/`. Select **Historical** mode; pick a symbol, past window, and speed; click Watch.
2. Wait for the cockpit to populate.
3. Read the displayed last/spread/tape-state, then `curl http://localhost:8000/tape/<SYM>/state` and `/features`.

**Expected outcome:** Cockpit renders real values (no fabricated panels); REST `/state` + `/features` match the on-screen values.
**Pass criteria:** UI values equal REST values (single source of truth). If vendor unreachable in QA env: record **operator-gated**; verify controls + cockpit-warmup render without error. SKIPPED-not-running is not a FAIL.

### TC-05 — Source label reads `historical <SYM> <window>`
**Type:** browser
**Preconditions:** Successful historical watch (TC-04) or fixture-backed watch.

**Steps:**
1. After a historical watch succeeds, read the watched-source label in the cockpit.

**Expected outcome:** Label shows `historical <SYM> <window>`, sourced from `snapshot.scenario` (row 6) — not client-recomputed.
**Pass criteria:** Label string matches the `scenario` returned by `/tape/<SYM>/state`.

### TC-06 — `GET /symbols/search` returns real tradable matches
**Type:** api (operator-gated — real adapter)
**Preconditions:** Creds present; backend on :8000.

**Steps:**
1. `curl -s "http://localhost:8000/symbols/search?q=AAP"`

**Expected outcome:** 200 with a JSON array of `{symbol, name}` objects, capped by the config result limit.
**Pass criteria:** Status 200; array elements have `symbol` and `name`; length ≤ configured limit. If no creds/network: returns `[]` (see TC-08), recorded operator-gated.

### TC-07 — Symbol-search short/empty query → empty list
**Type:** api
**Preconditions:** Backend on :8000.

**Steps:**
1. `curl -s -w "%{http_code}" "http://localhost:8000/symbols/search?q="`
2. `curl -s -w "%{http_code}" "http://localhost:8000/symbols/search?q=a"` (below config min length)

**Expected outcome:** Both return 200 with `[]` — short/empty is **not** an error.
**Pass criteria:** Status 200 and body `[]` for both.

### TC-08 — Symbol search with no creds degrades gracefully
**Type:** api
**Preconditions:** Creds absent (gate returns false).

**Steps:**
1. `curl -s -w "%{http_code}" "http://localhost:8000/symbols/search?q=AAPL"`

**Expected outcome:** 200 with `[]` — no error, no fabricated suggestions; free-text watch entry remains possible.
**Pass criteria:** Status 200, body `[]`.

### TC-09 — Symbol search box: suggestions, selection, free-text
**Type:** browser
**Preconditions:** Frontend on :3000, search endpoint returning matches (or empty).

**Steps:**
1. In Live/Historical mode, type a partial symbol in the symbol input.
2. Observe the debounced suggestions dropdown; click a suggestion.
3. Separately, type a full free-text symbol and Watch without selecting a suggestion.

**Expected outcome:** Suggestions (symbol + name) appear after debounce; clicking one fills the symbol; free-text entry still works.
**Pass criteria:** Dropdown renders adapter results verbatim; selection populates the input; free-text Watch proceeds. With no matches → no dropdown, free-text still works.

### TC-10 — Unknown/untradable historical symbol → `symbol_not_tradable`, no engine
**Type:** api
**Preconditions:** Creds present (or fixture/DI fake returning a not-tradable signal).

**Steps:**
1. `curl -s -w "%{http_code}" -X POST http://localhost:8000/watch/ZZZZZ -H 'Content-Type: application/json' -d '{"mode":"historical","start":"<past>","end":"<past+>","speed":1}'`
2. `curl -s -w "%{http_code}" http://localhost:8000/tape/ZZZZZ/state`

<!-- the timestamps above are placeholders; a valid past window -->

**Expected outcome:** Step 1 → 4xx with body `reason == "symbol_not_tradable"` and a "not a tradable symbol" detail; step 2 → 404 (no engine created).
**Pass criteria:** Watch body carries `reason:"symbol_not_tradable"`; subsequent `/state` returns 404.

### TC-11 — Empty window → `no_data_for_window`, no engine
**Type:** api
**Preconditions:** Creds present (or DI fake returning empty window).

**Steps:**
1. `POST /watch/<SYM>` with `mode:"historical"` and a valid-but-empty past window.
2. `GET /tape/<SYM>/state`.

**Expected outcome:** Step 1 → 4xx with body `reason == "no_data_for_window"` and "no data for that window" detail; step 2 → 404.
**Pass criteria:** `reason:"no_data_for_window"` present; `/state` 404.

### TC-12 — Missing creds → `503 provider_unavailable`, no engine
**Type:** api
**Preconditions:** Creds absent (gate false).

**Steps:**
1. `curl -s -w "%{http_code}" -X POST http://localhost:8000/watch/AAPL -H 'Content-Type: application/json' -d '{"mode":"historical","start":"<past>","end":"<past+>","speed":1}'`
2. `GET /tape/AAPL/state`.

**Expected outcome:** Step 1 → 503 with `reason == "provider_unavailable"`; step 2 → 404.
**Pass criteria:** Status 503, `reason:"provider_unavailable"`; `/state` 404. The three failure reasons (TC-10/11/12) are **distinct**.

### TC-13 — Honest non-cockpit panels render distinctly (browser)
**Type:** browser
**Preconditions:** Frontend on :3000.

**Steps:**
1. Trigger an untradable-symbol historical watch → observe panel.
2. Trigger a no-data-window watch → observe panel.
3. With no creds, trigger a historical watch → observe panel.

**Expected outcome:** Three **distinct** amber panels: "not a tradable symbol", "no data for that window", "real-data provider unavailable". Each replaces the cockpit; **no** cockpit/fabricated panels shown.
**Pass criteria:** Each reason renders its own message; cockpit is absent in all three.

### TC-14 — Param validation → 422 (no engine)
**Type:** api
**Preconditions:** Backend on :8000; creds present (validation precedes fetch).

**Steps:**
1. `end ≤ start`: `POST /watch/AAPL` with `start` after `end`.
2. Unparseable date: `start:"not-a-date"`.
3. Out-of-bounds speed: `speed:999`.

**Expected outcome:** Each returns 422; no engine created.
**Pass criteria:** Status 422 for all three; subsequent `/tape/AAPL/state` → 404.

### TC-15 — Unknown mode → 422 (regression)
**Type:** api
**Preconditions:** Backend on :8000.

**Steps:**
1. `POST /watch/AAPL` with `{"mode":"bogus"}`.

**Expected outcome:** 422 (Literal validation rejects unknown mode).
**Pass criteria:** Status 422.

### TC-16 — WatchManager historical lifecycle: cancellable, no orphaned task
**Type:** artifact (pytest)
**Preconditions:** `watch_manager` tests with DI fake adapter/provider.

**Steps:**
1. Start a historical watch (feeder task created).
2. Call `stop()`; assert the feeder task is cancelled and removed from `self._tasks`.
3. Start a watch then switch (new watch / source switch); assert prior feeder is torn down.

**Expected outcome:** No leaked/orphaned replay task after stop or switch (iter-0 lesson).
**Pass criteria:** Tests assert task cancellation on both `stop()` and switch; no lingering tasks.

### TC-17 — Adapter / vendor confinement
**Type:** artifact (pytest)
**Preconditions:** `test_real_data_gate.py` (extended).

**Steps:**
1. Run `.venv/bin/pytest tests/test_real_data_gate.py -v`.
2. Confirm the guard scans engine/config/serializers/`providers/base.py`/`providers/simulated.py` for the Alpaca name and `alpaca` import.

**Expected outcome:** `alpaca-py` import and the name "Alpaca" appear **only** in `providers/adapters/alpaca.py`; all other listed modules are vendor-free.
**Pass criteria:** Guard tests pass; SDK import allowed solely in the one adapter module.

### TC-18 — No secrets committed; `.env` untracked; `.env.example` empty
**Type:** artifact
**Preconditions:** Repo checkout.

**Steps:**
1. `git ls-files apps/backend/.env` (expect empty output).
2. `git check-ignore apps/backend/.env`.
3. Inspect `apps/backend/.env.example` for empty values only.

**Expected outcome:** `.env` is untracked and gitignored; `.env.example` carries variable names with empty values (canonical `ALPACA_API_KEY` / `ALPACA_API_SECRET`).
**Pass criteria:** `git ls-files` returns nothing for `.env`; `check-ignore` matches; `.env.example` contains no real secret values.

### TC-19 — `.env` loader does not override existing env (hermetic)
**Type:** artifact (pytest)
**Preconditions:** `app/env.py` loader; `conftest.py` imports it.

**Steps:**
1. Run a test that sets an env var via `monkeypatch`, then triggers the loader.
2. Assert the monkeypatched value is preserved.

**Expected outcome:** Loader is load-if-missing — never overrides an already-set var; suite stays hermetic.
**Pass criteria:** Existing gate tests stay green; override test passes.

### TC-20 — No magic numbers (config-sourced tunables)
**Type:** artifact
**Preconditions:** Repo checkout.

**Steps:**
1. Grep `app/config.py` for allowed replay-speed set + default, replay pacing cap, symbol-search result limit, search min-query-length.
2. Grep `historical.py` / `watch_manager.py` / `main.py` for inline numeric literals for these tunables.

**Expected outcome:** All new tunables defined in `config.py`; no inline magic numbers in engine/provider/main code. Allowed-speed set ⊇ UI `{1,2,5,10}`.
**Pass criteria:** Config holds each tunable; no offending literal found in code paths.

### TC-21 — `alpaca-py` added through the supply-chain gate and pinned
**Type:** artifact
**Preconditions:** Repo checkout.

**Steps:**
1. Confirm `apps/backend/requirements.txt` contains a **pinned** `alpaca-py==<version>`.
2. Confirm a capture script `apps/backend/scripts/capture_alpaca_fixture.py` exists.

**Expected outcome:** Pinned dependency present; capture script committed.
**Pass criteria:** Pinned `alpaca-py==` line exists; capture script present.

### TC-22 — Full backend suite passes; no regressions (≥84 tests)
**Type:** artifact (pytest)
**Preconditions:** `.venv` installed.

**Steps:**
1. `cd apps/backend && .venv/bin/pytest -q 2>&1 | tee reports/qa/goal-i_will_be_super_rich-iter-2-test.log`

**Expected outcome:** All existing 84 tests stay green plus new tests pass; exit code 0.
**Pass criteria:** 0 failures, 0 errors; total ≥ 84 + new tests.

### TC-23 — Sim path byte-for-byte unchanged (J-01–J-10 backend)
**Type:** api
**Preconditions:** Backend on :8000.

**Steps:**
1. `POST /watch/SIM-BUYER` with no body.
2. `POST /watch/SIM-BUYER` with `{}`.
3. `POST /watch/SIM-BUYER` with `{"mode":"sim"}`.

**Expected outcome:** All three behave identically to pre-iteration: 200, `status:"watching"`, scenario set; engine created normally.
**Pass criteria:** Identical 200 responses across the three; sim registry behavior unchanged.

### TC-24 — Browser regression: J-10 selector, J-01/J-02 buyer_control, J-09 stop→idle
**Type:** browser
**Preconditions:** Frontend on :3000, backend on :8000.

**Steps:**
1. Verify the data-source selector renders and per-mode controls reveal (J-10).
2. Watch SIM-BUYER → confirm tape state reaches `buyer_control` (J-01/J-02).
3. Click Stop → confirm cockpit returns to idle/empty (J-09).

**Expected outcome:** Selector + per-mode reveal intact; SIM-BUYER classifies buyer_control; Stop returns idle.
**Pass criteria:** All three behave as in iter-1; no regression. SKIPPED-not-running ≠ FAIL.

### TC-25 — Dev handoff written
**Type:** artifact
**Preconditions:** Implementation complete.

**Steps:**
1. Confirm `docs/handoffs/goal-i_will_be_super_rich-iter-2-dev.md` exists and documents the verification path taken (real capture vs. escalation).

**Expected outcome:** Handoff present and complete; if real capture was impossible, escalation is documented (no fabricated fixture).
**Pass criteria:** File exists with the verification-path outcome recorded.

---

## Summary

Total test cases: **25**
- API tests: 9 (TC-06, TC-07, TC-08, TC-10, TC-11, TC-12, TC-14, TC-15, TC-23)
- Browser tests: 6 (TC-04, TC-05, TC-09, TC-13, TC-24, and the browser half of J-11 in TC-04)
- Artifact checks (incl. pytest): 10 (TC-01, TC-02, TC-03, TC-16, TC-17, TC-18, TC-19, TC-20, TC-21, TC-22, TC-25)

Coverage map: J-11 → TC-01/02/03/04/05; J-13 → TC-06/07/08/09; J-14 → TC-10/11/12/13; validation → TC-14/15; lifecycle → TC-16; anti-goals (vendor seam, secrets, no-magic-numbers, deterministic, no fabrication) → TC-17/18/19/20/21; regression → TC-22/23/24; handoff → TC-25.

**Operator-gated** (require real Alpaca network/creds; record as gated if QA env cannot reach vendor, do not FAIL on this basis): TC-04 (live half), TC-06. In-loop J-11 evidence rests on the committed real fixture (TC-01/02/03).
