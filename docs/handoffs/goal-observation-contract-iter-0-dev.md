# goal-observation-contract-iter-0 Dev Handoff

**Phase:** goal-observation-contract-iter-0
**Date:** 2026-09-02
**Agent:** developer
**Status:** complete

## What Was Built

Nothing — by design. This is Era "Observation Contract v1"'s **verify-only baseline** (Mode:
baseline, Depth: lean). The iter spec's IN SCOPE section is explicitly empty for both Backend and
Frontend ("none — baseline is verify-only, no code changes"); the developer step's entire job is
confirming the BACKGROUND section's absence/presence claims by direct repo inspection and a live
test run, then recording the exact baseline evidence below for iteration 1 to plan against.

`git diff --stat -- apps/`, `git diff --stat -- docs/` and `git diff --stat -- project-extensions/`
are all **empty** — zero files under any of those three protected trees were created, modified or
deleted this iteration:

```
?? docs/phases/goal-observation-contract-iter-0.md
?? reports/goal-session-observation-contract-index.html
?? runs/goal-session-observation-contract/
 M reports/qa-scoped-backend-store-manifest.md
```

The four entries above are pipeline/report artifacts, not product source: the iter spec doc, the
goal-session's HTML index, the goal-mode session state directory, and a pre-existing tracked report
file (`reports/qa-scoped-backend-store-manifest.md`) that a shared test fixture rewrites with the
current run's scratch-store paths on every pytest launch in this repo (its own header describes it
as "the durable record of which store roots THIS launch's backend rig is bound to" — rewritten by
design, not a source/spec/config edit; `reports/` is not one of the DEFINITION OF DONE's protected
trees). No file under `backend`, `frontend`, `docs/` (outside this spec + the pre-existing
`blueprint.md`) or `project-extensions/` was touched.

## Baseline absence/presence confirmation (BACKGROUND section, verified live)

Confirmed absent, exactly as the spec predicted:

- `apps/backend/app/observation_contract.py` — does not exist.
- `GET /tape/{ticker}/observation` — not registered in `apps/backend/app/main.py`. Its `/tape/*`
  siblings are all present and unchanged: `/tape/{ticker}/state` (line 543), `/features` (548),
  `/events` (553), `/summary` (558), `/history` (563), and the `/tape/{ticker}/stream` websocket
  (617). `/observation` is the only sibling missing.
- `WatchManager.get_observation_source` — zero matches in `apps/backend/app/watch_manager.py`.
- `tests/test_tape_observation_*.py` — zero files match anywhere under `apps/backend/tests/`.

Confirmed present, exactly as the spec predicted:

- `docs/goal-archive/goal-2026-09-02.md` and `docs/observation-contract-spec.md` — both exist,
  committed.
- The dated opening note in `docs/research-directions.md` — present verbatim: "**OBSERVATION-CONTRACT
  OPENING NOTE (2026-09-02, operator pivot, under §5.6 'goal.md wins').**" confirming the Hypothesis
  Foundry closure and the era-open act.
- `apps/frontend/app/page.tsx`, `apps/frontend/app/structure/page.tsx`,
  `apps/frontend/app/desk/page.tsx` — all exist, confirmed untouched by `git diff --stat -- apps/`.
- The nine existing guard-test files named in the Anti-goal reminders all exist unedited:
  `test_no_execution_path.py`, `test_feed_basis.py`, `test_copy_discipline.py`,
  `test_profile_equivalence.py`, `test_fingerprint_epoch_retirement.py`, `test_mcp_server.py`,
  `test_stream_lifecycle.py`, `test_observer_equivalence.py`, `test_epoch_anchor.py`.

## Baseline test counts (the J-06 sentinel anchor)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

**3930 passed, 8 skipped, 0 failed, 0 errors (3938 collected).** Exit code 0.

Note on how this was derived: pytest 9.1.1 in this environment does not print its usual final
"N passed, M skipped in Ts" summary line after the warnings block (confirmed reproducibly across
three separate invocations, including a bare `--collect-only -q`, all missing the line byte-for-byte
— an environment/pytest-version quirk, not a test failure). The exact counts above were derived by
tallying the `-q` progress-line result characters (`.` = passed, `s` = skipped; zero `F`/`E`
characters present anywhere in the output) from the captured log, which is a lossless 1:1 count of
outcomes per pytest's own `-q` reporting contract.

This is **byte-identical** to the immediately-preceding era's own closing baseline
(`docs/handoffs/goal-hypothesis-foundry-iter-9-dev.md`: "3930 passed, 8 skipped, 0 failed" —
"matches iter-8's last recorded run exactly"). Zero test-count drift across the era boundary: the
`docs/goal.md` rewrite and the era-open docs commit (`2f3d2b32`) that opened Observation Contract v1
touched no code under `apps/`, exactly as this era's own Constraints require.

The 8 skips are the pre-existing environment-gated `integration`-marker tests (skipped by default,
consistent with the Deterministic-evidence rule — no mandatory test requires Alpaca, the network,
credentials or market hours): `tests/test_live_integration.py`, `tests/test_yahoo_live_integration.py`,
`tests/test_desk_universe_live_integration.py`, `tests/test_event_recording_integration.py`.

Command: `cd apps/frontend && npx tsc --noEmit`

**0 errors.** Exit code 0, empty output.

`config_fingerprint` (live-computed, not just grepped):

```
cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"
-> 08e471b10130e1e2
```

Matches the goal.md-pinned value exactly.

MCP contract (live-counted from `apps/backend/app/mcp/__init__.py`): 28 distinct `name="..."` tool
registrations (`tape_state`, `tape_features`, `tape_history`, `datasets`, `bars`, `levels`,
`tradability`, `setups`, `backtests`, `strategies`, `edge_report`, `desk_universe`, `desk_screen`,
`desk_forward`, `desk_playbook`, `desk_playbook_evidence`, `desk_referee`, `desk_referee_registry`,
`desk_micro_readiness`, `desk_micro_snapshots`, `desk_scout`, `desk_walkforward`, `desk_vault`,
`desk_graduation`, `pnl_ledger`, `taxonomy`, `ui_route_map`, `get_endpoint`) — matches the module's
own docstring pin ("MCP contract v8 — 27 -> 28 tools") and the goal's Foundation-remains-intact
success criterion (v8 / 28 tools). No new tool exists (correctly deferred — the route itself is
unbuilt).

## Journey-by-journey verification evidence

The goal-evaluator (via browser-qa-agent) assigns the authoritative pass/fail/partial status per
journey; this section records what direct codebase/config inspection actually showed — the
dev-level leg of the spec's Test-first contract (TC-1..TC-6), not the live-browser leg.

### J-01 — Pure projection, semantic identity, provenance, integrity (expected FAIL) — CONFIRMED ABSENT

- `apps/backend/app/observation_contract.py` does not exist — no builder, no schema constants, no
  hash laws.
- `tests/test_tape_observation_projection.py` does not exist.
- No route serves `"schema_version": "tape-observation-v1"` anywhere (confirmed: no `/observation`
  route registered at all — matches TC-1's generic-404 prediction).

### J-02 — Three honest time concepts, atomic read (expected FAIL) — CONFIRMED ABSENT

- No `timing.settled_at_utc` / `available_at_utc` / `availability_basis` field is served anywhere —
  no code path produces any of the three.
- `tests/test_tape_observation_time.py` does not exist.
- `WatchManager` has no settled-pair read (`get_observation_source` absent, confirmed above) — the
  atomic-read invariant this journey depends on has no implementation to test.

### J-03 — Lifecycle, feed basis, session identity (expected FAIL) — CONFIRMED ABSENT

- `WatchManager.get_observation_source` is not defined — no `lifecycle.*` / `source.session_id` /
  `source.data_feed` projection exists.
- `tests/test_tape_observation_lifecycle_feed.py` does not exist.
- The existing lifecycle/feed-basis machinery this journey will read through (`data_feed_for_scenario`
  in `apps/backend/app/`, the seven-state stream-status vocabulary) is present and unchanged
  (`tests/test_feed_basis.py`, `tests/test_stream_lifecycle.py` both still exist and are unedited) —
  confirmed as the reuse target for iteration 1+, not touched this iteration.

### J-04 — Ingestion-path equivalence (expected FAIL) — CONFIRMED ABSENT

- `tests/test_tape_observation_path_equivalence.py` does not exist.
- No code path anywhere computes `observation_hash` or `artifact_hash` (consequence of J-01's
  absence — the hash laws live in the unbuilt `observation_contract.py`).
- The replay/live feeder mechanisms this journey will drive (`_replay_events`, `_feed_live`,
  `LiveProvider`) are existing, unchanged infrastructure (`tests/test_observer_equivalence.py` still
  green, 0 modifications) — confirmed as the reuse target, not touched.

### J-05 — One read-only machine path (expected FAIL) — CONFIRMED ABSENT

- No `/tape/{ticker}/observation` route exists on the FastAPI app (`main.py` grep above, only the
  five existing `/tape/*` siblings plus the websocket).
- `tests/test_tape_observation_route.py` does not exist.
- The MCP `get_endpoint` proxy tool exists (28-tool set above) but has no `/observation` path to
  proxy yet — no new named MCP tool was added (correct; the goal requires none).

### J-06 — Guards and the regression sentinel (expected PARTIAL) — CONFIRMED PARTIAL

- **Era-open paperwork sub-check: DONE.** `docs/goal-archive/goal-2026-09-02.md`,
  `docs/observation-contract-spec.md`, and the dated `docs/research-directions.md` opening note all
  exist and are committed (confirmed above, quoting the note verbatim).
- **Guard-suite sub-check: UNBUILT.** `tests/test_tape_observation_guards.py` does not exist —
  nothing has been built yet for it to guard (copy-discipline lexicon, compound-identifier ban,
  external-system reference guard, English-only guard, real-provider isolation guard,
  mutator-call-site guard are all deferred).
- **Regression-sentinel sub-check: GREEN.** Full backend suite 3930 passed / 8 skipped / 0 failed
  (byte-identical to the prior era's closing baseline); frontend `tsc --noEmit` 0 errors;
  `config_fingerprint` confirmed live at `08e471b10130e1e2`; MCP contract confirmed at 28 tools; the
  nine named existing guard suites (`test_no_execution_path.py` etc.) all present and unedited.
- The full click-through browser confirmation that `/`, `/structure` and `/desk` each render with
  zero new panel/link/control, and that `/tape/SIM-BIDABS/observation` currently 404s from the
  Cockpit's own Sim watch flow, is the browser-qa-agent's step per the spec's TESTING REQUIREMENTS —
  this is the dev-level code/config inspection leg only.

## Files Changed

- (none — verify-only baseline; zero source, spec or config modifications under `apps/`, `docs/`
  outside this spec, or `project-extensions/`)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **3930 passed, 8 skipped, 0 failed** (3938 collected), exit 0 — byte-identical to the prior
era's closing baseline.

Command: `cd apps/frontend && npx tsc --noEmit`
Result: **0 errors**, exit 0.

## Known Issues

- **pytest 9.1.1 in this environment does not print its final "-N passed, M skipped in Ts" summary
  line** after the warnings block, reproducibly (confirmed across three separate invocations
  including a bare `--collect-only -q`). This is an environment/pytest-version display quirk, not a
  test failure — the exact pass/skip/fail counts above were derived losslessly from the `-q`
  progress-line character tally (a 1:1 mapping per pytest's own reporting contract: `.`=passed,
  `s`=skipped, `F`=failed, `E`=error — zero `F`/`E` characters present) and independently
  cross-verified against the immediately-preceding era's own recorded closing count, which matches
  exactly. Not this iteration's scope to fix (pytest/environment configuration, unrelated to the
  Observation Contract build); future iterations reading this handoff for a baseline count should be
  aware the terminal summary line may need the same tally workaround.
- `reports/qa-scoped-backend-store-manifest.md` was rewritten by the pytest run's own shared fixture
  (expected, pre-existing behavior across every prior era's baseline; not a source/spec/config file
  and not in the DEFINITION OF DONE's protected-tree list).
- No live network call was made (correctly out of scope — this era's Deterministic-evidence rule
  forbids any mandatory journey or test depending on Alpaca, the network, credentials or market
  hours).
- Full browser-driven verification of all six journeys (the Sim-mode `/tape/SIM-BIDABS/observation`
  step, the Watch/Pause/Resume/Stop lifecycle walk, and the `/`, `/structure`, `/desk` unchanged-render
  spot-check) is the browser-qa-agent's step per the spec's TESTING REQUIREMENTS; this handoff covers
  the dev-level code/config/test-suite inspection leg only.

## Suggested Next Phase

Per the spec's NOTES and `docs/goal.md`'s Binding Execution Order — constants/builder/hash laws (J-01)
must land before the time law/atomic read (J-02), before descriptor/lifecycle/provenance (J-03),
before ingestion-path equivalence (J-04), before the route (J-05), before guards/sentinel (J-06) —
iteration 1 should build **J-01 alone**: the schema constants, `build_tape_observation` in the new
`apps/backend/app/observation_contract.py` (pure, no clock/git/engine access), both hash laws per
Constitution §6, and `tests/test_tape_observation_projection.py` with its named
`test_counterexample_*` tests. `EngineSnapshot` (the sole semantic producer this era projects from,
unchanged) and the four-group partition definition are both already fully specified in
`docs/goal.md` Constitution §1 and §6 — no ambiguous interpretive call is needed to start.
