# Goal Iteration 0 — Baseline: verify all Structure-interlude journeys against current state

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** structure_ui
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04
- **Required-still-passing journeys:** none (baseline — this iteration establishes the passing/failing/partial set that later iterations preserve)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**

  _Immutable rails — the identity of the project:_
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

  _Interlude-specific anti-goals (added, not weakening any rail above):_
  - **The Structure UI recomputes nothing.** Every displayed value — level price/timeframe/type, zone class, net R, net $, n, `insufficient_sample`, the champion — is read verbatim from its canonical endpoint. No client-side grading, PnL math, aggregation, or champion resolution. A number that diverges from its API/MCP payload is a defect (trap T10). *(critical)*
  - **No new backend computation or endpoint.** This interlude consumes the existing canonical endpoints; the only backend edit is the additive `/structure` entry in the `meta.py` route registry (the nav owner). It creates no second implementation of any value. *(critical)*
  - **Honest UI states only.** No fabricated chart, level, zone, trade, fill, or PnL to force a green journey; every failure mode (no bar series, no levels, no zones, insufficient n, missing credentials, backend unreachable) surfaces an explicit, distinct state. *(critical)*
  - **The UI never promotes.** The comparison view runs backtests and diffs their reports; it MUST NOT move the champion pointer or write the PnL ledger — promotion remains the sweep's hold-out act. *(critical)*
  - **No vocabulary drift** (trap T9). No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a PnL-ledger (or, for a read surface, a single-source-of-truth) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Establish the honest starting line: run every Must-have journey (J-01–J-04) of the "Structure, made visible" interlude against the current codebase and record which already pass, which fail, and which are partial — with **no** code changes.

## BACKGROUND

This is the **baseline assessment**, not a feature delivery — the developer step is a no-op; the value comes entirely from browser-qa + the backend/equivalence suite running every journey to snapshot reality. This is a UI-surfacing interlude on top of the frozen eras 1–4 foundation: the era-4 structure stack (S/R levels, A/B/C confluence zones, the `v1`+`structure_tape` registry, the `structure_tape`-vs-`v1` backtest) already exists on REST/MCP/CLI but has **no browser home**. Codebase inspection this iteration (evidence, to be confirmed by the executor, not scored here) shows: no `/structure` page under `apps/frontend/app/`, and `apps/backend/app/meta.py` `UI_ROUTES` carries only the five pre-interlude routes (`/`, `/journal`, `/journal/[id]`, `/studies`, `/performance`) — so J-01/J-02/J-03 have no surface to render and are expected to read as failing, while J-04 (foundation sentinel) is expected to read as passing since nothing has changed. Depth is **lean** per the baseline-mode rule (lean cycle is sufficient — no code is written; the browser-qa step carries the value); there is no prior evaluator verdict and no ESCALATE. Lessons ledger is empty (first iteration), so no prior pitfall applies.

## IN SCOPE

### Backend
- [ ] None — verify-only baseline. No source files are modified this iteration.

### Frontend (if applicable)
- [ ] None — verify-only baseline. No source files are modified this iteration.

### Verification tasks (no code)
- [ ] Run J-01 via browser-qa-agent: attempt to reach a Structure tab / `/structure` route and render S/R levels + A/B/C confluence zones; record the result and the honest-state behavior observed.
- [ ] Run J-02 via browser-qa-agent: attempt to view the strategy registry (`v1` + `structure_tape`) and the badged champion; record the result.
- [ ] Run J-03 via browser-qa-agent: attempt the on-screen `structure_tape`-vs-`v1` comparison with per-class A/B/C breakdown; record the result.
- [ ] Run J-04 (foundation sentinel): execute the full backend suite + engine equivalence test, confirm `config_fingerprint` is `4d665603569b9dbf`, and spot-check `/`, `/journal`, `/studies`, `/performance` in the browser; record the result.

### New user-facing capability
None — this iteration delivers no capability. It records the baseline pass/fail/partial state of the four journeys.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product is unchanged after this iteration. Its only output is a recorded baseline of journey states.

### Blueprint conformance
No new surfaces this iteration. The blueprint (`runs/goal-session-structure_ui/state/blueprint.md`) is drafted alongside this spec: single new page `/structure` (Structure nav section) hosting J-01/J-02/J-03 as sections; J-04 covers the existing surfaces. No page is created this iteration.

### Data-contract additions
None. This interlude introduces **no** new owned value and **no** new computation. Every value the future Structure view will display is already owned by an era-1–4 canonical source and registered in the blueprint's Data Contract, read verbatim (bars, levels + `zone.class`, strategies + champion pointer, backtest `aggregates`/`aggregates_by_class`, PnL ledger, datasets, the `meta.py` route map).

## OUT OF SCOPE

- Any code change whatsoever (no `/structure` page, no `meta.py` `UI_ROUTES` edit — those begin in iteration 1).
- Any edit to `config.py`, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the engine, or any existing surface.
- Marking journeys as passing/failing — that is the goal-evaluator's job; this spec only requests they be exercised and recorded.
- The `/datasets` library-inventory page (explicitly out of scope for this interlude — Card 5.9 / Era-5 scope).

## DEFINITION OF DONE

- [ ] All four Must-have journeys (J-01, J-02, J-03, J-04) are exercised against the current HEAD and each has a recorded outcome (pass / fail / partial) with evidence.
- [ ] The full backend suite and the engine equivalence test are run and their current result recorded, with `config_fingerprint` observed and noted (baseline for the J-04 sentinel).
- [ ] No source files changed — `git diff` over `apps/` is empty (only run/report artifacts written).
- [ ] No anti-goal violation introduced (trivially satisfied — no code changes).
- [ ] Dev handoff written at `docs/handoffs/goal-structure_ui-iter-0-dev.md` noting this was a verify-only baseline (developer no-op).

## TESTING REQUIREMENTS

- **Browser:** J-01, J-02, J-03 (attempt to locate and drive the Structure surface — expected absent at baseline; record the honest "not present" observation), and J-04 (spot-check the existing `/`, `/journal`, `/studies`, `/performance` surfaces still work).
- **Unit/integration:** run the full backend test suite and the engine equivalence test as the J-04 baseline; record pass counts and the observed `config_fingerprint` (expected `4d665603569b9dbf`).
- **Error cases:** none this iteration — no new inputs are introduced; honest-empty/degraded states are only *observed*, not yet implemented.

## NOTES

- **Baseline framing:** the goal-evaluator will classify already-passing journeys as `already_passing` so later iterations skip them. Expected baseline read (evidence-based, evaluator to confirm): J-01/J-02/J-03 fail (no `/structure` route or nav entry exists), J-04 passes (foundation untouched). Do not treat these expectations as the verdict.
- **Dependency order for later iterations** (from `docs/goal.md`): J-01 → J-02 → J-03, with J-04 guarding continuously. Iteration 1 will likely target J-01 alone (it creates the `/structure` route + the additive `meta.py` `UI_ROUTES` entry that unblocks J-02 and J-03's shared page home).
- **Blueprint drafted this iteration:** `runs/goal-session-structure_ui/state/blueprint.md` — Information Architecture (one new `/structure` page under a Structure nav entry, data-driven via `GET /meta/ui-routes`) + a Data Contract in which the Structure view owns nothing. Auto-approved by default; the loop proceeds to iteration 1 unless `--require-blueprint-approval` was passed.
- The canonical endpoints the future Structure view will read (`/research/bars`, `/research/levels`, `/research/strategies`, `/research/profiles`, `/research/datasets`, `/research/backtests` + `/{id}`, `/research/pnl/ledger`, `/meta/ui-routes`) were confirmed present in the codebase this iteration — the interlude is a pure read/visualize surface over them.
