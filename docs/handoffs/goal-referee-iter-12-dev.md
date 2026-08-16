# goal-referee-iter-12 Dev Handoff

**Phase:** goal-referee-iter-12 (Era 6 "The Referee", J-11 — the accrual projection states its
own basis)
**Date:** 2026-08-16
**Agent:** developer
**Status:** complete

## What Was Built

J-11 is a pure read-side, additive field extension to the ALREADY-shipped J-07 shortlist endpoint
(`GET /research/desk/referee/registry/shortlist`, owner `referee_registry.py::shortlist_response()`)
plus its rendering in the already-shipped Referee Registry section on `/desk`. It adds a corpus-wide
`accrual_basis` block and two new per-candidate fields, measured in RECORDED sessions rather than
raw calendar days — so a multi-month zero-session recording gap in the corpus no longer silently
inflates the shipped calendar-day projection the owner reads before taking the one irreversible act
this era gates behind sample size (registration).

- **`app/research/referee_registry.py`**
  - New helper `_longest_zero_session_stretch(newest_by_date)`: walks the same sorted date keys
    `_corpus_session_span_days` already sorts to find the longest gap between two consecutive
    recorded session dates (`(later - earlier).days - 1`), returning `(days, start_date, end_date)`;
    `(0, "", "")` when fewer than two dates are recorded.
  - `shortlist_response()` now also returns a top-level `accrual_basis` dict
    (`corpus_first_session_date`, `corpus_last_session_date`, `corpus_span_days` — reused verbatim
    from the existing `_corpus_session_span_days()` call, never recomputed —
    `recorded_sessions_in_span` == `playbook_occurrence_readiness()`'s own `distinct_sessions`,
    `pooled_sessions_at_current_basis` == that same `distinct_sessions` minus
    `len(stale_basis_dates)`, and the longest-zero-session-stretch triple) and two new fields per
    candidate, beside (never replacing) the shipped `accrual_rate_sessions_per_day`/
    `projected_days_to_target`: `informative_sessions_per_pooled_session` (that candidate's own
    already-computed `n_sessions` over `pooled_sessions_at_current_basis`; `0.0` when the
    denominator is 0) and `projected_pooled_sessions_to_target` (`target_sessions` over that rate;
    `null` when the rate is 0 — the same divide-by-zero discipline the shipped pair already uses).
  - Zero new store scans added: reuses the SAME `newest_by_date` dict and `readiness` object the
    function already built before this iteration (proven by TC-7's counting-wrapper test — total
    `PlaybookStore.list()` calls per `shortlist_response()` invocation stays at its pre-iteration
    baseline of 2). Zero new `Config` fields, zero new `referee_parameters()` entries (pinned by a
    golden content-hash test), zero diff to `desk_playbook*.py`/`desk_forward.py`/`levels.py`/
    `tradability.py`/`pnl_scan.py`.

- **`docs/referee-statistical-spec.md`** — §9 gained item 8, a dated/named addendum
  ("2026-08-16 addendum, goal-referee-iter-12, J-11") stating the accrual projection is a
  read-side planning disclosure no statistical procedure consumes, and that both bases (calendar-
  day and recorded-session) are served side by side, neither ever replacing the other.

- **`apps/frontend/lib/types.ts`** — new `RefereeAccrualBasis` interface; `RefereeShortlistResponse`
  gains `accrual_basis`; `RefereeShortlistCandidate` gains
  `informative_sessions_per_pooled_session`/`projected_pooled_sessions_to_target`.

- **`apps/frontend/app/desk/page.tsx`** (`RefereeRegistrySection`) — one new descriptive basis line
  (`data-testid="referee-accrual-basis-line"`) rendered above the shipped shortlist table, reading
  `shortlist.accrual_basis` verbatim (recorded sessions, pooled sessions, corpus span with
  first→last date, longest zero-session stretch with its bounding dates; an honest
  "No sessions recorded yet." empty state when `corpus_first_session_date === ""`). One new
  right-aligned "Projected sessions" column immediately beside the shipped "Projected days" column,
  rendering `candidate.projected_pooled_sessions_to_target` with the identical `toFixed(0)`/"—"
  convention the shipped column uses, with a new per-row testid
  (`referee-shortlist-projected-pooled-${candidate_id}`). Zero client-side arithmetic anywhere —
  every value is a straight pass-through. `informative_sessions_per_pooled_session` is served on
  the API response and exercised by its own backend test but gets no dedicated table column this
  iteration (per `runs/goal-session-referee/state/assumptions.md`'s iter-12 entry, already recorded
  by the goal-decomposer before this dispatch — goal.md Step 4 names exactly one new column).

- **Guard test extensions**
  - `tests/test_desk_ui_guards.py::_PRICE_ARITHMETIC_FIELDS` widened: the existing `candidate.*`
    group gains `informative_sessions_per_pooled_session`/`projected_pooled_sessions_to_target`; a
    new `accrualBasis.*` group covers the four new numeric fields the basis line renders
    (`corpus_span_days`, `recorded_sessions_in_span`, `pooled_sessions_at_current_basis`,
    `longest_zero_session_stretch_days`). New seeded counter-test
    `test_desk_page_price_arithmetic_guard_catches_accrual_basis_and_pooled_projection_arithmetic`
    proves both extensions actually catch a violation (and that the shipped pass-through idioms
    stay clean).
  - `tests/test_copy_discipline.py` needed no code change — its frontend scan already globs
    `app/**/*.tsx`, so the new basis-line/column copy is automatically covered; ran green against
    the new strings with no lexicon changes needed.
  - `tests/test_referee_registry.py` gained 6 new tests (see Tests Run below).

## Files Changed

- `apps/backend/app/research/referee_registry.py` -- `_longest_zero_session_stretch` helper;
  `shortlist_response()` gains `accrual_basis` + two per-candidate fields.
- `apps/backend/tests/test_referee_registry.py` -- 6 new J-11 tests (TC-1/2/3/4/5/6/7/8/17
  coverage) + a `pathlib`/`referee_parameters_hash` import.
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` widened + 1 new
  counter-test.
- `apps/frontend/lib/types.ts` -- `RefereeAccrualBasis` interface; two response/candidate field
  additions.
- `apps/frontend/app/desk/page.tsx` -- `RefereeRegistrySection`: basis line + "Projected sessions"
  column.
- `docs/referee-statistical-spec.md` -- §9 dated addendum (item 8).
- `runs/goal-referee-iter-12/status.json` -- new, `current_step: dev_complete`.

Not touched (verified byte-identical, see Tests Run): `desk_playbook*.py`, `desk_forward.py`,
`levels.py`, `tradability.py`, `pnl_scan.py`, `app/mcp/__init__.py` (MCP tool count/paths
unchanged — the shortlist subpath is not proxied by any MCP tool and this iteration adds none),
`runs/goal-session-referee/state/blueprint.md` and `state/assumptions.md` (both already carried
the correct iter-12 entries from the goal-decomposer's own iteration authoring, verified accurate
against the implementation and left as-is).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest` (pyproject.toml's own `addopts = "-q"`;
do not pass an extra `-q` or the summary line disappears)

Result, full suite: **2687 passed, 8 skipped** (2695 collected — era-close baseline was 2688
collected / 2680 passed / 8 skipped; this iteration added exactly 7 new tests, 0 regressions, 0
skip-count change). 0 failures.

Targeted verification run alongside the full suite:
- `tests/test_referee_registry.py` (52 → 58 tests, all pass) — includes the 6 new J-11 tests:
  hand-computed `accrual_basis`/per-candidate fixture numbers against a deliberate 65-day
  zero-session gap fixture (2026-02-09 → 2026-04-16, corpus 2026-01-05..2026-06-20); the
  zero-pooled-session-denominator empty-corpus case; two-call determinism; the
  `PlaybookStore.list()` call-count pin (stays at 2, proving no third scan was added) +
  `BandMapResolver(compute=False)` pin; a golden `referee_parameters_hash()` pin
  (`0976d49e3e4583b5`, unchanged); the spec-addendum content check.
- `tests/test_desk_ui_guards.py` (78 tests, all pass, including the new counter-test).
- `tests/test_copy_discipline.py` (all pass, no code change needed).
- `tests/test_referee_adjudicate.py`, `test_referee_evidence.py`, `test_referee_guards.py`,
  `test_referee_null.py`, `test_referee_oracles.py`, `test_referee_stats.py`, `test_mcp_server.py`
  (still exactly 22 tools), `test_pnl_scan.py` — all pass, confirming zero cross-module regression.
- `tests/test_profile_equivalence.py` — 14 pass (`default`-profile engine equivalence green).
- TypeScript: `apps/frontend && node_modules/.bin/tsc --noEmit` — zero errors.

Frozen-foundation checks (before/after, all confirmed unchanged):
- `Config().config_fingerprint()` == `08e471b10130e1e2` (both before and after).
- `referee_parameters()`'s content hash == `0976d49e3e4583b5` (pinned by test, unchanged).
- `journal.db`/`tapeology_journal.db` (PnL ledger + champion pointer) SHA-256 unchanged
  (`352a9bb2...`/`3db3ee7e...` before and after — no write of any kind occurred).
- Every file under `apps/backend/.data/` (11,307 files) SHA-256-identical before/after (`diff -q`
  clean) — no store write occurred anywhere during dev/test.
- `git diff` scoped to `desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`,
  `pnl_scan.py` is empty.

Live real-corpus sanity check (read-only GET against the operator's actual store, via
`scripts/start-backend.sh` on the deterministic port :8301 — see Pre-handoff verification below;
no write occurred): the real corpus (156 recorded sessions, 2025-06-03 → 2026-08-13, 437 calendar
days) carries a genuine 212-day zero-session stretch (2025-06-03 → 2026-01-02). For every one of
the six shortlist candidates the new recorded-session projection reads meaningfully SHORTER than
the shipped calendar-day one (e.g. S-1 capitulation:long: 26.4 recorded-session-basis sessions vs.
73.9 calendar-day-basis days) — the intended effect, confirmed against real magnitudes per this
session's iter-8 lesson ("hand-check any served number whose formula has a subtraction, a floor,
or a saturation point against REAL-corpus magnitudes").

## Pre-handoff verification

- **Service startup**: `scripts/start-backend.sh` and `scripts/start-frontend.sh` (T-9: `rm -rf
  apps/frontend/.next` first) both started cleanly on the deterministic per-project ports
  (:8301/:3301 — this project's own hash-derived offset, which happens to coincide with the
  documented browser-QA rig ports), served `GET /research/desk/referee/registry/shortlist` (200,
  new fields present) and `GET /desk` (200, clean Next.js compile, no console errors). Stopped
  (exact-PID process-tree kill, never pattern-based `pkill`), ports confirmed free, started again
  cleanly with no port conflicts, stopped again. No server processes left running.
- **External integrations**: N/A — this iteration adds no adapter, scraper, or external API call
  (pure read-side arithmetic over an already-recorded corpus).
- **Native dependency binaries**: N/A — no new dependency of any kind (stdlib `date` arithmetic
  only; the IN SCOPE bullet's own "zero new runtime dependency" constraint).

## Known Issues

None found in this iteration's own scope. Two things worth flagging for whoever reviews or QAs
this:

1. The real corpus's `accrual_basis.longest_zero_session_stretch_days` is 212 days
   (2025-06-03 → 2026-01-02) — a genuine, large historical gap before active desk recording
   began. This is the honest disclosure the journey exists to surface, not a bug; flagging it here
   only so a reviewer doesn't mistake the real-corpus number for a fixture artifact when
   sanity-checking against live data.
2. Per this session's own carried-forward "Do not redo" list (`iteration-state.md`), four
   pre-existing, out-of-scope hardening items were deliberately left untouched because none lives
   inside `referee_registry.py` or the Referee Registry section: the store-scope guard script's
   4-Referee-dirs gap, `referee_adjudicate.py:550`'s both-names-unknown certificate matching, a
   dash-vs-unknown rendering on a failed second fetch, and a stale `19/7/1` comment. Not touched,
   not regressed.

Browser QA (screenshots of the new basis line + column, and every other shipped `/desk` section in
the same pass per TC-12/13/14) was NOT run by this agent — that is the browser-qa-agent's job
downstream. The `[NEW]`-flagged demo-narrator walkthrough was likewise not authored by this agent
(a separate pipeline stage); the new surface carries stable, distinct `data-testid`s
(`referee-accrual-basis-line`, `referee-shortlist-projected-pooled-${candidate_id}`) and a new,
non-colliding column heading ("Projected sessions") ready for that stage to target. Manually
verified against the three existing golden replay scripts in
`runs/goal-session-referee/journey-scripts/` (J-07, J-09, J-10) that none of their `testid`/`text`
expectations collide with or were altered by this iteration's additions.
