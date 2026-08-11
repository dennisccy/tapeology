# Goal Iteration 4 — The continuation family: JBE, DBI, cup-and-handle (J-04)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior ESCALATE: iter-3's verdict (`runs/goal-session-playbook/iter-3/eval.md`)
  was `ESCALATE` because a deep-planned iteration ran fast (no auditor) right before new detection
  math lands — the exact class of change where iter-1's auditor caught a fabricated opening range
  that 42 unit tests, review, and QA all missed. This alone is mandatory full depth; it also
  independently satisfies trigger 1 (structural/cross-cutting — new detectors span
  `desk_playbook_detect.py` + `desk_playbook_features.py` (shared consolidation-range/vertical-move/
  swing-pivots primitives reused, not reforked) + `desk_playbook.py` (parameters/signature/
  compute-walk wiring) + `apps/frontend/lib/types.ts`/`app/desk/page.tsx` (new per-setup geometry
  rendering) + two new structural guard tests, none of it covered by any single existing journey's
  test).
- **Frontend Present:** yes
- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-02, J-03, J-10
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
    tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
    fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
    imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
    research artifact.
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **Era-B desk anti-goals that remain binding:** membership is never a signal; snapshots are
    append-only and pinned; every run is an explicit operator act; the briefing describes, never
    advises; no new statistics, gates, or strategies; the demolition stays demolished; the ledger
    never holds orders; the suite stays keyless and hermetic; the fingerprint pin does not move.
    *(all critical)*
  - **No threshold exists outside the spec, and no code path sweeps one.** Every detector rule and
    threshold exists in [`docs/playbook-detector-spec.md`](../playbook-detector-spec.md) BEFORE the
    code that uses it; no code path iterates thresholds against outcomes (source-scan
    guard-tested); a threshold change is a spec revision + new signature, never an edit of recorded
    signals and never a sweep. *(critical)*
  - **A signal is an observation, not a call.** No signal, chip, or evidence cell uses advice,
    imperative, prediction, probability, expectancy, edge, or significance language; the served
    registers state what was NOT measured (no fills, no costs, returns not stop-adjusted);
    `invalidation_price` is geometry, never an order concept. *(critical)*
  - **No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1.** New
    signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never
    overwritten; the store exposes no update or delete method (source-scan guard-tested).
    *(critical)*
  - **No second implementation of the measurement rail.** Measurement helpers are imported from
    `desk_forward.py` with a zero diff to that file; no playbook module re-implements horizons,
    MDD, truncation, or the seed discipline (import-graph guard-tested). *(critical)*

## GOAL

The project owner runs the Playbook on a session and now sees not just opening-range breaks but
the book's continuation family — jump-base-explosion, drop-base-implosion, and cup-and-handle —
detected on the same recorded bars, measured on the same rail, and rendered legibly in the same
`/desk` Playbook Signals section.

## BACKGROUND

Per the priority rubric: nothing regressed (rule 1 n/a), no coherence-audit FAIL is on file (rule
2 n/a — no `coherence.md` exists yet for this session), and J-04 is the iter-3 evaluator's explicit
next-step recommendation and the natural dependency-order pick (`docs/goal.md`: "the detector
families J-04/J-05/J-06 (each lands visibly on the J-03 section)") — the smallest well-scoped unit
among the three remaining families since JBE/DBI are an exact long/short mirror pair sharing one
implementation, and cup-and-handle is long-only. Depth is `full`, mandatory per the prior `ESCALATE`
verdict (trigger 3) — the iter-3 evaluator's own stated reason was that this exact class of work
(new detection math) needs the auditor, having caught a fabricated opening range in iter-1's
otherwise fully-tested code.

**Two lessons apply directly and are binding on this iteration's design:**
- *iter-1 lesson (positional slot indexing fabricates data on gapped sessions)* — `consolidation_range`,
  `vertical_move`, and `swing_pivots` already exist as shared primitives (`desk_playbook_features.py`);
  JBE/DBI/cup-and-handle formation windows must read them by explicit bar-count/pivot-confirmation
  logic, never by positional slicing that assumes a contiguous session.
- *iter-2 lesson (the baseline-anchor seed-collision fix)* — iter-3 already shipped the seed-collision
  fix ahead of need (`side_sign` consolidation + a per-firing discriminator in the baseline draw).
  JBE is the FIRST detector that can fire twice per symbol-session (`PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION
  = 2`, the ladder-step cap) — this iteration is what actually exercises that fix for the first time
  and must prove it draws independent, non-colliding anchors for a real two-firing JBE fixture, not
  just a synthetic collision test.
- *iter-3 lesson (headless Chrome blanks on deep `scrollTo` at `/desk`'s current height)* — the
  browser evidence for this iteration's three new setups (which render inside the ALREADY-VISIBLE
  Playbook Signals section, not a new deep section) should not need the sibling-collapse technique,
  but the carried "re-take the lower Desk sections" item below does.

**Three items carried from iter-3's next-step recommendation ride inside this same cycle:**
1. Delete the stray browser-QA fixture record left in the operator's real store
   (`apps/backend/.data/playbook/playbook-2026-08-04-e0f249f57785.json`, git-ignored,
   self-disclosing as a TC-5 fixture) and scope every browser-QA plant/compute this iteration (and
   going forward — document in the dev handoff) to `TAPEOLOGY_DESK_PLAYBOOK_DIR` +
   `TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`/`_BACKSCAN_LOG_DIR` scratch paths, per the era-5B scoped-keyless
   recipe this session's own lessons.md already names.
2. Settle in writing whether the page's already-served `playbook_input_signature` counts as the
   goal's "parameters hash" on the provenance line, before J-07/J-08 reuse the same line — a
   documentation-only edit to `docs/playbook-detector-spec.md` §0 (the iter-2 B3/B4 pattern: catch
   the spec up to a call already made and defensible, zero behavior change, zero new field).
3. Re-take the lower `/desk` section screenshots (J-10's regression walk) using the documented
   sibling-`display:none`-collapse technique (iter-3 lesson) rather than a blind deep `scrollTo`.

## IN SCOPE

### Backend

- [ ] `desk_playbook_detect.py`: implement `jbe` (jump-base-explosion, long) per spec §3.3 — base
  via `consolidation_range` (`PLAYBOOK_BASE_MIN_BARS`..`PLAYBOOK_BASE_MAX_BARS`,
  `base_range ≤ PLAYBOOK_BASE_MAX_RANGE_MBR·MBR`), jump gate over `PLAYBOOK_JUMP_LOOKBACK_BARS`
  (`jump ≥ PLAYBOOK_JUMP_MIN_MULT·base_range` AND `≥ PLAYBOOK_JUMP_MIN_MOVE_MBR·MBR`), near-extreme
  gate (`PLAYBOOK_NEAR_EXTREME_MBR`), the volume-contrast gate (jump-bar RVOL vs base-bar RVOL,
  `PLAYBOOK_VOL_CONTRAST_RATIO`), trigger on first bar `high > U`, invalidation `L −
  0.30·(U − L)`, cap `PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION` (2) per side with a second base
  required to start after the first trigger bar, principles `["P3", "P4"]`.
- [ ] `desk_playbook_detect.py`: implement `dbi` (drop-base-implosion, short) as the exact mirror of
  `jbe` per spec §3.4 — same primitives, gates, and cap, direction-flipped.
- [ ] `desk_playbook_detect.py`: implement `cup_handle` (long only) per spec §3.6 — left/right rims
  via `swing_pivots` (confirmed strictly before the trigger bar, within `PLAYBOOK_RIM_MATCH_MBR` of
  each other and of session-high-so-far), cup depth ≥ `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR·MBR`,
  duration ≥ `PLAYBOOK_CUP_MIN_BARS` (disclose `cup_optimal` at `PLAYBOOK_CUP_OPTIMAL_BARS`), cup
  volume contrast (middle-third vs outer-thirds RVOL medians, `PLAYBOOK_VOL_CONTRAST_RATIO`), handle
  retrace ≤ `PLAYBOOK_HANDLE_MAX_RETRACE_FRAC` of cup depth, handle duration ≤
  `PLAYBOOK_HANDLE_MAX_DURATION_FRAC` × cup duration (disclose `handle_duration_desirable` at 25%),
  handle volume contrast (handle RVOL vs outer-thirds RVOL median); trigger on first bar after ≥ 1
  handle bar with `high > max(left_rim_high, right_rim_high)`; invalidation
  `handle_bottom − 0.30·(T − handle_bottom)`; cap 1 per symbol-session; principles `["P4", "P5-inverse"]`.
  A handle that retraces beyond 50% of cup depth voids the formation silently (it may still fire as
  a different detector's independent hypothesis, per spec §4's overlap policy — no cross-detector
  suppression).
- [ ] `desk_playbook.py`: wire all three new detectors into the compute walk beside
  `detect_opening_range_breaks`; extend `PLAYBOOK_SETUPS` to `("open_high_break", "open_low_break",
  "jbe", "dbi", "cup_handle")`; the new constants join `playbook_parameters()`'s embedded blob so
  `playbook_input_signature` moves for every future compute (expected, disclosed) while every
  already-recorded J-01/J-02/J-03-era file stays byte-identical (proven by SHA-256, not just "no
  code touched it").
- [ ] Zero new primitive in `desk_playbook_features.py` — `swing_pivots`, `consolidation_range`,
  `vertical_move` already exist from J-01/J-02; the three new detectors call them, they do not
  reimplement or extend them (expected: zero diff to that file this iteration).
- [ ] Structural guard tests (new): (a) a source-scan test asserting no playbook module (`desk_playbook.py`,
  `desk_playbook_detect.py`, `desk_playbook_features.py`) contains a loop/comprehension iterating
  over a `PLAYBOOK_*` constant or a candidate-value sequence to select a threshold (the
  no-threshold-sweep anti-goal, made concrete for this module set); (b) an import-graph test
  asserting `desk_playbook_detect.py` imports nothing named `*evidence*` (forward guard against
  `desk_playbook_evidence.py`, which does not exist yet — J-08 — so this locks the required
  detect→evidence import direction NEVER existing before it is even possible to violate it).
- [ ] Delete `apps/backend/.data/playbook/playbook-2026-08-04-e0f249f57785.json` (the stray
  browser-QA fixture from iter-3; git-ignored, self-disclosing, never distributed — removal is a
  hygiene fix, not a store mutation of a real record).
- [ ] `docs/playbook-detector-spec.md` §0: add one documentation-only paragraph stating that the
  served `playbook_input_signature` (+ `config_fingerprint` + the verbatim parameters blob) IS the
  provenance line's "parameters hash" — no new field, zero behavior change (mirrors the iter-2 B3/B4
  spec catch-up pattern; proven by a test that no source constant/field moved).
- [ ] `tests/test_desk_ui_guards.py`: extend `_PRICE_ARITHMETIC_FIELDS` (:152) with every new served
  numeric this iteration's UI renders (`jump_mbr`, `base_range_mbr`, `ladder_step_ratio`,
  `cup_depth_mbr`, `handle_retrace_frac`, `handle_duration_frac`, the three cup/handle RVOL medians
  below), plus seeded counter-test additions proving the extension actually catches an injected
  violation.

### Frontend

- [ ] `apps/frontend/lib/types.ts`: extend `DeskPlaybookGeometry` to cover the JBE/DBI and
  cup-and-handle disclosure fields alongside the existing opening-range fields (all served under
  the same `signal.geometry` object on the SAME `GET /research/desk/playbook` payload — see
  Data-contract additions below for exact names/types). `playbookSetupLabel` gains `"jbe"` →
  `"Jump-Base Explosion"`, `"dbi"` → `"Drop-Base Implosion"`, `"cup_handle"` → `"Cup and Handle"`.
- [ ] `apps/frontend/app/desk/page.tsx`: the signal-detail renderer (`PlaybookSignalDetail`, the
  function around line 4562) branches on `signal.setup_id` to render each new setup's own geometry
  line (base/jump geometry + ladder-step-ratio for JBE/DBI; cup/handle geometry for cup-and-handle)
  beside the already-shipped disclosures/volume/market lines, which stay setup-agnostic and
  unchanged. The signals table row and setup chip need no structural change — `playbookSetupLabel`
  already generalizes.
- [ ] T-9 discipline: `rm -rf apps/frontend/.next`, rebuild, restart before any browser evidence
  capture.
- [ ] T-11 discipline: no new `data-testid`/heading string collides with any of the 20 stored
  `goal-session-desk` golden scripts or this session's `J-10.json`; statically swept before
  capture.

### New user-facing capability

On the same Playbook Signals section, the operator now sees three additional setup types fire
alongside opening-range breaks — jump-base-explosion, drop-base-implosion, and cup-and-handle —
each with its own geometry disclosures, on the same session-date input and Run Playbook flow
already shipped.

### New information displayed

Per JBE/DBI signal: `jump_mbr`, `base_range_mbr`, `base_bars`, `base_flatline`,
`base_lows_ascending`, `ladder_step_ratio`. Per cup-and-handle signal: `cup_bars`,
`cup_depth_mbr`, `handle_retrace_frac`, `handle_duration_frac`, `cup_optimal`,
`handle_duration_desirable`, `cup_middle_third_rvol_median`, `cup_outer_third_rvol_median`,
`handle_rvol_median`. All already-shipped forward/baseline/invalidation-breached rendering applies
unchanged to signals of these new setups (no per-setup measurement branching needed).

### New user actions

None beyond the already-shipped session-date input + Run Playbook trigger/poll/cancel — the same
act now surfaces more setup types.

### UI surface changes

No new section. The existing Playbook Signals section (`/desk`) renders additional setup-specific
geometry lines when a JBE/DBI/cup-and-handle signal is present.

### Product surface delta

The operator's Playbook Signals table can now contain four setup types instead of two; every
shipped section (`/`, `/structure`, every `/desk` section, and the J-03 Playbook Signals shell
itself) behaves exactly as before for opening-range-break signals.

### Blueprint conformance

Lands inside the already-registered **Desk → Playbook Signals** home
(`runs/goal-session-playbook/state/blueprint.md`'s Information Architecture, which already names
"J-03, extended visibly by the detector families J-04/J-05/J-06"). No nav-skeleton edit; no
`blueprint.reapproval-requested` entry.

### Data-contract additions

New fields within the ALREADY-REGISTERED "Playbook records" row (owner `app/research/desk_playbook.py`
+ `desk_playbook_detect.py`, endpoint `GET /research/desk/playbook`, unchanged) — no new value, no
new owner, no new endpoint, per the "no second implementation" and single-source-of-truth rails.
`blueprint.md` already states this row's target shape includes "J-04/J-05/J-06 (each adds a
detector family to the same shared detect module — signature moves, endpoint/owner do not)", so no
edit to `blueprint.md` is needed:

| Field | Type/shape | On |
|---|---|---|
| `setup_id` | now one of `"open_high_break" \| "open_low_break" \| "jbe" \| "dbi" \| "cup_handle"` | `signal` |
| `geometry.jump_mbr` | `number` (MBR units) | JBE/DBI signal |
| `geometry.base_range_mbr` | `number` | JBE/DBI signal |
| `geometry.base_bars` | `int >= PLAYBOOK_BASE_MIN_BARS` | JBE/DBI signal |
| `geometry.base_flatline` | `boolean` | JBE/DBI signal |
| `geometry.base_lows_ascending` | `boolean` | JBE/DBI signal |
| `geometry.ladder_step_ratio` | `number \| null` (null when no prior ladder step exists) | JBE/DBI signal |
| `geometry.cup_bars` | `int >= PLAYBOOK_CUP_MIN_BARS` | cup_handle signal |
| `geometry.cup_depth_mbr` | `number` | cup_handle signal |
| `geometry.handle_retrace_frac` | `number` (0..`PLAYBOOK_HANDLE_MAX_RETRACE_FRAC`) | cup_handle signal |
| `geometry.handle_duration_frac` | `number` (0..`PLAYBOOK_HANDLE_MAX_DURATION_FRAC`) | cup_handle signal |
| `geometry.cup_optimal` | `boolean` | cup_handle signal |
| `geometry.handle_duration_desirable` | `boolean` | cup_handle signal |
| `geometry.cup_middle_third_rvol_median` | `number` | cup_handle signal |
| `geometry.cup_outer_third_rvol_median` | `number` | cup_handle signal |
| `geometry.handle_rvol_median` | `number` | cup_handle signal |

`playbook_input_signature` moves the moment these constants join `playbook_parameters()` (expected,
disclosed, versioned — never a silent reinterpretation of old records).

## OUT OF SCOPE

- The climax family (capitulation, euphoria marker — J-05) and the range family (range trades,
  double top/bottom — J-06). Each lands into this SAME Playbook Signals section with zero
  structural UI rework once its own detectors ship.
- The back-scan (J-07), the evidence view (J-08, including the `desk_playbook_evidence` module
  itself — this iteration only forward-guards against detect importing it), and MCP contract v4
  (J-09; MCP stays at exactly 18 tools, zero diff to `app/mcp/__init__.py`).
- Spec §4's `halted_formation` policy — still open per the iter-1 lesson; binds before J-07's
  back-scan touches real recorded sessions, not this iteration's fixture-scoped detectors.
- Spec §3.7-3.9 (range_trade, double_top, double_bottom) — J-06.
- Any diff to `desk_forward.py` itself — imported from only, zero diff, verified by `git diff`.
- Any diff to `desk_screen*.py`, `setups.py`, `bars.py`, or `levels.py` — read/mirrored only.
- Any new primitive in `desk_playbook_features.py` — `swing_pivots`/`consolidation_range`/
  `vertical_move` already exist as of J-01/J-02; expected zero diff to that file this iteration.
- Any change to any shipped `/desk` section's own behavior, columns, or copy, or to the J-03
  Playbook Signals shell's session-date input, Run/poll/cancel wiring, or absence/refusal states —
  render-only verification this iteration (Required-still-passing J-03/J-10).
- Any new `Config` field or fingerprint-epoch change; pin stays `08e471b10130e1e2`.
- Real (non-fixture) compute runs over the live recorded universe — fixture-scoped only.
- A new `parameters_hash` field on the served payload — the carried owner-ruling item is resolved
  by documenting that the existing signature already serves this role (see BACKGROUND item 2), not
  by inventing a field.

## DEFINITION OF DONE

- [ ] Target journey J-04 passes via browser-qa-agent — at least one JBE, one DBI, and one
  cup-and-handle signal legible (setup chip + geometry disclosures) in the J-03 Playbook Signals
  section on the fixture rig, in the same clean-rebuilt pass: TC-1, TC-2, TC-3.
- [ ] Required-still-passing journeys J-01, J-02, J-03 remain passing with zero change to
  opening-range-break behavior or already-recorded files: TC-9, TC-11.
- [ ] Required-still-passing journey J-10 remains at least `partial`, browser-verified in the SAME
  clean-rebuilt pass, with the lower-section screenshots re-taken via the sibling-collapse
  technique: TC-16, TC-17.
- [ ] No anti-goal violation introduced — no threshold sweep (TC-12), no import of a not-yet-built
  evidence module (TC-13), no second implementation of the shared primitives (TC-7 proves the
  lookahead property survives reusing the shared primitives unmodified; zero diff to
  `desk_playbook_features.py` proven alongside TC-16), the append-only/no-rewrite record discipline
  holds — duplicate keys still raise (TC-14) and a constant/signature change re-keys rather than
  rewrites, proven by SHA-256 (TC-10), deterministic seeded baselines including the first real
  two-firing JBE case (TC-8), no advice/probability language in new disclosures (TC-15).
- [ ] Unit tests pass; no regressions — full backend suite ≥ 2036 pass / 8 skip (the iter-3 floor),
  `Config().config_fingerprint()` prints `08e471b10130e1e2`, zero new `Config` fields: TC-16.
- [ ] All three carried items closed: the stray fixture record deleted and future plants scoped to
  `TAPEOLOGY_DESK_PLAYBOOK_DIR` (TC-18), the parameters-hash ruling written into the spec (TC-19),
  the lower-`/desk` screenshots re-taken (TC-17).
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-4-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-04 needs a real browser pass with screenshots showing a JBE signal, a DBI signal, and
  a cup-and-handle signal each rendering their own geometry disclosures inside the Playbook Signals
  section. Required-still-passing J-01/J-02/J-03 replay via the full backend suite (their behavior
  is not touched by this iteration; no browser re-capture needed for them specifically). Required
  J-10 MUST be replayed via its stored golden script (`runs/goal-session-playbook/journey-scripts/J-10.json`)
  in the SAME clean-rebuilt pass, walking every shipped `/desk` section including the lower ones
  (sibling-`display:none`-collapse technique, per the iter-3 lesson). Before trusting any browser-qa
  FAIL, verify the backend is alive by REQUEST (`curl :8301/health`), not by PID (iter-2 lesson 2).
  Scope every browser-QA compute/plant to `TAPEOLOGY_DESK_PLAYBOOK_DIR` (+ its log-dir env vars),
  never the operator's real `.data/playbook/` store (iter-3 lesson).
- Unit/integration:
  - `desk_playbook_detect.py`: fixture goldens for `jbe` (canonical firing: hand-computed
    `jump_mbr`, `base_range_mbr`, trigger, invalidation, `ladder_step_ratio`; near-miss: jump
    < `PLAYBOOK_JUMP_MIN_MULT`× base — silent) and `dbi` (mirror, short side).
  - `desk_playbook_detect.py`: fixture goldens for `cup_handle` (canonical firing: hand-computed
    `cup_depth_mbr`, `handle_retrace_frac`, `handle_duration_frac`, trigger, invalidation;
    near-miss: handle retraces beyond `PLAYBOOK_HANDLE_MAX_RETRACE_FRAC` — silent).
  - `desk_playbook.py`: a real two-firing JBE fixture (ladder step 1 and step 2 in one
    symbol-session) draws two independent, non-colliding baseline anchor indices, exercising the
    iter-3 seed-collision fix for the first time on a real (not synthetic) multi-fire signal.
  - `test_desk_playbook_detect.py`: extend `_LOOKAHEAD_FIXTURES` with the JBE, DBI, and
    cup-and-handle canonical-firing fixtures (truncate-after-trigger + mutate-post-trigger-bars
    property test, same generic harness as J-01/J-02).
  - A back-dated fixture re-run (before vs. after this iteration's constants join
    `playbook_parameters()`) shows the new-signature version recorded beside the old, with the old
    file's SHA-256 unchanged.
  - New structural guards: the no-threshold-sweep source-scan test and the
    detect-never-imports-evidence import-graph test, both green from the moment they are added.
  - `test_desk_ui_guards.py`: `_PRICE_ARITHMETIC_FIELDS` extended with all new geometry numerics +
    seeded counter-test(s).
  - Suite-wide: `Config().config_fingerprint()` unchanged; `git diff` empty against
    `desk_forward.py`/`desk_screen*.py`/`setups.py`/`bars.py`/`levels.py`/`config.py`/
    `mcp/__init__.py`/`desk_playbook_features.py`; full suite green at ≥ 2036 pass / 8 skip.
- Error cases:
  - A base still open at session close (JBE/DBI) emits nothing — no partial/guessed signal.
  - A handle still open at close (cup-and-handle) emits nothing.
  - A handle retracing beyond 50% of cup depth voids the cup-and-handle formation silently (may
    still fire as an independent hypothesis under a different detector — no cross-suppression).
  - A JBE/DBI base that never clears the volume-contrast or near-extreme gate fires no signal.
  - Thin/absent baseline or no bars for a symbol-session ⇒ disclosed absence row, never a guess
    (already-shipped absence machinery, exercised again for the new setups).

Test-first contract:

- TC-1: given the fixture rig with a canonical JBE firing session, when the operator runs the
  Playbook for that session and reads the signals table, then a `"jbe"` signal row renders with
  setup chip "Jump-Base Explosion", side long, and its geometry line showing `jump_mbr`,
  `base_range_mbr`, `base_bars`, `ladder_step_ratio` matching the hand-computed fixture values
  (screenshot).
- TC-2: given the fixture rig with a canonical DBI firing session, when the Playbook runs, then a
  `"dbi"` signal row renders with setup chip "Drop-Base Implosion", side short, mirrored geometry
  values matching the hand-computed fixture (screenshot).
- TC-3: given the fixture rig with a canonical cup-and-handle firing session, when the Playbook
  runs, then a `"cup_handle"` signal row renders with setup chip "Cup and Handle", side long, and
  its geometry line showing `cup_bars`, `cup_depth_mbr`, `handle_retrace_frac`,
  `handle_duration_frac` matching the hand-computed fixture values (screenshot).
- TC-4: given a JBE near-miss fixture (jump < `PLAYBOOK_JUMP_MIN_MULT`× base range), when
  `compute_playbook` runs over it, then no `"jbe"` signal is recorded for that symbol-session.
- TC-5: given a DBI near-miss fixture (mirrored gate failure), when `compute_playbook` runs over
  it, then no `"dbi"` signal is recorded for that symbol-session.
- TC-6: given a cup-and-handle near-miss fixture (handle retraces beyond
  `PLAYBOOK_HANDLE_MAX_RETRACE_FRAC` of cup depth), when `compute_playbook` runs over it, then no
  `"cup_handle"` signal is recorded for that symbol-session (it may still fire under a different
  detector's independent hypothesis, per spec §4).
- TC-7: given `_LOOKAHEAD_FIXTURES` extended with the JBE, DBI, and cup-and-handle canonical-firing
  fixtures, when the generic truncate-after-trigger + mutate-post-trigger-bars property test runs
  against each, then every detector's output is unchanged by the post-trigger mutation.
- TC-8: given a fixture session where the SAME `(symbol, "jbe")` pair fires twice (two ladder
  steps) within one session, when baseline anchors are drawn for each firing, then the two draws
  are independent (no seed collision) and the baseline pool reflects both draws — the first real
  exercise of the iter-3 seed-collision fix.
- TC-9: given every currently-recorded J-01/J-02/J-03-era playbook file, when this iteration's new
  constants join `playbook_parameters()` and a fresh compute runs over the SAME fixture inputs used
  to record them, then the output is byte-identical to what is already on disk and every existing
  file's SHA-256 is unchanged.
- TC-10: given a back-dated fixture recomputed after this iteration ships, when it is compared to
  its pre-iteration recorded version, then `playbook_input_signature` differs (new version minted
  beside the old) while the OLD file on disk is byte-identical (SHA-256 unchanged) — re-keying, not
  rewriting.
- TC-11: given J-01's and J-02's own test suites (99+ playbook tests) and the J-03 Playbook Signals
  section's shipped session-date/Run/poll/cancel/absence/refusal behavior, when this iteration
  ships, then all of it still passes/renders with zero change to opening-range-break signals or
  content.
- TC-12: given every playbook module (`desk_playbook.py`, `desk_playbook_detect.py`,
  `desk_playbook_features.py`) after this iteration, when the new source-scan guard test runs, then
  it finds zero loop/comprehension iterating over a `PLAYBOOK_*` constant or a candidate-value
  sequence to select a threshold.
- TC-13: given `desk_playbook_detect.py`'s imports after this iteration, when the new import-graph
  guard test runs, then it finds zero import of any module named `*evidence*`.
- TC-14: given the append-only playbook store, when a duplicate `(session_date,
  playbook_input_signature)` key is attempted, then it still raises exactly as J-01 shipped
  (unmodified store discipline — zero diff to the store's write path this iteration).
- TC-15: given the new geometry disclosures rendered on `/desk`, when
  `test_copy_discipline.py`'s frontend-literal walk scans them, then zero
  probability/expectancy/significance/advice language is found and the served register sentence is
  unchanged.
- TC-16: given the full backend test suite, when it is run after this iteration's changes, then it
  reports a pass count ≥ 2036 and skip count == 8, `Config().config_fingerprint()` prints
  `08e471b10130e1e2`, and `git diff` shows zero changes to `desk_forward.py`, `desk_screen*.py`,
  `setups.py`, `bars.py`, `levels.py`, `config.py`, `mcp/__init__.py`, and
  `desk_playbook_features.py`.
- TC-17: given the T-9 clean-rebuild discipline and the 20 stored `goal-session-desk` golden replay
  scripts plus `journey-scripts/J-10.json`, when `apps/frontend/.next` is removed/rebuilt/restarted
  and every shipped `/desk` section (including the lower ones, captured via the
  sibling-`display:none`-collapse technique) is walked and screenshotted, then J-10's regression
  replay passes with zero heading/`data-testid` collisions against any stored script.
- TC-18: given `apps/backend/.data/playbook/playbook-2026-08-04-e0f249f57785.json` on disk at the
  start of this iteration, when this iteration ships, then the file no longer exists, and this
  iteration's own browser-QA plants/computes are proven (by the env vars used in the QA report) to
  have targeted `TAPEOLOGY_DESK_PLAYBOOK_DIR` rather than the operator's real store.
- TC-19: given `docs/playbook-detector-spec.md` §0 after this iteration, when its provenance
  paragraph is read, then it states in writing that `playbook_input_signature` +
  `config_fingerprint` + the parameters blob together ARE the "parameters hash" the goal's
  provenance line names, with no source constant or served field moved as a result.

## NOTES

- The RVOL-median field names for cup-and-handle (`cup_middle_third_rvol_median`,
  `cup_outer_third_rvol_median`, `handle_rvol_median`) are this decomposer's concrete proposal since
  spec §3.6 names the three quantities in prose ("the three RVOL medians") without pinning literal
  field names. If the developer finds a clearer name consistent with the module's existing
  convention, keep the three values distinct and note the actual names chosen in the dev handoff —
  no ledger entry needed (a naming pick within an already-registered row is routine scoping, not an
  ambiguity in the goal itself).
- If the spec is found ambiguous or unimplementable for any one of the three detectors as literally
  written, drop that detector from this iteration, record the drop, and surface it for an owner
  ruling (Constraints §"The spec is canonical") — do not improvise a rule to keep J-04 fully green.
- **Blueprint: no edit this iteration.** The "Playbook records" row's target shape already names
  "J-04/J-05/J-06 (each adds a detector family to the same shared detect module — signature moves,
  endpoint/owner do not)" — this iteration is exactly that, so `blueprint.md` needs no edit, matching
  the precedent iter-1/iter-2/iter-3 set of not editing it when nothing new is introduced at the
  row/owner/endpoint level.
- **Key anchors for the developer** (verified against the current tree at authoring; re-locate by
  symbol name, never by line arithmetic): `desk_playbook_detect.py` — `detect_opening_range_breaks`
  :188 (the detector-function shape to mirror: formation → trigger → invalidation → disclosures →
  principles). `desk_playbook_features.py` — `swing_pivots` :171, `consolidation_range` :196,
  `vertical_move` :216, `side_sign` :300 (call, do not extend). `desk_playbook.py` —
  `PLAYBOOK_SETUPS` :137, `playbook_parameters()`'s constants blob, `compute_playbook_input_signature`
  :289, the compute walk's `detect_opening_range_breaks` call site :562. `docs/playbook-detector-spec.md`
  — §1's constants table (the complete tunable surface for this iteration's three detectors), §3.3-3.4
  (jbe/dbi), §3.6 (cup_handle), §4 (degenerate/edge policy). Frontend —
  `apps/frontend/app/desk/page.tsx`'s `playbookSetupLabel` :4401, the signal-detail renderer near
  :4562; `apps/frontend/lib/types.ts`'s `DeskPlaybookGeometry` :1480. Guard —
  `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` :152 (no line-number shift expected in
  `test_desk_refresh_chain_guard.py` — this iteration adds no new frontend action/handler, only new
  rendering branches on already-fetched data).
- **Scope-creep check:** every IN SCOPE item traces to J-04's own steps/acceptance text in
  `docs/goal.md`, or the iter-3 evaluator's next-step recommendation's three carried items — nothing
  here reaches outside `docs/goal.md`'s Key Capabilities or Constraints.
