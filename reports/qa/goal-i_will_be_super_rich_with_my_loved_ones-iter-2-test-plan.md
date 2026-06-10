# Goal Iteration 2 Functional Test Plan — Thesis Declaration with Honest Validation

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-2  
**Date:** 2026-06-10  
**Frontend Present:** yes

## Phase Goal

A user watching a ticker can declare a thesis (setup × direction × required invalidation) in the new cockpit thesis strip and see it live — frozen expected-behaviour statements with honest statuses and a `pending` verdict — with every incoherent input rejected explicitly (404/409/422), never silently coerced.

---

## Test Cases

### TC-01 — Declare absorption_reversal long thesis on SIM-BIDABS and observe active display

**Type:** browser  
**Preconditions:** Backend and frontend services running; SIM-BIDABS watched and cockpit populated with live state and features; tape has reached bid_absorption state (absorption_score elevated, bid_refresh_score elevated, last price stable or moving slowly downward despite high aggressive sell volume).

**Steps:**
1. Open the cockpit on `http://localhost:3000` with SIM-BIDABS watched
2. Locate the thesis strip (one-line declare affordance, positioned between the price chart and the panel grid)
3. Click the declare affordance to open the form
4. Select setup type `absorption_reversal` from the dropdown (fetched from `GET /research/taxonomy`)
5. Select direction `long`
6. Enter invalidation price (a price **below** the current last, matching the thesis spec's wrong-side validation rule)
7. Submit the form
8. Wait for the response and observe the active thesis display
9. Verify the WS frame's `thesis` key by opening browser developer tools and inspecting the latest WebSocket message

**Expected outcome:** The form submits, the backend returns HTTP 201 (or 200), and the thesis strip transitions to active-thesis display showing:
- Setup type: `absorption_reversal` in mono
- Direction: `long` in mono
- Invalidation: the submitted price in mono
- Three expected-behaviour statements with status badges (met / not-yet / violated), each status evaluated from live engine features
- Verdict badge: `pending` in slate color
- Bound source + data_feed stamp (e.g., "SIM scenario SIM-BIDABS, feed: sim")
- No page reload occurs

**Pass criteria:** 
- HTTP 201/200 response from `POST /research/thesis`; response body contains all thesis fields (id, setup_type, direction, invalidation_price, frozen statements, verdict)
- Active thesis strip displays all five elements (setup, direction, invalidation, statements with statuses, verdict badge) matching the response exactly
- `GET /research/thesis/active?ticker=SIM-BIDABS` returns the identical thesis projection as the WS frame's `thesis` key (byte-for-byte equal, verified via REST probe with server up)
- No paint/layout shift in the panel grid below the strip (J-68 strip-idle clause maintained)
- Each statement status is derived from EXISTING engine features only (absorption_score, bid_refresh_score, state) — no new indicators

---

### TC-02 — POST /research/thesis rejects unwatched ticker with 404

**Type:** api  
**Preconditions:** Backend service running; no active watch on `UNKNOWN-TICKER`.

**Steps:**
1. Run: `curl -X POST http://localhost:8000/research/thesis -H "Content-Type: application/json" -d '{"ticker":"UNKNOWN-TICKER","setup_type":"absorption_reversal","direction":"long","invalidation_price":99.50}'`
2. Capture the HTTP status code and response body

**Expected outcome:** HTTP 404 with a JSON error body: `{"detail":"Ticker not watched"}` or equivalent

**Pass criteria:** Status code is exactly 404; response body includes a message indicating the ticker is not watched; nothing is persisted to the journal store

---

### TC-03 — POST /research/thesis rejects wrong-side invalidation with 422

**Type:** api  
**Preconditions:** Backend service running; SIM-BIDABS watched with current last price = 100.50 (or fetch live via `GET /tape/SIM-BIDABS/state` to confirm).

**Steps:**
1. Identify the current last price (via REST probe)
2. For a **long** thesis: submit invalidation price **above** current last (e.g., 101.00 if last is 100.50)
3. Run: `curl -X POST http://localhost:8000/research/thesis -H "Content-Type: application/json" -d '{"ticker":"SIM-BIDABS","setup_type":"absorption_reversal","direction":"long","invalidation_price":101.00}'`
4. Capture HTTP status code and error message

**Expected outcome:** HTTP 422 with a JSON error body containing a message like `"invalidation price must be below current last for long"` or equivalent

**Pass criteria:** Status code is exactly 422; error message explicitly names the violation (wrong side / invalidation must be below / above); nothing is persisted; the thesis strip shows the error inline without creating a thesis

---

### TC-04 — POST /research/thesis rejects level_break without level_price with 422

**Type:** api  
**Preconditions:** Backend service running; SIM-BIDABS watched.

**Steps:**
1. Run: `curl -X POST http://localhost:8000/research/thesis -H "Content-Type: application/json" -d '{"ticker":"SIM-BIDABS","setup_type":"level_break","direction":"long","invalidation_price":99.00}'` (no `level_price` field)
2. Capture HTTP status code and response body

**Expected outcome:** HTTP 422 with an error message: `"level_price is required for level_break"` or equivalent

**Pass criteria:** Status code is exactly 422; error message names the missing field; nothing is persisted

---

### TC-05 — POST /research/thesis rejects absorption_reversal with level_price with 422

**Type:** api  
**Preconditions:** Backend service running; SIM-BIDABS watched.

**Steps:**
1. Run: `curl -X POST http://localhost:8000/research/thesis -H "Content-Type: application/json" -d '{"ticker":"SIM-BIDABS","setup_type":"absorption_reversal","direction":"long","invalidation_price":99.00,"level_price":101.00}'`
2. Capture HTTP status code and response body

**Expected outcome:** HTTP 422 with an error message: `"level_price is forbidden for absorption_reversal"` or equivalent

**Pass criteria:** Status code is exactly 422; error message names the forbidden field; nothing is persisted

---

### TC-06 — POST /research/thesis rejects duplicate active thesis with 409

**Type:** api  
**Preconditions:** Backend service running; SIM-BIDABS watched; an active thesis already declared on SIM-BIDABS.

**Steps:**
1. Declare the first thesis (via REST or browser): absorption_reversal / long / invalidation 99.50
2. Declare a second thesis on the same ticker (via REST): trend_continuation / short / invalidation 101.50
3. Capture HTTP status code and response body

**Expected outcome:** HTTP 409 with an error message: `"An active thesis already exists on this ticker"` or equivalent

**Pass criteria:** Status code is exactly 409; error message explicitly states a thesis exists; second thesis is not persisted; the strip shows the error inline

---

### TC-07 — Journal store writes frozen entry context and statements at creation

**Type:** artifact  
**Preconditions:** Backend service running; SIM-BIDABS watched; a thesis declared (absorption_reversal / long).

**Steps:**
1. Query the backend's journal store (SQLite) directly or via an internal endpoint: fetch the thesis record from the `theses` table by ticker and id
2. Verify the JSON fields: `entry_context`, `expected_statements`, `created_at`, `source_identity`, `data_feed`, `config_fingerprint`
3. Change the backend config (e.g., increase a classifier threshold) and watch the same ticker again
4. Declare a second thesis on a **new ticker** with the changed config
5. Compare the two stored `config_fingerprint` values

**Expected outcome:** The thesis row contains:
- `entry_context` (JSON): state, confidence, last, spread, primary-window features captured at creation time
- `expected_statements` (JSON list): three frozen statements with label, description (derived from setup type and direction)
- `source_identity`: the scenario descriptor ("SIM-BIDABS" for sim; exact window for historical; live SYMBOL for live) — NOT the bare ticker string
- `data_feed`: "sim" (for SIM-BIDABS)
- `config_fingerprint`: a hash of the entire config
- A second thesis with changed config has a **different** `config_fingerprint`
- No analyst-determined `risk_flags` field (omitted per the honesty constraint; it arrives in J-49)

**Pass criteria:** All five fields present and non-null in the store; `config_fingerprint` changes when config changes; `source_identity` is scenario-aware (not bare ticker); statements match the expected schema

---

### TC-08 — Verdict timeline starts with pending event at creation, persists append-only

**Type:** artifact  
**Preconditions:** Backend service running; SIM-BIDABS watched; a thesis just declared.

**Steps:**
1. Query the `verdict_events` table in the journal store for the thesis id
2. Verify the first (and only, since the thesis is new) event has: verdict = "pending", published_at >= created_at, evidence (empty or null), tape_state, confidence, last, rule_first_true (null for pending)
3. Within the same SQL session, attempt an UPDATE or DELETE on the verdict_events row — this should fail (repository exposes no update/delete)
4. Stop the watch or let the stream end naturally
5. Query the table again — expect an additional `expired(reason)` event appended

**Expected outcome:** 
- Initial verdict_events row: `{verdict: "pending", logical_ts: ..., published_at: ..., tape_state: ..., confidence: ...}`
- Attempt to UPDATE or DELETE fails (no repository method; if direct SQL works, note the defect)
- After stream end: a second row with `{verdict: "expired", evidence: "stream ended" or similar}`
- The timeline is append-only: events only grow, never recomputed or rewritten

**Pass criteria:** Initial pending event recorded; append-only enforced at the repository level; second expired event appended on stream end; no update/delete method exposed

---

### TC-09 — Equivalence test: engine outputs byte-identical with real research monitor attached

**Type:** artifact  
**Preconditions:** Backend source code and test suite available; `test_observer_equivalence.py` extended from iter-1.

**Steps:**
1. Run the extended equivalence test: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py -v`
2. Verify the test runs with three monitor configurations:
   - Benign monitor (attached, no thesis declared)
   - Real research monitor (attached, no thesis declared)
   - Throwing monitor (attached, raises an exception on every event)
3. Compare the engine's `serialize_stream()` output (state, confidence, features, history markers) for the same event stream across all three configurations

**Expected outcome:** The engine outputs are byte-identical across benign, real, and throwing monitors (the throwing monitor fails gracefully with `monitor_status: failed`, but does not corrupt the tape snapshot).

**Pass criteria:** Test passes (all assertions hold); engine `serialize_stream` and `serialize_history` projections are byte-identical with or without the real monitor; on observer exception, the feed continues and `monitor_status: failed` is surfaced in the thesis projection

---

### TC-10 — Thesis strip idles as a single declare affordance; J-68 strip-idle clause holds

**Type:** browser  
**Preconditions:** Backend and frontend services running; SIM-BIDABS watched; no thesis declared.

**Steps:**
1. Visit the cockpit at `http://localhost:3000` with SIM-BIDABS watched
2. Verify the thesis strip is rendered as a **single-line declare affordance** (not expanded; no form visible)
3. Verify the panel grid (tape state, features, event log) is laid out normally below the strip
4. Spot-check the price chart (J-17): confirm candlesticks are rendered with the correct bar size selector
5. Spot-check pause/resume controls (J-19): confirm they are visible and functional
6. Scroll the page or resize the viewport — confirm the strip does not reflow or shift the panel grid
7. Declare a thesis by clicking the affordance, filling the form, and submitting
8. Verify the strip expands in place to show the active thesis, and the panel grid **does not reflow**

**Expected outcome:** The strip occupies a fixed minimal height when idle; clicking it opens the form without shifting the grid below; submitting transitions the strip to active display in place; the grid remains at the same vertical position.

**Pass criteria:** Strip renders as a single line (one affordance text + button) when idle; no grid reflow occurs; form opens in-strip or as a modal overlay, not at a new position; grid position is unchanged after thesis creation

---

### TC-11 — REST GET /research/thesis/active equals WS thesis key verbatim with server up

**Type:** api  
**Preconditions:** Backend service running; SIM-BIDABS watched with an active thesis declared (absorption_reversal / long).

**Steps:**
1. Start a WebSocket client and subscribe to `WS /tape/SIM-BIDABS/stream`
2. Capture the latest frame and extract the `thesis` key
3. In a separate HTTP request, run: `curl http://localhost:8000/research/thesis/active?ticker=SIM-BIDABS`
4. Compare the REST response body with the WS `thesis` key

**Expected outcome:** The REST response (with trailing null vs WS envelope differences stripped) matches the WS `thesis` key exactly — same thesis id, setup_type, direction, invalidation_price, statements, verdict, source, data_feed, monitor_status.

**Pass criteria:** REST projection == WS `thesis` key (byte-for-byte, after envelope/format normalization); same projection function serves both endpoints, guaranteed by construction

---

### TC-12 — Journal store persists theses and verdict_events; journal store schema is versioned

**Type:** artifact  
**Preconditions:** Backend service running; SQLite journal store exists at the configured DB path; a thesis declared on SIM-BIDABS.

**Steps:**
1. Inspect the SQLite schema: `.schema` in sqlite3 CLI or via introspection query
2. Verify the `schema_version` table/field exists and holds a version number (e.g., 1)
3. Verify these tables exist: `theses`, `verdict_events`, `hints`, `actions`, `studies`, `study_occurrences`
4. Verify `verdict_events` has a unique constraint or primary key (append-only guarantee)
5. Stop the backend process cleanly
6. Start it again and query the store for the previously declared thesis
7. Verify the thesis and its verdict events are still present (persistence survived restart)

**Expected outcome:** 
- `schema_version` table/field present, version = 1 (or higher in later iterations)
- All seven required tables present
- `verdict_events` has a primary key or unique constraint (append-only at schema level)
- Thesis and verdict_events survive a backend restart (journal persists)

**Pass criteria:** Schema versioned; all tables present; verdict_events immutable at schema level; records persist across restarts

---

### TC-13 — GET /research/taxonomy returns setup catalog with per-setup level requirements

**Type:** api  
**Preconditions:** Backend service running.

**Steps:**
1. Run: `curl http://localhost:8000/research/taxonomy`
2. Parse the JSON response and extract the `setups` array
3. Verify each setup object has: name, description, statement_templates (array), level_required (boolean)
4. Check specific setups:
   - `absorption_reversal`: level_required = false
   - `trend_continuation`: level_required = false
   - `level_break`: level_required = true
   - `failed_move_fade`: level_required = true
5. Verify the response also includes `directions` enum (long, short) and `verdicts` enum (pending, confirming, weakening, rejecting, invalidated)

**Expected outcome:** HTTP 200 with a JSON object containing:
- `setups`: [{ name, description, statement_templates, level_required }, ...]
- `directions`: [{ value: "long", display: "Long" }, { value: "short", display: "Short" }]
- `verdicts`: [{ value: "pending", display: "Pending", color: "slate" }, ...]
- No hardcoded labels in the frontend; all labels sourced from this endpoint

**Pass criteria:** All four setups present with correct level_required flags; directions and verdicts enums complete; response is the single source of truth for the frontend's taxonomy-driven form

---

### TC-14 — Minimal lifecycle honesty: thesis auto-expires on stream end or stop

**Type:** browser + artifact  
**Preconditions:** Backend and frontend services running; SIM-BIDABS watched with an active thesis declared.

**Steps:**
1. Observe the active thesis strip on the frontend
2. Via API or browser UI, click the **Stop** button to end the watch
3. Verify the frontend reflects the stop (the cockpit clears or shows a "stopped" state)
4. Query the journal store: fetch the thesis's verdict_events timeline
5. Verify the final event has `verdict: "expired"` and `evidence: "stream ended"` or similar

**Expected outcome:** Upon stream end (via stop or feeder failure), the thesis is auto-resolved with an `expired` verdict and a final timeline event appended. The thesis is no longer "active" — the next `GET /research/thesis/active?ticker=SIM-BIDABS` returns `thesis: null`.

**Pass criteria:** Stream end triggers thesis expiry; `verdict: "expired"` event appended to timeline; `GET /research/thesis/active` returns null after expiry; the thesis is read-only (no further mutations)

---

### TC-15 — Startup sweep: stale active theses left in DB are resolved expired on backend restart

**Type:** artifact  
**Preconditions:** Backend service running; SIM-BIDABS watched with an active thesis declared; the thesis left in the DB with verdict = "pending" (simulating an unclean shutdown).

**Steps:**
1. Query the journal store: confirm the thesis has `verdict_status: "active"` or `verdict: "pending"` with no `expired` event in the timeline
2. Stop the backend process (kill -9 or hard kill to skip graceful shutdown)
3. Restart the backend
4. Query the thesis again: check the verdict_events timeline

**Expected outcome:** On restart, the startup sweep resolves any DB row left with an active status to `expired` with an event like `"startup recovery"` or `"found active on restart"`. The thesis is no longer considered active.

**Pass criteria:** Startup sweep runs on backend init; orphaned active theses are resolved to expired; timeline records the recovery event

---

## Summary

**Total test cases:** 15  
**API tests:** 8 (TC-02, TC-03, TC-04, TC-05, TC-06, TC-11, TC-13, and parts of TC-01)  
**Browser tests:** 4 (TC-01, TC-10, TC-12 verify, TC-14 verify)  
**Artifact/integration tests:** 5 (TC-07, TC-08, TC-09, TC-12, TC-15)  

**Coverage:**
- Thesis declaration happy path (TC-01)
- All rejection paths: unwatched (TC-02), wrong-side invalidation (TC-03), missing level (TC-04), forbidden level (TC-05), duplicate active (TC-06)
- Data integrity: frozen entry context + statements (TC-07), append-only verdict timeline (TC-08), equivalence with observer (TC-09)
- Frontend UX: strip idle state and J-68 compliance (TC-10), REST == WS projection (TC-11)
- Persistence + lifecycle: schema versioning (TC-12), auto-expiry on stream end (TC-14), startup sweep (TC-15)
- Taxonomy completeness (TC-13)

All test cases are grounded in the phase spec's explicit acceptance criteria and testing requirements (lines 94–107 of the phase spec).
