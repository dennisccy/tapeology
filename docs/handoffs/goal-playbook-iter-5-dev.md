# goal-playbook-iter-5 Dev Handoff

**Phase:** goal-playbook-iter-5
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

- **`detect_capitulation`** (`desk_playbook_detect.py`, spec §3.5, long only) -- a vertical decline
  (`vertical_move` DOWN with the `require_volume`/`rvols`/`rvol_surge` clause this iteration is the
  first to exercise) into a climax bar, followed by the first bar within `PLAYBOOK_BOUNCE_MAX_BARS`
  whose high exceeds the PRIOR bar's own high (`T = high[t-1]`). `leg_low` re-anchors the climax bar
  whenever a new low forms after it before any trigger (the panic still running) -- implemented as a
  shared internal walk, `_find_climax_formation`, that also powers euphoria (below). Invalidation
  `leg_low - 0.30*(T - leg_low)`; capped at 1 per symbol-session by construction; disclosures
  `decline_mbr`, `decline_bars`, `climax_rvol`, `bars_from_climax_to_trigger`; principle `["P1"]`.
  Follows the SAME signal-assembly shape as `detect_opening_range_breaks`/the continuation family
  (entry/entry_kind, `_market_block`, the shared volume/attempt-count disclosures) so it flows
  through `_measure_signal` unmodified.
- **`detect_euphoria`** (`desk_playbook_detect.py`, spec §3.5) -- the exact mirror UP of
  `detect_capitulation` (same `_find_climax_formation` walk, `direction="up"`), returning a MARKER
  event only: `{"trigger_idx": int}`, no side/entry/invalidation/geometry/setup_id. Never appended
  to `detected_signals`/`signals`/`signal_pool`/`baseline_pool` anywhere in `desk_playbook.py` --
  structurally incapable of becoming a served row (proven by a real firing in
  `test_euphoria_marker_never_appears_in_any_signal_pool_or_summary_key`, not just a source scan).
- **`_decorate_markers`** (`desk_playbook.py`, new) -- the marker-decoration pass: sets
  `disclosures.euphoria_recent`/`capitulation_recent` on every signal (any setup, including
  `capitulation` itself) whose own trigger bar (`geometry.slots_to_break`) falls STRICTLY AFTER a
  same-symbol-session marker's trigger bar and within `PLAYBOOK_MARKER_DECAY_BARS` bars of it --
  forward-only by construction (the strict-after comparison also makes a `capitulation` signal's
  self-decoration structurally impossible, with no special-case exclusion needed). Called once per
  member, right after that member's `detected_signals` (now including any `capitulation` firing)
  and `detect_euphoria`'s marker are both resolved, before the measurement loop.
- `compute_playbook` wires `detect_capitulation` into the per-member walk beside the existing four
  detector calls (measured identically via the existing `_measure_signal` pass); `PLAYBOOK_SETUPS`
  extended to the 6-tuple ending `..., "cup_handle", "capitulation"` -- `"euphoria"` deliberately
  never added (it is never a recorded setup).
- `PLAYBOOK_REGISTER` widened to name every shipped setup family (opening-range breaks,
  jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation), closing the OPEN minor
  anti-goal violation carried from iter-4 (the register/blurb text had drifted out of sync with
  J-04's own continuation-family launch). A NEW pinned-text assertion
  (`test_playbook_register_pinned_text_names_every_shipped_setup_family` in
  `test_desk_playbook.py`) locks the exact widened string with a rationale paragraph, so the next
  widening (J-06) fails loudly instead of silently repeating the drift.
- Two new structural guards in `test_desk_playbook_guards.py` (behavioral this time, not
  source-scan, since "does euphoria ever leak" and "is decoration forward-only" are properties of
  DATA the decoration pass produces): `_decorate_markers` never decorates a signal at-or-before a
  marker's own trigger bar, and a `capitulation` signal never self-decorates. Both carry seeded
  counter-tests proving the assertions are real triggers, not vacuous passes.
- `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` extended with `decline_mbr`,
  `climax_rvol`, `bars_from_climax_to_trigger` (`decline_bars` stays out, matching the
  `base_bars`/`cup_bars` bar-count precedent), plus a seeded counter-test.
- Frontend: `DeskPlaybookGeometry` (types.ts) gains the four capitulation-only optional fields;
  `playbookSetupLabel` gains `"capitulation"` -> `"Capitulation"`; `PlaybookSignalDetail` gains a
  capitulation geometry branch (decline magnitude/duration, climax RVOL, bars-to-reversal); the two
  copy spots (`/desk` empty-state sentence and populated-section blurb) widened to name every
  shipped family, matching the backend register widening.
- Zero diff to `desk_playbook_features.py` (as expected -- `vertical_move`'s `require_volume`
  clause already existed from J-01/J-04, unused until this iteration).

## Files Changed

- `apps/backend/app/research/desk_playbook_detect.py` -- `_rvol_series`, `_find_climax_formation`,
  `detect_capitulation`, `detect_euphoria`; `__all__` extended.
- `apps/backend/app/research/desk_playbook.py` -- `PLAYBOOK_SETUPS` extended to 6-tuple;
  `PLAYBOOK_REGISTER` widened; `_decorate_markers` (new); `compute_playbook`'s per-member walk
  wires `detect_capitulation`/`detect_euphoria`/`_decorate_markers`; docstring touch-ups.
- `apps/backend/tests/test_desk_playbook_detect.py` -- capitulation canonical + re-anchoring +
  near-miss/gate-relaxed-control fixtures, the truncate/mutate lookahead property test extension,
  and the euphoria marker canonical + near-miss fixtures.
- `apps/backend/tests/test_desk_playbook.py` -- capitulation wiring test (real `BarStore` walk),
  the euphoria-never-leaks structural proof (a real firing, not a source scan), the marker
  decoration end-to-end test (a single session with an early euphoria formation decorating a later,
  independent capitulation firing), the TC-9/TC-10 setups-tuple re-key test (mirrors the J-04
  precedent), and the register pinned-text test; the pre-existing J-04 setups-tuple test's
  "restore the current PLAYBOOK_SETUPS" assertion updated from 5 to 6 entries (a live "what does
  the tuple currently say" assertion, not a frozen discipline guard -- see its own updated comment).
- `apps/backend/tests/test_desk_playbook_guards.py` -- two new behavioral guards (marker-decoration
  forward-only + capitulation self-exclusion), each with a seeded counter-test.
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` extended + counter-test.
- `apps/frontend/lib/types.ts` -- `DeskPlaybookGeometry` gains the capitulation-only fields.
- `apps/frontend/app/desk/page.tsx` -- `playbookSetupLabel`; `PlaybookSignalDetail` capitulation
  geometry branch; the two widened copy spots.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/` (project `addopts = "-q"`; adding a
second explicit `-q` on the command line stacks to `-qq`, which suppresses pytest 9.1.1's final
summary line -- noted here since prior handoffs' quoted command includes an explicit `-q` that
would trigger the same suppression; the dot/percentage progress and per-file counts are unaffected
either way, only the trailing "N passed in Xs" line is).
Result: **2079 passed, 8 skipped** in 152.32s. Zero failures (floor was ≥ 2061 pass / 8 skip --
grew by 20 new tests net of the one pre-existing J-04 assertion updated in place for the tuple's
new length; zero regressions).

Also ran: `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_playbook_detect.py
tests/test_desk_playbook.py tests/test_desk_playbook_guards.py tests/test_desk_ui_guards.py` in
isolation during development (all green throughout).

`Config().config_fingerprint()` still prints `08e471b10130e1e2`. `git diff` is empty against
`desk_forward.py`, `desk_screen*.py`, `setups.py`, `bars.py`, `levels.py`, `config.py`,
`mcp/__init__.py`, and `desk_playbook_features.py` (verified explicitly).

Frontend: `cd apps/frontend && npx tsc --noEmit` (clean) and `rm -rf .next && npm run build`
(clean production build, 6/6 static pages, `/desk` bundle 27.7 kB / 139 kB first load).

## Fixture correctness

Every capitulation/euphoria fixture (canonical firing, re-anchoring, near-miss + gate-relaxed
control, the compute_playbook-level wiring/decoration/euphoria-never-leaks fixtures) was verified
by direct execution against the real `detect_capitulation`/`detect_euphoria`/`compute_playbook`
code before being written into pytest assertions -- not hand-derived-and-trusted.

## Service startup verification

`scripts/dev.sh` (backend `:8301`, frontend `:3301` at this project's port offset) -- started
clean, `GET /health` returned `{"status":"ok"}`, `GET /desk` returned 200. Stopped (all backend/
frontend/wrapper processes killed, ports verified free) and restarted cleanly with zero port
conflicts; `/health`/`/desk` re-verified after the restart.

## Known Issues

- No real browser screenshot pass was taken by this agent -- that is the browser-qa-agent's job
  (per the phase spec's TESTING REQUIREMENTS). The capitulation geometry branch and the decoration
  chips (`disclosures.euphoria_recent`/`capitulation_recent`, already wired since a prior iteration)
  were verified against the ACTUAL served field shapes via `compute_playbook` fixtures during
  development, and the frontend passes `tsc`/`next build` cleanly, but visual legibility on the
  fixture rig (TC-1/TC-2/TC-3) and the carried DBI screenshot re-take (TC-18) are unverified by this
  handoff -- both need a T-9 clean-rebuilt real browser pass.
- The two carried owner-ruling questions from iter-4 (the 1.5x jump-to-base gate reachability under
  `BASE_MAX_RANGE_MBR`/`JUMP_MIN_MOVE_MBR`; the cup rim constant naming) remain open, unrelated to
  and unblocked by this iteration's own scope -- still surfaced in `iteration-state.md`'s "Owner
  rulings pending" list (not re-litigated here).
- No new `data-testid`/heading string introduced this iteration
  (`desk-playbook-signal-capitulation-geometry`, plus the label "Capitulation") collides with any
  of the 20 stored `goal-session-desk` golden scripts or this session's own `J-01`/`J-02`/`J-03`/
  `J-10.json` scripts (grepped explicitly across every `runs/*/journey-scripts/*.json` in the repo
  -- zero hits).
- The re-anchoring semantics implemented (`leg_low`/the climax bar track the running minimum low
  from the FIRST candidate vertical-move window's own start through the current scan position,
  re-anchoring to whichever bar sets that running minimum) is this developer's concrete reading of
  spec §3.5's terse "a new low after v re-anchors v" sentence -- documented in
  `_find_climax_formation`'s own docstring. `decline_bars`/`decline_mbr` (the goal's own data-
  contract phrasing "bars from the -- possibly re-anchored -- climax bar to leg_low's formation"
  read literally would give a degenerate always-zero field, since the climax bar IS where leg_low
  forms) were implemented instead as the WHOLE decline leg's span/magnitude (from the first
  candidate window's own start through the final, possibly re-anchored, climax bar) -- a
  genuinely useful disclosure that grows when re-anchoring extends the panic, verified in the
  dedicated re-anchoring fixture test. Flagged here in case an owner ruling on the exact phrasing
  is wanted; no code behavior is ambiguous, only the docs/goal.md table's own wording.
