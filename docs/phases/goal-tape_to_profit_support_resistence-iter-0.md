# Goal Iteration 0 — Baseline: verify every structure-and-tape journey against current state

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit_support_resistence
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07
- **Required-still-passing journeys:** (none — baseline establishes the passing set)
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

Establish the era-4 baseline: run all seven structure-and-tape Must-have journeys (J-01–J-07) against the current codebase — with **no code changes** — so the evaluator can record which already pass, which fail, and which are partial.

## BACKGROUND

This is a **baseline assessment, not a feature delivery** (iteration 0 of the structure-and-tape era). Its value comes entirely from the browser-QA / verification step running every journey against the frozen era-3 foundation; the developer step is a no-op. Codebase inspection shows the era-3 foundation is intact (research router mounted; `/research/{datasets,backtests,pnl/ledger,profiles,studies}` present; strategy `v1` in `Config.strategy_definition(STRATEGY_V1_ID)`; `pnl_scan`/`edge_report` CLIs present; MCP server present) while **none** of the era-4 machinery exists yet — no bar store, no `/research/bars*` / `/research/levels` / `/research/strategies` endpoints, no S/R or confluence module, no `structure_tape` strategy (the strategy registry currently refuses any id but `v1` with 422), and no `fetch_bars`/`RawBar` on the Alpaca adapter seam. The expected shape of this baseline is therefore J-07 (regression sentinel) passing on the untouched foundation and J-01–J-06 failing/absent — but this spec asserts nothing; the goal-evaluator makes those calls from the verification evidence. Depth is **lean** per the baseline-mode rule (no code path is exercised, so the full 11-step pipeline is unnecessary; the verify pass suffices). `lessons.md` is empty (first iteration) — no prior lesson applies.

## IN SCOPE

### Backend
- [ ] None — this is a verify-only baseline. No source files are created or modified.

### Frontend (if applicable)
- [ ] None — era 4 adds machine surfaces only; the nav skeleton is unchanged (`Frontend Present: no`).

### New user-facing capability
None — baseline assessment only.

### New information displayed
None — baseline assessment only.

### New user actions
None.

### UI surface changes
None. (Verification includes a browser spot-check of the unchanged `/`, `/journal`, `/studies`, `/performance` surfaces for the J-07 regression sentinel.)

### Product surface delta
None. This iteration records the starting line; it changes no product behaviour.

### Blueprint conformance
No new surfaces. Verification exercises the existing Information Architecture (Cockpit · Journal · Studies · Performance) and the era-3 `/research/*` machine surface exactly as registered in `runs/goal-session-tape_to_profit_support_resistence/state/blueprint.md`.

### Data-contract additions
None. The era-4 Data Contract rows 38–43 (bar series; S/R levels + A/B/C confluence classes; strategy registry + champion pointer; `structure_tape` definition; per-class PnL breakdown; named-strategy comparison report) are drafted in the blueprint for future iterations but introduce **no** value in this iteration.

## OUT OF SCOPE

- Any implementation of J-01–J-06 (bars, levels, confluence classes, `structure_tape`, class-scaled risk, strategy comparison) — deferred to subsequent iterations.
- Any change to the era-1–3 foundation (tape engine, `default` profile, `v1` strategy, datasets, backtests, PnL ledger, sweep, edge report, MCP tool set).
- Any credentialed Alpaca bar fetch — real multi-timeframe bars are a later credentialed operator action; baseline runs keyless.
- Editing `docs/goal.md`, the Anti-goals section, or the AUTO:journeys marker block.

## DEFINITION OF DONE

- [ ] Every Must-have journey (J-01, J-02, J-03, J-04, J-05, J-06, J-07) is verified against the current codebase and its pass/fail/partial result is recorded by the goal-evaluator in `journey-history.json`.
- [ ] The verification evidence distinguishes "already implemented" (foundation intact) from "yet to build" (era-4 machinery absent) for each journey.
- [ ] No source file was created or modified (baseline is verify-only) — `git status` shows no code changes attributable to this iteration.
- [ ] No anti-goal violation is introduced (trivially satisfied — no code changes).

## TESTING REQUIREMENTS

- **Browser:** J-07 — spot-check the unchanged archived surfaces in the browser: sim cockpit flows on `/` (`SIM-BUYER` settles `buyer_control`, `SIM-SELLER` settles `seller_control`) and a render check of `/journal`, `/studies`, `/performance`.
- **Backend / verification (each journey, keyless against committed fixtures):**
  - J-01 — probe for a bar store + `GET /research/bars`; expect absent (no `/research/bars*` route, no bar-store module, no `fetch_bars`/`RawBar` on the adapter seam).
  - J-02 — probe for `GET /research/levels`; expect absent (no S/R module).
  - J-03 — probe for confluence zones + A/B/C classes on `/research/levels`; expect absent.
  - J-04 — probe `GET /research/strategies` and a `structure_tape` backtest; expect absent (registry serves `v1` only; unknown strategy id → 422).
  - J-05 — probe for a per-class PnL breakdown in a `structure_tape` backtest report; expect absent.
  - J-06 — probe `pnl_scan`/`edge_report` for named-strategy (`structure_tape` vs `v1`) evaluation; expect champion-only today.
  - J-07 — run the full backend suite and the engine equivalence test; confirm byte-identical `default` state/features/history and pinned `config_fingerprint`, and that `v1` + the champion pointer are untouched.
- **Error cases:** none to reject this iteration — no inputs are accepted (verify-only). Record honest "not-yet-implemented / route-absent" observations rather than fabricating any bar, level, class, trade, or PnL to make a journey appear green (Anti-goal: *No fabricated data — honest failure states*).

## NOTES

- **Baseline intent:** the goal-evaluator marks already-passing journeys (expected: J-07) as `already_passing` so later iterations skip them, and records J-01–J-06 as the era-4 build queue. This iteration asserts no verdict itself.
- **Natural dependency order for later iterations** (from `docs/goal.md`): J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding continuously. J-01 (multi-timeframe bar store + neutral `RawBar` on the adapter seam) is the unblocker — J-02–J-06 all consume its bar series — and is a data-model + provider-seam change, i.e. a risky iteration to isolate on its own next.
- **Blueprint drafted** at `runs/goal-session-tape_to_profit_support_resistence/state/blueprint.md` (era-4 rows 38–43 additive over the frozen foundation rows 1–37; nav skeleton unchanged). Auto-approved by default; the loop proceeds to iter-1 unless `--require-blueprint-approval` was passed.
- **Foundation is law:** J-07 is a permanent regression sentinel — every subsequent iteration keeps `default`/`v1` byte-identical and the era-3 measurement machine intact.
