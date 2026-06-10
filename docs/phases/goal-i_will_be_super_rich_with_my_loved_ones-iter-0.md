# Goal Iteration 0 — Verify-only baseline: establish per-journey status for J-01–J-68 (no code changes)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16, J-17, J-18, J-19, J-20, J-21, J-22, J-23, J-24, J-25, J-26, J-27, J-28, J-29, J-30, J-31, J-32, J-33, J-34, J-35, J-36, J-37, J-38, J-39, J-40, J-41, J-42, J-43, J-44, J-45, J-46, J-47, J-48, J-49, J-50, J-51, J-52, J-53, J-54, J-55, J-56, J-57, J-58, J-59, J-60, J-61, J-62, J-63, J-64, J-65, J-66, J-67, J-68
- **Required-still-passing journeys:** none (first iteration — nothing recorded yet)
- **Superseded journeys:** J-33 and J-34 are marked **superseded** in `docs/goal.md` (⚠ notes) — they are verified through their successors J-36/J-37 and must be recorded as superseded, not independently exercised.
- **Anti-goal reminders** (headline sentences verbatim from `docs/goal.md` ## Anti-goals — the full section is binding for the evaluator):
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. *(critical)*
  - **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no fundamental analysis, no chart-pattern or indicator charting, no portfolio/position management. *(critical)*
  - **Price impact over raw aggression.** A tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state, never to control. *(critical)*
  - **Honest uncertainty.** When evidence is weak or mixed, the state MUST be `unclear` with low confidence; spread/impact tests are judged relative to the instrument, and a quoting artifact MUST NOT veto a clearly directional move. *(critical)*
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI. *(critical)*
  - **No magic numbers.** Every threshold/cutoff/boundary MUST come from config.
  - **Provider-agnostic engine.** Swapping the data source MUST NOT require engine or API changes; the vendor SDK lives in exactly one adapter.
  - **No secrets in source.** Real-vendor keys come only from environment/config.
  - **Deterministic & reproducible.** Same ordered event stream (and seed) ⇒ identical features, state, and confidence.
  - **No ML in v1.** The MVP classifier MUST be transparent rule/threshold logic.
  - **No trade/profit claims.** Tape state is descriptive, not prescriptive.
  - **Honest side inference, not fabrication.** No quote AND no prior trade ⇒ the print stays `unknown`. *(critical)*
  - **One focused chart, computed once.** OHLC bars and markers are computed once in the engine history buffer; the UI never recomputes side, state, or price. *(critical)*
  - **Honest pause.** Pause freezes without teardown or fabricated catch-up data. *(critical)*
  - **Timezone-correct windows.** A historical window is fetched for the exact local instant selected — no silent UTC shift. *(critical)*
  - **No silent dead-clicks.** Pressing Watch MUST always produce a visible UI change within ~1 second. *(critical)*
  - **No mute cockpit, no silent return to idle.** A valid Watch resolves to a non-idle terminal state; never a confident `live` over an empty tape. *(critical)*
  - **Bounded, honest, performant vendor calls.** Real call-level deadlines, backend bound < frontend timeout, fast by design not by lengthening timeouts. *(critical)*
  - **Real-data journeys are proven with real data.** Outcomes that depend on real market data are NOT done until an automated test over committed real captured data asserts them in CI without credentials. *(critical)*
  - **No unsolicited or unconditional trade commands.** Every actionable cue is gated on a user-declared thesis with an invalidation; no imperative buy/sell/enter/exit wording anywhere. *(critical)*
  - **Evidence before cues.** The entry checklist/stance and hints MUST NOT be built before the journal, excursions, and replay studies exist and their journeys (J-58–J-62) pass. *(critical)*
  - **No profitability or edge claims.** No currency P&L, equity curves, or win-rate-as-edge presentation anywhere. *(critical)*
  - **No prediction language.** A verdict or stance describes what the tape is doing now — never a forecast. *(critical)*
  - **No naked outputs.** Every published verdict, stance, hint, flag, check, and grade carries plain-language evidence. *(critical)*
  - **Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time. *(critical)*
  - **The research layer is read-only over the engine.** Byte-identical engine outputs with or without observers/theses (equivalence-tested). *(critical)*
  - **Source, feed, and config honesty.** Every research record is stamped with bound source, `data_feed`, and `config_fingerprint`; no pooling across feeds or fingerprints. *(critical)*
  - **No scanning, no execution — still.** Theses/hints exist only on the one watched ticker; studies only over explicitly chosen windows.
  - **No new indicators, no auto-tuning.** Research composes EXISTING engine features/states only; no parameter optimizer. *(critical)*
  - **Persistence stays scoped to research records.** SQLite holds research records only — no tape data persisted.

## GOAL

Establish an honest baseline: verify every Must-have journey (J-01–J-68) against the current codebase with **zero code changes**, so the session knows exactly which journeys already pass (carried over from prior sessions) and which the research evolution must build.

## BACKGROUND

This is a baseline assessment, not a feature delivery. The codebase already contains the full tape-reading product from prior goal sessions (`i_will_be_rich`, `i_will_be_super_rich`, which ended GOAL_ACHIEVED): the simulated cockpit (J-01–J-09), real-data live/historical modes (J-10–J-16), the prediction chart, pause/resume and local-time windows (J-17–J-20), Watch-lifecycle honesty (J-21–J-27), vendor responsiveness (J-28–J-30), the refinement pass (J-31, J-32, J-35), and the reopened real-data fixes (J-36, J-37). The expectation is that most or all of J-01–J-37 already pass and will be recorded `already_passing`.

The **research evolution** (J-38–J-68: declared theses, verdict engine, journal + SQLite persistence, review/grading, excursions, analytics, replay studies, and — last — the cue layer) is **not built**: the backend has no research module, no SQLite store, and no `/research/*` endpoints; the frontend has only the `/` page (no `/journal`, no `/studies`, no thesis strip, no hint dock); the two new sim scenarios `SIM-SHIFT` / `SIM-REVERSAL` do not exist. These journeys are expected to fail and should be recorded FAILING quickly by absence of their canonical surfaces — do not burn time walking 31 detailed flows against pages that do not exist.

## IN SCOPE

No Backend or Frontend code changes. Verification only:

- [ ] Start the backend and frontend via the standard harness scripts
- [ ] Run the full backend test suite once (`cd apps/backend && .venv/bin/python -m pytest tests/ -v`) and record the result as supporting evidence (including the committed real-data fixture tests gating J-36/J-37 and the existing per-scenario classifier tests)
- [ ] Browser-verify each journey per the Testing Requirements below and record pass / fail / partial / blocked per journey

### New user-facing capability
None — verification only.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None. After this iteration the session has a recorded per-journey baseline in `journey-history.json`.

### Blueprint conformance
No new surfaces. The session blueprint is already drafted **and human-approved** at `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` (`blueprint.approved` marker present, 10-06-2026) — it carries forward the prior approved contract rows 1–13 and registers the research-evolution IA + Data Contract. No blueprint action remains in this iteration.

### Data-contract additions
None in this iteration (the approved blueprint pre-registers the research-evolution values, rows 14–26, for future iterations; nothing is built here).

## OUT OF SCOPE

- Any code change, fix, refactor, config tweak, or test addition — even for journeys that fail
- Building any research-evolution surface (thesis strip, `/journal`, `/studies`, `/research/*` endpoints, SQLite store, `SIM-SHIFT`/`SIM-REVERSAL`)
- Marking journeys passed/failed in `journey-history.json` (the goal-evaluator owns that)
- Live-market-hours socket verification (J-12/J-15 real-socket legs are operator-gated per `docs/goal.md`)

## DEFINITION OF DONE

- [ ] Every Must-have journey J-01–J-68 verified against the current state (browser where verifiable, by-absence for unbuilt surfaces, credential/operator-gated legs explicitly recorded as such — never silently skipped)
- [ ] Backend test suite run once and its result recorded
- [ ] Results recorded so the goal-evaluator can populate `journey-history.json` (already-passing vs failing vs blocked/partial, J-33/J-34 recorded superseded)
- [ ] No code changes made (the diff for this iteration is empty apart from session artifacts)
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-0-dev.md` (stating no-op + verification evidence)

## TESTING REQUIREMENTS

- **Browser — sim-verifiable existing journeys (no credentials):** J-01–J-10 (watch the five `SIM-*` scenarios; cockpit panels, states, transitions, REST/UI agreement, stop), J-17 (sim chart + markers + bar sizes), J-19 (pause/resume), J-21/J-23/J-24 (dead-click, failure surfacing, inline validation), J-31 sim leg (synthetic session clock axis), J-35 (dd-MM-yyyy everywhere + custom date input), and the no-credential legs of J-14/J-22/J-25 if credentials are absent.
- **Browser + credentials (if configured in the environment):** J-11, J-13, J-16, J-18, J-20 (correct-window fetch), J-25 real-mode legs, J-26–J-30, J-32, and the real-window confirmations of J-36/J-37. If credentials are absent, record these as blocked/partial with the reason — do not fabricate a result.
- **Operator-gated (record as such, do not attempt):** J-12 and J-15 real-socket legs (require market hours).
- **CI-fixture journeys:** J-36/J-37 are primarily judged by the committed real-data fixture tests in the backend suite (runnable without credentials) — record their pass/fail from the pytest run.
- **Research-evolution journeys (expected FAILING):** J-38–J-68 — verify by absence of canonical surfaces: no thesis strip on `/`, no `/journal`, no `/studies`, no `/research/taxonomy` endpoint, no `SIM-SHIFT`/`SIM-REVERSAL` scenarios. A 404 on `GET /research/thesis/active?ticker=SIM-BUYER` plus missing nav/pages is sufficient to fail the whole block; note per-journey which surface is missing. J-68 (regression sentinel) is recorded failing/pending because its equivalence test does not exist yet, even though J-01–J-09 themselves may pass.
- **Unit/integration:** one full run of the existing backend suite; no new tests.
- **Error cases:** none to add — existing suites only.

## NOTES

- **Session restart context:** a prior run of this session aborted on 10-06-2026 before the baseline executed (0 iterations recorded; `journey-history.json` is empty). Its planning artifacts remain valid and are reused: this spec was authored against the current `docs/goal.md` (which predates it), and the coherence blueprint was drafted then **human-approved at resume** — neither needs re-drafting. This dispatch simply executes the verification that the aborted run never ran.
- Lessons file is empty (fresh session); no prior evaluator feedback exists.
- The journey set is large (68) — this is intentional and allowed only in baseline mode. Subsequent iterations will target 1–3 journeys each.
- `docs/goal.md` build order is binding for later iterations: cue journeys (J-63–J-67) MUST NOT be implemented before the evidence journeys (J-58–J-62) pass (*Evidence before cues* anti-goal). The decomposer will sequence accordingly from iter-1.
- The `.claude/project-template.md` ROADMAP table is stale (it reflects the first session); ignore it for journey status — `journey-history.json` after this baseline is authoritative.
- Reserved sim tickers currently registered: `SIM-BUYER`, `SIM-SELLER`, `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP`. `SIM-SHIFT` and `SIM-REVERSAL` (capability 21) are session deliverables, not yet present.
