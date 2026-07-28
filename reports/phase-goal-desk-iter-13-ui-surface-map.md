# Phase goal-desk-iter-13 — UI Surface Map

**Phase:** goal-desk-iter-13
**Date:** 2026-07-28
**Written by:** ui-impact-analyst

---

## Changed-File Classification

Per `.claude/skills/diff-to-ui-impact.md`'s categories (frontend-direct / backend-api /
backend-internal / config), **zero files this iteration fall into any of them.** Every file this
iteration touched is a documentation or evidence artifact living outside the application's runtime
source tree (`apps/backend/app/`, `apps/frontend/`) — confirmed independently:
`git diff --stat -- apps/backend/app apps/frontend` returns no output (zero diff) as of this report.

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `docs/handoffs/goal-desk-iter-13-dev.md` (new) | documentation | none | The dev handoff itself — a process record, not application code or a rendered surface. |
| `reports/phase-goal-desk-iter-13-smoke-replay-results.md` (new) | documentation/evidence | none | Regression-replay report (7/7 PASS) — a pipeline artifact describing test results, not part of the running application. |
| `reports/qa/goal-desk-iter-13-evidence/J-01-verify.png` … `J-08-verify.png` (7 new; J-06 excluded, no browser surface) | evidence (screenshot) | none | Screenshot evidence from replaying already-shipped, unchanged journeys — proves no regression, introduces no UI. |
| `reports/qa/goal-desk-iter-13-evidence/UT-J-09-empty-fullpage.png` (new) | evidence (screenshot) | none (documents existing UI) | Full-page capture of the already-shipped `/desk` honest-empty Top-up Runs state (iteration-11 code, unchanged). |
| `reports/qa/goal-desk-iter-13-evidence/UT-J-09-empty-topup-section.png` (new) | evidence (screenshot) | none (documents existing UI) | Cropped/upscaled close-up of the same capture, for legibility. |
| `reports/qa/goal-desk-iter-13-evidence/UT-J-09-populated-fullpage.png` (new) | evidence (screenshot) | none (documents existing UI) | Full-page capture of the already-shipped `/desk` populated Top-up Runs state, same still-live rig as the empty capture. |
| `reports/qa/goal-desk-iter-13-evidence/UT-J-09-populated-topup-section.png` (new) | evidence (screenshot) | none (documents existing UI) | Cropped/upscaled close-up of the same capture, for legibility. |

**Confirmed NOT touched** (the complete 16-file out-of-scope list, zero diff on every one):
`desk_topup_log.py`, `desk_topup_compute.py`, `desk_routes.py`, `desk_screen.py`,
`desk_coverage.py`, `tradability.py`, `levels.py`, `bars.py`,
`apps/frontend/app/desk/page.tsx`, `lib/types.ts`, `lib/api.ts`, `StructureChart.tsx`,
`PriceChart.tsx`, `config.py`, `meta.py`, `app/mcp/__init__.py`.
`runs/goal-session-desk/journey-scripts/J-09.json` was also not touched this iteration.

---

## Affected UI Surfaces

No UI surface changed this iteration. Under the skill's own definition (a route/page/component/
form/modal/table/chart/nav element that *changed*), zero rows qualify — none of this iteration's
changed files fall into the `frontend-direct`, `backend-api`, or `full-stack` categories that would
map to a surface here.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| *(none — no UI surface changed this iteration)* | | | | |

---

## Re-Verified This Iteration (Zero Code Diff — Evidence Only)

Although no surface *changed*, this iteration's entire purpose was producing fresh, specific
evidence about surfaces that already exist, unmodified. Listed separately from the (empty) table
above so the distinction stays unambiguous: nothing here is a code change, only newly captured proof
of existing behavior. Each "What to Test" reproduces the exact check this iteration itself performed.

### J-09 target: `/desk` Top-up Runs panel (shipped iteration 11, code unchanged)

| Route / Page | Component / Element | Evidence Produced | What to Test (reproduces this iteration's own check) |
|---|---|---|---|
| `/desk` | "Top-up Runs" panel, honest-empty state (`aria-label="Top-up runs"`, `data-testid="desk-topup-runs-empty"`) | `UT-J-09-empty-fullpage.png` + `UT-J-09-empty-topup-section.png` | On a freshly-seeded scoped backend+frontend pair (never a prior iteration's rig) with `GET /research/desk/topup/runs` confirmed returning `{"runs": [], "latest": null}`, load `/desk` with both processes already live and confirm the Top-up Runs panel at the bottom of the page reads exactly "No top-up runs recorded yet." with zero run rows. Capture the screenshot only after the frontend is already live — not before it exists. |
| `/desk` | "Top-up Runs" panel, populated state — run table + latest-run detail + failed-pairs list (same component, same iteration-11 code) | `UT-J-09-populated-fullpage.png` + `UT-J-09-populated-topup-section.png` | On the SAME still-live rig used for the empty-state check above (never restarted or swapped), record 3 checkpoint top-up runs in order — one ordinary (`state: done`, `pairs_attempted == pairs_total`), one cancelled mid-walk (`state: cancelled`, `pairs_attempted < pairs_total`), one with an induced failed pair — then reload `/desk` and confirm one screenshot legibly shows all three together: the 3-row run table, the latest run's "N of M pairs attempted" line with its per-outcome (`reused`/`fetched`/`failed`) counts, and the failed pair's own verbatim detail text. This iteration's own recorded example reads "state: done · 404 of 404 pairs attempted · 0 reused · 403 fetched · 1 failed" and "Failed pairs (1): AAPL 1h — no data for that window". |

### Regression smoke-replay set (J-01–J-05, J-07, J-08 — unchanged, re-confirmed only)

Full detail and command in `reports/phase-goal-desk-iter-13-smoke-replay-results.md`.

| Route(s) | Journey | What It Confirms | What to Test |
|---|---|---|---|
| `/desk` | J-01 — Universe ingestion | `desk-provenance` block still shows "Universe snapshot" and the frozen fingerprint `08e471b10130e1e2` | Replay `journey-scripts/J-01.json` via `demo_runner.py --mode verify` against a scoped backend/frontend pair; confirm the run reports PASS with 0 failed steps and `UT-J-01`'s screenshot shows the provenance block with a real (non-placeholder) snapshot id. |
| `/desk` | J-02 — Coverage + top-up | `desk-screen-rows-table` still shows per-symbol "coverage" and "tick evidence" columns | Replay `journey-scripts/J-02.json`; confirm PASS with 0 failed steps and the screenshot shows the coverage/tick-evidence columns populated, not blank. |
| `/desk` | J-03 — The screen | `desk-screen-rows-table` still shows a "Class A" tradability class; `desk-history-table` still lists dated snapshots; `desk-provenance` still shows the config fingerprint | Replay `journey-scripts/J-03.json`; confirm PASS with 0 failed steps and the screenshot shows at least one "Class A" row and a non-empty history table. |
| `/desk` | J-04 — The `/desk` briefing page | Nav still labels the page "Desk"; the page title, "The latest screen over the registered universe" copy, the rows table, and the history table all still render; nav can still reach "Cockpit" | Replay `journey-scripts/J-04.json`; confirm PASS with 0 failed steps and the screenshot shows the full briefing layout (title, descriptive copy, rows table, history table, nav) with no missing section. |
| `/desk` → `/structure` | J-05 — Ledger history + drill-in | Clicking a `desk-history-row` still shows "Viewing the recorded screen for `<date>` — not the latest."; clicking a `desk-screen-row` still client-side-navigates to `/structure` and shows the tradable-map table with the pinned "298.02–300.1001" band | Replay `journey-scripts/J-05.json`; confirm PASS with 0 failed steps and the screenshot shows the `/structure` page reached via the drill-in click (not a fresh page load) with the tradable-map table populated. |
| `/` and `/structure` | J-07 — Regression sentinel | Cockpit's Simulated "Watch" flow still reaches "Buyer Control"; `/structure`'s symbol/as-of load still shows the "300.11" resistance figure, the tradable-map chart caption, and a rendered chart canvas | Replay `journey-scripts/J-07.json`; confirm PASS with 0 failed steps and the screenshot shows both the cockpit watch state and the loaded `/structure` chart. Note: this iteration's first replay attempt transiently timed out on this journey's own step-4 wait (unrelated to any code this iteration touched) and passed cleanly on immediate retry — disclosed, not hidden, in the smoke-replay report. |
| `/desk` | J-08 — Ranked briefing rows name their basis bar | `desk-row-basis` still reads "`<N>`d before as-of" for the latest screen and "basis not recorded in this snapshot" for an older, pre-basis-field snapshot (2026-07-25); the "Latest" button still restores the "d before as-of" reading | Replay `journey-scripts/J-08.json`; confirm PASS with 0 failed steps and the screenshot shows both basis-text variants (present-for-latest, honestly-absent-for-older) captured in sequence. |

None of these seven journeys' own golden steps click a Run Screen/Top-up/Compute control — verified
by inspecting each script before replay (see `reports/phase-goal-desk-iter-13-smoke-replay-results.md`)
— so none of them exercise a code path this iteration could have disturbed even indirectly.

---

## Backend-Only Changes (No UI Impact)

None — no backend source file changed this iteration (zero diff on `desk_topup_log.py`,
`desk_topup_compute.py`, `desk_routes.py`, `desk_screen.py`, `desk_coverage.py`, `tradability.py`,
`levels.py`, `bars.py`, `config.py`, `meta.py`, `app/mcp/__init__.py`). See "Changed-File
Classification" above for the complete list of documentation/evidence files this iteration actually
touched — none of them are backend code either, so there is nothing to place in this section beyond
what is already itemized there.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 0
- **Documentation/evidence-only files changed:** 11 (1 dev handoff + 1 replay report + 9 screenshots
  — see "Changed-File Classification")
- **Surfaces re-verified with fresh evidence, zero code diff:** the `/desk` "Top-up Runs" panel
  (both honest-empty and populated states, this iteration's actual target) plus the J-01–J-05,
  J-07, J-08 regression set (`/desk`, `/`, `/structure`) — see "Re-Verified This Iteration" above
  for exact reproduction steps.
