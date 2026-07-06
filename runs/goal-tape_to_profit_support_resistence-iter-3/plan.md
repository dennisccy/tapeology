# goal-tape_to_profit_support_resistence-iter-3 Execution Plan

## Alignment check

J-03 (confluence zones + A/B/C conviction classes) is docs/goal.md Key Capability #3
("Confluence classification") and Must-have journey J-03 verbatim. It builds directly on J-01
(bar store, iter-1) and J-02 (deterministic, lookahead-free S/R levels, iter-2), both shipped and
PASS/PASS_WITH_GAPS-audited. No drift from the project goal, no scope creep detected — the spec's
IN SCOPE section maps 1:1 onto goal.md's J-03 acceptance text (clustering, timeframe-weighted
score, A/B/C grading, additive field on the existing endpoint). Everything the spec defers
(direction/kind labelling, a distinct corrupt-sole-series state, J-04-J-06) is correctly named as
OUT OF SCOPE and matches the archived plan's own reserved shape (`levels.py:2` and
`routes.py:1631` already mark `classes` as deliberately absent pending this iteration).

## What to Build

- **Config-owned confluence parameters** in `apps/backend/app/config.py`, `sr_`-namespaced, each
  documented with rationale (no magic numbers): a clustering tolerance / confluence band (spec
  suggests `sr_confluence_band_bps`) and the A/B/C class thresholds/criteria (score cutoffs and/or
  confluence criteria such as minimum distinct timeframes / required long-term member — exact
  field name(s) and shape are the developer's call, mirroring the `sr_timeframe_weights` style).
  **Add every new field to `config_fingerprint()`'s `excluded` set** — same rationale as the three
  existing `sr_*` fields at `config.py:1320-1322`. The pinned `default` fingerprint MUST stay
  `4d665603569b9dbf`.
- **Deterministic, lookahead-free confluence clustering + A/B/C classification**, added INSIDE the
  existing `apps/backend/app/research/levels.py` (the registered Data-Contract-Row-39 owner — NO
  new module, endpoint, or MCP tool): cluster the levels `compute_levels` already produces, across
  timeframes, into confluence zones wherever prices fall within the config band; score each zone as
  a timeframe-weighted sum of its member levels' strengths; grade A/B/C by the config
  thresholds/criteria. Each zone records its member levels (with timeframes), its score, its class.
  Sort zones by an explicit total order for byte-identical served JSON.
- **Return zones as an additive field** on `compute_levels`'s existing return dict (beside `levels`
  and `no_bar_series_for_symbol`) — served verbatim by the existing `GET /research/levels` route
  and the existing MCP `levels` proxy. No second computation path; MCP JSON stays byte-identical to
  REST.
- **Honest labelling**: class A only when the config confluence criteria are met; B/C otherwise —
  never a fabricated class. `no_bar_series_for_symbol` behavior is unchanged. A symbol with levels
  but no qualifying cluster returns an explicit empty zones list (never a bare/ambiguous result).
- **Decide + document (do not fix) the corrupt-sole-series seam**: confirm the confluence layer
  reads only the healthy levels `compute_levels` already produces and introduces no new fabricated
  or aliased state; the distinct corrupt-series state stays owned by `GET /research/bars` (iter-2
  finding B1). Record this decision explicitly in the dev handoff.

## Agents Required

- **developer: yes** — backend-only implementation (confluence clustering/scoring/grading in
  `research/levels.py`, config fields, tests). Equivalent answer in the dispatcher's own
  vocabulary: **backend-data: yes, frontend-ux: no** — there is no frontend work in this iteration.

Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/config.py` -- add the confluence-band + A/B/C class-threshold field(s),
  `sr_`-namespaced, with rationale; add all new fields to `config_fingerprint()`'s `excluded` set
  (same pattern as `sr_pivot_lookback` / `sr_touch_tolerance_bps` / `sr_timeframe_weights`)
- `apps/backend/app/research/levels.py` -- add clustering + timeframe-weighted scoring + A/B/C
  grading; wire the new zones field into `compute_levels`'s return dict; update the module
  docstring's "confluence classes are J-03, out of scope here" line (now in scope)
- `apps/backend/app/research/routes.py` -- update the "classes deliberately ABSENT" comment block
  above `GET /research/levels` (`routes.py:1627-1633`); no route body change should be needed since
  the route already spreads `compute_levels`'s dict verbatim (`**result`)
- `apps/backend/app/mcp/__init__.py` -- update the `levels` tool's description text to mention
  confluence zones/classes for doc parity; no dispatch-logic change needed (already a byte-identical
  proxy that forwards any new field)
- `apps/backend/tests/test_levels.py` -- extend: one or more synthetic multi-timeframe fixtures for
  exact-value control over A/B/C assertions (mirroring the existing `_swing_fixture` /
  `_prior_period_fixture` pattern — see Known Consideration below), deterministic clustering tests,
  score-exactness tests, A/B/C grading tests with exact expected classes, byte-identical re-run
  test, no-lookahead-for-classes test (physical truncation, same style as J-02's), no-magic-numbers
  introspection extended to the new config field(s), honest empty-zones-list test, fingerprint-
  exclusion test extended to the new fields
- `apps/backend/tests/test_levels_api.py` -- extend the happy-path test(s) to assert the new zones
  field's exact shape/values on the committed PG fixture; assert honest states unchanged
- `apps/backend/tests/test_mcp_server.py` -- extend the `levels` byte-identity test to cover the new
  zones field
- `docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md` -- NEW dev handoff (must
  include the corrupt-sole-series seam decision, per DoD)

`apps/frontend/` MUST NOT change this iteration (confirm via `git diff -- apps/frontend/` empty in
the handoff, same as iter-1/iter-2).

## Known Consideration (flagging, not deciding, for the developer)

The only **committed real** bar fixture is PG `1h` (9 bars) + PG `1d` (5 bars) — **two**
timeframes. If the config's A-class criterion requires 3+ distinct timeframes (or specifically a
long-term member plus multiple others), the real committed fixture alone may never produce a class
A zone. This is exactly the situation J-02 solved by pairing synthetic fixtures (full numeric
control) with the real PG fixture (keyless real-data proof) — the same pattern should carry
forward here: use a synthetic multi-series fixture to exercise and exactly assert a genuine A case
(and a genuine B/C case), and separately assert whatever honest classes the 2-timeframe real PG
fixture actually produces (which may legitimately be B/C-only). This is a design decision for the
developer to make and document, not something this plan prescribes.

## Key Test Scenarios

- Levels within the config confluence band, across timeframes, cluster into one zone; levels
  outside the band do not join.
- Zone score = timeframe-weighted sum of member levels' strengths — exact value asserted on a
  synthetic fixture with known inputs.
- A/B/C grading: a zone meeting the config criteria grades A; a non-qualifying cluster grades B/C
  — exact expected classes asserted (both a synthetic A case and whatever the real PG fixture
  honestly produces).
- Byte-identical deterministic re-runs of zones/classes (explicit total order).
- No-lookahead extended to classes: a bar after as-of `T` cannot change any zone or class (physical
  store-truncation test, mirroring J-02's `test_lookahead_free_...`).
- MCP `levels` tool remains byte-identical to the REST response including the new zones field.
- No-magic-numbers introspection extended to the new confluence config field(s).
- `Config().config_fingerprint() == '4d665603569b9dbf'` unchanged; new confluence fields present in
  the `excluded` set; a real-threshold counter-test proves they'd move the hash if NOT excluded.
- Honest empty states: `no_bar_series_for_symbol` behavior unchanged; a symbol with levels but no
  qualifying cluster returns an explicit empty zones list (not fabricated, not conflated with the
  no-series state).
- Full backend suite green (no regressions); `test_observer_equivalence.py` +
  `test_profile_equivalence.py` + `test_real_data_gate.py` all green (`default`/`v1` byte-identical,
  frozen).
- `git diff -- apps/frontend/` empty.
- Grep-guard: no `research/strategies`, `structure_tape`, or second computation path introduced
  (J-04–J-06 correctly remain unbuilt).
