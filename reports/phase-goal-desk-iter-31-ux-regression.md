# Phase goal-desk-iter-31 — UX Regression Review

**Date:** 2026-07-31

**Verdict:** UX-REGRESSION-PASS

## New Capability Discoverability

None new this iteration — the execution plan, phase spec, and both ui-impact-analyst reports
(`reports/phase-goal-desk-iter-31-user-visible-changes.md`,
`reports/phase-goal-desk-iter-31-ui-surface-map.md`) are explicit and consistent: this iteration
lands two honesty/correctness fixes that iteration 30's depth-downgrade dropped, plus a
repo-hygiene revert. No new page, section, control, `data-testid`, endpoint, or `Config` field.

The two fixes correct rendering/derivation of already-registered fields on the "Screen Runs"
section shipped at iter-29 (`docs/handoffs/goal-desk-iter-29-frontend.md`):
- **Reused-run suppression** (`LatestScreenRunDetail`, `apps/frontend/app/desk/page.tsx`): a
  `done && reused` latest run no longer shows the amber "N members not reached" note or the
  "0 ranked · 0 skipped..." counts line next to its own honest "reused `<id>` — no walk was
  performed" outcome text. Navigation path is unchanged from iter-29: nav → Desk (1 click) →
  scroll to "Screen Runs" panel → "Latest run" block (0 additional clicks, no new discoverability
  burden). qa's browser-qa results (`reports/qa/goal-desk-iter-31-qa.md`, TC-4) and the merged UI
  test results (`reports/phase-goal-desk-iter-31-ui-test-results.md`, UT-02) both confirm this
  live against the ambient store's current latest run (`screenrun-2026-07-31-fe0829e64a0d`):
  neither `desk-screen-run-latest-unreached` nor `desk-screen-run-latest-counts` is present in the
  DOM, while `desk-screen-run-latest-outcome` still reads the honest reuse text.
- **`failed_member: null` on an `attempted == 0` crash** (`desk_screen_compute.py`): backend-only
  correction with no live UI trigger on the current ambient store (correctly disclosed as "Not
  Visible Yet" in the user-visible-changes report, proven instead by
  `test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null` plus the unmodified
  `test_tc6_...` regression guard). This is an honest scope call, not a hidden capability — there
  is nothing for a user to discover until a crash-before-any-attempt actually occurs, and the
  frontend's pre-existing `?? "(member not recorded)"` fallback (page.tsx ~1346, untouched this
  iteration) will render it correctly whenever that happens.

Per qa's UI Evolution Audit (`reports/qa/goal-desk-iter-31-qa.md`, "Applicability: Not applicable
to this iteration... The UI audit rules apply only to iterations with new capabilities or
information. This iteration modifies rendering behavior of already-registered fields... for a
specific state transition, which is a bug fix, not a new feature.") — this reasoning is sound and
I did not re-derive it. No `coherence.md` was produced for iter-31 (goal-slice/decomposer-only
artifacts present in `runs/goal-session-desk/iter-31/`), consistent with a fix-only, no-new-journey
iteration.

Label clarity: unaffected — no label changed. Visual feedback: unaffected — the suppression is a
pure conditional removal of two elements; the remaining `screenRunOutcomeText` line already reads
clearly ("reused `<id>` — no walk was performed"). No audit contradiction between qa's UI Evolution
Audit and any other artifact.

## Regression Risk

| Prior feature (shipped) | Shared component touched this iteration | Risk |
|---|---|---|
| J-18 "Screen Runs" section (iter-29): full ledger table + latest-run detail | `LatestScreenRunDetail` in `apps/frontend/app/desk/page.tsx` | **Low** — verified via `git diff 48c5fc2 -- apps/frontend/app/desk/page.tsx`: exactly two lines changed, both additive `&&` guards (`unreached > 0 && !(run.state === "done" && run.reused) && (...)` and `run.state === "done" && !run.reused && (...)`); no other JSX, `data-testid`, or copy string touched. `desk-screen-runs-table` (the history table J-18's golden replay targets) is untouched. |
| J-18's `run_screen_and_record` failure path | `apps/backend/app/research/desk_screen_compute.py` `except Exception` handler | **Low** — `git diff 48c5fc2 -- apps/backend/app/research/desk_screen_compute.py` shows exactly one line changed (`attempted < len(members)` → `0 < attempted < len(members)`). `failed_member` has no other consumer besides `desk_screen_log.py` (the writer), `desk_routes.py` (a heavy-key allowlist comment/tuple, unaffected), and this same `page.tsx` line 1346 — confirmed by grep across `apps/`. |
| J-01, J-02, J-03, J-04, J-06, J-07, J-09, J-10, J-12, J-16 (required-still-passing set) | `desk_screen_compute.py` is on the shared write path any screen-producing journey passes through | **Low, evidenced not inferred** — all 10 replayed green (UT-J-01…UT-J-16 in the merged UI test results), plus the full backend suite at 1502 pass/8 skip/0 fail (above the 1,500/8 baseline), fingerprint `08e471b10130e1e2` and MCP tool count 17 both unchanged. |
| Screen-compute live-progress UI (`RunScreenButton`, distinct component, ~page.tsx:1460-1510) | Not touched | **None** — this component has its own independent, already-honest `compute.reused` outcome message ("Reused the snapshot already recorded for this key — `<id>`" vs "Recorded a new snapshot — `<id>`"); it was not part of this iteration's diff and needed no fix. Confirmed by reading the surrounding source; flagged here only to note it is a distinct code path from `LatestScreenRunDetail`, so the two "reused" disclosures staying independently correct is expected, not a gap. |
| Repo build plumbing (`next-env.d.ts`, `tsconfig.json`) polluted at iter-30 | Reverted this iteration | **None (resolved)** — `git diff 48c5fc2^ -- apps/frontend/next-env.d.ts apps/frontend/tsconfig.json` is empty (byte-identical to pre-pollution content); `npm run build` compiled cleanly per both the dev handoff and qa report. No product behavior tied to these files. |

No shared component used by any OTHER prior-phase feature (ranked table, Top-up Runs, Index
Reconciliation, Structure page, Cockpit) was touched. The diff's blast radius is exactly the two
lines the plan specified.

## UI vs Backend Parity

- **Reused-run suppression fix**: backend field (`reused`) was already surfaced pre-iteration;
  this iteration only corrects the frontend's *use* of it. Parity: full, verified live.
- **`failed_member: null` fix**: backend-only field correction; frontend already has the correct
  fallback rendering (`?? "(member not recorded)"`, pre-existing, untouched). Parity: full by
  construction — no UI change was needed because the display-layer contract already handled `null`
  correctly; only the backend was fabricating a wrong non-null value. No backend capability is left
  unexposed.
- No new backend capability was added this iteration (no new endpoint, field, or `Config` key per
  the plan's explicit "No new capability" line and the ui-surface-map's "Backend-Only Changes"
  section, all of which are test-file/build-plumbing-only). Nothing to check for a UI gap.

## Flags

### Hidden Capabilities
- None.

### Undiscoverable Capabilities
- None. Both fixes are corrections to an existing, already-discoverable section (nav → Desk →
  "Screen Runs" panel, 1 click from home, unchanged since iter-29).

### Potential Regressions
- None identified. The diff is confined to the two specific lines the plan named; all touched
  files were diffed directly against pristine baselines (`48c5fc2`, `48c5fc2^`) confirming no
  incidental changes; the required-still-passing journey set (10/10) plus J-18 all replay green;
  full backend suite green at 1502/8/0.

### Visual Consistency
- No new visual pattern introduced — the fix is a pure conditional suppression of two pre-existing
  elements, styled identically to how they already rendered for the states where they still
  appear (fresh walk, cancelled, failed — confirmed byte-unchanged by UT-06's diff check). No
  arbitrary values, no new Tailwind classes, no new component. Consistent with the DESIGN SYSTEM by
  construction (zero new styling surface).

## Recommendation

No action required. This iteration is a scoped, low-risk correctness fix with full live and test
evidence, no new capability to expose, and no measurable regression risk to any prior-phase
journey.
