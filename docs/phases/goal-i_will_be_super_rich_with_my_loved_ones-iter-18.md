# Goal Iteration 18 — Replay-study layer: runner + seeded null baseline + `/studies` page + pinned reference study (J-60/J-61/J-62)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 18
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-60, J-61, J-62
- **Required-still-passing journeys:** J-01, J-02, J-08, J-09, J-17, J-19, J-31, J-35, J-36, J-37, J-38, J-42, J-50, J-51, J-52, J-54, J-55, J-56, J-57, J-58, J-59 — plus every other journey currently `passing`/`already_passing` in journey-history.json; J-68 sentinel re-verified (new nav state: the Studies entry is now enabled — that is the ONLY permitted cockpit-adjacent pixel change).
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - "**No profitability or edge claims.** No currency P&L, equity curves, compounding, or win-rate-as-edge presentation anywhere. R statistics are journaled measurements and MUST always appear with their n, the abandonment bucket, the null baseline (where one applies), and the spread/R cost figure." *(critical)*
  - "**Source, feed, and config honesty.** Every research record MUST be stamped with its bound source, its `data_feed`, and a `config_fingerprint` over the entire frozen config; … analytics and studies MUST NOT pool across feeds or fingerprints; and SIP-derived research MUST NOT be presented as validating IEX-live behaviour without the explicit basis label." *(critical)*
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested)." *(critical)*
  - "**Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness."
  - "**No new indicators, no auto-tuning.** Confirmation rules, stances, hints, and studies MUST be composed from the EXISTING engine features and states only; research thresholds are config-owned research defaults calibrated against the sims/fixtures; no parameter optimizer, grid search, or automatic threshold fitting of any kind." *(critical)*
  - "**No scanning, no execution — still.** Theses and hints exist only on the one watched ticker; studies run only over explicitly chosen windows; there is no background or multi-symbol setup detection…"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do." *(critical)*
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass." *(critical)*
  - "**Persistence stays scoped to research records.** SQLite holds theses, verdict events, hints, actions, reviews, and study results only — no trades, quotes, candles, or feature series are persisted (committed test fixtures excepted)."
  - "**Real-data journeys are proven with real data.** … NOT done until an **automated test over committed, real captured market data** asserts the outcome and runs in CI **without** live credentials." *(critical)*

## GOAL

From a new, nav-enabled `/studies` page the user creates, monitors, cancels, and reads deterministic replay studies of the setup grammar over an explicitly chosen window — occurrence rows and aggregates reported **side-by-side with a seeded random-arm-time null baseline** — and a committed reference study over the iter-17 PG SIP fixture (plus the seeded sims) reproduces **exact pinned results in CI without credentials**, flipping J-60, J-61, and J-62 to passing.

## BACKGROUND

Iter-17 delivered the capability-34 engine performance gate goal.md explicitly gates studies on: truly incremental feature maintenance, byte-identical (zero re-pins), with the committed ≈10-minute real **PG SIP** fixture (`apps/backend/tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json`, 3,229 trades + 11,012 quotes, all five windows evict) replaying unpaced in ~10 s inside the config-owned `dense_replay_time_budget_seconds` budget. That fixture was committed deliberately as the capability-32 reference-study window — this iteration is its second consumer. The iter-17 evaluator's verdict was CONTINUE with an explicit **full-depth** recommendation for exactly this scope (multi-surface: new page + nav enablement + background jobs + first writes to the `studies`/`study_occurrences` tables).

This is the last evidence-layer step: when J-60–J-62 flip, the *Evidence before cues* gate (J-58–J-62 all passing) opens for the strictly-last cue layer (J-53, J-63–J-67) — which remains OUT of this iteration.

Lessons applied (state/lessons.md): **iter-17** (the study runner inherits the PG-fixture perf profile — ~10 s/replay dominated by `_window._refresh_rebuilds`, NOT the merge fallback; and the backend's pytest `addopts = "-q"` means an extra `-q` suppresses the count line — verify by exit code); **iter-16** (the persistent dev journal DB `apps/backend/tapeology_journal.db` is the multi-fingerprint substrate for browser-verifying never-pool stamps; serving-only config keys are excluded from `config_fingerprint` only WITH rationale + stability test + counter-test); **iter-4** (any `store.py` schema change needs a versioned migration + committed old-schema fixture, proven beyond temp-DB injection); **iter-6** (browser QA against a server started AFTER dev, canary-probed); **iter-2/3/14** (full-page, non-blank, scrolled-into-view captures — `/studies` is a brand-new below-the-fold-prone surface); **iter-15** (one absence-fallback copy string must not serve two distinct states — study statuses each get their own explicit copy); **iter-5** (diff the designed test plan against this spec's journey matrix; do not trust "complete" without artifacts).

## IN SCOPE

### Backend

- [ ] **Study runner — single owner module** (new, e.g. `apps/backend/app/research/studies.py`): runs the setup grammar over an explicitly chosen source + window as an **unpaced offline replay through a fresh `TapeEngine`** (the proven fixture-replay pattern of `test_real_data_classify.py` / `test_dense_replay_gate.py`), attaching ONLY via the existing observer seam. **NO change to any file under `app/engine/`, `app/providers/`** (or equivalent provider modules), **the classifier, the history buffer, or the chart core.** The runner is read-only over the engine; observer-equivalence (J-68 byte-identity) must stay green.
- [ ] **Study sources (three, all through existing seams):** (a) the **committed reference window** — the PG SIP fixture, loadable without credentials (this is the J-60 "the committed reference window works" leg and the CI leg); (b) the **seeded sim scenarios** (e.g. SIM-REVERSAL for absorption_reversal, SIM-BUYER/SIM-SHIFT for trend_continuation) replayed unpaced; (c) an **arbitrary symbol + past window** via the EXISTING historical fetch path unchanged (credentialed; failures surface the existing explicit error states — never fabricated data).
- [ ] **State-native auto-arming** for `absorption_reversal` and `trend_continuation`: arming rules composed ONLY of existing engine states/features (e.g. sustained matching absorption / sustained matching control), every threshold config-owned and **IN `config_fingerprint`**. Each armed occurrence then runs the EXISTING per-setup verdict rule tables (`app/research/verdict.py` semantics — no new rules, no new indicators) and records a per-occurrence verdict summary.
- [ ] **Level setups require a user-supplied level** (`level_break`, `failed_move_fade`): the study is stamped **`hindsight_level`**, labeled "level chosen with hindsight — illustrative", and **excluded from any cross-study aggregate** (enforced in code + test, even if no cross-study aggregate view ships this iteration). A level-setup study without a level is a **422, never a guess**.
- [ ] **Deterministic occurrence R definition (named design decision — document it):** auto-armed occurrences have no user-typed invalidation, so the study's R basis MUST be derived deterministically from existing engine values at arm time via a config-owned rule (e.g. a config spread-multiple distance on the adverse side of the arm price), identical between setup occurrences and null arms, documented as a research default — never fitted. R values and ternary outcomes MUST go through the existing single helpers (`app/research/marks.py::r_basis` + the `excursions.py` ternary/horizon machinery, `excursion_horizons_seconds`) — the study becomes a **registered consumer of the same formula, never a second one**.
- [ ] **Excursion measurement per occurrence:** confirmation/arm-anchored, per config horizon, first-touch in logical time; horizons cut short by window end are flagged **truncated and counted separately — never silently dropped, never extrapolated**.
- [ ] **Seeded random-arm-time null baseline:** `study_null_arm_count` (new config key, **IN fingerprint**) random arm times drawn from a **recorded seed** over the same window, same direction, same R definition, same horizons; the seed is persisted on the study record so the baseline reproduces exactly. Design note: a single replay pass should serve both setup arms and null arms (the observer records what each arm point needs in memory during the job) — N independent engine replays would blow the time budget; no tape data is persisted (in-job memory only).
- [ ] **Cancellable background jobs:** explicit status enum `queued | running | done | cancelled | failed` with progress while running; cancellation honored between events/chunks via `POST /research/studies/{id}/cancel`; a cancelled study resolves to explicit **cancelled** with partial results clearly marked partial (never presented as complete); a failed study (e.g. no data, provider error) surfaces an explicit error — **never an empty success**. The job MUST NOT block the live cockpit: replay runs off the event loop (worker thread/executor with cooperative yields), and all SQLite writes go through the existing single writer queue — never from event processing or WS serialization.
- [ ] **API (blueprint row 23, exactly these endpoints):** `POST /research/studies` (create + start; full validation: unknown setup/direction/source → 422; future or empty window → 422 or explicit failed status; level rules above), `GET /research/studies` (list), `GET /research/studies/{id}` (status/progress + stored results), `POST /research/studies/{id}/cancel` (404 unknown; 409 if already terminal). Results are **persisted once at their defining moments** (stamps at creation; occurrence rows + aggregates + baseline at completion/cancellation) and served VERBATIM — never recomputed at read; the UI computes nothing.
- [ ] **Honesty stamps + never-pool:** every study is stamped at creation with bound source, `data_feed`, `config_fingerprint`, and the baseline seed; nothing aggregates across `data_feed` or `config_fingerprint` (J-59 discipline); aggregates render with n and caveats; groups under the config minimum sample reuse the insufficient-sample honest-marker pattern (n always shown).
- [ ] **Committed reference study (the J-62 flip):** a committed test executes the reference study — PG SIP fixture window AND at least one seeded sim — **unpaced, in CI, without credentials**, asserting the **exact pinned occurrence rows + aggregates + null-baseline counts (byte-stable)** and completing within the config-owned time budget. Double-run determinism asserted (identical results for identical (source, fingerprint, seed)). Pin the key numbers in the dev handoff.
- [ ] **Schema:** the `studies` + `study_occurrences` tables already exist (v1 payload-blob shape) — first writes land here. **Prefer no `store.py` schema change (schema stays v7).** If a schema change proves unavoidable: a versioned **v8** migration + a committed v7 old-schema fixture + NO backfill (iter-4 lesson) — and say so in the handoff.
- [ ] **Config:** every new study value (null-arm count, arming thresholds/dwell, occurrence R-definition multiple) is a documented research default in `app/config.py` and **enters `config_fingerprint`** (they shape persisted results). Any genuinely serving-only key (e.g. a studies list page size) follows the iter-12/16 exclusion pattern: documented rationale + fingerprint-stability test + counter-test — never a bare exclusion.
- [ ] **Taxonomy/display copy (row 24, additive):** study status labels, the `hindsight_level` label, the truncated label (reuse), null-baseline caption, the journaled-measurements framing, and per-status honest-absence copy (each status distinct — iter-15 lesson) served by `GET /research/taxonomy`; the frontend hardcodes none.

### Frontend

- [ ] **Enable the Studies nav entry** (`apps/frontend/components/NavBar.tsx`: the pre-registered disabled `/studies` entry flips to enabled — the approved skeleton never carried a dead link; now the page exists).
- [ ] **`/studies` page (new route):** create form — source pick (reference-window quick-pick labeled as the committed SIP fixture; sim scenarios; symbol + past window reusing the existing symbol search + dd-MM-yyyy custom date input/shared formatter), setup × direction, manual level input shown only for level setups with the hindsight warning; **job list** with status/progress and a Cancel control; **results view** rendering stored results verbatim: occurrence rows, aggregates **side-by-side with the seeded null baseline** (the goal.md register, e.g. "setup: 8/13 `+1R_first`; random-time baseline: 41/100"), ternary outcomes, truncated counted separately, `hindsight_level` label where applicable, feed + fingerprint stamps visible, n + caveats, "Descriptive only — not trading advice" register — all copy from row-24 taxonomy. Dark instrument-panel style, mono numerics, loading/empty/error states per the design system.

### New user-facing capability
The user can run, monitor, cancel, and re-run deterministic replay studies of their setup grammar over chosen windows, and read honestly-framed results against a reproducible random-arm-time null baseline.

### New information displayed
Study list with status/progress; per-study results: occurrence rows (arm time, verdict summary, per-horizon ternary excursions, truncation flags), aggregates with n + caveats, the seeded null baseline side-by-side, the recorded seed, `hindsight_level` labels, feed + config-fingerprint stamps.

### New user actions
Create study (source/setup/direction/level), run, cancel, open results, re-run identical study.

### UI surface changes
New `/studies` page; the persistent nav's Studies entry becomes enabled (the only change visible from existing pages).

### Product surface delta
The evidence layer completes: Tapeology now validates the setup grammar against data instead of only journaling it — the last gate before the cue layer is allowed to exist.

### Blueprint conformance
The `/studies` page lands at its pre-registered home (nav section **Studies**, route `/studies`, blueprint IA + feature-home table row "J-60–J-62"). Enabling the nav entry is a **nav-skeleton change**: `blueprint.md` has been edited (iter-18 note) and `state/blueprint.reapproval-requested` written — the session pauses for human re-approval per protocol.

### Data-contract additions
No new contract row: **row 23 (Study results)** is the registered owner/endpoint set and this iteration builds it out — an additive build-out note registers the recorded seed, status enum, `hindsight_level` exclusion, and the persist-once moments. Row 24 gains the studies display copy additively. R/excursion values flow through the existing row-27/row-20 single helpers (registered consumers — never a second formula); no value already in the contract gains a second computation or serving path.

## OUT OF SCOPE

- The entire cue layer — J-53, J-63–J-67 (entry checklist/stance, freshness, hints + hint log, copy sweep, feed badge) — **strictly last**, only after J-58–J-62 all pass.
- `delivery_lag_seconds` (blueprint row 14, capability 22) — lands with the cue-layer freshness work (J-64), not here.
- Hint study-baseline citation (J-65) — cue layer.
- Any change to `app/engine/**`, the classifier, providers, sim scenarios, history buffer, observer seam, or snapshot shape; any re-pin of any engine value (byte-identity is mandatory; a needed semantics change is a stop-and-flag).
- Any change to journal analytics (row 21) or its endpoint — studies are a separate surface; no pooling of study results into `/research/analytics`.
- A cross-study aggregate/comparison VIEW (only the hindsight-exclusion discipline is enforced in code + test now).
- Parameter sweeps, optimizers, or multi-config studies — one frozen config, one fingerprint per study.
- Watchlists/scanning: studies run ONLY over explicitly user-chosen windows.

## DEFINITION OF DONE

- [ ] J-60 passes via browser-qa-agent: create → run (status/progress) → results with occurrence rows + aggregates side-by-side with the seeded null baseline, feed + fingerprint stamped; the identical re-run reproduces identical results (browser + unit-pinned).
- [ ] J-61 passes via browser-qa-agent: `hindsight_level` label on a manual-level study (+ exclusion test), truncated occurrences flagged and counted separately, cancel → explicit **cancelled** with partial-marked results (cancellation also unit-tested), a failing study → explicit error, never empty success.
- [ ] J-62 flips to passing: the committed reference-study test pins exact occurrence rows + aggregates (byte-stable) over the PG SIP fixture + a seeded sim, unpaced in CI without credentials, within the config-owned budget; the iter-17 engine-gate tests stay green untouched.
- [ ] Required-still-passing journeys remain green; J-68 sentinel re-verified in pixels (cockpit unchanged except the now-enabled Studies nav entry); observer-equivalence 7/7 green.
- [ ] No anti-goal violation introduced (no edge claims, no pooling, no prediction language, no fabricated data, no engine mutation).
- [ ] Full backend suite green (629+ tests, zero re-pins); frontend builds clean.
- [ ] Diff confinement holds: app-code changes only under `app/research/**`, `app/config.py`, routes wiring, and `apps/frontend/**` (reviewer verifies the file list; NO engine/provider/classifier/store-schema file unless the declared v8-migration path was taken).
- [ ] Blueprint updated (iter-18 note + row 23/24 build-out) and `blueprint.reapproval-requested` present for the nav-skeleton change.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-18-dev.md` (including the pinned reference-study key numbers and the documented occurrence-R design decision).

## TESTING REQUIREMENTS

- **Browser:** J-60 end-to-end on the reference-window quick-pick (create, watch status flip queued→running→done, open results, re-run identical → identical numbers in pixels + REST); J-61 legs (manual-level hindsight label; truncation flags; cancel a long-running study — a sim or long window — to explicit cancelled; a failing study shows an explicit error); nav: Studies entry enabled, `/studies` reachable in ≤2 clicks; J-68 sentinel spot-check (no-thesis SIM-BUYER cockpit). Discipline: full-page, non-blank, size-sane captures of the asserted elements; backend started AFTER dev with a canary probe (`GET /research/taxonomy` must contain the new studies copy — iter-6 lesson); use the persistent dev DB for multi-fingerprint stamp pixels (iter-16 lesson).
- **Unit/integration:** the pinned reference study (exact rows/aggregates/baseline counts, byte-stable, in budget, no credentials); double-run determinism for (source, fingerprint, seed); null-baseline seed reproducibility (same seed ⇒ identical arms; different seed ⇒ recorded + different); arming-rule tests on the seeded sims (deterministic occurrence counts); hindsight exclusion from cross-study aggregation; never-pool/stamp assertions; cancellation (mid-run cancel ⇒ cancelled + partial-marked, writer-queue intact); failure path (no data ⇒ failed + message); fingerprint tests (new study keys MOVE the fingerprint; any serving-only key has the stability + counter pair); observer-equivalence 7/7 + `test_dense_replay_gate.py` + full suite green; migration test against a committed v7 fixture IF (and only if) v8 was taken.
- **Error cases:** unknown setup/direction/source → 422; level setup without level → 422 (never a guessed level); future/empty/invalid window → 422 or explicit failed; cancel unknown id → 404; cancel terminal study → 409; arbitrary-window study without credentials → explicit unavailable error, never fabricated or fixture-substituted data.

## NOTES

- **Mandatory fallback for the open `qa_complete` harness defect** (full pipeline may halt after QA, skipping audit/ux-regression/closure): this iteration's completion claim MUST NOT depend on audit or closure artifacts existing. The **goal-evaluator MUST independently re-run**, regardless of which pipeline steps completed: the pinned reference-study test, the study determinism + seed-reproducibility tests, the never-pool/stamp + fingerprint tests, `test_observer_equivalence.py` (7/7), `test_dense_replay_gate.py`, and the full backend suite — and must open the `/studies` pixels (results + baseline side-by-side, hindsight label, cancelled status) plus the J-68 sentinel. If the harness hard-blocks before QA, complete lean-style (developer → reviewer → browser-qa) with the same evaluator re-runs.
- **Performance reality (iter-17 lesson):** one unpaced PG-fixture replay costs ~10 s, dominated by `_window._refresh_rebuilds` (bounded quote-remap re-walks), NOT the merge fallback — budget job runtimes and the CI pin accordingly, and check the rebuild counter first if replays slow down. Do NOT "fix" engine perf here — engine files are out of scope.
- **One replay, many arms:** the null baseline must come from the same single replay pass (in-memory observation), not N engine re-replays — otherwise the CI budget and cockpit responsiveness both lose. No tape data may be persisted in the process (committed fixtures excepted).
- **The occurrence-R design decision is the riskiest ambiguity** — the reviewer must check it is config-owned, deterministic, identical for setup and null arms, routed through `marks.py::r_basis`, and documented as a research default (never fitted to make results look good; that would be auto-tuning).
- **Copy register:** every studies string is descriptive, present-tense, measurement-framed — n and caveats always visible, never "edge", "win rate" as advice, no imperative. This page is the most edge-claim-prone surface in the product; the J-66 sweep will audit it later, but writing it clean now is cheaper.
- **pytest gotcha:** the backend's `addopts = "-q"` double-quiets if you pass `-q` again, suppressing the final count line — verify suites by exit code (iter-17 lesson).
- **Stall note for the evaluator:** three journeys are expected to flip (J-60, J-61, J-62). J-62 flips only when the pinned reference-study test exists, passes, and stays within budget — not on the runner merely working in the browser.
