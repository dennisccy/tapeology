# Goal Iteration 20 — Cue layer begins: the holding-period management stance on the thesis strip (J-53)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 20
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-53
- **Required-still-passing journeys:** J-38, J-42, J-43, J-44, J-50, J-52, J-54, J-56, J-08 — plus every other journey currently `passing`/`already_passing` in journey-history.json. The J-68 idle-strip sentinel (cockpit with no thesis unchanged) must be re-spot-checked because this iteration touches the thesis strip.
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - "**No unsolicited or unconditional trade commands.** Every actionable cue MUST be gated on a user-declared thesis with an invalidation, rendered as named checks with margins and evidence, in present-tense descriptive language. No imperative buy/sell/enter/exit wording, no price targets, no certainty language — anywhere. A hint is a logged description of a forming pattern, never a command and never a thesis by itself." *(critical)*
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do." *(critical)*
  - "**No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect." *(critical)*
  - "**No profitability or edge claims.** No currency P&L, equity curves, compounding, or win-rate-as-edge presentation anywhere. R statistics are journaled measurements and MUST always appear with their n, the abandonment bucket, the null baseline (where one applies), and the spread/R cost figure." *(critical)*
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed." *(critical)*
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect." *(critical)*
  - "**Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned." *(critical)*
  - "**No new indicators, no auto-tuning.** Confirmation rules, stances, hints, and studies MUST be composed from the EXISTING engine features and states only; research thresholds are config-owned research defaults calibrated against the sims/fixtures; no parameter optimizer, grid search, or automatic threshold fitting of any kind." *(critical)*
  - "**No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape." *(critical)*

## GOAL

While holding a journaled position (an entry-marked, unresolved thesis), the thesis strip answers "does the tape still support this position?" — the **management stance** (`thesis_intact | thesis_weakening | thesis_invalidated`) derived from the same published verdicts, with live distance-to-invalidation ($ and R) and open R in mono, in factual, never-imperative copy (J-53).

## BACKGROUND

Iter-19 flipped J-60/J-61 to passing on evaluator-opened pixels, so **the Evidence-before-cues gate (J-58–J-62 all passing) is now OPEN** — the strictly-last cue layer may begin. The evaluator's recommendation is J-53 and/or J-63 at the `/` thesis strip (blueprint row 25), one cue surface per iteration. This iteration takes **J-53 alone**: the management stance is the smallest honest first cue — it is a pure derivation from the row-16 published verdicts plus the row-27 R basis, needs **no** `delivery_lag_seconds`, no named-check margin machinery, and no freshness states (those land with J-63/J-64). The entry checklist is deliberately deferred so its delicate honesty constraints (live margins, `no_fresh_tape`, nearest-counterevidence, its own dwell) get a dedicated iteration.

Depth stays **lean** per the evaluator: the FULL-pipeline `qa_complete` harness halt remains open upstream; the lean cycle (developer → reviewer → browser-qa) is the proven path.

Lessons applied (state/lessons.md):
- **iter-1:** SIM-SHIFT's phase 2 arrives after ~60 s of logical time at live pacing — browser QA must budget for the weakening/invalidation legs; the append-only event log / verdict timeline carries sequence claims if a transient frame is missed.
- **iter-5:** stance captures are time-critical — a sim thesis auto-expires at scenario end; capture the strip AT each asserted stance moment, before teardown.
- **iter-7/iter-8:** any change near verdict/statement semantics demands four-quadrant proof (favorable + adverse tape × long + short) with the spec's named anchor values actually present in test parameters — the stance mapping and the open-R sign convention both get this treatment.
- **iter-10:** declare the invalidation within/near the visible candle range or the chart price-line may sit off-scale in captures (the geometry itself is not in scope here, but J-53's frames include the chart).
- **iter-11:** sim-calibrated thresholds are razor-thin — time the declare with a REST polling loop, not a sleep.
- **iter-15:** one absence-fallback string must not cover two causes — "no stance because no entry mark" vs "no live readout because the monitor is not evaluating (surviving thesis)" need distinct honest copy.
- **iter-19:** the frontend must never pre-empt backend authority with client-side courtesy logic — the strip renders the projection's stance/numbers **verbatim** and computes nothing.
- **iter-2/iter-6/iter-18:** no `npm run build` into the live dev server's shared `.next` before browser QA; restart both servers after dev completes and canary-probe code identity before any capture — `GET /research/taxonomy` carrying the NEW management-stance display copy is this iteration's perfect canary.

## IN SCOPE

### Backend
- [ ] **Management-stance evaluator (blueprint row 25, stance half)** — a single-owner module under `apps/backend/app/research/` (suggested `stance.py`), driven per event by the existing research monitor (observer-only; engine untouched). It derives the stance **exclusively from the latest published row-16 verdict** of an **entry-marked, unresolved** thesis: `confirming → thesis_intact`; verdict decay (`weakening`/`rejecting`) → `thesis_weakening` carrying the verdict's plain-language evidence; `invalidated` (the J-44 auto-resolve) → `thesis_invalidated` (terminal display, evidence = the offending-print facts, e.g. "invalidation level traded"). The full five-verdict mapping is a backend-owned table; the `pending` case (entry while pending — the J-54 scenario) must read honestly and MUST NOT render `thesis_intact` without a published confirmation — its evidence names the actual verdict.
- [ ] **Stance dwell** — the stance publishes through its own config-owned, logical-time dwell (no per-tick flapping), EXCEPT `thesis_invalidated`, which is dwell-exempt (mirrors the hard invalidation trigger). New config key (e.g. `management_stance_dwell_seconds`) documented as a research default — no magic numbers. The stance is never persisted, so the key qualifies as serving-only: if excluded from `config_fingerprint`, follow the codified iter-12/16 pattern (documented rationale comment + fingerprint-stability test + counter-test that a real threshold still moves the fingerprint).
- [ ] **Live position readouts (row 27 consumer #5)** — inside the SAME single `build_projection` (`apps/backend/app/research/monitor.py`), additive keys: `management_stance` (value + evidence + published-at), `distance_to_invalidation` (in $ and in R), `open_r` (the current open move in R, signed by direction with the SAME sign convention as `marks.py`'s realized move). R basis MUST come from the existing `r_basis()` in `apps/backend/app/research/marks.py` — the stance becomes its fifth registered consumer; never a second formula.
- [ ] **Honest presence rules** — the stance/readout keys are present ONLY while the thesis is entry-marked AND unresolved AND a live monitor is evaluating; `thesis_invalidated` renders at/after the auto-resolve moment as the terminal stance treatment. The surviving not-evaluated path (row 15 iter-9: unwatched / mismatched source) carries NO live numbers and NO frozen-stale stance — its existing not-evaluated notice stays, with absence copy distinct from "no entry mark yet" (iter-15 lesson).
- [ ] **REST = WS verbatim** — the additive keys flow identically through `GET /research/thesis/active` and the WS `thesis` key (the existing single-projection invariant; no new endpoint).
- [ ] **Display copy via taxonomy (row 24)** — stance labels, evidence templates, and the two distinct absence copies are served additively by `GET /research/taxonomy`; the frontend hardcodes none. All copy is present-tense, factual, thesis-attributed — never imperative, never predictive.
- [ ] **No persistence change** — stances are live cues, not records: schema stays **v7**, `verdict_events` untouched, no store.py change.

### Frontend
- [ ] **ThesisStrip.tsx — management-stance block**: when the active projection carries the stance keys, the strip's holding-period view shows the stance label in the established palette (`thesis_intact` emerald, `thesis_weakening` amber, `thesis_invalidated` rose with the terminal treatment), its evidence line, and the live **distance-to-invalidation ($ and R)** plus **open R** in `font-mono`. All values render verbatim from the projection — zero client-side arithmetic, zero client-side stance derivation.
- [ ] Without the stance keys, the strip is pixel-identical to today (declare affordance / verdict view / resolved view unchanged — the J-38/J-42/J-50 surfaces).
- [ ] Open R / distance copy carries the journaled-measurement register (consistent with the existing realized-R label discipline); the "Descriptive only — not trading advice" register extends to the stance block.

### New user-facing capability
While holding a journaled position, the user sees at a glance whether the tape still supports it — `thesis_intact` / `thesis_weakening` / `thesis_invalidated` with evidence — instead of mentally re-deriving it from the raw verdict.

### New information displayed
The management stance + evidence; live distance-to-invalidation in $ and R; open R — on the thesis strip, only while entry-marked and unresolved.

### New user actions
None. The stance is display-only; existing declare/mark/resolve controls are unchanged. Nothing blocks, nothing commands.

### UI surface changes
One surface: the thesis strip on `/` gains its holding-period (entry-marked) state block. No new page, no nav change, no hint dock, no checklist.

### Product surface delta
The first decision-support cue ships on the evidence layer that now backs it: the holding-period read promised by Product Shape ("…or the holding-period management stance") becomes real, in the same honest register as every research surface before it.

### Blueprint conformance
The stance renders at its registered canonical home — the `/` thesis strip, nav section **Cockpit** (blueprint feature-home row "J-38–J-46, J-49, J-50, J-52, **J-53** … `/` thesis strip"). No new routes; no nav-skeleton change; no re-approval needed.

### Data-contract additions
No new contract row. This builds out the **management-stance half of existing row 25** (stance evaluator, computed once server-side, publishes through its own dwell, served via row 15's projection as additive keys), with additive notes registered in `blueprint.md`: row 25 (build-out), row 27 (stance distance/open-R = fifth registered consumer of the single `r_basis()`), row 24 (stance display copy), and the config list (stance dwell). The stance reads row-16 published verdicts and row-18 marks from their registered owners — no value is recomputed or served via a second path.

## OUT OF SCOPE

- **J-63/J-64 — the entry checklist**: named checks with live margins, `feed_live`/`tape_lag_ok`, `delivery_lag_seconds` (blueprint row 14, still unbuilt by design), nearest-counterevidence, `no_fresh_tape` freshness, the checklist's own dwell — the next cue iteration.
- **J-65 hints** (hint dock, hint log, baseline citations), **J-66 copy sweep**, **J-67 live feed badge**, and the optional sound cue (defaults OFF — not built at all yet).
- Any engine/provider/classifier/history-buffer/chart-core change; any `store.py` schema change (stays v7); persisting stances or live readouts anywhere.
- Any new endpoint, page, route, nav change, or dependency.
- The long-tail J-01–J-37 partials gating the J-68 full flip — separate, later effort.
- Re-pinning any test value (the observer-equivalence and byte-identity pins must hold as-is).

## DEFINITION OF DONE

- [ ] Target journey J-53 passes via browser-qa-agent on SIM-SHIFT with evaluator-openable, non-blank, full-page (or scrolled-into-view) captures at EACH stance moment: `thesis_intact` (entry-marked while confirming) → `thesis_weakening` (verdict decay, with evidence) → `thesis_invalidated` (invalidation prints, auto-resolve per J-44) — distance-to-invalidation ($ and R) and open R visible in mono throughout the active legs.
- [ ] Required-still-passing journeys remain green (browser spot-checks: J-52 marks flow, J-38 declare/idle strip, J-68 idle-strip sentinel; suite-level: verdict journeys J-40–J-46 untouched-by-pins).
- [ ] No anti-goal violation introduced — in particular: no imperative/predictive copy anywhere in the new strings (copy-lint), no naked stance (evidence always attached), no engine mutation (observer-equivalence suite green, zero re-pins).
- [ ] Backend suite passes (`cd apps/backend && .venv/bin/python -m pytest tests/` — verify by exit code, not an extra `-q`); frontend builds (`npm run build` only AFTER browser QA, or with an isolated dist dir).
- [ ] REST `GET /research/thesis/active` and the WS `thesis` frame carry the stance keys byte-identically (J-08 discipline).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-20-dev.md`.

## TESTING REQUIREMENTS

**Preconditions (mandatory before any capture):** fresh backend + frontend starts AFTER dev completes; canary-probe `GET /research/taxonomy` for the NEW management-stance copy (proves server code identity — iter-6 lesson); no production build into the shared `.next` before captures complete (iter-2/18 lesson); diff the executed plan against this journey-leg matrix (iter-5 lesson).

- **Browser (J-53 on SIM-SHIFT, per the goal.md steps):**
  1. Watch `SIM-SHIFT` (Simulated); during the control phase declare **trend_continuation / long** with the invalidation just below the late-control price (inside the coming chop band) — time the declare via a REST polling loop on the snapshot (iter-11), not a sleep.
  2. **Mark an entry while confirming** → the strip switches to the management stance: capture `thesis_intact` (emerald) with distance-to-invalidation ($ and R) and open R in mono.
  3. Through the phase shift (~60 s real time — budget for it, iter-1) → capture `thesis_weakening` (amber) with evidence; the verdict timeline / event log carries the sequence claim if a transient frame is missed.
  4. When the band prints through the invalidation → auto-resolve (J-44) → capture `thesis_invalidated` (rose, terminal) with factual copy ("invalidation level traded" register — no instruction).
  5. REST cross-check at step 2 or 3: `…/thesis/active` stance keys equal the WS frame verbatim.
  6. Honest-absence legs: (a) an active thesis with NO entry mark shows no stance block and no live readouts (verdict view unchanged); (b) regression spot-checks — J-52 mark flow, J-38 declare, J-68 idle strip.
- **Unit/integration:**
  - Stance mapping for ALL five published verdicts, including the honest `pending` case (entry before confirmation never reads `thesis_intact`).
  - Dwell behavior: a verdict flip publishes the stance only after the configured dwell (no per-tick flapping); `thesis_invalidated` is dwell-exempt.
  - Distance-to-invalidation and open R computed via `marks.py::r_basis()` (registered-consumer assertion — one formula), with **four-quadrant sign proof** (long + short × favorable + adverse last), asserting exact values in test parameters (iter-8 lesson).
  - Presence rules: keys absent without an entry mark; absent on the surviving not-evaluated path (no frozen stance, distinct absence copy); terminal `thesis_invalidated` present at the auto-resolve moment.
  - REST-vs-WS projection equality including the new keys; observer-equivalence suite still byte-identical; full suite exit 0 with zero re-pins.
  - Copy-lint over the new taxonomy strings: no imperative trade words (buy/sell/enter/exit/should), no prediction/certainty language (J-66 preparation).
  - Config: stance dwell config-owned; if excluded from `config_fingerprint` — rationale comment + stability test + counter-test (iter-16 pattern).
- **Error cases:** no new endpoints, so no new 4xx surface — but verify the stance never blocks or alters existing flows: marking entry/exit, resolve, and the J-44 auto-resolve behave exactly as before with the stance attached (the stance is read-only over the verdict stream, as the research layer is over the engine).

## NOTES

- **Why J-53 alone:** the evaluator's "one cue surface per iteration" rule. J-63's checklist carries the heaviest honesty machinery in the goal (live margins in own units, `no_fresh_tape`, nearest-counterevidence, its own dwell, row 14 `delivery_lag_seconds`) and deserves an undiluted iteration — recommended next (iter-21), then J-64 freshness, then J-65 hints, with J-67's feed badge as a small companion somewhere in that run and the J-66 sweep last.
- **Stance is a derivation, not a record:** nothing about it is persisted; the journal-integrity anti-goal is satisfied by construction (timelines untouched, schema v7). If the developer finds any need to persist stance history, STOP — that is out of scope and would need a new contract registration.
- The known FULL-pipeline `qa_complete` harness halt is still open upstream — lean depth keeps this inside the proven lean cycle. Restore full depth for the J-63 iteration if the harness defect is fixed by then (the evaluator explicitly wants audit + ux-regression scrutiny on the cue layer).
- Blueprint: additive edits only this iteration (row 25/27/24 build-out notes + IA iter-20 note + config note) — no skeleton change, no re-approval marker.
- Evaluator note: judge the three stance moments on opened pixels (iter-3/14 discipline); the weakening→invalidated sequence may legitimately lean on the append-only timeline if a transient frame is missed (iter-1 fallback) — but `thesis_intact` and `thesis_invalidated` end-states must be in pixels.
