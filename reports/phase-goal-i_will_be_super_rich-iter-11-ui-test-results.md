# Phase goal-i_will_be_super_rich-iter-11 — UI Test Results

**Phase:** goal-i_will_be_super_rich-iter-11
**Date:** 2026-06-07
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

**Overall:** 14/16 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Cockpit page loads without errors | smoke | P1 | Page renders with mode selector and symbol input, no error | Page loaded; "Live", "Historical", "Simulated" buttons and symbol input visible; no error banner | PASS | `UT-01-initial.png` |
| UT-02 | Symbol search shows results for two-character query | happy-path | P1 | Single char "A" shows no suggestions; "AA" shows AA-prefixed suggestions | Single char "A" shows 20 dropdown suggestions (SYMBOL_SEARCH_MIN_QUERY=1, not 2); "AA" shows AA-prefixed suggestions correctly | FAIL | `UT-02-single-char-A-dropdown.png`, `UT-02-two-char-AA-results.png` |
| UT-03 | Rapid typing shows only final query results | happy-path | P1 | Only "AAP"-matching tickers appear after typing "TS" then "AAP" quickly | Dropdown showed 12 AAP-prefixed symbols; no TSLA/TS-prefixed tickers appeared in results | PASS | `UT-03-rapid-type-result.png` |
| UT-04 | First search after backend restart responds within one second | happy-path | P1 | Dropdown suggestions appear within 1 second of typing "AAPL" | Dropdown appeared in ~60ms; AAPL was first suggestion; no multi-second stall | PASS | `UT-04-aapl-fast-response.png` |
| UT-05 | Aborted search leaves no stuck "Searching..." indicator | validation | P2 | TSLA suggestions appear; no stuck spinner or error banner | TSLA dropdown showed 20 results; no "Searching..." text; no error banner | PASS | `UT-05-tsla-no-stuck-spinner.png` |
| UT-06 | Oversized Historical window shows actionable timeout error | error | P1 | Failure panel shows "try a shorter range"; no cockpit data | Error "that window is very high-volume — try a shorter range" appeared; cockpit showed "No ticker watched" | PASS | `UT-06-timeout-error.png` |
| UT-07 | Historical watch cockpit populates with real values quickly | happy-path | P1 | Non-idle tape state and real feature values within ~10s | Within 2s: cockpit populated with TSLA data; tape state "Unclear" confidence 0.200; full features panel with real values; recent trades visible | PASS | `UT-07-cockpit-populated.png` |
| UT-08 | Re-watching identical Historical window is near-instant | happy-path | P1 | Cockpit repopulates in under 2 seconds on second watch | Confidence visible in ~131ms on re-watch; well under 2 second target; stream went live immediately | PASS | `UT-08-rewatch-cache-hit.png` |
| UT-09 | Vendor hiccup produces empty dropdown with no error banner | error | P2 | "ZZZ" shows empty dropdown; no error banner; no stuck spinner | Empty dropdown (0 li items); no red error banner; input remained responsive | PASS | `UT-09-zzz-empty-dropdown.png` |
| UT-10 | Single-character query fires no search request | validation | P2 | No dropdown for single char "A"; no network request to /symbols/search | Single char "A" fires search and shows 20 dropdown suggestions — SYMBOL_SEARCH_MIN_QUERY=1 in config | FAIL | `UT-10-single-char-fires-search.png` |
| UT-11 | Free-text symbol entry works without dropdown selection | regression | P1 | Watch submits with "SIM-BUYER"; cockpit begins loading; no blocking validation error | "SIM-BUYER" typed in Simulated mode; Watch clicked without selecting from dropdown; watch started; cockpit loaded | PASS | `UT-11-12-sim-buyer-control.png` |
| UT-12 | Simulated SIM-BUYER watch resolves to buyer_control | regression | P1 | Tape state "Buyer Control"; confidence > 0%; non-zero feature values | Tape state "Buyer Control"; confidence 0.870; aggressive buy ratio 0.925; all features non-zero | PASS | `UT-11-12-sim-buyer-control.png` |
| UT-13 | Symbol search returns matches for real multi-character query | regression | P1 | AAPL appears in dropdown; clickable; selects "AAPL" | AAPL appeared as first suggestion; clicking it selected "AAPL" and closed dropdown | PASS | `UT-13-aapl-selected.png` |
| UT-14 | Mode selector controls are all present and selectable | regression | P2 | All three modes visible; clicking each works without crash | "Live", "Historical", "Simulated" all present; Simulated selected OK; Historical revealed date picker; Live showed market status; no errors | PASS | `UT-14-mode-selector.png` |
| UT-15 | Waiting indicator appears during Historical watch fetch | ux | P2 | Amber pulsing dot visible within 1–2s of clicking Watch; disappears when data loads | MutationObserver captured pulse=true, connecting=true state within first 300ms; pulsing dot disappeared once data loaded | PASS | `UT-15-waiting-indicator.png` |
| UT-16 | Actionable error message is specific, not generic | ux | P2 | Failure panel contains "try a shorter range"; not just "please try again" | Message read "that window is very high-volume — try a shorter range" — specific and actionable | PASS | `UT-06-timeout-error.png` |

---

## Passed Tests

### UT-01 — Cockpit page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-01-initial.png`
- Navigated to http://localhost:3650; page rendered with "Tapeology" title, three mode buttons (Live, Historical, Simulated), symbol input field, and "Watch" button; no blank screen or error banner.

---

### UT-03 — Rapid typing shows only final query results
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-03-rapid-type-result.png`
- Typed "T"→"TS" within 50ms, then immediately changed to ""→"A"→"AA"→"AAP" within 250ms total. After 1.5s debounce, dropdown showed 12 AAP-prefixed symbols (AAP, AAPB, AAPD, AAPG, AAPL, AAPR, AAPU, AAPW, AAPX, AAPY, APLY, CAAP). No TSLA or TS-prefixed tickers appeared.

---

### UT-04 — First search after backend restart responds within one second
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-04-aapl-fast-response.png`
- Typed "AAPL" into the symbol search (Historical mode). MutationObserver polling at 50ms intervals detected dropdown appearing in ~60ms. AAPL was the first suggestion. No multi-second stall.

---

### UT-05 — Aborted search leaves no stuck "Searching..." indicator
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-05-tsla-no-stuck-spinner.png`
- Typed "T"→"TS"→"TSL"→"TSLA" at 50ms intervals. After 1.5s, dropdown showed 20 TSLA-related suggestions. No "Searching…" text in any li element. No error banner.

---

### UT-06 — Oversized Historical window shows actionable timeout error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-06-timeout-error.png`
- Selected Historical mode; typed "AAPL"; applied Full RTH 9:30–16:00 ET quick-pick for 2025-06-06; clicked Watch. Within ~5 seconds the error "that window is very high-volume — try a shorter range" appeared. Cockpit showed "No ticker watched" — no tape state or confidence populated.

---

### UT-07 — Historical watch cockpit populates with real values quickly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-07-cockpit-populated.png`
- Selected Historical mode; typed "TSLA"; set date 2025-06-06, window 14:30–14:32 (09:30–09:32 ET); clicked Watch. Within 2 seconds: cockpit populated. Tape state: "Unclear", confidence 0.200. Features panel: trade speed 9.83/s, volume speed 563.1/s, aggressive buy ratio 0.308, aggressive sell ratio 0.692, net aggressive volume −6442 — all real non-zero values. 15 recent trades visible with real prices/sizes/sides.

---

### UT-08 — Re-watching identical Historical window is near-instant
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-08-rewatch-cache-hit.png`
- After UT-07 completed, clicked Stop. Kept same TSLA / 2025-06-06 / 14:30–14:32 settings. Clicked Watch again. MutationObserver detected confidence value appearing in ~131ms. Stream status went live without any lingering spinner.

---

### UT-09 — Vendor hiccup produces empty dropdown with no error banner
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-09-zzz-empty-dropdown.png`
- Typed "ZZZ" in Historical mode symbol search. After 1.5s debounce: 0 li items in dropdown; no `.text-rose-400` red error element; no "Searching…" text; input value remained "ZZZ" and accepted further typing.

---

### UT-11 — Free-text symbol entry works without dropdown selection
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-11-12-sim-buyer-control.png`
- Clicked Simulated mode. Typed "SIM-BUYER" in the plain text input (no SymbolSearch dropdown in Simulated mode). Clicked Watch without any dropdown interaction. Watch submitted; cockpit loaded with "Watching SIM-BUYER" and scenario "buyer_control". No "please select a symbol from the list" error appeared.

---

### UT-12 — Simulated SIM-BUYER watch resolves to buyer_control
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-11-12-sim-buyer-control.png`
- SIM-BUYER watch in Simulated mode resolved to tape state "Buyer Control", confidence 0.870. Features panel: trade speed 2.00/s, aggressive buy ratio 0.925, net aggressive volume +14800, large prints 13 — all non-zero. Observations: "Buyer aggression increasing", "Price lifting on buy prints", "Spread stable and narrow".

---

### UT-13 — Symbol search returns matches for real multi-character query
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-13-aapl-selected.png`
- Typed "AAPL" in Historical mode symbol search. Dropdown appeared with 7 suggestions; "AAPL" (Apple Inc. Common Stock) was first. Clicked AAPL button — dropdown closed, input value set to "AAPL". No error banner.

---

### UT-14 — Mode selector controls are all present and selectable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-14-mode-selector.png`
- All three buttons ("Live", "Historical", "Simulated") present on page load. Clicking Simulated: plain ticker input shown, 4 interactive elements. Clicking Historical: date/time pickers appeared, SymbolSearch combobox visible, no crash. Clicking Live: date pickers hidden, market status indicator showed "market closed — next open Jun 8, 02:30 PM GMT+1", no error banner.

---

### UT-15 — Waiting indicator appears during Historical watch fetch
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-15-waiting-indicator.png`
- Watched TSLA 2025-06-03 15:00–15:05 (uncached). MutationObserver captured 4 state transitions within first 300ms. First entry at ~118562ms: `pulse=true, connecting=true` — amber pulsing dot and "connecting" status were observable immediately after clicking Watch. Pulse was absent once data loaded. No blank idle screen during fetch.

---

### UT-16 — Actionable error message is specific, not generic
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-06-timeout-error.png`
- Same scenario as UT-06. Failure panel displayed: "that window is very high-volume — try a shorter range". The message includes the required substring "try a shorter range". The message does not say only "please try again" or show a blank/generic "Error" label. A user would understand they need to submit a shorter time window.

---

## Failed Tests

### UT-02 — Symbol search shows results for two-character query
**Verdict:** FAIL
**Failure:** The test expected that typing a single character "A" shows NO dropdown suggestions (enforcing a min-query length of ≥2), but the actual configured `SYMBOL_SEARCH_MIN_QUERY` constant in `apps/frontend/lib/config.ts` is **1**, so single-character queries DO fire searches and show results.
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-02-single-char-A-dropdown.png`

**Steps taken:**
1. Navigated to http://localhost:3650
2. Switched to Historical mode (SymbolSearch component with dropdown is only rendered in Live/Historical mode)
3. Typed "A" into the symbol search input
4. Waited 1.5 seconds for the debounce to settle

**Expected:** No dropdown suggestions after single char "A"; dropdown populates after second char "A" (making "AA")

**Actual:** After typing "A": dropdown appeared immediately with 20 suggestions (first: "A" — Agilent Technologies Inc.). After typing second "A" (making "AA"): dropdown showed 20 AA-prefixed suggestions (Alcoa Corporation "AA", AAPL alternatives, etc.). The two-char behavior is correct, but the single-char expectation is violated.

**Config evidence:** `apps/frontend/lib/config.ts` line 34: `export const SYMBOL_SEARCH_MIN_QUERY = 1;`

---

### UT-10 — Single-character query fires no search request
**Verdict:** FAIL
**Failure:** Test expected no network request to `/symbols/search` and no dropdown for a single character query. `SYMBOL_SEARCH_MIN_QUERY=1` means the frontend fires a search immediately on single-character input.
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/UT-10-single-char-fires-search.png`

**Steps taken:**
1. Navigated to http://localhost:3650
2. Switched to Historical mode
3. Typed single letter "A" into the symbol search input
4. Waited 2 full seconds

**Expected:** No dropdown suggestions; no search fired; no error banner

**Actual:** 20 dropdown suggestions appeared (A — Agilent Technologies Inc. first). The search request fired within ~60ms. `SYMBOL_SEARCH_MIN_QUERY` is configured as 1, not 2.

**Config evidence:** `apps/frontend/lib/config.ts` line 34: `export const SYMBOL_SEARCH_MIN_QUERY = 1;`

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Backend URL:** http://localhost:8650
- **Browser:** Chrome via MCP (mcp__plugin_superpowers-chrome_chrome__use_browser)
- **Test Date:** 2026-06-07
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-11-evidence/`
