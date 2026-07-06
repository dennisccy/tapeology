# Goal Iteration 6 — J-06: `structure_tape` measured honestly against the `v1` champion (named-strategy comparison + hold-out promotion gate)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit_support_resistence
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-07 (full regression — final journey; touches the champion pointer + PnL ledger)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets. The ONLY permitted "fill" is the offline backtester's simulated fill against recorded historical tape, clearly labelled simulated and sent nowhere; "position size" is a simulated notional, never a real order. *(critical)*
  - **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out basis, and its null baseline — never presented as expected live results, an edge claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
  - **The tape engine, `default` profile, and `v1` strategy are frozen.** Structure work is additive and versioned only: new bars/levels/classes and the `structure_tape` strategy may be added, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, `v1` stays byte-identical, and no enhancement may mutate an archived-era behaviour to pass. *(critical)*
  - **No train-only promotion.** Nothing becomes the champion on train data alone: hold-out survival (net R AND net $, at the configured minimum n) is the only promotion gate; overfit results are labelled overfit. *(critical)*
  - **No lookahead.** Levels and classes computed "as of" time T use only bars at or before T; a backtest may never see a level derived from data after the moment it is used. *(critical)*
  - **No ML, no online tuning.** S/R detection, confluence scoring, class thresholds, and class-based risk are bounded, config-enumerated, offline, and deterministic; no fitted models, no optimizer loops in the engine, no thresholds that move at runtime.
  - **No fabricated data — honest failure states.** No synthesized bars, levels, trades, fills, or PnL to force a green journey; every failure mode (backend down, corrupt file, empty window, missing credentials, rate-limited, no levels found, insufficient n) surfaces an explicit, distinct state. *(critical)*
  - **Single source of truth.** Every canonical value — bar series, levels, confluence classes, backtest aggregates, PnL rows — is computed once and read verbatim by every surface (REST, WebSocket, UI, MCP, reports). A second computation path or a diverging number across surfaces is a defect. *(critical)*
  - **No capital or portfolio management.** Class "position size" is a per-trade simulated notional only — no account, no equity curve, no compounding projection, no real position tracking. *(critical)*
  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*
  - **Persistence stays scoped.** SQLite holds research records; the bar and dataset stores hold explicitly recorded historical bars and tape for research replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a PnL-ledger acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

The era-3 sweep/edge-report path is generalized to measure a **named** strategy — so `structure_tape` is backtested across every registered dataset and compared to the `v1` champion on train AND hold-out — producing a per-split, per-dataset comparison report with a `survivor` flag that is true only on a hold-out win at n ≥ the configured minimum, labelling train-only wins overfit, promoting a genuine survivor by appending exactly one PnL-ledger row and moving the one champion pointer WITHOUT modifying `default`/`v1`/any engine default, and honestly reporting **no survivor at exit 0** on the committed fixtures.

## BACKGROUND

J-06 is the **sole remaining failing journey and the final Must-have** — the goal-completing iteration. It is fully unblocked: iter-5 (evaluator PASS, coherence PASS) shipped J-05 so `structure_tape` now carries its class-scaled stop/reward/size math, and Data-Contract row 43 (named-strategy comparison report) was registered forward at baseline. The generalization rides an existing seam I verified in the code: `pnl_scan.run_sweep` already compares a candidate against the champion per split with a `survivor`/`overfit`/`robustness` gate and a crash-safe two-write promotion — but it pins `strategy_id` to the champion's and varies only `profile`; `BacktestJobManager.create` already accepts any registered `strategy_id` (so `structure_tape` needs no new backtest path); and the champion is seeded `{v1, default}`, so "vs the champion" IS "vs v1". Depth is **full**: J-06 is a new canonical computation that touches the **champion pointer (rows 33/40) and the PnL ledger (row 32)** — frozen-foundation artifacts — through a promotion path, its load-bearing correctness is the critical **"no train-only promotion"** anti-goal (a thorough audit is warranted before any GOAL_ACHIEVED), and as the pre-completion gate it warrants a full regression. This matches the iter-5 evaluator's explicit next-step recommendation.

## IN SCOPE

### Backend
- [ ] **Generalize the ONE existing sweep (`apps/backend/app/research/pnl_scan.py`, Data-Contract row 43/36) to evaluate a NAMED candidate strategy** (`structure_tape`) against the current champion (`v1`/`default`) — reusing the SAME `BacktestJobManager.create` + `run_sync` computation path (never a second net R/$/edge computation) and the SAME `_dataset_rows`/`_split_summary`/`_is_positive`/`_promote` machinery. Add a **strategy axis** to the existing profile axis: the CLI gains a way to name the candidate strategy (e.g. `--strategy structure_tape`); the candidate backtest runs at `strategy_id=structure_tape`, `profile=default` and is compared to the champion at `strategy_id=v1`, `profile=default`. With NO named-strategy argument, the existing profile sweep (row 36 / J-07-adjacent) behaves **byte-identically** — backward compatible.
- [ ] The comparison report records, **per split (train, hold-out), never pooled**: `structure_tape`'s and `v1`'s net R AND net $, n, the per-dataset breakdown, and the candidate-minus-champion deltas — the SAME `_split_summary` shape generalized to the strategy axis.
- [ ] The **`survivor` flag reuses the existing gate verbatim**: true iff the summed hold-out delta is positive on BOTH net R AND net $ AND the summed hold-out candidate n ≥ `Config.promotion_min_sample_size` (**reuse the existing field — add NO new min-n field**). `overfit` = positive train AND NOT survivor. `robustness` (robust/speculative) unchanged.
- [ ] **Promotion of a genuine hold-out survivor reuses the existing crash-safe two-write order**: append EXACTLY ONE PnL-ledger row via `pnl_ledger.append_validation_row` (the ONE writer, row 32) THEN move the ONE row-33/40 champion pointer via `store.set_champion_pointer` — **generalized to move the strategy axis** (`strategy_id=structure_tape`, keeping `profile=default`) rather than the profile axis. The move is a **pointer write only**: it MUST NOT modify `default`, `v1`, or any engine default. The `enhancement_id` distinctly names the named-strategy promotion (e.g. `structure_tape-over-v1`).
- [ ] **Honest fixture outcome**: on the committed train/hold-out fixture pair, `structure_tape`'s hold-out n is below `promotion_min_sample_size` (2-timeframe bar fixture → mostly class-C, few trades — iter-3 lesson), so there is **no survivor** → no promotion → champion stays `{v1, default}` → the CLI exits 0 with an honest "no survivor" report. Nothing written to the ledger, pointer unmoved.
- [ ] **Determinism**: the comparison report carries no wall-clock / per-run-random field (the existing `_render_report` sorted-key discipline); two independent fresh-state runs on the fixtures produce **byte-identical** `--out` bytes.
- [ ] **Resolve audit item B1 by disclosure** (NOT by re-arming): the breakthrough arm is a static price-position test, not a fresh event-to-event cross — a sanctioned but loose anchor that inflates breakthrough-arm frequency. Because tightening it would perturb the frozen-ish J-04/J-05 arming (a second risky change in the goal-completing iteration), resolve B1 by **explicitly disclosing the loose-anchor caveat in the comparison report's provenance/assumptions** so the `structure_tape`-vs-`v1` edge number is not silently inflated. (Tightening the arm is allowed ONLY if it provably keeps J-04/J-05 byte-identical — otherwise disclose.)
- [ ] Extend `tests/test_no_execution_path.py`'s grep-guard to cover any new comparison/promotion code — no broker/order/routing/execution/paper-trading identifier is introduced; the champion move is a pointer write, not an order.
- [ ] **Prefer adding NO new `Config` field.** Reuse `promotion_min_sample_size`, `pnl_min_sample_size`, and `PROFILE_DEFAULT`. If a config-owned parameter is genuinely required, it MUST be added to the `config_fingerprint` `excluded` set (iter-1 lesson) so the pinned `default`/`v1` fingerprint `4d665603569b9dbf` does not move.

### Frontend (if applicable)
- None. This is a machine surface (CLI report + existing REST/MCP reads); `apps/frontend/` MUST NOT be touched (iter-0 lesson: a zero frontend diff is what keeps J-07's cockpit leg green without a new screenshot).

### New user-facing capability
An operator (or an agent, read-only via MCP) can run the sweep to measure whether `structure_tape` beats the `v1` champion on **held-out** data — and, only if it genuinely survives hold-out at n ≥ the minimum, promote it to champion with a full audit trail (one ledger row + a moved pointer). On the committed fixtures the honest answer is "no survivor," champion unmoved.

### New information displayed
A named-strategy comparison report (`structure_tape` vs `v1` per split: net R AND net $, n, per-dataset breakdown + deltas, `survivor`/`overfit`/`robustness`, `champion_before`/`champion_after`) written to the CLI `--out` file; and, only on a genuine promotion, one new row on the existing `GET /research/pnl/ledger` (row 32) plus a moved champion visible via the existing `GET /research/profiles` / `GET /research/strategies` (rows 33/40). On the fixtures: the report's honest "no survivor," champion `{v1, default}` unmoved.

### New user actions
None (CLI + read-only REST/MCP; no new buttons/forms/controls). The only "action" is invoking the generalized sweep CLI with the named strategy.

### UI surface changes
None (no nav/page change; blueprint Information Architecture unchanged — machine surface only).

### Product surface delta
The measurement machine — which in era 3 could only sweep candidate **profiles** at a fixed strategy — can now A/B a named **strategy** (`structure_tape`) against the champion (`v1`) on hold-out, under the same honesty guards and the same hold-out promotion gate. This is the era's final capability: it makes the founding question — *does the tape read become profitable when anchored to price structure?* — answerable honestly, with no thumb on the scale.

### Blueprint conformance
**No new surfaces.** The named-strategy comparison (row 43) lives at its already-registered canonical home — the CLI `pnl_scan`/`edge_report` `--out` report + the existing `GET /research/pnl/ledger` (row 32) + the one champion pointer (rows 33/40). Nav skeleton (Cockpit · Journal · Studies · Performance) unchanged; the report is a machine surface with no nav home, exactly as the blueprint lists it. No `blueprint.reapproval-requested` this iteration.

### Data-contract additions
**None new.** J-06 realizes **row 43** (Named-strategy comparison report), already registered at baseline in `blueprint.md`, whose owner (the SAME row-36 `pnl_scan` / row-37 `edge_report` path, *generalized to a named strategy* — reusing the ONE `BacktestJobManager`, never a second R/$/edge computation) and serving surface (`--out` report file + row-32 PnL-ledger row + row-33/40 champion pointer) are unchanged. No new displayed value, no new computing module, no new serving endpoint → **no `blueprint.md` edit this iteration**. Any config field (if genuinely required) is a parameter of row 43's existing owner, not a new served value.

## OUT OF SCOPE

- A NEW comparison/promotion module or a NEW endpoint — the named-strategy comparison EXTENDS the existing `pnl_scan` (single owner of the promotion path); a second computer of net R/$/edge is a single-source-of-truth violation and a coherence FAIL.
- A SECOND champion pointer or a SECOND min-n field — reuse the ONE row-33/40 pointer and the existing `promotion_min_sample_size`.
- Any change to `v1`, the `default` profile, the tape engine, the live cockpit, or any engine default (all frozen; byte-identical; the promotion is a pointer move only).
- Tightening the breakthrough arm (audit B1) into a fresh event-to-event cross IF it would perturb J-04/J-05 arming — resolved by **disclosure** in the report provenance instead (see IN SCOPE; tightening allowed only if J-04/J-05 stay byte-identical).
- Any REAL promotion on the committed fixtures — n is below the minimum, so the honest outcome is no-survivor; the promotion PATH is exercised only by synthetic ≥-min-n fixtures in tests.
- A required generalization of `edge_report.py` — OPTIONAL and, if done, strictly read-only (no promotion). The survivor comparison + promotion IS the sweep (`pnl_scan`); the DoD does not depend on touching `edge_report`.
- Any new REST endpoint, nav, or page; any UI change; any real position/account/portfolio/equity/compounding concept (the comparison measures simulated PnL only).

## DEFINITION OF DONE

- [ ] **J-06 passes:** running the generalized sweep with the named `structure_tape` strategy produces a report recording, per split (train + hold-out), `structure_tape`-vs-`v1` net R AND net $, n, and a per-dataset breakdown, with a `survivor` flag true iff `structure_tape` beats the champion on **hold-out** net R AND net $ at n ≥ `promotion_min_sample_size` — verified by the J-06 acceptance suite (exit 0).
- [ ] **Overfit is labelled and never promoted:** a positive-train / failing-hold-out synthetic fixture yields `overfit=true`, `survivor=false`, and NO promotion (champion unmoved, no ledger row).
- [ ] **A genuine hold-out survivor promotes correctly:** a synthetic ≥-min-n survivor fixture appends EXACTLY ONE PnL-ledger row (row 32) THEN moves the ONE row-33/40 champion pointer to `strategy_id=structure_tape` — and `default`, `v1`, and every engine default are byte-identical after (`config_fingerprint()=='4d665603569b9dbf'` unmoved; `tests/test_profile_equivalence.py` green; engine equivalence green).
- [ ] **Honest fixture outcome:** on the committed fixtures (hold-out n below `promotion_min_sample_size`) the CLI reports "no survivor," champion stays `{v1, default}`, exits 0, and writes nothing to the ledger / moves no pointer.
- [ ] **Deterministic re-runs:** two independent fresh-state runs on the fixtures produce byte-identical `--out` bytes.
- [ ] **Single source of truth:** every backtest goes through the ONE `BacktestJobManager` (source-scan test — no second net R/$/edge computation); `store.set_champion_pointer` is still called from exactly one source file.
- [ ] **No live execution path:** extended `tests/test_no_execution_path.py` green over the comparison/promotion code (no broker/order/routing/execution/paper-trading identifier; the champion move is a pointer write).
- [ ] **Audit B1 resolved:** the breakthrough arm's loose-anchor assumption is explicitly disclosed in the comparison report's provenance/assumptions (or tightened only if J-04/J-05 stay byte-identical).
- [ ] **Backward compatibility:** the existing profile sweep (no named strategy) behaves byte-identically (row 36 unchanged).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-07 remain green (deterministic replay + full backend suite).
- [ ] No anti-goal violation introduced (scan-report CLEAN; coherence PASS).
- [ ] Unit tests pass; full backend suite green; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-dev.md`, listing ALL files changed (including any doc edits).

## TESTING REQUIREMENTS

- **Browser:** none required (machine surface; Frontend Present: no). J-07's cockpit/frozen-surface leg is covered by deterministic replay + engine equivalence because `apps/frontend/` is untouched (iter-0 lesson: zero frontend diff → no new screenshot owed).
- **Unit/integration (this IS the acceptance for a machine surface):**
  - **Named-strategy comparison shape:** per split, `structure_tape` and `v1` net R AND net $, n, per-dataset breakdown + deltas; train and hold-out never pooled.
  - **Survivor gate on the strategy axis:** (a) a below-min-n hold-out win is NOT a survivor; (b) an at/above-min-n positive hold-out win IS a survivor — using synthetic fixtures (a controlled ≥-min-n survivor + a below-min-n case), mirroring the existing `tests/test_pnl_scan.py` min-n tests.
  - **Overfit:** positive train + failing hold-out → labelled overfit, never promoted.
  - **Promotion correctness + crash safety:** exactly ONE ledger row appended THEN the pointer moved to `strategy_id=structure_tape`; a mid-promotion re-run hits the existing `DuplicateEnhancementError` → explicit `ScanError` (no silent double-append, no orphan).
  - **Frozen foundation AFTER a promotion:** fingerprint `4d665603569b9dbf` unmoved, `v1`/`default` byte-identical, engine equivalence green — a promotion moves the pointer only, mutating no strategy/profile/engine default.
  - **Fixture honesty:** the committed train/hold-out fixture pair yields no survivor, champion unmoved, exit 0.
  - **Determinism:** byte-identical `--out` re-run on the fixtures.
  - **Backward compatibility:** the existing profile sweep (no named strategy) reproduces byte-identically.
  - **Single-source scan:** champion-pointer setter called from exactly one source file; no second net R/$/edge computation path.
- **Error cases / honest states:**
  - Corrupt dataset / non-`done` backtest → explicit `ScanError`, nothing written, nothing promoted.
  - Unknown candidate strategy id → explicit refusal (never a coerced/fabricated comparison).
  - More than one train or one hold-out dataset registered → promotion explicitly skipped with an honest note (existing `append_validation_row` shape), the comparison still fully reported.
  - Grep-guard: no broker/order/routing/execution/paper-trading identifier introduced.

## NOTES

- **Depth = full** justified by (Picking-depth triggers): J-06 touches the data model / sensitive foundation artifacts — the **champion pointer (rows 33/40) and PnL ledger (row 32)** — via a promotion path; its load-bearing correctness is the critical **"no train-only promotion"** anti-goal (needs a full audit); and as the **goal-completing** journey a full regression + audit is warranted before any GOAL_ACHIEVED. Prior verdict was CONTINUE (not ESCALATE); full is chosen by the data-model/champion-pointer trigger and matches the iter-5 evaluator's explicit recommendation.
- **Lessons applied (surface to developer / reviewer / evaluator):**
  - *iter-5:* (1) do NOT silently break `_class_scaled_invalidation`'s level-relative-vs-entry-relative fallback when re-backtesting `structure_tape` for the comparison; (2) the DoD's "per train/hold-out split" is satisfied by **dataset provenance** — one backtest = one dataset carrying one frozen `split` tag — so the cross-split comparison IS J-06 (comparing the train-summary vs hold-out-summary aggregates), NOT a second split axis inside a single backtest report. Don't over-build a two-axis breakdown.
  - *iter-4 audit B1:* the breakthrough arm is a static price-position test, not a fresh event-to-event cross — a sanctioned but loose anchor that inflates breakthrough-arm frequency and materially affects the `structure_tape`-vs-`v1` edge number → resolve by **explicit disclosure** in the report provenance (tighten only if J-04/J-05 stay byte-identical).
  - *iter-3:* the committed PG bar fixture holds only two timeframes (1h, 1d) → mostly class-C, few `structure_tape` trades → the fixture comparison honestly yields no survivor (n below the minimum). Class-A / above-min-n survivor cases MUST use **synthetic** fixtures, never the committed PG fixture.
  - *iter-1:* `config.py` is vendor-name-forbidden even in comments; ANY new `Config` field must join the `config_fingerprint` `excluded` set or the pinned `4d665603569b9dbf` moves and J-07 breaks — **prefer reusing** `promotion_min_sample_size` / `pnl_min_sample_size` / `PROFILE_DEFAULT` and adding none.
- The champion is seeded `{v1, default}` (`store.py::_ensure_champion_pointer_seeded`, idempotent — never overwrites a promoted pointer), so "`structure_tape` vs the champion" IS "`structure_tape` vs `v1`" on a fresh/foundation store. `v1` "loses money" on real tape (the era-3 finding), so a genuine hold-out win by `structure_tape` is precisely the era-4 hypothesis under honest test — with the fixtures honestly returning no survivor.
- **Doc-parity rider (minor):** update the README / relevant docs so the shipped named-strategy comparison capability and the honest "no survivor on the fixtures" finding are documented, and ensure the iter-5 incidental README note plus all iter-6 doc edits are listed in the dev handoff's Files Changed.
- **GOAL_ACHIEVED note:** J-06 is the FINAL Must-have; only the **evaluator** (not this planner, and only after the deterministic gates + two-key confirm) may declare GOAL_ACHIEVED. This spec marks no journey passing.
- **Target selection followed the rubric with no deviation:** no regressions (rule 1 N/A); iter-5 coherence PASS so no consolidation owed (rule 2 N/A); J-06 is the SOLE remaining failing journey — the goal-completing pick — carried alone as ONE risky change (rule 5 respected: B1 resolved by disclosure to avoid a second risky arming change in the same diff).
