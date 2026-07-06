# goal-tape_to_profit_support_resistence-iter-2 Audit Report

**Date:** 2026-07-06
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal — deterministic, lookahead-free S/R levels (price, timeframe, type, touch_count,
strength) computed once from the committed multi-timeframe bar store and served byte-identically
across `GET /research/levels` and the read-only MCP `levels` tool — is fully achieved and
independently verified. Every DEFINITION OF DONE item is genuinely met (not merely claimed): the
lookahead-free property is proven by a physical store-truncation test, determinism by a total-order
sort, single-source-of-truth by an HTTP-forwarding MCP proxy, and the J-07 fingerprint sentinel
stays pinned at `4d665603569b9dbf` with the three new `sr_*` fields correctly excluded. One minor,
honestly-documented gap keeps this from a clean PASS: at the levels endpoint a corrupted *sole* bar
series for a symbol is aliased to the `no_bar_series_for_symbol: true` ("never recorded") state
rather than a distinct integrity state — acceptable because that failure mode is surfaced distinctly
at its owning endpoint (`GET /research/bars`) and the spec deliberately scoped the "why is it empty"
distinction OUT for J-02.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented): corrupted sole bar series aliases to `no_bar_series_for_symbol: true`**
`compute_levels` (`apps/backend/app/research/levels.py:181`) does `records, _integrity_errors =
store.list()` and discards the integrity-error half. A symbol whose ONLY stored series file is
corrupt therefore has an empty `matching` list and returns `{"levels": [], "no_bar_series_for_symbol":
True}` — byte-identical to a symbol that was never recorded at all. The session anti-goal enumerates
"corrupt file" among the failure modes that "must surface an explicit, distinct state," so this is a
real (if minor) gap at *this* endpoint. Mitigating and why it is a GAP not an IMPORTANT finding:
(a) the corrupt-file state IS surfaced explicitly and distinctly at its canonical owner — `bars.py`'s
`BarStore.list()` separates corrupt files into `integrity_errors`, and `GET /research/bars` reports
them, so no information is lost product-wide; (b) J-02's DoD and Testing Requirements enumerate only
three honest states (no-series / no-levels / the 422 matrix), none of which require a corrupt-file
distinction here; (c) the spec's OUT OF SCOPE explicitly defers the "why is this empty" distinction
unless J-02 genuinely needs it; (d) no data is fabricated and no error is masked as a *success with
fake data* — the result is honestly empty. Dev flagged this in the handoff's Known Issues. No fix
applied (a distinct integrity state at the levels endpoint is a design decision beyond J-02's scope —
fixing it would be scope creep). Worth revisiting if J-03 (which consumes levels) needs to tell
"corrupt" from "absent."

**B2 — OBSERVATION: two exactly-equal same-type pivots at the same price would emit duplicate level dicts**
`_swing_pivots` (`levels.py:103`) appends one dict per qualifying bar; if two distinct bars in the
same timeframe were each a strict swing-high at the identical float price, the output would contain
two identical level dicts (same price/type/touch_count/strength). This is deterministic (stable sort,
identical dicts), non-fabricated (both are real pivots), and not triggered by any committed or
synthetic fixture. No action — informational only; a future de-dup/merge is a J-03 confluence concern,
not a J-02 defect.

### Frontend Findings

None applicable. Backend/machine-only iteration; `git status --porcelain -- apps/frontend/` is empty
(independently confirmed) and no `apps/frontend/` file appears in `changed_files`.

### Test Findings

**T1 — OBSERVATION (positive): exact-value assertions throughout, no loose/accidental passes**
The test suite asserts exact prices, touch counts, and strengths against directly-computed (not
hand-waved) fixture values — e.g. `test_committed_fixture_swing_pivots_exact_values_keyless` pins the
1h set to `{149.4796, 148.74, 148.06, 148.095}` with exact touch_count/strength, and
`test_committed_fixture_prior_period_extremes_exact_values_keyless` asserts `len(result["levels"]) ==
20`. The lookahead-free test (`test_lookahead_free_a_level_at_t_is_unchanged_by_any_bar_after_t`)
builds a *physically truncated* store and asserts `len(truncated_hourly) < len(full_hourly_bars)`
before the byte-identity comparison, so it cannot pass vacuously. The fingerprint test pairs the
exclusion assertion with a real counter-test (`Config(min_trade_speed=0.51)` DOES move the hash).
This is the correct shape of proof for the no-lookahead anti-goal; I found no assertion that accepts
multiple outcomes.

---

## 3. Domain Assessment

The core domain logic is correct and, importantly, lookahead-free *by construction* rather than by
convention:

- **Lookahead-free filter is applied at the single choke point.** `_bars_as_of` (`levels.py:73`)
  truncates each series to `epoch <= as_of` BEFORE any detector runs; `_swing_pivots` needs
  `lookback` confirming bars on each side (so an end-of-prefix pivot simply does not register until
  its confirming bars are themselves visible), and `_prior_period_extremes` additionally gates on
  `bar.epoch + period_seconds > as_of_epoch` (a period is "prior" only once its END has passed).
  I traced both detectors and the touch-count helper — none reaches a bar after `as_of`. The
  physical-truncation test confirms the property empirically, not just structurally.
- **Determinism** is guaranteed by the `(timeframe, price, type)` total-order sort at
  `levels.py:195`; float serialization is stable within a Python version, so byte-identity holds
  across fresh store objects (proven by `test_byte_identical_determinism_across_independent_runs`).
- **Single source of truth** is real: the REST route (`routes.py:1636`) is the only caller of
  `compute_levels`, and the MCP tool forwards the endpoint's `response.text` verbatim
  (`mcp/__init__.py:346`) — there is no second computation path. The byte-identity test seeds the
  live backend's bar dir with the committed fixture and asserts `result.content[0].text.encode() ==
  rest.content`.
- **No magic numbers**: every parameter (`sr_pivot_lookback`, `sr_touch_tolerance_bps`,
  `sr_timeframe_weights`) is config-sourced; the introspection test greps the module source for the
  three `config.sr_*` references and pins `set(sr_timeframe_weights) == set(bar_timeframes)` so a
  weight lookup can never fall back to a fabricated default. The `_PERIOD_SECONDS` calendar constants
  (86400/604800/2592000) are correctly treated as structural facts, not tunable S/R parameters.
- **Fingerprint discipline**: the three `sr_*` fields are in the `excluded` set (`config.py:1320`)
  with a rationale comment matching the existing `bar_timeframes` exclusion style; `CONFIG.
  config_fingerprint()` independently recomputed to `4d665603569b9dbf`. The KeyError-on-unknown-
  timeframe guard is unreachable for stored data because `POST /research/bars` 422s any out-of-set
  timeframe at write time (so an invalid timeframe can never reach the store), and it would be a loud
  500 rather than a silent/fabricated result if it ever did.

Anti-goal compliance: no live-execution path, no PnL/profit surface, no ML/optimizer, MCP is a
read-only GET proxy, `default`/`v1` frozen (fingerprint pinned + observer/profile equivalence green),
no train-only promotion (no strategy/backtest code added), levels computed once. All verified.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | None. No CRITICAL or IMPORTANT findings; the single GAP (B1) is out of J-02's required scope and fixing it would be scope creep. |

**Independent verification commands run (all green):**
- `pytest tests/test_levels.py tests/test_levels_api.py -q` → 24 passed
- `pytest tests/test_mcp_server.py::test_levels_tool_byte_identical_on_a_non_empty_live_result
  ::test_levels_tool_requires_both_arguments tests/test_observer_equivalence.py
  tests/test_profile_equivalence.py -q` → 24 passed (2 + 7 + 15)
- `python -c "assert CONFIG.config_fingerprint()=='4d665603569b9dbf'"` → PINNED OK
- `git status --porcelain -- apps/frontend/` → empty; `git diff --name-only -- apps/backend/app/engine/
  apps/backend/app/serializers.py` → empty (engine/default untouched)
- `grep -rn "research/strategies|structure_tape" apps/backend/app/` → no matches (J-04–J-06 unbuilt)

---

## 5. Recommended Next Step

**Proceed to J-03 (confluence zones + A/B/C classification).** J-02 delivers the levels half of
Data-Contract row 39 correctly, lookahead-free, deterministic, and single-sourced across REST + MCP,
with the endpoint shape reserving room for J-03's additive `classes` field. The one documented gap
(B1) is minor, acceptable, and does not block downstream work — but J-03 should decide, when it starts
consuming levels, whether it needs to distinguish a corrupt sole series from an absent one; if so, add
a distinct honest state at the levels endpoint then (with the corrupt-file failure mode surfaced
explicitly per the anti-goal). No remediation is required before advancing.
