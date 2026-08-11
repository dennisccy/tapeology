# goal-playbook-iter-4 Dev Handoff

**Phase:** goal-playbook-iter-4
**Date:** 2026-08-10
**Agent:** developer
**Status:** complete

## What Was Built

- **`jbe` (jump-base-explosion, long)** and **`dbi` (drop-base-implosion, short)** — spec
  §3.3-3.4, one shared internal walk (`_continuation_signals` / `_find_one_continuation` in
  `desk_playbook_detect.py`), direction-parameterized so dbi is genuinely jbe's mirror rather than
  a second hand-written copy. Detects a tight consolidation base (`consolidation_range`), a prior
  jump into it, near-extreme/volume-contrast gates, a strict breakout trigger, and (jbe/dbi's own
  exception) up to `PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION` (2) ladder-step firings per
  symbol-session, the second base required to start after the first trigger.
- **`cup_handle` (long only)** — spec §3.6, `detect_cup_handle` in `desk_playbook_detect.py`.
  Searches every confirmed swing-high pivot pair (`swing_pivots`) chronologically for a valid cup
  (depth, duration, middle-third-vs-outer-thirds RVOL contrast) and handle (retrace ≤ 50% of cup
  depth, duration ≤ 30% of cup duration, its own RVOL dryness), firing on the first bar that
  breaks the rim after ≥ 1 confirmed handle bar. Capped at 1 per symbol-session by construction.
- Both new families wired into `compute_playbook`'s per-member walk (`desk_playbook.py`) beside
  `detect_opening_range_breaks`, sharing the SAME per-member absence gate (5m bars / baseline /
  opening range) J-01 shipped — see "Known Issues" below for what this simplification means.
- `PLAYBOOK_SETUPS` extended to the 5-tuple `("open_high_break", "open_low_break", "jbe", "dbi",
  "cup_handle")`; two prose-only spec thresholds promoted to real named constants
  (`PLAYBOOK_BASE_FLATLINE_MAX_MBR = 1.0`, `PLAYBOOK_HANDLE_DESIRABLE_DURATION_FRAC = 0.25`),
  both joined to `playbook_parameters()` and tabulated in `docs/playbook-detector-spec.md` §1 (the
  `PLAYBOOK_OR_MIN_1M_BARS` precedent from a prior iteration).
- `docs/playbook-detector-spec.md` §0: the documentation-only "parameters hash" provenance
  paragraph (the carried item from iter-3's next-step recommendation) — states in writing that
  `playbook_input_signature` + `config_fingerprint` + the served `parameters` blob together ARE
  the goal's own "parameters hash" line. Zero behavior change, zero new field.
- Two new structural guard tests (`tests/test_desk_playbook_guards.py`): a no-threshold-sweep
  source scan (no playbook module iterates a `PLAYBOOK_*` name or a literal numeric candidate
  sequence to pick a threshold) and a detect-never-imports-evidence import-graph guard
  (forward-guards the not-yet-built `desk_playbook_evidence.py`, J-08).
- Frontend: `DeskPlaybookGeometry` (types.ts) gains the JBE/DBI and cup-and-handle fields (all
  optional now, since the shape genuinely differs by `setup_id`; `slots_to_break` stays the one
  universal field); `playbookSetupLabel` gains the three new labels; `PlaybookSignalDetail`
  branches on `signal.setup_id` to render each new setup's own geometry line, verbatim, no
  client-side arithmetic.
- `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` extended with every new served
  geometry numeric, plus a seeded counter-test.
- The three carried housekeeping items closed: deleted the stray browser-QA fixture
  (`apps/backend/.data/playbook/playbook-2026-08-04-e0f249f57785.json`, git-ignored); every
  scratch compute this iteration used `tempfile.mkdtemp()`/pytest `tmp_path`, never the real
  `.data/playbook/` store (verified — the real store still holds exactly the 5 legitimate
  pre-iteration records, none newer); the §0 provenance paragraph is written.

## Files Changed

- `apps/backend/app/research/desk_playbook_detect.py` -- `detect_jbe`, `detect_dbi` (shared
  `_continuation_signals`/`_find_one_continuation` walk), `detect_cup_handle`,
  `_base_lows_ascending` helper.
- `apps/backend/app/research/desk_playbook.py` -- `PLAYBOOK_SETUPS` extended to 5-tuple; two new
  named constants + `playbook_parameters()` entries; `compute_playbook`'s per-member walk loops
  over ALL detected signals (OR-break + jbe list + dbi list + cup_handle) instead of at most one;
  docstring touch-ups.
- `apps/backend/tests/test_desk_playbook_detect.py` -- canonical + near-miss fixture goldens for
  jbe/dbi/cup_handle, a real two-firing JBE ladder test, and a second truncate/mutate lookahead
  harness (`_CONTINUATION_LOOKAHEAD_FIXTURES` + direct cup_handle truncate/mutate tests) alongside
  the untouched OR-break harness.
- `apps/backend/tests/test_desk_playbook.py` -- a real `BarStore`-backed two-firing JBE test (the
  first real exercise of the iter-3 seed-collision fix), and a test proving the new setups tuple
  re-keys the signature while an already-recorded file stays byte-identical and the OR-break
  signal's own content is unaffected.
- `apps/backend/tests/test_desk_playbook_guards.py` (new) -- the two structural guards.
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` extended + counter-test.
- `apps/frontend/lib/types.ts` -- `DeskPlaybookGeometry` gains the new optional fields.
- `apps/frontend/app/desk/page.tsx` -- `playbookSetupLabel` new labels; `PlaybookSignalDetail`
  setup-branching geometry render.
- `docs/playbook-detector-spec.md` -- §0 provenance paragraph; two new §1 constant rows.
- Deleted `apps/backend/.data/playbook/playbook-2026-08-04-e0f249f57785.json` (stray, git-ignored).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **2059 passed, 8 skipped** (floor was ≥ 2036 pass / 8 skip — grew by 23 new tests, zero
regressions).

Also ran: `cd apps/frontend && npx tsc --noEmit` (clean) and `npm run build` (clean production
build, 6/6 static pages).

`Config().config_fingerprint()` still prints `08e471b10130e1e2`. `git diff` is empty against
`desk_forward.py`, `desk_screen*.py`, `setups.py`, `bars.py`, `levels.py`, `config.py`,
`mcp/__init__.py`, and `desk_playbook_features.py` (verified explicitly).

Service startup verified: `scripts/dev.sh` (backend :8301, frontend :3301 at this project's port
offset) — both start clean, `/health` returns `{"status":"ok"}`, `/desk` returns 200. Stopped and
restarted with no port conflicts.

## Design decisions and interpretations (flagged for owner ruling where noted)

1. **Two prose-only spec constants promoted to named constants** (mirrors the
   `PLAYBOOK_OR_MIN_1M_BARS` precedent from a prior iteration): `PLAYBOOK_BASE_FLATLINE_MAX_MBR =
   1.0` (spec §3.3's own "base range ≤ 1.0 MBR" prose) and
   `PLAYBOOK_HANDLE_DESIRABLE_DURATION_FRAC = 0.25` (the HANDLE_MAX_DURATION_FRAC row's own "25%
   desirable" parenthetical). Both are now tabulated in `docs/playbook-detector-spec.md` §1. This
   is a documentation-and-naming promotion of a value the spec already states, not a new
   threshold invented in code — flagged for an owner ruling the same way `PLAYBOOK_OR_MIN_1M_BARS`
   was.
2. **jbe/dbi/cup_handle share the OR-break family's own absence gate** ("5m bars + sufficient
   baseline + a buildable opening range") rather than running independently of the opening-range
   check. Spec §3.1's own edge-case prose scopes "no OR ⇒ absence" to the OR-break family alone,
   so in principle jbe/dbi/cup_handle could fire on a symbol-session with 5m coverage but no
   buildable 1m/5m opening range. I chose NOT to decouple this: the plan's own wording ("wire all
   three into `compute_playbook`'s walk beside `detect_opening_range_breaks`") reads naturally as
   the same call site/gate, and decoupling would touch the shared absence-continue control flow
   J-01/J-02 already shipped (risking TC-11's "zero change to opening-range-break behavior"
   requirement for no real gain — a session with 5m bars but no buildable opening range is rare
   in practice). **Flagged for an owner ruling**: if this proves too conservative once the
   back-scan (J-07) runs over the real recorded universe, decoupling the three new detectors from
   the OR gate is a small, well-scoped follow-up.
3. **`ladder_step_ratio`** is computed as `(this firing's jump_mbr) / (the previous firing's
   jump_mbr)` — the spec states the concept ("vs `PLAYBOOK_LADDER_HEALTHY_LOW`/`_HIGH`") without
   pinning the exact ratio formula; this is the natural "measured-move ladder" reading (successive
   legs compared to the prior leg). `null` on the first firing (no prior step exists).
4. **`base_lows_ascending`** is ONE served field name for both `jbe` and `dbi` (per the goal's own
   Data-contract table), computed as "lows non-decreasing" for jbe (ascending-triangle base) and
   "highs non-increasing" for dbi (the mirrored descending-triangle base) — the direction-
   appropriate check under a shared name, documented in the field's own helper docstring
   (`_base_lows_ascending`).
5. **RVOL-median field names for cup-and-handle** kept exactly as the decomposer's proposal:
   `cup_middle_third_rvol_median`, `cup_outer_third_rvol_median`, `handle_rvol_median` — no change.
6. **`concurrent_signals` stays unwired** (always `[]`) for the new detectors too, matching
   `detect_opening_range_breaks`'s own existing behavior. Cross-detector signal correlation is a
   `compute_playbook`-level concern, not named in this iteration's IN SCOPE/TC list — left for a
   future iteration rather than built speculatively.
7. **Detector function names**: `detect_jbe`, `detect_dbi`, `detect_cup_handle` (the `detect_`
   prefix already established by `detect_opening_range_breaks`), rather than the plan's shorthand
   `jbe`/`dbi`/`cup_handle` prose names — a naming-convention consistency choice, not a behavior
   change.

## Bug found and fixed during development (not in any prior report)

While building `detect_cup_handle`, the initial trigger-search loop only required "≥ 1 handle bar"
(`t > handle_start`), NOT that the right rim's own pivot was actually confirmed
(`t > right["confirmed_at"]`) — since `PLAYBOOK_PIVOT_LOOKBACK_BARS = 3`, this could fire a trigger
BEFORE the right rim's pivot was knowable, a genuine lookahead bug (spec §3.6: "Both rims
pivot-confirmed strictly before `t`"). Fixed before any test was written against it: the trigger
search now starts at `max(handle_start + 1, right["confirmed_at"] + 1)`. Verified via the
truncation/mutation lookahead tests and by direct execution during fixture design (see the
function's own docstring for the reasoning).

## Known Issues

- Item 2 above (jbe/dbi/cup_handle sharing the OR-break absence gate) is the one behavioral
  simplification worth an owner's eyes before the back-scan (J-07) runs over the real recorded
  universe — see that section for the exact tradeoff.
- No browser-QA pass was run by this agent (that is the QA agent's job per the pipeline); the
  frontend build is clean (`tsc --noEmit`, `next build`) and the new render branches were read
  against the served field shapes by hand, but the actual screenshots (TC-1/TC-2/TC-3 of J-04's
  acceptance) still need a real browser pass on the fixture rig.
- This iteration's own dev-time verification never computed a playbook record over the real
  recorded universe (fixture-scoped only, as required) — the real back-scan validation of jbe/dbi/
  cup_handle's actual firing frequency on live data is J-07's job, not this iteration's.
