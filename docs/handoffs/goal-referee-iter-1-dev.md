# goal-referee-iter-1 Dev Handoff

**Phase:** goal-referee-iter-1
**Date:** 2026-08-14
**Agent:** developer
**Status:** complete

## What Was Built

J-01 — "the evidence readiness fold": the first concrete Referee artifact, a single new backend
endpoint reporting honest per-family evidence readiness. No frontend change (goal.md marks J-01
`(Keyless; automated.)`).

- **`app/research/referee_evidence.py` (new)** — the readiness fold, pure aggregation over
  already-recorded `PlaybookStore` / `DatasetStore` / `JournalStore` records:
  - `current_playbook_detector_basis()` — `sha256(canonical(playbook_parameters()))[:16]`
    (`docs/goal.md` Key Capability 1), read fresh at call time.
  - `playbook_occurrence_readiness(store, config_fingerprint)` — `records`/`distinct_sessions`
    are the store's raw, unfiltered content; `signals_at_current_basis`/`per_setup_side` pool only
    the newest-per-`session_date` records (T-6) whose own `(detector_basis, config_fingerprint)`
    match today's live values. A stale-basis record (e.g. recorded before a genuine
    detector-constant revision) still counts toward the first two fields, never the last two.
    `per_setup_side` is sparse — only cells with at least one signal appear (proven by TC-5's
    `== []` zero-corpus requirement).
  - `strategy_trade_readiness(dataset_store, journal_store)` — `dataset_count`/`per_split_counts`
    off `DatasetStore.list()`; `trade_count` sums `len(result.trades)` over every recorded
    backtest report (`JournalStore.list_backtests` at an effectively-unlimited scan cap — the
    serving-only `Config.backtest_list_max` of 100 would silently undercount an aggregate); the
    honest tick-gate statement (`REFEREE_TICK_GATE_SYMBOL_DAYS = 150`,
    `docs/research-directions.md` Card 5.2) via `_tick_gate_state`; `basis_caveats` carrying the
    new `REFEREE_FORMING_BAR_BASIS_CAVEAT`.
  - `REFEREE_FORMING_BAR_BASIS_CAVEAT` — the Card-6.4 forming-bar disclosure, **authored for the
    first time this iteration** (no verbatim text existed anywhere before). Exported as the single
    source of truth; J-06/J-08 must import and reuse this exact string rather than minting a
    second version. Verified clean against `test_copy_discipline.find_violations`.
  - Both stores' own `.list()` `errors` returns are surfaced verbatim as an additive
    `integrity_errors` key on each of the two blocks — the desk router's own uniform convention
    (every sibling `GET` route in `desk_routes.py` does this), and how this iteration's "a
    corrupted file must propagate the store's surfaced error, never be silently dropped"
    testing requirement is satisfied without touching any of the six pinned response keys.
- **`app/research/referee_routes.py` (new)** — `router = APIRouter(prefix="/research/desk/
  referee")`; `GET /evidence` wires `referee_evidence()` to the playbook store (imported verbatim
  from `desk_routes.get_playbook_store` — no second provider), the dataset store (imported
  verbatim from `routes.get_dataset_store`), and the `JournalStore` via the existing
  `ResearchRegistry` (`routes.get_registry`, `registry.store` — the same seam
  `GET /research/backtests` already reads). A fresh router/file rather than folding into
  `desk_routes.py` (already 1600+ lines) — mirrors that file's own stated rationale for splitting
  off `routes.py`; the era's Data Contract table names five more referee routes landing in later
  iterations under this same prefix, so a dedicated file is the right home from the start.
- **`app/main.py`** — one import + one `app.include_router(referee_router)` call, mounted beside
  `desk_router`. No MCP change needed: `get_endpoint`'s `ALLOWED_GET_PREFIXES` already includes
  `"/research/"` (confirmed by reading `app/mcp/__init__.py` directly), so the new path is reached
  automatically.
- **`tests/test_referee_guards.py` (new, 8 tests)** — the two named guard-test pins:
  1. The `playbook-band-context-v3` spec-drift pin: `docs/playbook-detector-spec.md` §6's heading
     block and its "Structural (shape, not thresholds)" constants line both asserted to contain
     the **live** `PLAYBOOK_CONTEXT_ALGORITHM_VERSION` value (never a hardcoded string — the
     assertion fails the instant doc and code diverge in either direction), plus a whole-module
     `hashlib.sha256(inspect.getsource(desk_playbook_context))` zero-diff pin recorded at the
     start of this iteration (the module is untouched, so it still matches at the end).
  2. The `docs/research-directions.md` catalog-reconciliation pins: one substring per status-table
     row (eras 5/5B/5C/5D/B/B2) and the two "AMENDED 2026-08-14" notes (Cards 6.2, 6.3) — every
     pinned substring was independently `grep -F`-verified against the committed file before being
     hardcoded into the test.
  Each guard carries a seeded can-fail counter-test (the `test_desk_playbook_guards.py`
  precedent).
- **`tests/test_referee_evidence.py` (new, 7 tests)** — hermetic fixture tests for the endpoint,
  built through each store's own public write path (`PlaybookStore.record`, `DatasetStore.record`,
  `JournalStore.insert_backtest`), never a hand-typed file:
  - TC-1/TC-2: one fixture corpus (4 playbook records / 3 session dates) exercising newest-per-date
    supersession (an older record superseded by a newer one at the same date), cross-record
    pooling into two `(setup, side)` cells, and stale-basis exclusion (a fifth-signal record
    planted with deliberately different `parameters`) — every count hand-verified.
  - TC-3: 3 datasets across both splits + 3 backtest reports, including one `status: "running"`
    record with no `result` yet, proving it contributes zero trades rather than erroring.
  - TC-4: the unmet tick-gate statement + the caveat string on the endpoint, plus direct
    unit tests of both `_tick_gate_state` branches (met and unmet).
  - TC-5: a fully empty corpus serves an honest `200` with every count `0`/`[]`, never a
    `404`/`500`.

## Files Changed

- `apps/backend/app/main.py` -- mount the new referee router (7 additive lines).
- `apps/backend/app/research/referee_evidence.py` -- new: the readiness fold.
- `apps/backend/app/research/referee_routes.py` -- new: `GET /research/desk/referee/evidence`.
- `apps/backend/tests/test_referee_evidence.py` -- new: hermetic fixture tests (TC-1..TC-5).
- `apps/backend/tests/test_referee_guards.py` -- new: the two named guard-test pins (TC-6..TC-8).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

Result: **2441 collected, 2433 passed, 8 skipped, 0 failed, 0 errors** (verified via
`--junit-xml` — this pytest install's `-q` mode prints no final terminal summary line, a
known pre-existing environment quirk also recorded in `goal-desk-iter-32`'s own status.json, not
introduced by this diff). 2433 = the iteration-0 floor of 2418 plus exactly this iteration's 15
new tests (7 + 8) — every pre-existing test still passes unmodified.

`Config().config_fingerprint()` still prints `08e471b10130e1e2`. `git diff --stat` against the
pre-iteration commit touches only `apps/backend/app/main.py`; zero diff to `desk_playbook*.py`,
`desk_forward.py`, `levels.py`, `tradability.py`, `setups.py`, `pnl_scan.py`, or `app/config.py`.

**Live verification against the REAL corpus** (`scripts/dev.sh`, backend on `:8301`): the endpoint
reproduces every one of `docs/goal.md`'s own recorded "corpus reality at authoring" numbers
byte-for-byte — `playbook_occurrence.records == 210`, `.distinct_sessions == 156`,
`.signals_at_current_basis == 3222`, and all ten `per_setup_side` cells (e.g.
`double_top:short 771/105`, `capitulation:long 473/71`, `cup_handle:long 1/1`) exactly as goal.md
lists them. Notably, `signals_at_current_basis` reaches **156** dates rather than the 155 goal.md
attributes to exact-`playbook_input_signature` pooling — the intended "survives daily bar top-ups"
property of pooling on `detector_basis` (parameters-only) instead of the full signature (which
also hashes bar-series checksums). `strategy_trade` served `dataset_count == 18` (12 train / 6
holdout), `trade_count == 873`, `tick_gate_met == false` ("132 short of the gate").

`scripts/dev.sh` started both backend (`:8301`) and frontend (`:3301`) cleanly (cockpit `/`
compiled and rendered `200`); the new endpoint served `200` against the real corpus both times.
Stopped (confirmed the full process tree — including the `uvicorn --reload` worker and
`next-server` child processes, not just the top-level PIDs — was gone) and restarted a second
time with no port conflicts; stopped again afterward. No stray backend/frontend process was left
running at the end of this dev pass.

## Known Issues

- **Zero frontend change** — J-01 is backend-only per `docs/goal.md`'s own `(Keyless;
  automated.)` marker; no `docs/handoffs/goal-referee-iter-1-frontend.md` was written (none was
  applicable).
- **J-10 (the regression sentinel) was not run by this dev pass** — it is a separate
  required-still-passing check (cockpit, `/structure`, every shipped `/desk` section), not a J-01
  deliverable; the iter spec assigns it to the browser-qa lane.
- **No real MCP call was made** — none was needed. `app/mcp/__init__.py`'s
  `ALLOWED_GET_PREFIXES = ("/tape/", "/research/", "/meta/")` is a plain prefix check (confirmed
  by reading the source, not assumed), so `get_endpoint` reaches the new
  `/research/desk/referee/evidence` path automatically with zero MCP code change — consistent
  with this iteration's explicit "zero MCP changes" scope.
- **The `integrity_errors` key is additive beyond the iteration spec's literally-pinned response
  shape.** The spec's Data-contract section says "No other new displayed/served value this
  iteration," but the TESTING REQUIREMENTS' Error-cases bullet separately requires that "a
  corrupted/unparseable store file must propagate the existing store's surfaced error, never be
  silently dropped." Every sibling `GET` route in `desk_routes.py` satisfies the identical
  requirement the identical way (serving `store.list()`'s own `errors` return verbatim as
  `integrity_errors`, HTTP 200, never a 404/500) — judged the more faithful reading of "propagate,
  never silently drop" than either raising (which would be inconsistent with this router family's
  own never-404/500 convention and would let one corrupted historical file take down the whole
  readiness endpoint) or truly adding nothing (which would silently exclude a corrupted file's
  existence from the counts with no disclosure at all, the literal failure mode the requirement
  warns against). None of TC-1 through TC-12 assert an exhaustive key set on either block, so this
  is judged additive rather than a shape violation — flagged here for the reviewer's own
  read on the trade-off.
- **`trade_count` counts every recorded backtest report's trades, not one report's.** The pinned
  field is a single integer with no per-strategy/per-profile breakdown, so it was implemented as
  the simplest defensible reading: the sum of `len(result.trades)` across every backtest report on
  file (a readiness total, "how much backtested trade evidence exists," mirroring how
  `playbook_occurrence` totals across every recorded signal rather than one record). If a
  narrower reading (e.g. champion-only, or the most recent sweep only) was intended, that is a
  one-line change inside `strategy_trade_readiness`.
