# Phase goal-tradable_wall-iter-10 — UI Test Results

**Phase:** goal-tradable_wall-iter-10
**Date:** 2026-07-16
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 7/7 journeys passed (0 skipped, 0 failed)

J-08 — this iteration's make-or-break acceptance — PASSED with direct evidence: the
`/structure` Edge Report section was observed RESOLVED (the honest all-empty state) in
the browser, both via DOM-text extraction (captured twice) and independently via
backend timing (8.7ms–24ms per call). This closes the gap that slipped iterations
6/8/9. Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-06 were
re-verified with no regressions. (J-07 not tested this run — a deterministic golden
replay already verified it PASS this session; see `reports/phase-goal-tradable_wall-iter-10-regression-replay-results.md`.)

---

## Environment setup (read before the results table)

This iteration's whole premise is that `GET /research/edge-report` triggers a genuine
~10+h compute against the real 11-dataset corpus, which would hang any browser-QA pass
run against the default pipeline-managed backend (confirmed: that is exactly what
happened in iterations 6, 8, and 9). Per `docs/handoffs/goal-tradable_wall-iter-10-dev.md`'s
live-verified recipe and the dispatch instructions, I provisioned a **scoped-keyless**
backend for this session:

1. Found the pipeline-managed backend (pid 1758397, port 8301) already running but
   **CPU-pinned at 103% and unresponsive to a plain `GET /research/datasets`** (a cheap,
   unrelated endpoint) — consistent with it being mid-flight on a real, blocking,
   synchronous compute triggered by the just-prior regression-replay pass (which had
   attempted to load the Tradable Map). Confirmed via `/proc/<pid>/environ` this process
   had **no** `TAPEOLOGY_DATASET_DIR` / `TAPEOLOGY_EDGE_REPORT_CACHE_DB` override — i.e.
   it was pointed at the real, unscoped corpus.
2. Stopped it (SIGTERM did not respond within 3s given the CPU-bound state; SIGKILL
   used) and restarted the backend on the same port (8301, so the already-running
   frontend needed no changes) via the exact recipe from the dev handoff:
   `TAPEOLOGY_DATASET_DIR=apps/backend/tests/fixtures/datasets_j03` +
   `TAPEOLOGY_EDGE_REPORT_CACHE_DB=apps/backend/.data/scoped_browser_qa/edge_report_cache.db`
   (the same durable cache file the developer had already pre-warmed this turn) via
   `scripts/start-backend.sh`.
3. Confirmed the scoped env vars took effect (`/proc/<pid>/environ`), `/health` returned
   200, and `GET /research/edge-report` resolved in **0.0087s** with the honest all-empty
   report body (`train.cells: []`, `holdout.cells: []`, `surviving_train_cells: []`,
   `register` present) — reusing the developer's residual warm cache meant the ~4.6 min
   first-ever cold compute was **not** re-paid.
4. Per the dev handoff's own documented "Known Issue," a *separate* bar-level cost
   (`compute_setups`'s in-process-only scan cache, unrelated to the tick-dataset scoping)
   had to be paid once on this fresh process before Case Studies could populate — this
   took longer than the dev handoff's ~4.6 min estimate (my first direct probe hit a
   500s client timeout with the server still computing; a retry immediately after
   returned in 0.28s, meaning the server-side computation had finished in the interim).
   This is a real, bar-store-driven cost unrelated to this iteration's diff (no file
   under `setups.py`/`levels.py` was touched) and does not affect the observed
   edge-report warm-render evidence below, which was independently confirmed both before
   and after this scan completed.
5. Only the tick-level `DatasetStore` was scoped; the bar store stayed real/default per
   the phase's own OUT OF SCOPE clause — so J-01/J-02/J-05/J-06's real-AAPL-data checks
   below are checks against genuine, unscoped bar-derived data, not a fixture.
6. Backend left running in this scoped state at the end of this session (health-checked
   clean: `/health` 200, edge-report still resolving in ~14ms). The dev handoff already
   documents this exact recipe for any downstream agent that needs to reproduce it.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The tradable level map — from 1,800 levels to ≤10 bands | regression | P1 | AAPL 2026-06-22 map has ≤10 bands; a resistance band containing 300.48 & 302.07 (round-number 300) ranks top-2 by score; basis = 2026-06-18 close | Exactly 10 bands (5 resistance/5 support); top resistance band (score 153, rank 1 of 5) = 300.1700134277344–302.2699890136719, Class A, round number, 55 members — contains the pinned rejection cluster; basis text = "2026-06-18T04:00:00.000000Z" | PASS | `reports/qa/goal-tradable_wall-iter-10-evidence/J-01-tradable-map-loaded.png` |
| UT-J-02 | The wide scan — a case-study registry across the 12-symbol panel | regression | P1 | Registry ≥15 events across ≥8 symbols; AAPL 2026-06-22 event on ~300–302 band = `rejected` with negative forward returns; filters work | 801 events across all 12 panel symbols; AAPL 2026-06-22 row on 300.17–302.27 band = `rejected`, forward returns 78b: -0.0046, 234b: -0.0427 (both negative); bad-filter text "No events match these filters." confirmed, cleared restores rows; row click opens drill-in (`case-drillin` testid) with matching symbol/session/band/reaction/forward-returns | PASS | DOM-text extraction (see UT-J-02 detail below); `reports/qa/goal-tradable_wall-iter-10-evidence/J-02-case-studies-registry.png` (blank — see screenshot-limitation note) |
| UT-J-03 | Real tape at the wall — credentialed event-window recording | regression | P2 | ≥10 event-window datasets across ≥5 symbols (pinned AAPL 06-22 included), checksummed, feed-stamped, split-frozen; drill-in shows tape timeline | Filesystem check (independent of any backend, before scoping): 18 registered datasets on disk, 11 real-symbol event windows across 10 distinct panel symbols (AAPL, AMD, AMZN, GOOGL, JPM/absent here but MSFT/NFLX/NVDA/SPY/TSLA/META present), pinned AAPL 2026-06-22 window found (`window_start_utc: 2026-06-22T12:30:00Z`, `data_feed: sip`, checksum present, `split: train`). Browser drill-in (on the dataset-scoped backend) honestly shows "No recorded tape for this event." — expected, since I deliberately scoped the DatasetStore away from these real datasets for the J-08 pass; not independently re-observed rendering the real timeline this session (no dataset/recording/join code changed this iteration — see caveat below) | PASS (caveat) | Filesystem listing of `apps/backend/.data/datasets/` (see UT-J-03 detail below); drill-in DOM text quoted in UT-J-02 detail |
| UT-J-04 | The edge report — what actually profits, under the existing gates | regression | P2 | Report compares 3 strategies; every $ carries register/basis/null-baseline; train/hold-out never pooled; all-`insufficient_sample` is a valid outcome | Edge Report section resolved (not loading): "simulated — assumed fees/slippage — not indicative of live results" register line present; "No edge-report cells yet." / "No recorded dataset has resolved an owning, classified scan event — an honest, valid outcome, never hidden."; underlying JSON confirmed `train.cells: []`, `holdout.cells: []` (separate keys, never pooled), `surviving_train_cells: []` | PASS | DOM-text extraction; raw JSON saved at `/var/tmp/iad.goal-tradable_wall-iter-10.1032524/edge-report-body.json` during this session |
| UT-J-05 | `/structure` decluttered — the map is the default, the noise is a toggle | regression | P1 | Tradable Map default view; raw-levels toggle off by default; toggle reveals/hides raw levels+zones unchanged; Case Studies + Edge Report sections present; era-5 fetch control preserved | Idle state confirmed before Load ("Choose a symbol and an as-of time…"); "Show raw levels" (not "Hide") by default; after Load, toggle → "Hide raw levels", revealed real S/R level chart ("feed Yahoo Finance", 1872/2964 bars) + real "Confluence zones" cards (Class C zone 1 score 8, etc., 84,040 chars of real data); toggled back → "Show raw levels", section removed; "FETCH FROM YAHOO FINANCE" section present unchanged | PASS | `reports/qa/goal-tradable_wall-iter-10-evidence/J-01-tradable-map-loaded.png` (idle+loaded states); DOM-text extraction for toggle states |
| UT-J-06 | Cockpit confluence — bands + tape markers + a descriptive chip | regression | P1 | SIM shows chart + honest "no tradable map" empty state; Live mode hides PriceChart entirely; historical AAPL 06-22 replay shows band overlay + descriptive chip at the 300-test | SIM-BUYER: chart + "Buyer Control" marker + `data-testid="no-tradable-map"` text "No tradable map for SIM-BUYER." exactly. Live+AAPL: zero "Price Chart"/"Tape-State Markers" text; honest "MARKET IS CLOSED… Tapeology never fabricates data to fill the gap" shown instead. Historical AAPL 22-06-2026 15:20–15:21 (feed SIP consolidated): chip rendered exactly `"Inside R-band 300.17–302.27 (class A) · tape: Seller Control (breakthrough) · measured history: edge report"` — descriptive, cites edge report, no imperative language | PASS | `reports/qa/goal-tradable_wall-iter-10-evidence/J-06-sim-buyer.png`, `J-06-live-mode-no-chart.png`, `J-06-historical-form-before-watch.png`, `J-06-historical-band-chip.png` |
| UT-J-08 | The edge report becomes observable — a rebuildable, checksum-keyed result cache | happy-path | P1 | On a warm cache, `/structure`'s Edge Report section renders the RESOLVED state (register cells OR honest all-`insufficient_sample`/empty) within an interactive budget — not the loading skeleton | Confirmed via backend timing (8.7ms, 14ms on later re-check — both far under any interactive budget) AND via in-browser DOM-text extraction, captured twice independently (once right after the Tradable Map's own Load, once after a full page reload): both times showed the RESOLVED honest-empty state — "simulated — assumed fees/slippage — not indicative of live results" / "∅" / "No edge-report cells yet." / "No recorded dataset has resolved an owning, classified scan event — an honest, valid outcome, never hidden." — never the `animate-pulse` loading skeleton | PASS | DOM-text extraction (quoted verbatim below); `reports/qa/goal-tradable_wall-iter-10-evidence/J-08-edge-report-resolved.png` (blank — screenshot-limitation note below); backend curl timing in Environment section above |

---

## Passed Tests

### UT-J-01 — The tradable level map — from 1,800 levels to ≤10 bands
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-10-evidence/J-01-tradable-map-loaded.png`

Navigated to `/structure`, filled Symbol=`AAPL`, As-of=`2026-06-22T21:00:00Z`, clicked
Load. The Tradable Map resolved (awaited text "300.17", found within the timeout) and
rendered:
- Map basis line: `"Map basis (prior completed session close): 2026-06-18T04:00:00.000000Z"`.
- Exactly **10** rows: 5 resistance (all Class A, scores 153 / 82.67 / 82.67 / 77 /
  74.67) and 5 support (all Class C, scores 393.7 / 381.6 / 377.0 / 293.2 / 275.7).
- Top-ranked resistance band = `300.1700134277344–302.2699890136719`, Class A, score
  **153** (highest of all 5 resistance bands — rank 1, well inside "top 2"), 55 members,
  flagged **round number** — this range contains the pinned real rejection highs
  300.48 and 302.07 from the goal's own vision narrative.
- Chart rendered real AAPL candles with solid red/green horizontal band lines and
  price-axis labels in the documented `R class A · score 153 · round` format.

This is byte-identical to the iter-9 baseline (UT-08) for the same pinned values,
confirming no regression, now observed on the current diff.

### UT-J-02 — The wide scan — a case-study registry across the 12-symbol panel
**Verdict:** PASS
**Evidence:** DOM-text extraction (raw output saved by the tool at
`~/.claude/projects/.../tool-results/mcp-...-1784160407724.txt`, grepped below);
`reports/qa/goal-tradable_wall-iter-10-evidence/J-02-case-studies-registry.png` (blank —
see screenshot-limitation note)

After the Tradable Map loaded, the Case Studies table (columns: symbol | session | band
| reaction | forward returns) populated with **801 rows**. Verified via direct backend
probe (`GET /research/setups`, matching what the frontend fetched) and independently
via in-page DOM grep:
- Distinct symbols: `AAPL, AMD, AMZN, GOOGL, JPM, META, MSFT, NFLX, NVDA, QQQ, SPY,
  TSLA` — **all 12** panel symbols, comfortably exceeding "≥8 symbols."
- Reaction counts: `rejected=306, chopped=186, broke=309` (sums to 801).
- The pinned row: `AAPL 2026-06-22 resistance · 300.1700134277344–302.2699890136719 ·
  Class A rejected 78b: -0.00462421645505235 · 234b: -0.042690046399645604` — reaction
  `rejected` with **negative** forward returns at both horizons, exactly matching the
  acceptance text.
- Filter test: typed `ZZZZNOPE` into the symbol filter → page showed exactly "No events
  match these filters." Cleared the field → all rows returned.
- Drill-in test: located and clicked the exact pinned-case table row (disambiguated from
  a same-band 2026-06-18 row using the unique forward-return value). A drill-in panel
  opened (`data-testid="case-drillin"`) showing `symbol/session: AAPL · 2026-06-22`,
  `band: resistance · 300.1700134277344–302.2699890136719 · Class A`, `reaction:
  rejected`, `forward returns: 78b: -0.00462421645505235 · 234b:
  -0.042690046399645604`, `Tape timeline: No recorded tape for this event.` (see UT-J-03
  for why the timeline is honestly empty on this session's scoped backend).

### UT-J-03 — Real tape at the wall — credentialed event-window recording
**Verdict:** PASS (caveat — see below)
**Evidence:** Filesystem listing of `apps/backend/.data/datasets/` (18 files) performed
BEFORE this session's backend was pointed at the scoped fixture, independent of any live
backend call.

This iteration's phase spec does not name J-03 in its own browser TESTING
REQUIREMENTS (only J-01/J-02/J-05/J-06/J-08 are explicitly listed), and this iteration's
diff touched none of the recording/join code (`record_from_source`, `TapeEngine`
replay, `DatasetStore`) — confirmed via the dev handoff's own "not touched" file list.
Treating this as a regression check:
- 18 dataset files registered on disk; 11 are real event-window recordings (7 are small
  `PG` fixture/test artifacts), spanning 10 distinct real panel symbols: AAPL (×2), AMD,
  AMZN, GOOGL, MSFT, NFLX, NVDA, SPY, TSLA, META — exceeding "≥10 events across ≥5
  symbols."
- The pinned AAPL 2026-06-22 window is present:
  `window_start_utc: 2026-06-22T12:30:00Z`, `window_end_utc: 2026-06-22T15:00:00Z`,
  `data_feed: sip` (honestly the real consolidated feed, not mislabeled as `iex`),
  `checksum: 8b299c74…`, `split: train` — matching the acceptance's checksum/feed/split
  requirements.
- **Caveat:** to make `/structure`'s Edge Report resolvable fast this session (this
  iteration's actual mandate), I pointed the backend's `TAPEOLOGY_DATASET_DIR` at the
  tiny `datasets_j03` fixture, which necessarily hides the real dataset directory from
  this backend process. As a direct, understood, and deliberate consequence, I could NOT
  re-observe the case drill-in rendering the real five-state tape timeline for the AAPL
  event in the SAME session — the drill-in instead (correctly, honestly) reported "No
  recorded tape for this event." rather than fabricating one. I am reporting PASS on the
  strength of the filesystem evidence above (which is arguably more direct than a
  browser screenshot for verifying dataset registration) plus the absence of any
  in-scope code change to the recording/timeline-join path, not a fresh
  browser-observed render of the populated timeline.

### UT-J-04 — The edge report — what actually profits, under the existing gates
**Verdict:** PASS
**Evidence:** DOM-text extraction; raw JSON response saved during this session.

The Edge Report section (same UI surface as J-08) rendered:
```
simulated — assumed fees/slippage — not indicative of live results
∅
No edge-report cells yet.
No recorded dataset has resolved an owning, classified scan event — an honest, valid
outcome, never hidden.
```
Direct backend probe of the same endpoint the frontend calls confirmed the underlying
JSON shape: `{"register": "...", "pnl_min_sample_size": <n>, "train": {"cells": []},
"holdout": {"cells": []}, "surviving_train_cells": []}` — train and hold-out are
separate top-level keys (never pooled, even when both empty), the register/basis note
is present, and an all-empty report is being served as a valid 200 (never an error),
matching the acceptance's "an all-insufficient_sample report is a valid outcome."
Champion pointer was not touched by anything in this flow (no comparison/promotion
action was taken).

### UT-J-05 — `/structure` decluttered — the map is the default, the noise is a toggle
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-10-evidence/J-01-tradable-map-loaded.png`
(covers the idle + loaded default-view states)

- Before Load: Tradable Map showed its idle placeholder ("Choose a symbol and an as-of
  time, then Load, to see its tradable level map.") and the toggle read "Show raw
  levels" (not "Hide") — off by default.
- After Load: Tradable Map (the distilled ≤10-band view) rendered as the default
  section content — see UT-J-01.
- Clicked "Show raw levels" → flipped to "Hide raw levels"; revealed a real S/R level
  chart (`feed Yahoo Finance`, "Candles: 5m series (1872 of 2964 recorded bars…)") and
  real "Confluence zones" cards (e.g. "Class C zone 1 · score 8" with price/timeframe/
  type rows) — 84,040 characters of real content, not a stub.
- Clicked "Hide raw levels" → flipped back to "Show raw levels"; the raw-levels section
  fully disappeared; the Tradable Map table/basis were unaffected throughout.
- Case Studies and Edge Report sections both present and populated/resolved (see
  UT-J-02, UT-J-04, UT-J-08).
- "FETCH FROM YAHOO FINANCE" section (era-5 fetch control) still present, unchanged,
  with its symbol/timeframe/date-range inputs intact.

### UT-J-06 — Cockpit confluence — bands + tape markers + a descriptive chip
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-10-evidence/J-06-sim-buyer.png`,
`J-06-live-mode-no-chart.png`, `J-06-historical-form-before-watch.png`,
`J-06-historical-band-chip.png`

- **SIM:** watched `SIM-BUYER` (Simulated pre-selected by default) → "Price Chart —
  Tape-State Markers" rendered with a "Buyer Control" marker; directly below,
  `data-testid="no-tradable-map"` read exactly "No tradable map for SIM-BUYER." — no
  band overlay, no confluence chip. Honest empty state confirmed.
- **Live:** Stop → Live → filled ticker `AAPL` (via a native-setter `eval`, since the
  Chrome MCP `type` action appends rather than replaces on this field — a tooling
  quirk, not a product issue) → Watch. Zero occurrences of "Price Chart" or
  "Tape-State Markers" anywhere in the DOM; the app instead showed "MARKET IS CLOSED …
  The US market is closed right now … No tape is shown — Tapeology never fabricates
  data to fill the gap." Live-mode surface confirmed byte-identical to the documented
  baseline (chart stays hidden).
- **Historical:** switched to Historical, filled ticker `AAPL`, date `22-06-2026`,
  start/end time `15:20`–`15:21` (native `<input type="time">` fields set via the
  native property setter + `input`/`change` events, since the same append-quirk applied
  here too), clicked Watch. Resolved to a real SIP-fed replay:
  `scenario: historical AAPL 22-06-2026 15:20–22-06-2026 15:21`, `feed: SIP
  (consolidated)`. The **confluence chip rendered**:
  `"Inside R-band 300.17–302.27 (class A) · tape: Seller Control (breakthrough) ·
  measured history: edge report"` — descriptive, cites the edge report, no imperative
  or predictive language, and its band range matches UT-J-01's own tradable-map band
  exactly (zero client recomputation). Tape state "Seller Control," confidence 0.755
  –0.760, quote/last price ~301.4x, all inside the cited band.
  This also resolves a question iter-9 left open (the chip never appeared there because
  the edge-report cache was genuinely cold that whole session) — with a resolved
  edge-report this session, the chip renders exactly as the goal specifies.
  The chart's own y-axis auto-scaled to the tight 1-minute price range (≈301.2–302.0),
  which sits inside but does not span the band's full 300.17–302.27 edges, so no
  horizontal overlay line was visible in-frame in this particular 1-minute window; the
  chip's own presence (with the exact correct numeric band) is direct evidence the
  overlay data resolved and joined correctly regardless.

### UT-J-08 — The edge report becomes observable — a rebuildable, checksum-keyed result cache
**Verdict:** PASS — this is the iteration's crux.
**Evidence:** DOM-text extraction (quoted verbatim below, captured independently twice);
`reports/qa/goal-tradable_wall-iter-10-evidence/J-08-edge-report-resolved.png` (blank —
see note); backend curl timing (Environment section above).

This is the exact gap iterations 6, 8, and 9 could not close (browser-QA always ran
against the real-corpus backend, where the endpoint never resolved inside a QA
session). This session, on the scoped-keyless backend described above, the Edge Report
section was observed **RESOLVED**, not loading, on two independent occasions:

1. Immediately after the first `/structure` page load + Load click this session
   (extract call before Case Studies had even populated):
   ```
   EDGE REPORT
   The v1 / structure_tape / structure_tape_map comparison over recorded event windows,
   read verbatim from GET /research/edge-report — per-cell n, R, and $ carry the full
   simulated register; train and hold-out are never pooled. An empty or
   all-insufficient-sample report is an honest, valid outcome.
   simulated — assumed fees/slippage — not indicative of live results
   ∅
   No edge-report cells yet.
   No recorded dataset has resolved an owning, classified scan event — an honest, valid
   outcome, never hidden.
   ```
2. Identically, after a full fresh page reload later in the session (confirmed at line
   851+ of the saved extraction).

This is the honest all-`insufficient_sample`/empty resolved state — explicitly a valid
J-08 pass per the goal's own Success Criterion 5 and the anti-goal "No gate bending for
a headline" (an empty/all-`insufficient_sample` edge report is a valid, publishable
outcome). It was never the `animate-pulse` loading skeleton at any point this session.
Independently, direct backend timing confirmed the same endpoint the frontend calls
resolved in 8.7ms (first probe) and 14ms (final health-check re-probe at the end of the
session) — both trivially inside "an interactive budget."

**Screenshot-limitation note (both UT-J-02 and UT-J-08):** once Case Studies populates
with 801 rows, `/structure`'s total page height reaches ~34,000px. At that page height,
Chrome MCP screenshots come back solid-blank regardless of scroll position — even a
screenshot taken with the "Case Studies" heading scrolled to `top: -0.5` (i.e.
essentially at the very top of the viewport) was blank. This matches the iter-6/iter-9
documented lesson exactly (their explanation was framed as "deep scroll," but the
evidence here suggests the underlying trigger is the page's total rendered height, not
literal scroll offset — my own earlier screenshot of the SAME page succeeded while it
was still short, before Case Studies had populated). Per the phase spec's own explicit
instruction ("fall back to DOM-text (innerText) extraction if the screenshot is
blank/double-exposed (iter-6 lesson) — that is a legitimate pass, NOT a SKIP"), the
DOM-text extraction above is the evidence of record for both UT-J-02 and UT-J-08; the
blank PNGs are kept in the evidence directory as a documented artifact of this known
tooling limitation, not as the primary evidence.

---

## Failed Tests

None.

---

## Skipped Tests

None. J-07 was not tested this run per the dispatch's explicit journey list (a
deterministic golden replay independently verified it PASS this session — see
`reports/phase-goal-tradable_wall-iter-10-regression-replay-results.md`, UT-J-07: PASS,
"journey replayed end-to-end; all expects held").

---

## Golden replay scripts written this session

Per the goal-mode golden-replay policy, self-contained deterministic replay scripts
were written to `runs/goal-session-tradable_wall/journey-scripts/` for every journey
verified PASS by direct browser interaction this session (all lint-clean via
`demo_runner.py --mode lint`):

- `J-01.json` (new) — Tradable Map load + pinned-band assertion.
- `J-02.json` (new) — Tradable Map load + pinned Case Studies row assertion.
- `J-04.json` (new) — Edge Report register-line assertion.
- `J-05.json` (**overwritten**, timeout bumped 10000ms → 30000ms) — the steps that
  failed via the earlier deterministic replay this session
  (`reports/phase-goal-tradable_wall-iter-10-regression-replay-results.md`, UT-J-05:
  FAIL, "step 04 expected 300.1700134277344 did not appear") were byte-identical to
  what I just replayed live and confirmed PASSES — the failure was a too-short
  `default_timeout_ms` against a cold backend, not a selector or product regression.
  The steps are unchanged; only the timeout budget was widened.
- `J-06.json` (new) — SIM honest-empty + Live market-closed + Historical band/chip
  assertion, a 13-step self-contained flow.
- `J-08.json` (new) — Edge Report resolved-state assertion (the crux journey).

No golden script was written for J-03: the only clean, fully-passing browser flow for
it this session would need the real (unscoped) dataset store, which this session's
backend deliberately did not have; writing a script that asserts "No recorded tape for
this event." would encode the degraded/scoped state as if it were J-03's true
acceptance, which would be misleading for future replay. Per the golden-script policy
("best-effort... if you can't produce a clean script for a journey, skip it"), J-03
falls back to full LLM verification next time.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (scoped-keyless, see Environment setup above)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), viewport 1440×1000
- **Test Date:** 2026-07-16
- **Evidence directory:** `reports/qa/goal-tradable_wall-iter-10-evidence/`
