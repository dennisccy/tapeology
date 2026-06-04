# goal-i_will_be_super_rich-iter-1 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-1
**Date:** 2026-06-04
**Frontend Present:** yes

## Phase Goal

A user can pick a data source — Live / Historical / Simulated — and see the controls each mode needs; choosing a **real** mode with **no credentials configured** yields an explicit, honest **"real-data provider unavailable"** (HTTP 503 / non-cockpit panel) instead of any fabricated read, while Simulated keeps working exactly as before. Verified with **NO credentials configured**.

Conventions: backend base URL `http://localhost:8000` (QA harness may use an offset port, e.g. `:8650` — substitute as needed). Frontend `http://localhost:3000` (harness offset e.g. `:3650`). Backend tests: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`. All real-mode tests assume `ALPACA_API_KEY` / `ALPACA_API_SECRET` are **absent** from the environment.

## Test Cases

### TC-01 — Sim watch regression: no body still watches the sim engine

**Type:** api
**Preconditions:** Backend running; no Alpaca creds in env.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/watch/SIM-BUYER`
2. `curl -s -w "\n%{http_code}" http://localhost:8000/tape/SIM-BUYER/state`

**Expected outcome:** No-body POST starts the existing simulated watch unchanged; a state snapshot becomes available.
**Pass criteria:** Step 1 returns `200`; step 2 returns `200` with a JSON snapshot containing a `tape_state`/`state` field. No body required (backward compatible).

---

### TC-02 — Sim watch regression: `mode:"sim"` body watches the sim engine

**Type:** api
**Preconditions:** Backend running; no creds.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/watch/SIM-BUYER -H 'Content-Type: application/json' -d '{"mode":"sim"}'`
2. `curl -s -w "\n%{http_code}" http://localhost:8000/tape/SIM-BUYER/state`

**Expected outcome:** `{"mode":"sim"}` is treated identically to no-body — sim path, unchanged.
**Pass criteria:** Step 1 returns `200`; step 2 returns `200` with a snapshot. Behavior identical to TC-01.

---

### TC-03 — Live watch, no creds → 503 provider_unavailable

**Type:** api
**Preconditions:** Backend running; `ALPACA_API_KEY`/`ALPACA_API_SECRET` absent.

**Steps:**
1. `curl -s -w "\n%{http_code}" -X POST http://localhost:8000/watch/AAPL -H 'Content-Type: application/json' -d '{"mode":"live"}'`

**Expected outcome:** Explicit, distinct honest-failure error; no engine created; nothing synthesized.
**Pass criteria:** HTTP `503`; response JSON has `detail == "real-data provider unavailable"` **and** a machine-readable `reason == "provider_unavailable"`. NOT 500, NOT 200, NOT a snapshot.

---

### TC-04 — No engine created after rejected live watch (no fabricated snapshot)

**Type:** api
**Preconditions:** TC-03 executed (live watch on `AAPL` rejected) OR run fresh.

**Steps:**
1. `curl -s -X POST http://localhost:8000/watch/AAPL -H 'Content-Type: application/json' -d '{"mode":"live"}'` (rejected with 503)
2. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/tape/AAPL/state`

**Expected outcome:** The rejected real-mode watch left no engine/snapshot behind.
**Pass criteria:** Step 2 returns `404` (no engine, no fabricated tape state). Proves no fall-back to the simulator and no synthesized data.

---

### TC-05 — Historical watch, no creds → 503 provider_unavailable + 404 state

**Type:** api
**Preconditions:** Backend running; no creds.

**Steps:**
1. `curl -s -w "\n%{http_code}" -X POST http://localhost:8000/watch/MSFT -H 'Content-Type: application/json' -d '{"mode":"historical","start":"2026-01-02T09:30","end":"2026-01-02T10:00","speed":1}'`
2. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/tape/MSFT/state`

**Expected outcome:** Historical real mode is gated identically to live; no engine created.
**Pass criteria:** Step 1 → HTTP `503`, `detail == "real-data provider unavailable"`, `reason == "provider_unavailable"`; step 2 → `404`.

---

### TC-06 — Unknown mode → explicit 4xx, no engine created

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl -s -w "\n%{http_code}" -X POST http://localhost:8000/watch/SIM-BUYER -H 'Content-Type: application/json' -d '{"mode":"bogus"}'`
2. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/tape/SIM-BUYER/state`

**Expected outcome:** An unrecognized mode is rejected explicitly — never a silent default into sim or a real feed.
**Pass criteria:** Step 1 returns a `4xx` (`422` from a Pydantic Literal/enum, or explicit `400`) — NOT 200, NOT 503, NOT 500. Step 2 returns `404` for a previously-unwatched ticker (no engine created by the bogus request).

---

### TC-07 — `real_data_available` derived from env presence/absence (both ways)

**Type:** artifact (backend unit/integration test)
**Preconditions:** Test suite present; monkeypatch fixtures available.

**Steps:**
1. Run the backend suite: `cd apps/backend && .venv/bin/python -m pytest tests/test_real_data_gate.py -v` (or wherever the gate tests live).
2. Confirm a test monkeypatches `ALPACA_API_KEY`+`ALPACA_API_SECRET` **present** → asserts `real_data_available is True`.
3. Confirm a test with both **absent** → asserts `real_data_available is False`.

**Expected outcome:** The canonical availability boolean reflects credential presence, computed from `AlpacaAdapter().is_available()`.
**Pass criteria:** Both monkeypatched cases pass with exact `True`/`False` assertions. The boolean is NOT placed in the engine `Config` dataclass.

---

### TC-08 — Single-module credential confinement (provider-agnostic seam)

**Type:** artifact (source scan)
**Preconditions:** Repo checked out.

**Steps:**
1. `grep -rl "ALPACA_API_KEY\|ALPACA_API_SECRET" apps/backend/app/`
2. Inspect imports of the engine, API (`main.py`), and `app/providers/base.py` / `app/providers/simulated.py`.

**Expected outcome:** Vendor credential names and any vendor SDK live in exactly one module.
**Pass criteria:** Step 1 returns **exactly one** file path (the Alpaca adapter, e.g. `app/providers/adapters/alpaca.py`). The engine, API, and existing providers import no vendor SDK / no `ALPACA_*` names. A backend test asserting this confinement passes.

---

### TC-09 — `.env.example` holds names only, empty secret values (no secrets in source)

**Type:** artifact
**Preconditions:** Repo checked out.

**Steps:**
1. Read `apps/backend/.env.example`.
2. `git ls-files apps/backend/.env apps/backend/.env.example` to confirm only `.env.example` is tracked.

**Expected outcome:** Variable names documented; no key value committed; no real `.env` tracked.
**Pass criteria:** `.env.example` contains `ALPACA_API_KEY=` and `ALPACA_API_SECRET=` with **empty** values (`ALPACA_FEED=iex` non-secret default allowed). No committed file contains a non-empty key/secret value. No `.env` is git-tracked.

---

### TC-10 — Engine and canonical reads untouched (no-regression: full backend suite)

**Type:** artifact (backend test suite)
**Preconditions:** Test suite present.

**Steps:**
1. `cd apps/backend && .venv/bin/python -m pytest tests/ -v 2>&1 | tee reports/qa/goal-i_will_be_super_rich-iter-1-test.log`

**Expected outcome:** The pre-existing backend suite (68 passing per plan) stays green; engine/`/state`/`/features`/`/summary`/`/events`/`WS /stream` unchanged.
**Pass criteria:** 0 failures, 0 errors; pre-existing test count (≈68) still passes plus the new gate tests. No `git diff` touching `app/engine/*`, `app/config.py`, `app/serializers.py`, `app/providers/base.py`, `app/providers/simulated.py`, or the canonical read/stream endpoints.

---

### TC-11 — J-10: selector offers exactly three modes with per-mode control reveal

**Type:** browser
**Preconditions:** Frontend at `http://localhost:3000`; backend reachable; no creds.

**Steps:**
1. Chrome MCP: navigate to `/`.
2. Locate the data-source selector in the TopBar; read its options.
3. Select **Simulated** → observe controls.
4. Select **Live** → observe controls.
5. Select **Historical** → observe controls.
6. Screenshot each mode under `reports/qa/<phase>-evidence/`.

**Expected outcome:** Exactly three modes; each reveals its mode-specific controls; cockpit body unchanged.
**Pass criteria:** Selector shows **exactly** Live / Historical / Simulated (default Simulated). **Simulated** → ticker input + Watch. **Live** → symbol search box + market-status indicator + Watch. **Historical** → symbol search box + date/time-window picker + replay-speed control + Watch.

---

### TC-12 — J-01/J-02 regression via Simulated: SIM-BUYER → buyer_control

**Type:** browser
**Preconditions:** Frontend + backend running; no creds.

**Steps:**
1. Navigate to `/`; ensure selector is **Simulated**.
2. Enter `SIM-BUYER` in the ticker input; click **Watch**.
3. Wait for the stream to connect and panels to populate; let the state stabilize.
4. Read the tape-state panel, confidence, and price-impact readouts; screenshot.

**Expected outcome:** The full cockpit renders live values and resolves the buyer-control scenario — no regression.
**Pass criteria:** Cockpit panels populate over the WebSocket; tape state settles on **buyer_control** with confidence ≥ threshold; event log shows "Tape state changed to buyer_control". No fabricated/empty cockpit.

---

### TC-13 — J-14 no-credentials path (Live): provider-unavailable panel in place of cockpit

**Type:** browser
**Preconditions:** Frontend + backend running; no creds.

**Steps:**
1. Navigate to `/`; select **Live**.
2. Type a symbol (e.g. `AAPL`) into the symbol search box.
3. Click **Watch**; observe the result.
4. Screenshot.

**Expected outcome:** An explicit "real-data provider unavailable" panel replaces the cockpit; market-status indicator reads an honest "unavailable".
**Pass criteria:** A clearly-labeled **"real-data provider unavailable"** panel renders **in place of** the cockpit — **no** cockpit/tape panels, **no** fabricated values, **no** silent fall-back to Simulated. Market-status indicator shows "unavailable" (not a fabricated open/closed).

---

### TC-14 — J-14 no-credentials path (Historical): provider-unavailable panel

**Type:** browser
**Preconditions:** Frontend + backend running; no creds.

**Steps:**
1. Navigate to `/`; select **Historical**.
2. Type a symbol (e.g. `AAPL`); pick a date/time window and a replay speed.
3. Click **Watch**; observe; screenshot.

**Expected outcome:** Same honest non-cockpit state as Live.
**Pass criteria:** "real-data provider unavailable" panel renders in place of the cockpit; no cockpit, no fabricated data, no sim fall-back.

---

### TC-15 — Watch-lifecycle hardening: switching source/symbol tears down the prior watch

**Type:** browser
**Preconditions:** Frontend + backend running; no creds.

**Steps:**
1. Navigate to `/`; in **Simulated**, watch `SIM-BUYER` (cockpit live).
2. Without an explicit Stop, switch the data source (e.g. to **Live**) and/or start a new Watch with a different symbol.
3. Observe the UI and (if accessible) the backend watched set.

**Expected outcome:** The prior watch is implicitly torn down (`DELETE /watch/SIM-BUYER`) and its WebSocket closed before the new mode/watch begins — no orphaned backend watch/socket.
**Pass criteria:** After the switch the previous cockpit is gone (returns to idle/empty before the new mode's controls); no orphaned watch for `SIM-BUYER` remains alive (no further updates for the prior ticker; new watch starts clean).

---

## Summary

Total test cases: 15
- API tests: 6 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06)
- Browser tests: 5 (TC-11, TC-12, TC-13, TC-14, TC-15)
- Artifact checks: 4 (TC-07, TC-08, TC-09, TC-10)

Coverage map: J-10 → TC-11; J-14 no-credentials path → TC-03/04/05 + TC-13/14; J-01/J-02 regression → TC-12; sim regression → TC-01/02; honest-failure & no-fabricated-data → TC-03/04/05/13/14; no-secrets-in-source → TC-08/09; provider-agnostic seam → TC-08/10; canonical-reads-untouched → TC-10; iter-0 watch-lifecycle lesson → TC-15.
