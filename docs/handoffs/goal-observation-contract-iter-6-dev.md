# goal-observation-contract-iter-6 Dev Handoff

**Phase:** goal-observation-contract-iter-6
**Date:** 2026-09-05
**Agent:** developer
**Status:** complete

## What Was Built

This iteration is **test-only** (Binding Execution Order step 6, J-06) -- zero production files
under `apps/backend/app/` or `apps/frontend/` changed, confirmed by `git status --porcelain`
returning empty for both trees.

- New test module `apps/backend/tests/test_tape_observation_guards.py` (21 tests, 0 failed) --
  the guard suite (Key Capability 8; Required Trap Coverage items 40-45). Five structural
  mechanisms, each with its own `test_counterexample_*` that perturbs a REAL scanned
  constant/module/artifact (never a second hand-written literal, per the iter-3/iter-4 lessons
  this exact file is named against):
  1. **Copy-discipline lint + compound-identifier ban** -- reuses `find_violations` verbatim
     (imported from `test_copy_discipline.py`, never reimplemented) plus a new fixed 11-token
     compound-identifier ban (`should_trade`, `trade_signal`, `entry_price`, `stop_loss`,
     `position_size`, `trade_allowed`, `READY`, `NO_TRADE`, `NO_VERDICT`, `PENDING_CONDITION`,
     `composite_policy`), scanned over (a) `observation_contract.py`'s source, (b) the five
     existing `test_tape_observation_*.py` modules' source, and (c) one live-served
     `/tape/SIM-BIDABS/observation` artifact fetched over HTTP from a REAL uvicorn subprocess
     (never `TestClient`-only, per the plan). `#` comments, every docstring, and every
     `test_counterexample_*` function body are stripped from source texts before scanning (via
     `ast` + `tokenize`) -- this resolves two concrete false positives found empirically, without
     touching either frozen file: `test_tape_observation_route.py:174`'s comment ("...guaranteed
     to observe...") trips `find_violations`' certainty-claim pattern, and
     `test_tape_observation_lifecycle_feed.py`'s own
     `test_counterexample_actionability_scan_catches_an_injected_token` legitimately embeds
     `trade_allowed` as seeded fixture data proving an earlier (iteration-3) guard's scanner can
     fail. One additional narrow, documented exception (`_KNOWN_PATTERN_LIST_EXCEPTIONS`) covers
     `test_tape_observation_lifecycle_feed.py`'s own pre-existing `ACTIONABILITY_TOKENS` module
     constant (5 of the 11 banned tokens, defined at module scope, not inside a
     `test_counterexample_*` function) -- the same `test_no_execution_path.py` SELF-exemption
     precedent ("this gate itself names every pattern as data"), scoped per-file and per-token so
     any other token, or these same tokens in any other file, still trips the ban.
  2. **External-system reference guard** -- `workstation`/`trendora`/`tensteps` absent,
     case-insensitively, under `apps/` (all `.py`/`.ts`/`.tsx`/`.js` files, standard skip-dirs)
     and in `docs/observation-contract-spec.md`. `project-extensions/host-guard/host-guard.env`
     was confirmed (by direct inspection) to legitimately name sibling host projects ("trendora",
     "tensteps") for shared CPU/RAM budgeting -- exactly why goal.md excludes that path, though
     the two scan roots used here never reach it in the first place.
  3. **English-only guard** -- scoped exactly to schema keys (from
     `observation_contract.field_partition_map()`), the closed enum vocabularies (tape-state,
     source_mode, availability_basis, data_feed -- read from `CONFIG`/`data_feed_for_scenario`
     rather than hardcoded literals -- and the Constitution §4 seven-status lifecycle set), and
     `observation_contract.py`'s module identifiers. Deliberately does NOT scan `source.scenario`
     or `observations[]` (free-text labels) -- `app/main.py`'s historical scenario string
     (`f"historical {ticker} {body.start}-{body.end}"`) legitimately carries an en dash, and
     goal.md Constitution §8 explicitly exempts exactly this.
  4. **Real-provider isolation guard** -- an AST-precise scan (real `Name`/`Attribute`/import
     nodes, never a text substring) confirms no `test_tape_observation_*` module -- all SIX,
     including this new one -- reaches `AlpacaAdapter` outside a `TAPEOLOGY_REAL_PROVIDER_SMOKE`-
     gated smoke test (none exists yet this era, confirmed by inspection; the carve-out is proven
     real via a synthetic gated-pattern fixture). Because the scan is AST-identifier-precise, this
     module's own prose discussing "AlpacaAdapter" as a quoted string never self-triggers -- no
     textual SELF-exclusion needed for this mechanism.
  5. **Mutator-call-site guard** -- an AST visitor finds every call site under `app/` where the
     receiver is a bare `Name(id="engine")` and the method is one of `TapeEngine`'s six mutators
     (`process_event`, `set_stream_status`, `set_delivery_lag`, `set_epoch_anchor`, `pause`,
     `resume`), and confirms each lives inside a `WatchManager` method (`watch_manager.py`) or
     `DatasetStore.replay` (`research/datasets.py`). 29 real call sites found, 0 violations. The
     bare-`Name("engine")` receiver restriction was verified (by direct inspection of every
     `TapeEngine(...)` construction and every mutator call under `app/`) to correctly separate
     real `TapeEngine` mutator calls from two same-method-name-but-different-class collisions:
     `WatchManager.pause`/`resume` (called as `manager.pause(ticker)` in `app/main.py`) and
     `HistoryBuffer.set_epoch_anchor` (called as `self._history.set_epoch_anchor(...)` inside
     `TapeEngine` itself).
- A shared helper (`_existing_observation_test_modules`) globs `test_tape_observation_*.py` and
  explicitly excludes this new file (SELF) -- proven non-vacuous and correct by
  `test_existing_observation_test_modules_glob_is_not_vacuous_and_excludes_self`, which asserts
  the resulting set is exactly the five pre-existing filenames.

> **Auditor amendment (2026-09-05, `docs/handoffs/goal-observation-contract-iter-6-audit.md` fix #1):**
> mechanism 5 shipped as a call-site LOCATION check (any `WatchManager` method) rather than the
> re-settling predicate `docs/goal.md` J-06 step 3 / Required Trap Coverage item 44, the phase spec
> and `runs/goal-observation-contract-iter-6/plan.md` all specify. The auditor tightened it in this
> same module (settling methods derived from `self._settle(...)` call sites via AST, plus one
> documented carve-out for `WatchManager.stop`, which deletes the engine in the same method) and
> added two tests. The counts below are therefore superseded: the module is now **750 lines,
> 23 tests, 0 failed**, and the full suite is **4067 passed / 8 skipped / 0 failed** (iter-5
> baseline 4044 + 23). Every other claim in this handoff was re-verified and stands.

## Files Changed

- `apps/backend/tests/test_tape_observation_guards.py` -- new, 649 lines, 21 tests, 0 failed
  (superseded by the auditor amendment above: 750 lines, 23 tests).
- `docs/handoffs/goal-observation-contract-iter-6-dev.md` -- new (this file).
- `reports/phase-goal-observation-contract-iter-6-implementation-summary.md` -- new.
- No file under `apps/backend/app/`, `apps/frontend/`, or any of the nine protected guard test
  files changed -- confirmed via `git status --porcelain` (empty for all three checks) both
  before writing the handoff and as a final check.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_guards.py -q`
Result: **21 passed, 0 failed** (confirmed both via `-q` progress-character tally and an
independent `--collect-only -q` count, which agree exactly -- this venv's pytest 9.1.1 prints no
final summary line, per the iter-0 lesson).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (full suite)
Result: **4065 passed, 8 skipped, 0 failed** (4073 collected, exit code 0) -- exactly the iter-5
baseline (4044 passed, 8 skipped, 4052 collected) plus this iteration's 21 net-new tests, 8
skipped unchanged, 0 regressions. Tallied by counting `-q` progress characters directly from the
captured output (`.`=4065, `s`=8, `F`=0, `E`=0) and cross-checked against an independent
`--collect-only -q` per-file-count sum (4073) -- the two tallies agree exactly. The historically
flaky `test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates` (iter-2 lesson)
did not fail this run.

Also run individually:
- The focused observation-contract + MCP + guard regression set together
  (`test_tape_observation_guards.py test_tape_observation_route.py
  test_tape_observation_path_equivalence.py test_tape_observation_projection.py
  test_tape_observation_time.py test_tape_observation_lifecycle_feed.py test_mcp_server.py
  test_no_execution_path.py test_copy_discipline.py`) -- **236 passed, 0 failed**.
- `Config.config_fingerprint()` -- confirmed `08e471b10130e1e2` (unchanged, per the pinned value).
- `len(app.mcp.TOOL_NAMES)` -- confirmed `28` (unchanged; MCP contract stays v8 / 28 tools).
- `cd apps/frontend && npx tsc --noEmit` -- **0 errors** (exit code 0; no frontend file touched).

## Pre-handoff verification (service startup)

This iteration touches zero application/frontend runtime files, so the primary evidence that the
backend serves correctly is the new guard module's own `live_served_observation` fixture, which
starts a REAL `uvicorn app.main:app` subprocess, waits for `/health`, watches `SIM-BIDABS`, waits
for it to settle, pauses it, and fetches `/tape/SIM-BIDABS/observation` over real HTTP -- this
passed as part of the 21/21 module run above.

In addition, ran the repo's actual dev workflow directly (`scripts/dev.sh`, this repo's
deterministic port pair :8301 backend / :3301 frontend):
- Cold start: both services came up cleanly (`Uvicorn running on http://0.0.0.0:8301`, Next.js
  `Ready in 1401ms`). `GET :8301/health` -> 200, `GET :3301/` -> 200, `GET :3301/structure` -> 200,
  `GET :3301/desk` -> 200.
- Stopped both (killed the bound ports), confirmed both ports fully released, then started
  `scripts/dev.sh` again -- a clean restart with no port-conflict errors (`dev.sh`'s own
  port-clearing logic ran once against a leftover PID and succeeded); `GET :8301/health` -> 200
  and `GET :3301/` -> 200 again on the second run. Both services stopped and ports confirmed clear
  at the end.

No adapter/scraper/external-API code was added this iteration (test-only), so the "external
integrations work live" and "native dependency binaries" pre-handoff checklist items do not
apply.

## Known Issues

- None. All five guard mechanisms pass with non-vacuous counter-tests; the full suite is green
  with the expected pass-count delta; `tsc`, the config fingerprint, and the MCP tool count are
  all unchanged; zero files outside the one new test module were touched.
- The real-provider-isolation guard's gated-smoke-test carve-out (`_is_gated_smoke_module`) is
  currently exercised only by a synthetic fixture in
  `test_gated_smoke_module_pattern_is_recognized_as_exempt`, since no
  `TAPEOLOGY_REAL_PROVIDER_SMOKE`-gated module exists in this repository yet (confirmed by
  inspection; building one is explicitly out of scope for this era per goal.md Constraints). This
  is expected, not a gap: the carve-out exists so a future smoke test would be correctly exempted,
  not because one is missing today.
- This iteration was test-only by design (Binding Execution Order step 6); the two browser-
  evidence gaps the plan also names (J-04's paused-reload identity check, J-02's own numbered
  steps) are LLM browser-qa-lane work against the backend origin, not developer/code work, and
  are not part of this handoff.
