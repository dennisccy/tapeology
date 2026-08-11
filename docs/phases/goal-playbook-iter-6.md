# Goal Iteration 6 — The range family: range trades + double top/bottom (J-06)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior verdict was `ESCALATE` (mandatory full depth, no exceptions). The
  evaluator's own recommendation is explicit: "run it as a deep iteration with the auditor" —
  the deep pass has caught a real honesty bug every time new detection maths landed (a fabricated
  opening-range fixture at iter-1, a false-negative near-miss fixture at iter-4), and the last two
  attempts at a deep pass were both silently demoted to lean by the engine's own budget-breach
  timing rule (iter-3, iter-5). Independently compounded by trigger 1 (structural/cross-cutting):
  three new detectors land in one commit across `desk_playbook_detect.py`/`desk_playbook.py`/two
  frontend geometry branches, one of them (`range_trade`) explicitly PROVISIONAL-tier per the
  spec's own vaguest book rule.
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-10 (widened to the FULL
  set of currently-passing journeys per the ESCALATE-triggers-a-wider-regression rule — the last
  full regression pass was iter-4/iter-5, both of which ran lean before this one)
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
    tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
    fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
    imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them,
    never a mutation of them. *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
    through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are
    labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
    feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
    research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
    MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
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
  - **The evidence pools one signature.** Distributions never mix parameter regimes; other
    signatures are listed, not merged; the min-n floor tags, it never filters; truncated values
    never enter a pool undisclosed. *(critical)*
  - **No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1.** New
    signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never
    overwritten; the store exposes no update or delete method (source-scan guard-tested).
    *(critical)*
  - **No second implementation of the measurement rail.** Measurement helpers are imported from
    `desk_forward.py` with a zero diff to that file; no playbook module re-implements horizons,
    MDD, truncation, or the seed discipline (import-graph guard-tested). *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY
    inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys,
    this Anti-goals section, or any other part of this file; proposed journeys MUST carry a
    single-source-of-truth acceptance criterion, keep the `default` profile and `v1`
    byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey
    just to keep the loop alive is a failure. *(critical)*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
    with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
    beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
    (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
    bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
    interactive pump sessions are auto-confined in place by the engine (`host-guard-adopt.sh`;
    `scripts/automation/host-guard-exec.sh claude` is the optional from-birth wrapper) — the
    engine pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established.
    Never disable, widen, or bypass these caps to make a run faster or a pause go away; widening
    the mask follows the verification ladder in
    `trendora/project-extensions/host-guard/README.md`. *(critical)*

## GOAL

The project owner runs the Playbook on a session and now sees the book's last detector family —
range trades (support-bounce long, resistance-fade short) and double top/double bottom reversals —
beside the five already-shipped setup families in the same `/desk` Playbook Signals section,
completing the full nine-detector-plus-marker set the era promised.

## BACKGROUND

Per the priority rubric: nothing regressed (rule 1 n/a — J-01..J-05 all re-verified passing at
iter-5), the iter-5 coherence audit was `COHERENCE-PASS` with zero blocking violations (rule 2
n/a — no consolidation pass owed), and J-06 is both the iter-5 evaluator's explicit next-step
recommendation and the last item in the natural dependency order before the back-scan
(`docs/goal.md`: "the detector families J-04/J-05/J-06 (each lands visibly on the J-03 section),
then J-07 → J-08 → J-09") — completing it unblocks J-07 (the back-scan walks whatever detector set
exists) and J-08 (the evidence view pools whatever setups have fired), satisfying rule 3. It is the
only remaining detection-maths journey, so rule 4 (smallest-spec-wins) does not offer an
alternative; only one risky journey is in scope (rule 5). Depth is `full` and mandatory per the
prior `ESCALATE` verdict (see Full trigger above) — not merely the evaluator's non-binding
recommendation this time, but the binding rule itself.

**Four lessons apply directly and are binding on this iteration's design:**
- *iter-5 lesson (a CONTINUE verdict's `Depth: full` is not binding, but ESCALATE is)* — this
  iteration's full depth rests on the `ESCALATE` rule specifically, not on re-arguing a trigger
  that a budget-breach marker could demote.
- *iter-4 lesson (a "must not fire" fixture can pass for the wrong reason)* — EVERY near-miss
  fixture this iteration (the strict-break-dissolves-range fixture, the failed-double-top fixture)
  MUST ship WITH a gate-relaxed control proving the NAMED gate specifically is the rejecter, not an
  earlier, coincidental gate. Do not accept `results == []` alone as proof of anything.
- *iter-4 lesson (extending the setup families silently invalidated the product's own summary
  copy)* — `PLAYBOOK_REGISTER` and BOTH `/desk` copy spots (`page.tsx:4993-4994` empty-state,
  `page.tsx:5091-5092` populated blurb) MUST be widened to name all eight families in the SAME
  commit that adds them, and the existing pinned-text test
  (`test_playbook_register_pinned_text_names_every_shipped_setup_family`,
  `apps/backend/tests/test_desk_playbook.py:1243`) MUST be re-derived to the new exact string with
  its own rationale paragraph — this is the third time this pattern applies (J-04, J-05, now J-06);
  do not defer it.
- *iter-5 lesson (a decomposer-invented field definition needs a degeneracy check)* — any field
  definition this spec proposes below that the canonical `docs/playbook-detector-spec.md` does not
  itself pin down (e.g. exact touch-count field shape for `range_trade`) is a NAMING proposal only,
  not a binding degenerate formula; the developer verifies it is not identically zero/constant by
  construction before shipping it, and reports the actual definition used in the dev handoff.

**Three small items carried from iter-5's next-step recommendation ride inside this same cycle:**
1. Write into `docs/playbook-detector-spec.md` §3.5 what `decline_bars`/`decline_mbr` mean and how
   the re-anchoring walk works — a documentation-only edit transcribing the whole-decline-leg
   reading `desk_playbook_detect.py`'s `_find_climax_formation`/`detect_capitulation` already ships
   (per the iter-5 evaluator's own read of the code), closing iter-5's OPEN minor anti-goal item.
   Zero number or behavior change; a source-scan test proves the code lines did not move (the
   iter-2 B3/B4 / iter-4 `PLAYBOOK_OR_MIN_1M_BARS` precedent this session has already ratified
   three times). See NOTES for the assumption-ledger entry already logged for this decision.
2. Investigate the two `.data/playbook_runs/playbookrun-2026-08-11-{9af9d27134e1,f24507d3e644}.json`
   rows naming record files nobody can find (both pre-date iter-5, not caused by it). If the cause
   is unscoped log-dir env vars (the iter-3 lesson: "scope EVERY browser-QA compute to
   `TAPEOLOGY_DESK_PLAYBOOK_DIR` **+ its log-dir env vars**" being only half-applied), document the
   finding and make this iteration's own test/browser-QA runs write their run-history to the SAME
   scratch folder as their records. This is an observability/process fix, not expected to touch
   product code.
3. Record a stored golden replay script for J-05 (`runs/goal-session-playbook/journey-scripts/J-05.json`)
   so the climax family is auto-replayed going forward — closes the `golden_coverage` gap the
   iteration-state has flagged since iter-5.

**Not resolved this iteration (surfaced for the operator, not decided here):** the two still-open
owner-ruling questions from iter-4/iter-5 — whether spec §3.3's 1.5x jump-to-base gate is reachable
under the current `BASE_MAX_RANGE_MBR`/`JUMP_MIN_MOVE_MBR` pairing, and whether the cup's rim test
should read the spec-named `RIM_MATCH_MBR` constant rather than the code's `near_extreme_mbr` (both
currently 1.0, zero behavior delta) — are genuine judgment calls about already-shipped J-04 code,
unrelated to J-06's own scope. They stay in `iteration-state.md`'s "Owner rulings pending" list.

## IN SCOPE

### Backend

- [ ] `desk_playbook_detect.py`: implement `range_trade` (support-bounce long + resistance-fade
  short, exact mirror) per spec §3.7 — arming via `zone_touches` on the high/low
  `NEAR_EXTREME_MBR`-wide zones (`≥ 2` touches each, each later touch extending the extreme by
  `≤ PLAYBOOK_RANGE_HOLD_TOL_MBR·MBR`, "held"), session range `≥ PLAYBOOK_RANGE_MIN_WIDTH_MBR·MBR`;
  trigger via the SAME reversal-bar grammar `detect_capitulation`'s bounce already implements (a
  bar touches the zone, the first bar within `PLAYBOOK_BOUNCE_MAX_BARS` with `high > high[t-1]` and
  the low-so-far still holding the zone within `RANGE_HOLD_TOL` — one shared mechanism per spec
  §3.7's own framing, not a second vague one); invalidation `SL − 0.30·(T − SL)` mirrored; cap 1 per
  side per symbol-session; disclosures `range_width_mbr`, per-zone touch counts, `crossed_midrange`,
  `absorption_bar_present` (a zone bar with `RVOL ≥ PLAYBOOK_RVOL_ELEVATED` and range
  `≤ RANGE_HOLD_TOL·MBR`). Module docstring/PROVISIONAL-tier note carried per spec §3.7's own
  "first candidate for removal" framing — no code behavior change from that note, disclosure only.
- [ ] `desk_playbook_detect.py`: implement `double_top` / `double_bottom` (exact mirror,
  `double_top` described) per spec §3.8-3.9 — two confirmed `swing_pivots` within
  `PLAYBOOK_TOPS_MATCH_MBR·MBR`, separated by `≥ PLAYBOOK_TOPS_MIN_SEPARATION_BARS`, both within
  `NEAR_EXTREME_MBR` of the session extreme at their own times; valley/peak depth
  `≥ PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR·MBR`; trigger on the FIRST bar breaking the valley/peak
  (never the second top/bottom itself), `p2` pivot-confirmed strictly before `t`; invalidation
  `S + 0.30·(S − T)` where `S = max(high(p1), high(p2))` (mirrored for the bottom); cap 1 per
  detector per symbol-session (first valid break only — a triple top cannot re-fire the same
  valley); disclosures `tops_gap_mbr`, `tops_separation_bars`, `valley_depth_mbr`,
  `nominal_risk_mbr` (the FULL pattern height, never shrunk), `second_top_rvol_vs_first` (median
  RVOL of p2±1 / p1±1); reuses the ALREADY-served `disclosures.attempt_count` field for the
  ≥3-attempts-before-break count (no new disclosure field — the shared §0 block already carries it).
- [ ] `desk_playbook.py`: wire all three new detectors into the SAME per-member compute walk beside
  the existing five detector calls (same absence gate, same `_measure_signal` pass, same baseline
  draw); extend `PLAYBOOK_SETUPS` to add `"range_trade"`, `"double_top"`, `"double_bottom"`.
- [ ] `desk_playbook.py`: widen `PLAYBOOK_REGISTER` (`:171`) to name all eight shipped setup
  families (opening-range breaks, jump-base-explosion, drop-base-implosion, cup-and-handle,
  capitulation, range trades, double top/bottom) — register text is NOT part of
  `playbook_parameters()`, so this does not move `playbook_input_signature`.
- [ ] New guard test: the playbook compute walk performs ZERO calls to `compute_tradability` and
  ZERO calls to `compute_levels` (call-count instrumentation — a stub/counting double, not a
  source-scan regex, since the guard must survive future refactors) — the concrete, machine-checked
  form of J-06's own "the book's intraday ranges and the desk's structural walls are different
  owners" acceptance line. Add to `apps/backend/tests/test_desk_playbook_guards.py` beside the
  existing structural guards.
- [ ] `apps/backend/tests/test_desk_playbook.py`: re-derive
  `test_playbook_register_pinned_text_names_every_shipped_setup_family`'s expected string to the
  widened register, with the mandatory rationale paragraph (the `_EXPECTED_EFFECT_COUNT`
  re-derivation pattern).
- [ ] `tests/test_desk_ui_guards.py`: extend `_PRICE_ARITHMETIC_FIELDS` (`:168`) with this
  iteration's new served price-arithmetic geometry numerics (see Data-contract additions below for
  the exact field list — bar-count fields like `tops_separation_bars` stay OUT, following the
  `base_bars`/`cup_bars`/`decline_bars` precedent), plus seeded counter-test additions.
- [ ] Doc-only: `docs/playbook-detector-spec.md` §3.5 gains prose stating exactly what
  `decline_bars`/`decline_mbr` measure and how the re-anchoring walk works (carried item 1 above) —
  zero diff to any constant value; a source-scan test proves
  `_find_climax_formation`/`detect_capitulation` code lines are byte-unchanged.
- [ ] Zero new primitive in `desk_playbook_features.py` — `zone_touches`, `swing_pivots`,
  `consolidation_range`, `market_context`, `side_sign` all already exist and are reused verbatim;
  expected zero diff to that file this iteration.
- [ ] Investigate and (if the cause is confirmed) fix the two orphaned run-ledger rows per carried
  item 2 above; scope this iteration's own test/browser-QA run-history writes to
  `TAPEOLOGY_DESK_PLAYBOOK_DIR`'s sibling scratch layout.
- [ ] Record `runs/goal-session-playbook/journey-scripts/J-05.json` (carried item 3) from this
  iteration's own clean-rebuilt browser pass, following the J-01..J-04 script shape already on
  file, with static-shell-string targets only (T-11 — the era-5 lesson: never target async-list
  text).

### Frontend

- [ ] `apps/frontend/lib/types.ts`: extend `DeskPlaybookGeometry` (`:1488`) with the range_trade
  and double_top/double_bottom fields listed in Data-contract additions below.
  `playbookSetupLabel` (`page.tsx:4401`) gains `"range_trade"` → `"Range Trade"`,
  `"double_top"` → `"Double Top"`, `"double_bottom"` → `"Double Bottom"`.
- [ ] `apps/frontend/app/desk/page.tsx`: `PlaybookSignalDetail` (the renderer around line 4557)
  gains a `range_trade` geometry branch (range width, zone touch counts, `crossed_midrange`,
  `absorption_bar_present`) and a `double_top`/`double_bottom` geometry branch (tops/valley gap,
  separation, depth, `nominal_risk_mbr`, `second_top_rvol_vs_first`) — same rendering pattern as
  the jbe/dbi (`:4600`) and capitulation (`:4635`) branches already shipped: verbatim `fmt()`
  display, zero client-side arithmetic.
- [ ] `apps/frontend/app/desk/page.tsx`: widen the empty-state sentence (`:4993-4994`) and the
  populated-section blurb (`:5091-5092`) to name all eight shipped setup families — the frontend
  half of the register-widening item above.
- [ ] T-9 discipline: `rm -rf apps/frontend/.next`, rebuild, restart before any browser evidence
  capture (already re-instated at iter-5; keep it that way).
- [ ] T-11 discipline: no new `data-testid`/heading string collides with any of the 20 stored
  `goal-session-desk` golden scripts, this session's `J-01`..`J-04`/`J-10` scripts, or the new
  `J-05.json` this iteration records; statically swept before capture.

### New user-facing capability

On the same Playbook Signals section, the operator now sees the book's last three setup types —
range-trade (support bounce / resistance fade) and double top/double bottom reversals — with their
own geometry disclosures, completing all nine detectors (plus the euphoria marker) the era
promised.

### New information displayed

Per range_trade signal: `range_width_mbr`, low/high zone touch counts, `crossed_midrange`,
`absorption_bar_present`. Per double_top/double_bottom signal: `tops_gap_mbr`,
`tops_separation_bars`, `valley_depth_mbr`, `nominal_risk_mbr`, `second_top_rvol_vs_first`. No
other already-shipped field, section, or behavior changes.

### New user actions

None beyond the already-shipped session-date input + Run Playbook trigger/poll/cancel — the same
act now surfaces three more setup types.

### UI surface changes

No new section. The existing Playbook Signals section (`/desk`) renders two additional
setup-specific geometry branches (range_trade; double_top/double_bottom).

### Product surface delta

The operator's Playbook Signals table can now contain eight setup types instead of five; every
shipped section (`/`, `/structure`, every `/desk` section, and every already-shipped setup family)
behaves exactly as before.

### Blueprint conformance

Lands inside the already-registered **Desk → Playbook Signals** home
(`runs/goal-session-playbook/state/blueprint.md`'s Information Architecture and Data Contract,
both of which already name J-06 landing on the same "Playbook records" row/section — freshened
this iteration for status only, no IA/Data-Contract structural change). No nav-skeleton edit; no
`blueprint.reapproval-requested` entry.

### Data-contract additions

New fields within the ALREADY-REGISTERED "Playbook records" row (owner
`app/research/desk_playbook.py` + `desk_playbook_detect.py`, endpoint
`GET /research/desk/playbook`, unchanged) — no new value, no new owner, no new endpoint:

| Field | Type/shape | On |
|---|---|---|
| `setup_id` | now also `"range_trade"`, `"double_top"`, `"double_bottom"` | `signal` |
| `geometry.range_width_mbr` | `number` (MBR units, ≥ `PLAYBOOK_RANGE_MIN_WIDTH_MBR`) | range_trade signal |
| `geometry.low_zone_touches` | `int` (≥ 2 by the arming gate) | range_trade signal |
| `geometry.high_zone_touches` | `int` (≥ 2 by the arming gate) | range_trade signal |
| `geometry.crossed_midrange` | `boolean` | range_trade signal |
| `geometry.absorption_bar_present` | `boolean` | range_trade signal |
| `geometry.tops_gap_mbr` | `number` (≤ `PLAYBOOK_TOPS_MATCH_MBR`) | double_top / double_bottom signal |
| `geometry.tops_separation_bars` | `int` (≥ `PLAYBOOK_TOPS_MIN_SEPARATION_BARS`) | double_top / double_bottom signal |
| `geometry.valley_depth_mbr` | `number` (≥ `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR`) | double_top / double_bottom signal |
| `geometry.nominal_risk_mbr` | `number` (full pattern height, never shrunk) | double_top / double_bottom signal |
| `geometry.second_top_rvol_vs_first` | `number \| null` | double_top / double_bottom signal |

`disclosures.attempt_count` (already served, unchanged shape) is REUSED for the double_top/
double_bottom "≥3 attempts" disclosure — no new disclosure field created for it (never duplicate a
contract value). `playbook_input_signature` moves the moment `PLAYBOOK_SETUPS` gains the three new
ids (expected, disclosed, versioned — never a silent reinterpretation of old records).

## OUT OF SCOPE

- The back-scan (J-07), the evidence view (J-08 — the forward-guard against detect importing it,
  shipped at iter-4, stays untouched), and MCP contract v4 (J-09; MCP stays at exactly 18 tools,
  zero diff to `app/mcp/__init__.py`).
- Resolving the two carried owner-ruling questions (1.5x jump-to-base reachability; cup rim
  constant naming) — surfaced for the operator, not resolved by this iteration.
- Spec §4's `halted_formation` policy — still open per the iter-1 lesson; binds before J-07's
  back-scan touches real recorded sessions, not before J-06.
- Removing or demoting `range_trade` from `PLAYBOOK_SETUPS` under its own PROVISIONAL-tier clause
  — that decision requires the back-scan's real forward distributions (J-07/J-08), not available
  yet; this iteration ships it exactly as spec §3.7 defines it.
- Any diff to `desk_forward.py`, `desk_screen*.py`, `setups.py`, `bars.py`, `levels.py`,
  `config.py`, `mcp/__init__.py`, or `desk_routes.py` — read/imported/mirrored only, verified by
  `git diff`.
- No change to `tests/test_desk_refresh_chain_guard.py`'s `_EXPECTED_EFFECT_COUNT` — range_trade
  and double_top/double_bottom ride the SAME "Run Playbook" button and compute manager; no new
  compute path or UI effect is introduced.
- Any change to any shipped `/desk` section's own behavior, columns, or copy outside the two named
  register-widening spots, or to the J-03 Playbook Signals shell's session-date input,
  Run/poll/cancel wiring, absence/refusal states, or to the already-shipped `open_high_break`/
  `open_low_break`/`jbe`/`dbi`/`cup_handle`/`capitulation`/`euphoria` detection logic itself —
  render-only verification this iteration (Required-still-passing J-01/J-02/J-03/J-04/J-05/J-10).
- Any new `Config` field or fingerprint-epoch change; pin stays `08e471b10130e1e2`.
- Real (non-fixture) compute runs over the live recorded universe — fixture-scoped only.
- Cross-symbol range/pivot detection — every detector reads only its own symbol-session's bars,
  same as every prior family.

## DEFINITION OF DONE

- [ ] Target journey J-06 passes via browser-qa-agent — one range_trade signal and one
  double_top/double_bottom signal both legible in the J-03 Playbook Signals section on the fixture
  rig, in the same clean-rebuilt pass: TC-1, TC-4, TC-9.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05 remain passing with zero change
  to their own signals or content: TC-15.
- [ ] Required-still-passing journey J-10 remains at least `partial`, browser-verified in the SAME
  clean-rebuilt pass: TC-16.
- [ ] No anti-goal violation introduced — no threshold sweep (TC-7), zero
  `compute_tradability`/`compute_levels` calls from the playbook walk (TC-7), lookahead property
  test extended for all three new detectors (TC-8), append-only/no-rewrite record discipline holds
  — a fresh compute over existing fixture inputs stays byte-identical and existing files' SHA-256
  is unchanged (TC-13), a signature change re-keys rather than rewrites (TC-14), no advice/
  probability language in new disclosures (TC-17).
- [ ] The two OPEN minor anti-goal items carried from iter-5 are addressed: the `decline_bars`/
  re-anchoring documentation gap is CLOSED (TC-18), and the two orphaned run-ledger rows are
  investigated with a documented finding (TC-19).
- [ ] The register/blurb widening (the third occurrence of this pattern) is CLOSED with a
  re-derived pinned-text guard: TC-6.
- [ ] Unit tests pass; no regressions — full backend suite ≥ 2079 pass / 8 skip (the iter-5 floor),
  `Config().config_fingerprint()` prints `08e471b10130e1e2`, zero new `Config` fields: TC-11.
- [ ] A stored golden replay script for J-05 exists and passes: TC-20.
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-6-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-06 needs a real browser pass with screenshots showing one range_trade signal and one
  double_top-or-double_bottom signal inside the Playbook Signals section, each with its own
  geometry legible. Required-still-passing J-01/J-02/J-03/J-04/J-05 replay via the full backend
  suite (their own behavior is not touched this iteration); J-05 additionally gets its first stored
  golden replay script recorded this iteration. Required J-10 MUST be replayed via its stored
  golden script (`runs/goal-session-playbook/journey-scripts/J-10.json`) in the SAME clean-rebuilt
  pass, walking every shipped `/desk` section (sibling-`display:none`-collapse technique, per the
  iter-3 lesson). Before trusting any browser-qa FAIL, verify the backend is alive by REQUEST
  (`curl :8301/health`), not by PID (iter-2 lesson). Scope every browser-QA compute/plant to
  `TAPEOLOGY_DESK_PLAYBOOK_DIR` (+ its log-dir env vars), never the operator's real
  `.data/playbook/` store (iter-3 lesson).
- Unit/integration:
  - `desk_playbook_detect.py`: fixture goldens for `range_trade` support-bounce long (canonical
    firing: triple-touch armed low zone, hand-computed `range_width_mbr`, zone touch counts,
    `crossed_midrange`, `absorption_bar_present`, trigger, invalidation) and its resistance-fade
    short mirror.
  - `desk_playbook_detect.py`: a near-miss fixture where price strictly breaks a zone by more than
    `PLAYBOOK_RANGE_HOLD_TOL_MBR·MBR` before any reversal bar (range-mode dissolves, no signal)
    PAIRED with a gate-relaxed control (the SAME fixture with the break brought back within
    tolerance) asserting exactly one signal fires — proving the break-tolerance gate specifically
    is the rejecter (the iter-4 lesson).
  - `desk_playbook_detect.py`: fixture goldens for `double_top` (clean two-pivot fixture, valley
    break trigger, hand-computed `tops_gap_mbr`/`tops_separation_bars`/`valley_depth_mbr`/
    `nominal_risk_mbr`/`second_top_rvol_vs_first`) and its `double_bottom` mirror.
  - `desk_playbook_detect.py`: a near-miss fixture where `p2` exceeds `p1` by more than
    `PLAYBOOK_TOPS_MATCH_MBR` (no double_top) PAIRED with a gate-relaxed control (p2 brought within
    tolerance) asserting exactly one signal fires — proving `PLAYBOOK_TOPS_MATCH_MBR` specifically
    is the rejecter.
  - A degeneracy check on every new field definition this spec proposes above that the canonical
    spec does not itself pin to a formula (the iter-5 lesson) — confirm none is identically zero or
    constant by construction before it ships; report the actual definition used in the dev handoff.
  - Extend the generic truncate-after-trigger + mutate-post-trigger-bars lookahead property test
    with the range_trade and double_top/double_bottom canonical-firing fixtures.
  - New guard: a call-counting double/stub for `compute_tradability`/`compute_levels` proves
    `compute_playbook` calls neither, zero times, over a fixture walk that fires all eight setup
    types.
  - `test_desk_ui_guards.py`: `_PRICE_ARITHMETIC_FIELDS` extended with the new geometry numerics
    (see Data-contract additions; bar-count fields excluded per the `base_bars`/`decline_bars`
    precedent) + seeded counter-test(s).
  - The register/blurb pinned-text assertion, with its mandatory rationale paragraph, re-derived to
    the new widened text.
  - A back-dated fixture re-run (before vs. after this iteration's `PLAYBOOK_SETUPS` change) shows
    the new-signature version recorded beside the old, with the old file's SHA-256 unchanged.
  - Suite-wide: `Config().config_fingerprint()` unchanged; `git diff` empty against
    `desk_forward.py`/`desk_screen*.py`/`setups.py`/`bars.py`/`levels.py`/`config.py`/
    `mcp/__init__.py`/`desk_routes.py`/`desk_playbook_features.py`; full suite green at ≥ 2079
    pass / 8 skip.
- Error cases:
  - A range fixture that never achieves 2 zone touches on either extreme (never arms) emits
    nothing — no partial/guessed signal.
  - A double-top fixture whose valley depth falls short of `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR`
    emits nothing.
  - Thin/absent baseline or no bars for a symbol-session ⇒ disclosed absence row, never a guess
    (already-shipped absence machinery, exercised again for all three new detectors).
  - A double-top fixture where price collapses through the valley INSIDE `p2`'s own
    pivot-confirmation window fails closed (no signal) — the pivot-confirmation-delay lookahead
    rule applied to this detector for the first time.

Test-first contract:

- TC-1: given the fixture rig with a canonical triple-touch armed-range session (low zone touched
  ≥ 2, each later touch within `RANGE_HOLD_TOL_MBR` of the extreme, a reversal bar within
  `PLAYBOOK_BOUNCE_MAX_BARS` of the last touch), when the operator runs the Playbook for that
  session and reads the signals table, then a `"range_trade"` signal row renders with setup chip
  "Range Trade", side long, and its geometry line showing `range_width_mbr`, `low_zone_touches`,
  `crossed_midrange`, `absorption_bar_present` matching the hand-computed fixture values
  (screenshot).
- TC-2: given the same fixture mirrored to the high zone, when `compute_playbook` runs, then a
  `"range_trade"` signal with side short is recorded, an exact geometric mirror of TC-1.
- TC-3: given a range fixture where price strictly breaks beyond a zone by more than
  `PLAYBOOK_RANGE_HOLD_TOL_MBR·MBR` before any reversal bar, when `compute_playbook` runs over it,
  then no `range_trade` signal is recorded for that symbol-session, and the gate-relaxed control
  (the same fixture with the break brought back within tolerance) fires exactly one signal.
- TC-4: given a clean double-top fixture (two confirmed swing-high pivots within
  `PLAYBOOK_TOPS_MATCH_MBR·MBR`, separated by `≥ PLAYBOOK_TOPS_MIN_SEPARATION_BARS`, valley depth
  `≥ PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR·MBR`), when the operator runs the Playbook and reads the
  signals table, then a `"double_top"` signal row renders triggered at the valley break (never at
  the second top's own bar), with `nominal_risk_mbr` equal to the full pattern height
  (screenshot).
- TC-5: given a fixture where `p2` exceeds `p1` by more than `PLAYBOOK_TOPS_MATCH_MBR`, when
  `compute_playbook` runs over it, then no `double_top` signal is recorded, and the gate-relaxed
  control (p2 brought within tolerance) fires exactly one signal.
- TC-6: given `PLAYBOOK_REGISTER` and the `/desk` empty-state (`page.tsx:4993-4994`) and
  populated-section (`page.tsx:5091-5092`) copy after this iteration, when they are read, then both
  name all eight shipped setup families instead of five, and the re-derived pinned-text test
  asserts the exact register string with its rationale paragraph.
- TC-7: given a fixture walk that fires all eight setup types in one `compute_playbook` call, when
  the new call-counting guard runs, then it records exactly zero calls to `compute_tradability` and
  exactly zero calls to `compute_levels`.
- TC-8: given the range_trade and double_top/double_bottom canonical-firing fixtures added to the
  generic lookahead fixture list, when the truncate-after-trigger + mutate-post-trigger-bars
  property test runs against them, then each detector's trigger, invalidation, and geometry are
  unchanged by the post-trigger mutation.
- TC-9: given a fixture recording at least one range_trade and one double_top/double_bottom signal
  on the browser rig, when the operator opens the Playbook Signals section in a real (non-headless
  assumption) browser pass, then both new signal types' geometry lines are legible with real
  numbers, not placeholders (screenshot).
- TC-10: given a double-top fixture where price collapses through the valley strictly INSIDE `p2`'s
  own pivot-confirmation window, when `compute_playbook` runs, then no `double_top` signal fires
  (fail-closed, the pivot-confirmation-delay rule).
- TC-11: given the full backend test suite, when it is run after this iteration's changes, then it
  reports a pass count ≥ 2079 and skip count == 8, `Config().config_fingerprint()` prints
  `08e471b10130e1e2`, and `git diff` shows zero changes to `desk_forward.py`, `desk_screen*.py`,
  `setups.py`, `bars.py`, `levels.py`, `config.py`, `mcp/__init__.py`, `desk_routes.py`, and
  `desk_playbook_features.py`.
- TC-12: given the structural guards shipped in iter-4/iter-5 (no-threshold-sweep source-scan;
  detect-never-imports-evidence import-graph; marker-decoration forward-only), when they run after
  this iteration's new detector code lands, then all stay green with zero relaxation.
- TC-13: given every currently-recorded J-01..J-05-era playbook file, when this iteration's three
  new setup ids join `PLAYBOOK_SETUPS` and a fresh compute runs over the SAME fixture inputs used to
  record them (no range/double-top formation present in those fixtures), then the output is
  byte-identical to what is already on disk and every existing file's SHA-256 is unchanged.
- TC-14: given a back-dated fixture recomputed after this iteration ships, when compared to its
  pre-iteration recorded version, then `playbook_input_signature` differs (new version minted
  beside the old) while the OLD file on disk is byte-identical (SHA-256 unchanged).
- TC-15: given J-01's/J-02's/J-03's/J-04's/J-05's own already-shipped test suites and the J-03
  Playbook Signals section's shipped session-date/Run/poll/cancel/absence/refusal behavior plus
  every prior setup renderer, when this iteration ships, then all of it still passes/renders with
  zero change to their own signals or content.
- TC-16: given J-10's stored golden script and every shipped `/desk` section, when this iteration's
  browser pass replays it (sibling-`display:none`-collapse technique for the lower sections), then
  it passes with zero heading/`data-testid` collisions against any stored script (including the new
  J-05 script), with screenshots for every shipped section.
- TC-17: given the new range_trade and double_top/double_bottom geometry disclosures rendered on
  `/desk`, when `test_copy_discipline.py`'s frontend-literal walk scans them, then zero
  probability/expectancy/significance/advice language is found.
- TC-18: given `docs/playbook-detector-spec.md` §3.5 after the doc-only edit, when read, then it
  states explicitly what `decline_bars`/`decline_mbr` measure and how re-anchoring works, with a
  source-scan test proving `_find_climax_formation`/`detect_capitulation`'s code lines are
  byte-unchanged and `git diff` shows zero change to any `PLAYBOOK_*` constant value.
- TC-19: given the two orphaned run-ledger rows named in `iteration-state.md`, when this iteration
  investigates them, then the dev handoff records either a confirmed cause (with the process fix
  applied to this iteration's own test/browser-QA runs) or an explicit "cause unconfirmed, still
  pre-existing, not reproduced this iteration" finding — never silence.
- TC-20: given `runs/goal-session-playbook/journey-scripts/J-05.json` recorded this iteration, when
  the deterministic replay engine runs it against a live rig, then it reproduces J-05's browser
  acceptance (capitulation signal + euphoria-recent decoration legible) without falling back to the
  LLM lane.

## NOTES

- **Field-name proposals are this decomposer's concrete suggestion**, consistent with the existing
  `jump_mbr`/`base_range_mbr`/`decline_mbr` naming convention. If the developer finds a clearer
  name for a field the canonical spec does not itself name (spec §3.7-3.9 describe the DISCLOSURE
  in prose — "per-zone touch counts", "tops_gap_mbr", etc. — some names are lifted directly from
  spec prose, others like `low_zone_touches`/`high_zone_touches` are this decomposer's own split of
  "per-zone touch counts" into two servable fields), keep the actual name chosen consistent with
  the precedent and note it in the dev handoff — no ledger entry needed (routine scoping, not a
  goal ambiguity) unless the developer finds the field is degenerate/undefined by the spec, in
  which case apply the iter-5 lesson's degeneracy check before shipping it.
- If the spec is found ambiguous or unimplementable for any of the three detectors as literally
  written, drop it from this iteration, record the drop, and surface it for an owner ruling
  (Constraints §"The spec is canonical") — do not improvise a rule to keep J-06 fully green. Spec
  §3.7 already flags `range_trade` PROVISIONAL for exactly this reason; a drop of `range_trade`
  alone (keeping `double_top`/`double_bottom`) is an acceptable, spec-sanctioned partial outcome if
  the trigger grammar cannot be implemented deterministically as written — record it plainly rather
  than force it.
- **The assumption-ledger entry for carried item 1** (the `decline_bars` doc-only edit) is already
  logged at `runs/goal-session-playbook/state/assumptions.md` under "iter-6 — goal-decomposer" —
  read it before writing the spec edit so the transcribed reading matches exactly what
  `detect_capitulation` already ships.
- **Key anchors for the developer** (verified against the current tree at authoring; re-locate by
  symbol name, never by line arithmetic): `desk_playbook_features.py` — `zone_touches` :259 (overlap
  + full-exit-re-arm semantics, the arming primitive), `swing_pivots` :171 (the pivot-confirmation
  primitive double_top/double_bottom need), `consolidation_range` :196, `market_context` :277,
  `side_sign` :300. `desk_playbook_detect.py` — `detect_capitulation`/`_find_climax_formation`
  (the shared reversal-bar trigger grammar range_trade's own trigger explicitly reuses, per spec
  §3.7's own framing), `detect_jbe`/`detect_dbi`/`detect_cup_handle` (the detector-function shape to
  mirror). `desk_playbook.py` — `PLAYBOOK_SETUPS` :157, `playbook_parameters()`'s
  `range_min_width_mbr`/`range_hold_tol_mbr`/`tops_match_mbr`/`tops_min_separation_bars` entries
  (already embedded, unused until now), `PLAYBOOK_REGISTER` :171, the compute walk's
  `detected_signals` assembly around :637-665. `docs/playbook-detector-spec.md` — §1's constants
  table (all range/double-top constants already tabulated), §3.7-3.9. Frontend —
  `apps/frontend/app/desk/page.tsx`'s `playbookSetupLabel` :4401, the signal-detail renderer near
  :4557, the two copy spots :4993-4994/:5091-5092; `apps/frontend/lib/types.ts`'s
  `DeskPlaybookGeometry` :1488.
- **Scope-creep check:** every IN SCOPE item traces to J-06's own steps/acceptance text in
  `docs/goal.md`, or iter-5's next-step recommendation's carried items — nothing here reaches
  outside `docs/goal.md`'s Key Capabilities or Constraints.
