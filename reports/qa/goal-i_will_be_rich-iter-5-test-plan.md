# goal-i_will_be_rich-iter-5 Functional Test Plan

**Phase:** goal-i_will_be_rich-iter-5
**Date:** 2026-06-03
**Frontend Present:** yes

## Phase Goal

Watching `SIM-BIDABS` settles the cockpit on **bid_absorption** (not seller_control) and `SIM-ASKABS` on **ask_absorption** (not buyer_control) — proving the keystone "price impact, not raw aggression" claim — rendered live in amber with absorption/refresh readouts and an absorption event-log message, while the top-bar stream-status dot reads the engine's canonical `snapshot.stream_status`. Directional journeys (J-01/J-02/J-03/J-08) must stay green.

## Test Cases

### TC-01 — J-04: SIM-BIDABS resolves to bid_absorption (browser)

**Type:** browser
**Preconditions:** Backend on :8000, frontend on :3000 with `NEXT_PUBLIC_API_URL` set.

**Steps:**
1. Navigate to `http://localhost:3000`.
2. Enter ticker `SIM-BIDABS`, click Watch.
3. Wait past warm-up for the tape state to resolve over WebSocket (no reload).
4. Read the Tape-state panel, Features panel, and Event-log panel.

**Expected outcome:** Tape state settles on **Bid Absorption** at confidence ≥ `reasonable_confidence`; `aggressive_sell_ratio` reads high while the last price does NOT move meaningfully lower; `absorption_score` and `bid_refresh_score` read elevated; event log shows an absorption message (e.g. "Large sell print absorbed" / "Bid refreshing at <price>").
**Pass criteria:** Displayed state == `bid_absorption` (label "Bid Absorption"), NOT seller_control and NOT unclear; confidence ≥ threshold; high sell ratio + flat last price; absorption_score & bid_refresh_score elevated; absorption line present in event log; update arrived live over WS.

---

### TC-02 — J-04: bid_absorption renders in amber, confirmed by probe (browser)

**Type:** browser
**Preconditions:** TC-01 reached a resolved `bid_absorption` state.

**Steps:**
1. On the resolved SIM-BIDABS view, locate the headline tape-state text and the confidence-bar fill.
2. Run `getComputedStyle` on the headline (expect `text-amber-400` color) and the confidence bar (expect `bg-amber-500` fill).
3. Probe the served stylesheet for base selectors `.text-amber-400{` and `.bg-amber-500{`, excluding `:hover`/variant forms.

**Expected outcome:** First on-screen amber render of the resolved absorption state is amber by computed style AND a base-selector rule exists.
**Pass criteria:** Computed color/background match amber values AND base-selector rules present. NOT a screenshot glance, NOT a grep-substring.

---

### TC-03 — J-05: SIM-ASKABS resolves to ask_absorption (browser)

**Type:** browser
**Preconditions:** Services up as in TC-01.

**Steps:**
1. Navigate to `http://localhost:3000`, watch `SIM-ASKABS`.
2. Wait past warm-up for resolution over WS.
3. Read Tape-state, Features, and Event-log panels.

**Expected outcome:** Tape state settles on **Ask Absorption** at confidence ≥ threshold; `aggressive_buy_ratio` high while last price does NOT move meaningfully higher; `absorption_score` and `ask_refresh_score` elevated; event log shows an absorption message (e.g. "Large buy print absorbed" / "Ask refreshing at <price>").
**Pass criteria:** Displayed state == `ask_absorption` ("Ask Absorption"), NOT buyer_control and NOT unclear; high buy ratio + flat last price; absorption_score & ask_refresh_score elevated; absorption line in event log; live amber render (confirm amber via the TC-02 probe method on this state too).

---

### TC-04 — Stream-status dot reflects canonical snapshot.stream_status (browser)

**Type:** browser
**Preconditions:** A watched ticker with an active snapshot.

**Steps:**
1. Watch a ticker; observe the top-bar dot during connecting → live.
2. `curl -s http://localhost:8000/tape/<ticker>/summary` and read `stream_status`.
3. Compare the dot color/label to the snapshot value; let a bounded sim stream exhaust and confirm the dot follows `stream_status` → closed (not a false "live").

**Expected outcome:** Dot maps from `snapshot.stream_status` (connecting/live/stale/closed) when a snapshot is present; falls back to client `connStatus` only pre-snapshot.
**Pass criteria:** Dot label/color == `summary.stream_status`; on stream exhaustion the dot no longer reads a false "live".

---

### TC-05 — Regression J-01: six panels live on SIM-BUYER (browser)

**Type:** browser
**Preconditions:** Services up.

**Steps:**
1. Watch `SIM-BUYER`; confirm all six cockpit panels render and update live over WS.

**Expected outcome:** All panels populated and updating; no errors.
**Pass criteria:** Six panels visible and live; no console/runtime errors; live dot stable.

---

### TC-06 — Regression J-02 / J-03: directional states not misrouted (browser)

**Type:** browser
**Preconditions:** Services up.

**Steps:**
1. Watch `SIM-BUYER` → confirm state resolves to **buyer_control** (green), NOT ask_absorption.
2. Watch `SIM-SELLER` → confirm state resolves to **seller_control** (rose), NOT bid_absorption.

**Expected outcome:** Directional scenarios still resolve to control states with correct coloring.
**Pass criteria:** SIM-BUYER == buyer_control (green, not ask_absorption); SIM-SELLER == seller_control (rose, not bid_absorption); live dots unaffected.

---

### TC-07 — Regression J-08: UI ≡ REST single source of truth (browser + api)

**Type:** browser
**Preconditions:** A watched absorption ticker (e.g. SIM-BIDABS) resolved.

**Steps:**
1. Read `bid_refresh_score` and the tape state/confidence shown in the UI.
2. `curl -s http://localhost:8000/tape/SIM-BIDABS/features` and `.../state`.
3. Compare UI values to REST values.

**Expected outcome:** UI values equal REST values (no client recompute).
**Pass criteria:** UI `bid_refresh_score` == `/features` value; UI tape_state/confidence == `/state` value.

---

### TC-08 — Keystone classifier guard tests (api/unit)

**Type:** api
**Preconditions:** `apps/backend/tests/test_classifier.py` present.

**Steps:**
1. Run `pytest apps/backend/tests/test_classifier.py -v`.

**Expected outcome:** High `aggressive_sell_ratio` + `sell_price_impact ≈ 0` (above −cutoff) + high `bid_refresh_score` + stable spread ⇒ **bid_absorption** (NOT seller_control, NOT unclear). High `aggressive_sell_ratio` + real negative `sell_price_impact` ⇒ **seller_control** (NOT bid_absorption). Mirror buy/ask pair. Wide spread blocks absorption (stays unclear).
**Pass criteria:** All four guard assertions pass; precedence + mutual-exclusion-on-impact verified.

---

### TC-09 — Feature engine tests (api/unit)

**Type:** api
**Preconditions:** `apps/backend/tests/test_features.py` present.

**Steps:**
1. Run `pytest apps/backend/tests/test_features.py -v`.

**Expected outcome:** `bid_refresh_score` high when bid holds under sell prints / low when it walks down; `ask_refresh_score` mirror; `absorption_score` high on high-ratio-flat-impact, low on real-impact; the existing 9 feature values unchanged by the bid/ask `add_quote` threading.
**Pass criteria:** All feature assertions pass; existing-9-unchanged assertion passes.

---

### TC-10 — Scenario + determinism tests (api/unit)

**Type:** api
**Preconditions:** `apps/backend/tests/test_scenario.py` present.

**Steps:**
1. Run `pytest apps/backend/tests/test_scenario.py -v`.

**Expected outcome:** SIM-BIDABS deterministically reaches `bid_absorption` (conf ≥ `reasonable_confidence`) within warm-up; SIM-ASKABS reaches `ask_absorption`; SIM-BUYER still buyer_control and SIM-SELLER still seller_control (no misroute); same seed ⇒ identical state/confidence per scenario.
**Pass criteria:** Both absorption scenarios reach the expected state at threshold; no directional regression; determinism assertions pass.

---

### TC-11 — API projection agreement for an absorption ticker (api)

**Type:** api
**Preconditions:** Backend running; SIM-BIDABS watched.

**Steps:**
1. `curl -s http://localhost:8000/tape/SIM-BIDABS/state`
2. `curl -s http://localhost:8000/tape/SIM-BIDABS/features`
3. `curl -s http://localhost:8000/tape/SIM-BIDABS/summary`
4. Connect `WS /stream` for SIM-BIDABS and read one snapshot.

**Expected outcome:** `/state`, `/features`, `/summary`, and `WS /stream` agree on tape_state/confidence and absorption feature values (single canonical producer/endpoint).
**Pass criteria:** tape_state, confidence, and `bid_refresh_score`/`absorption_score` identical across all four; HTTP 200 on REST.

---

### TC-12 — Error / no-fabrication paths (api)

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/tape/NOPE/state` (unknown ticker).
2. Read state for a known-but-not-watched ticker (not-watched read).
3. Inspect a silent/cold provider read (no refresh evidence).

**Expected outcome:** Unknown ticker ⇒ 400; not-watched read ⇒ 404; silent/cold provider stays honest **unclear** (absorption gate requires real `*_refresh_score` evidence, not mere absence of impact) — no fabricated absorption.
**Pass criteria:** Status codes 400 / 404 as specified; cold provider state == unclear, never an absorption state.

---

### TC-13 — Backend test suite (no regressions) (api)

**Type:** api
**Preconditions:** Backend test deps installed.

**Steps:**
1. Run the full backend test command from `.claude/project-template.md`.

**Expected outcome:** The 31-test baseline plus the new absorption tests pass; no regressions.
**Pass criteria:** Test runner exits 0; pass count ≥ 31 + new tests; zero failures.

---

### TC-14 — Features panel shows three new absorption rows (browser)

**Type:** browser
**Preconditions:** A watched ticker resolved.

**Steps:**
1. Open the Features panel and look for `absorption_score`, `bid_refresh_score`, `ask_refresh_score` rows.

**Expected outcome:** Three new rows appear with sensible labels, 3-decimal monospaced numerics, not color-by-sign; existing 9 rows unchanged; absent values show "—".
**Pass criteria:** All three rows present and formatted to 3 decimals; existing rows intact.

---

### TC-15 — Dev handoff artifact exists (artifact)

**Type:** artifact
**Preconditions:** Dev phase complete.

**Steps:**
1. Check `docs/handoffs/goal-i_will_be_rich-iter-5-dev.md` exists and is non-empty.

**Expected outcome:** Handoff file present documenting the implementation.
**Pass criteria:** File exists at the path with content.

---

## Summary

Total test cases: 15
- API tests: 6 (TC-08, TC-09, TC-10, TC-11, TC-12, TC-13)
- Browser tests: 8 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-14)
- Artifact checks: 1 (TC-15)

**Real gate:** browser J-04 (TC-01/TC-02) and J-05 (TC-03) plus regression guards (TC-05/TC-06/TC-07). A backend PASS does NOT substitute for browser verification of the absorption journeys; if browser-qa SKIPS due to a frontend HTTP 500 (corrupted `.next`), treat it as a verification-closure signal, not a pass.
