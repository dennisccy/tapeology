# Goal Iteration 10 — Era-closing pass: spec catch-up, the midrange-turn disclosure, kept-product fixes

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 10
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — cross-cutting era-closing pass: spec-doc edits across four detector
  families (§3.3/§3.6/§3.7/§3.8), a new disclosure field spanning detector + serialization +
  frontend-types + UI, a fixture-seeding index-repair fix, and a golden-replay-asset fix — at
  least nine files across five layers (spec doc, backend detector, backend tests, frontend types,
  frontend UI, test-fixture infra, golden-replay JSON), none of whose combined correctness is
  covered by any single journey's own tests; plus R-3.3's explicit "run the pass at FULL depth
  with the auditor" mandate, which four prior specs asked for and the arbiter demoted every time.
  (Not trigger 2: every code change here is purely additive — a new optional field for a
  never-before-served disclosure — never a change to an already-registered Data-Contract value's
  owner/endpoint or to persisted-record schema; R-3.3 itself pins `playbook_input_signature` and
  `config_fingerprint` unmoved.)
- **Frontend Present:** yes
- **Target journeys:** J-06, J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-07, J-08, J-09
- **Anti-goal reminders:**
  - "Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five states
    and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them,
    never a mutation of them. *(critical)*"
  - "No lookahead — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*"
  - "Single source of truth — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*"
  - "Immutable data — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*"
  - "Persistence stays scoped — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*"
  - "No threshold exists outside the spec, and no code path sweeps one. Every detector rule and
    threshold exists in `docs/playbook-detector-spec.md` BEFORE the code that uses it; no code
    path iterates thresholds against outcomes (source-scan guard-tested); a threshold change is a
    spec revision + new signature, never an edit of recorded signals and never a sweep.
    *(critical)*"
  - "A signal is an observation, not a call. No signal, chip, or evidence cell uses advice,
    imperative, prediction, probability, expectancy, edge, or significance language; the served
    registers state what was NOT measured (no fills, no costs, returns not stop-adjusted);
    `invalidation_price` is geometry, never an order concept. *(critical)*"
  - "No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1. New
    signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never
    overwritten; the store exposes no update or delete method (source-scan guard-tested).
    *(critical)*"
  - "Host-guard caps are law ... Never disable, widen, or bypass these caps to make a run faster
    or a pause go away; widening the mask follows the verification ladder in
    `trendora/project-extensions/host-guard/README.md`. *(critical)*"

## GOAL

Close Era B2 by ratifying the spec text against the shipped code exactly where `docs/goal.md`'s
new R-3 ruling directs, shipping the one small disclosure it authorizes, and fixing the two
test/evidence defects the iteration-9 evaluator carried forward — so the next evaluation can judge
the era on a fully consistent, fully re-verified product instead of on open owner questions.

## BACKGROUND

Iteration 9 shipped all ten journeys passing but halted `STALLED`: two "the spec is canonical"
items (the `range_trade` degenerate-trigger clause, and four places the shipped code reads the
spec more narrowly than written) had sat open since iteration 6, and per the decision tree a
pending ruling that could still remove a Must-have setup blocks an honest `GOAL_ACHIEVED`. The
owner has now ruled — `docs/goal.md`'s new **R-3** block (R-3.1 ratifies `range_trade` as
written, R-3.2 accepts all four narrower-than-spec readings as canonical with one completion, and
R-3.3 scopes exactly what iteration 10 must do). This spec turns R-3.3's directive into concrete
work: transcribe R-3.2(a)/(c)/(d)/(e) into `docs/playbook-detector-spec.md` with zero code diff,
ship R-3.2(b)'s one new disclosure field, fix `J-10.json`'s fixture-rebuild-dependent golden
assertion, and fix the scoped rig's `/structure` chart evidence gap. R-3.3 also asks that this run
at full depth with the auditor — the fifth time full has been requested for this closing work, per
R-3.3's own count of the four prior demotions. The evaluator's own recommendation for THIS
iteration is `full` (binding by default per this agent's instructions), and Full trigger 1 above
is the honest, independently-justified reason this spec cites. Whether the engine's deterministic
arbiter actually grants it this time is a separate, mechanical question, addressed transparently
in NOTES rather than assumed away — this iteration's scope, DEFINITION OF DONE, and TC- scenarios
are written to hold regardless of which depth actually dispatches.

Per the priority rubric: no journey is `failing` or `regressed` (all ten pass per
`journey-history.json`), so this is a consolidation pass, directly following rule 2 ("consolidation
before features") in spirit even though the trigger is an owner ruling rather than a coherence
FAIL — R-3.3 is explicit that iteration 10's scope is the catch-up items and nothing else, so no
new Must-have or proposer journey is picked this iteration. Two journeys carry genuine new/changed
surface (J-06 gains a field, J-10's own test asset is fixed) and are Targets; the other eight ride
as a full regression sweep, matching "every few iterations, widen it to a full regression of all
passing journeys" — this is that iteration for the era.

**Lessons applied (from `runs/goal-session-playbook/state/lessons.md`):**
- iter-9: a golden assertion rewritten mid-run to a fixture-state-dependent value quietly stops
  protecting anything — `J-10.json`'s fix must target a STATIC, always-rendered `/desk` shipped
  string, never a hash or any value a run just produced.
- iter-8 (×2): a screenshot's filename is a claim, not evidence — evidence review this iteration
  must open the actual images; and store-scope protection only works as an OBLIGATION the engine
  enforces, never an optional launcher. That obligation is now live (see NOTES) — this iteration
  does not need to re-invoke a scoped-backend script by hand.
- iter-6: a behavior-only fix (constants unchanged) does not move `playbook_input_signature`, so
  pre-fix browser evidence for anything this iteration touches must be treated as voided and
  re-captured on a fresh rebuild — relevant here because the same iteration both repairs the
  fixture rig's indexing AND adds new detector code.
- iter-5: a decomposer/iteration field definition the canonical spec does not itself state needs a
  degeneracy check before being treated as binding. Applied directly: this spec does NOT dictate
  the exact bar-by-bar "turned at midrange" test (see IN SCOPE) — only the disclosure's name,
  shape, and the binding constraint that it reuse an already pre-registered constant.

## IN SCOPE

### Backend

- [ ] `docs/playbook-detector-spec.md` §3.8 Caps line (mirrored by convention in §3.9): rewrite
  per R-3.2(a) to the shipped reading ("the first pivot pair, in chronological `(p1, p2)` order,
  whose full formation validates AND triggers"). Doc text only — zero change to
  `desk_playbook_detect.py`'s double-top/double-bottom code.
- [ ] `docs/playbook-detector-spec.md` §3.3 body + the `PLAYBOOK_JUMP_MIN_MULT` row of the
  constants table (§1): annotate per R-3.2(c) that the BOOK 1.5× ratio gate is mathematically
  dominated by `PLAYBOOK_JUMP_MIN_MOVE_MBR`/`PLAYBOOK_BASE_MAX_RANGE_MBR` and has never
  independently rejected a formation (min observed ratio 1.735 across 32 recorded signals). Doc
  text only — zero change to any `PLAYBOOK_*` constant VALUE or to the JBE/DBI gate code.
- [ ] `docs/playbook-detector-spec.md` §3.6: rename the left-rim "near session-high-so-far" test's
  constant per R-3.2(d) from `PLAYBOOK_RIM_MATCH_MBR` to `PLAYBOOK_NEAR_EXTREME_MBR` (matching the
  shipped code); the rim-to-rim test keeps `RIM_MATCH_MBR`. Doc text only — zero change to
  `cup_handle`'s code.
- [ ] `docs/playbook-detector-spec.md` §3.7 Trigger clause: narrow per R-3.2(e) from "a bar `b`
  touches the low zone" to name the arming-completing touch `b` specifically (matching
  `_range_trade_side`, `apps/backend/app/research/desk_playbook_detect.py:1068-1153`). Doc text
  only — zero change to that function.
- [ ] `docs/playbook-detector-spec.md` §3.7 Disclosures clause: spec-first split per R-3.2(b) —
  name `crossed_midrange` exactly as "did price cross the range midpoint on the approach" (its
  actual implemented semantics), and name the second disclosure ("whether the prior swing turned
  at midrange, the BOOK midrange rule") as its own field with its own mechanical definition,
  reusing ONE already pre-registered constant (candidates already in the constants table:
  `PLAYBOOK_RANGE_HOLD_TOL_MBR`, this detector's own existing "held" tolerance; or the existing
  `swing_pivots` primitive keyed by `PLAYBOOK_PIVOT_LOOKBACK_BARS`) — never a new one. This text
  lands BEFORE the code below.
- [ ] `apps/backend/app/research/desk_playbook_detect.py`'s `_range_trade_side` (the function that
  already builds `crossed_midrange` at line ~1180-1246): add `geometry.turned_at_midrange` per the
  spec text above — disclosure-only (never gates/suppresses/creates a signal), lookahead-clean
  (reads only bars at-or-before the arming-completing touch, the same discipline
  `crossed_midrange` already uses), computed for both long and short sides. If, after a genuine
  attempt, the definition cannot be expressed without a new constant, DROP the field, add nothing
  new to the constants table, and record the drop with its reason (assumption ledger +
  `iteration-state.md`) — this is R-3.2(b)'s own sanctioned outcome, not a failure of this item.
- [ ] A new counter-test (extending `test_monkeypatched_constant_moves_parameters_and_signature_and_mints_a_new_version`,
  `apps/backend/tests/test_desk_playbook.py:300`) proving `playbook_parameters()`/
  `compute_playbook_input_signature` are byte-unchanged by this iteration's own code (no constant
  value changed), on top of the existing proof that monkeypatching the reused constant DOES move
  both.
- [ ] `apps/backend/scripts/seed_playbook_iter8_replay_rig.py`'s `_copy_kept_symbol_series` step
  (around line 201-238, called from `main()` at line 283): after copying AAPL's real bar files
  onto the scoped rig, index them into the scoped rig's own `bar_index.db` via the EXISTING
  `desk_index_reconcile.run_reconcile` (`apps/backend/app/research/desk_index_reconcile.py:150` —
  the sole `BarIndex.reindex()` repair path; it repairs the index only, never bar content).
  Diagnosed root cause of the iter-9 blank-chart evidence gap (verify before implementing): a raw
  `shutil.copy2` never updates the index, and `GET /research/bars?symbol=...` — what the
  `/structure` chart fetches — resolves a `symbol=` filter through `BarIndex.list()`
  (`apps/backend/app/research/routes.py:770`), so an unindexed copy is invisible to that filtered
  read even though the levels/tradability table (a separate cache path) already shows real
  numbers. This is test/fixture infrastructure, not product code.

### Frontend

- [ ] `apps/frontend/lib/types.ts`: add `turned_at_midrange?: boolean` to `DeskPlaybookGeometry`
  (`:1488`), beside the existing `crossed_midrange?: boolean` (`:1523`) — or omit if the backend
  item above is dropped-and-surfaced.
- [ ] `apps/frontend/app/desk/page.tsx`'s `range_trade` geometry line
  (`desk-playbook-signal-range-trade-geometry`, `:5099-5106`): render the new field as one more
  conditional chip, the same pattern as the existing `crossed_midrange`/`absorption_bar_present`
  chips (e.g. `{geometry.turned_at_midrange && " · turned at midrange"}`).

### New user-facing capability

An already-shipped `range_trade` signal's geometry line can now also disclose whether the
approach swing turned at the range's midpoint (the book's own "midrange rule"), alongside the
existing "crossed midrange" disclosure — informational only, never gating, never advice.

### New information displayed

`turned_at_midrange: boolean` — a small inline chip on `range_trade` signals only, shown when
true (matching how `crossed_midrange`/`absorption_bar_present` already render).

### New user actions

None — no new buttons, forms, or controls. This iteration only enriches an existing row's
disclosure text and fixes test/evidence infrastructure.

### UI surface changes

One new conditional `<p>` chip inside the EXISTING `desk-playbook-signal-range-trade-geometry`
element on `/desk`'s Playbook Signals section. No new section, no new page, no nav change.

### Product surface delta

The end-user-visible product is otherwise unchanged this iteration. Every other delta (spec-doc
catch-up, a signature-stability proof, a golden-replay-script fix, a fixture-index repair) is
internal consistency/regression work with zero additional visible surface.

### Blueprint conformance

No new Information-Architecture surface. J-06's new chip renders inside the ALREADY-registered
"Playbook Signals" section under `/desk` → Desk nav (`runs/goal-session-playbook/state/blueprint.md`,
Navigation skeleton + Feature/journey-homes table, J-06 row). J-10 re-verifies the ALREADY-registered
Cockpit/Structure/Desk homes. `blueprint.md` has been freshened additively this iteration (status
banner + the J-06/J-09/J-10 IA rows + the "Playbook records" Data-Contract row); no nav-skeleton
edit was needed, so no `blueprint.reapproval-requested` file was written.

### Data-contract additions

`geometry.turned_at_midrange: boolean` (optional key) — a NEW field on the ALREADY-registered
"Playbook records" Data-Contract row (owner: `app/research/desk_playbook_detect.py` +
`desk_playbook.py`, unchanged; endpoint: `GET /research/desk/playbook`, unchanged; MCP:
`desk_playbook`'s existing byte-identical proxy forwards it automatically, zero MCP code diff).
Present (`true`/`false`) on every `range_trade` signal computed after this iteration's code lands;
ABSENT (never `null`) on every record computed before it, including the 87 real signals under
signature `16a2734d10c91ea7` — no backfill, per the append-only anti-goal. No new owner, no new
endpoint, no new row. If the backend item above is dropped-and-surfaced instead (R-3.2(b)'s escape
hatch), this addition is "none" and `blueprint.md`'s row is left exactly as this iteration wrote
it (still describing only the SHIPPED five rows, no phantom field).

## OUT OF SCOPE

- Any detector LOGIC change to `open_high_break`/`open_low_break`/`jbe`/`dbi`/`capitulation`/
  `cup_handle`/`double_top`/`double_bottom` beyond the four doc-only text edits named above — all
  four are zero-code-diff by construction and are verified via `git diff` (TC-1..TC-4).
- Any change to `desk_forward.py` (era-wide zero-diff invariant) or to Evidence aggregation
  (`desk_playbook_evidence.py`) — the new field is a Playbook Signals disclosure only, never
  pooled or measured.
- Any new MCP tool, MCP schema change, or new `Config` field / fingerprint-epoch bump — the pin
  `08e471b10130e1e2` and `playbook_input_signature` do not move this iteration.
- Re-litigating R-3.1 or R-3.2's owner-ratified readings — this iteration transcribes them into
  the spec; it does not re-derive, second-guess, or expand them.
- The `GET .../backscan/plan` malformed-date input case — already closed at iteration 8 (HTTP 200,
  empty/disclosed plan); not reopened.
- The three store-scope hardening items (abort-on-breach, QA-agent-lane gating, repo-wide
  fixture-forcing) — CLOSED at iterations 8-9 per the "Do not redo" list; not reopened.
- Any new Must-have journey or `AUTO:journeys` proposal — this is a closing/consolidation pass.
- Re-seeding or re-capturing any J-01-J-09 evidence beyond what the full-depth regression sweep's
  own replay/fallback naturally re-verifies — only J-06 and J-10 get fresh captures.

## DEFINITION OF DONE

- [ ] J-06 passes via browser-qa-agent (existing acceptance unchanged, plus the new
  `turned_at_midrange` disclosure visible in at least one fresh screenshot — or the drop is
  recorded and J-06's acceptance is unaffected by the escape hatch)
- [ ] J-10 passes via browser-qa-agent (`J-10.json` step 6 fixed and green; fresh `/structure`
  screenshot shows real candlesticks, not a blank canvas)
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-07, J-08, J-09 remain green
  (deterministic replay + LLM fallback on any miss)
- [ ] `docs/playbook-detector-spec.md` R-3.2(a)/(c)/(d)/(e) edits land with git-diff-proved ZERO
  change to any detector code or `PLAYBOOK_*` constant value
- [ ] `docs/playbook-detector-spec.md` §3.7's Disclosures clause is split/completed spec-first
  (R-3.2(b)) before any code change
- [ ] `geometry.turned_at_midrange` ships (disclosure-only, reuses an existing constant, optional
  key, zero signature move) OR is dropped-and-surfaced per the named escape hatch
- [ ] `playbook_input_signature` is byte-unchanged by this iteration's own code (new counter-test)
  and `Config().config_fingerprint()` prints `08e471b10130e1e2`
- [ ] `runs/goal-session-playbook/journey-scripts/J-10.json` step 6 asserts a static,
  always-rendered `/desk` shipped-section string, never a fixture-rebuild-dependent value
- [ ] The scoped fixture rig's `/structure` chart renders real candles for the kept-symbol
  regression capture (indexing fix verified, not just implemented)
- [ ] No anti-goal violation introduced; the store-scope guard reports zero delta against the
  operator's real store across the whole pass
- [ ] Full backend suite ≥2163 passed / 8 skipped / exit 0; no regressions
- [ ] Coherence-auditor (runs at every depth) confirms single-source-of-truth for the new field
  via its Data Contract check; whichever agent reviews the diff — the dedicated `auditor` if full
  depth is actually granted, the `reviewer` if the depth arbiter demotes this to lean — confirms
  zero code diff for the four doc-only spec items via `git diff` (TC-1..TC-4 are mechanically
  checkable regardless of which agent runs them)
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-10-dev.md`

## TESTING REQUIREMENTS

- Browser: J-06 (fresh screenshot with the new chip visible on a `range_trade` signal), J-10
  (fixed `J-10.json` replay + fresh `/structure` screenshot with real candles + the existing
  Cockpit/Desk regression walk). Required-still-passing J-01/J-02/J-03/J-04/J-05/J-07/J-08/J-09
  via deterministic replay with LLM fallback on any miss.
- Unit/integration: `desk_playbook_detect.py` range_trade tests extended with the new field's
  True/False fixture pair (or the drop recorded, no new test needed, if dropped); a new
  `playbook_input_signature`-unchanged counter-test in `test_desk_playbook.py`; a smoke check that
  `desk_index_reconcile.run_reconcile` leaves the scoped rig's `bar_index.db` with entries for the
  copied AAPL series; the existing `tests/test_copy_discipline.py` sweep re-run over the new chip
  text; full backend suite green above the 2163-test floor.
- Error cases: a session with no confirmable "prior swing" before the arming-completing touch
  (e.g. the touch is one of the session's first bars) must resolve `turned_at_midrange` to a
  disclosed `False` (or the key absent, if the developer's fail-closed reading omits it) — never a
  crash, never a guessed `True`. No other new input surface is added this iteration (the four
  doc-only items add no new code path; the `backscan/plan` malformed-date case is already closed).

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line below (given / when / then, observable end state, no vague
terms):

- TC-1: given `docs/playbook-detector-spec.md` §3.8's Caps line and its §3.9 mirror BEFORE any
  code change, when rewritten per R-3.2(a) to "the first pivot pair, in chronological `(p1, p2)`
  order, whose full formation validates AND triggers", then `git diff` on
  `desk_playbook_detect.py`'s double_top/double_bottom functions shows zero lines changed.
- TC-2: given `docs/playbook-detector-spec.md` §3.3's body and the `PLAYBOOK_JUMP_MIN_MULT`
  constants-table row, when annotated per R-3.2(c) to disclose the BOOK ratio's inertness, then
  `git diff` on the JBE/DBI gate code and on every `PLAYBOOK_*` constant's VALUE shows zero change.
- TC-3: given `docs/playbook-detector-spec.md` §3.6, when the left-rim clause is renamed per
  R-3.2(d) from `PLAYBOOK_RIM_MATCH_MBR` to `PLAYBOOK_NEAR_EXTREME_MBR` (rim-to-rim clause
  unchanged), then `git diff` on `desk_playbook_detect.py`'s `cup_handle` detector shows zero
  change.
- TC-4: given `docs/playbook-detector-spec.md` §3.7's Trigger clause, when narrowed per R-3.2(e)
  to name the arming-completing touch `b`, then `git diff` on `_range_trade_side`'s trigger-scan
  code (`desk_playbook_detect.py:1068-1153`) shows zero change.
- TC-5: given `docs/playbook-detector-spec.md` §3.7's Disclosures clause BEFORE any
  `desk_playbook_detect.py` change, when split per R-3.2(b), then `crossed_midrange` is named
  exactly as "did price cross the range midpoint on the approach" and the new field is named as
  its own disclosure whose mechanical definition cites only a constant already present in the
  Pre-registered constants table (§1) — no new table row added.
- TC-6: given a scoped-rig `range_trade` fixture whose approach swing satisfies the new spec-first
  "turned at midrange" definition, when `detect_range_trade` runs, then
  `geometry.turned_at_midrange` is `True` and every pre-existing field on that signal
  (`trigger_price`, `invalidation_price`, `crossed_midrange`, `absorption_bar_present`,
  `range_width_mbr`, etc.) is byte-unchanged from its pre-iteration-10 value.
- TC-7: given a fixture whose approach swing does NOT satisfy that same definition, when the
  detector runs, then `geometry.turned_at_midrange` is `False` — the required near-miss pairing.
- TC-8: given an existing playbook record recorded before this iteration (e.g. one of the 87 real
  `range_trade` signals under signature `16a2734d10c91ea7`), when served via
  `GET /research/desk/playbook`, then its geometry object has no `turned_at_midrange` key at all
  (absent, never `null`) and the response is still HTTP 200.
- TC-9: given the reused constant is monkeypatched, when `playbook_parameters()`/
  `compute_playbook_input_signature` run, then the signature moves; and given no constant is
  changed (only this iteration's field-adding code lands), when the same signature helper runs on
  the same bar/member inputs as before this iteration, then it returns the byte-identical value —
  and `Config().config_fingerprint()` still prints `08e471b10130e1e2`.
- TC-10: given the developer determines the field cannot be defined without minting a new
  `PLAYBOOK_*` constant, when this is discovered, then the field is dropped, no new constant is
  added anywhere, and the drop plus its reason is recorded in
  `runs/goal-session-playbook/state/assumptions.md` and `iteration-state.md`.
- TC-11: given the `range_trade` geometry line on `/desk` (`desk-playbook-signal-range-trade-geometry`),
  when a `range_trade` signal with `turned_at_midrange: true` renders, then the line shows a new
  " · turned at midrange" chip and `tests/test_copy_discipline.py`'s existing sweep passes over the
  new copy text with no advice/imperative/prediction/probability language detected.
- TC-12: given the fixed `runs/goal-session-playbook/journey-scripts/J-10.json` step 6, when the
  deterministic replay lane runs it against the scoped fixture rig, then it asserts a static,
  always-rendered `/desk` shipped-section string (a kept Era-B heading, never a hash or a value
  the run itself just produced) and passes.
- TC-13: given `apps/backend/scripts/seed_playbook_iter8_replay_rig.py`'s AAPL kept-symbol bar
  copy is indexed into the scoped rig's own `bar_index.db` via `desk_index_reconcile.run_reconcile`
  (`apps/backend/app/research/desk_index_reconcile.py:150`), when the browser-qa lane loads
  `/structure?symbol=AAPL&asof=2026-06-22T23:59:59Z` and clicks Load, then the candlestick chart
  renders real candles (not "No candles to draw for this timeframe") in a fresh screenshot, the
  resistance/support levels table still reads the same pinned numbers as before (e.g. the
  `300.11-302.2` band, byte-identical), and no bar file content is mutated.
- TC-14: given the full-depth pass's whole-era re-verification, when the full backend suite runs
  to completion, then it exits 0 with at least 2163 passed and 8 skipped.
- TC-15: given the store-scope guard's mandatory require/snapshot/verify wrap around every lane at
  the depth that actually dispatches, when the pipeline's replay and browser-qa lanes run
  (including the `/structure` re-capture, which stays on the scoped rig per TC-13 — never the
  operator's real, now-restored `:8301`), then `store_scope_verify` reports zero delta against the
  protected-path manifest and `apps/backend/.data/playbook*` gains no new file.
- TC-16: given the coherence-auditor's Data Contract check on this iteration's diff, when it
  inspects the `turned_at_midrange` addition (or its dropped-and-surfaced alternative), then it
  confirms the field rides the already-registered "Playbook records" row (same owner, same
  endpoint, no second computing module) and the existing `desk_playbook` MCP proxy forwards it
  automatically (zero `app/mcp/__init__.py` diff).

## NOTES

- **Depth-arbiter transparency, not a request to route around it.** This spec requests
  `Depth: full` because that is what the evaluator's binding recommendation and Full trigger 1
  above both call for. Independently, `run-goal.sh`'s SPEED-20 arbiter caps at most one full
  dispatch per `CHAIN_FULL_CADENCE_CAP`-iteration window (default 4;
  `goal_full_ran_in_window`, `incredible_auto_dev/scripts/automation/lib/common.sh:1074`) —
  iteration 8 already used that window's slot (`iter-8/depth-dispatched` = `full`), and that check
  fires BEFORE the arbiter ever reaches the branch that would honor this spec's own
  `Full trigger:` line. On the current on-disk history this would demote to lean
  (`reason: full-cap`), the same way iterations 2/3/5/7/9 were each demoted before it (confirmed in
  `runs/goal-session-playbook/telemetry.jsonl`'s `depth_demoted`/`depth_full_granted` events) — a
  fifth demotion of this closing work, the exact pattern R-3.3 names. This is disclosed here, not
  routed around: nothing this spec writes changes engine configuration. If the owner wants the
  dedicated `auditor` step to actually run for this pass, the lever is operator-side
  (`CHAIN_FULL_CADENCE_CAP` raised, or `CHAIN_DEPTH_ARBITER=false`, when invoking `run-goal.sh` for
  this iteration) — a decision for whoever runs the engine next, not something this spec can do.
  Every DEFINITION OF DONE item and TC- above is written to hold regardless of which depth actually
  dispatches (the coherence-auditor runs at both depths; every other check is a git-diff,
  counter-test, or screenshot fact, not an agent-identity claim), so a demotion does not block this
  iteration's completion.
- **The store-scope guard is now automatic, not a launcher to invoke by hand.** Since iteration 9
  (`project-extensions/store-scope/README.md`), `browser-qa-phase.sh` (full depth) and
  `goal-iter-lean.sh` (lean) both call `store_scope_require`/`snapshot`/`verify` around every lane
  themselves — the QA port is force-swapped to the fixture rig automatically, and any delta
  against the protected-path manifest hard-fails with a report. Nobody needs to invoke
  `qa_playbook_iter7_fixture_scoped_backend.sh` manually this iteration; the ONE thing this
  mechanism means for the `/structure` fix is that pointing the browser lane at the operator's
  real, now-restored `:8301` is not an available option even for a single read-only step — the fix
  has to live in the scoped rig's OWN seed data (the index-repair item above), not in routing.
- **R-3.3 confirms the operator restored `:8301` to the real store before this resume.** That fact
  is why the era-closing pass can now safely run without repeating the iteration-6/7/8 accidental
  real-store-write incidents (the automatic guard above is the actual protection; the restoration
  just means the AMBIENT backend, when the guard's `require` step swaps it out and back, is the
  operator's genuine backend again afterward — nothing this iteration should rely on touching it
  directly).
- **J-06.json does not need editing.** Its steps assert element presence
  (`desk-playbook-signal-range-trade-geometry` becomes visible), not exact text content, so the
  new chip is invisible to that golden script and safe by construction — do not touch it.
- **Any browser evidence captured before both fixes land (the new field's code AND the seed
  script's index repair) must be treated as voided**, per the iter-6 lesson: re-capture on a fresh
  rebuilt rig once both are in, never mix pre-fix and post-fix screenshots into one evidence set.
- If the owner's R-3 ruling is later found to require a **second** resume before this spec is
  dispatched (e.g. a further clarification), re-read `docs/goal.md`'s OWNER RATIFICATION section
  for a new dated block before executing — do not assume R-3 is the final word if a later R-4
  exists at execution time.
