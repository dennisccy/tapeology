# Goal Iteration 0 — Baseline assessment (verify-only)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_rich
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09
- **Required-still-passing journeys:** none (baseline establishes the bar)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no fundamental analysis, no chart-pattern or indicator charting, no portfolio/position management — these belong to separate projects and MUST NOT be built here. *(critical)*
  - **Price impact over raw aggression.** The classifier MUST distinguish absorption from control: a tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state (bid_absorption / ask_absorption), never to seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical)*
  - **Honest uncertainty.** When evidence is weak or mixed, the spread is wide, or there is no clean price impact, the state MUST be `unclear` with low confidence. The system MUST NOT manufacture a directional call to look decisive. *(critical)*
  - **No fabricated data.** On a provider gap/failure the system MUST surface an explicit stale/no-data state and MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed MUST NOT require engine or API changes.
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness. Each simulated scenario MUST have an automated test asserting the expected state is reached with reasonable confidence.
  - **No ML in v1.** The MVP classifier MUST be transparent rule/threshold logic over named features — no trained model in the first version.
  - **No trade/profit claims.** The product MUST NOT claim profitability or present output as trading advice; tape state is descriptive, not prescriptive.
  - **No secrets in source.** No API keys, tokens, or credentials committed; any future provider keys come from environment/config only.

## GOAL

Establish the baseline: attempt all nine Must-have user journeys against the current codebase
and record, per journey, whether it already passes, partially passes, or fails — so later
iterations build only what is actually missing.

## BACKGROUND

This is a **baseline assessment, not a feature delivery**. No code is written this iteration.
Codebase verification (Glob/Bash) confirms the repository contains **no product implementation
yet** — only the `incredible_auto_dev/` dev-chain framework subtree and the goal-session state;
there is no backend (`apps/`, `backend/`, FastAPI app), no Next.js frontend, and no engine. The
expected baseline outcome is therefore that **all nine journeys (J-01…J-09) are FAILING / not
yet implemented**. Recording this seeds `journey-history.json` so iteration 1 can target the
real gap (start the backend engine + provider + API, then the cockpit UI). The lessons ledger is
empty (first iteration), so there are no prior pitfalls to apply.

This iteration also drafts the **coherence blueprint**
(`runs/goal-session-i_will_be_rich/state/blueprint.md`) — the Information Architecture (the
single `/` tape-cockpit home) and the Data Contract (each canonical value → its one computing
module → its one serving endpoint). `run-goal.sh` pauses after baseline for the human to
review/approve that blueprint before any feature is built.

## IN SCOPE

### Backend
- [ ] None — verify-only iteration. No backend code is written.

### Frontend (if applicable)
- [ ] None — verify-only iteration. No frontend code is written.

### New user-facing capability
None (verify-only; no code changes this iteration).

### New information displayed
None (verify-only; no code changes this iteration).

### New user actions
None (verify-only; no code changes this iteration).

### UI surface changes
None (verify-only; no code changes this iteration).

### Product surface delta
None. The product experience is unchanged because nothing is built yet; this iteration only
measures the starting point.

### Blueprint conformance
No new surfaces. The blueprint (Information Architecture + Data Contract) is **drafted** this
iteration at `runs/goal-session-i_will_be_rich/state/blueprint.md` and awaits human approval; no
pages are built. All future surfaces must live under the single `/` home defined there.

### Data-contract additions
None (no code this iteration). The full contract — tape state + confidence, the 14 features ×
5 windows, bid/ask/spread/last, recent trades with side, observations/event-log, and the
watched-scenario label, each with its single canonical computing module and serving endpoint —
is drafted in `blueprint.md` for human approval, not implemented here.

## OUT OF SCOPE

- Writing any backend, engine, classifier, provider, or frontend code (deferred to iter 1+).
- Marking journeys as passing/failing in `journey-history.json` — only the goal-evaluator does that.
- Standing up or scaffolding the FastAPI app or the Next.js app.
- Anything outside `docs/goal.md` Key Capabilities (scanners, news/sentiment, charting,
  fundamentals, execution/broker integration, portfolio management, ML).

## DEFINITION OF DONE

- [ ] Each Must-have journey J-01…J-09 is attempted by the browser-qa-agent against the current
      codebase and its result (pass / partial / fail) is recorded with evidence.
- [ ] The baseline result is captured so the goal-evaluator can seed `journey-history.json`
      (already-passing vs yet-to-build) for iteration 1 targeting.
- [ ] No code was written this iteration (verify-only); no anti-goal violation introduced.
- [ ] The coherence blueprint exists at `runs/goal-session-i_will_be_rich/state/blueprint.md`
      and is ready for the human approval pause.

## TESTING REQUIREMENTS

- **Browser:** attempt all of J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09 and record a
  pass/partial/fail result per journey. With no app running, the expected, honest result is that
  every journey fails (nothing to watch, no cockpit, no stream) — that is the correct baseline
  signal, not a defect to fix this iteration.
- **Unit/integration:** N/A — no code changes this iteration.
- **Error cases:** N/A this iteration.

## NOTES

- **Greenfield finding:** no product code exists yet; the only tracked code is the
  `incredible_auto_dev/` framework subtree. Treat the baseline as "everything to build."
- **Stack (from `docs/goal.md` Constraints), for iter 1 context:** backend Python 3.12+ /
  FastAPI (uvicorn); frontend Next.js (App Router) + TypeScript; WebSocket for live push, REST
  for request/response; Phase-1 data simulated, deterministic and seedable; in-memory only.
- **Suggested iter 1 direction:** stand up the provider interface + deterministic
  `SimulatedProvider` with the five reserved sim tickers (`SIM-BUYER`, `SIM-SELLER`,
  `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP`), the feature engine + rule-based classifier, and the
  REST/WS API, then the `/` cockpit UI — sequenced so J-01 (watch + live cockpit) becomes
  verifiable first, conforming to the approved blueprint.
- After this baseline, `run-goal.sh` pauses for human review/approval of `blueprint.md`; resume
  with `--resume` (or use `--auto-approve-blueprint`) to begin iteration 1.
