# Phase goal-desk-iter-16 — UX Regression Review

**Date:** 2026-07-29

**Verdict:** UX-REGRESSION-WARN

---

## Process note (evidence sourcing)

Per this review's instructions, reachability/click-depth is normally consumed from qa's live
"UI Evolution Audit" block and, in goal mode, `coherence.md`. Neither exists for this iteration:

- `reports/qa/goal-desk-iter-16-qa.md` contains no "UI Evolution Audit" section — a departure from
  iterations 1, 13, 14, and 15 of this same session, which all carried one. The report substitutes
  a "Known Issues" note and a TC-by-TC table instead.
- `runs/goal-session-desk/iter-16/coherence.md` does not exist yet. Trace-log ordering
  (`runs/goal-session-desk/trace/022*.log`) shows coherence-auditor runs AFTER ux-regression-reviewer
  and the main auditor in this pipeline's actual iteration order (confirmed from iter-15's trace:
  `...0223-browser-qa-agent → 0224-demo-narrator → 0225-ux-regression-reviewer → 0226-auditor →
  0227-coherence-auditor...`), so it is not available to consume, not merely skipped.

In their absence I fell back to the next-best live-browser evidence actually produced this
iteration: `reports/phase-goal-desk-iter-16-ui-test-results.md` /
`.llm.md` (browser-qa-agent, UT-01..UT-14 + regression journeys) and
`reports/phase-goal-desk-iter-16-regression-replay-results.md` (deterministic replay, 8/8). This is
real click-by-click DOM evidence, not a substitute audit — see the discoverability findings below,
which are built directly from it.

---

## New Capability Discoverability

### Capability A — Individually addressable screen snapshots (id-based Screen History selection)

**Navigation path:** `/desk` (no new page, no nav change) → scroll to Screen History → click any
row. Zero added click-depth versus before this iteration; the same click that already existed now
resolves correctly for same-date pairs.

**Live-browser evidence:** Strong. UT-01 (page loads clean) → UT-02 (click earlier `2026-07-27` row,
`eval()`-confirmed sole `data-selected="true"`, banner text, Provenance id/`created_utc` exact
match, NFLX `1d` badge `data-has-bars="false"`) → UT-03 (click the later sibling row, highlight moves
exclusively, Provenance updates, badge flips to `data-has-bars="true"`) → UT-05 (default-view
highlight tracks `created_utc`, not date) → UT-06 (Provenance field order/values exact) → UT-08
(toggle + "Latest" revert exact) → UT-09 (single-recording dates unaffected). This is one of the
more thoroughly live-verified capabilities I've seen in this session's UX reviews — every claimed
behavior has a DOM-level assertion behind it, not just a screenshot.

**Assessment:** Discoverable. No hidden menu, no undocumented parameter — the existing click path
just got smarter.

### Capability B — `created_utc` per Screen History row

Live-verified (UT-04): the new "recorded" column sits between "date" and "rows", and the two
same-date rows read distinct values without opening either. Discoverable at a glance, no click
required.

### Capability C — Provenance panel `id` / `created_utc` rows

Live-verified (UT-06): both new `Metric` rows render in the documented position, updating on every
history-row click. Discoverable.

### Capability D — Ledger `integrity_errors` disclosure (Screen History, Top-up Runs, Index Reconciliation)

**Navigation path:** `/desk` → scroll to the relevant section. Correctly positioned per the ui-test-
designer's own guide (`reports/phase-goal-desk-iter-16-what-to-click.md` step 8) and confirmed by
source (`apps/frontend/app/desk/page.tsx:744-746`, `:927-929`, `:1395-1397` — three
`IntegrityErrorsNote` call sites with distinct `data-testid`s: `desk-topup-runs-integrity-errors`,
`desk-reconcile-runs-integrity-errors`, `desk-screen-history-integrity-errors`).

**Live-browser evidence: absent for the positive case, across every lane that ran this iteration.**
- Browser-qa-agent explicitly SKIPPED UT-11/UT-12/UT-13 (the three tests that plant a corrupt file
  and check the note renders), citing no scoped second backend/frontend rig was provided
  (`reports/phase-goal-desk-iter-16-ui-test-results.md` Skipped Tests section). Only UT-10 ran — the
  negative case (no note when the store is clean).
- The demo-narrator's `[NEW]`-flagged walkthrough step 8 is titled "confirm no integrity errors" —
  i.e., it also only exercises the negative case against the real, currently-clean ambient store
  (`reports/phase-goal-desk-iter-16-demo-results.md`).
- The operator "what to click" guide's step 8 likewise only describes the negative case ("NO amber
  ... note anywhere") and lists an amber note appearing as a "Common Issue," never as an expected,
  demonstrated state.

So across QA, demo, and the operator guide, nobody has ever visually observed this iteration's
headline second capability — "any ledger's own file-integrity problem is now visibly disclosed" —
actually disclosing anything. What exists is: (a) solid backend test coverage with planted corrupt
files (`test_desk_topup_log.py`, `test_desk_index_reconcile.py`, confirmed passing in the QA report's
1426/1426 suite run), and (b) a source-code-level confirmation that the three `IntegrityErrorsNote`
call sites are wired to the right payload field with the right conditional-render gate (same pattern
UT-10 exercised for the empty-array branch).

**Assessment:** Not hidden (position/label are correct and match the plan), but **unverified in a
live render** — a QA-evidence gap, not a demonstrated defect. Downgraded from "hidden" to
"undiscoverable-by-evidence" because the one thing that would prove it discoverable (a screenshot of
the note actually appearing) does not exist anywhere in this iteration's artifact set.

---

## Regression Risk

All components this iteration touches are used by prior-phase journeys. Regression coverage ran in
two independent lanes this iteration — LLM-driven browser-qa (`UT-J-03/04/05/07/08/09/10/11`) and
deterministic Playwright replay (`reports/phase-goal-desk-iter-16-regression-replay-results.md`,
8/8) — both 8/8 PASS with a real page screenshot per journey. Risk assessment per shared component:

| Shared component | Prior-phase feature(s) | Risk |
|---|---|---|
| `DeskHistoryRow`/`DeskHistoryTable` (selection + highlight) | J-05 (click-through to a past screen's own rows, drill-in to `/structure`), J-10 (repair — the same-date pair this journey's selection logic is built directly on top of) | LOW — UT-J-05/UT-J-10 both PASS in both lanes; UT-02/03/05/08/09 additionally give row-level DOM proof the id-based rewrite didn't regress single-recording dates |
| `DeskProvenance` | J-04 (briefing provenance), J-08 (basis/tradability) | LOW — UT-J-04/UT-J-08 PASS; UT-06/UT-07 confirm the two new rows + reworded note render alongside the unchanged existing rows in the documented order |
| `TopupRunsSection` | J-09 (top-up run ledger) | LOW — UT-J-09 PASS in both lanes; UT-10 confirms no false-positive note against real data. The new-note positive case itself is unverified live (see Capability D above), which is a discoverability gap, not an observed regression |
| `ReconciliationSection` | (Index Reconciliation ledger, pre-existing) | LOW — no dedicated regression journey ID surfaced for this section specifically, but J-07 ("the kept product stands — regression sentinel") PASS covers the page broadly; same positive-case-unverified caveat as Top-up Runs |
| `DeskPopulatedScreen`/`DeskPage` (layout host) | J-03, J-07, J-11 | LOW — UT-J-03/07/11 PASS; UT-01 confirms all 7 panel headings still render with no console errors |

No potential regression rises above LOW. This is a well-evidenced iteration on the regression axis.

---

## UI vs Backend Parity

| Backend capability | UI exposure |
|---|---|
| `GET /research/desk/screen?id=` | Fully wired and live-verified (Capability A) |
| `integrity_errors` on `GET /research/desk/topup/runs` | Wired (source-confirmed), **not live-verified** (Capability D) |
| `integrity_errors` on `GET /research/desk/coverage/reconcile/runs` | Wired (source-confirmed), **not live-verified** (Capability D) |
| `integrity_errors` on `GET /research/desk/screen` (list) | Wired this iteration for Screen History (source-confirmed), **not live-verified** (Capability D) |
| `integrity_errors` on `GET /research/desk/universe` | **Still zero UI exposure of any kind** — pre-existing since J-01, named in this iteration's own IN SCOPE text as a fourth section to build, not built because no Universe list/table exists anywhere in the frontend to extend (only a single `universe_snapshot_id` string inside Provenance). Honestly disclosed by the dev handoff, the review (routed to auditor/product-manager as a MINOR), and the ui-impact-analyst's "Not Visible Yet" section — this is not a surprise finding, but it is a real, still-open gap |
| `id`+`date` 4xx refusal | No UI surface (frontend never constructs this request) — correctly documented as backend-only, not a gap |

---

## Flags

### Hidden Capabilities
- **Universe ledger `integrity_errors`** — has existed on `GET /research/desk/universe` since J-01
  (multiple iterations ago) and still has no rendering path anywhere in the app. This iteration's own
  spec named it as in-scope and the team correctly declined to invent an untested new UI section
  rather than force a bad one in — but the underlying gap is now confirmed to have persisted across
  at least this many iterations. Recommend either a follow-up journey to build a minimal Universe
  ledger section, or a goal.md wording correction (both already proposed by the reviewer's routing
  note) so this doesn't keep getting silently re-named into future scope text.

### Undiscoverable Capabilities
- **Ledger integrity-error disclosure (Screen History, Top-up Runs, Index Reconciliation)** — code
  is correctly positioned and labeled per plan, but no artifact in this iteration's full pipeline
  (browser-qa, demo-narrator, operator "what to click" guide) contains a screenshot or DOM assertion
  of the note actually rendering with real corrupt data. All three lanes exercised only the negative
  (empty-array, no note) case. To close this, a future dispatch needs the scoped second-rig
  (`TAPEOLOGY_DESK_TOPUP_LOG_DIR`/`TAPEOLOGY_DESK_INDEX_RECONCILE_DIR`/`TAPEOLOGY_DESK_SCREEN_DIR`
  pointed at a planted-corrupt-file copy) that UT-11/12/13 note they were not given.

### Potential Regressions
- None found. All 5 shared components carry LOW risk with dual-lane (LLM + deterministic replay)
  evidence; see Regression Risk table above.

### Visual Consistency
- New elements (the "recorded" column, the two Provenance `Metric` rows, `IntegrityErrorsNote`)
  reuse existing component patterns per the plan (`Metric` for Provenance rows, an inline-note
  pattern matching `desk-provenance-signature-note` for integrity lines) rather than introducing new
  visual primitives. No layout restructuring. Consistent with the established dark/dense/monospace
  `/desk` styling per the dev handoff and reviewer's PASS_WITH_NOTES on standards. Nothing in the
  live-verified UT screenshots (UT-01 through UT-09) suggests style drift, though I have not
  independently opened the PNGs pixel-by-pixel — this assessment relies on the qa/browser-qa report's
  own text-dump verification plus the reviewer's `standards.architecture_principles: pass`.

---

## Recommendation

1. Before this iteration is treated as fully closed on the UX axis, capture at least one real
   screenshot (or DOM assertion) of the ledger integrity-error note actually rendering — UT-11/12/13
   should be un-skipped with the scoped rig they name as missing. This is the one place where "built"
   and "seen working" currently diverge.
2. Carry forward the Universe-ledger gap as an explicit backlog item (not silently re-named into a
   future iteration's IN SCOPE text again) — either build a minimal Universe ledger section or correct
   goal.md to stop naming it as a fourth ledger.
3. No action required on the regression axis — this iteration's dual-lane regression evidence (8/8
   LLM + 8/8 deterministic replay) is unusually strong.
