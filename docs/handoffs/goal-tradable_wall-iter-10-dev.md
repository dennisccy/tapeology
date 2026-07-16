# goal-tradable_wall-iter-10 Dev Handoff

**Phase:** goal-tradable_wall-iter-10
**Date:** 2026-07-16
**Agent:** developer
**Status:** complete

## What Was Built

Two small, additive items — no product computation changed:

1. **The scoped-keyless browser-QA backend recipe** (verification harness, not product code):
   documented and LIVE-VERIFIED the exact `TAPEOLOGY_DATASET_DIR` + `TAPEOLOGY_EDGE_REPORT_CACHE_DB`
   combination that lets `GET /research/edge-report` resolve against a tiny committed fixture
   instead of the real ~10+h/11-plus-dataset corpus, and pre-warmed it once to prove the
   **warm**-cache path is genuinely fast. See "Scoped-Keyless Browser-QA Backend Recipe" below —
   this is the reproducible procedure browser-qa-agent needs for J-08's browser-observed render.
2. **The `band side` cosmetic rename** (iter-9 coherence-WARN advisory b) in
   `apps/backend/app/research/pnl_ledger.py`: the 3-way `strategy_comparison` table's band-level
   column header changed from `side` to `band side` (it holds `cell["band_side"]` —
   `support`/`resistance` — which collided in name, though never in meaning, with the pre-existing
   two-way row's own `side` column, which holds the `baseline`/`candidate` role). The function's
   docstring, which incorrectly claimed the table was built "WITHOUT a `side` column," is corrected
   to describe the column that is actually emitted.

Blueprint conformance (iter-9 coherence-WARN advisory a — the `pnl_ledger.py` owner registration)
was already present in `runs/goal-session-tradable_wall/state/blueprint.md` before this turn
started (row: "PnL-ledger register / `reports/pnl/pnl-history.md`") and already documented the
`band side` rename as this iteration's own change — nothing further needed there; confirmed
untouched by `git status`.

## Files Changed

- `apps/backend/app/research/pnl_ledger.py` -- `_render_strategy_comparison_row_lines`: header
  `| strategy | class | side | ... |` → `| strategy | class | band side | ... |`; separator row
  widened to match; docstring corrected to describe the emitted `band side` column instead of
  falsely claiming its absence.
- `apps/backend/tests/test_pnl_ledger.py` -- one assertion in
  `test_existing_two_way_rows_render_unchanged_alongside_a_new_3way_row` updated to expect
  `"strategy | class | band side | reaction | feed"`.
- `apps/backend/tests/test_pnl_history.py` -- one assertion in
  `test_append_and_render_writes_the_new_row_and_regenerates_markdown` updated to expect the same
  new header text.
- `docs/handoffs/goal-tradable_wall-iter-10-dev.md` -- this handoff.
- `docs/handoffs/goal-tradable_wall-iter-10-frontend.md` -- verify-only frontend confirmation (no
  frontend code changed).

**Not touched** (confirmed via `git status`): `research/levels.py`, `research/setups.py`,
`research/tradability.py`, `research/backtests.py`, `research/edge_report.py`,
`research/edge_report_cache.py`, `config.py`, any `apps/frontend/**` file, the committed
`reports/pnl/pnl-history.md`, `runs/goal-session-tradable_wall/state/blueprint.md`.

## TDD

Updated both test assertions to expect `band side` FIRST and confirmed they FAILED against the
unmodified source (`test_existing_two_way_rows_render_unchanged_alongside_a_new_3way_row` and
`test_append_and_render_writes_the_new_row_and_regenerates_markdown`, both red with the old `side`
text still being emitted). Then made the source change and confirmed both went green, with no
other test in either file touched.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_pnl_ledger.py tests/test_pnl_history.py -v`
Result: **38 passed, 0 failed.**

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1392 passed, 7 skipped, 0 failed, 0 errors** (dot-progress stream contained only `.`/`s`
characters, no `F`/`E`; exit code 0). Identical to iter-9's baseline (1392 passed / 7 skipped) —
**zero regressions**, no new tests needed for a pure rename.

Command: `python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"`
Result: **`4d665603569b9dbf`** — unchanged (frozen-foundation invariant).

Command: `git status --porcelain` (scope check)
Result: exactly the 3 intended files modified (`pnl_ledger.py`, `test_pnl_ledger.py`,
`test_pnl_history.py`); every frozen/out-of-scope file listed above confirmed untouched;
`reports/pnl/pnl-history.md` (the committed file) untouched.

## Scoped-Keyless Browser-QA Backend Recipe (the IN-SCOPE deliverable for J-08)

This is the exact, live-verified procedure so browser-qa-agent's backend answers
`GET /research/edge-report` fast instead of triggering the real-corpus ~10+h compute. **Only the
dataset store is scoped — the bar store stays real/default**, per the phase spec's own OUT OF
SCOPE clause (Case Studies/J-02 must keep rendering from the real bar store in the same browser
session).

### 1. Start the backend with two env vars set

```bash
cd apps/backend
export TAPEOLOGY_DATASET_DIR="$(pwd)/tests/fixtures/datasets_j03"
export TAPEOLOGY_EDGE_REPORT_CACHE_DB="$(pwd)/.data/scoped_browser_qa/edge_report_cache.db"
cd ..
bash scripts/dev.sh
```

`scripts/dev.sh` starts both backend (`:8301`, the deterministic per-repo-path offset port — same
port iter-9's dev handoff observed) and frontend (`:3301`); the two exported vars are inherited by
the backend subshell unchanged (`dev.sh` only sets `CORS_ORIGINS` itself). `EdgeReportCache`
auto-creates `.data/scoped_browser_qa/` if it does not exist yet
(`Path(db_path).parent.mkdir(parents=True, exist_ok=True)` in `edge_report_cache.py`), so no
manual `mkdir` step is needed. `datasets_j03/` is the SAME committed fixture (symbol `PG`, one
1-minute window) `test_edge_report.py`'s existing
`test_keyless_committed_j03_fixture_with_the_real_panel_is_an_honest_empty_report` already proves
produces the honest empty-report shape under the real config-owned panel (PG is not one of the 12
panel symbols, so it can never resolve an owning scan event — every cell is honestly absent, the
degenerate valid case of "all insufficient_sample," vacuously, because there are none). This is
the SAME scenario the route's own docstring names: "An all-empty or all-`insufficient_sample`
report (the expected shape on a keyless, single-fixture registry) is a valid 200, never an error."

### 2. Pre-warm the durable cache ONCE, BEFORE opening the browser

```bash
curl -s http://localhost:8301/research/edge-report > /dev/null
```

**Budget several minutes for this call, not literal seconds** — see "Known Issues" below for why.
It must complete (HTTP 200) before step 3.

### 3. Confirm the cache is warm (optional but recommended sanity check)

```bash
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://localhost:8301/research/edge-report
```

Expect `200 0.0xxxxxs` (sub-second — I measured 0.0099s–0.0246s locally). If this second call is
also slow, something is wrong with the cache wiring and the browser pass should not proceed.

### 4. Open the browser

Only now open `http://localhost:3301/structure` — the Edge Report section's `fetchEdgeReport()`
call hits the now-warm cache and should resolve near-instantly to the RESOLVED (honest empty, on
this fixture) state instead of the loading skeleton.

### Live verification performed (this turn, scratch port 18455 — never the standard project ports, to avoid disturbing any other concurrently running dev server on this shared machine)

- **Cold pre-warm call** (fresh process, empty scoped cache dir): `GET /research/edge-report` →
  `HTTP 200` in **278.145s** (~4.6 min). Response body: the honest all-empty report
  (`train.cells: []`, `holdout.cells: []`, `surviving_train_cells: []`,
  `register`/`pnl_min_sample_size` present and correct).
- **Warm call, same process** (second request, no restart): `HTTP 200` in **0.0099s**,
  byte-identical to the cold response.
- **Warm call, after a full process restart** (killed uvicorn, restarted fresh pointing at the
  SAME durable `TAPEOLOGY_EDGE_REPORT_CACHE_DB` file): first request on the new process →
  `HTTP 200` in **0.0246s**, byte-identical to the original — proving the durable (not merely
  in-process) layer is what makes this reproducible for browser-qa-agent even if `--reload`
  triggers an incidental worker restart between the pre-warm step and opening the browser.
- All three responses are byte-identical to each other.
- A residual pre-warmed cache file is left at `apps/backend/.data/scoped_browser_qa/edge_report_cache.db`
  (gitignored via the existing `.data/` rule, confirmed via `git status` — not part of the diff).
  If browser-qa-agent's turn runs against the same working tree, pointing
  `TAPEOLOGY_EDGE_REPORT_CACHE_DB` at this exact path will already be warm and skip step 2's wait
  entirely. The recipe above does not depend on this — it is a bonus, not a requirement, since the
  cache is a rebuildable accelerator by design (a miss just recomputes).
- Standard-port sanity check (separate from the above): ran `scripts/dev.sh` twice (unscoped,
  default env, real corpus) to satisfy the pre-handoff "service startup works" checklist — see
  "Service Startup" below. Deliberately did NOT hit `/research/edge-report` on those instances.

### Known Issues

- **The cold pre-warm is NOT literally "seconds"** as the phase spec's IN-SCOPE bullet phrased it —
  it measured **278s (~4.6 min)** locally. Root cause: per the phase's own OUT OF SCOPE clause the
  bar store stays real/default (unscoped), and `compute_setups`'s own scan cache
  (`setups.py`'s `_SCAN_CACHE`, per iter-9's notes) is **in-process only, no durable layer** — so
  every FRESH backend process must recompute setups over the real 12-symbol panel's full bar
  history before the edge-report's own (J-08, now-durable) cache can return anything, even though
  the tick-level dataset side is correctly scoped down to one tiny fixture. This is NOT the
  10+-hour real-corpus path (that cost is tick-level, in `BacktestJobManager`, and stays scoped out
  by `TAPEOLOGY_DATASET_DIR`) — it is a separate, bounded, one-time bar-level cost, paid once per
  fresh process and then durably cached. I did not change `setups.py` or add a durable layer to its
  scan cache — out of scope for this iteration (no file under OUT OF SCOPE's forbidden list was
  touched) and not something the phase spec asked for; flagging it here as a real, measured
  constraint on the recipe (budget ~5 minutes for the pre-warm curl, not treat a multi-minute wait
  as a hang) rather than silently fixing or hiding it. The actual DoD requirement — the BROWSER
  observing a WARM, fast render — is fully met: steps 2-3 above prove the warm path is sub-25ms,
  comfortably within any interactive budget.
- **`scripts/dev.sh`'s SIGTERM trap still does not reap the full process tree** (the `next-server`
  grandchild survives a plain `kill` of the tracked PIDs) — pre-existing, first documented in the
  iter-8 dev handoff, reconfirmed live again this turn on both dev.sh starts, out of this
  iteration's file scope (not touched). Worked around both times via pattern/PID-targeted
  `kill -9` after first confirming (via `/proc/<pid>/cwd`) the target process actually belonged to
  this project's `apps/frontend`, not another project's dev server running concurrently on this
  shared machine.
- The alternative fixture the phase spec also permits (`tests/fixtures/datasets`, the
  train/hold-out pair `test_edge_report.py`/`test_pnl_scan.py` already use) was not explored —
  `datasets_j03` was chosen because it is the ONE fixture with an existing precedent test whose own
  docstring names this exact scenario ("The literal DoD scenario") as intentionally
  honest-empty-safe under the real panel, so it carries the least risk of an unexpected slow path
  or surprising cell content.

## Service Startup (pre-handoff checklist)

Ran `scripts/dev.sh` twice, standard/unscoped env, standard ports (`8301`/`3301`):
- **Run 1**: backend reached "Application startup complete", frontend "Ready in 1252ms". Confirmed
  `GET /research/taxonomy` (200), `GET /research/strategies` (200), frontend `/` (200), frontend
  `/structure` shell (200) — deliberately did NOT hit `/research/edge-report` on this
  standard-port/real-corpus instance.
- **Stopped**: SIGTERM to `dev.sh`'s own tracked PIDs, then pattern/PID-targeted `kill -9` for the
  `next-server` grandchild (the documented gap above) after confirming via `/proc/<pid>/cwd` it was
  this project's frontend, not another project's. Confirmed both ports free.
- **Run 2**: started cleanly on the SAME ports (`8301`/`3301`) — no "address already in use"
  conflict. Confirmed "Ready in 1245ms".
- **Final cleanup**: stopped run 2 the same way; confirmed ports `8301`, `3301`, and my scratch
  verification port `18455` all free; confirmed an unrelated concurrently-running project's
  `next-server` process (a different repo entirely, sharing this machine) was never touched.

## Frontend

Verify-only, per the plan — zero frontend files changed (`git status` confirms no
`apps/frontend/**` diff). See `docs/handoffs/goal-tradable_wall-iter-10-frontend.md`.
