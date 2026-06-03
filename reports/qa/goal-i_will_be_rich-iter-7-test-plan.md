# goal-i_will_be_rich-iter-7 Functional Test Plan

**Phase:** goal-i_will_be_rich-iter-7
**Date:** 2026-06-03
**Frontend Present:** yes

## Phase Goal

A user watching a ticker can press a **Stop** control that issues `DELETE /watch/{ticker}`; the live stream closes client-side, the cockpit returns to the idle/empty state with no stale numbers, and re-watching the same ticker starts a fresh (cold) read — closing the ninth and final Must-have journey (J-09).

## Test Cases

### TC-01 — DELETE /watch stops a watched ticker

**Type:** api
**Preconditions:** Backend running on `http://localhost:8000`; `SIM-BUYER` is watched (`POST /watch/SIM-BUYER` returned 200).

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/watch/SIM-BUYER`
2. `curl -s -w "\n%{http_code}" -X DELETE http://localhost:8000/watch/SIM-BUYER`

**Expected outcome:** DELETE returns HTTP 200 with body `{"ticker":"SIM-BUYER","status":"stopped"}`.
**Pass criteria:** Status code is `200` AND response JSON has `status == "stopped"` and `ticker == "SIM-BUYER"`.

---

### TC-02 — DELETE /watch on a not-watched ticker returns 404 (no fabricated success)

**Type:** api
**Preconditions:** Backend running; `NEVER-WATCHED` is not currently watched.

**Steps:**
1. `curl -s -w "\n%{http_code}" -X DELETE http://localhost:8000/watch/NEVER-WATCHED`

**Expected outcome:** HTTP 404 (honest "not watched"), no `stopped` success body.
**Pass criteria:** Status code is `404` AND body is an error detail, NOT `{"status":"stopped"}`.

---

### TC-03 — Reads of a stopped ticker return 404 (no synthesized snapshot)

**Type:** api
**Preconditions:** `SIM-BUYER` was watched then stopped via TC-01.

**Steps:**
1. For each of `state`, `features`, `events`, `summary`: `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/tape/SIM-BUYER/<read>`

**Expected outcome:** All four reads return 404 because the engine was removed from the registry.
**Pass criteria:** Each of the four endpoints returns `404`; no endpoint returns a 200 with synthesized data.

---

### TC-04 — Fresh WS connect to a stopped ticker is rejected (4404)

**Type:** api
**Preconditions:** `SIM-BUYER` watched then stopped (TC-01).

**Steps:**
1. Open a new WebSocket to `ws://localhost:8000/tape/SIM-BUYER/stream` (e.g. via a short Python `websockets` snippet or `websocat`).
2. Capture the close code.

**Expected outcome:** Connection is closed with application code `4404` (`manager.get(ticker)` is `None`).
**Pass criteria:** WS close code equals `4404`.

---

### TC-05 — Re-POST /watch after stop yields a fresh cold-start snapshot

**Type:** api
**Preconditions:** `SIM-BUYER` watched then stopped (TC-01).

**Steps:**
1. `curl -s -w "\n%{http_code}" -X POST http://localhost:8000/watch/SIM-BUYER`
2. `curl -s http://localhost:8000/tape/SIM-BUYER/state` immediately after.

**Expected outcome:** POST returns 200; the new state reflects a cold start (no carried-over event count / no leftover closed status) — a genuinely fresh engine.
**Pass criteria:** POST status `200` AND the fresh read returns 200 with a cold-start state (event/processed count consistent with a brand-new watch, not the pre-stop accumulated count).

---

### TC-06 — Unit/integration backend suite passes (incl. new stop/DELETE tests)

**Type:** artifact
**Preconditions:** Repo at iter-7 dev complete.

**Steps:**
1. Run the backend test suite (`apps/backend/tests/`).
2. Confirm the prior 61 tests stay green and new `WatchManager.stop()` / re-watch-fresh / DELETE-route tests are present and pass.

**Expected outcome:** All backend tests pass; new tests cover stop (cancel feeder, set `stream_status="closed"`, remove engine → `get()` None), re-watch returns a different engine instance starting cold, DELETE 200-then-404/4404, not-watched → 404, and the determinism guard (watch→stop→re-watch identical fresh snapshot).
**Pass criteria:** Test exit code `0`; pass count ≥ 61 plus the new cases; 0 failures/errors.

---

### TC-07 — Determinism: watch → stop → re-watch matches first-ever watch

**Type:** artifact
**Preconditions:** Seeded sim ticker.

**Steps:**
1. Confirm a unit test asserts `watch(t) → stop(t) → watch(t)` produces an identical cold-start snapshot to a first-ever watch of `t`.

**Expected outcome:** No state leakage across the stop boundary; identical deterministic snapshot.
**Pass criteria:** The determinism guard test exists and passes.

---

### TC-08 — Untouched-file guard (anti-goal)

**Type:** artifact
**Preconditions:** iter-7 diff available (`git diff`).

**Steps:**
1. Verify `apps/backend/app/classifier.py`, `features.py`, `config.py`, and everything under `apps/backend/app/providers/` are byte-untouched in the iter-7 diff.

**Expected outcome:** Teardown is purely WatchManager + API + frontend; no classifier/feature/provider/config change.
**Pass criteria:** `git diff` shows zero changes to those four targets; no new config/threshold literals introduced.

---

### TC-09 — Frontend build passes

**Type:** artifact
**Preconditions:** Frontend deps installed.

**Steps:**
1. `cd apps/frontend && npm run build`

**Expected outcome:** Production build succeeds with the new Stop button, `stopTicker`, and `handleStop` wiring.
**Pass criteria:** Build exits `0`; no type/lint errors.

---

### TC-10 — J-09 browser: live → Stop → idle (the real gate)

**Type:** browser
**Preconditions:** Backend + frontend running (`http://localhost:3000`). Optionally `TAPEOLOGY_FEED_PACE=0.12` to widen the live window.

**Steps:**
1. Navigate to `http://localhost:3000`. Watch `SIM-BUYER` from cold; wait for status dot **live** and cockpit panels populated (screenshot: cockpit-live).
2. Press **Stop** promptly while the stream is still live.
3. Observe the body and status dot (screenshot: post-Stop-idle).

**Expected outcome:** Body switches to `<IdleState/>` ("No ticker watched"); status dot returns to **idle**; no further snapshot updates arrive (WS closed client-side via `setTicker(null)`).
**Pass criteria:** "No ticker watched" idle state is visible, dot is idle, the Stop button is gone, and the panels show no stale/frozen numbers. *(If the bounded stream exhausts before the click, the idle-return assertion still holds.)*

---

### TC-11 — J-09 browser: re-watch repopulates from cold (fresh read)

**Type:** browser
**Preconditions:** Continues from TC-10 (idle state after Stop).

**Steps:**
1. Re-watch the same `SIM-BUYER`.
2. Observe cockpit transition (screenshot: re-watch-fresh).

**Expected outcome:** Cockpit repopulates from a cold start (connecting → live → values) — a genuinely fresh read, not a frozen/closed leftover.
**Pass criteria:** Status progresses through connecting/live and panels repopulate with fresh values; not stuck on a closed/frozen frame.

---

### TC-12 — Stop button visibility & static class

**Type:** browser
**Preconditions:** Frontend running.

**Steps:**
1. In idle state, confirm no Stop button is present in the top bar.
2. Watch a ticker; confirm a **Stop** button appears next to the watched-ticker label.
3. (Optional) Inspect the served bundle / element to confirm a **static** Tailwind color class (e.g. rose ghost) is applied — not a runtime-built class that gets dropped.

**Expected outcome:** Stop is rendered only while watching; its color class is statically present in the bundle.
**Pass criteria:** Button absent in idle, present while watching; if asserted, the rose/slate color class is present (color is not load-bearing for J-09 acceptance).

---

### TC-13 — Required-still-passing journeys (J-01, J-02, J-08) — no regression

**Type:** browser
**Preconditions:** Backend + frontend running.

**Steps:**
1. J-01: watch a sim ticker → live cockpit renders.
2. J-02: re-watched `SIM-BUYER` re-resolves to `buyer_control` with positive `buy_price_impact` (proves the fresh read).
3. J-08: spot-check that a displayed value in the UI equals the corresponding `GET /tape/SIM-BUYER/...` REST value (UI ≡ REST, no recomputation).

**Expected outcome:** All three remain green; J-03–J-07 not visibly regressed.
**Pass criteria:** J-01 cockpit renders; J-02 scenario label is `buyer_control` with positive buy price impact; J-08 UI value matches REST exactly.

---

### TC-14 — Frontend stopTicker treats 404 as effectively-stopped

**Type:** browser
**Preconditions:** Frontend running; a way to trigger Stop when the backend already considers the ticker not-watched (e.g. stream already exhausted/removed).

**Steps:**
1. Trigger Stop in a state where `DELETE` returns 404.

**Expected outcome:** UI still returns to the idle state (404 = effectively-stopped), error cleared.
**Pass criteria:** Cockpit empties to `<IdleState/>` despite the 404; no error banner left displayed.

---

## Summary

Total test cases: 14
- API tests: 5 (TC-01 – TC-05)
- Browser tests: 5 (TC-10 – TC-14)
- Artifact checks: 4 (TC-06 – TC-09)
