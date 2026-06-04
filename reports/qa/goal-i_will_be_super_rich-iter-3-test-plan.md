# goal-i_will_be_super_rich-iter-3 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-3
**Date:** 2026-06-04
**Frontend Present:** yes

## Phase Goal

Complete **J-14 (4/4)** by building the registered Data Contract **row 8** (`GET /market/clock`) and using it to (a) turn the Live **market-status indicator** from a hardcoded "unavailable" stub into a real open/closed + next-open readout, and (b) add a **market-closed pre-flight gate** to the live `POST /watch` branch so a Live watch while the market is closed surfaces an explicit, distinct **"market is closed (with next open)"** non-cockpit state — never a cockpit, never a fabricated tape, **no engine created** — while live streaming stays honestly absent (`provider_not_implemented`).

> Note: the QA harness may serve the backend on a deterministic offset port (e.g. `:8650`) and the frontend on `:3000`. Commands below use `${API}` (default `http://localhost:8000`); substitute the harness port. Hermetic backend tests run via `FakeAdapter` + `dependency_overrides` and are authoritative for closed-market behavior regardless of wall-clock.

## Test Cases

### TC-01 — Backend suite passes with no regressions
**Type:** artifact
**Preconditions:** Repo clean; deps installed.

**Steps:**
1. Run the backend test command from `.claude/project-template.md` (pytest), capturing to `reports/qa/<phase>-test.log`.
2. Record exact pass/fail counts.

**Expected outcome:** All backend tests pass; count ≥ prior baseline (was **110**), increased by the new clock/gate tests.
**Pass criteria:** pytest exit code 0; **0 failures, 0 errors**; total collected ≥ 110.

---

### TC-02 — `GET /market/clock` with creds, market open
**Type:** api (hermetic — FakeAdapter clock=open via `dependency_overrides`)
**Preconditions:** FakeAdapter `is_available()=True`, `get_market_clock()` → `is_open=True`.

**Steps:**
1. Override `get_market_adapter` with an open-clock FakeAdapter.
2. `GET /market/clock`.

**Expected outcome:** `200` with `available:true`, `is_open:true`, ISO-8601 (`Z`) `next_open`/`next_close`.
**Pass criteria:** status `200`; body `{"available": true, "is_open": true, "next_open": <iso str>, "next_close": <iso str>}`; datetimes are explicit UTC ISO-8601 strings.

---

### TC-03 — `GET /market/clock` with creds, market closed
**Type:** api (hermetic — FakeAdapter clock=closed)
**Preconditions:** FakeAdapter `is_available()=True`, `get_market_clock()` → `is_open=False`.

**Steps:**
1. Override adapter with a closed-clock FakeAdapter.
2. `GET /market/clock`.

**Expected outcome:** `200` reporting closed with a real next open.
**Pass criteria:** status `200`; `available:true`, `is_open:false`, **`next_open` is non-null** ISO-8601 string.

---

### TC-04 — `GET /market/clock` with no creds → explicit unavailable
**Type:** api (hermetic — FakeAdapter `is_available()=False`)
**Preconditions:** Adapter override reports no credentials.

**Steps:**
1. Override adapter to `is_available()=False`.
2. `GET /market/clock`.

**Expected outcome:** Explicit unavailable; never a guessed open/closed.
**Pass criteria:** status `200`; body `{"available": false, "is_open": null, "next_open": null, "next_close": null}` (all session fields null, **no fabricated** open/closed).

---

### TC-05 — `GET /market/clock` adapter/network error → degrade, never fabricate
**Type:** api (hermetic — FakeAdapter whose `get_market_clock()` raises)
**Preconditions:** Adapter override raises on `get_market_clock()`.

**Steps:**
1. Override adapter so `get_market_clock()` raises (vendor/network error).
2. `GET /market/clock`.

**Expected outcome:** Benign degrade (like `/symbols/search`), not a 500 and not a fabricated status.
**Pass criteria:** status `200`; `available:false` with null `is_open`/`next_open`/`next_close`; **no** invented open/closed value.

---

### TC-06 — `POST /watch` Live, market closed → distinct `market_closed` refusal + no engine
**Type:** api (hermetic — FakeAdapter `is_available()=True`, `is_open=False`)
**Preconditions:** Closed-clock FakeAdapter override.

**Steps:**
1. `POST ${API}/watch/AAPL` with body selecting `mode:"live"`.
2. Inspect status + body.
3. `GET ${API}/tape/AAPL/state`.

**Expected outcome:** Explicit `market_closed` refusal carrying the next open; **no engine created**.
**Pass criteria:** watch response status is the configured 4xx/503 (default **409**, `CONFIG.market_closed_status_code`); body `reason == "market_closed"`, `detail` mentions market closed, and a structured **`next_open`** field is present and non-null; subsequent `GET /tape/AAPL/state` → **404** (no engine/snapshot).

---

### TC-07 — `POST /watch` Live, market open → honest `provider_not_implemented`
**Type:** api (hermetic — FakeAdapter `is_available()=True`, `is_open=True`)
**Preconditions:** Open-clock FakeAdapter override (streaming still unbuilt).

**Steps:**
1. `POST ${API}/watch/AAPL` with `mode:"live"`.
2. Inspect body; then `GET /tape/AAPL/state`.

**Expected outcome:** Honest iter-4 boundary — streaming absent, no fabricated cockpit.
**Pass criteria:** `reason == "provider_not_implemented"`; **no** cockpit/snapshot produced (`GET /tape/AAPL/state` → 404).

---

### TC-08 — Degraded-clock honesty: unreachable clock is NOT reported as closed
**Type:** api (hermetic — FakeAdapter `is_available()=True` but clock degraded → `is_open=None`/raises)
**Preconditions:** Creds present, but `get_market_clock()` degrades (`available:false` / `is_open=None`).

**Steps:**
1. Override adapter so creds present but the clock call degrades.
2. `POST ${API}/watch/AAPL` `mode:"live"`.

**Expected outcome:** A degraded clock must not fabricate a "closed" session; fall through to the existing refusal.
**Pass criteria:** `reason != "market_closed"`; falls through to `provider_not_implemented` (the gate guards on `is_open is False`, not falsy `None`). No fabricated session state.

---

### TC-09 — Four real-data refusal reasons are pairwise distinct
**Type:** api (hermetic)
**Preconditions:** FakeAdapter variants for each path.

**Steps:**
1. Trigger each: no-creds live (`provider_unavailable`), untradable symbol (`symbol_not_tradable`), empty historical window (`no_data_for_window`), live+closed (`market_closed`).
2. Collect the `reason` of each.

**Expected outcome:** Each failure mode surfaces its own distinct reason.
**Pass criteria:** the set `{provider_unavailable, symbol_not_tradable, no_data_for_window, market_closed}` has 4 distinct values; the existing three reasons' response bodies are unchanged byte-for-byte (only `market_closed` carries `next_open`).

---

### TC-10 — Vendor/credential confinement stays green (anti-goal guard)
**Type:** artifact
**Preconditions:** Working tree after implementation.

**Steps:**
1. Run the existing SDK-confinement + credential-confinement tests.
2. `git grep -n "import alpaca\|ALPACA_API_"` across `app/` excluding `providers/adapters/alpaca.py`.

**Expected outcome:** `import alpaca` and `ALPACA_API_*` names confined to `providers/adapters/alpaca.py`; engine/config/serializers/`providers/base.py`/`providers/simulated.py` reference no vendor.
**Pass criteria:** confinement tests pass **unchanged**; grep finds zero vendor references outside `alpaca.py`.

---

### TC-11 — No-magic-numbers & engine-untouched guard
**Type:** artifact
**Preconditions:** Implementation complete.

**Steps:**
1. Confirm the market-closed status code is read from `app/config.py` (no inline literal in main.py gate).
2. `git diff` the engine/classifier/serializers/`providers/base.py`/`providers/simulated.py`/`providers/historical.py`.

**Expected outcome:** Status code is config-driven; sim + historical paths behavior-identical.
**Pass criteria:** `CONFIG.market_closed_status_code` (or equivalent) exists and is used; **empty diff** in engine/config-math/serializers/`providers/base.py`/`simulated.py`/`historical.py`.

---

### TC-12 — Frontend build is clean
**Type:** artifact
**Preconditions:** Frontend deps installed.

**Steps:**
1. Run `npm run build` in `apps/frontend`.

**Expected outcome:** Production build succeeds with no type errors.
**Pass criteria:** build exit code 0; no TypeScript errors (e.g. `market_closed` in `FailureReason`, `MarketClock` type resolve).

---

### TC-13 — Live market-status indicator renders real session status (browser)
**Type:** browser (Chrome MCP)
**Preconditions:** Backend + frontend running; real Alpaca creds in env.

**Steps:**
1. Navigate to `http://localhost:3000`.
2. Select **Live** data source.
3. Observe the TopBar market-status indicator.
4. Screenshot to `reports/qa/<phase>-evidence/TC-13-market-indicator.png`.

**Expected outcome:** Indicator shows a **real** session status — **open** (emerald "market open") or **closed** (amber "market closed — next open <time>"), or **unavailable** (slate/amber) if `available:false`. Never the old static "unavailable" stub when creds are present, never a placeholder "open" before first fetch.
**Pass criteria:** indicator reflects the live `GET /market/clock` value (open/closed/unavailable), with a `font-mono` next-open time when closed; document which branch (open/closed) was observed at run time.

---

### TC-14 — Live watch while market closed → honest non-cockpit panel (browser)
**Type:** browser (Chrome MCP)
**Preconditions:** Backend + frontend running; creds present; market **closed** at run time (else rely on TC-06 for the closed branch and document).

**Steps:**
1. Select **Live**; enter `AAPL`; click **Watch**.
2. Observe rendered panel; screenshot to `reports/qa/<phase>-evidence/TC-14-market-closed.png`.

**Expected outcome:** The **"market is closed — next open <time>"** panel renders **in place of** the cockpit (no quote / trades / state panels), via the mutually-exclusive `Cockpit | ProviderUnavailable | IdleState` ternary.
**Pass criteria:** distinct "market is closed" copy + next-open time shown; **no** cockpit/quote/trades/state panel present; if market is open at run time, document that and cite TC-06 for the closed branch.

---

### TC-15 — Poll cleanup on unmount / mode-change (resource-leak guard)
**Type:** browser (Chrome MCP) / code inspection
**Preconditions:** Frontend running.

**Steps:**
1. Select **Live** (indicator begins polling on its config-driven interval).
2. Switch the data source away from Live (e.g. to Simulated).
3. Confirm via DevTools / code that the poll interval is cleared (no continued `/market/clock` requests; cleared on unmount and mode-change).

**Expected outcome:** No leaked timer after leaving Live (iter-0 lesson).
**Pass criteria:** no `/market/clock` network requests fire after switching away from Live; the indicator's `useEffect` clears its interval on unmount/mode-change.

---

### TC-16 — Regression smoke: core journeys still green (browser)
**Type:** browser (Chrome MCP)
**Preconditions:** Backend + frontend running.

**Steps:**
1. Simulated: Watch `SIM-BUYER` → confirm classification resolves to **buyer_control** (J-01/J-02/J-10).
2. Historical: run a replay → confirm the cockpit populates (J-11).
3. Symbol search → confirm it fills the ticker box (J-13).
4. Click **Stop** → confirm return to idle state (J-09).
5. Screenshot key states under `reports/qa/<phase>-evidence/`.

**Expected outcome:** All listed required-still-passing journeys behave as before; no regression from the TopBar/panel changes.
**Pass criteria:** `SIM-BUYER` → buyer_control; historical replay populates cockpit; symbol search fills box; Stop → idle. All pass.

---

## Summary

Total test cases: **16**
- API tests: **8** (TC-02 – TC-09)
- Browser tests: **4** (TC-13, TC-14, TC-15, TC-16)
- Artifact checks: **4** (TC-01, TC-10, TC-11, TC-12)

Coverage maps to DoD: J-14 4/4 (TC-06, TC-14), row-8 `GET /market/clock` matrix (TC-02–TC-05), degraded-clock honesty (TC-08), distinct reasons (TC-09), no-regression of J-01–J-11/J-13 (TC-01, TC-11, TC-16), and anti-goal guards — confinement (TC-10), no-magic-numbers/engine-untouched (TC-11), no-fabricated-data (TC-04/TC-05/TC-08).
