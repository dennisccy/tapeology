# Goal Iteration 17 — Capability-34 engine performance gate (byte-identity-pinned, isolated)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 17
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes  *(NO frontend code changes — "yes" exists solely to force the browser-QA step to run the J-68 regression sentinel after the first engine touch of the session; see Frontend section)*
- **Target journeys:** J-62 (partial advance — the engine-performance-gate clause ONLY; J-62 CANNOT flip this iteration because its reference-study clause lands with J-60/J-61 next iteration)
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-17, J-19, J-31, J-36, J-37, J-42, J-58, J-59 — plus every other journey currently `passing`/`already_passing` in journey-history.json
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - "**Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness."
  - "**No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code."
  - "…every performance optimization MUST preserve correctness — **no fabricated or dropped trades/quotes, no recomputation outside the engine** (single source of truth holds)." *(from "Bounded, honest, performant vendor calls", critical)*
  - "**Real-data journeys are proven with real data.** A journey whose outcome depends on real market data … is NOT done until an **automated test over committed, real captured market data** asserts the outcome and runs in CI **without** live credentials." *(critical)*
  - "**The research layer is read-only over the engine.** … the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested)." *(critical)*
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass." *(critical)*
  - "**Persistence stays scoped to research records.** SQLite holds theses, verdict events, hints, actions, reviews, and study results only — no trades, quotes, candles, or feature series are persisted (**committed test fixtures excepted**)."

## GOAL

Make rolling-feature maintenance truly incremental across window evictions — byte-identical values, proven by a committed ≈10-minute real SIP fixture replayed unpaced inside a CI-gated time budget — so the replay-studies layer (J-60–J-62) can be built on an engine that demonstrably keeps up.

## BACKGROUND

This is the **first engine-touching iteration of the session** and the binding prerequisite for studies: goal.md capability 34 gates J-60–J-62 on "truly incremental feature maintenance — no per-event full-window rescans after evictions — with feature values byte-identical to before … a CI timing gate replays a committed dense fixture unpaced within a configured budget." The defect is precisely located: `apps/backend/app/engine/features.py::_Window` flips `self._refresh_incremental = False` **permanently** on the first trade OR quote eviction (`_evict`, ~lines 171–205), after which **every** `compute()` call serves `bid_refresh_score`/`ask_refresh_score` from `_refresh_fractions()` — a full forward-merge over the whole window — i.e. an O(window) rescan per event, quadratic on any stream longer than a feature window. All other aggregates (sums, impacts, large prints, spreads, reference price) are already incremental and need no change.

The iter-16 evaluator recommended depth **full** for this change class, preferring the gate scoped as its own byte-identity-pinned step before the J-60 runner — this spec takes exactly that shape. The known **full-pipeline `qa_complete` harness defect** (engine halts after QA; audit/ux-regression/closure may never run — iter-5 lesson, still open) is handled by the mandatory evaluator-side fallback in NOTES: this iteration's done-ness must NOT depend on the audit or closure gates having run.

Neither committed fixture can exercise the post-eviction regime on all windows (GME SIP fixture = 7 s; F fixture = 2 min; the 180 s/300 s windows never evict), so this iteration also commits the **≈10-minute moderate-density real SIP fixture** that goal.md capability 32 requires for the reference study anyway — one fixture, two consumers (this iteration's timing gate; next iteration's pinned reference study).

Lessons applied (state/lessons.md): iter-16 (a config key that never enters persisted computation is excluded from `config_fingerprint` only WITH a documented rationale + a stability test + a counter-test); iter-8 (named truth anchors must match actual test parameters — reviewer must diff them); iter-6 (browser QA must run against a server started AFTER dev completes, canary-checked); iter-4 (NO store.py schema change is permitted here — and none is needed); iter-2/3/14 (sentinel captures must be full-page/scrolled-into-view, non-blank, of the asserted surface).

## IN SCOPE

### Backend

- [ ] **Truly incremental refresh-score maintenance** in `apps/backend/app/engine/features.py::_Window`: remove the permanent post-eviction degradation so that on the **engine path** (trades carrying their in-effect `eff_bid`/`eff_ask`) `bid_refresh_score` and `ask_refresh_score` are maintained with amortized O(1) (or at worst O(log n)) work per event **including across trade and quote evictions** — no per-event full-window rescan once the window slides. The algorithm choice is the developer's (e.g. a monotonic-structure / two-stack sliding-window-aggregation approach), subject to the byte-identity constraint below.
- [ ] **Byte-identity to the CURRENT post-eviction semantics — non-negotiable.** The oracle is today's `compute()` output, which after any eviction equals `_refresh_fractions()`: a forward-merge using **only in-window quotes** (an in-window trade older than the oldest surviving quote gets no in-effect quote and is SKIPPED — it contributes no refresh evidence). The new incremental structure MUST reproduce **that** semantics exactly — NOT the append-time true-in-effect-quote semantics, which diverges once quotes evict (this divergence is precisely why the current code drops to the merge). If the developer concludes byte-identity is not achievable incrementally, they MUST stop and flag — the "justified and re-pinned as its own iteration" escape in capability 34 is explicitly NOT taken this iteration.
- [ ] **`_refresh_fractions()` is retained** as (a) the authoritative path for the standalone `FeatureEngine` API (no `eff_*` threaded — unchanged behavior, documented) and (b) the test oracle.
- [ ] **Committed dense fixture:** fetch and commit a **≈10-minute, moderate-density, real SIP** trades+quotes window (`apps/backend/tests/fixtures/alpaca/`), via the existing vendor adapter's bounded/chunked fetch (credentials available at dev time only; CI consumes the committed file). Requirements: real SIP data (never IEX — single-venue spreads are garbage for this purpose); window length comfortably > the 300 s longest feature window so **all five windows evict**; density moderate (choose symbol/time-of-day so the committed file stays within a sane repo budget — target well under ~25 MB); provenance documented in the fixture/test docstring (symbol, exact UTC window, feed, fetch date). This fixture is deliberately the one capability 32's reference study will reuse next iteration.
- [ ] **CI timing gate test:** a committed test replays the new dense fixture **unpaced through a fresh full `TapeEngine`** (the proven fixture-replay pattern of `test_real_data_classify.py` — the same path the study runner will use) and asserts wall-time < a **config-owned budget**, running in CI without credentials. Budget calibrated with documented headroom (e.g. ≥5× the measured time on the dev machine — generous enough not to flake, far below the minutes the O(n²) path costs).
- [ ] **Structural no-rescan test:** during the dense-fixture replay on the engine path, count invocations of the merge fallback (`_refresh_fractions`) after evictions have begun and assert the count is zero (or a strictly bounded constant if the chosen design has a justified, documented bounded fallback) — the complexity claim is pinned structurally, not only by timing. The test MUST also assert evictions actually occurred during the replay (guard against a silently too-short fixture).
- [ ] **Oracle-equivalence test:** over the dense fixture AND at least one seeded sim scenario, assert at every compute (or a dense sampled subset that provably includes many post-eviction ticks) that the incremental `bid_refresh_score`/`ask_refresh_score` **exactly equal** (`==`, never approx) the `_refresh_fractions()` oracle on identical window contents.
- [ ] **Pinned regression anchors:** commit exact final feature values (at minimum the refresh scores, impacts, ratios) from the dense-fixture replay as equality-pinned assertions, per the `test_real_data_classify.py` standard.
- [ ] **Config:** new key for the replay time budget (e.g. `dense_replay_time_budget_seconds`) in `app/config.py` as a documented research/CI default — **excluded from `config_fingerprint`** with the iter-12/iter-16 discipline: documented rationale comment (a CI gate value never enters persisted computation; fingerprinting it would dishonestly fragment analytics pools) + a fingerprint-stability test (changing it does NOT move the fingerprint) + the counter-test (a real classifier threshold still DOES).
- [ ] **Whole existing suite stays green** — in particular `test_features.py`, the progressive-vs-single-shot determinism test, `test_observer_equivalence.py` (7/7), `test_real_data_classify.py` (5 pinned), `test_real_data_gate.py` (35), `test_scenario.py`.

### Frontend

- [ ] **No frontend file changes.** `Frontend Present: yes` exists ONLY so browser QA runs after the engine touch. Browser scope: the **J-68 regression sentinel** (watch `SIM-BUYER` with no thesis declared — cockpit panels, chart + markers, observations, event log, confidence all behave identically; full-page captures per iter-3/iter-14 capture discipline) and a **J-08 REST == UI spot check**. The backend serving these captures MUST be started after dev completes, with a canary check (iter-6 lesson).

### New user-facing capability
None — by design. This iteration's user-facing acceptance is the **negative assertion**: nothing visible changes. (UI-evolution audit note: the backend adds no user-facing capability — a performance gate is not a capability the UI could expose; do not flag UI-FAIL for "backend changed but UI did not".)

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
Invisible now, foundational next iteration: the engine demonstrably sustains dense real-tape replay (CI-proven), unblocking the `/studies` surface (J-60–J-62) that goal.md gates on this work.

### Blueprint conformance
No new surfaces, routes, or nav changes. The disabled Studies nav entry stays disabled (its page lands with J-60). An additive iter-17 build-out note is appended to `blueprint.md` (no skeleton change, no reapproval needed).

### Data-contract additions
None. No new displayed value; no contract row changes owner or endpoint — rows 1–2 (`TapeStateClassifier`, `FeatureEngine`) keep their owners and their byte-identical outputs. The dense fixture and the time-budget config key are test/CI assets, registered in the blueprint's iter-17 note.

## OUT OF SCOPE

- The J-60/J-61 study runner, studies API (`POST/GET /research/studies` …), background jobs, null baseline, and the `/studies` page — next iteration, on top of this gate.
- The pinned **reference study** itself (the other half of J-62) — lands with the runner.
- `delivery_lag_seconds` (blueprint row 14, capability 22) — feeder/serialization work, NOT part of the capability-34 gate; lands with the studies/live-honesty work.
- All cue-layer work (J-53, J-63–J-67) — **strictly last**, gated on J-58–J-62 passing.
- Any `app/research/store.py` change (schema stays **v7**; no migration).
- Any change to `classifier.py`, thresholds, window lengths, sim scenarios, providers, history buffer, observer seam, or snapshot shape.
- Any re-pinning of feature values — byte-identity is mandatory this iteration; a semantics change is a stop-and-flag, never a silent re-pin.

## DEFINITION OF DONE

- [ ] Post-eviction engine-path refresh maintenance is incremental: structural no-rescan test green (with its evictions-actually-occurred guard).
- [ ] Byte-identity proven: oracle-equivalence test green (exact `==`); full backend suite green including observer-equivalence 7/7, `test_real_data_classify.py` + `test_real_data_gate.py` pins, progressive-vs-single-shot determinism; pinned dense-fixture anchors committed.
- [ ] CI timing gate green: ≈10-min real SIP fixture committed with documented provenance; unpaced full-`TapeEngine` replay completes within the config-owned budget, in CI, without credentials.
- [ ] Config budget key documented + fingerprint-exclusion rationale + stability test + counter-test all present (iter-16 lesson pattern).
- [ ] Browser sentinel: J-68 (no-thesis SIM-BUYER cockpit identical) and J-08 (REST == UI) re-verified in non-blank, full-page pixels against a post-dev server.
- [ ] Required-still-passing journeys remain green; no anti-goal violation introduced.
- [ ] No store.py / schema / classifier / provider / frontend file in the diff (reviewer verifies the diff file list).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-17-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-68 regression sentinel (SIM-BUYER, no thesis: panels, chart + Control marker, observations, event log, confidence); J-08 REST-vs-UI agreement spot check. Full-page captures, scrolled into view, non-blank (size-sanity per iter-14 lesson).
- **Unit/integration:** the structural no-rescan counter test; the oracle-equivalence test (dense fixture + ≥1 sim scenario, exact equality, provably covering post-eviction ticks); pinned dense-fixture final-value anchors; the CI timing gate; fingerprint stability + counter-test pair; entire existing suite (607+ tests) green.
- **Error cases (byte-identical to oracle in each):** empty window; trades before the first quote (no in-effect quote ⇒ no refresh evidence, never fabricated); quote-only and single-trade windows; the eviction boundary (oldest trade's `impact_delta` removal unchanged); a quote eviction that strips an early in-window trade of its in-effect quote (the trade must STOP contributing refresh evidence, exactly as the merge oracle does).

## NOTES

- **Mandatory fallback for the open `qa_complete` harness defect (full pipeline may halt after QA, skipping audit/ux-regression/closure):** this iteration's completion claim must NOT depend on audit or closure artifacts existing. The **goal-evaluator MUST independently re-run**, regardless of which pipeline steps completed: the full backend suite, `test_observer_equivalence.py`, the new oracle-equivalence + structural no-rescan + timing-gate tests, and the fingerprint stability/counter pair — and must open the J-68/J-08 sentinel pixels. If the harness instead hard-blocks mid-pipeline before QA, fall back to completing the iteration lean-style (developer → reviewer → browser-qa) with the same mandatory evaluator re-runs.
- **The byte-identity trap to watch (reviewer attention):** the engine path stores the append-time true in-effect quote per trade, but the post-eviction oracle (`_refresh_fractions`) computes in-effect quotes from **in-window quotes only** — the two genuinely disagree once quotes evict. Matching the oracle, including its skip-when-no-surviving-quote quirk, is the requirement. A "cleaner" semantics is a different iteration's decision, never this one's.
- **Truth-anchor discipline (iter-8 lesson):** the reviewer/evaluator must read the new test files and confirm assertions are exact equality over states that actually include evictions — not approx-equality, not pre-eviction-only coverage, not a handoff claim.
- **Fixture fetch:** use the SIP feed and the existing bounded/chunked adapter paths (the unbounded-fetch hang is a known gotcha). If credentials are genuinely unavailable at dev time, STOP and flag — do not substitute synthetic or looped data for the committed fixture (anti-goal: real-data journeys are proven with real data).
- **Stall-risk note for the evaluator:** no journey can flip this iteration by design (J-62's other half needs the J-60 runner). This is one deliberate no-flip iteration, not a stall; J-60 targets next.
