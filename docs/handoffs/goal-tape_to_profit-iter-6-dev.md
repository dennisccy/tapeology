# goal-tape_to_profit-iter-6 Dev Handoff

**Phase:** goal-tape_to_profit-iter-6
**Date:** 2026-07-03
**Agent:** developer
**Status:** complete

## Resume posture — verify-and-complete (this session)

Per the iter spec's explicit resume posture, HEAD was already at the iter-5 commit with a
**complete, uncommitted J-06 implementation** in the working tree plus this exact handoff file
already written (an earlier developer-agent invocation). This session made **zero code changes**
— it independently re-verified every DoD item from scratch (fresh test run, fresh live server,
fresh curl/API checks) rather than trusting the prior session's claims on inspection alone. Every
check below was re-run independently in this session; none required a fix:

- Read the full diff of all 6 changed files (`config.py`, `backtests.py`, `profiles.py`,
  `routes.py`, `test_profiles_api.py`, `test_backtests_api.py`) plus the new
  `test_profile_equivalence.py` (327 lines / 15 tests) end-to-end against the iter spec's IN
  SCOPE bullets — confirmed line-by-line, not just the handoff's prose summary.
- Ran the **full backend suite** fresh: **1004 passed, 1 skipped, 0 failed** (0 FAILED/ERROR via
  `grep`), matching the claimed 988-baseline + 16 net-new. Confirmed via `-v` output that
  `test_profile_equivalence.py` (15/15), the profile-related tests in `test_backtests_api.py` and
  `test_profiles_api.py`, `test_no_execution_path.py` (4/4), and `test_observer_equivalence.py`
  (7/7) all show clean dot-runs with no `F`.
- Confirmed OUT-OF-SCOPE files are untouched: `git diff --stat` on `pnl_ledger.py`,
  `pnl_baseline.py`, `pnl_history.py`, `reports/pnl/pnl-history.md`, `app/mcp/`, and
  `apps/frontend/` all show **zero diff**; `pnl_min_sample_size` does not appear anywhere in the
  `config.py` diff.
- Read `apps/frontend/app/performance/page.tsx` directly (not just the source-scan test) and
  confirmed it maps `profiles.profiles` generically with no hardcoded candidate id and no
  `<select>` — the "zero frontend changes needed" claim holds structurally.
- Confirmed the MCP↔REST byte-identical requirement for `/research/profiles` is already covered
  by the pre-existing `test_get_endpoint_profiles_byte_identical_on_the_live_200` in
  `test_mcp_server.py` (part of the green full-suite run); `app/mcp/` has zero diff so this
  continues to hold.
- **Live end-to-end verification against a freshly started server** (not just re-running pytest):
  `GET /research/profiles` → both profiles, exact registry shape; re-registering the founding
  TRAIN window correctly `409`s (already registered, immutable); `POST /research/backtests` under
  `default` → queued+done with `config_fingerprint` `4d665603569b9dbf` at both the queued and
  terminal stamp; under `candidate-faster-warmup` → queued+done with `8c2c0fbf978228e3` at both
  stamps; under `nonexistent-profile` → `422` listing `['default', 'candidate-faster-warmup']`;
  the TRAIN backtest's aggregates were byte-identical between profiles live (matches the pinned
  "train trade doesn't move" claim); J-08 sentinel — `SIM-BUYER` → `buyer_control` @ 0.86 —
  and `/`, `/journal`, `/studies`, `/performance` all `200` live.
- **Restart test**: stopped all servers, restarted `scripts/dev.sh` a second time, confirmed no
  port conflicts on `:8301`/`:3301`, and re-confirmed `GET /research/profiles` still served
  correctly post-restart.
- **Environment note (not a defect, worth recording for the next session):** `pyproject.toml`
  sets `addopts = "-q"`; passing an additional `-q` on the command line compounds to `-qq`, which
  in pytest 9.1.1 suppresses the final `N passed` summary line entirely (dots only, no count) even
  though the run completes normally with exit code 0. The project's documented command
  (`pytest tests/ -v`) does not hit this — `-v` cancels the config's `-q` back to normal verbosity
  and the summary line prints correctly. Confirmed by direct byte inspection (`xxd`) of a `-qq`
  run's output — the summary line is genuinely never written, not a display/capture truncation.
- **Process-cleanup finding reproduced twice** (matches the prior session's note, so this is a
  stable characteristic of `scripts/dev.sh`'s process tree, not a one-off): after
  `pkill -f "next dev"` / `pkill -f "next-server"`, the `npm exec next dev` → `sh -c` → `node
  next dev` → `next-server` chain (plus, after killing an active `uvicorn --reload`, its orphaned
  `multiprocessing.resource_tracker`/`spawn_main` helpers reparented to `systemd --user`) survived
  the pattern-based `pkill` both times and needed an explicit `kill -9 <pid>` by PID. `fuser -k -9
  $PORT/tcp` (what `scripts/dev.sh` itself uses internally) reliably frees the **port** each time
  — confirmed by the clean second `dev.sh` startup with no conflicts — so the automation pipeline
  is unaffected; this only matters for an interactive agent's own manual `pkill`-by-name cleanup.
  All processes this session started are confirmed stopped (`lsof -ti :8301 :3301` empty, full
  `ps aux` sweep clean except one pre-existing, not-mine `python -m app.mcp` stdio process on
  `pts/2` that predates this session and was never touched).

No further action was needed — every DoD checklist item held on independent re-verification. The
rest of this handoff (below) is the original implementation narrative, confirmed accurate.

## What Was Built

J-06 (versioned indicator profiles): a config-owned profile registry with the frozen `default`
plus the era's first additive candidate, selectable only by an explicit backtest run.

- **`Config.profile_definition(profile_id)`** (`app/config.py`) — the ONE registry lookup,
  mirroring the existing `strategy_definition` pattern. `default` → `{id, frozen: True,
  is_default: True}`. The registered candidate `candidate-faster-warmup` → `{id, frozen: False,
  is_default: False, based_on: "default", overrides: {"warmup_min_events": 30}}` (self-documenting:
  id, base, and the exact declared override — all read from config, no magic numbers). Unregistered
  ids return `None`.
- **`Config.profile_registry()`** — the full ordered list (`default` then the candidate); the
  single source `GET /research/profiles` and the backtest route's validation both consult.
- **`Config.resolved_for_profile(profile_id)`** — the per-run `Config` for a profile: `default`
  returns the identical `CONFIG` object (not a copy — the strongest byte-identical guarantee);
  the candidate returns a fresh `dataclasses.replace(self, warmup_min_events=30)` overlay, never
  mutating the shared singleton. Unregistered → `None`.
- **New `Config` field `profile_candidate_warmup_min_events: int = 30`** — the candidate's one
  additive alternate-threshold value (lowers the classifier's cold-start floor from the default
  40). Excluded from `config_fingerprint()` (it's registry metadata only, never itself read by
  engine code — the OVERLAID `warmup_min_events` field, never excluded, is what actually moves the
  fingerprint for a candidate-resolved config).
- **`app/research/routes.py`** — retired the hardcoded `if body.profile != PROFILE_DEFAULT: 422`
  in `create_backtest`; replaced with `registry.config.profile_definition(body.profile) is None`.
  A registered candidate is now accepted (previously always 422); an unregistered profile still
  422s, listing the known ids.
- **`app/research/backtests.py`** — `BacktestRunner.run()` resolves `run_config =
  self._config.resolved_for_profile(params["profile"])` and passes it ONLY into `_replay()` (the
  fresh engine construction for that one run) and the persisted `result["config_fingerprint"]`.
  Every OTHER computation in the module (fees, slippage, the strategy grammar, the null baseline)
  still reads the manager's base `self._config` unconditionally — a profile is an
  engine/classifier concern (Data Contract row 33), never a strategy-grammar one (row 34).
  `BacktestJobManager.create()`'s queued-time stamp now resolves the same way, so the queued
  payload's `config_fingerprint` already matches what the terminal report will carry.
- **`app/research/profiles.py`** — rewritten to project `Config.profile_registry()` instead of a
  hardcoded single-entry list; no longer imports from `.backtests` (both modules now depend only
  on `config.py`, an even cleaner dependency graph than before).
- **`PROFILE_DEFAULT`** moved from `app/research/backtests.py` to `app/config.py` (beside
  `STRATEGY_V1_ID` — the same "id constant + Config-owned definition method" pattern for both).
  `backtests.py` still re-exports it via `__all__`, so all 7 pre-existing importers
  (`routes.py`, `pnl_baseline.py`, 4 test files) needed zero changes.

### The candidate is empirically proven to fire (not a no-op)

Per iter-5's lesson, I replayed the committed PG SIP reference fixture under both profiles before
writing any pinned test values. Lowering `warmup_min_events` from 40 to 30 genuinely moves the
first directional `tape_state` call earlier on **both** founding windows:

- TRAIN (17:00:00–17:01:00Z): 13 snapshots flip state (first at index 129 vs default's 248) —
  but the strategy's *sustained*-arm instant happens not to move, so the TRAIN backtest report is
  byte-identical between profiles (proving the candidate changes nothing it doesn't legitimately
  touch).
- HOLDOUT (17:05:00–17:05:45Z): 24 snapshots flip state (first at index 136 vs default's 160) —
  and this **does** move the sustained-arm instant: the candidate's holdout trade enters at
  ts=6.278 vs default's ts=6.550, a different price, and flips net R from +0.333 to −0.173. A
  real, materially different, deterministic outcome — not a metadata relabel.

## Files Changed

- `apps/backend/app/config.py` — `PROFILE_DEFAULT`/`PROFILE_CANDIDATE_FASTER_WARMUP` constants,
  `profile_candidate_warmup_min_events` field (fingerprint-excluded), `profile_definition` /
  `profile_registry` / `resolved_for_profile` methods.
- `apps/backend/app/research/backtests.py` -- resolves the per-run profile config in `run()` and
  `create()`; `_replay()` takes an explicit `config` param instead of reading `self._config`.
- `apps/backend/app/research/profiles.py` -- projects `Config.profile_registry()` instead of a
  hardcoded single entry.
- `apps/backend/app/research/routes.py` -- registry-backed profile validation (was hardcoded);
  updated docstrings/comments that described the pre-J-06 state.
- `apps/backend/tests/test_profile_equivalence.py` (new) -- 15 tests: registry/resolution unit
  tests, fingerprint pin + exclusion + counter-tests, the pinned default-equivalence test (byte-
  identical vs pre-J-06 literal values on the committed fixture), the candidate-difference test
  (engine-level state diffs + backtest-report-level trade diffs, both individually deterministic),
  and the "no engine path outside the backtest runner resolves a profile" + "no frontend selection
  control" source-scan guards.
- `apps/backend/tests/test_profiles_api.py` -- updated the 2 tests whose names/docstrings
  explicitly said "before J-06" to assert the new 2-profile registry shape; extended the
  no-duplicate-literal source scan to cover the new candidate id.
- `apps/backend/tests/test_backtests_api.py` -- renamed `..._until_the_profile_registry_ships` to
  `test_unregistered_profile_is_422`; added `test_registered_candidate_profile_is_accepted_and_runs_to_done`.

No frontend files changed — see "Frontend" below.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` (per `.claude/project-template.md`)

Result: **1004 passed, 1 skipped** (0 failed). Baseline at iter-5 was 988 passed / 1 skipped; this
iteration added 16 net new tests (15 in the new file + 1 net in `test_backtests_api.py`; the 2
renamed tests in `test_profiles_api.py` are a 1:1 swap) and deleted none.

Targeted re-run of the 3 changed/new files alone: 32/32 passed.

Frontend: `cd apps/frontend && npm run build` — compiled clean, 7/7 static pages, `/performance`
unchanged at 2.52 kB.

## Frontend

No frontend code was changed. The existing `/performance` registry panel (`app/performance/page.tsx`,
shipped at J-05) already renders `profiles.profiles.map(...)` generically — `key={profile.id}`,
reading only `id`/`frozen`/`is_default` — with no hardcoded assumption of exactly one row and no
selection control. A registered candidate therefore appears automatically as a second `<li>`; this
is exactly the "display consequence of row 33 gaining a candidate" the iter spec anticipated, not
a new frontend feature. Verified live:

- `npm run build` compiles clean (unchanged route sizes).
- Started the dev backend + frontend via `scripts/dev.sh`; `curl :8301/research/profiles` returns
  both profiles with the exact registry shape; `curl -o /dev/null -w '%{http_code}' :3301/performance`
  → 200.
- Confirmed via `tests/test_profile_equivalence.py::test_performance_page_offers_no_profile_selection_control`
  (a source-scan: no `<select` element, no hardcoded reference to the candidate id in the page
  source) that the "no selection affordance" constraint holds structurally, not just by inspection.

No `docs/handoffs/goal-tape_to_profit-iter-6-frontend.md` was written since there is no frontend
diff to hand off.

## Pre-handoff Verification

- **Service startup**: `bash scripts/dev.sh` — backend (`:8301`) and frontend (`:3301`) both came
  up clean. Stopped (port-killed) and restarted via the same script a second time — no port
  conflicts, both came back up on the identical ports, `/research/profiles` still served both
  profiles correctly post-restart.
- **Live end-to-end checks** (real running server, not mocked):
  - `GET /research/profiles` → `default` + `candidate-faster-warmup`, exact shape matched the
    pinned unit tests.
  - `POST /research/backtests` with `profile: "nonexistent-profile"` → 422, listing the two known
    ids.
  - `POST /research/backtests` with `profile: "candidate-faster-warmup"` on the real founding
    TRAIN dataset → ran to `done`; both the queued-time and terminal `config_fingerprint` read
    `8c2c0fbf978228e3` (matching the pinned test value, and matching each other — no divergence
    between the two stamps).
  - The identical dataset under `profile: "default"` → `done`, `config_fingerprint`
    `4d665603569b9dbf` on both stamps — byte-identical to the value pinned before this iteration
    (verified against the committed `reports/pnl/pnl-history.md` founding row, untouched).
  - `POST /watch/SIM-BUYER?mode=sim` → warms to `buyer_control` at confidence ~0.93 (J-08
    sentinel, live-checked, not just via the suite).
- **External integrations**: none added this iteration (no new adapters/scrapers/vendor calls —
  the candidate reuses the existing committed reference-fixture path).
- **Native dependency binaries**: none added.
- **Process cleanup note** (not a defect, just a verification finding worth recording): after my
  manual `pkill -f "next dev"` cleanup, a `next-server` grandchild process remained running,
  invisible to a pattern that only matches "next dev" — I had to also `pkill -f "next-server"`.
  `scripts/dev.sh` itself is unaffected: its own kill logic is port-based (`lsof -ti :$PORT` /
  `fuser -k -9 $PORT/tcp`), which I proved correctly reclaims the port on a second invocation
  (the restart test above came up clean). All server processes are stopped as of this handoff
  (verified via `lsof -ti :8301 :3301` and a full `ps aux` scan, both empty).

## Known Issues

None. Every IN SCOPE item and DEFINITION OF DONE bullet in the iter spec is implemented and
tested; OUT OF SCOPE items (the sweep harness, any ledger append, moving the champion pointer, any
new MCP tool, `pnl_min_sample_size`/fixture changes, registering more than the one candidate) were
left untouched — confirmed via `git diff --stat` showing zero diff on `pnl_ledger.py`,
`pnl_baseline.py`, `pnl_history.py`, `reports/pnl/pnl-history.md`, and the `app/mcp/` package.

One scope judgment call worth flagging for the reviewer: `BacktestJobManager.create()`'s
queued-time `config_fingerprint` stamp was not explicitly called out in the iter spec's IN SCOPE
list (only the terminal report's fingerprint was), but I updated it too so the two stamps in a
persisted backtest record never diverge for a candidate run (see "What Was Built" above). This
touches only `backtests.py`, which is already an IN SCOPE file for this iteration.
