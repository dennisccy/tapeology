# goal-playbook-iter-6 Dev Handoff

**Phase:** goal-playbook-iter-6
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

- **`detect_range_trade`** (`desk_playbook_detect.py`, spec §3.7, PROVISIONAL tier) -- support-bounce
  long + resistance-fade short, checked independently (cap 1 per side per symbol-session), collapsed
  into one served `setup_id` ("range_trade") the way `open_high_break`/`open_low_break` already
  share one detector family. Arming: at each candidate bar `t`, the session's own prefix extremes
  (`SH`/`SL` over `session_bars[:t]`) must be `>= PLAYBOOK_RANGE_MIN_WIDTH_MBR` wide, with `>= 2`
  touches (`zone_touches`) of the armed side's own `NEAR_EXTREME_MBR`-wide zone -- evaluated as a
  genuine arming COMPLETION only the first `t` at which the most recent touch is `t-1` itself (so the
  same pair is never re-attempted on later, untouched bars). Trigger: from the completing touch `b`,
  scans up to `PLAYBOOK_BOUNCE_MAX_BARS` for the reversal-bar grammar (`high > high[t-1]` long /
  `low < low[t-1]` short), gated at every candidate bar by `min(low[b..t-1]) >= SL - HOLD_TOL*MBR`
  (mirrored short) -- the first bar where that hold check fails ends the scan (a strict break beyond
  the zone dissolves range-mode, spec's own edge case). Invalidation `SL - 0.30*(T-SL)` (short
  mirrored); disclosures `range_width_mbr`, `low_zone_touches`, `high_zone_touches`,
  `crossed_midrange`, `absorption_bar_present`.
  **Design note (documented in the module docstring too):** the trigger's reversal-bar predicate is
  the SAME comparison `_find_climax_formation`'s own bounce trigger uses (spec §3.7's "same
  reversal-bar grammar as the capitulation bounce" framing), but is NOT literally routed through
  `_find_climax_formation` -- that function's own arming precondition is a `vertical_move` formation
  with re-anchoring, a formation range_trade does not share (range_trade arms via `zone_touches`,
  never a vertical move). Forcing a shared call site would either bend `_find_climax_formation` to a
  formation it was never built for or risk J-05's own byte-identical behavior for a J-06 need it does
  not have; the one-line predicate is duplicated under a cross-referenced docstring instead.
  **Field-name degeneracy check (the iter-5 lesson):** `crossed_midrange` and
  `absorption_bar_present` are this developer's own concrete readings of spec §3.7's vague "BOOK
  midrange rule"/"passive accumulation" prose (neither is pinned to a formula in the canonical spec)
  -- verified NOT identically constant: `crossed_midrange` is `True` on the canonical long fixture and
  `False` on the canonical short fixture (an independent hand-built mirror, not merely negated
  values); `absorption_bar_present` is `False` on both canonical fixtures (a real, reachable
  condition -- `RVOL >= RVOL_ELEVATED` AND bar range `<= HOLD_TOL*MBR` on a touch bar -- that simply
  did not fire on either hand-designed fixture; the two-part gate itself is exercised as reachable by
  construction, not degenerate).
- **`detect_double_top`/`detect_double_bottom`** (`desk_playbook_detect.py`, spec §3.8-3.9, exact
  mirror, one shared internal walk `_find_double_extreme`) -- two confirmed swing pivots (`p1 < p2`,
  HIGHS for double_top / LOWS for double_bottom) within `PLAYBOOK_TOPS_MATCH_MBR`, separated by
  `>= PLAYBOOK_TOPS_MIN_SEPARATION_BARS`, both near the session extreme at their own (already-
  confirmed) times; a valley/peak (min low / max high strictly between them) with depth
  `>= PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR` gated against the SHALLOWER of the two pivots (the
  conservative reading). Trigger: the first bar breaking the valley/peak, `p2` pivot-confirmed
  STRICTLY BEFORE the trigger bar -- a bar breaking the valley/peak inside `p2`'s own confirmation
  window (`[p2.index, p2.confirmed_at]`) fails the WHOLE pair closed (TC-10; never delays the trigger
  search past confirmation, which would silently misrepresent when the actual break happened).
  Invalidation uses the FARTHER (worse-case) pivot -- max top for double_top, min bottom for
  double_bottom -- so `nominal_risk_mbr` is the full, never-shrunk pattern height, distinct from the
  shallower-pivot depth the formation GATE uses. Capped at 1 per detector per symbol-session (single
  return, first validating-and-triggering pivot pair, the `detect_cup_handle` rim-pair-search
  precedent). Disclosures `tops_gap_mbr`, `tops_separation_bars`, `valley_depth_mbr`,
  `nominal_risk_mbr`, `second_top_rvol_vs_first` (median RVOL of p2±1 / p1±1, `None` when either
  median is unavailable). The already-served `disclosures.attempt_count` field is reused verbatim for
  the "≥3 attempts" reading -- no new field.
- `compute_playbook` wires all three new detectors into the per-member walk beside the existing five
  (same absence gate, same `_measure_signal` pass, same baseline draw); `PLAYBOOK_SETUPS` extended to
  the 9-tuple ending `..., "range_trade", "double_top", "double_bottom"`.
- `PLAYBOOK_REGISTER` widened to name all eight shipped setup families (opening-range-break,
  jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation, range-trade, double-top,
  double-bottom) -- the third occurrence of this pattern this session (J-04, J-05, now J-06). The
  re-derived pinned-text test (`test_playbook_register_pinned_text_names_every_shipped_setup_family`)
  carries its own rationale paragraph.
- New behavioral guard (`test_desk_playbook_guards.py`): a call-counting stub/double patched onto the
  REAL `app.research.tradability.compute_tradability`/`app.research.levels.compute_levels` proves
  `compute_playbook` calls neither, zero times, over a real `BarStore`-backed fixture walk that fires
  all eight setup families across eight members in one universe -- instrumentation (survives future
  refactors), not a source-scan regex, plus a seeded counter-test.
- New source-hash guard (TC-18, `test_desk_playbook_guards.py`): pins `_find_climax_formation`'s and
  `detect_capitulation`'s own source (via `inspect.getsource`) to the exact SHA-256 they hashed to
  before this iteration's doc-only spec edit, plus a companion check that every `PLAYBOOK_*` constant
  those two functions read is unchanged -- proving the spec prose addition below moved zero code and
  zero numbers.
- `docs/playbook-detector-spec.md` §3.5 gained prose (closing iter-5's OPEN minor anti-goal item)
  stating exactly what `decline_bars`/`decline_mbr` measure and how the re-anchoring walk works --
  transcribing the reading `_find_climax_formation`/`detect_capitulation` already ship (per the
  assumption-ledger entry "iter-6 -- goal-decomposer"). Zero diff to any `PLAYBOOK_*` constant or to
  either function's code lines (proven by the pinned-hash guard above).
- Two new `compute_playbook`-level wiring tests (`test_desk_playbook.py`): range_trade and
  double_top/double_bottom each join the SAME per-member walk as every other family (`forward`/
  `invalidation_breached` attached, `summary`/`baseline_anchors` keyed correctly) -- real `BarStore`
  walks, not just detector-level pure-function fixtures.
- New setups-tuple re-key test (TC-13/TC-14, mirroring the J-04/J-05 precedent exactly): a file
  recorded under the pre-J-06 (6-setup) parameters stays byte-identical on disk after a fresh compute
  under the current (9-setup) parameters mints a genuinely new, differently-signed version beside it.
- `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` extended with `range_width_mbr`,
  `tops_gap_mbr`, `valley_depth_mbr`, `nominal_risk_mbr`, `second_top_rvol_vs_first` (bar-count/int-
  count fields -- `tops_separation_bars`, `low_zone_touches`, `high_zone_touches` -- stay OUT,
  following the `base_bars`/`cup_bars`/`decline_bars` precedent), plus a seeded counter-test.
- Frontend: `DeskPlaybookGeometry` (types.ts) gains the range_trade-only and double_top/
  double_bottom-only optional fields; `playbookSetupLabel` gains `"range_trade"` -> "Range Trade",
  `"double_top"` -> "Double Top", `"double_bottom"` -> "Double Bottom"; `PlaybookSignalDetail` gains a
  range_trade geometry branch and a double_top/double_bottom geometry branch (verbatim `fmt()`
  display, zero client-side arithmetic, same pattern as every prior setup branch); the two copy spots
  (`/desk` empty-state sentence, populated-section blurb) widened to name all eight families.
- Zero diff to `desk_playbook_features.py` (as expected -- every primitive the three new detectors
  need, `zone_touches`/`swing_pivots`/`side_sign`, already existed).
- Investigated the two orphaned `.data/playbook_runs/playbookrun-2026-08-11-{9af9d27134e1,
  f24507d3e644}.json` rows -- see "Known Issues" below for the finding.
- Recorded `runs/goal-session-playbook/journey-scripts/J-05.json` -- see "Known Issues" for the
  verification method and its one disclosed limitation.

## Files Changed

- `apps/backend/app/research/desk_playbook_detect.py` -- `_range_trade_side`, `detect_range_trade`,
  `_find_double_extreme`, `detect_double_top`, `detect_double_bottom`; `__all__` extended; module
  docstring gains the range_trade design note.
- `apps/backend/app/research/desk_playbook.py` -- `PLAYBOOK_SETUPS` extended to 9-tuple;
  `PLAYBOOK_REGISTER` widened; `compute_playbook`'s per-member walk wires `detect_range_trade`/
  `detect_double_top`/`detect_double_bottom`; docstring touch-ups.
- `apps/backend/tests/test_desk_playbook_detect.py` -- canonical + near-miss/gate-relaxed-control
  fixtures for range_trade (both sides) and double_top/double_bottom (both, plus the p2-inside-
  confirmation-window fail-closed fixture), the lookahead property test extension (own harness, per
  the J-04/J-05 precedent of not touching the OR-break harness).
- `apps/backend/tests/test_desk_playbook.py` -- compute_playbook-level wiring tests for range_trade
  and double_top/double_bottom, the re-derived register pinned-text test with rationale paragraph,
  the J-06 setups-tuple re-key test (TC-13/TC-14), and small "live" assertion updates in two J-04/J-05
  tests whose own `PLAYBOOK_SETUPS[-1] ==`/literal-list assertions needed to track the tuple's new,
  legitimately-longer real value (the same maintenance those tests' own comments already document as
  expected each time the tuple grows).
- `apps/backend/tests/test_desk_playbook_guards.py` -- the new zero-`compute_tradability`/
  zero-`compute_levels` call-counting guard (with counter-test) and the decline-disclosure doc-edit
  source-hash guard (with counter-test).
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` extended + counter-test.
- `docs/playbook-detector-spec.md` -- §3.5 doc-only prose addition (decline_bars/decline_mbr +
  re-anchoring reading).
- `runs/goal-session-playbook/journey-scripts/J-05.json` -- new stored golden replay script.
- `apps/frontend/lib/types.ts` -- `DeskPlaybookGeometry` gains the new optional fields.
- `apps/frontend/app/desk/page.tsx` -- `playbookSetupLabel`; two new `PlaybookSignalDetail` geometry
  branches; the two widened copy spots.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **2098 passed, 8 skipped** in 194.38s. Zero failures (floor was >= 2079 pass / 8 skip -- grew
by 19 new tests net of zero removed/skipped; zero regressions). Two other full runs during
development also showed zero `F` markers and the expected 8 skips (their trailing summary line was
suppressed by the project's own `pytest.ini` `addopts = "-q"` stacking with an extra `-q`/pipe
truncation on those particular invocations -- the same iter-5 handoff gotcha; this final run avoided
it). Targeted runs throughout development, all green:
- `pytest tests/test_desk_playbook_detect.py tests/test_desk_playbook.py tests/test_desk_playbook_guards.py tests/test_desk_playbook_features.py`
- `pytest tests/test_desk_ui_guards.py tests/test_copy_discipline.py`

`Config().config_fingerprint()` == `08e471b10130e1e2` (verified unchanged; zero new `Config` fields).
`git diff --stat` against `desk_forward.py`/`desk_screen*.py`/`setups.py`/`bars.py`/`levels.py`/
`config.py`/`mcp/__init__.py`/`desk_routes.py`/`desk_playbook_features.py` is empty (verified).
`npx tsc --noEmit` in `apps/frontend` -- zero errors.

## Frontend

Frontend work is documented in this same handoff (no separate `-frontend.md` this iteration -- the
frontend delta is small and entirely described above under "What Was Built"/"Files Changed": two new
`PlaybookSignalDetail` geometry branches plus the two copy-spot widenings, all reusing the exact
established rendering pattern with zero new components).

## Known Issues

**TC-19 -- the two orphaned run-ledger rows (investigated, cause identified, fix applied to this
iteration's own runs, no product code change).**
`apps/backend/.data/playbook_runs/playbookrun-2026-08-11-{9af9d27134e1,f24507d3e644}.json` each name
a `playbook_id` (`playbook-2026-08-08-cc26e2c49bf4`, `playbook-2026-08-07-7e8d3e936847`) that does not
exist under `apps/backend/.data/playbook/` (confirmed by directory listing). Findings:
- Both rows carry `playbook_input_signature: "898af0960779e897"`. The CURRENTLY-recorded files for the
  same two session dates (`playbook-2026-08-07-fe29f0b6eb53.json`, `playbook-2026-08-08-27e45e6888ea.json`)
  carry a DIFFERENT signature (`5b70ba860b5efd47`) and were recorded EARLIER
  (`2026-08-10T19:47-19:51Z`) than the two orphaned runs (`started_at 2026-08-11T00:04-00:19Z`, ~4.5h
  later) -- so a second, real compute ran against those same two dates under code whose parameters
  had since changed, minted a genuinely new (at-the-time) signature, and (per its own
  `outcome: "recorded"`) DID write two record files -- which are no longer present.
- Trace-log timestamps place these two runs inside iter-5's own `0041-browser-qa-agent` step's
  execution window (its own log finished at local 01:23, ~19 minutes after the second orphaned run's
  own `started_at`) -- consistent with a REAL "Run Playbook" browser interaction during iter-5's
  browser-QA pass.
- The dates involved (2026-08-07/08) are real, near-"today" trading-calendar dates for the REAL
  101-member universe, not one of the fixture rig's synthetic tickers (LADDER/DBI1/CUP1/AAA/DECOR) --
  consistent with this compute having run against the LIVE, UNSCOPED `apps/backend/.data/` store
  rather than a `TAPEOLOGY_DESK_PLAYBOOK_DIR`-scoped fixture directory, exactly the general scoping
  gap the iter-3 lesson already named ("scope every browser-QA compute ... never the operator's real
  `.data/playbook/` store").
- **Not fully confirmed:** exactly what removed the two record files afterward. `.data/` is fully
  gitignored (never tracked by git, ruling out a git operation); `PlaybookRunLogStore`/`PlaybookStore`
  expose no delete method anywhere (by design), so no CODE path could have "fixed" the ledger to
  match -- the two run rows are therefore permanently orphaned unless someone manually removes the
  ledger files too (which this iteration deliberately does NOT do -- an append-only store's own files
  are never hand-edited as a "fix"). Most plausibly a later cleanup step removed the two stray record
  files from the real store without also touching their sibling run-ledger directory, but this
  developer could not verify that specific action from the available trace logs.
- **Fix applied to this iteration's own runs (not a product-code change, exactly as the iteration
  spec expected):** this iteration's own J-05.json verification pass (see below) scoped ALL FOUR
  relevant env vars together -- `TAPEOLOGY_BAR_DIR`, `TAPEOLOGY_DESK_UNIVERSE_DIR`,
  `TAPEOLOGY_DESK_PLAYBOOK_DIR`, `TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR` -- to one shared scratch root,
  so both the fixture bars/universe AND the resulting playbook record/run-ledger writes landed
  together in the SAME scoped location, never touching the operator's real store. This is the
  concrete instance of "scope every browser-QA compute/plant to `TAPEOLOGY_DESK_PLAYBOOK_DIR` + its
  log-dir env vars" the iteration asked for; the next browser-QA pass (and any future one) should use
  the same four-variable scoping together.

**J-05.json's own verification method and one disclosed limitation.** The script was verified against
a REAL, live browser pass (Chrome via CDP, the frontend dev server already running) -- but against
this developer's OWN minimal, single-member (`DECOR`-only) scoped fixture rig (see above), not the
multi-symbol (LADDER/DBI1/CUP1/AAA/DECOR) rig iter-5's own QA report describes, which is not
reproducible from anything committed to the repo (no seed script exists for it; it was set up ad hoc
by that iteration's browser-QA agent). Against the single-member rig, `desk-playbook-signal-row`
resolves unambiguously to the one capitulation/DECOR row, and clicking it renders "euphoria recent"
exactly as the script expects -- confirmed live, not guessed. In a future multi-symbol rig, the
generic testid-only click target could in principle resolve to a DIFFERENT row than the
euphoria-decorated one if a capitulation signal from another member sorts earlier in the served
`signals` list (the same generic-click pattern J-02.json's own script already uses, with a weaker,
row-independent assertion). This developer judged the residual risk acceptable given the precedent
and the live verification performed, but flags it explicitly rather than claiming full certainty --
the browser-QA agent running after this handoff is best positioned to confirm or adjust it against
whatever rig it actually sets up.

**range_trade's own design latitude (documented, not a gap).** Spec §3.7 is explicitly the vaguest,
PROVISIONAL-tier rule in the canonical spec. This developer implemented the trigger grammar precisely
as spelled out in the iteration's own IN SCOPE text ("a bar touches the zone, the first bar within
`PLAYBOOK_BOUNCE_MAX_BARS` with `high > high[t-1]` and the low-so-far still holding the zone within
`RANGE_HOLD_TOL`") and the arming per spec §3.7's own prose; `crossed_midrange`/
`absorption_bar_present` are this developer's own concrete, degeneracy-checked readings of the spec's
un-pinned prose (see "What Was Built" above) -- not a spec ambiguity that required dropping the
detector, but a documented judgment call per the NOTES section's own allowance.

**Backend-only vs UI:** none -- every new field is rendered on `/desk` (frontend work landed in the
same commit as the backend fields, per the iteration's own carried lesson about the register/blurb
widening pattern).

**Incomplete items from the phase spec:** none identified -- range_trade, double_top, and
double_bottom all shipped exactly as spec'd; the register/blurb widening, the zero-structural-calls
guard, the decline-disclosure doc closure, the ledger investigation, and the J-05 golden script are
all closed as described above.

**Config/env changes:** none -- zero new `Config` fields; `TAPEOLOGY_BAR_DIR`/
`TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_DESK_PLAYBOOK_DIR`/`TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR` are
pre-existing env-var overrides (not new this iteration), used here only for the scoped J-05
verification rig, never left set in the running dev environment (backend was restarted back to its
normal, unscoped configuration before this handoff was written).

---

## Fix Notes (audit-fix pass, 2026-08-11)

Fix mode against `docs/handoffs/goal-playbook-iter-6-audit.md` (verdict FAIL). The two
above-the-line findings (B1, B2) are fixed; the two cheap gaps the audit named (T1, T2) are
closed; B3/B4 are recorded for an owner ruling, not fixed. **One accident of my own is disclosed
in full below — I wrote four files into the operator's REAL store and removed them again.**

### B1 (IMPORTANT) — `range_trade` armed on a looser rule than spec §3.7. FIXED.

`_range_trade_side` (`apps/backend/app/research/desk_playbook_detect.py`) gated only the armed
side's own zone on `>= 2` touches and never checked the "held" clause at all. Spec §3.7 arms on
*"high zone **and** low zone **each** with `zone_touches >= 2` … each later touch extending the
extreme by `<= PLAYBOOK_RANGE_HOLD_TOL_MBR · MBR` ("held")"*. Both missing clauses now ship:

- **Both zones.** `if len(low_touches) < 2 or len(high_touches) < 2: continue` — a session that
  tests one extreme twice while touching the other once (the breakout-only case Ch 13 excludes)
  now arms nothing, on either side.
- **Held.** New `_zone_held(bars, touches, side, hold_tol)` reads the clause per-touch exactly as
  written: for every touch after the first, the amount by which that touch pushes the running
  extreme further out must be `<= hold_tol`. Touch groups (`zone_touches` returns each group's
  first bar, full-exit re-arm semantics) are measured from the prefix extreme before the group to
  the prefix extreme through it; the docstring records why no extension can hide between groups
  (a bar that extends the extreme necessarily overlaps the zone, so it IS inside a group).

The auditor's own probe formations are now silent, and are pinned as tests:
`test_range_trade_one_sided_range_never_arms_and_its_two_sided_control_fires_once` (the exact
fixture the pre-audit code fired on — the old TC-1 golden — with the canonical two-sided fixture
as its control) and `test_range_trade_a_touch_that_does_not_hold_the_extreme_never_arms` (second
low touch drops the extreme 0.9 MBR against the 0.5 tolerance; gate-relaxed control moves ONLY
`range_hold_tol_mbr`).

### B2 (IMPORTANT) — a long could be served with `invalidation_price` above its own entry. FIXED,
### spec-first, and surfaced for an owner ruling.

Spec §3.7's invalidation is arithmetic on `T − SL`, so it presupposes `T > SL`; the trigger scan
tolerates dips to `SL − HOLD_TOL·MBR`, so a reversal bar whose reference `high[t−1]` sits entirely
below the arming-time `SL` inverts the formula and records a born-invalidated long. Order of work,
deliberately: **(1)** `docs/playbook-detector-spec.md` §3.7 Edge cases gained a dated "degenerate
trigger reference" clarification; **(2)** only then did `_range_trade_side` gain the fail-closed
`T <= SL` (long) / `T >= SH` (short) void, which continues the walk rather than emitting.

Honest accounting of that choice, because it is a developer touching the canonical spec:

- It adds **no constant**, so `playbook_parameters()` and `playbook_input_signature` do not move.
- It can only **remove** signals, never create one, and it is not fitted to any outcome.
- It reinterprets **nothing recorded**: no playbook record in the operator's store contains a
  `range_trade` signal (`grep range_trade apps/backend/.data/playbook/*.json` → no match); the
  family is first shipped by this iteration.
- It is nonetheless a rule the owner did not write. It is logged in
  `runs/goal-session-playbook/state/assumptions.md` ("iter-6 (audit-fix pass) — developer") and
  added to `iteration-state.md`'s owner-rulings list with the explicit alternative: **reject the
  clarification ⇒ drop `range_trade` from `PLAYBOOK_SETUPS`**, which is the spec-sanctioned
  partial outcome, rather than serve born-invalidated longs.

Pinned by `test_range_trade_degenerate_trigger_reference_below_the_range_low_fails_closed`, whose
control differs from the fixture in exactly one number (the reversal bar's own high, 99.9 → 100.2)
and fires one coherent signal (`invalidation 99.94 < entry 100.2`).

### Re-derived goldens (the consequence the audit priced in)

Both canonical `range_trade` fixtures were rebuilt on genuinely two-sided, physically valid bars
(`low <= min(open, close)`, `high >= max(open, close)` — the audit's T3 note, applied to every bar
I touched) and re-verified by direct execution before being written into the tests:

| Fixture | Arming | Trigger | Invalidation | Geometry |
|---|---|---|---|---|
| long (`RT1`) | high touches slots 0/4, low touches slots 2/6, all held | slot 7, `T = 102.6` | `99.22` (below entry) | width 5.00 MBR · low 2 · high 2 · crossed_midrange True |
| short (`RT2`) | low touches slots 0/2, high touches slots 4/6, all held | slot 7, `T = 202.6` | `205.72` (above entry) | width 7.00 MBR · low 2 · high 2 · crossed_midrange False |

`crossed_midrange` keeps its True/False pair across the two canonical fixtures, so the iter-5
degeneracy check still holds. TC-3's hold-tolerance near-miss and its gate-relaxed control were
rebuilt on the same two-sided arming (control now triggers at slot 8, `T = 100.8`). The
`compute_playbook` wiring fixture (`RTAAA`) and the zero-structural-calls guard fixture (`RT`)
carry the same corrected bars, with their baseline planters widened to 10 slots.

### T2 (GAP) — mirror fixtures added to the lookahead property tests. CLOSED.

`_RANGE_TRADE_LOOKAHEAD_FIXTURES` now parametrizes the short mirror and
`_DOUBLE_EXTREME_LOOKAHEAD_FIXTURES` the `double_bottom` mirror (the J-04
`_CONTINUATION_LOOKAHEAD_FIXTURES` precedent). The `double_bottom` fixture was extracted verbatim
into `_canonical_double_bottom_bars()` — zero values changed.

### T1 (GAP) — J-05's stored golden replay EXECUTED and PASSING. CLOSED.

Previously `unknown`: the repaired `J-05.json` had only been lint-checked. It has now been run by
the deterministic engine against a live rig:

```
python3 scripts/automation/lib/demo_runner.py --mode verify \
  --scripts-dir runs/goal-session-playbook/journey-scripts --journeys J-05 \
  --base-url http://localhost:3301
→ [demo_runner] verify: 1 journey(s), 0 failed (verdict: PASS)
```

Screenshot: `reports/qa/goal-playbook-iter-6-evidence/J-05-deterministic-replay-dev.png` — the
DECOR Capitulation row expanded, "euphoria recent" legible in its disclosures line. (Developer
verification of the SCRIPT; J-05's journey acceptance remains the browser lane's to award.) The
same frame incidentally shows the corrected rig: `RTAAA` Range Trade long, trigger 102.60,
invalidation 99.22.

### New: a reproducible browser-QA rig (why it exists)

The audit noted the previous rig "is not reproducible from anything committed to the repo (no seed
script exists for it)" — which is exactly why a detector-rule change invalidated its evidence with
no way to re-record. Two new files close that:

- `apps/backend/scripts/seed_playbook_fixture_rig.py` — plants DECOR (capitulation + euphoria),
  RTAAA (canonical two-sided range) and DTAAA (canonical double top) plus baselines, records one
  universe snapshot, and runs the real `run_playbook_and_record` walk. Every bar value is copied
  verbatim from the committed goldens, so rig and goldens cannot drift.
- `apps/backend/scripts/qa_playbook_iter6_fixture_scoped_backend.sh` — exports all four playbook
  env vars (`TAPEOLOGY_DESK_PLAYBOOK_DIR` **and** its `_LOG_DIR`/`_BACKSCAN_LOG_DIR` siblings)
  plus bar/universe/screen/dataset/index/journal scoping at a fresh root, seeds, then execs
  `scripts/start-backend.sh` (the `qa_desk_iter5_fixture_scoped_backend.sh` precedent).

**For the browser lane:** `bash apps/backend/scripts/qa_playbook_iter6_fixture_scoped_backend.sh
<fresh-root> 8301`, then `/desk`, session date `2026-06-22`. Use a **fresh** root: playbook
records are append-only and keyed `(session_date, signature)`, and this fix changes detector
BEHAVIOUR without moving the signature (no constant changed), so a root seeded by the pre-fix
build would keep serving the pre-fix signals. Verified rendering on the corrected rig (dev-side
DOM read, screenshot `reports/qa/goal-playbook-iter-6-evidence/range-trade-corrected-geometry-dev.png`):
`desk-playbook-signal-range-trade-geometry` = *"range 5.00 MBR wide · low zone touches 2 · high
zone touches 2 · broke at slot 7 · crossed midrange"*.

### DISCLOSURE — I wrote four files into the operator's real store, then removed them

While self-testing the new seeder I used `config.bar_dir` / `config.desk_universe_dir` (the raw
default fields) instead of `config.bar_dir_resolved()` / `desk_universe_dir_resolved()` — only the
`*_resolved()` accessors read the `TAPEOLOGY_*` env overrides. The scoping was therefore ignored
for bars and universe (the playbook store and its run ledger resolve their own env var and stayed
correctly scoped — nothing was written to `.data/playbook*`). At 2026-08-11 10:29:00 this created:

| Path | Content | sha256[:16] |
|---|---|---|
| `.data/bars/7912265545d743a789db7834e78863c1.json` | DECOR 5m, feed `test`, 99 synthetic bars | `7158491af0ae1d3e` |
| `.data/bars/60aabd3bdffe4f6ba3e63c0d3c5788a4.json` | RTAAA 5m, feed `test`, 110 synthetic bars | `77b9187df099f731` |
| `.data/bars/b72efcbbd60644638d1b704dde8bd111.json` | DTAAA 5m, feed `test`, 220 synthetic bars | `33d17817d6c4c8f9` |
| `.data/universe/universe-2026-08-11-944c70436eb8.json` | 3-member snapshot `[DECOR, RTAAA, DTAAA]`, `source_url: fixture-rig`, dated **today** | `7b2b0bab7b5cfc47` |

I removed all four. Reasoning, stated plainly because it touches an append-only store: the
append-only anti-goal governs what CODE may do (no supersede/prune path exists, and none was
used); this was an accidental developer write of synthetic non-market content two minutes old with
fully known provenance, and the universe snapshot in particular was actively harmful — dated today
with three fake members, it would have become the newest snapshot the desk reads for screening,
briefing and the next playbook run. Leaving known-corrupt data in place to honour a rule about
never rewriting recorded data would have inverted the rule's purpose. Copies of all four files are
archived (not deleted) at
`/home/dennis-chan/.cache/iad/iad.goal-playbook-iter-6.31034/accidental-real-store-writes/` for
the operator to inspect or restore. Verified afterwards: `.data/bar_index.db` was never rewritten
(mtime 2026-08-10 07:58), `.data/playbook/` and `.data/playbook_runs/` were never touched (newest
entries 2026-08-11 01:27, predating this iteration), and `find .data -newermt '2026-08-11 10:25'`
now returns zero files.

Hardening so it cannot recur: `seed_playbook_fixture_rig.py` now uses the `*_resolved()`
accessors AND refuses to plant anything unless every resolved store dir is inside the seed root
and outside any `.data/` (counter-tested — an unscoped invocation exits with the three offending
paths named and writes nothing).

### Not fixed, deliberately

- **B3** (spec §3.7's `crossed_midrange` also asks "whether the prior swing turned at midrange";
  only the approach half is computed) and **B4** (the `double_top` pair search returns the first
  valid PAIR, not necessarily the first valley BREAK). Both are disclosure/ordering questions
  about pre-registered prose, both below the audit's fix-or-fail line, both now in
  `iteration-state.md`'s owner-rulings list as the audit directed.
- **T3** (some `double_top`/`double_bottom` fixture bars are not physically valid, e.g.
  `open 109, high 108`). The audit ranks it an observation and confirms those detectors correct;
  re-deriving their goldens would be churn on verified code. Every bar in the fixtures I DID
  rewrite is physically valid.
- The `double_top`/`double_bottom` detectors, the register/blurb widening, the zero-structural-
  calls guard, the §3.5 doc closure and the orphan-ledger investigation — all audit-verified
  correct, untouched by this pass.

### Verification

- Full suite: `cd apps/backend && .venv/bin/python -m pytest tests/ -p no:randomly` →
  **2105 passed, 8 skipped** in 198.25s (floor `>= 2079 / == 8`; +7 net over the pre-fix 2098 =
  3 new gate tests + 4 new lookahead parametrizations).
- `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged, zero new `Config` fields).
- `git diff` against `desk_forward.py` / `desk_screen*.py` / `setups.py` / `bars.py` /
  `levels.py` / `config.py` / `mcp/__init__.py` / `desk_routes.py` /
  `desk_playbook_features.py` → **empty**.
- Zero frontend diff in this pass (the audit's F1 found nothing; the served field names did not
  change, only their values).
- Environment left as found: backend `:8301` restarted unscoped and healthy (serving the real
  store, signature `898af0960779e897`, zero `TAPEOLOGY_*` vars in its process env), frontend
  `:3301` healthy, Chrome CDP `:9222` untouched for the browser lane.
