# Goal Iteration 5 — J-05: class-scaled stop, reward, and simulated size (per-class PnL breakdown)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit_support_resistence
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-07
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

The `structure_tape` strategy sizes and stops each simulated entry by its arming level's A/B/C conviction class (A → ~1bp stop beyond the level, larger simulated notional, reward toward the next opposing level; B/C → wider stop, smaller size), and its backtest report exposes a per-class PnL breakdown (net R AND net $, n, per train/hold-out split) — all config-owned and caveated as simulated.

## BACKGROUND

J-05 is the sole remaining tractable failing journey in the strict dependency order (J-01→J-06); J-06 cannot honestly compare `structure_tape` to `v1` until `structure_tape` carries its class-scaled risk math, so J-05 unblocks J-06. Every prerequisite is in place: iter-4 (evaluator PASS, coherence PASS) shipped J-04 so each `structure_tape` trade already carries `trade['level']['class']` (A/B/C), and rows 41 (grammar) and 42 (per-class breakdown) were registered forward at baseline. Depth is **full** (matching the evaluator's iter-4 next-step recommendation and the J-02/J-03/J-04 shape): this is a new canonical computation (class-scaled risk math) that **splits the `_arm_trade`/`_close_trade`/`_synthetic_invalidation`/size arithmetic `structure_tape` currently inherits byte-identically from `v1`** — a regression surface on the frozen `v1`/`default` — and it introduces the critical "position size = simulated notional, transmits nothing" grep-guard (no-execution + no-capital anti-goals), so it needs new correctness tests beyond browser smoke and a full audit pass, not a lean cycle.

## IN SCOPE

### Backend
- [ ] Add config-owned, `structure_tape_*`-namespaced class-scaling fields to `Config` (research defaults, each with its rationale documented in `config.py` — NO numeric literal in `research/backtests.py`): (a) per-class **stop distance** (A ≈ 1bp beyond the level; B/C wider), (b) per-class **reward target** (R:R toward the next opposing level — a target-R multiple and/or the next-opposing-level rule, config-bounded), and (c) per-class **simulated size multiple** (better class → larger notional, applied over the existing `strategy_dollars_per_r`). No magic numbers; all A/B/C values enumerated in config.
- [ ] Add EVERY new class-scaling field to the `config_fingerprint` `excluded` set (beside the existing `structure_tape_*` exclusions at `config.py:1579-1581`), with the same rationale — read ONLY when `structure_tape` is selected, so their presence MUST NOT move the pinned `default`/`v1` fingerprint `4d665603569b9dbf`.
- [ ] Extend the `structure_tape` branch of `Config.strategy_definition` ONLY (it is evaluated before `v1`'s branch and returns first, so `v1`'s dict stays byte-for-byte identical) so its exits/size grammar declares the class-scaled stop, the reward target, and the simulated size — read BY NAME from the new config fields. `v1`'s returned grammar is unchanged.
- [ ] In `BacktestRunner`, apply the class-scaled stop, the reward-target exit, and the class-scaled size to `structure_tape` trades ONLY — gated on the arming `level`/class being present (`level is not None`) — so `v1` and the null-baseline paths stay byte-identical:
  - stop: class-scaled invalidation distance in `_arm_trade` (A ≈ 1bp beyond the level), still flowing R through the ONE shared `marks.r_basis` — never a second R formula.
  - reward: a NEW take-profit exit reason (R:R toward the next opposing level) added to `_exit_reason` for `structure_tape` trades only, inserted at a documented fixed precedence, and lookahead-free (the next opposing level comes from the same as-of `compute_levels` read).
  - size: class-scaled notional in `_close_trade` (`shares` derived from the class size multiple × `strategy_dollars_per_r`, `structure_tape` only; `v1`/null trades carry no `level` key → unchanged `shares`).
- [ ] Add the per-class PnL breakdown (row 42) to the backtest report: the SAME single `_aggregate`/runner computes net R AND net $, n, per train/hold-out split, per class A/B/C — computed ONCE, persisted, and served verbatim by the EXISTING `GET /research/backtests/{id}` (NO new endpoint) + MCP `backtests`. Each $ appears beside its R, n, split, null baseline, and the visible `REGISTER`; sub-minimum-n classes are labelled "insufficient sample"; a class with zero trades is honest-empty (n=0, `None` rate), never fabricated.
- [ ] Extend the existing `tests/test_no_execution_path.py` grep-guard to cover the sizing code: "position size" is a simulated notional that places / routes / transmits nothing — no broker/order/routing/execution/paper-trading identifier is introduced.

### Frontend (if applicable)
- None. This is a machine surface (REST + MCP + report); `apps/frontend/` MUST NOT be touched (iter-0 lesson: a zero frontend diff is what keeps J-07's cockpit leg green without a new screenshot).

### New user-facing capability
An operator (or an agent via MCP) can read, per A/B/C class, whether tighter-stop/larger-size A-class structure entries measure better than B/C entries — a class-resolved view of `structure_tape`'s simulated risk math, all as caveated simulated PnL.

### New information displayed
Per-class PnL breakdown (net R AND net $, n, per train/hold-out split, per A/B/C class) on the existing backtest report via `GET /research/backtests/{id}` + MCP `backtests`, each beside the "simulated — assumed fees/slippage — not indicative of live results" register; sub-minimum-n classes labelled "insufficient sample". The `structure_tape` grammar on `GET /research/strategies` now shows its class-scaled stop/reward/size parameters.

### New user actions
None (read-only machine surface; no new buttons/forms/controls).

### UI surface changes
None (no nav/page change; blueprint Information Architecture unchanged — machine surface only).

### Product surface delta
The research/MCP surface gains a class-resolved view of `structure_tape`'s simulated stop/reward/size and per-class PnL — the last data piece before J-06 can measure `structure_tape` against `v1` honestly.

### Blueprint conformance
No new surfaces. Per-class PnL (row 42) lives at its already-registered canonical home — `GET /research/backtests/{id}` + MCP `backtests` (the row-31 endpoint; no second endpoint). The class-scaled stop/reward/size grammar (row 41) is served by the already-registered `GET /research/strategies` + MCP `strategies`. Nav skeleton (Cockpit · Journal · Studies · Performance) unchanged.

### Data-contract additions
**None new.** J-05 realizes two rows already registered at baseline in `blueprint.md`:
- Row 41 — `structure_tape` strategy definition (class-scaled stop [A ≈ 1bp], reward target [R:R toward next opposing level], simulated notional [better class → larger]); computed by `Config.strategy_definition("structure_tape")`; served by `GET /research/strategies` + MCP `strategies`.
- Row 42 — Per-class PnL breakdown; computed by the ONE row-31 `BacktestJobManager`; served by `GET /research/backtests/{id}` + MCP `backtests`.

No new displayed value, no new computing module, no new serving endpoint → no `blueprint.md` edit and no `blueprint.reapproval-requested` this iteration. The new config fields are parameters of row 41's existing owner, not a new served value.

## OUT OF SCOPE

- J-06 (generalize the edge-report/sweep to a **named** strategy, `structure_tape` vs `v1`, and the hold-out promotion path) — the next journey; do NOT touch `research/pnl_scan.py`, `research/edge_report.py`, or the champion pointer.
- Any change to `v1`, the `default` profile, the tape engine, or the live cockpit (all frozen; byte-identical).
- Any new REST endpoint or nav/page — the per-class breakdown rides the existing `GET /research/backtests/{id}`.
- Any real position/account/portfolio/equity/compounding concept — "position size" is a per-trade simulated notional only.
- Tightening audit item B1 (the breakthrough arm is a static price-position test, not a fresh event-to-event cross) — carried forward as a disclosed limitation; it affects J-06's honest edge measurement, not J-05's sizing math.

## DEFINITION OF DONE

- [ ] J-05 passes: a `structure_tape` backtest report exposes per-class (A/B/C) net R AND net $, n, per train/hold-out split on `GET /research/backtests/{id}` and byte-identically via MCP `backtests`, each beside the `REGISTER`, sub-minimum-n classes labelled "insufficient sample" — verified by the J-05 acceptance suite (exit 0).
- [ ] Every stop distance, reward target, and size multiple is read from a named `Config` field (no inline numeric literal in `research/backtests.py`) — asserted by a "no magic number" test.
- [ ] `v1`/`default` stay byte-identical AFTER the shared-arithmetic split: `config_fingerprint()=='4d665603569b9dbf'` (every new field excluded), `tests/test_profile_equivalence.py` green, and the `v1` backtest trades reproduce byte-identically.
- [ ] "position size" places/routes/transmits nothing: extended `tests/test_no_execution_path.py` green (no broker/order/routing/execution/paper-trading identifier in the sizing/exit code).
- [ ] Deterministic re-runs: the per-class report reproduces byte-identically on re-run.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-07 remain green (deterministic replay + suites).
- [ ] No anti-goal violation introduced (scan-report CLEAN; coherence PASS).
- [ ] Unit tests pass; full backend suite green; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit_support_resistence-iter-5-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none required (machine surface; Frontend Present: no). J-07's cockpit/frozen-surface leg is covered by deterministic replay + engine equivalence because `apps/frontend/` is untouched (iter-0 lesson: zero frontend diff → no new screenshot owed).
- **Unit/integration (this is the acceptance for a machine surface):**
  - Per-class breakdown correctness: the A/B/C partition of the same `structure_tape` trade population sums to the strategy total (net R AND $, n) per split; the class dimension is computed once by the same runner (single-source scan — no second aggregation path).
  - Class-scaled stop: A-class invalidation ≈ 1bp beyond the level; B/C wider — asserted on the synthetic 3-timeframe `SYN-CONFLUENCE` fixture for the class-A case (iter-3 lesson: the committed PG bar fixture holds only 1h+1d → its honest real output is `[C,…,B]`, never class-A).
  - Class-scaled size: better class → larger notional/shares; the multiple is config-owned.
  - Reward-target exit: a take-profit exit fires toward the next opposing level in the documented fixed precedence and stays lookahead-free (as-of level read only).
  - `v1`/`default`/null byte-identity AFTER the split: fingerprint pinned, equivalence green, `v1`/null trade dicts byte-identical (no `level` key, unchanged `shares`/invalidation).
  - Determinism: byte-identical re-run of the per-class report; MCP `backtests` per-class JSON byte-identical to REST.
- **Error cases / honest states:**
  - Sub-minimum-n class → "insufficient sample" label (never a dishonest 0%).
  - A class with zero trades → honest empty (n=0, `None` rate), never fabricated.
  - Unknown `strategy_id` still 422; class-scaling never leaks into a `v1` or null backtest.
  - Grep-guard: no broker/order/routing/execution/paper-trading identifier introduced by the sizing/exit code.

## NOTES

- **Depth = full** justified by: new canonical computation (class-scaled risk math); it splits the `_arm_trade`/`_close_trade`/`_synthetic_invalidation`/`shares` arithmetic shared byte-identically with the frozen `v1`/`default` (regression surface → re-verify byte-identity + fingerprint AFTER the split); it introduces the critical "position size = simulated notional" grep-guard (no-execution + no-capital); and it needs correctness tests beyond browser smoke. Prior verdict was CONTINUE (not ESCALATE) — full is chosen by these triggers, matching J-02/J-03/J-04.
- **Lessons applied (surface to developer / reviewer / evaluator):**
  - *iter-1 / iter-4:* `config.py` is vendor-name-forbidden even in comments; EVERY new class-scaling field MUST join the `config_fingerprint` `excluded` set or the pinned `4d665603569b9dbf` moves and J-07 breaks. Gate all class-scaling on `level is not None` and re-verify `v1`/`default` byte-identity AFTER parameterizing the shared `_arm_trade`/`_close_trade`/`_synthetic_invalidation`/size math.
  - *iter-3:* the committed PG bar fixture stores only two timeframes (1h, 1d) → honest real output `[C,C,C,C,C,B]`, never class-A. Any class-A assertion (A ≈ 1bp stop, largest size) MUST use the synthetic 3-timeframe `SYN-CONFLUENCE` fixture, not the committed PG fixture.
  - *iter-4 audit B1 (carried forward, NOT fixed here):* the breakthrough arm is a static price-position test, not a fresh event-to-event cross — a sanctioned but loose anchor; it affects J-06's honest edge comparison, not J-05's sizing math.
- Coherence at iter-4 was PASS → no consolidation owed; this is clean forward feature work.
- Target selection followed the rubric with no deviation: J-05 is the single next failing journey in dependency order, it unblocks J-06, and it is one risky change carried alone (no bundling). This scope was driven by the iter-4 evaluator's explicit next-step recommendation.
