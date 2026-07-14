# goal-tradable_wall-iter-1 Audit Report

**Date:** 2026-07-14
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-01's tradable level map is genuinely and verifiably achieved. Independently reproducing the
headline acceptance against the committed real AAPL fixture returns **10 bands (5+5), basis
2026-06-18T04:00Z, the pinned 300.48–302.07 resistance band at rank 0 (top-2), round_number=True,
inherited class, score 123.0** — every Definition-of-Done item traced through the actual code holds.
The module is a real lens (single `compute_levels` import, no pivot/extreme re-detection, single
call site, frozen `levels.py`/`config.py`-values byte-identical), the `config_fingerprint` is
live-confirmed `4d665603569b9dbf`, and the full suite is independently re-run green
(1234 passed / 6 skipped / 0 failed, exit 0). One honestly-documented, zero-acceptance-impact
limitation (the `_PriorSessionBarView` over-excludes the prior session's own intraday bars, deferred
to J-06) plus two design-freedom observations are the only gaps — none compromise the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented, not fixed): `_PriorSessionBarView` over-excludes the prior session's own intraday bars**
`tradability.py:360` bounds every timeframe's bars to `epoch <= prior_bar.epoch`, where
`prior_bar.epoch` is the DAILY bar's open stamp (e.g. `2026-06-18T04:00:00Z`). The prior session's
own intraday bars (1h/5m, stamped 13:30Z+) therefore never enter the map, even though they are
"fully completed by the prior session's close" and would be legitimate under the morning-markup
anti-goal. This is a completeness under-inclusion, NOT a correctness bug: it sits on the SAFE side of
the critical no-lookahead rail (it over-excludes *completed* bars, never admits forming/future data),
so it is anti-goal-compliant. The dev proved by simulation (handoff Fix Notes → NOTE) that a
provably-safe date-based cutoff admits all of 06-18's own 5m bars yet leaves the pinned band's rank
and score **identical (#0, 153.0)** — the score is daily-touch-driven and daily bars are already
fully included. **Not fixed:** the spec's DoD required only "no bar newer than the 2026-06-18 close"
(satisfied), touching the no-lookahead cutoff is the single highest-risk edit in the module, and the
change has zero acceptance benefit — fixing it here would be scope creep against a critical rail. The
documented date-based approach is the correct home for J-06 (which will care about intraday recency).

**B2 — OBSERVATION: no runtime clamp on `tradability_band_cap_per_side` above 5**
The default is `5` (`config.py:1171`), verified compliant and pinned by
`test_tradability_parameters_are_config_sourced_no_magic_numbers` (`1 <= cap <= 5`). Nothing in code
rejects a future config override above 5, which would emit >5 bands/side / >10 total. The spec
required only that the DEFAULT be `K ≤ 5` and the acceptance holds on the default config — a >5
override is a deliberate operator config change, not a runtime escape hatch (it cannot be triggered
by request input). Honestly disclosed in the dev handoff. No action needed.

**B3 — OBSERVATION: permissive round-number rule (design freedom)**
`tradability_round_number_increment=50.0`, `tradability_round_number_tolerance_bps=50.0`
(`config.py:1218-1219`) flag any band edge within ~1.5 points (at $300) of a 50-multiple. This is
wide, but (a) the goal only required that 300 be flagged — verified (low edge 300.23 is 0.23 off 300,
within the 1.50 tolerance); (b) the flag is not decisive in ranking (the pinned band's 123.0 score is
dominated by the daily-touch factor 78, not the round-number 20); (c) the spec explicitly grants
weight/rule values as config-owned design freedom. Calibrated and regression-guarded. No action.

### Frontend Findings

N/A — `Frontend Present: no`. This iteration is backend + API + MCP only; the map's UI home
(`/structure` → Tradable Map) is J-05. UI pipeline stages correctly N/A-stubbed. No frontend to audit.

### Test Findings

**T1 — OBSERVATION (positive): test quality is high; the two key guards genuinely bite**
Assertions are tight and exact (`quality_score == pytest.approx(123.0)`,
`basis_as_of == "2026-06-18T04:00:00.000000Z"`, exact `price_low/price_high`, exact member prices,
exact `daily_touch == 39`), not loose ranges. Two guards were independently confirmed to bite, not
pass by accident: (1) `test_no_lookahead_bars_after_the_basis_never_affect_the_result` uses a
synthetic 8-day zero-weekend-gap series whose day-7 canary (prices 999/998) sits exactly on the
consecutive-session collision epoch the `_PriorSessionBarView` fix targets — I traced that
`resolved_as_of = day6.epoch + 86400` lands precisely on day-7's own epoch, so without the view the
canary would leak; (2) `test_aapl_pinned_band_ranks_top2_under_realistic_multitimeframe_density`
carries a regression guard asserting a higher-raw-touch intraday band ranks BELOW the wall — the dev
verified this fails under the reverted all-timeframe sum. Error cases (422 on missing symbol /
malformed as_of / empty symbol) and all four honest empty states are asserted distinctly.

---

## 3. Domain Assessment

The core domain logic is correct and disciplined. Verified by reading the actual code, not the
handoff:

- **Lens, not a second engine (the critical anti-goal):** `tradability.py` imports exactly
  `from .levels import compute_levels` and nothing else from `levels.py`; it calls no
  pivot/extreme/selection internal and reads no frozen `sr_*` threshold (guarded statically by
  `test_tradability_module_is_a_lens_never_a_second_levels_engine`). `compute_tradability` has
  exactly ONE call site in app code (`routes.py:1830`); the MCP tool proxies that route over HTTP.
  Single source of truth holds — no second computation path. Frozen `levels.py`, `backtests.py`,
  `edge_report.py` are byte-untouched (git diff empty); `config.py` is purely additive (0 deletions).

- **Morning-markup as-of resolution + the `_PriorSessionBarView` fix:** genuinely non-obvious,
  correctness-bearing new code. The naive "prior bar epoch + 1 day" as-of collides with the requested
  session's own bar epoch for any two consecutive sessions (because real daily bars share an
  hour-of-day stamp and `levels.py`'s `_bars_as_of` uses one inclusive `<=` for both visibility and
  period-close). The second read-only truncation layer closes that gap on the safe side. I confirmed
  the mechanism against `levels.py:92-162` and the biting canary test — this is a real fix, not scope
  creep, directly serving the no-lookahead rail.

- **Quality scoring (the round-1 CRITICAL, verified fixed):** the touch factor counts only `"1d"`
  members' `touch_count` (`tradability.py:277-279`), aligning code to goal.md's literal "daily touch
  count". Confirmed the pinned wall ranks #0 both on the daily-only fixture (score 123, independently
  reproduced) and — per the passing multi-timeframe regression + the dev's live `.data/bars` probe —
  under realistic intraday density (score 153). The pre-ship reviewer catch was correctly resolved.

- **Determinism & honesty:** every collection carries an explicit total order (price_low is unique
  per side, so `_served_sort_key` is truly total); class inheritance is an honest projection of the
  best overlapping zone with `null` for no overlap (never a fabricated grade); the two empty states
  mirror `levels.py`'s `no_bar_series_for_symbol` semantics exactly and are asserted distinctly.

---

## 4. Fixes Applied During This Audit

None. All findings are GAP/OBSERVATION severity — fixing them would be scope creep (B1 is a
deliberate, spec-permitted, zero-impact conservatism on the highest-risk rail; B2/B3 are
config-owned design freedom the spec explicitly grants). No CRITICAL or IMPORTANT issue was found.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

**Proceed to the next journey (J-02 — the touch-event scanner / `setups.py` + 12-symbol scan
registry).** J-01 is the intended unblocker and it is genuinely complete: the canonical
`/research/tradability` value + endpoint + read-only MCP proxy are in place, byte-identical across
REST/MCP, deterministic, and consuming `compute_levels` verbatim. The single documented limitation
(B1, prior-session intraday recency) is naturally owned by J-06 (cockpit overlay), exactly as the dev
handoff notes — carry the recorded date-based cutoff forward so J-06 adopts it deliberately with its
own no-lookahead tests. No remedial work is required before continuing.
