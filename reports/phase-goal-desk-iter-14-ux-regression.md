# Phase goal-desk-iter-14 — UX Regression Review

**Date:** 2026-07-28

**Verdict:** UX-REGRESSION-WARN

Live product: fully discoverable, zero regressions found, full UI/backend parity — all
independently verified against source, not just against upstream reports. One real, non-blocking
gap: the `[NEW]`-flagged demo-narrator walkthrough (TC-19) does not visually demonstrate the
before/after story it narrates — a recurrence, in a new form, of the exact failure class this
same session's ux-regression-reviewer caught at iteration 13 (see "Flags → Showcase Evidence Gap").

---

## New Capability Discoverability

**Capability:** trigger a reconciliation of the bar-coverage index against the frozen bar store,
from `/desk`; read a durable before/after history.

- **Navigation path:** `/desk` is already in the top nav (Cockpit / Structure / Desk, `meta.py`'s
  `UI_ROUTES`, unchanged this iteration). Home → Desk = 1 click. The trigger button
  (`data-testid="desk-reconcile-button"`) is inside the existing "Run Screen / Top-up / Reconcile
  Index" controls panel, reachable with zero additional clicks past landing on `/desk` (it is
  visible on ordinary scroll, not gated behind a tab/toggle/modal). Total: **1 click** to the
  action. **Verdict: discoverable.**
- **Read-only result panel:** the "Index Reconciliation" section is the LAST section on the page
  (after Provenance, Briefing, Skipped Members, Screen History, controls, Top-up Runs) — confirmed
  by direct source read of `apps/frontend/app/desk/page.tsx:1642-1660`, both new/history sections
  sit outside the screen-state conditional so they render in all four page states (loading,
  unavailable, not-computed, populated), matching the claim in `ui-surface-map.md`. Browser QA's
  UT-10 independently confirmed it is reachable "by ordinary scroll... no toggle/tab needed." This
  continues an established pattern (Top-up Runs, shipped iter-11, occupies the same tier) rather
  than introducing a new one — noted below as a growing-page observation, not a new problem.
- **Label clarity:** "Reconcile Index" / "Index Reconciliation" match `docs/goal.md`'s own J-10
  vocabulary verbatim and sit alongside the equally-technical "Top-up" label this product already
  ships. This is an operator/power-user research tool, not a consumer surface — the label is
  internally consistent with the page's established jargon level, not confusing relative to it.
  No label-confusion flag.
- **Visual feedback:** four distinct button/section states are wired and source-verified —
  idle ("Reconcile Index"), running ("Reconciling…" + phase text + pulsing dot + Cancel, byte-
  identical dot markup to Screen/Top-up's own controls — `page.tsx:957`, `:1042`, `:1127` are
  identical strings), failed ("Retry Reconcile Index" + red error text), cancelled (amber note).
  Idle→running→done was live-verified (UT-04); the failed/cancelled visual states were not
  live-exercised this iteration (no induced-failure or cancel-mid-run checkpoint was recorded for
  Reconcile, unlike Top-up's three-checkpoint recording in iter-11/12/13) — low risk, since the
  CSS/markup is a verbatim copy of already browser-proven Screen/Top-up control states, but
  unverified live for this specific control. Non-blocking; see Recommendation.

## Regression Risk

Independently verified against source (not just against the dev/ui-impact reports) — `git status
--short` and direct `Read` of `apps/frontend/app/desk/page.tsx` and `apps/backend/app/research/
desk_routes.py`:

| Shared component | Prior journey(s) it serves | This iteration's change | Risk |
|---|---|---|---|
| `DeskNotComputedPanel` (iter-4) | J-03/J-04 (pre-screen empty state + Run Screen/Top-up controls) | Gained one new `reconcile` prop, renders `<ReconcileIndexControl>` as a 3rd sibling (`page.tsx:1185-1213`) | **Low** — additive only; `screen`/`topup` props and their render output byte-unchanged |
| `DeskPopulatedScreen` (iter-6) | J-02 (coverage badges), J-03 (ranked table/Screen History), J-05 (drill-in links), J-08 (basis column) | Gained `reconcileControlProps` prop + a 3rd button in its controls panel; Provenance/Briefing/Skipped/Screen History panels (`page.tsx:1264-1298`) are unchanged lines | **Low** — confirmed via source read that only the controls-panel title string and button list changed |
| Controls-panel title/`aria-label` | J-02, J-03 (the two pre-existing buttons live here) | "Run Screen / Top-up" → "Run Screen / Top-up / Reconcile Index"; `aria-label` grew to match | **Low** — `grep` over all 9 `journey-scripts/*.json` golden files found zero references to the old title/aria-label text; nothing to break. Browser QA (UT-03) re-confirmed the new title live |
| Coverage badges (`DeskCoverageBadges`) | J-02 | Zero code diff — confirmed `desk_coverage.py` untouched via `git status --short` (empty). Only the underlying index DATA changes once reconciled | **None** — this is the iteration's own stated goal (badges become correctable), not a side effect |
| Top-up Runs section (J-09, iter-11) | J-09 | Zero change — Index Reconciliation added as an independent sibling `<section>` immediately after it (`page.tsx:1647-1660`) | **None** — confirmed via source read; UT-J-09/UT-03 re-verified Top-up Runs' own empty state unaffected |
| `bar_index.py`, `bars.py`, `tradability.py`, `levels.py`, `desk_coverage.py` | J-01/J-02/J-03 compute paths | Zero diff required (TC-15) | **None** — independently confirmed via `git status --short`, empty output on all five |
| `StructureChart.tsx`, `PriceChart.tsx` | J-05 drill-in, J-07 kept-product (Structure/Cockpit) | Zero diff required (TC-15) | **None** — independently confirmed via `git status --short`, empty output |
| MCP surface (`app/mcp/__init__.py`) | J-06 | Zero diff; new GET route auto-reachable via the existing `/research/` prefix allowlist | **None** — `EXPECTED_TOOLS` still 17 per dev handoff; UT-J-06 re-confirmed live |
| Nav shell (`meta.py` `UI_ROUTES`, `NavBar.tsx`) | All journeys | Untouched | **None** — nav confirmed exactly 3 routes throughout QA session |

All nine required-still-passing journeys (J-01 through J-09) were re-verified this iteration via
deterministic replay + LLM browser QA and reported PASS (`phase-goal-desk-iter-14-ui-test-results.md`,
21/21). Combined with the source-level zero-diff confirmation above, regression risk from this
iteration's changes is **low across the board**.

## UI vs Backend Parity

Independently cross-checked `apps/backend/app/research/desk_routes.py` against
`apps/frontend/lib/api.ts`: all four new routes have a matching frontend function and a matching
rendered UI element —

| Backend route | Frontend function | UI element |
|---|---|---|
| `POST /research/desk/coverage/reconcile/compute` | `triggerDeskReconcileCompute()` | "Reconcile Index" button |
| `GET /research/desk/coverage/reconcile/compute` | `fetchDeskReconcileCompute()` | running/progress/cancel block |
| `POST /research/desk/coverage/reconcile/compute/cancel` | `cancelDeskReconcileCompute()` | "Cancel" button |
| `GET /research/desk/coverage/reconcile/runs` | `fetchDeskReconcileRuns()` | "Index Reconciliation" table + latest-run detail |

No backend capability shipped this iteration lacks a UI access point. The one intentionally
missing piece — no CLI warmer for reconcile, unlike Top-up's CLI — is explicitly and honestly
disclosed in `user-visible-changes.md`'s "Not Visible Yet" section as a deliberate, spec-driven
scope decision (`docs/goal.md`'s J-10 text never names one), not a hidden backend capability. No
parity gap.

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None. (See growing-page note under Recommendation — not currently a discoverability failure.)

### Potential Regressions
None found in the live product. All nine required-still-passing journeys independently
re-confirmed; all named zero-diff files independently confirmed via `git status --short`.

### Showcase Evidence Gap (new finding — not a live-product regression)

The `[NEW]`-flagged demo-narrator walkthrough for J-10 (`reports/phase-goal-desk-iter-14-demo.json`,
`reports/demo/goal-desk-iter-14/`) does not visually demonstrate the before/after narrative TC-19
requires, despite the live product itself working correctly (confirmed via UT-02/UT-04–UT-09 and
the code review above).

- **Verified via MD5 + direct image inspection** (not merely file listings):
  `step-01.png`, `step-02.png`, and `step-06.png` are **byte-identical**
  (md5 `d64f057cf48d0892dce2550153fe33b9`, all 85333 bytes), despite narrating three different
  moments in the story:
  - Step 01 (J-04, not new): "Open the Desk page."
  - Step 02 (J-10, `[NEW]`): "See the repair panel before it has ever run" — point-out claims "The
    panel at the foot of the page reads 'No reconciliation run recorded yet.'"
  - Step 06 (J-10, `[NEW]`): "See the price badge fixed" — point-out claims "AAPL's 1-day coverage
    badge is now lit, matching its neighbors."
  Direct inspection of the shared image shows only the top-of-viewport Provenance/Briefing/Skipped
  Members region — the Index Reconciliation panel is not in frame at all (it is far below the
  fold, per the section order above), so the image supports neither step 02's "empty panel" claim
  nor step 06's "badge fixed" claim distinctly from step 01's own unrelated claim.
- **Root cause, per the demo.json step-02 `capture` block's own note**: the honest-empty
  reconciliation state is a one-way door that had already closed on this rig by the time this
  demo-recording pass ran (an earlier browser-QA dispatch had already triggered a real
  reconciliation to capture TC-18). The demo-narrator's own JSON explicitly anticipated this exact
  failure mode, named the correct fix — splice the genuine pre-run screenshot
  (`reports/qa/goal-desk-iter-14-evidence/UT-02-before-empty-and-dark-badge.png`) over the
  live-recorded `step-02.png` "before this walkthrough ships" — and explicitly cited "iteration
  13's equivalent case" as precedent. **That splice was not performed**: `step-02.png`'s md5
  (`d64f057c...`) does not match the named source file's md5 (`f15f778e...`).
  `reports/phase-goal-desk-iter-14-demo-results.md` does carry one soft note ("Step 02 — expected
  'No reconciliation run recorded yet.' did not appear; recorded anyway") — the self-check the
  capture note predicted did fire — but the remediation it called for was not completed.
- **Undisclosed half of the same defect**: step 06's identical-to-01/02 frame carries **no** soft
  note anywhere in `demo-results.md` or `demo-script.md`, even though it equally fails to
  distinctly show the claimed "badge now lit" state (it cannot, since it is pixel-for-pixel the
  same file as the "before" step).
- **Why this is a recurrence, not a new class of bug**: `docs/handoffs/goal-desk-iter-13-audit.md`
  finding A1 (CRITICAL, fixed) describes the exact same failure shape for J-09's own walkthrough —
  a one-way-door empty state closed before the demo-recording pass ran, producing a
  narration/frame mismatch — and states "the ux-regression reviewer reached the same conclusion
  independently" that iteration. This iteration's demo-narrator visibly tried to apply that
  lesson (the capture-block note references it by name and describes the correct fix) but the
  fix was not actually carried out before this report was written.
- **Why this is WARN, not FAIL**: the live `/desk` product is unaffected — TC-17/TC-18's own
  official evidence (`TC-17-empty-reconciliation.png`, `TC-18-populated-reconciliation.png`,
  `UT-02...`, `UT-07-UT-08...`) are separate, correctly-captured, full-page screenshots that DO
  show the genuine empty and populated states legibly (independently viewed and confirmed). Only
  the demo-narrator showcase gallery — a documentation/communication asset, not the shipped
  feature — is affected. DEFINITION OF DONE's TC-19 bullet is nonetheless not fully met by the
  artifact as it currently stands.

### Visual Consistency

Assessed by direct source read of the new components (`page.tsx:657-905`, `:1080-1213`), not just
by the frontend handoff's own claim:

- Zero new design tokens confirmed: `ReconcileIndexControl`, `DriftList`,
  `IndexReconciliationTable`, `LatestReconciliationDetail` reuse `Panel`, `EmptyState`,
  `LoadingPanel`, `UnavailablePanel`, `HEADER_CELL`/`HEADER_CELL_LEFT`/`LABEL_CELL`/`NUMERIC_CELL`,
  `PRIMARY_BUTTON_CLASS`/`CANCEL_BUTTON_CLASS` — all pre-existing, singly-defined constants, not
  redeclared or forked.
  the file already uses in 8+ other places (`HEADER_CELL`'s own definition, `Metric` captions,
  the provenance note, etc.) — not a new arbitrary value introduced this iteration.
- The running-state pulsing dot (`animate-pulse rounded-full bg-emerald-400`, `page.tsx:1127`) is
  a byte-identical string to Screen's (`:957`) and Top-up's (`:1042`) own pulsing dots — genuine
  pixel-level consistency, not just "similar."
- Color usage (slate palette for structural text, amber-200/70 for cancelled notes, red-300 for
  errors) matches the rest of the page exactly; no new hue introduced.
- No project-wide `DESIGN SYSTEM.md` exists for this codebase (confirmed by search) — consistency
  here is enforced by the shared Tailwind-class-constant convention above, which this iteration
  followed without exception.

## Recommendation

1. **Fix the demo-walkthrough evidence gap before this iteration's showcase artifacts are treated
   as closing TC-19.** Splice `reports/qa/goal-desk-iter-14-evidence/UT-02-before-empty-and-dark-badge.png`
   over `reports/demo/goal-desk-iter-14/step-02.png` (the fix the demo-narrator's own JSON already
   specifies and iteration 13 already used once for the equivalent J-09 case). Step 06 needs a
   distinct frame showing the actually-lit badge/populated panel — a full-page capture cropped from
   `UT-07-UT-08-lit-badge-and-reconciliation.png` (already captured, already proven legible) is a
   ready-made source, mirroring the same splice technique.
2. Optional, non-blocking: no live browser evidence exists yet for the Reconcile control's
   failed/cancelled visual states specifically (as opposed to the byte-identical CSS already proven
   via Screen/Top-up). Low priority given the code-level identity confirmed above; a future
   iteration could record failed/cancelled reconcile checkpoints the way iter-11/12/13 did for
   Top-up, if that history ever needs to be demonstrated.
3. Watch, not act: `/desk` has now accumulated three durable-history panels stacked at the page's
   bottom (Screen History mid-page; Top-up Runs and Index Reconciliation at the very end,
   ~4000px+ of scroll). Not a discoverability failure today (UT-10 confirmed plain-scroll
   reachability), but worth reconsidering (tabs, anchor nav, or a collapsible-panel pattern) if a
   future journey adds a fourth such panel.

No action required on discoverability, live-product regression risk, or UI/backend parity — all
three passed independent verification against source and against this iteration's own extensive
browser-QA evidence.
