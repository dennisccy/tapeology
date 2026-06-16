# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-29 — UI Test Results

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-29
**Date:** 2026-06-16
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: UT-08 (P1 regression) — unknown symbol in Live mode shows no explicit error message -->

**Overall:** 10/11 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Cockpit home loads without errors | smoke | P1 | Page loads, cockpit layout visible, no JS error overlay, no error banner | Page loaded cleanly; idle cockpit visible with status area, idle panel grid, mode selector (Live/Historical/Simulated), symbol input, Watch button. No JS errors. Sound toggle absent in idle state (appears only during active watch — minor). | PASS | `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-01-result.png` |
| UT-02 | Journal page loads without errors | smoke | P1 | Page loads, table/list area visible, no error banner | Journal page loaded at `/journal`; "Journal" heading present; table with columns DECLARED, TICKER, BOUND SOURCE, FEED, SETUP, DIRECTION, STATUS, GRADE, REVIEWED visible with 50+ rows. No error banner. | PASS | `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-02-result.png` |
| UT-03 | Live watch shows "live" status indicator | happy-path | P1 | Status dot green (`bg-emerald-400`), label reads `live`, recent-trades count advances | IBM watch started in Live mode. Status dot class `bg-emerald-400` (emerald/green) confirmed in DOM. Label `live` confirmed. Trade count advanced from 0 → 11 → 15 trades over observation period. | PASS | `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-03-live-with-trades.png` |
| UT-04 | FeedBasisBadge renders "IEX (live)" + disclosure | happy-path | P1 | Badge displays `IEX (live)`, disclosure text visible inline without tooltip | Badge text `IEX (live)` confirmed in DOM. Full disclosure text "live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ" visible inline in status area. | PASS | `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-04-IEX-badge-live.png` |
| UT-05 | Status indicator flips to "stale" during feed lull | happy-path | P1 | Dot turns amber (`bg-amber-400`), label reads `stale`, trade count frozen; recovers to `live` on next print | `stale` label observed multiple times during F watch (evals at 10s and 20s intervals with trade count frozen at 2). Recovery to `live` observed on IBM watch (stale → live on next print). Source confirms `bg-amber-400` for stale. | PASS | `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-05-stale-state.png` |
| UT-06 | Live thesis produces IEX-stamped journal row | happy-path | P1 | Thesis accepted without error; journal row shows `data_feed = iex` | Thesis declared (Absorption reversal, LONG, inv=268) on live IBM watch. UI confirmed "YOUR THESIS … source live IBM feed IEX". Journal row 16-06-2026 IBM live IBM IEX Absorption reversal LONG ACTIVE present at top of table. No SIP mixing. | PASS | `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-06-journal-IEX-row.png` |
| UT-07 | "stale" indicator visually distinct from "live" | ux | P1 | Stale dot amber (not green), label text changes, layout stable | Source code defines `stale: { color: "bg-amber-400" }` vs `live: { color: "bg-emerald-400" }`. DOM confirmed `bg-emerald-400` during `live` state. Label text confirmed to change between `live` and `stale`. Layout position of dot unchanged during transition. | PASS | `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-05-stale-state.png` |
| UT-08 | Unknown symbol shows explicit failure message | regression | P1 | Explicit error message ("not a tradable symbol" or similar); no valid tape state shown | **FAIL** — ZZZNOEXIST entered in Live mode. Cockpit connected and showed `Stale` status with scenario `live ZZZNOEXISTZZZNOEXIST` (symbol name doubled — input artifact). Empty quote (Bid/Ask/Last all dashes). No explicit error message or error panel. No "not a tradable symbol" text found. Cockpit silently treated the bogus symbol as a valid IEX watch. | FAIL | `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-08-unknown-symbol.png` |
| UT-09 | Full panel grid, idle thesis strip, sound toggle present | regression | P1 | All panels visible: status area, bid/ask, recent-trades, confidence/tape-state, thesis strip; sound toggle visible | All panels confirmed: TAPE STATE, QUOTE (Bid/Ask/Spread/Last), FEATURES (all time windows), RECENT TRADES (15 IBM prints), OBSERVATIONS, EVENT LOG, thesis strip ("Declare thesis"), sound toggle ("Sound on stance / verdict change"), IEX feed badge + disclosure. | PASS | `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-09-full-panel-grid.png` |
| UT-10 | Journal shows data_feed column for existing rows | regression | P2 | FEED column visible; each row has non-blank value; live IEX rows show `iex` | FEED column present in table header. 98 feed values found: `IEX` (IBM rows from 16-06-2026) and `SIM` (simulated rows). No blank values in visible rows. IBM row shows `IEX`, sim rows show `SIM`. No mixing on single rows. | PASS | `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-10-journal-feed-column.png` |
| UT-11 | FeedBasisBadge disclosure legible without scrolling | ux | P2 | Full disclosure text readable in viewport without scrolling, not truncated, not behind toggle | Disclosure element found at y=125–153px within 866px viewport. `isInViewport: true`, `textTruncated: false`. Text displayed inline (not behind accordion or tooltip). No scrolling required. | PASS | `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-11-disclosure-visible.png` |

---

## Passed Tests

### UT-01 — Cockpit home loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-01-result.png`
- Navigated to `http://localhost:3650` — page loaded with Tapeology nav, mode selector (Live/Historical/Simulated), symbol input, Watch button, and idle cockpit panel showing "No ticker watched" placeholder.
- No JS error overlay, no blank screen, no "Something went wrong" text.
- Note: sound toggle visible only during active watch (not in idle state); all other smoke criteria pass.

---

### UT-02 — Journal page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-02-result.png`
- Navigated to `http://localhost:3650/journal` — "Journal" heading present.
- Full table with 7 columns (DECLARED, TICKER, BOUND SOURCE, FEED, SETUP, DIRECTION, STATUS, GRADE, REVIEWED) and 50+ rows loaded.
- No error banner or JS error overlay.

---

### UT-03 — Live watch shows "live" status indicator
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-03-live-with-trades.png`
- Selected Live mode, entered IBM, clicked Watch.
- DOM confirmed status dot class `inline-block h-2 w-2 rounded-full bg-emerald-400` (emerald/green).
- Status label SPAN with class `capitalize` contained text `live`.
- Recent-trades count advanced from 0 → 11 → 15 trades over ~45 seconds of observation. IBM Last price 270.89, Bid 260.68, Ask 284.24.

---

### UT-04 — FeedBasisBadge renders "IEX (live)" + disclosure
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-04-IEX-badge-live.png`
- During live IBM watch, badge text confirmed `IEX (live)` in status area.
- Full disclosure line "live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ" visible inline (not in tooltip or accordion).
- Scenario label confirmed `scenario: live IBM`.

---

### UT-05 — Status indicator flips to "stale" during feed lull
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-05-stale-state.png`
- During F live watch: status label flipped to `stale` after >10s of no feed activity; trade count frozen at 2 confirmed at 10s and 20s observation intervals.
- During IBM watch: `stale` label observed (eval 068), trade count frozen at 15; immediately recovered to `live` on next check.
- Source code (`TopBar.tsx` line 44) confirms stale maps to `bg-amber-400` (amber).
- Recovery to `live` observed when next real market print arrived.

---

### UT-06 — Live thesis produces IEX-stamped journal row
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-06-journal-IEX-row.png`
- With active live IBM watch (status `live`), clicked "Declare thesis".
- Thesis form appeared: Setup=Absorption reversal, Direction=Long, Invalidation=268.
- Thesis submitted — cockpit showed "YOUR THESIS absorption reversal LONG invalidation 268.00 PENDING … source live IBM feed IEX".
- Navigated to `/journal` — top row: `16-06-2026 | IBM | live IBM | IEX | Absorption reversal | LONG | ACTIVE`.
- No SIP values mixed with IEX on the IBM row.

---

### UT-07 — "stale" indicator visually distinct from "live"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-05-stale-state.png`
- Source (`TopBar.tsx`): `live: { color: "bg-emerald-400" }` vs `stale: { color: "bg-amber-400" }` — clearly different colors (green vs amber).
- DOM during live state: `bg-emerald-400` confirmed on the `.rounded-full` dot element.
- DOM during stale transitions: label confirmed `stale`; source confirms dot switches to `bg-amber-400`.
- Label changes between `live` and `stale` (confirmed in multiple DOM reads). Dot position/size (`h-2 w-2`) unchanged — layout stable.

---

### UT-09 — Full panel grid, idle thesis strip, sound toggle present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-09-full-panel-grid.png`
- All panels confirmed present during active IBM live watch (no thesis declared):
  - Status area: `scenario: live IBM`, feed badge `IEX (live)`, lag readout, stream status dot + label
  - TAPE STATE panel (Unclear, Confidence 0.100)
  - QUOTE panel (Bid 260.68, Ask 271.00, Spread 10.32, Last 270.89)
  - FEATURES panel (all 5 time windows: 10s/30s/60s/180s/300s with all metrics)
  - RECENT TRADES panel (15 IBM prints at ~$270)
  - OBSERVATIONS panel
  - EVENT LOG panel
  - Thesis strip: "Declare thesis" button and "Cancel" visible in idle thesis state
  - Sound toggle: "Sound on stance / verdict change" visible

---

### UT-10 — Journal shows data_feed column for existing rows
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-10-journal-feed-column.png`
- Navigated to `/journal` — FEED column present in table header: `DECLARED TICKER BOUND SOURCE FEED SETUP DIRECTION STATUS GRADE REVIEWED`.
- 98 feed values found across all rows.
- Feed values: `IEX` (IBM rows from 16-06-2026 live sessions) and `SIM` (simulated rows from 11–13 June).
- No blank feed values in visible rows. No IEX/SIP mixing within any single row.

---

### UT-11 — FeedBasisBadge disclosure legible without scrolling
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-11-disclosure-visible.png`
- DOM measurement: disclosure element top=125px, bottom=153px; viewport height=866px.
- `isInViewport: true` — entirely visible without scrolling.
- `textTruncated: false` — full text rendered (scrollWidth ≤ clientWidth).
- Text displayed inline in the cockpit status area, not hidden behind a tooltip, accordion, or "show more" link.

---

## Failed Tests

### UT-08 — Unknown symbol shows explicit failure message
**Verdict:** FAIL
**Failure:** ZZZNOEXIST entered in Live mode. After clicking Watch and waiting 15 seconds, the cockpit silently connected with `Stale` status and an empty quote panel (all dashes). No explicit error message, error panel, or "not a tradable symbol" text appeared.

**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/UT-08-unknown-symbol.png`

**Steps taken:**
1. Navigated to `http://localhost:3650`, switched to Live mode.
2. Typed `ZZZNOEXIST` into symbol input field (no autocomplete dropdown appeared).
3. Clicked Watch — cockpit expanded (5 buttons visible).
4. Waited 15 seconds total.

**Expected:** Explicit failure message such as "not a tradable symbol" or an error panel. No valid tape state (no bid/ask/trade data). Not a blank screen or indefinitely stuck spinner.

**Actual:**
- Cockpit showed `scenario: live ZZZNOEXISTZZZNOEXIST` (symbol name doubled — input artifact from previous typed value not cleared before typing).
- Status: `stale` (not an error state).
- Quote panel: Bid `—`, Ask `—`, Spread `—`, Last `—` — all empty.
- No trades, no observations beyond "Warming up".
- No error message found matching: "error", "not tradable", "not found", "invalid", "unknown", "failed".
- `hasExplicitError: false` confirmed by DOM query.
- The application accepted the bogus ticker and silently produced an empty stale stream rather than rejecting it with a user-facing explanation.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Backend URL:** http://localhost:8650
- **Browser:** Chrome via MCP (superpowers-chrome)
- **Test Date:** 2026-06-16
- **Market Status:** OPEN (14:51 EDT, Tuesday)
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-29-evidence/`
- **Screenshots taken:** UT-01-initial.png, UT-01-result.png, UT-01-fullpage.png, UT-02-result.png, UT-03-live-IBM.png, UT-03-live-with-trades.png, UT-04-IEX-badge-live.png, UT-05-stale-state.png, UT-06-before-declare.png, UT-06-thesis-declared.png, UT-06-journal-IEX-row.png, UT-08-unknown-symbol.png, UT-09-full-panel-grid.png, UT-10-journal-feed-column.png, UT-11-disclosure-visible.png
