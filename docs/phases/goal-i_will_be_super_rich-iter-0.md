# Goal Iteration 0 — Baseline assessment (verify-only) + coherence blueprint

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15
- **Required-still-passing journeys:** (none — baseline establishes the starting line; nothing to regress yet)
- **Anti-goal reminders** (verbatim from `docs/goal.md`; this and every later iteration MUST respect them):
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no fundamental analysis, no chart-pattern or indicator charting, no portfolio/position management. *(critical)*
  - **Price impact over raw aggression.** A tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state (bid_absorption / ask_absorption), never to seller_control / buyer_control. *(critical)*
  - **Honest uncertainty.** When evidence is weak or mixed, the spread is wide, or there is no clean price impact, the state MUST be `unclear` with low confidence. The system MUST NOT manufacture a directional call to look decisive. *(critical)*
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state and never a cockpit: provider gap/feed lull → `stale`; unknown/untradable symbol → explicit error; empty historical window → explicit no-data; live watch while market closed → explicit closed (with next open); missing credentials → explicit "unavailable". *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface; swapping the simulator for a real feed (live or historical) MUST NOT require engine or API changes. A concrete vendor SDK MUST appear in only one adapter module behind a vendor-neutral seam.
  - **No secrets in source.** Real-vendor API keys/tokens MUST come only from environment/config and MUST NOT be committed; with no keys the app runs simulator-only and real modes report an explicit "unavailable".
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness.
  - **No ML in v1.** The MVP classifier MUST be transparent rule/threshold logic over named features — no trained model in the first version.
  - **No trade/profit claims.** The product MUST NOT claim profitability or present output as trading advice; tape state is descriptive, not prescriptive.

## GOAL

Establish the starting line: run every Must-have journey (J-01 – J-15) against the **current** codebase and record which already pass, which fail, and which are partial — no code changes.

## BACKGROUND

This is a **baseline assessment, not a feature delivery**. A prior session (`i_will_be_rich`) built and shipped the
**simulated** half of the product — the single-ticker tape cockpit on reserved sim tickers (J-01 – J-09) — proven over
seven iterations. The goal was then **expanded** (commit `544267c`) to add **real US-equity market data** in two modes
that reuse the same engine: **live** streaming and **historical replay**, behind a vendor-agnostic adapter (Alpaca,
free IEX feed) — journeys **J-10 – J-15**.

Codebase reconnaissance for this baseline confirms the split concretely: the engine, simulated provider, watch manager,
serializers, all REST reads (`/state`, `/features`, `/events`, `/summary`), `WS /stream`, and the full cockpit UI exist;
**none** of the real-data surfaces exist yet — there is no live or historical provider, no Alpaca/vendor adapter, no
`GET /symbols/search`, no `GET /market/clock`, no `mode` body on `POST /watch`, and the TopBar has no data-source
selector, symbol search, window picker, replay-speed control, or market-status indicator. The expectation is therefore
that J-01 – J-09 pass and J-10 – J-15 are not yet implemented — **but this iteration only records evidence; the
goal-evaluator (not this spec) classifies each journey.** Already-passing journeys are marked `already_passing` so later
iterations skip them and target only the failing/partial real-data journeys.

This iteration also **drafts the coherence blueprint** (`runs/goal-session-i_will_be_super_rich/state/blueprint.md`),
carrying forward the approved simulated IA + Data Contract and extending it with the real-data half. After this baseline,
`run-goal.sh` pauses for human review/approval of that blueprint before any feature is built.

No `lessons.md` entries exist for this session yet (fresh ledger).

## IN SCOPE

### Backend
- [ ] No code changes. Verification only.

### Frontend
- [ ] No code changes. Verification only.

### New user-facing capability
None — this is a verify-only baseline. No new capability is delivered.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product is observed as-is to record the journey pass/fail baseline.

### Blueprint conformance
The blueprint is **drafted this iteration** (Information Architecture + Data Contract for the full J-01 – J-15 product)
and awaits human approval. No new UI surfaces are built in this iteration, so there is nothing to conform yet.

### Data-contract additions
None built this iteration. The blueprint *registers* the future real-data values (symbol search results → `GET /symbols/search`;
market clock → `GET /market/clock`; watched-source descriptor + stale stream-status → `WatchManager`/feeder; real-data
availability/failure state → live/historical provider) so that the iterations which build them have a single canonical
owner + endpoint to conform to. No value is computed or served in this iteration.

## OUT OF SCOPE

- Any source-code change (backend or frontend) — this is strictly an assessment pass.
- Building any real-data capability: live provider, historical-replay provider, Alpaca/vendor adapter, `/symbols/search`,
  `/market/clock`, the `mode` watch body, or any new UI control. These are future iterations.
- Marking journeys pass/fail — that is the goal-evaluator's job, from this iteration's recorded evidence.
- Configuring or committing real-vendor credentials.

## DEFINITION OF DONE

- [ ] Every Must-have journey (J-01 – J-15) is exercised against the current codebase and its observed result is recorded with evidence (screenshot / endpoint output / explicit "not implemented").
- [ ] The simulated journeys (J-01 – J-09) are run end-to-end in the browser on their reserved sim tickers.
- [ ] The real-data journeys (J-10 – J-15) are exercised to the extent the current code + environment allow; where a surface does not exist or credentials are absent, that is recorded explicitly (not silently skipped, not marked pass).
- [ ] The coherence blueprint is drafted at `runs/goal-session-i_will_be_super_rich/state/blueprint.md` and ready for human approval.
- [ ] No source files were modified.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-0-dev.md` noting "baseline — no code changes" and listing the per-journey observations.

## TESTING REQUIREMENTS

- **Browser (run every journey, record the result):**
  - **J-01 – J-09** on the reserved sim tickers (`SIM-BUYER`, `SIM-SELLER`, `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP`) — expected to render the live cockpit, resolve to the scenario's tape state, announce transitions, agree with REST (J-08), and stop cleanly (J-09).
  - **J-10** — look for the data-source selector (Live / Historical / Simulated) and its mode-specific control reveal. Absent in current code → record as not-implemented.
  - **J-11, J-13** — historical replay and symbol search require vendor credentials; if the surfaces and/or credentials are absent, record as not-implemented / not-runnable (do **not** mark pass).
  - **J-12, J-15** — live streaming and the stale-recovery behavior are operator/gated credentialed checks; their UI controls (Live selector + market-status + status dot) are browser-checkable on their own. Record the controls' presence/absence; the real-socket behavior is out of reach at baseline.
  - **J-14** — the honest no-credentials / unknown-symbol / closed-market degradation states. Record whether any explicit "unavailable / not tradable / no-data / closed" state exists today (expected: not yet, since the real modes are unbuilt).
- **Unit/integration:** Run the existing backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`) to confirm the current engine/classifier/API tests pass as the baseline — no new tests are added this iteration.
- **Error cases:** Confirm the existing honest-failure behavior still holds (unknown sim ticker → 400; not-watched read → 404; post-Stop reads 404 / WS rejected). No new error paths are introduced.

## NOTES

- **Credential gating is expected and is not a failure of this baseline.** J-11 / J-12 / J-13 / J-15 depend on real-vendor
  credentials and (for J-12 / J-15) market hours; with the real modes unbuilt and likely no keys in the QA harness, the
  honest baseline record is "surface not present / not runnable," which the evaluator should read as *failing/to-build*,
  never as passing.
- The real-data half (J-10 – J-15) is the actual work of this session; this baseline exists to confirm the simulated half
  (J-01 – J-09) is the green floor that the real-data work **must not regress** (anti-goal: the real-data work MUST NOT
  regress the simulated journeys).
- Per goal-decomposer baseline rules: the developer step is effectively a no-op; the value of this iteration comes from the
  browser-qa step exercising every journey, and from the drafted blueprint awaiting approval.
