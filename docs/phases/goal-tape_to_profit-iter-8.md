# Goal Iteration 8 — J-09 baseline-edge report: rank the frozen champion's simulated hold-out edge per dataset, honestly

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets, no recommendation to execute. The ONLY permitted "fill" is the offline backtester's simulated fill computed against recorded historical tape, clearly labeled simulated and sent nowhere. *(critical)*
  - **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out basis, and its null baseline — and MUST never be presented as expected live results, an edge claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
  - **Default engine outputs are frozen.** Indicator evolution is additive and versioned only: candidate profiles may add feature keys or alternate thresholds, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, and no enhancement may mutate an archived-era behavior to pass. *(critical)*
  - **No train-only promotion.** Nothing becomes the champion, a proposed journey, or a claimed improvement on the strength of train data alone: hold-out survival (net R AND net $, with the configured minimum n) is the only promotion gate; overfit results are labeled overfit. *(critical)*
  - **No ML, no online tuning.** Candidate search is bounded, config-enumerated, offline, and deterministic; no fitted models, no optimizer loops inside the engine, no thresholds that move at runtime.
  - **No fabricated data — honest failure states.** No synthesized trades, quotes, fills, datasets, or PnL to force a green journey; every failure mode (backend down, corrupt dataset, empty window, missing credentials, insufficient n) surfaces an explicit, distinct state. *(critical)*
  - **Single source of truth.** Every canonical value in the Data Contract is computed once and read verbatim by every surface — REST, WebSocket, UI, markdown reports, and MCP. A second computation path or a diverging number across surfaces is a defect. *(critical)*
  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*
  - **Persistence stays scoped.** SQLite holds research records (now including backtests and the PnL ledger); the dataset store holds explicitly recorded historical tape for research replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a PnL-ledger acceptance criterion, keep the default profile byte-identical, and include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Deliver `python -m app.research.edge_report --out <path>` — a strictly read-only, deterministic baseline-edge report that measures the frozen `v1/default` champion across every registered dataset, ranks its simulated hold-out edge per dataset, flags each dataset that clears a positive hold-out edge at n ≥ the configured minimum while beating its own null baseline, and states "no positive-edge dataset" honestly when none qualify — so the operator can see whether the tape read carries measurable simulated edge across a diverse library.

## BACKGROUND

J-01–J-08 are all `passing` and the iter-7 verdict was GOAL_ACHIEVED — but that verdict covered only those eight journeys. `docs/goal.md` now carries a ninth human-authored Must-have, **J-09** (presented verbatim in this iteration's goal slice; absent from `journey-history.json`), which makes the operator's real-scale measurement a first-class journey. Per the priority rubric there is no regression and the last coherence verdict was COHERENCE-PASS, so J-09 is the sole and correct target: it is the only non-passing Must-have, it is not evaluator-marked human-blocked (see below), and it closes the era.

**Why full depth (cite triggers):** J-09 requires new tests well beyond browser smoke — determinism / byte-identical re-runs, pure-render equality of every displayed value to its `GET /research/backtests/{id}` aggregate, the positive-edge flag proven BOTH ways with the minimum-n controlled, the honest empty-finding exit-0 path, the missing-credentials state, and a fresh default-engine equivalence check. It is also the era's goal-closing iteration touching FOUR critical anti-goals (single source of truth, no profit claims, default frozen, no fabricated data), so it warrants the full 11-step pipeline — exactly the J-07 precedent (the prior goal-closer, dispatched full).

**Why this is NOT human-blocked (evaluator read this carefully).** J-09's headline says it "requires Alpaca credentials to record a real-scale library," but its CODE acceptance is 100% keyless-verifiable, and the journey's own parenthetical says so: *"(Credentialed operator data; the record and backtest capabilities are keyless-tested by J-02/J-03.)"* The record + backtest capabilities are already passing keyless (J-02/J-03); the ONLY new deliverable is the **baseline-edge report machinery**, which reads already-stored backtest aggregates and is fully exercisable on the committed fixture pair plus keyless SIM-recorded datasets. The real ≥3-symbol × ≥2-regime library "only enlarges the data — changes no behavior" (goal's own words) and is the operator's action, out of scope here (see OUT OF SCOPE). This iteration builds and verifies the report; the operator runs the real recording when credentialed.

**Lessons applied (from `lessons.md`):** iter-2 (machine-surface journeys get no golden replay — route regression through the backend suite; Chrome-MCP in-page `fetch()` for browser-originated checks); iter-3 (`/tmp` tmpfs per-user quota pins large-suite/browser lanes — check `du -sh /tmp/pytest-of-dennis-chan` and use `TMPDIR`/`--basetemp` off tmpfs before diagnosing "flaky"); iter-4 (the committed fixture pair arms **n=1 per split, < min 5** — any sample-size gate must be controlled BOTH ways in tests); iter-6 (the founding PnL row's `config_fingerprint 4d665603569b9dbf` is the sharpest default-frozen cross-check); iter-7 (a backend-only `full` iteration SKIPS the browser/replay lane — substitute each required journey's real acceptance mechanism, and do NOT let QA over-claim "golden replay" when none ran).

## IN SCOPE

### Backend
- [ ] New module `apps/backend/app/research/edge_report.py` exposing `run_edge_report(store, dataset_store, config) -> dict` + a `python -m app.research.edge_report --out <path>` CLI, modeled on `app/research/pnl_scan.py` (its structural template — reuse its disciplines, do not fork them).
- [ ] Read the CURRENT champion verbatim via `store.get_champion_pointer()` (row 33) — the report measures whatever the persisted pointer says (today `v1`/`default`); it never hardcodes an id.
- [ ] For every registered dataset (train AND hold-out, kept in **separate, never-pooled** sections), run the champion's backtest through the EXISTING `BacktestJobManager.create` + `run_sync` — the ONE computation path (exactly as `pnl_scan`/`pnl_baseline` do) — and read the persisted row-31 `aggregates` **verbatim** (`net_r`, `net_usd`, `n`, and the seeded null baseline). No second R/$/edge computation anywhere.
- [ ] Rank each split's datasets by hold-out edge with a deterministic tie-break (e.g. by `dataset_id`), so ordering is reproducible.
- [ ] Flag a dataset positive-edge ONLY when its hold-out `net_r > 0` AND `net_usd > 0` AND `n >= <configured minimum>` AND it beats its own null baseline; otherwise unflagged. Emit an explicit `"no positive-edge dataset"` finding (exit 0) when none qualify. The minimum MUST come from config (no magic number) — reuse the semantically-apt existing `Config.pnl_min_sample_size` unless a distinct honesty semantic is justified in the handoff (see NOTES).
- [ ] Attach to EVERY dollar figure its R counterpart, its n, its null baseline, and the ONE `REGISTER` string (import from `app/research/backtests.py`, as `pnl_scan`/`pnl_ledger` do) — never re-declare it.
- [ ] Deterministic `--out` render (sorted-key JSON, `pnl_scan._render_report` precedent): STRIP every per-run-random field (fresh backtest-report ids, wall-clock) before writing, so two independent fresh-state runs of an identical scenario produce byte-identical bytes.
- [ ] Honest failure states, reusing the `pnl_scan.ScanError` pattern: a dataset failing integrity verification, or a backtest ending non-`done`, aborts with an explicit error and NOTHING written; the existing missing-credentials 503 (`routes.py` real-data-record path) is the surfaced state when a real-feed record is attempted without keys — never synthesized data.
- [ ] Grep-style guard test proving the module introduces NO broker/order/account/execution code and does NOT call `set_champion_pointer` or `append_validation_row` (the edge report promotes/appends nothing).

### Frontend (if applicable)
- None. J-09 is a machine-surface CLI report (Frontend Present: no). No page, panel, nav, or `/meta/ui-routes` change.

### New user-facing capability
The operator can run `python -m app.research.edge_report --out report.json` and get a deterministic, honest ranking of the frozen champion's simulated hold-out edge across every registered dataset — with a clear "no positive-edge dataset" verdict when the read shows no measurable edge.

### New information displayed
The baseline-edge report artifact (Data Contract row 37): per-dataset champion `net_r`/`net_usd`/`n` + null baseline, ranked by hold-out edge, with positive-edge flags and an explicit empty-finding line — every $ beside its R, n, null baseline, and the simulated-results register.

### New user actions
One new CLI invocation: `python -m app.research.edge_report --out <path>`. No UI actions.

### UI surface changes
None. No new pages, panels, or nav entries; `NavBar.tsx`, the `/performance` page, and `/meta/ui-routes` stay zero-diff.

### Product surface delta
The product gains its first cross-dataset *measurement* view of the champion: not "is candidate X better than the champion" (that is J-07's sweep) but "does the frozen champion itself carry positive simulated hold-out edge, per dataset, across a library" — the operator-facing answer to the era's founding question, delivered read-only and caveated.

### Blueprint conformance
Lives on the existing **Machine surface** (no nav home), registered this iteration in `blueprint.md` alongside `pnl_scan` and MCP. No Information-Architecture nav-skeleton change (purely additive machine-surface entry) → no re-approval requested.

### Data-contract additions
- **Row 37 — Baseline-edge report** (registered in `blueprint.md` this iteration): computing module = `app.research.edge_report` (single owner; pure render of row-31 `aggregates` read verbatim via the one `BacktestJobManager` runner — no second computation path); served by = the `--out` report file (machine-readable artifact; no REST endpoint, no MCP tool). It introduces NO new numeric primitive — every value is row 31 read verbatim; the new artifact is the ranked, flagged report itself (analogous to row 36 reading row 31).

## OUT OF SCOPE

- **Recording the real ≥3-symbol × ≥2-session-regime × ≥2-hold-out-window Alpaca library** (J-09 step 1's credentialed data). That is an operator action requiring Alpaca credentials; it "only enlarges the data — changes no behavior," and its record + backtest capabilities are already keyless-proven by J-02/J-03. This iteration builds and verifies the report machinery keyless; the operator runs the real recording when credentialed.
- **No new REST endpoint** — the goal's API surface adds none for J-09; the report is a machine-surface CLI artifact only.
- **No new MCP tool** — MCP stays zero-diff.
- **No `/performance` page change, no committed markdown render** — future polish only; not required by J-09's acceptance.
- **No mutation of the champion pointer, PnL ledger, datasets, profiles, or any engine default** — the edge report is strictly read-only. The ONLY writes are the standard row-31 backtest rows the existing runner persists and the `--out` file.
- No change to the strategy grammar, fee/slippage/notional model, or any threshold — all values come from existing config.

## DEFINITION OF DONE

- [ ] Target journey **J-09** is marked `passing` by the goal-evaluator on keyless evidence (committed fixtures + keyless SIM-recorded datasets).
- [ ] `python -m app.research.edge_report --out <p>` writes a report that, for every registered dataset, shows the champion's `net_r` AND `net_usd` AND `n`, its seeded null baseline, and the `REGISTER` string, with train and hold-out in **separate, never-pooled** sections.
- [ ] A test asserts every displayed R/$/n value equals its `GET /research/backtests/{id}` aggregate byte-for-byte (pure-render equality — no second computation path).
- [ ] On the committed fixture pair (n=1 per split < min) the report emits the explicit `"no positive-edge dataset"` finding and exits 0.
- [ ] A test with the minimum-n controlled so a hold-out dataset clears `net_r>0 ∧ net_usd>0 ∧ n≥min ∧ beats-null` yields exactly one flagged positive-edge dataset (positive-edge flag proven BOTH ways).
- [ ] Two independent fresh-state runs of an identical scenario produce byte-identical `--out` files (per-run-random ids / wall-clock stripped).
- [ ] A real-feed record attempted without Alpaca credentials surfaces the EXISTING explicit 503 unavailable state — no synthesized data (test).
- [ ] A dataset failing integrity verification, or a backtest ending non-`done`, aborts with an explicit error and NOTHING written to `--out` (test).
- [ ] Grep-style guard: the new module contains no broker/order/account/execution code and never calls `set_champion_pointer` or `append_validation_row`; `test_no_execution_path.py` still 4/4.
- [ ] `default`-engine byte-equivalence test green AND the founding PnL row's `config_fingerprint` still reads `4d665603569b9dbf`.
- [ ] Required-still-passing journeys J-01–J-08 remain green (full backend suite ≥ the iter-6 baseline of 1004 passing; observer-equivalence 7/7; each journey's test module spot-run). Browser/replay lane is SKIPPED (backend-only) — verify each browser journey via its real acceptance mechanism, not golden replay (iter-7 lesson).
- [ ] No anti-goal violation introduced (`git diff` shows zero change under `apps/frontend/`, `apps/backend/app/mcp/`, and `docs/goal.md`).
- [ ] Unit/integration tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit-iter-8-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none. J-09 is a machine-surface CLI report (no page); browser/replay lane SKIPPED (iter-2 + iter-7 lessons). The required-still-passing browser journeys are re-verified via their real acceptance mechanisms — J-08 via observer-equivalence 7/7 (its sentinel) + `apps/frontend/` zero-diff; J-05 via `test_profiles_api.py` through the real HTTP route + `/performance` page zero-diff; J-01 via MCP zero-diff + proxied-endpoint check — NOT via golden replay (do not let QA over-claim replay that did not run).
- **Unit/integration (`apps/backend/tests/test_edge_report.py` + existing modules):**
  - pure-render equality: each displayed R/$/n equals the stored `GET /research/backtests/{id}` aggregate exactly.
  - train/hold-out kept separate, never pooled or averaged together.
  - ranking order deterministic with a stable tie-break.
  - positive-edge flag BOTH ways: n<min (fixtures) ⇒ unflagged + explicit "no positive-edge dataset" at exit 0; minimum-n controlled so a qualifying dataset ⇒ exactly one flag.
  - byte-identical re-runs across two fresh-state invocations.
  - `REGISTER` string present beside every $ figure; determinism under the fixed config-owned null-baseline seed.
  - default-engine byte-equivalence stays green; founding-row `config_fingerprint` unchanged (`4d665603569b9dbf`).
  - no-execution grep guard (no broker/order/fill-execution; no `set_champion_pointer`/`append_validation_row` call).
- **Error cases (must be rejected/handled explicitly, nothing written):**
  - corrupt / integrity-failing dataset ⇒ explicit error, no `--out`.
  - backtest ending non-`done` ⇒ explicit error, no `--out`.
  - real-feed record without Alpaca credentials ⇒ existing 503 "real-data provider unavailable," never synthesized data.
  - empty registry (no datasets) ⇒ honest empty report, exit 0 (no fabricated edge).
- **Environment:** before the large suite / any browser lane, check `du -sh /tmp/pytest-of-dennis-chan` against the per-user tmpfs quota and route pytest `--basetemp`/`TMPDIR` off tmpfs if pinned (iter-3 lesson) — otherwise the suite and equivalence runs go flaky for reasons unrelated to J-09.

## NOTES

- **Template, not fork.** `app/research/pnl_scan.py` already implements every discipline J-09 needs — champion-pointer read, the one `BacktestJobManager` computation path, verbatim `aggregates` read, `_measurement`, sorted-key deterministic render, id-stripping for byte-identical re-runs, split separation, and the `ScanError` honest-failure pattern. Build `edge_report.py` in that image; the KEY difference is that edge_report is **strictly read-only** — it measures the champion and promotes/appends NOTHING (no `_promote`, no ledger write, no pointer move). This makes the "no train-only promotion" anti-goal satisfied by construction.
- **Config minimum-n field.** J-09's positive-edge flag is a *display/measurement* gate (not a promotion gate), so `Config.pnl_min_sample_size` (=5, the existing "insufficient sample" floor) is the semantically-apt field. Do NOT add a new min-n config field unless a distinct honesty semantic is justified in the handoff — the coherence-auditor will ask why a third minimum exists (cf. the `promotion_min_sample_size` justification precedent at `config.py:996-1019`).
- **Honesty framing is load-bearing.** "Positive-edge" is a caveated *measurement of the past*, never an edge claim or a reason to trade (anti-goal 2). Keep the report's language measurement-framed; the flag means "cleared the disclosed hold-out threshold on this dataset," not "will be profitable."
- **Evaluator guidance.** Score J-09 on its keyless CODE acceptance (report machinery on the committed fixtures + keyless SIM datasets). The real ≥3-symbol diverse library is the operator's credentialed data-enlargement action (OUT OF SCOPE) — do not block J-09 on credentials; the journey is deliberately structured to be keyless-verifiable at the code level, and the record/backtest legs it depends on are already `passing` (J-02/J-03).
- **Post-J-09 the era is complete** (J-01–J-09) — a passing J-09 is a GOAL_ACHIEVED candidate for the evaluator to weigh; per the archived memory, the proposer previously dry-stopped pending operator real-scale data, which J-09 now makes a first-class, keyless-testable journey.
- **Non-blocking iter-7 polish carried forward** (do not gate J-09, address only if touched): wrap `store.set_champion_pointer` in `_promote` in an explicit error type (review #2 / audit B2); remove the unused `import time` in `store.py:36` (audit T1). These live in `pnl_scan`/`store`, not the new module.
