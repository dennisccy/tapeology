# goal-playbook-iter-4 Execution Plan

## What to Build

Target journey **J-04: The continuation family — JBE, DBI, cup-and-handle**. Three new detectors
land in the existing `desk_playbook_detect.py` module and fire beside the already-shipped
opening-range-break detectors, rendering into the ALREADY-SHIPPED `/desk` Playbook Signals section
(J-03) with zero structural UI rework.

- `jbe` (jump-base-explosion, long, spec §3.3): consolidation-range base gated on bar count +
  `PLAYBOOK_BASE_MAX_RANGE_MBR`, a jump over `PLAYBOOK_JUMP_LOOKBACK_BARS` gated on
  `PLAYBOOK_JUMP_MIN_MULT`/`PLAYBOOK_JUMP_MIN_MOVE_MBR`, near-extreme gate
  (`PLAYBOOK_NEAR_EXTREME_MBR`), volume-contrast gate (`PLAYBOOK_VOL_CONTRAST_RATIO`), trigger on
  first bar `high > U`, invalidation `L − 0.30·(U−L)`, cap 2/session with a second base starting
  after the first trigger, principles `["P3","P4"]`.
- `dbi` (drop-base-implosion, short, spec §3.4): exact direction-flipped mirror of `jbe`, same
  primitives/gates/cap.
- `cup_handle` (long only, spec §3.6): left/right rims via confirmed `swing_pivots` within
  `PLAYBOOK_RIM_MATCH_MBR`, depth ≥ `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR`, duration ≥
  `PLAYBOOK_CUP_MIN_BARS` (disclose `cup_optimal` at `PLAYBOOK_CUP_OPTIMAL_BARS`), cup + handle
  volume-contrast checks, handle retrace ≤ `PLAYBOOK_HANDLE_MAX_RETRACE_FRAC`, handle duration ≤
  `PLAYBOOK_HANDLE_MAX_DURATION_FRAC` × cup duration (disclose `handle_duration_desirable` at
  25%), trigger on first bar after ≥1 handle bar with `high > max(left_rim, right_rim)`,
  invalidation `handle_bottom − 0.30·(T − handle_bottom)`, cap 1/session, principles
  `["P4","P5-inverse"]`. A handle retracing beyond 50% voids the formation silently (no
  cross-detector suppression — spec §4).
- Wire all three into `compute_playbook`'s walk beside `detect_opening_range_breaks`; extend
  `PLAYBOOK_SETUPS` to the 5-tuple. `playbook_input_signature` moves for future computes
  (expected, disclosed); every already-recorded J-01/J-02/J-03-era file must stay byte-identical
  (proven by SHA-256, not just "no code touched it").
- **Zero new primitive** in `desk_playbook_features.py` — `swing_pivots`/`consolidation_range`/
  `vertical_move`/`side_sign` already exist; the new detectors call them, they do not extend them
  (expected zero diff to that file).
- Two new structural guards: (a) source-scan test — no playbook module contains a
  loop/comprehension iterating over a `PLAYBOOK_*` constant or a candidate-value sequence to pick
  a threshold; (b) import-graph test — `desk_playbook_detect.py` imports nothing named
  `*evidence*` (forward-guards a module that doesn't exist yet, J-08).
- Frontend: `DeskPlaybookGeometry` (types.ts) gains the JBE/DBI + cup-and-handle fields;
  `playbookSetupLabel` gains the three new labels; `PlaybookSignalDetail` branches on
  `signal.setup_id` to render each new setup's own geometry line — no other UI structure changes.
- `test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` gains every new served numeric
  (`jump_mbr`, `base_range_mbr`, `ladder_step_ratio`, `cup_depth_mbr`, `handle_retrace_frac`,
  `handle_duration_frac`, the three cup/handle RVOL medians) + a seeded counter-test.
- **Three carried housekeeping items** (from iter-3's next-step recommendation, bundled into this
  cycle):
  1. Delete the stray browser-QA fixture record
     `apps/backend/.data/playbook/playbook-2026-08-04-e0f249f57785.json` (git-ignored,
     self-disclosing); scope this iteration's own browser-QA plants/computes to
     `TAPEOLOGY_DESK_PLAYBOOK_DIR` (+ `_LOG_DIR`/`_BACKSCAN_LOG_DIR`) scratch paths, never the
     operator's real store — document the env vars used in the dev handoff.
  2. `docs/playbook-detector-spec.md` §0: add one documentation-only paragraph stating that
     `playbook_input_signature` + `config_fingerprint` + the verbatim parameters blob together ARE
     the provenance line's "parameters hash" — no new field, zero behavior change (proven by a
     test that no source constant/served field moved).
  3. Re-take the lower `/desk` section screenshots for the J-10 regression walk using the
     documented sibling-`display:none`-collapse technique (iter-3 lesson), not a blind deep
     `scrollTo`.

Everything else — the climax family (J-05), the range family (J-06), the back-scan (J-07), the
evidence view (J-08), MCP v4 (J-09) — is explicitly OUT OF SCOPE this iteration.

## Agents Required

- backend-data: yes -- three new detectors in `desk_playbook_detect.py`, compute-walk wiring in
  `desk_playbook.py`, two new structural guard tests, fixture goldens + lookahead-property
  extensions, spec doc paragraph, stray-fixture deletion.
- frontend-ux: yes -- `types.ts` geometry field additions, `page.tsx` per-setup detail rendering
  branch, guard-test field additions; no new route, no new section, no new user action.

## Frontend Present

yes

## Files to Create/Modify

- `apps/backend/app/research/desk_playbook_detect.py` -- add `jbe`, `dbi`, `cup_handle` detector
  functions, mirroring `detect_opening_range_breaks`'s (formation → trigger → invalidation →
  disclosures → principles) shape (:188 in the current tree — re-locate by symbol name).
- `apps/backend/app/research/desk_playbook.py` -- extend `PLAYBOOK_SETUPS` (:137) to the 5-tuple;
  wire the three new detectors into the compute walk beside the `detect_opening_range_breaks`
  call site (:562); `playbook_parameters()` (:203) already reads most of the needed constants
  (jump/base/cup/handle thresholds are already present in the module per the constants table —
  verify against `docs/playbook-detector-spec.md` §1 and add anything genuinely missing).
- `apps/backend/app/research/desk_playbook_features.py` -- **expected zero diff**; the three new
  detectors call `swing_pivots` (:171), `consolidation_range` (:196), `vertical_move` (:216),
  `side_sign` (:300) as-is.
- `apps/backend/tests/test_desk_playbook_detect.py` -- fixture goldens for `jbe`/`dbi` (canonical
  firing + near-miss each) and `cup_handle` (canonical firing + near-miss); extend
  `_LOOKAHEAD_FIXTURES` with all three canonical fixtures.
- `apps/backend/tests/test_desk_playbook.py` -- TC-8 (real two-firing JBE fixture proving
  independent, non-colliding baseline anchors via the iter-3 seed-collision fix), TC-9/TC-10
  (byte-identical existing files + re-keyed back-dated fixture, both via SHA-256), TC-14 (duplicate
  key still raises).
- New test file for the two structural guards (source-scan no-threshold-sweep test +
  detect-never-imports-evidence import-graph test) — place alongside the existing playbook test
  files (e.g. extend `test_desk_playbook_detect.py` or a small new
  `test_desk_playbook_guards.py`, developer's call).
- `apps/backend/tests/test_desk_ui_guards.py` -- extend `_PRICE_ARITHMETIC_FIELDS` (:160) with the
  new geometry numerics + seeded counter-test additions.
- `docs/playbook-detector-spec.md` -- §0 provenance-line paragraph (documentation only).
- `apps/frontend/lib/types.ts` -- extend `DeskPlaybookGeometry` (:1480) with the JBE/DBI +
  cup-and-handle fields listed in the Data-contract table below.
- `apps/frontend/app/desk/page.tsx` -- `playbookSetupLabel` (:4401) gains `"jbe"`, `"dbi"`,
  `"cup_handle"` labels; `PlaybookSignalDetail` (:4553) branches on `signal.setup_id` to render
  each new setup's geometry line.
- Delete: `apps/backend/.data/playbook/playbook-2026-08-04-e0f249f57785.json` (stray browser-QA
  fixture, git-ignored).
- `docs/handoffs/goal-playbook-iter-4-dev.md` -- dev handoff (required deliverable).

### New served fields (within the already-registered `GET /research/desk/playbook` payload — no
new endpoint, no new owner)

| Field | Shape | On |
|---|---|---|
| `setup_id` | now includes `"jbe" \| "dbi" \| "cup_handle"` | `signal` |
| `geometry.jump_mbr`, `geometry.base_range_mbr` | `number` | JBE/DBI |
| `geometry.base_bars` | `int` | JBE/DBI |
| `geometry.base_flatline`, `geometry.base_lows_ascending` | `boolean` | JBE/DBI |
| `geometry.ladder_step_ratio` | `number \| null` | JBE/DBI |
| `geometry.cup_bars` | `int` | cup_handle |
| `geometry.cup_depth_mbr`, `geometry.handle_retrace_frac`, `geometry.handle_duration_frac` | `number` | cup_handle |
| `geometry.cup_optimal`, `geometry.handle_duration_desirable` | `boolean` | cup_handle |
| `geometry.cup_middle_third_rvol_median`, `geometry.cup_outer_third_rvol_median`, `geometry.handle_rvol_median` | `number` | cup_handle |

## UI Evolution

- New user-facing capability: the same Playbook Signals table (already shipped) can now display
  three additional setup types firing on a recorded session — jump-base-explosion,
  drop-base-implosion, cup-and-handle — each with its own geometry disclosure line.
- New information displayed: per-setup geometry fields listed above, rendered in the existing
  expandable signal-detail panel.
- New user actions: none — the same session-date input + Run Playbook trigger/poll/cancel
  already shipped in J-03 now simply surfaces more setup types.
- UI surface changes: none structural — the existing Playbook Signals section gains conditional
  rendering branches; no new section, no new route.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing signal-row/expandable-detail pattern and chip styling
  (`CHIP_CLASS`) already shipped for open-high/open-low break signals — the three new setups are
  additional cases in the same renderer, not a new component.
- Layout: unchanged — geometry lines render inside the already-shipped `PlaybookSignalDetail`
  expansion beneath the signals table.
- Key visual effects: none new — house style (dark-only, dense, terminal-grade) carries forward
  unchanged; no marketing chrome, setup names are the book's own.
- States to handle: near-miss fixtures must render NO signal (silent, not an error state); a
  cup-and-handle handle retracing beyond 50% voids silently and must not appear as a false
  cup_handle row (it may independently fire under a different detector).

## Key Test Scenarios

- TC-1/TC-2/TC-3: canonical JBE, DBI, and cup-and-handle fixture sessions each render their own
  signal row + setup chip + geometry line matching hand-computed values (browser screenshot).
- TC-4/TC-5/TC-6: near-miss fixtures for each of the three detectors produce zero signal for that
  symbol-session (JBE jump-too-small, DBI mirror, cup-and-handle handle-too-deep).
- TC-7: the generic truncate-after-trigger + mutate-post-trigger-bars lookahead property test
  passes for all three new detectors' canonical fixtures.
- TC-8: a real fixture where the same `(symbol, "jbe")` fires twice in one session draws two
  independent, non-colliding baseline anchors (first real exercise of the iter-3 seed-collision
  fix, not just a synthetic collision test).
- TC-9/TC-10: every existing J-01/J-02/J-03-era recorded file stays byte-identical (SHA-256) after
  the new constants join `playbook_parameters()`; a back-dated fixture recomputed post-iteration
  mints a NEW `playbook_input_signature` beside the untouched old file.
- TC-11: J-01/J-02 suites (99+ tests) and J-03's shipped session-date/Run/poll/cancel/absence/
  refusal behavior all still pass with zero change to opening-range-break content.
- TC-12: the new source-scan guard finds zero threshold-sweep loops across all three playbook
  modules.
- TC-13: the new import-graph guard finds zero `*evidence*` import in `desk_playbook_detect.py`.
- TC-14: a duplicate `(session_date, playbook_input_signature)` key still raises
  `PlaybookAlreadyRecorded` (unmodified store write path).
- TC-15: `test_copy_discipline.py` finds zero probability/expectancy/advice language in the new
  geometry disclosures.
- TC-16: full backend suite ≥ 2036 pass / 8 skip; `Config().config_fingerprint()` prints
  `08e471b10130e1e2`; `git diff` empty against `desk_forward.py`, `desk_screen*.py`, `setups.py`,
  `bars.py`, `levels.py`, `config.py`, `mcp/__init__.py`, `desk_playbook_features.py`.
- TC-17: T-9 clean rebuild (`rm -rf apps/frontend/.next`); every shipped `/desk` section
  (including the lower ones, via the sibling-`display:none`-collapse technique) walked and
  screenshotted; J-10's stored golden replay script passes with zero heading/`data-testid`
  collisions.
- TC-18: the stray fixture file no longer exists on disk; this iteration's browser-QA env is
  proven (in the QA report) to target `TAPEOLOGY_DESK_PLAYBOOK_DIR`, never the real store.
- TC-19: `docs/playbook-detector-spec.md` §0 states the signature+fingerprint+parameters-blob
  provenance ruling in writing, with no source constant or served field moved.

## Notes for the developer

- If any one of the three detectors is found ambiguous or unimplementable exactly as the spec
  states, drop THAT detector from the iteration, record the drop, and surface it for an owner
  ruling — do not improvise a rule to force all three green.
- RVOL-median field names for cup-and-handle
  (`cup_middle_third_rvol_median`/`cup_outer_third_rvol_median`/`handle_rvol_median`) are the
  decomposer's proposal, not spec-pinned literals — keep the three values distinct; note actual
  chosen names in the dev handoff if changed.
- No blueprint edit needed this iteration (the "Playbook records" row already names J-04 as
  extending the same shared detect module).
- No `Config` field, no fingerprint-epoch change, zero diff to `desk_forward.py` — measurement
  helpers are imported only.
