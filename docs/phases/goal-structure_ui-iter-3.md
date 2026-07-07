# Goal Iteration 3 — Structure: the honest `structure_tape`-vs-`v1` comparison (J-03)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** structure_ui
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-02, J-04
- **Anti-goal reminders** (verbatim from `docs/goal.md`):

  Immutable rails:
  1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. (See the forming-bar rule in card 6.4.) *(critical)*
  6. **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  10. **Persistence stays scoped** — no ambient recording of live streams; recording is an explicit, logged act. *(critical)*

  Interlude-specific:
  - **The Structure UI recomputes nothing.** Every displayed value — level price/timeframe/type, zone class, net R, net $, n, `insufficient_sample`, the champion — is read verbatim from its canonical endpoint. No client-side grading, PnL math, aggregation, or champion resolution. A number that diverges from its API/MCP payload is a defect (trap T10). *(critical)*
  - **No new backend computation or endpoint.** This interlude consumes the existing canonical endpoints; the only backend edit is the additive `/structure` entry in the `meta.py` route registry (the nav owner). It creates no second implementation of any value. *(critical)*
  - **Honest UI states only.** No fabricated chart, level, zone, trade, fill, or PnL to force a green journey; every failure mode (no bar series, no levels, no zones, insufficient n, missing credentials, backend unreachable) surfaces an explicit, distinct state. *(critical)*
  - **The UI never promotes.** The comparison view runs backtests and diffs their reports; it MUST NOT move the champion pointer or write the PnL ledger — promotion remains the sweep's hold-out act. *(critical)*
  - **No vocabulary drift** (trap T9). No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.

## GOAL

Inside the app at `/structure`, the user can choose a registered dataset, run `structure_tape` and the champion `v1` over it as an offline research job, and read the two strategies' aggregates and per-class A/B/C breakdown side by side — seeing, on the committed keyless reference dataset, `structure_tape` honestly labelled a non-survivor with insufficient n and the champion unchanged at `v1`/`default`.

## BACKGROUND

J-03 is the sole remaining `failing` journey; J-01, J-02, and J-04 are green. Building the on-screen `structure_tape`-vs-`v1` comparison as a third section of the existing `/structure` page makes all four Must-have journeys browser-visible → a GOAL_ACHIEVED candidate for the evaluator.

**Depth = full** (per "Picking depth" triggers, cited): (a) the iter-2 evaluator explicitly recommended `full` for iter-3; (b) J-03 is the single riskiest journey — it orchestrates two backtest jobs (dual POST + poll to `done`) and renders simulated PnL, so it exercises the most anti-goal rails at once (no-execution, no-profit-claims + the visible register, insufficient-sample labelling, champion-moved-never + no-promotion, and T10 single-source). These warrant the audit + coherence + ux-regression + closure lanes that a lean cycle omits. This is *not* ESCALATE-driven (the iter-2 verdict was CONTINUE) and it carries exactly one risky journey — no second risky change is bundled in.

**Verified against the codebase, the backend already fully supports J-03 with zero new work:** `POST /research/backtests`, `GET /research/backtests/{backtest_id}`, `GET /research/datasets`, and `GET /research/pnl/ledger` all exist (`apps/backend/app/research/routes.py:1670 / 1729 / 1499 / 1769`) and every backtest report payload already carries the aggregates, the `aggregates_by_class` breakdown, `insufficient_sample`, and the `register` string. So this is a **frontend-only** iteration — honoring the "no new backend computation or endpoint" rail. The `/structure` nav entry shipped in iter-1; `apps/backend/` must stay an empty diff.

**Load-bearing single-source detail (T10):** the simulated register is NOT a frontend literal. `apps/frontend/app/performance/page.tsx:28` documents "the simulated register is the API payload's `register` string — no frontend copy of it exists," and the served string is the fuller `REGISTER = "simulated — assumed fees/slippage — not indicative of live results"` (`apps/backend/app/research/backtests.py:142`, imported by `pnl_ledger.py`). Hardcoding the goal-doc's abbreviated "simulated — not indicative of live results" would *diverge from the payload* — a coherence-fail plus vocabulary-drift risk. J-03 MUST render `register` from the payload verbatim, exactly like `/performance`'s `pnl-register`.

Applicable lessons (from `runs/goal-session-structure_ui/state/lessons.md`): **iter-0** — a J-01/J-02/J-03 journey with no populated `reports/qa/goal-structure_ui-iter-3-evidence/` screenshot is `unknown`, not `passing`; do not accept "comparison renders" on prose. **iter-1(b)** — if the auditor fixes a browser-QA FAIL in place, J-03 stays `partial` until an *independent* browser-QA re-run confirms. **iter-1(a)** — any loading/empty overlay placed over a `lightweight-charts` canvas needs an explicit z-index above the canvases (the comparison is tabular, but adding a section must not re-occlude J-01's chart). **iter-2** — at eval time the code is uncommitted; scope the diff with `git diff <snapshot> -- <path>` / `git status --short`, never a two-dot `snapshot..HEAD` range.

## IN SCOPE

### Backend
- [ ] **None.** J-03 is fully served by the existing frozen backend (endpoints + payloads verified above). `apps/backend/` diff MUST remain empty; `config_fingerprint` stays `4d665603569b9dbf`.

### Frontend
- [ ] Add three verbatim-read helpers to `apps/frontend/lib/api.ts` (mirror `fetchStrategies`' discipline — return `null`/error honestly on any non-200 or unreachable backend, never a fabricated payload): `fetchDatasets()` → `GET /research/datasets`; `createBacktest({ dataset_id, strategy_id, profile })` → `POST /research/backtests`; `fetchBacktest(id)` → `GET /research/backtests/{backtest_id}`.
- [ ] Add matching TS types to `apps/frontend/lib/types.ts` for the datasets list, the backtest request, and the backtest payload (`status`, aggregates `n`/`net_r`/`net_usd`/`win_rate`/`max_drawdown_r`, `aggregates_by_class` with `insufficient_sample`, and `register`) — typed to the served shape, with **no** client-derived fields.
- [ ] Add a third **Comparison** section to `apps/frontend/app/structure/page.tsx` (below the Registry section), `aria-label="structure_tape vs v1 comparison"`: a dataset selector (from `fetchDatasets()`), a "Run comparison" button that POSTs two backtests — `v1` and `structure_tape`, both at `profile=default`, on the chosen dataset — and a job/poll loop reusing the Studies pattern (`setInterval ~700ms`; poll `GET /research/backtests/{id}` while `queued`/`running`; stop on terminal) until both are `done`.
- [ ] Render side-by-side aggregates (`n`, net R, net $, `win_rate`, `max_drawdown_r`) plus the per-class **A/B/C** table from `aggregates_by_class`, every value `String()`/verbatim from `GET /research/backtests/{id}` — **no** client recompute of R, $, win-rate, or the class partition.
- [ ] Render `insufficient_sample` verbatim (overall and per-class) wherever the payload flags n below the minimum (mirror `StudyResultsView`'s insufficient-sample label; keep `win_rate: null` shown as an honest null, never `0`).
- [ ] Render the simulated register **verbatim from the payload's `register` string** (never a hardcoded literal), styled like `/performance`'s `pnl-register`.
- [ ] Render the champion pointer (badged `v1`/`default`, read-only) and the founding baseline row from `GET /research/pnl/ledger` beside the comparison — the champion is moved **never**; there is **no** promotion control.
- [ ] Honest, distinct states for the Comparison section: no datasets registered (empty), a backtest `queued`/`running` (in-progress), a backtest `failed`, a backtest `cancelled`, `done`-but-insufficient-n, and backend-unreachable — each an explicit, distinct state (mirror `StudyResultsView`'s `results-failed` / `results-cancelled` / `results-status-absence`), never a fabricated green/edge result.

### Polish (fold in because the iteration touches `/structure`; **non-gating**)
- [ ] Extend the `/structure` header subtitle (`data-testid="structure-framing"`) to preview all three sections including Registry + Comparison (iter-2 audit F1 / ux-regression rec #1).
- [ ] Update `README.md`'s "Structure page" bullet to reflect the full shipped surface (levels/zones + registry/champion + the `structure_tape`-vs-`v1` comparison), replacing the stale J-01-only description (iter-2 coherence advisory).

### New user-facing capability
The user can choose a registered dataset, run `structure_tape` vs `v1` as an offline research job, and read both strategies' aggregates + per-class A/B/C breakdown side by side — with the honest keyless outcome (`structure_tape` a non-survivor, insufficient n, champion unchanged) visible in the browser rather than only via `curl`/MCP.

### New information displayed
Side-by-side backtest aggregates (`n`, net R, net $, `win_rate`, `max_drawdown_r`) for `v1` and `structure_tape`; the per-class A/B/C `aggregates_by_class` table with `insufficient_sample`; the founding baseline row from the PnL ledger; the champion pointer; and the simulated register string — all read verbatim from their canonical payloads.

### New user actions
A dataset selector and a "Run comparison" button (an offline research job over immutable recorded data — it places nothing). No promotion control; no order/execution control.

### UI surface changes
One new Comparison section on the existing `/structure` page (below Registry). No new route, no nav change. Header subtitle updated to preview the section.

### Product surface delta
`/structure` becomes the complete read-only home of the era-4 structure stack — levels/zones (J-01) + registry/champion (J-02) + the honest comparison (J-03). All four Must-have journeys become browser-visible.

### Blueprint conformance
J-03's canonical home already exists in `blueprint.md` Information Architecture ("`/structure` (Comparison section) · Structure"); this iteration builds that section. No new route, no nav-skeleton change, so **no `blueprint.reapproval-requested` file**. The Comparison section is 1 click from the persistent top bar (then same-page), within the ≤2-click rule.

### Data-contract additions
No value J-03 displays is new to the app — all are already registered (backtest aggregates → `backtests.py:_aggregate`; per-class breakdown + `insufficient_sample` → `backtests.py:_aggregate_by_class`; PnL-ledger + founding baseline → `pnl_ledger.py:ledger_projection`; datasets → dataset store; champion → `get_champion_pointer`; strategies → `Config.strategy_definition`). **One additive registration** was made to `blueprint.md` this iteration: the **simulated-honesty register string**, newly surfaced on `/structure` — single owner `REGISTER` (`apps/backend/app/research/backtests.py:142`, imported by `pnl_ledger.py`), served verbatim by `GET /research/backtests/{id}` and `GET /research/pnl/ledger`. No new computation, no new endpoint, no second owner.

## OUT OF SCOPE

- No `/datasets` library-inventory page (roadmap Card 5.9; explicit goal non-goal).
- No champion promotion or any control that moves the champion pointer; no PnL-ledger write.
- No backend edit of any kind — the backend already serves J-03; `config.py`, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the engine, and `config_fingerprint` `4d665603569b9dbf` are frozen.
- No client-side recomputation of R, $, win-rate, the class partition, or the champion.
- No brokerage / order / execution / real-money / paper-trading path of any kind.
- No pooling of train/hold-out; no lowering of the minimum sample size to manufacture a survivor.
- No new `lightweight-charts` chart for the comparison (tabular render); no change to J-01's chart or J-02's registry behavior.
- No new vocabulary ("paper trading" / "annualized" / "expected profit" / advice / imperative phrasing); the register text comes from the payload, not the frontend.

## DEFINITION OF DONE

- [ ] **J-03 passes via browser-qa-agent** with populated screenshots in `reports/qa/goal-structure_ui-iter-3-evidence/`: a dataset chosen; both backtests polled to `done`; side-by-side aggregates byte-matching `GET /research/backtests/{id}`; the per-class A/B/C table with `insufficient_sample` verbatim; the `register` string rendered from the payload; the champion unchanged at `v1`/`default`; and the keyless `structure_tape`-non-survivor outcome.
- [ ] Required-still-passing **J-01** and **J-02** re-verified green on the now-3-section `/structure` page (levels/zones + chart overlay legible with intact z-index; registry + champion intact).
- [ ] Required-still-passing **J-04** green: backend suite passes (≥1146 passed / 1 skipped), engine equivalence byte-identical, `config_fingerprint` recomputes live to `4d665603569b9dbf`, 5-link nav intact, `/performance` unaffected, `apps/backend/` diff empty.
- [ ] coherence-auditor returns **COHERENCE-PASS** (register + every aggregate read verbatim from their single canonical source; no second computation, no second endpoint).
- [ ] No anti-goal violation introduced (no execution path; no promotion / no `set_champion_pointer`; no client recompute; no hardcoded register; no vocabulary drift).
- [ ] Unit/integration tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-structure_ui-iter-3-dev.md`.

## TESTING REQUIREMENTS

- **Browser** (required, with screenshot evidence — iter-0 lesson): **J-03** end-to-end — choose dataset → run both strategies → poll to `done` → side-by-side aggregates + per-class A/B/C table verbatim + `insufficient_sample` + register-from-payload + champion unchanged + the keyless non-survivor outcome; and every honest state (empty datasets, `running`, `failed`, `done`-but-insufficient-n, backend-unreachable). Re-verify **J-01** (levels/zones render; chart overlay legible) and **J-02** (registry/champion) since the page gains a section. Re-verify **J-04** (5-link nav; `/performance` intact).
- **Unit/integration:** the backend suite must stay green (regression sentinel — no backend edit expected). The new `api.ts` helpers must return `null`/error honestly on failure (no fabricated payload), demonstrated via the honest-state browser checks.
- **Error cases:** empty datasets list → honest empty state; a `failed`/`cancelled` backtest → distinct honest state; n below the minimum → `insufficient_sample` verbatim; backend unreachable → honest error. None may fabricate a green or edge result.

## NOTES

- **GOAL_ACHIEVED candidate:** J-03 passing makes all four Must-have journeys green. The evaluator decides GOAL_ACHIEVED — this spec does not assert it.
- **Single-source register (T10, load-bearing):** render the `register` string from the payload (`GET /research/backtests/{id}` / `GET /research/pnl/ledger`); do NOT hardcode it. The served constant is the fuller `"simulated — assumed fees/slippage — not indicative of live results"` (`backtests.py:142`); the goal doc's abbreviated phrase must not be typed into the UI.
- **Lesson iter-0 (Applies to J-01/J-02/J-03):** treat any target journey with no populated `reports/qa/goal-structure_ui-iter-3-evidence/` screenshot as `unknown`, not `passing`.
- **Lesson iter-1(b) (Applies to J-03):** if the auditor fixes any browser-QA FAIL in place, J-03 stays `partial` until an independent browser-QA re-run confirms — not the auditor's self-verification screenshot alone.
- **Lesson iter-1(a) (Applies to J-03 + charts):** the Comparison section is tabular, so the `lightweight-charts` z-index trap is low-risk here — but confirm adding the section does not re-occlude J-01's `StructureChart` overlay. Carry-over F2 (`PriceChart.tsx` on Cockpit, same latent occlusion) stays out of scope.
- **Lesson iter-2 (Applies to the evaluator/coherence diff-scope):** the iter-3 code will be uncommitted at eval time; scope the diff with `git diff <snapshot> -- <path>` / `git status --short`, never a two-dot `snapshot..HEAD` range (which returns empty and falsely reads "nothing built").
- **Reuse anchors:** `apps/frontend/components/StudyResultsView.tsx` (verbatim aggregate render + `results-failed`/`results-cancelled`/`results-status-absence` honest states + insufficient-sample label) and the Studies page poll loop (`apps/frontend/app/studies/page.tsx`, `setInterval` 700ms, poll-while-active). Note the Studies page polls `/research/studies` (sweeps); J-03 polls `/research/backtests/{id}` — reuse the *pattern*, not the endpoint.
- **Polish is non-gating:** do not block J-03 on the README bullet or the header-subtitle preview.
