# Phase goal-desk-iter-29 — UI Test Results

**Phase:** goal-desk-iter-29
**Date:** 2026-07-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 7/8 tests passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads, Screen Runs panel present | smoke | P1 | Fourth panel "Screen Runs" visible after Index Reconciliation, no blank/error, empty or table state, no h-scroll, no console errors | Panel present with `data-testid="desk-screen-runs-empty"` showing exact text "No screen runs recorded yet."; no h-scroll (scrollWidth=clientWidth=1425 at 1440 viewport); console clean (only React DevTools info line) | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-01-result.png` |
| UT-02 | Freshly-completed run appears in ledger | happy-path | P1 | New row in table, date=today UTC, state=done, attempted/total equal (e.g. 101/101), produced=screen id; Latest-run detail block with heading/state/elapsed/ranked-skipped counts | Real "Run Screen" click walked all 101 members (started 01:58:48Z, finished 02:00:29Z, ~1m41s). Row: `2026-07-31 · screenrun-2026-07-31-725c4ec2bfcd · done · 101 / 101 · screen-2026-07-31-c169546856c7`. Detail block: "Latest run — 2026-07-31 · screenrun-2026-07-31-725c4ec2bfcd", "state: done", "101 of 101 members attempted", "1m 40s elapsed", "screen-2026-07-31-c169546856c7", "100 ranked · 0 skipped (no bars) · 1 skipped (no basis)" | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-02-result.png` |
| UT-03 | Duplicate click short-circuits, recorded as reused | happy-path | P1 | Second click resolves much faster, progress counter does not climb; new row "0 / total"; produced = "reused `<id>` — no walk was performed" with id identical to UT-02's; latest-detail outcome line matches; counts line (if shown) not a fabricated re-count | Second run: started/finished 02:01:55.4866Z/.5010Z (~15ms vs ~1m41s). New row: `done · 0 / 101 · reused screen-2026-07-31-c169546856c7 — no walk was performed` (same screen id as UT-02). Latest-detail outcome (`desk-screen-run-latest-outcome`) text byte-identical. Counts line DID render (state===done) but read "0 ranked · 0 skipped (no bars) · 0 skipped (no basis)" — honest zeros, not the original walk's 100/0/1, i.e. not a fabricated re-count | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-03-result.png` |
| UT-04 | Empty state never fabricates outcome | validation | P2 | Exact text "No screen runs recorded yet." in `desk-screen-runs-empty`; no table; no latest-run detail; nothing invented | Verified against the genuinely-empty ambient store (`GET /research/desk/screen/runs` returned `{"runs":[],"latest":null,"integrity_errors":[]}` before any run this session — confirmed by curl before triggering UT-02, and independently by DOM eval: `emptyText` exact match, `tablePresent:false`, `detailPresent:false`) | PASS | none — see note below |
| UT-05 | Failed run shows verbatim error + member | error | P2 | Failed row's produced column reads "nothing recorded"; latest-detail failure block shows raising member (monospace) + " — " + verbatim error; counts line absent | SKIPPED — see Skipped Tests section | SKIP | none |
| UT-06 | Ranked table unchanged | regression | P1 | Columns/layout unchanged from pre-iteration; row drill-in still navigates to `/structure`; no h-scroll at 1440x900 | Header row unchanged: rank/symbol/side/class/distance/score/coverage/tick evidence/basis/history/band/opposite/levels (13 cols, matches pre-iteration shape). Clicked row's own `data-testid="desk-row-drill-in"` anchor for BRK-B → navigated to `/structure?symbol=BRK-B&asof=2026-07-31T23%3A59%3A59Z`, confirmed via `window.location.href` and "Structure" heading. No h-scroll (1425/1425) | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-06-result.png` |
| UT-07 | Top-up Runs / Index Reconciliation unaffected | regression | P1 | Both sibling panels render as before; no screen-run text leaks into them; section order: Screen History → Run controls → Top-up Runs → Index Reconciliation → Screen Runs (last) | Top-up Runs latest-counts unchanged ("0 reused · 390 fetched · 0 unchanged · 14 failed"); DOM-scoped check confirmed neither Top-up Runs nor Index Reconciliation section contains any `screenrun-` text. `h2` order confirmed: Provenance, Briefing, Skipped Members, Screen History, Run Screen / Top-up / Reconcile Index, Top-up Runs, Index Reconciliation, Screen Runs (last) | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-07-result.png` |
| UT-08 | Screen Runs panel discoverable | ux | P2 | Reached within one scroll from Index Reconciliation; heading style/capitalization matches siblings; no new nav | Reconcile section bottom=1391.5px, Screen Runs section top=1415.5px (one continuous scroll). `className="mt-6"` identical across Top-up Runs / Index Reconciliation / Screen Runs sections; heading class (`text-xs font-semibold uppercase tracking-wider text-slate-500`) identical across all three. Nav bar unchanged (Cockpit / Structure / Desk only) | PASS | `reports/qa/goal-desk-iter-29-evidence/UT-08-result.png` |

---

## Passed Tests

### UT-01 — `/desk` loads and the Screen Runs panel is present
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-29-evidence/UT-01-result.png` (screenshot shows the panel in its later, populated state — see the screenshot-tooling note below; the panel's *presence and non-error rendering*, which is what UT-01 actually tests, was verified at both the empty and populated moments)
- Navigated to `/desk`, page loaded with heading "Desk", no blank screen or error.
- Section order confirmed via `h2` text extraction ends with "Screen Runs" as the last (fourth) ledger section, immediately after "Index Reconciliation".
- At first load this session the panel showed the honest empty state (`data-testid="desk-screen-runs-empty"`, text "No screen runs recorded yet.") — the genuine ambient-store state before any run was triggered — confirmed via DOM eval (see UT-04). UT-01's own acceptance criterion explicitly allows either the empty state or a populated table ("shows either the empty-state text ... or a table"), so the panel's later populated-table screenshot below is equally valid smoke evidence.
- `document.documentElement.scrollWidth === clientWidth === 1425` at a 1440×900 viewport — no horizontal scrollbar.
- Console messages captured from page load: only the informational React DevTools message; no errors.

### UT-02 — A freshly-completed screen run appears in Screen Runs
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-29-evidence/UT-02-result.png` (this crop is taken after UT-03 also ran, so it shows both rows together — see the screenshot-tooling note below; the fresh run's own row and stats are fully visible and legible in it)
- Clicked `data-testid="desk-run-screen-button"`. Button changed to "Computing…" (disabled), `data-testid="desk-screen-compute-progress"` climbed from `3 / 101 members` through `101 / 101 members` over ~1m41s (confirmed via the backend's own `GET /research/desk/screen/compute` timestamps: started `2026-07-31T01:58:48.237928Z`, finished `2026-07-31T02:00:29.056640Z`).
- Screen Runs table gained one row: date `2026-07-31`, run id `screenrun-2026-07-31-725c4ec2bfcd`, state `done`, attempted/total `101 / 101`, produced `screen-2026-07-31-c169546856c7` — visible as the table's first row in the evidence screenshot.
- At the moment this run was the latest, the latest-run detail block (`data-testid="desk-screen-run-latest-detail"`) was confirmed via live DOM eval to read: "Latest run — 2026-07-31 · screenrun-2026-07-31-725c4ec2bfcd", "state: done", "101 of 101 members attempted", "1m 40s elapsed", the screen id, and counts line "100 ranked · 0 skipped (no bars) · 1 skipped (no basis)" — matching the backend record's `ranked_count: 100, skipped_by_reason: {no_bars: 0, no_basis: 1}` exactly (raw JSON captured via `curl http://localhost:8301/research/desk/screen/runs` at the time, quoted in full in the dispatch trace).

### UT-03 — A duplicate Run Screen click short-circuits and is recorded as reused
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-29-evidence/UT-03-result.png` (full-page crop of the Screen Runs section taken after the second click, showing the table's second row and the latest-run detail block, both for this reused run)
- Clicked "Run Screen" again immediately after UT-02. Backend record shows the second run started `2026-07-31T02:01:55.486557Z` and finished `2026-07-31T02:01:55.501036Z` (~15ms) — dramatically faster than UT-02's ~1m41s; the members-progress counter never climbed (`members_attempted: 0`).
- New table row: `done · 0 / 101 · reused screen-2026-07-31-c169546856c7 — no walk was performed` — the screen id is byte-identical to UT-02's.
- Latest-run detail's outcome line (`data-testid="desk-screen-run-latest-outcome"`) read the identical "reused screen-2026-07-31-c169546856c7 — no walk was performed" text.
- The ranked/skipped-counts line DID render (the reused run's `state` is also `"done"`, matching the test plan's own caveat), but its content was "0 ranked · 0 skipped (no bars) · 0 skipped (no basis)" — the honest counts for what this specific run record actually did (nothing), not a fabricated repeat of UT-02's 100/0/1. This satisfies the test's explicit instruction to verify the counts are not a fabricated re-count.

### UT-04 — The empty state never fabricates a produced outcome
**Verdict:** PASS
**Evidence:** none (see "Screenshot tooling note" below — the genuinely-empty state was consumed by this same session's own UT-02 run before a valid screenshot mechanism was confirmed; DOM-text evidence below was captured live at the exact moment the empty state was real)
- Before triggering any run this session, `curl http://localhost:8301/research/desk/screen/runs` returned the genuinely empty `{"runs":[],"latest":null,"integrity_errors":[]}` against the real ambient store (not a scoped fixture — the ambient store happened to have zero recorded screen-run-log entries because this iteration's `ScreenRunStore` log dir had never been written to before this session, per the dev handoff's TC-15 note).
- DOM eval confirmed at that same moment: `desk-screen-runs-empty` element text is exactly "No screen runs recorded yet." (rendered with a leading "∅" glyph before the text — the text itself is the exact required string: `"emptyText":"∅No screen runs recorded yet."`), `desk-screen-runs-table` absent (`"tablePresent":false`), `desk-screen-run-latest-detail` absent (`"detailPresent":false`). No screen id, date, or state text of any kind appeared anywhere in the section.
- This state cannot be reproduced again on the ambient store within this session (the run log is append-only and this session's own UT-02 click already appended a real record), so no fresh screenshot could be taken after the screenshot-capture bug below was found and fixed. The DOM-eval evidence above was captured via direct property extraction, not inferred, and is treated as sufficient evidence for this P2 test.

### UT-06 — The ranked briefing table is unchanged by this iteration
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-29-evidence/UT-06-result.png`
- Ranked table header columns: rank, symbol, side, class, distance, score, coverage, tick evidence, basis, history, band, opposite, levels — unchanged shape (13 columns).
- Per the project's own house rule, clicked the row's own stretched drill-in anchor (`data-testid="desk-row-drill-in"`, not a raw cell click) for the BRK-B row.
- Browser navigated to `/structure?symbol=BRK-B&asof=2026-07-31T23%3A59%3A59Z` (confirmed via `window.location.href` and the "Structure" page heading) — drill-through behavior unchanged.
- No horizontal scroll at 1440×900 (`scrollWidth === clientWidth === 1425`).

### UT-07 — Top-up Runs and Index Reconciliation sections still render correctly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-29-evidence/UT-07-result.png` (full-page crop covering both sections in full, including all 14 failed top-up pairs' verbatim detail and the reconcile drift blocks — all legible)
- Top-up Runs section's latest-counts (`data-testid="desk-topup-run-latest-counts"`) unchanged: "0 reused · 390 fetched · 0 unchanged · 14 failed".
- DOM-scoped check: neither the Top-up Runs `<section>` nor the Index Reconciliation `<section>` contains any `screenrun-` text — no state leakage from the new Screen Runs section.
- `h2` heading order top-to-bottom confirmed: Provenance, Briefing, Skipped Members, Screen History, "Run Screen / Top-up / Reconcile Index", Top-up Runs, Index Reconciliation, Screen Runs (last) — matches the spec's required visual order exactly.

### UT-08 — The Screen Runs panel is discoverable without special knowledge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-29-evidence/UT-08-result.png` (crop showing the tail of Index Reconciliation — "Drift after (0) no drift" — immediately followed by the "SCREEN RUNS" panel heading, with no unrelated content in between)
- `getBoundingClientRect()` (viewport-relative, captured at a single scroll instant) on the Index Reconciliation and Screen Runs sections showed the Screen Runs section beginning just 24px below where Index Reconciliation ends (top 1415.5 vs. bottom 1391.5 in that instant's viewport-relative coordinates) — i.e. back-to-back with normal section spacing, not separated by any extra content — reachable within a single continuous scroll. (See the Screenshot Tooling Note below: these coordinates are relative to a nonzero scroll offset, not document-absolute, but the *relative* gap between the two sections — the only thing this check depends on — is unaffected.)
- All three sibling sections (Top-up Runs, Index Reconciliation, Screen Runs) share the identical `className="mt-6"` on the `<section>` and the identical heading class (`mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500`) on their `<h2>` — consistent capitalization/style ("SCREEN RUNS" rendered uppercase via CSS, matching its siblings).
- Nav bar unchanged (Cockpit / Structure / Desk only) — no new link, tab, or menu item was added; this is a same-page scroll-to section as specified.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-05 — A failed run's exact error and raising member are shown verbatim
**Verdict:** SKIPPED
**Reason:** Per the test plan's own precondition note, this scenario "cannot be triggered through normal UI operation" — it requires a fixture-scoped backend serving a `ScreenRunStore` whose latest record has been deliberately planted with `state: "failed"`, a verbatim `error`, and a `failed_member`. Producing this would require standing up a second backend instance (on a spare port, pointed at a scratch `TAPEOLOGY_DESK_SCREEN_LOG_DIR` with a hand-crafted failed record file) plus a second frontend instance pointed at that backend, since the pinned frontend at :3301 always talks to the pinned backend at :8301 which serves the real ambient store. Standing up parallel infrastructure beyond the pinned rig is out of scope for browser QA (which drives the existing app, not new server instances) and risks conflicting with the harness's ownership of ports 3301/8301. This exact `state: "failed"` code path (raising member + verbatim error persisted, no snapshot written, no fabricated screen id) is covered by the backend's own TC-6 test in `apps/backend/tests/test_desk_screen_compute.py`, per the dev handoff. This is a P2 test and does not affect the PASS verdict (only P1 smoke/happy-path tests gate it).

---

## Screenshot Tooling Note

Mid-run, the browser tool's `screenshot` action was found to return a blank solid-navy frame
(constant 5,853-byte PNG, `rgb(2,6,23)` — the app's own background color, no content) for every
capture taken after the page had been scrolled via either an `eval`-triggered `scrollIntoView()`/
`scrollTo()` **or** the tool's own native `scroll` action — confirmed by directly viewing the saved
PNGs. A plain `click` on an off-screen element (which auto-scrolls internally) did not trigger the
bug, which is how UT-06's screenshot came out correct on the first attempt. The fix used for every
other test: `screenshot` with `{"fullpage": true}` from an unscrolled page (captures the entire
document — verified at 1425×8478px, non-blank, fully legible) followed by a local PIL crop to the
relevant section. This also surfaced that the `/desk` page's true rendered height (8,478px with two
screen runs recorded and the full 100-row ranked briefing table) is far taller than an earlier
in-run viewport-relative `getBoundingClientRect()` reading suggested — that earlier reading was
relative to a then-nonzero scroll offset, not the document origin; it does not affect any test's
verdict since all of UT-06/07/08's substantive checks (heading order, `className` equality, relative
section-to-section proximity, drill-through navigation) were computed from same-instant relative
comparisons or from `testid`/text-content presence, none of which depend on absolute scroll
position. UT-04's screenshot could not be recovered because its precondition (a genuinely empty
screen-run ledger) was consumed by this same session's own real UT-02 "Run Screen" click before this
bug was found; DOM-text evidence captured live at the time stands in its place (see UT-04 above).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (headless, CDP 127.0.0.1:9222), viewport 1440×900
- **Test Date:** 2026-07-31
- **Evidence directory:** `reports/qa/goal-desk-iter-29-evidence/`
- **Data store:** the real ambient `apps/backend/.data/` store (not a scoped fixture) — the Screen Runs ledger was genuinely empty at the start of this run, which doubled as UT-04's precondition; UT-02/UT-03 then produced two real, durable run records via the actual UI controls.

---

## Golden Replay Script

Wrote `runs/goal-session-desk/journey-scripts/J-18.json` (read-only: `goto` + `expect` steps only, no click on "Run Screen"), mirroring the J-09 precedent — the button triggers a real ~101-member walk whenever the day's five pins are new, so future regression replays re-read the durable run records this session's real clicks already left on the ambient store rather than re-triggering an expensive/variable-duration compute. Lint-checked clean: `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-desk/journey-scripts --journeys J-18` → `J-18 ok`.

---

## Regression Lanes (Deterministic Replay)

Per dispatch instructions, J-03, J-04, J-05, J-06, J-07, J-09, J-10, J-12, J-16, J-17 were already re-verified via stored golden-script replay before this dispatch and are not re-tested or re-reported here; their rows merge into the results automatically.
