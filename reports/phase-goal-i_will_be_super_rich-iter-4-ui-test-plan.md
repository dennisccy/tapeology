# Phase goal-i_will_be_super_rich-iter-4 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-4
**Date:** 2026-06-04
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650 (CHAIN_FRONTEND_URL)

---

## Scope & Context

This iteration changed **0 frontend files**. The single screen (`/`) is unchanged code;
what changed is the *observable behavior* of the existing **Live "Watch"** path — the backend
now streams a real live feed instead of refusing with `provider_not_implemented` (503).

Test cases below cover the 7 affected/re-verify surfaces from the UI surface map.

**Operator note on the live feed:** A *real* live watch (dot turns emerald `live`, then amber
`stale` on a feed lull) can only be exercised during US market hours **with Alpaca credentials
configured**. Today (2026-06-04) the market may be closed and/or credentials may be absent. Where
that is the case, the live happy-path (UT-02) and stale-flip (UT-09) cannot be browser-verified in
loop — they fall back to the honest non-cockpit states (UT-05, UT-06), and the live/stale flip is
covered by the hermetic backend tests (functional TC-01/TC-02). This is expected, **not a FAIL**.

---

## Test Cases

<!-- UT-XX prefix distinguishes these from the functional plan's TC-XX IDs. -->

---

### UT-01 — Home screen loads with mode controls (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error overlay
- The TopBar is visible with a status dot (initially `closed`/idle, rose or grey)
- A data-source / mode selector control is visible (offering sim / historical / live)
- No uncaught errors in the browser console

---

### UT-02 — Live watch of a real symbol mounts the cockpit (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — Live mode "Watch" button

**Preconditions:**
- US market is **open** AND Alpaca credentials are configured in the backend
- (If market is closed or creds absent, run UT-05 / UT-06 instead — this path is gated)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Open the data-source selector and choose **Live**
3. Type `F` into the symbol search field and select/confirm `F` as the symbol
4. Click the **Watch** button

**Expected Result:**
- The `<Cockpit>` mounts: the tape panels (tape state, confidence, recent trades) appear
- An error banner does **NOT** appear (no `provider unavailable`, no `market is closed`)
- The TopBar status dot is **emerald** (`live`)
- The watched-source label in the TopBar reads exactly `scenario: live F`
- Network: `POST /watch/F` returned `{ "scenario": "live F", "status": "watching" }` (HTTP 200)

---

### UT-03 — Live mode reveals symbol search + market-status indicator (smoke / re-verify)

**Type:** smoke
**Priority:** P1
**Surface:** `/` — Mode selector → Live controls (`SymbolSearch`, `MarketStatusIndicator`)

**Preconditions:**
- Frontend running at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650`
2. Open the data-source selector and choose **Live**

**Expected Result:**
- A symbol search input field becomes visible
- The `MarketStatusIndicator` renders a status — either **open**, or **closed** with a next-open time
- No error overlay appears just from switching to Live mode

---

### UT-04 — Symbol search filters and fills the symbol box (happy path / re-verify, J-13)

**Type:** happy-path
**Priority:** P2
**Surface:** `/` — `SymbolSearch` in Live mode

**Preconditions:**
- Frontend running; Live mode selected (per UT-03)

**Steps:**
1. In Live mode, click the symbol search field
2. Type `AAP` into the field
3. Wait for the suggestion list to populate

**Expected Result:**
- A list of matching symbols appears (e.g. `AAPL` among the suggestions)
- Clicking a suggestion (e.g. `AAPL`) fills the symbol box with that ticker
- The search does not crash or show an empty/error list for a valid prefix

---

### UT-05 — Live + missing credentials → honest "provider unavailable" (error)

**Type:** error
**Priority:** P2
**Surface:** `/` — Live "Watch" button (no-credentials path)

**Preconditions:**
- Backend running **without** Alpaca credentials (adapter `is_available()` → False)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Choose **Live** mode
3. Enter symbol `AAPL`
4. Click **Watch**

**Expected Result:**
- The cockpit does **NOT** mount (no tape panels)
- An explicit honest message referencing **provider unavailable** is shown to the user
- Network: `POST /watch/AAPL` returned HTTP **503** with code `provider_unavailable`
- No fabricated/simulated cockpit appears as a fallback

---

### UT-06 — Live + market closed → honest "market is closed" with next open (error)

**Type:** error
**Priority:** P2
**Surface:** `/` — Live "Watch" button (market-closed path)

**Preconditions:**
- Backend running **with** credentials, but the market clock reports closed (e.g. off-hours)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Choose **Live** mode
3. Enter symbol `AAPL`
4. Click **Watch**

**Expected Result:**
- The cockpit does **NOT** mount
- An explicit **market is closed** message is shown, including the next open time
- Network: `POST /watch/AAPL` returned HTTP **409** with code `market_closed` and a `next_open` value
- No fabricated cockpit appears

---

### UT-07 — Sim mode still classifies a scenario (regression, J-01/J-02)

**Type:** regression
**Priority:** P1
**Surface:** `/` — Sim mode Watch

**Preconditions:**
- Frontend + backend running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Choose **Sim** mode in the data-source selector
3. Select the **SIM-BUYER** scenario
4. Click **Watch**
5. Observe the cockpit tape state

**Expected Result:**
- The cockpit mounts and the tape state reads `buyer_control`
- The confidence bar is populated (non-empty)
- Behavior is identical to before this iteration (sim path is a verified 0-line diff)

---

### UT-08 — Historical AAPL replay still populates (regression, J-11)

**Type:** regression
**Priority:** P1
**Surface:** `/` — Historical mode Watch

**Preconditions:**
- Frontend + backend running; historical AAPL fixture present

**Steps:**
1. Navigate to `http://localhost:3650`
2. Choose **Historical** mode
3. Enter `AAPL` (committed fixture window)
4. Click **Watch**
5. Observe the cockpit

**Expected Result:**
- The cockpit mounts and shows non-empty state/features for the AAPL historical replay
- No error banner; behavior is identical to before this iteration

---

### UT-09 — Live status dot flips live → stale → live on a feed lull (happy path, J-15)

**Type:** happy-path
**Priority:** P2
**Surface:** `/` — TopBar status dot (`STREAM_DOT` reading `snapshot.stream_status`)

**Preconditions:**
- A real live watch is running and emerald `live` (per UT-02) — market open + creds
- A naturally quiet symbol or a quiet moment beyond `stale_gap_seconds` (default 10s) can occur
- (If a live watch cannot be started in loop, this is covered by functional TC-02 — not a FAIL)

**Steps:**
1. With a live watch of `F` running and the dot emerald (`live`), stop interacting and watch the TopBar
2. Wait until no live trade/quote has arrived for longer than the stale-gap window (~10s+)
3. Observe the status dot
4. Wait for real events to resume (e.g. new trades print)

**Expected Result:**
- During the lull the dot turns **amber** (`stale`)
- The recent-trades count does **NOT** increase during the lull (no fabricated trades)
- When real events resume the dot returns to **emerald** (`live`)

---

### UT-10 — Stop / switch tears down the live watch cleanly (happy path / teardown)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — Cockpit teardown (`teardownActiveWatch` → `DELETE /watch/<SYM>`)

**Preconditions:**
- A live watch (or any watch) is running and the cockpit is mounted

**Steps:**
1. With a watch running, click the **Stop** button (or switch to a different symbol/mode and Watch)
2. Observe the cockpit and the status dot

**Expected Result:**
- The cockpit clears (tape panels disappear) and the status dot goes to `closed`
- A subsequent `GET /watch/<SYM>/state` returns **404** (no orphaned watch)
- No leftover/leaked stream — re-watching the same symbol starts cleanly

---

### UT-11 — Live mode is discoverable from the mode selector (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/` — data-source / mode selector

**Preconditions:**
- Frontend running at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650`
2. Locate and open the data-source / mode selector from the home screen (within 2 clicks)

**Expected Result:**
- A **Live** option is clearly labelled and selectable in the selector
- Choosing it reveals the Live controls (symbol search + market-status indicator) without extra navigation
- The label is unambiguous (distinguishable from sim / historical)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home screen loads with mode controls | smoke | P1 | `/` |
| UT-02 | Live watch mounts cockpit (live dot) | happy-path | P1 | `/` Live Watch |
| UT-03 | Live mode reveals search + market indicator | smoke | P1 | `/` mode selector |
| UT-04 | Symbol search filters & fills | happy-path | P2 | `/` SymbolSearch |
| UT-05 | Live + no creds → provider unavailable | error | P2 | `/` Live Watch |
| UT-06 | Live + market closed → market closed | error | P2 | `/` Live Watch |
| UT-07 | Sim SIM-BUYER → buyer_control | regression | P1 | `/` Sim Watch |
| UT-08 | Historical AAPL replay populates | regression | P1 | `/` Historical Watch |
| UT-09 | Status dot live → stale → live | happy-path | P2 | `/` TopBar dot |
| UT-10 | Stop/switch tears down cleanly | happy-path | P1 | `/` teardown |
| UT-11 | Live mode discoverable | ux | P3 | `/` mode selector |

**P1 tests must all pass for the browser QA verdict to be PASS.**

**Gated-path caveat:** UT-02 and UT-09 require market-open + credentials. If unavailable in loop,
they are SKIPPED (not FAILED) and their substance is covered by hermetic functional tests
TC-01/TC-02; UT-05/UT-06 then verify the honest non-cockpit states on the real path instead.
