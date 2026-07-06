# goal-tape_to_profit_support_resistence-iter-4 Audit Report

**Date:** 2026-07-06
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-04 is genuinely achieved. `structure_tape` is a real, config-owned registry entry beside the
frozen `v1`; the backtest runner arms **only** where a classified confluence-zone level and a
confirming tape state coincide (proven by two discriminating negative tests, not just happy-path
asserts), stamps strategy id + exact level provenance, re-runs byte-identical, and reads levels
exclusively via the one canonical `compute_levels` owner as-of each event's own timestamp
(no-lookahead). Every critical anti-goal guard I re-ran myself is green: the `default`/`v1`
fingerprint is unmoved (`4d665603569b9dbf`), `apps/frontend/` is untouched, no second S/R path or
second champion source exists, and no execution/brokerage code was introduced.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (gap): `structure_tape` breakthrough arm is a static price-position test, not a fresh cross**
`_structure_tape_arm` (`app/research/backtests.py:504-506`) qualifies a breakthrough with
`point.last > price` (long) / `point.last < price` (short) — i.e. price is *beyond* a level, not
that it *crossed* the level between two consecutive events. Because there is almost always some
classified level below the current price, the breakthrough reading's structural anchor is looser
than the rejection reading's tight 5-bps proximity band (it approaches "arm on `buyer_control`/
`seller_control` while above/below any zone level"). I investigated this as a potential correctness
defect and concluded it is **not** one, for three grounded reasons: (a) it faithfully mirrors the
frozen studies precedent `_arm_setup_occurrences` (`app/research/studies.py:507`), whose own
variable is literally named `crossed` for the identical `point.last > level` static test — and the
execution plan explicitly directed the dev to reuse "the studies' level-cross technique"; (b)
`levels.py:71-74` deliberately delegates a level's support/resistance "kind" to the J-04 tape read,
which this design honors (bid/ask absorption and buyer/seller control select the direction); (c)
the binding DoD wording is "a classified level and a confirming tape state coincide", which is
satisfied. Recorded as an honest limitation a future research-quality iteration could tighten to a
true event-to-event cross; **not fixed** — changing it would diverge from the precedent the plan
mandated and is scope creep here.

**B2 — OBSERVATION (gap): `compute_levels` re-read on every qualifying flat event (O(events × bar files))**
`_structure_tape_arm` calls `compute_levels` (which re-reads/re-verifies every bar-series file from
disk) on each flat event whose tape state matches a reading (`app/research/backtests.py:500`). This
is *correct* — no-lookahead requires an as-of-T computation and this is the one canonical owner, no
second path — but uncached. Already disclosed by the dev and flagged NOTE by the reviewer. Fine at
this era's fixture scale; a future large-bar-library backtest may want per-as-of caching. **Not
fixed** (a real limitation the spec did not require solving).

### Test Findings

**T1 — GAP (gap): no dedicated corrupt-sole-bar-series test for `structure_tape` specifically**
The iter-2/iter-3 NOTES asked the dev to decide `structure_tape`'s behaviour when a symbol's sole
bar series is corrupt. The decision (honest empty — zero arms — because a corrupt sole series routes
through `compute_levels`'s existing `no_bar_series_for_symbol` aliasing to an empty
`confluence_zones`, which the arming loop treats identically to "no series recorded") is sound and
is proven *transitively*: the empty-zones → zero-arms path is asserted by
`test_structure_tape_no_arm_when_symbol_has_no_classified_levels`
(`tests/test_backtests.py:394`), and the corrupt-file aliasing itself is exhaustively tested in
`test_levels.py`. The runner adds no new logic on that path. The spec's TESTING REQUIREMENTS list
"no classified levels → honest empty" (which IS tested), not a dedicated corrupt-file backtest
variant. **Not fixed** — adding it is optional documentation parity, not a correctness gap; already
flagged NOTE by dev and reviewer.

---

## 3. Domain Assessment

The core domain logic is correct and honestly bounded. The strategy grammar is fully config-owned:
the two tape-confirmation maps (`structure_tape_rejection_state_by_direction`,
`structure_tape_breakthrough_state_by_direction`) and the proximity band
(`structure_tape_proximity_band_bps`) are named `Config` fields with documented rationale — no
inline literal in the runner (verified: `_structure_tape_arm` reads `entries["..."]` by name). The
arming decision correctly requires BOTH a classified level AND a confirming tape state — and this is
proven by the two load-bearing negatives, which are the discriminating tests a skeptic needs:
`test_structure_tape_no_arm_when_symbol_has_no_classified_levels` fires the *same* confirming
SIM-BUYER tape but with no bar series → zero arms (tape alone never arms), and
`test_structure_tape_no_arm_when_tape_state_is_unconfirmed` presents a real class-A level but a
never-confirming SIM-CHOP tape → zero arms (a level alone never arms). The four positive tests
assert the exact `(setup_type, direction)` and the exact `{"price","timeframe","class"}` provenance
for all four combos. No-lookahead is not asserted by prose but by
`test_structure_tape_no_arm_before_the_defining_bars_are_visible_no_lookahead`, which re-anchors the
*same* tape so the as-of instant precedes the defining bar → honestly zero levels → zero arms,
proving the runner computes `compute_levels` per-event (`epoch_anchor + point.timestamp`) rather
than a single whole-history snapshot. Single-source discipline holds on both axes: levels come only
from `compute_levels` (source-scan test forbids `_swing_pivots`/`_cluster_levels`/
`_prior_period_extremes`/`_grade_zone` in the runner — verified), and the champion is read verbatim
from the one `store.get_champion_pointer()`, with `test_strategies_champion_reflects_a_moved_pointer`
proving the strategies and profiles endpoints return the identical pointer after a move.

Anti-goal posture is clean: the README bullet describes the strategy in operator language with
"simulated" returns reported in R AND $ beside the random-entry null baseline — no edge/advice/
prediction framing; no execution/order/broker identifier appears in the diff; the frozen
`v1`/`default` fingerprint is unmoved; and MCP `strategies` is a read-only GET proxy byte-identical
to REST.

---

## 4. Fixes Applied During This Audit

None. Every DEFINITION OF DONE item and every critical anti-goal is satisfied with independently
re-run evidence; the three findings above are all GAP/OBSERVATION-level (documented limitations),
and fixing any of them would be scope creep (B1 would diverge from the plan-mandated studies
precedent; B2/T1 are optional). No CRITICAL or IMPORTANT issue was found.

**Evidence I re-ran myself (not trusted from the handoff):**

| Check | Command | Result |
|-------|---------|--------|
| J-07 fingerprint pin | `python -c "Config().config_fingerprint()"` | `4d665603569b9dbf` — unmoved |
| Arming + equivalence + no-execution + real-data-gate + strategies API | `pytest tests/test_backtests.py tests/test_strategies_api.py tests/test_profile_equivalence.py tests/test_no_execution_path.py tests/test_real_data_gate.py` | 100 passed |
| MCP strategies byte-identity (real uvicorn subprocess) | `pytest tests/test_mcp_server.py` | passed (exit 0) |
| Frozen-frontend guard | `git status --short -- apps/frontend/` | empty |
| No second S/R path / no J-06 leak / no execution ids | `git diff` greps over `app/` | all clean |

I did **not** re-run the full 1128-test suite end-to-end (QA already did: exit 0, 1128 passed / 1
skipped, +21 vs the iter-3 baseline of 1107); my targeted re-runs cover every load-bearing guard
for this iteration and are all green, consistent with that count.

---

## 5. Recommended Next Step

Proceed. J-04 is complete and the required-still-passing journeys (J-01, J-02, J-03, J-07) remain
green. The natural next journey is **J-05 (class-scaled stop/reward/simulated size + per-class PnL
breakdown)**, which was correctly excluded from this iteration and now has its unblocker: the
`structure_tape` entries armed here carry the arming level's A/B/C class in `trade["level"]["class"]`,
which J-05 will consume to scale risk/size. The three GAP/OBSERVATION items may be carried forward
as-is (none block J-05); if a future iteration backtests `structure_tape` over a large real bar
library, revisit B2 (per-as-of level caching) and consider whether B1's breakthrough anchor should
become a true event-to-event cross.
