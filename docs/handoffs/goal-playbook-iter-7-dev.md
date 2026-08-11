# goal-playbook-iter-7 Dev Handoff

**Phase:** goal-playbook-iter-7
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

J-07 — the playbook back-scan: preview which recorded session dates already carry a playbook
record at the current signature vs. which are missing, trigger one resumable/cancel-safe compute
that walks every planned date through the existing `run_playbook_and_record` entry point, and
review a runs table of what every scan attempt did.

- **`app/research/desk_playbook_backscan.py`** (new module):
  - `plan_backscan(from_day, to_day, bar_store, members, config_fingerprint, playbook_store)` —
    pure, metadata-only. Resolves ONE `playbook_input_signature` (`compute_playbook_input_signature`
    — `list(include_bars=False)`-only) and classifies every CALENDAR day in `[from_day, to_day]` as
    `recorded_at_current_signature` (a `PlaybookStore.find_by_key` hit) or
    `missing_at_current_signature`. Performs zero `BarStore` bar-content reads (proven by a
    stub-store test at both the pure-function and route levels — TC-9). Deliberately does NOT use
    `desk_sessions.recorded_session_dates` (which reads `merged_bars`, a real bar-content read) to
    determine "session-ness" — see the module docstring for why: the plan does not pre-filter
    non-session days, so `refused_non_session` (discovered by the real per-date walk) is a genuine,
    expected outcome rather than one the plan would have hidden.
  - `run_backscan(planned_dates, universe_store, bar_store, config, playbook_store, progress=,
    should_abort=)` — the SOLE walker. Calls `run_playbook_and_record` once per date (never a
    second implementation of detect+measure+record), classifying each outcome as `reused` /
    `recorded` / `refused_non_session` / `failed`; a per-date failure or refusal is caught and the
    walk continues to the remaining dates. Cancel is cooperative, checked before each date starts.
  - `DeskPlaybookBackscanComputeManager` — single-flight, cancellable, progress-publishing
    background job (mirrors `DeskPlaybookComputeManager`/`DeskDeepBackfillComputeManager`). No
    distinct `"cancelling"` visible state (the Data Contract's 5-state enum:
    `idle|running|done|cancelled|error`).
  - `BackscanRunStore` (+ `resolve_desk_playbook_backscan_log_dir`, no new `Config` field) —
    terminal-state-only durable ledger, mirrors `DeepBackfillRunStore`'s three-terminal-state set.
    **One deliberate rule beyond that precedent:** a `"cancelled"` terminal state is logged ONLY
    when `completed >= 1` — a cancel that measured nothing leaves no row at all (TC-10), while a
    cancel with partial progress IS logged with its partial per-outcome counts (TC-5). `"done"`/
    `"error"` always log.
  - `_assert_scoped(root)` (+ `PlaybookNotScopedError`) — TC-13's positive scoping guard. A
    TEST/BROWSER-QA-LANE-ONLY helper (never called from the live HTTP routes — a real operator
    compute legitimately runs with none of the four scoping env vars set). Checks all four:
    `TAPEOLOGY_DESK_PLAYBOOK_DIR`, `TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`,
    `TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR`, `TAPEOLOGY_DESK_UNIVERSE_DIR`.
- **`app/research/desk_routes.py`**: three new routes — `GET /research/desk/playbook/backscan/plan`
  (`?from=&to=`), `POST`/`GET`/`POST .../cancel` on `/research/desk/playbook/backscan/compute`,
  `GET /research/desk/playbook/backscan/runs`. New process-wide singleton manager
  `_desk_playbook_backscan_manager`, exposed via `get_desk_playbook_backscan_manager` (test-
  overridable). Zero diff to any other route in this file.
- **Frontend** — see `docs/handoffs/goal-playbook-iter-7-frontend.md`.
- **`apps/backend/tests/test_desk_playbook_detect.py`**: added the SHORT-side mirror of
  `test_range_trade_degenerate_trigger_reference_below_the_range_low_fails_closed`
  (`_range_trade_degenerate_reference_bars_short` + the TC-12 test) — the `T >= SH` short-side
  degenerate-trigger-reference case, with its own control proving the clause specifically is the
  rejecter. Zero diff to `desk_playbook_detect.py` itself (the fail-closed clause already ships
  symmetrically; the test fixture was empirically verified against the real detector before being
  committed).
- **`apps/backend/tests/test_desk_refresh_chain_guard.py`**: `_EXPECTED_EFFECT_COUNT` 17→19,
  `_EXPECTED_INTERVAL_COUNT` 6→7 (timeout unchanged at 1), `_TRIGGER_CALLS` +2
  (`handleTriggerBackscan(`, `triggerDeskPlaybookBackscanCompute(`) — with the mandatory rationale
  paragraph appended in-source, deriving the new counts from the two new effects (plan-preview read
  + compute-poll-with-terminal-ledger-refresh) the Backscan section adds.
- **`apps/backend/tests/test_desk_ui_guards.py`**: `_PRICE_ARITHMETIC_FIELDS` extended with
  `plan.(total|missing)`, `compute.(planned_total|completed)`,
  `outcomes.(reused|recorded|refused_non_session|failed)` — the panel performs no arithmetic on
  these today, but the IN SCOPE contract ("no client-side arithmetic on served numerics") is guarded
  structurally rather than by convention, matching every prior playbook iteration's own extension.
- **`apps/backend/scripts/seed_playbook_iter7_backscan_fixture.py`** (new) + **`apps/backend/
  scripts/qa_playbook_iter7_fixture_scoped_backend.sh`** (new) — the iter-7 scoped fixture rig,
  extending (not editing) iter-6's own script/seed. Reuses `seed_playbook_fixture_rig.main()`
  verbatim (DECOR/RTAAA/DTAAA on 2026-06-22, already computed), then plants a new member `BSCAN`
  with a plain canonical open_high_break firing session on TWO new dates (2026-06-23, 2026-06-24),
  each with its own 10 prior baseline sessions, and registers a NEW four-member universe snapshot
  (append-only — never edits iter-6's own three-member one). **Note:** registering the fourth
  member changes `playbook_input_signature` (it hashes `members ∪ {SPY}`), so 2026-06-22's own
  three-member record is honestly reported `missing_at_current_signature` too — a real Run Backscan
  click over `[2026-06-22, 2026-06-24]` has genuine work to do on all three dates. Verified live end
  to end (see Tests Run below) — never touched `.data/`.

## Files Changed

- `apps/backend/app/research/desk_playbook_backscan.py` -- new module (plan/walker/manager/ledger + scoping guard)
- `apps/backend/app/research/desk_routes.py` -- wired three new backscan routes + singleton manager
- `apps/backend/tests/test_desk_playbook_backscan.py` -- new, 24 tests covering TC-1..TC-11, TC-13, plus resolve_dir/run_backscan/manager/route unit coverage
- `apps/backend/tests/test_desk_playbook_detect.py` -- TC-12 short-side degenerate-trigger mirror test
- `apps/backend/tests/test_desk_refresh_chain_guard.py` -- effect/interval/trigger-call census extended for the Backscan section
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` extended for the new served numerics
- `apps/backend/scripts/seed_playbook_iter7_backscan_fixture.py` -- new, extends the iter-6 seed with a fourth member + two new dates
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` -- new, the iter-7 scoped backend entry point (all four playbook env vars)
- `apps/frontend/app/desk/page.tsx` -- the Backscan panel (see frontend handoff)
- `apps/frontend/lib/api.ts` -- five new API client functions for the backscan endpoints
- `apps/frontend/lib/types.ts` -- new `DeskPlaybookBackscan*` types

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest -q`
Result: **2131 passed, 8 skipped, 0 failed** (iter-6 floor was 2105 passed / 8 skipped — no
regressions, net +26 including the new backscan/TC-12 tests).

`Config().config_fingerprint()` still prints `08e471b10130e1e2` (verified directly). `tests/
test_mcp_server.py` still green (18-tool contract unchanged, TC-16).

Additional live verification (never touching `.data/`):
- Ran `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` against a scratch root on
  a throwaway port (8399): `GET .../backscan/plan` returned the expected 3-date, all-missing plan;
  `POST .../backscan/compute` completed to `"done"` with `outcomes.recorded == 3`; `GET .../backscan/
  runs` showed exactly one row with matching outcomes and `config_fingerprint: "08e471b10130e1e2"`.
  Confirmed via `find apps/backend/.data -iname "*backscan*"` (empty) and the pinned `:8301` backend's
  own `GET /research/desk/playbook/backscan/runs` (`{"runs": [], "latest": null}`) that the real
  store was never touched.
- Confirmed TypeScript compiles cleanly: `npx tsc --noEmit -p tsconfig.json` (frontend) — zero
  errors.
- Restarted the pinned `:8301`/`:3301` dev pair (they were down at dispatch despite the environment
  note) via `scripts/start-backend.sh`/`scripts/start-frontend.sh`; both now respond 200, and
  `GET :3301/desk` renders the new "Backscan" section text. Left both running and healthy.

## Known Issues

- **The real full-corpus back-scan was never run** (explicitly out of scope this iteration — "an
  operator-run act… reported run-or-not-run", not a mechanically-gated passing condition). The
  fixture-scoped keyless core plus the one fixture-scoped live scan above is the complete evidence
  for this iteration's passing bar.
- **The plan walks every calendar day in range, not just recorded trading sessions.** This was a
  deliberate design choice forced by TC-9's "zero bar-content reads" contract (`desk_sessions.
  recorded_session_dates` reads `merged_bars`, which would violate it) — see the module docstring.
  For a very wide real-corpus range this means the plan/walk will include weekends/holidays as
  `missing_at_current_signature` entries that the real walk then classifies `refused_non_session`.
  This is honestly disclosed and exercised by TC-8, but is a real efficiency cost for the (out-of-
  scope) full real-corpus back-scan a future iteration might want to address — e.g. by having
  `run_backscan` itself pre-filter via `recorded_session_dates` (which is NOT bound by the plan
  GET's zero-bar-read contract), trading a bounded number of daily-bar reads at compute-trigger time
  for a much shorter real walk. Left unaddressed this iteration to stay inside IN SCOPE.
  Not a raised owner-ruling item — a candidate for a later iteration's own scope, not something to
  action here.
- **No CLI warmer for the back-scan** (unlike `desk_deep_backfill.py`/`desk_playbook_compute.py`,
  which both ship one). The phase spec's own route list (`GET plan`, the compute trio, `GET runs`)
  never mentions a CLI, so none was built — the UI trigger + manager IS the complete operator-facing
  surface this iteration specifies.
- Browser-QA evidence (TC-11, the plan-preview + triggered-scan-completion screenshot; the owed
  Range Trade row re-capture, TC-14) was NOT captured by this dev pass — that is the browser-qa-agent's
  job in the next pipeline step, using `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`
  as the ONLY backend entry point for that work, per this iteration's critical process note.

## Test-first contract coverage (TC-1..TC-17)

- TC-1, TC-2, TC-3, TC-4, TC-5, TC-6, TC-7, TC-8, TC-9, TC-10, TC-11 (browser, deferred to QA),
  TC-13, TC-17 — covered in `test_desk_playbook_backscan.py`.
- TC-12 — covered in `test_desk_playbook_detect.py`.
- TC-14 (evidence make-up, non-blocking) — deferred to browser-qa-agent.
- TC-15 — full suite green at 2131/8 skip, pin `08e471b10130e1e2` confirmed.
- TC-16 — `tests/test_mcp_server.py` green, 18-tool contract unchanged.
