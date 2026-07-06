# goal-tape_to_profit_support_resistence-iter-3 Audit Report

**Date:** 2026-07-06
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-03 ships the confluence-zone + A/B/C classification half of Data-Contract Row 39 as a purely
additive `confluence_zones` field on the existing `compute_levels` return dict — no new module,
route, or MCP tool — and every acceptance property (deterministic anchor-fixed clustering,
timeframe-weighted scoring, honest A/B/C grading, no-lookahead, byte-identical REST≡MCP, honest
empty states, frozen `default`/`v1`) is genuinely implemented and independently verified against the
running code, not just the handoff. I traced the algorithm's unhappy paths (singletons, same-price
duplicates, corrupt-sole-series aliasing, later-bar leakage) and re-ran the full suite myself; no
CRITICAL or IMPORTANT issue exists, so no fix was applied.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): committed real PG fixture can never produce a class A zone**
`apps/backend/app/config.py:1139` sets `sr_confluence_class_a_min_timeframes = 3`, but the committed
PG fixture stores only two timeframes (1h, 1d), so class A is structurally unreachable on real
committed data. This is honestly documented (config comment `config.py:1135-1138`, handoff "Known
Issues") and class A reachability is instead proven end-to-end through the real bar-driven
`compute_levels` path on a dedicated synthetic 3-timeframe fixture
(`test_levels.py:505` `test_synthetic_three_timeframe_fixture_produces_exact_a_b_c_zones_through_compute_levels`).
An honest data-breadth consequence, not a defect — no fix warranted.

**B2 — OBSERVATION (observation): same-price levels of different `type` both count toward a zone**
When a swing-pivot and a prior-period-extreme land on the identical price (e.g. PG zone[1] members
`[139.89, 139.89, 140.0]`, `research/levels.py:246` `_confluence_zone`), both appear as distinct
members and both contribute to `score` (12.0 here). This is by design — two independent detection
methods corroborating one price — and is honestly labelled (each member carries its own distinct
`type`), never a fabricated duplicate. Verified directly: `score == sum(member strengths)` holds for
every zone. No fix warranted.

**B3 — OBSERVATION (observation): the "2 members = cluster" minimum is a code literal, not config**
`research/levels.py:216,221` gate a qualifying cluster on `len(current) >= 2`. Unlike the confluence
band and the A/B/C timeframe floors (all config-owned and fingerprint-excluded), this `2` is a
literal. It is the structural definition of "confluence" (you cannot have levels *aligning* with
fewer than two), analogous to the deliberately-non-config `_PERIOD_SECONDS` calendar facts, not a
tunable research threshold — so it is out of the no-magic-numbers requirement's intent. Noted only
for completeness; no fix warranted.

### Frontend Findings

N/A — J-03 is a machine surface (REST + MCP). `git diff -- apps/frontend/` is empty (verified by me,
not just claimed); browser-qa correctly SKIPPED.

### Test Findings

**T1 — OBSERVATION (observation): no-magic-numbers introspection is a presence-check, not an absence-check**
`test_levels.py:616` `test_sr_parameters_are_config_sourced_no_magic_numbers` asserts each of the six
`config.sr_*` field names appears in `levels.py`'s source, but does not grep for the *absence* of
literal thresholds (as the test plan's TC-09 pass-criteria phrased it). I closed this gap by reading
`levels.py` directly: the grading/clustering logic contains no hardcoded threshold — the only numeric
literals are the structural bps denominator `10_000.0` (identical to the pre-existing `_touch_count`
usage) and the structural cluster-minimum `2` (B3). The guard is therefore adequate in practice. No
fix warranted.

---

## 3. Domain Assessment

The core domain logic is correct and honest. I verified each property against the running code:

- **Clustering (`_cluster_levels`, `research/levels.py:194`)** — an anchor-fixed scan over
  price-sorted levels: the lowest member fixes the tolerance window (`anchor * band_bps / 10_000`)
  and every candidate is re-checked against that FIXED anchor, so a cluster's span is bounded by one
  tolerance rather than an unbounded chain. Directly tested
  (`test_confluence_clustering_is_anchor_fixed_not_chained_to_the_previous_member`, with a premise
  assertion), and I confirmed independently that every served zone's members sit within the band of
  their anchor. Singletons are dropped (never a fabricated one-member zone). Because anchor prices
  are strictly increasing across clusters, `_zone_sort_key`'s lowest-member-price element is already
  a strict total order — byte-identical determinism holds (re-verified via a fresh-store `json.dumps`
  equality test).

- **Grading (`_grade_zone`, `research/levels.py:226`)** — by distinct-timeframe breadth alone, never
  by score. Class A requires BOTH a config-owned distinct-timeframe floor AND a long-term member
  (`PRIOR_PERIOD_TIMEFRAMES`, reused verbatim — no second "long-term" list); the two conditions are
  independently enforced, proven by
  `test_confluence_class_a_requires_a_long_term_member_not_just_timeframe_count` (a 1h+4h+8h cluster
  meets the count but grades B). Class B needs only the distinct-timeframe floor; a same-timeframe
  cluster grades C. Exact expected classes are asserted on the committed PG fixture
  (`[C,C,C,C,C,B]`) and the synthetic fixture (`A,B,C`) — I reproduced both directly.

- **Scoring** — `score = sum(member strength)`, and since each level's `strength` already folds in
  its own timeframe weight, the sum is timeframe-weighted without double-weighting. Verified:
  `score == sum(strength)` for every served zone.

- **No-lookahead (the headline critical property, extended to classes)** —
  `compute_confluence_zones` is a pure function of the already-`ts <= as_of`-truncated `levels` list
  (`compute_levels` filters via `_bars_as_of` before any windowing), so it introduces no second
  truncation surface. The physical-truncation test asserts the full response dict (including
  `confluence_zones` and each `class`) is byte-identical between a store holding only bars ≤ T and
  the full store queried at the same T, plus an explicit non-vacuous assertion that a
  not-yet-confirmed 1h swing (148.095) is absent from the zone at the earlier as-of.

- **Single source of truth / MCP read-only** — the route spreads `**result` verbatim
  (`routes.py:1655`); the MCP `levels` tool proxies `response.text` byte-for-byte. The byte-identity
  test compares encoded MCP text to the REST body on a NON-EMPTY result (asserting `confluence_zones`
  is non-empty first, so the proof is not vacuous). Grep confirmed no second computation path and no
  premature J-04/J-05 code (`structure_tape` / `research/strategies` / `class_scaled` → no matches).

- **Honest failure states** — three distinct states each return `confluence_zones: []` and are
  asserted with exact full-dict equality: no series (`no_bar_series_for_symbol: true`), series but
  nothing derivable (`false`, empty levels), and levels but no qualifying cluster (`false`, non-empty
  levels). The corrupt-sole-series seam is correctly decide-and-documented (not fixed, per scope):
  `compute_confluence_zones` reads only the healthy `levels` list, so a corrupt sole series still
  aliases to `no_bar_series_for_symbol: true` exactly as in iter-2 — no new fabricated/aliased state,
  ownership retained by `GET /research/bars`.

- **Frozen `default`/`v1` + fingerprint** — all three new `sr_confluence_*` fields are in
  `config_fingerprint()`'s `excluded` set (`config.py:1366-1368`); I confirmed
  `config_fingerprint() == '4d665603569b9dbf'` and that changing the band does NOT move the hash,
  while a real classifier threshold (`min_trade_speed`) still does. The J-07 freeze gate
  (observer + profile + real-data equivalence, 57 tests) passes.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT finding surfaced; all findings are OBSERVATION-level and documenting
them (not fixing them) is the correct action. No source file, test, or handoff was modified by this
audit.

### Independent verification performed (evidence)

| Check | Command / method | Result |
|-------|------------------|--------|
| Full backend suite (regressions) | `pytest tests/ -q` | 1107 passed, 1 skipped, 0 failed, 0 errors (exit 0) — status-char count 1108 |
| Confluence + levels + MCP + J-07 gate | `pytest tests/test_levels.py tests/test_levels_api.py tests/test_mcp_server.py tests/test_observer_equivalence.py tests/test_profile_equivalence.py tests/test_real_data_gate.py -q` | 114 passed (exit 0) |
| Pinned fingerprint + active exclusion | `Config().config_fingerprint()` + counter | `4d665603569b9dbf`; band change does not move hash |
| Served shape + invariants | direct `compute_levels` call on committed PG fixture | additive `confluence_zones`; classes `[C,C,C,C,C,B]`; A unreachable; `score==Σstrength`; all members within band of anchor |
| Frontend untouched | `git diff --stat -- apps/frontend/` | empty |
| No scope creep | grep `structure_tape` / `research/strategies` / `class_scaled` | no matches |

---

## 5. Recommended Next Step

**Proceed.** J-03 fully achieves its goal — `GET /research/levels` (and the byte-identical MCP
`levels` tool) now serves confluence zones with member levels (+ timeframes), a timeframe-weighted
score, and an honest A/B/C conviction class, computed once in the Row-39 owner, lookahead-free, with
`default`/`v1` frozen and the pinned fingerprint unmoved. Required-still-passing J-01/J-02/J-07 remain
green. The three OBSERVATIONs are honest, documented limitations that do not compromise the phase
goal and require no action here. The A/B/C zones are ready to be consumed by J-04's `structure_tape`
entries (arm-at) and J-05's class-scaled risk in later iterations.
