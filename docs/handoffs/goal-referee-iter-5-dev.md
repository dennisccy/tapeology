# goal-referee-iter-5 Dev Handoff

**Phase:** goal-referee-iter-5
**Date:** 2026-08-15
**Agent:** developer
**Status:** complete

## What Was Built

**J-04 — matched nulls (both variants), fully spec-implemented (`docs/referee-statistical-spec.md` Sec4):**

- New `apps/backend/app/research/referee_null.py` (the era's fourth `referee_*.py` module):
  - `referee-null-tod-v1`: for each eligible J-02 observation (a signal + one of the rail's 15
    `measure_key`s — "eligible" holds by construction, since `playbook_observations()` never emits
    an observation for an excluded/truncated leaf), draws `K = REFEREE_NULL_ANCHORS_PER_OCCURRENCE`
    (4) seeded anchor bars — same symbol, same measurement series (reconstructed by locating the
    RTH session bar carrying the signal's own recorded `forward["at_utc"]` epoch exactly, finest
    series (1m) first then 5m — never a re-derivation of `desk_playbook._measurement_anchor`'s
    detection-adjacent logic), same ToD bucket, remaining-time-matched for fixed horizons
    (literal wall-clock distance to the session's own 16:00 ET close — TC-4 hand-verified: 60 min
    remain at 15:00 ET, 55 min at 15:05 ET), ToD-bucket-only for `to_close`-family measures,
    excluding the occurrence's own trigger/anchor bar, without replacement via the **imported**
    `desk_forward._draw_anchor_indices`. Measures every anchor through the **imported**
    `desk_forward._measure_from` at `entry_kind="close"` with the occurrence's own side sign (via
    `desk_playbook_features.side_sign`, NOT `desk_forward._side_sign` — that helper's
    `"resistance"`-vocabulary check silently mis-signs every `"short"` playbook occurrence, a real
    bug caught and avoided during implementation, documented in the module docstring).
  - `referee-null-context-v1`: as above, plus every candidate anchor's own close must satisfy a
    named backing-bucket predicate (default `at_wall`) evaluated through the **imported**
    `desk_playbook_context.BandMapResolver`/`band_context_block` over the recorded band map —
    never re-derived locally. A cell whose map is not yet computed excludes the WHOLE occurrence
    (never falls back to the unfiltered ToD population); `room_r` at each anchor borrows the paired
    occurrence's own risk distance (`risk_source="paired_signal"`).
  - The three named, signature-bearing spec ids (`referee-null-tod-v1`, `referee-null-context-v1`,
    `referee-test-perm-v1`), each hashing its own full parameter blob, read at call time.
  - The append-only `RefereeNullStore` (keyed `(observation_id, null_spec_signature)`; duplicate
    key raises `NullAlreadyRecorded`; no update/delete method exists anywhere — structural,
    source-scan guard-tested), the durable `RefereeNullRunStore` (terminal-state-only writes;
    `state` includes a real `"cancelled"` outcome, unlike `desk_playbook_log.py`'s exclude-cancel
    convention, matching this ledger's own Data-Contract-pinned enum), `RefereeNullComputeManager`
    (single-flight **per null-spec**, not process-global — a `referee-null-tod-v1` build and a
    `referee-null-context-v1` build may run concurrently, but two requests for the SAME spec never
    do), `run_null_build_and_record` (resumable/idempotent: an already-recorded
    `(observation_id, null_spec_signature)` is skipped, never rewritten), and a CLI warmer
    (`python -m app.research.referee_null --null-spec-id <id>`).
  - Non-finite anchor measurements are excluded and counted (`non_finite_excluded_count`), never
    propagate an exception and never exclude the whole occurrence (T-5) — deliberately different
    from `referee_stats.py`'s new fail-loud door guard (see NOTES below).
- Extended `apps/backend/app/research/referee_routes.py`: `GET /research/desk/referee/nulls`
  (optional `?id=`), `POST /research/desk/referee/nulls/compute`, `GET
  /research/desk/referee/nulls/compute?null_spec_id=`, `POST
  /research/desk/referee/nulls/compute/cancel`, `GET /research/desk/referee/nulls/runs` — matching
  the route shape already registered in `runs/goal-session-referee/state/blueprint.md`. GETs never
  compute (T-8, verified: the compute manager's snapshot stays `idle` after a GET); an
  unknown/malformed `null_spec_id` is refused 422 at every entry point (route body validation,
  `build_null_record`, `RefereeNullComputeManager.trigger`).

**The three riders (`referee_stats.py`):**

- `min_attainable_p` fix: `2.0 / (draws_used + 1)` in exact-enumeration mode (was the unreachable
  `1.0 / (draws_used + 1)`), unchanged at `1.0 / (draws_used + 1)` in the seeded branch. Proven by
  a fresh >=1,000-case tail-regime sweep asserting the served FIELD (not just `p`) equals the true
  floor, with >=100 cases landing exactly on it (the can-fail guard). One EXISTING iter-3 test
  (`test_permutation_test_enumeration_matches_a_hand_computed_p_value`) asserted the OLD wrong
  value (`0.25`) on its own hand fixture — updated to the corrected value (`0.5`, which this
  fixture's own math makes IDENTICAL to `p`, since the observed grouping is this fixture's unique
  extreme) with an explanatory comment; this is the one place this iteration touches a pre-existing
  test assertion, and it is a direct, spec-mandated consequence of the fix this iteration ships,
  not a scope drift. Touches none of `_ATTESTATION_EXPECTED`'s four pinned fields — no
  `STATS_CORE_VERSION` bump, no re-pin.
- Non-finite (NaN/inf) fail-loud guard: `_t_statistic` (covering `permutation_test`,
  `sign_flip_result`, `equal_weight_t`, which all call it first) and `bootstrap_ci_occurrence`/
  `bootstrap_ci_cluster` (checked explicitly, even though `bootstrap_ci_cluster` also calls
  `_t_statistic` internally — checked BEFORE the `min_clusters` floor short-circuit so an
  `insufficient_sample` return can never mask a bad input) now raise `ValueError` immediately on
  any non-finite value. One shared `_require_finite_values`/`_require_finite_session_groups` pair,
  checked once at each entry point (no per-draw re-validation — sums/differences/quotients of
  already-finite numbers stay finite by construction).
- TC-8 tightened from 6.0 to 3.5 standard errors (empirically verified during development: the
  module's own fast path measured ~0.30 SE and the independent general-algorithm reference ~0.17 SE
  off ground truth on the pinned seed — 3.5 stays comfortably non-flaky). A companion mutation
  counter-test (`test_iter5_tc15_...`) reintroduces the realistic "dropped `total -` complement"
  bug in the `n2 == 1` fast path (entirely inside the test file, never touching the real module) and
  proves its `p` deviates ~0.12 from ground truth — vastly outside the tightened band, proving the
  tightened band actually discriminates a real regression.

**The import-topology guard correction (`tests/test_referee_guards.py`):**

- Split `test_no_referee_module_imports_the_detect_or_context_modules` into (a)
  `test_no_referee_module_imports_the_detect_module` — UNCHANGED blanket ban on
  `desk_playbook_detect`, zero exceptions, and (b)
  `test_no_referee_module_other_than_referee_null_imports_the_context_module` — a narrower ban on
  `desk_playbook_context` that exempts ONLY `referee_null.py`, citing `docs/goal.md`'s exact
  Read-side-law sentence in the code comment. The reverse-direction guard
  (`test_the_detect_and_context_modules_import_no_referee_module`) is byte-unchanged. Added a
  can-fail counter-test for the new narrower rule. `referee_stats.py`'s own separate, stricter ban
  (TC-23, `test_referee_stats_module_imports_none_of_the_banned_rail_detector_context_modules`) is
  untouched — it still bans `desk_playbook_context` too.

## Files Changed

- `apps/backend/app/research/referee_null.py` -- NEW. The matched-null builders, stores, run
  ledger, compute manager, and CLI (J-04).
- `apps/backend/app/research/referee_stats.py` -- the `min_attainable_p` fix in `permutation_test`
  (one conditional, one line) and the non-finite fail-loud guard in `_t_statistic`/
  `bootstrap_ci_occurrence`/`bootstrap_ci_cluster` (one shared helper pair, checked at each entry
  point). No other line changed.
- `apps/backend/app/research/referee_routes.py` -- added the five `/nulls*` routes + their
  dependency providers + a module-level `RefereeNullComputeManager` singleton. `GET /evidence`
  (J-01) is byte-unchanged.
- `apps/backend/tests/test_referee_null.py` -- NEW. 29 tests: TC-1 through TC-9, TC-13, TC-16
  (library level, using real rail measurements against hand-built `RawBar` fixtures — never a
  hand-typed forward block), store-discipline (no update/delete method), compute-manager
  single-flight/cancel (both unit-level and route-level via `TestClient`), TC-17 through TC-20
  (route level), a CLI smoke test (real `main()` invocation via `sys.argv` + env-scoped stores,
  including an idempotent-second-run check and an unknown-spec-id argparse-rejection check).
- `apps/backend/tests/test_referee_stats.py` -- 9 new tests (TC-10 hand fixture + tail-regime
  sweep, TC-11 seeded-branch regression, TC-12 finite-guard x5, TC-15 mutation counter-test); TC-8's
  tolerance tightened 6.0->3.5; one pre-existing iter-3 assertion corrected (`0.25` -> `0.5`, per
  this iteration's own fix) with an explanatory comment.
- `apps/backend/tests/test_referee_guards.py` -- the guard split described above; net +2 test
  functions (1 split into 2, plus a new can-fail counter-test).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ --junit-xml=/tmp/junit_full.xml -q`
(pyproject.toml's `addopts = "-q"` means `-q` on the CLI becomes `-qq`, which prints no "N passed"
summary line — verified via the JUnit XML instead, this project's own established practice per
every prior `goal-referee-iter-*` handoff.)

Result: **2553 collected, 2545 passed, 8 skipped, 0 failed, 0 errors** (~252s). Exceeds the
iteration-4 floor (2513 collected / 2505 passed / 8 skipped) by exactly **+40** — 29 new tests in
`test_referee_null.py` (27 library/route + 2 CLI) + 9 new tests in `test_referee_stats.py` + a net
+2 in `test_referee_guards.py` (1 split into 2, plus 1 new can-fail counter-test) = 40, confirming
no stray/uncounted collection (an earlier draft accidentally imported `referee_null.py`'s
`test_perm_spec_parameters`/`test_perm_spec_signature` functions under their literal names, which
pytest's `test_*` collection convention picked up as phantom test functions — caught via a
`PytestReturnNotNoneWarning` during development and fixed by importing them under aliased names).

Targeted re-runs, all green:
- `tests/test_referee_stats.py` (81 tests incl. the 9 new ones)
- `tests/test_referee_null.py` (29 tests, new)
- `tests/test_referee_guards.py` (guard corrections)
- `tests/test_referee_evidence.py` + `tests/test_referee_oracles.py` (J-01/J-02/J-03
  required-still-passing regression check — both green, unmodified)
- `tests/test_copy_discipline.py`, `tests/test_mcp_server.py` (still 20 tools),
  `tests/test_no_execution_path.py` -- all green

`Config().config_fingerprint()` verified live: still `08e471b10130e1e2`.

`git status --porcelain` confirms the diff is scoped to exactly the 6 files above (plus this
handoff and `status.json`) — zero diff to `desk_forward.py`, `desk_playbook.py`,
`desk_playbook_context.py`, `levels.py`, `tradability.py`, `setups.py`, `edge_report*.py`,
`backtests.py`, `pnl_scan.py`, `app/config.py`, `app/main.py`, or
`docs/referee-statistical-spec.md`. Zero new `Config` field (every new constant is a module
constant in `referee_null.py`, read at call time by its own parameter-blob builders).

**Service startup verified** (`scripts/dev.sh`, ports 8301/3301 — this project's deterministic
port offset): started cleanly, both `GET /research/desk/referee/nulls` (new, honest empty state)
and `GET /research/desk/referee/evidence` (existing, unmodified — served the same real-corpus
numbers as every prior iteration: 210 records / 156 sessions / 3222 signals at current basis) 200'd
against the REAL backend/corpus; stopped by exact PID (the full process tree — `uvicorn --reload`'s
WatchFiles worker child, and `next dev`'s `npm exec` -> `sh -c` -> `node` -> `next-server` chain,
not just the top-level PIDs `dev.sh` itself prints — located via `lsof`/`ss` and killed
individually, per the host's own "never pattern-based `pkill`" rule); restarted a second time with
**no port conflicts**; stopped again, verified both ports free and no stray project process left
running. No live external-integration test was needed this iteration (no adapter/scraper/API code
added — the module is a pure read-side library over already-recorded stores).

## Known Issues

- **The remaining-time boundary rule uses literal wall-clock distance to the session's own 16:00
  ET close, not bar-count-equivalent minutes.** TC-4 hand-verifies this is the correct reading (60
  min remain at 15:00 ET before a 16:00 close), and it is simpler/more robust than an
  array-index-based formula (independent of exactly where the bar series happens to start/end).
  This is a genuine, reversible interpretive choice where the spec's prose is compatible with
  either reading — flagged here for reviewer visibility, not because I believe it is wrong.
- **The seeded stream's `hypothesis_id` slot is filled with the null-spec id itself** (`referee_
  stream(null_spec_id, "null-draw", session_date=..., i=observation_id)`), since no hypothesis
  exists yet at J-04 (registration is J-05). This is documented in the module docstring as a
  deliberate, reversible pre-registration analogue — J-05, once hypothesis ids exist, may choose to
  re-scope future null builds under a real hypothesis id instead; today's null RECORDS themselves
  are keyed by `(observation_id, null_spec_signature)`, not by this stream choice, so nothing
  downstream depends on this specific seed-key shape.
- **`referee-test-perm-v1`'s minting function lives in `referee_null.py`**, not `referee_stats.py`
  (the module it conceptually describes) — an explicit implementation choice the iteration spec
  itself named as open ("File placement ... is an implementation choice"). No route or store field
  reads it this iteration; J-05/J-06 are its first real consumers.
- **`window_overlap_fraction`'s exact formula is my own design** (spec Sec4.1 names the disclosure
  but not its formula): the fraction of the OCCURRENCE's own measurement window that each anchor's
  window overlaps, in bar-index space. Not gate-tested by any TC number (TC-1/TC-2 assert counts
  and exclusion flags, not this value precisely) — served honestly, computed once via
  `math.fsum`-class accumulation for the record-level `mean_window_overlap`.
- **No real-corpus null-build was run** (explicitly OUT OF SCOPE this iteration — "Any real-corpus
  null-building compute run ... is a future explicit operator act once J-05/J-06/J-07 need it").
  `GET /research/desk/referee/nulls` against the real corpus correctly serves the honest empty
  state (`{"records": [], "integrity_errors": []}`), verified live above.
- **J-10's browser regression sentinel (the full kept-product browser walk with fresh screenshots
  after a clean `.next` rebuild) was NOT performed in this dev pass** — matching every prior
  `goal-referee-iter-*` dev handoff's own precedent (iter-1 through iter-4 all note this is a
  QA-stage responsibility, not a dev-pass deliverable), and consistent with this iteration's own
  spec text ("J-04 itself carries no browser acceptance and no golden replay is possible for it").
  Zero frontend files changed this iteration (no frontend handoff written).
