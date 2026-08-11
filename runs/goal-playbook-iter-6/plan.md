# goal-playbook-iter-6 Execution Plan

## What to Build

- `range_trade` detector (spec §3.7, PROVISIONAL tier) in `desk_playbook_detect.py`:
  support-bounce long + resistance-fade short, exact mirror. Arming via `zone_touches` on the
  high/low `NEAR_EXTREME_MBR`-wide zones (≥2 touches each, "held" within `RANGE_HOLD_TOL_MBR`),
  session range ≥ `RANGE_MIN_WIDTH_MBR`; trigger reuses the SAME reversal-bar grammar
  `detect_capitulation`'s `_find_climax_formation`/bounce logic already implements (one shared
  mechanism, per spec's own framing — do not build a second one); invalidation
  `SL − 0.30·(T − SL)` mirrored; cap 1 per side per symbol-session; disclosures
  `range_width_mbr`, per-zone touch counts, `crossed_midrange`, `absorption_bar_present`.
- `double_top` / `double_bottom` detectors (spec §3.8-3.9, exact mirror) in
  `desk_playbook_detect.py`: two confirmed `swing_pivots` within `TOPS_MATCH_MBR`, separated by
  ≥ `TOPS_MIN_SEPARATION_BARS`, both within `NEAR_EXTREME_MBR` of the session extreme; valley/peak
  depth ≥ `MIN_STRUCTURE_DEPTH_MBR`; trigger on the FIRST bar breaking the valley/peak (never the
  second top itself), `p2` pivot-confirmed strictly before `t` (fail closed if price collapses
  through the valley INSIDE `p2`'s own confirmation window); invalidation
  `S + 0.30·(S − T)`; cap 1 per detector per symbol-session; disclosures `tops_gap_mbr`,
  `tops_separation_bars`, `valley_depth_mbr`, `nominal_risk_mbr` (full pattern height, never
  shrunk), `second_top_rvol_vs_first`; reuses the ALREADY-served `disclosures.attempt_count` field
  — no new disclosure field for the "≥3 attempts" reading.
- Wire all three new detectors into `compute_playbook`'s existing per-member walk
  (`desk_playbook.py`, beside the five existing detector calls — same absence gate, same
  `_measure_signal` pass, same baseline draw); extend `PLAYBOOK_SETUPS` (`:157`) to an 8-tuple
  adding `"range_trade"`, `"double_top"`, `"double_bottom"`.
- Widen `PLAYBOOK_REGISTER` (`:171`) to name all eight shipped setup families (this is the THIRD
  occurrence of this pattern — J-04, J-05, now J-06; do not defer it). Register text is not part
  of `playbook_parameters()`, so this alone does not move the signature.
- New behavioral guard test in `test_desk_playbook_guards.py`: a call-counting stub/double proves
  the playbook compute walk makes ZERO calls to `compute_tradability` and ZERO calls to
  `compute_levels` over a fixture walk that fires all eight setup types — instrumentation, not a
  source-scan regex (must survive future refactors).
- Re-derive `test_playbook_register_pinned_text_names_every_shipped_setup_family`
  (`test_desk_playbook.py:1243`) to the widened 8-family string, with its own rationale paragraph
  (the `_EXPECTED_EFFECT_COUNT` re-derivation pattern already used twice this session).
- Extend `test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` (`:168`-ish, relocate by name) with
  this iteration's new price-arithmetic geometry numerics: `range_width_mbr`, `tops_gap_mbr`,
  `valley_depth_mbr`, `nominal_risk_mbr`, `second_top_rvol_vs_first` (bar-count / int-count fields
  — `tops_separation_bars`, `low_zone_touches`, `high_zone_touches` — stay OUT, following the
  `base_bars`/`cup_bars`/`decline_bars` precedent), plus seeded counter-test additions.
- Doc-only: `docs/playbook-detector-spec.md` §3.5 gains prose on what `decline_bars`/`decline_mbr`
  measure and how the re-anchoring walk works, transcribing the reading already shipped in
  `_find_climax_formation`/`detect_capitulation` (iter-5's dev handoff already states the exact
  reading to transcribe; the assumption-ledger entry at
  `runs/goal-session-playbook/state/assumptions.md` "iter-6 — goal-decomposer" is pre-logged).
  Zero diff to any `PLAYBOOK_*` constant or to the two functions' code lines — prove it with a
  source-scan test.
- Investigate the two orphaned `.data/playbook_runs/playbookrun-2026-08-11-{9af9d27134e1,
  f24507d3e644}.json` run-ledger rows (pre-date iter-5). If caused by an unscoped log-dir env var
  (the iter-3 lesson applied only half — `TAPEOLOGY_DESK_PLAYBOOK_DIR` scoped but not its log-dir
  siblings), document the finding and scope this iteration's own test/browser-QA run-history
  writes to the same scratch folder as their records. Report a confirmed cause + fix, OR an
  explicit "cause unconfirmed, pre-existing, not reproduced" finding — never silence (TC-19).
- Record a stored golden replay script `runs/goal-session-playbook/journey-scripts/J-05.json` from
  a clean-rebuilt browser pass (capitulation signal + euphoria-recent decoration legible),
  following the J-01..J-04 script shape already on file — static-shell-string targets only (the
  era-5 lesson: never target async-list/`<option>` text).
- Frontend: `DeskPlaybookGeometry` (`types.ts:1488`) gains the range_trade and
  double_top/double_bottom fields; `playbookSetupLabel` (`page.tsx:4401`) gains
  `"range_trade"` → "Range Trade", `"double_top"` → "Double Top", `"double_bottom"` → "Double
  Bottom"; `PlaybookSignalDetail` (renderer near `page.tsx:4557`) gains a `range_trade` geometry
  branch and a `double_top`/`double_bottom` geometry branch, same verbatim-`fmt()`/zero-client-
  arithmetic pattern as the jbe/dbi/capitulation branches; the empty-state sentence (`:4993-4994`)
  and populated-section blurb (`:5091-5092`) widen to name all eight families.
- T-9 (clean `.next` rebuild) and T-11 (no `data-testid`/heading collision against any of the 20
  `goal-session-desk` scripts, this session's J-01..J-04/J-10 scripts, or the new J-05.json)
  discipline applies to every browser pass this iteration.

## Agents Required

- backend-data: yes -- three new detectors in `desk_playbook_detect.py`, wiring + register/setups
  widening in `desk_playbook.py`, new zero-structure-calls guard, pinned-text re-derivation,
  doc-only spec edit, orphaned-ledger investigation, J-05 golden replay script recording.
- frontend-ux: yes -- `types.ts` geometry fields, `playbookSetupLabel`, two new
  `PlaybookSignalDetail` branches, the two widened copy spots.

## Frontend Present

yes

## Files to Create/Modify

- `apps/backend/app/research/desk_playbook_detect.py` -- add `detect_range_trade` (long+short via
  shared mirror helper), `detect_double_top`, `detect_double_bottom`; extend `__all__`.
- `apps/backend/app/research/desk_playbook.py` -- extend `PLAYBOOK_SETUPS` (`:157`) to 8-tuple;
  widen `PLAYBOOK_REGISTER` (`:171`); wire the three new detectors into `compute_playbook`'s
  per-member walk (`detected_signals` assembly near `:637-665`).
- `apps/backend/tests/test_desk_playbook_detect.py` -- canonical + near-miss + gate-relaxed-control
  fixtures for range_trade (both sides) and double_top/double_bottom (both), lookahead property
  test extension, the p2-inside-confirmation-window fail-closed fixture.
- `apps/backend/tests/test_desk_playbook.py` -- compute_playbook-level wiring tests for the three
  new detectors, the re-derived register pinned-text test with rationale paragraph, the
  back-dated-fixture re-key test (TC-14), byte-identity test (TC-13).
- `apps/backend/tests/test_desk_playbook_guards.py` -- new zero-`compute_tradability`/
  zero-`compute_levels` call-counting guard with seeded counter-test.
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` extended + counter-test.
- `docs/playbook-detector-spec.md` -- §3.5 doc-only prose addition (decline_bars/decline_mbr +
  re-anchoring), with an accompanying source-scan test proving zero code-line diff.
- `runs/goal-session-playbook/journey-scripts/J-05.json` -- new stored golden replay script.
- `apps/frontend/lib/types.ts` -- `DeskPlaybookGeometry` (`:1488`) gains the new optional fields.
- `apps/frontend/app/desk/page.tsx` -- `playbookSetupLabel` (`:4401`), `PlaybookSignalDetail`
  (~`:4557`) two new geometry branches, the two copy spots (`:4993-4994`, `:5091-5092`).
- `docs/handoffs/goal-playbook-iter-6-dev.md` -- dev handoff (required deliverable).

## UI Evolution

- New user-facing capability: the same Playbook Signals section (`/desk`) now can show
  range-trade (support bounce / resistance fade) and double top/double bottom reversal signals,
  completing all nine detectors (plus the euphoria marker) the era promised.
- New information displayed: per range_trade signal -- `range_width_mbr`, low/high zone touch
  counts, `crossed_midrange`, `absorption_bar_present`. Per double_top/double_bottom signal --
  `tops_gap_mbr`, `tops_separation_bars`, `valley_depth_mbr`, `nominal_risk_mbr`,
  `second_top_rvol_vs_first`.
- New user actions: none beyond the already-shipped session-date input + Run Playbook
  trigger/poll/cancel -- the same act now surfaces three more setup types.
- UI surface changes: no new section; the existing Playbook Signals section renders two additional
  setup-specific geometry branches.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the exact rendering pattern already shipped for jbe/dbi (`:4600`) and
  capitulation (`:4635`) geometry branches inside `PlaybookSignalDetail` -- a labeled geometry line
  with verbatim `fmt()` display, zero client-side arithmetic, same chip/label styling via
  `playbookSetupLabel` + `CHIP_CLASS`.
- Layout: unchanged -- signals table row + expandable/inline geometry detail block, below every
  shipped `/desk` section, dark-only terminal-grade styling already established.
- Key visual effects: none new -- match existing signal-detail typography/spacing exactly; no new
  chrome, no marketing language (setup names stay the book's own).
- States to handle: honest absence (no signals -> nothing rendered for that setup, existing
  absence-row machinery), the new detectors' near-miss cases must never render a partial/guessed
  signal (arming that never completes = no row).

## Key Test Scenarios

- TC-1/TC-2: canonical triple-touch armed range fires a `"range_trade"` long signal (and its
  short mirror) with geometry matching hand-computed fixture values (screenshot).
- TC-3: a strict-break-beyond-tolerance fixture fires nothing; the SAME fixture with the break
  brought back within `RANGE_HOLD_TOL_MBR` fires exactly one signal (gate-relaxed control proving
  the named gate is the rejecter, per the iter-4 lesson).
- TC-4/TC-5: clean double-top fixture triggers at the valley break (never the second top's own
  bar) with correct `nominal_risk_mbr`; a `p2`-exceeds-`p1`-beyond-tolerance fixture fires nothing,
  its gate-relaxed control fires exactly one signal.
- TC-6: `PLAYBOOK_REGISTER` and both `/desk` copy spots name all eight families; the re-derived
  pinned-text test asserts the exact string with its rationale paragraph.
- TC-7: the new call-counting guard proves zero `compute_tradability`/`compute_levels` calls over
  a fixture walk firing all eight setup types.
- TC-8/TC-10: lookahead property test extended for all three new detectors; a fixture where price
  collapses through the valley inside `p2`'s own pivot-confirmation window fails closed.
- TC-9: real (non-headless) browser pass on the fixture rig shows one range_trade signal and one
  double_top/double_bottom signal with legible, real-numbered geometry (screenshot).
- TC-11/TC-12: full backend suite ≥ 2079 pass / 8 skip, `config_fingerprint()` ==
  `08e471b10130e1e2`, `git diff` empty against the named untouched files; all prior structural
  guards stay green with zero relaxation.
- TC-13/TC-14: fresh compute over existing fixture inputs is byte-identical to what's on disk
  (SHA-256 unchanged) when no new-family formation is present; a back-dated fixture recompute
  mints a new signature/version while the old file's SHA-256 stays unchanged.
- TC-15/TC-16: J-01..J-05's own suites/behavior unchanged; J-10's stored golden script replays
  clean with zero heading/`data-testid` collisions (including the new J-05 script).
- TC-17: zero probability/expectancy/significance/advice language in the new disclosures
  (`test_copy_discipline.py`).
- TC-18: spec §3.5 doc edit states the `decline_bars`/`decline_mbr` reading with a source-scan
  test proving `_find_climax_formation`/`detect_capitulation` code lines are byte-unchanged.
- TC-19: the two orphaned run-ledger rows get a documented finding (confirmed cause + fix, or
  explicit unconfirmed-not-reproduced) in the dev handoff.
- TC-20: the new `J-05.json` golden replay script reproduces J-05's browser acceptance
  deterministically without falling back to the LLM lane.
