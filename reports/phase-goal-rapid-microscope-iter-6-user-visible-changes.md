# Phase goal-rapid-microscope-iter-6 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-6
**Date:** 2026-08-17
**Written by:** ui-impact-analyst

---

**Context (read this first):** this iteration's entire diff is two backend Python files —
`apps/backend/app/research/walkforward.py` and `apps/backend/tests/test_walkforward.py` (confirmed
via `git diff --stat`: 2 files changed, 0 `.tsx`/frontend files touched). The plan declares
`Frontend Present: yes` not because any UI shipped, but as a documented mechanical workaround: the
browser-QA harness's `detect_frontend_in_plan` check otherwise skips the ENTIRE browser lane —
including the required-still-passing regression journeys — whenever a plan says `Frontend Present:
no`, which silently happened in iterations 4 and 5. So the sections below are short and factual:
there is genuinely no new UI to describe this iteration.

---

## What Users Can Now Do

None. This iteration adds no new page, button, field, or served value an operator can act on. Both
fixes land inside an already-shipped backend engine (`run_diagnostic_walkforward`) that has no
dedicated UI section of its own yet — the Desk page's Walk-Forward rendering is deferred to a
separate, later iteration (J-08). Confirmed by grep: zero references to "walkforward" or
"walk-forward" anywhere under `apps/frontend/`.

## What Changed in the Visible UI

None. No page, component, or navigation element changed this iteration. `GET
/research/desk/micro/walkforward`'s response shape is unchanged, and the one Desk-page component
that reads the sibling `GET /research/desk/micro/readiness` endpoint (`MicroReadinessSection` in
`apps/frontend/app/desk/page.tsx`) was not touched — confirmed via `git diff --stat` (zero frontend
files in this diff).

## What Old Behavior Changed

- **Walk-forward compute — command line and compute route only, no UI surface yet.** Previously,
  running the walk-forward diagnostic against a corpus with fewer than 105 usable trading sessions
  would silently finish with an empty fold report and no explanation (`build_folds` returning
  `[]`). Now it refuses immediately with a typed message naming the exact shortfall (e.g., "11 <
  105") — whether triggered via `python -m app.research.walkforward --diagnostic` (prints the
  message, exits non-zero) or via `POST /research/desk/micro/walkforward/compute` (the run
  resolves to `{"state": "failed", "error": "<message>"}`). Today's real corpus (154 sessions) is
  well above the floor, so an operator using the product today sees no difference — this only
  matters once a smaller corpus reaches the same path, and no frontend page consumes this endpoint
  yet, so there is nowhere in the UI this would currently be seen even when it does trigger.

## Not Visible Yet

- **The typed "insufficient sessions" refusal** (`InsufficientSessionsForFoldsError`) is now
  reachable from the CLI and the compute route, but there is still no Desk-page Walk-Forward
  section to display its message — that UI is explicitly deferred to a later iteration (J-08).
- **The tick-corpus exposure-registry seeding fix** (marking the 12 legacy tick symbol-days
  "exposed" under a new internal `corpus_id`, `tick_legacy_symbol_days_v1`) has no user-facing
  surface at all, ever — it is internal bookkeeping inside the walk-forward engine's own exposure
  registry, a completely different mechanism from the `exposure_state` column the Desk page's
  Microscope Readiness section already renders (that column reads a separate, per-shard value and
  is proven unchanged by this iteration's own verification — still `exploratory` for all 18
  shards).

---

## Regression note (why a test plan exists despite no UI change)

Because `Frontend Present: yes` forces the browser lane to genuinely dispatch this iteration —
likely for the first time in three iterations — the test plan and operator guide below are a
**regression pass over pre-existing, unmodified surfaces**, not a walkthrough of new capability:
J-01's "Microscope Readiness" section on `/desk` (overdue a fresh, non-fabricated evidence
screenshot after 2 iterations of the browser lane silently skipping) and the 13-step whole-product
kept-product sentinel (`journey-scripts/J-10.json`, covering the cockpit `/`, `/structure`, and
several `/desk` sections). See `reports/phase-goal-rapid-microscope-iter-6-ui-surface-map.md` for
the full surface-by-surface breakdown.
