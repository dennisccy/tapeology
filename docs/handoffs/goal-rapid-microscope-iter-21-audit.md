# goal-rapid-microscope-iter-21 Audit Report

**Date:** 2026-08-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-09's foundation is genuinely built, not merely claimed: I re-ran the delta-divergence screen on the
committed hermetic fixture myself (`killed_null`, effect `-0.012 bps`, `p_screen 0.218`, every §5.4
disclosure and the §5.5 econ column present), reproduced the live `band_touch_count` of exactly
`8247` against the operator's real 18-dataset store, and re-verified the restored `J-10.json`
assertions and the guard scan. The browser lane's UT-04 FAIL was a REAL product gap — the
walk-forward floor check existed in source with **zero** non-test callers — and I fixed it: the
pilot run is now the operator-reachable path that records that decision, proved by a new route-level
test plus a non-vacuity probe. Two limitations remain documented and unfixed: `GET .../micro/readiness`
now costs a measured **22.3 s** of uncached raw-event parsing per request against the real store, and
the divergence anchor extraction is quadratic (measured ~7.3 min per 2,027-pair band per 1 M snapshot
rows), so a real-corpus pilot run is not yet tractable.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the walk-forward floor check was reachable only from a unit test**

`apps/backend/app/research/scout.py:1732` (`register_screen_and_walkforward_check`) and
`apps/backend/app/research/walkforward.py:1136` (`scout_candidate_walkforward_floor_check`) had **no
production caller at all**. The only operator paths — `POST /research/desk/micro/scout/compute`
`{"grid":"delta_divergence_pilot"}` and `python -m app.research.scout --grid delta_divergence_pilot`
— both went through `ScoutComputeManager.trigger` → `run_scout_grid_and_record`
(`scout.py:1671`), which called **only** `register_and_screen_candidate`. Verified by
`grep -rn "register_screen_and_walkforward_check" app/ tests/`: one definition, one `__all__` entry,
and two hits in `tests/test_scout.py` — nothing else. The browser lane found the same thing
independently (UT-04 FAIL, `reports/phase-goal-rapid-microscope-iter-21-ui-test-results.md:29`), and
UT-05 recorded that its own "…and its walk-forward companion row" clause could not hold either.

Why this is IMPORTANT and not a GAP: the phase spec's *New information displayed* promises the
floor-refusal renders in a shipped section, and IN SCOPE item 6 requires the decision "recorded …
in the scout ledger". A capability that only a `pytest` process can produce is not recorded anywhere
a user, an operator, or the ledger's own served surface can see. (DoD item 4 itself is met by the
hermetic TC-5/TC-6 contract — I verified both run and assert real values — so this is a
partially-implemented spec'd flow, not a false DoD checkbox.)

**Fix applied** (see §4 for the file list): `run_scout_grid_and_record` gained an optional
`exposure_registry`; when given, each grid request runs through `register_screen_and_walkforward_check`
instead, so the screen row and the floor-check row land under the same `candidate_id`. The pilot
selector on `ScoutComputeManager.trigger` now **requires** an `ExposureRegistry` (a `ValueError`,
mirroring the existing `resolver` requirement), the route supplies it from the *same*
`get_micro_exposure_registry_dir` dependency `POST /walkforward/compute` already uses, and the CLI's
pilot branch builds it from `resolve_micro_exposure_registry_dir`. The **default reference grid is
untouched** — `exposure_registry` stays `None` there, one ledger row per candidate, byte-identical.

Evidence the fix works, and that the test is not vacuous:

```
$ .venv/bin/python -m pytest tests/test_scout.py -k "iter21_audit_b1 or grid_selector or omitted_body"
4 passed, 67 deselected, 2 warnings in 9.54s
```

Non-vacuity probe (temporarily forcing the pre-fix wiring `exposure_registry=None` in the manager's
worker, then reverting it):

```
FAILED tests/test_scout.py::test_iter21_audit_b1_pilot_route_records_the_walkforward_floor_check_row
1 failed, 1 passed, 69 deselected
```

Full suite after the fix:

```
$ .venv/bin/python -m pytest tests/
3316 passed, 8 skipped, 2 warnings in 638.91s (0:10:38)
```

0 failed, 0 errors, ≥ 3,281 floor cleared (3,314 → 3,316: my two new tests).
`Config().config_fingerprint()` re-checked by me: `08e471b10130e1e2`. No `referee_*.py` file is in
`git status` (all six byte-untouched).

**B2 — IMPORTANT (gap, NOT fixed): `GET /research/desk/micro/readiness` now burns a measured 22.3 s
of uncached raw-event parsing per request against the operator's real store**

`micro_routes.py:108` now constructs a `BandMapResolver` on **every** readiness GET, and
`micro_join.joinable_corpus_counts` (`micro_join.py:639-643`) calls `enumerate_band_touches` per
dataset, which calls `DatasetStore.load_events` — a full parse of a ~50 MB dataset JSON — with **no
cache of any kind**. Measured twice, back-to-back, using the route's own cached store constructions
(`routes.get_dataset_store` / `routes.get_bar_store`), so these are warm, steady-state numbers:

| step | run 1 | run 2 |
|---|---|---|
| `ds.list()` (pre-existing, index-cached) | 0.00 s | 0.00 s |
| `BandMapResolver(...)` ctor (new this iteration) | 5.71 s cold / 0.55 s warm | 0.55 s |
| **`enumerate_band_touches` over all 18 datasets (new)** | **22.33 s** | **22.53 s** |
| result | 8,247 touches | 8,247 touches |

The `8247` figure in the dev handoff reproduces exactly — the count is real. The cost is real too,
and it lands on a page-load GET that `/desk` issues automatically (`lib/api.ts:2170`, a plain
`fetch` with no client timeout, so the Microscope Readiness panel simply spins for ~22 s).

Two things make this more than a nit. First, the *sibling fold inside the same builder* already
solves exactly this problem the right way: `micro_readiness.py:414-418` looks up `fallback_frac` in
the checksum-keyed durable `MicroReadinessCache` and calls `store.load_events` only on a miss. The
new fold ignores that established pattern. Second, it grows: **5 of 18** datasets resolve a band map
today (AAPL ×2, MSFT, AMZN, GOOGL, AMD, NFLX all consume measurable time) — not "1 of 18" as the QA
report states — so every additional operator-warmed tradability map adds seconds to every future
page load.

I deliberately did **not** fix this during the audit, and I want to be explicit about why: the
correct fix is a durable, checksum-plus-map-key-keyed cache, and a cache that answers "0 touches"
from a stale key after an operator warms a new tradability map would be a silent-wrong-data defect —
strictly worse than the latency it removes. That is a design change with an invalidation contract,
not a surgical patch, and the reviewer already routed it to a follow-up
(`reports/reviews/goal-rapid-microscope-iter-21-review.md`, `micro_join.py:163`). Prescribed fix:
cache the per-dataset touch count keyed on `(dataset checksum, resolver.map_key(symbol, window_start))`,
publishing **only** when the map actually resolved (never memoize a miss, which is exactly the state
an operator warm-up flips). I weighed IMPORTANT vs GAP here and chose the higher level, per the
rubric, because the spec's own *Product surface delta* claims "no visible change against the real
production store" and a 22 s stall on a shipped section is a visible change.

**B3 — GAP: the divergence anchor extraction is quadratic; a real-corpus pilot run cannot finish**

`scout._extract_divergence_anchors` (`scout.py:525-611`) does, for every consecutive touch pair of
every band: two `mj.feature_row_at_trigger(rows, …)` calls — each of which **rebuilds a filtered copy
of the entire row list** (`micro_join._trade_rows`, `micro_join.py:215`) — plus one
`trade_rows.index(tau2_row)`, an O(n) dict-equality scan. Calibrated on a 1,000,000-row synthetic
list with the real functions:

```
feature_row_at_trigger on 1,000,000 rows (late ts): 0.096s per call
list.index(last row) on 1,000,000 row-dicts:       0.024s per call
=> one band with 2027 consecutive pairs: 7.3 minutes of pure lookup, per 1M snapshot rows
```

The real AAPL 2026-06-22 dataset alone yields **2,028 touches** on its resolved band map, and its
snapshot is 481 MB (millions of rows) — so a single band of a single dataset is tens of minutes, and
the manager's cooperative abort only checks `should_abort` at *candidate* boundaries, so such a run
cannot be cancelled. This is inside the spec's explicit OUT OF SCOPE ("running the pilot grid against
the REAL production `.data/` store"), which is why it is a GAP rather than a defect — but it must be
fixed before any real-corpus pilot run is attempted. This is the same class of bug
`micro_join._shares_horizon_row`'s own iter-4 comment records ("measured to hang
`POST /research/desk/micro/scout/compute` against the real 18-dataset corpus"). **Disclosure:** my B1
fix re-extracts anchors once more for the floor check (the snapshot-row parse is shared via
`rows_cache`, the enumeration and pair lookups are not), so it roughly doubles this cost on any
corpus where it is already impractical.

**B4 — OBSERVATION: the floor check reads the *read-exposure registry*, where the spec names
*exposed-vault* class-2 sessions**

The spec's IN SCOPE item 6 says the floor check runs "against the corpus's `historical_oos` (class-2
/ exposed-vault) session count"; `walkforward.scout_candidate_walkforward_floor_check`
(`walkforward.py:1172-1180`) instead counts sessions not marked exposed in the `ExposureRegistry`.
I traced whether these can disagree and concluded they cannot today: the candidate's
`corpus_manifest` is already `exclude_withheld`-filtered (so a sealed / not-yet-exposed shard never
reaches the observation list), and the 12 legacy tick symbol-days are pre-marked exposed by
`initialize_r2_exposure_registry`, so both definitions yield 0 OOS sessions on both the real and the
fixture corpora. The conservative `has_any_exposure_entries` guard also fails closed on an
uninitialized registry. Worth an owner note only: a legacy session missing from the r2 window list
would be counted as OOS by the registry-based rule but not by the vault-based one.

**B5 — OBSERVATION (pre-existing, reviewer already logged): an unknown `body.grid` value on
`POST /scout/compute` surfaces as a raw HTTP 500** rather than a 422 (`micro_routes.py`, the
`manager.trigger` `ValueError`). Loud, never silent, and the parameter is undiscoverable in the UI
by design (UT-09), so I left it alone rather than widen my diff.

### Frontend Findings

**F1 — OBSERVATION: `ScoutTrialRow.feature`/`outcome` are typed non-optional, but the floor-check row
omits them.** `apps/frontend/lib/types.ts:2571` declares `feature: { name; transform; params }`
while the walk-forward row carries neither `feature` nor `outcome` nor `structure_context`. There is
no runtime problem — every read in the trial-row render is optional-chained with an em-dash fallback
(`app/desk/page.tsx:6333-6350`), and `JSON.stringify(null)` renders `"null"` in the detail block, so
the row displays exactly as the UI test plan expected. Now that B1 makes such rows genuinely
reachable in the browser, widening those two fields to optional would make the type match the served
shape.

**F2 — verified, no finding: the two shipped renders do what the handoffs claim.** `UT-03`'s
screenshot shows the trial row reading `divergence_at_level_bearish / threshold (band_touch)` under
family `divergence_at_level_bearish__band_touch__trades_20`, and the Microscope Readiness table
carries the new "Joinable corpus — band touches" row. I opened `UT-06-result.png` myself: it is a
genuine tight element capture showing "Backend unreachable — is the API running?" and "Nothing
cached and nothing fabricated is shown in its place." — the UT-10 passenger DoD item is honestly
satisfied. `J-10.json` steps 9-10 are restored verbatim with the later steps renumbered to 17, and
the golden replay passed 8/8.

### Test Findings

**T1 — GAP: TC-5's headline assertions are loose where the fixture is deterministic.**
`tests/test_scout.py` TC-5 asserts `row["decision"] in scout_ledger.CLOSED_DECISIONS` and
`result["econ_interesting"] in (True, False)` — both pass for *any* outcome, which is the one thing a
known-effect oracle test should not allow. I ran the fixture myself; the values are stable and
specific: `decision = "killed_null"`, `effect_bps = -0.012`, `p_screen = 0.2179`,
`econ_interesting = False`, `fallback_tercile` splitting candidates (`low`) from comparators (`mid`).
Pinning `decision == "killed_null"` and `econ_interesting is False` would make the test discriminate.
The rest of TC-5/TC-6 is tight and genuinely non-vacuous (`n_candidate == 6`, `n_comparator == 6`,
`n_usable_sessions == 2`, the exact `missing["signal_sessions"]` string, two rows / one variant).

**T2 — no finding: TC-3, TC-9 and TC-10 are strong.** The band-touch oracle pins the exact instants
`[1.0, 4.0, 6.0]`, covers the inclusive `price_low` boundary, proves two bands arm independently, and
proves the honest empty list on an unresolved map; TC-9's sealed-shard case is non-vacuous
(`count == 0` **and** `withheld_excluded == 1`); the new guard module carries both a
planted-violation counter-test and a live check that the scan really parsed a file containing a real
`from .referee_evidence import …` line.

**T3 — OBSERVATION: one dev-handoff test count does not reproduce.** The handoff reports
`tests/test_micro_readiness.py — 198 passed`; that module collects 42 tests (the other per-module
figures — `test_micro_join.py` 44, the guard module 4 — reproduce exactly). The number the DoD
actually gates on, the full-suite count, reproduces precisely.

### Process Findings

**Q1 — the QA report over-claims on the one item the browser lane failed.** `reports/qa/…-qa.md`
ticks "✓ Floor-check decision ('insufficient_n') recorded in ledger as expected" and prints a scout
row whose `decision` is `killed_insufficient_n`. That is the **screen's** own insufficient-n kill,
not the walk-forward floor check — no floor-check row existed anywhere at the time, as the browser
lane proved the same day. The QA report also states "only 1 of 18 real datasets has a band map
today" (measured: 5) and gives an overall PASS while the merged browser verdict is FAIL. The
evaluator should not inherit those three claims; the underlying gap is now fixed (B1), but it was
fixed by this audit, not by QA's pass.

**Q2 — coverage shed by the framework's own budget trim, disclosed not hidden:** UT-J-07 is
`DEFERRED-BUDGET` (not re-verified this iteration; it has no golden script) and the ux-regression
reviewer was skipped (SPEED-15 rung 3b). The other eight required journeys replayed green.

---

## 3. Domain Assessment

The domain work is sound and, unusually for a round this size, honest about its own limits.

*Enumerator.* `enumerate_band_touches` mirrors `setups.py`'s "first touch, re-arm only once fully
exited" rule per band, resolves the map once at the window start with `compute=False` (so the GET
never computes a tradable map it does not hold), and returns an honest empty list when nothing
resolves. The sealed-shard rail holds where it matters: the sum runs over the **already
`exclude_withheld`-filtered** `records` (`micro_join.py:615`), so no sealed shard's events are read
for this count — TC-9's third case proves it non-vacuously.

*Anchor extraction.* The three-way dispatch keeps the original `"none"` body byte-identical and reuses
`join_band_touch` / `join_playbook_signal` rather than re-implementing joins. No-lookahead holds on
the divergence path: `price_history` is bounded above by tau2, `baseline_volumes` uses only the
session prefix before tau1, and the outcome is measured forward from tau2's own row position. I
checked the one crash I expected to find — `trade_rows.index(tau2_row)` where `tau2_row` came from
`feature_row_at_trigger(rows, …)` — and it cannot raise, because that function already filters to
`_trade_rows` internally, the same predicate the caller uses.

*Screen.* Re-run independently by me on the committed fixture: 6 candidate / 6 comparator anchors
over 2 sessions, `evidence_class = historical_exposed_diagnostic`, concentration, ToD, and
fallback-tercile disclosures all populated, `econ_interesting` served **beside** the statistical
result with the frozen proxy sentence, `econ_floor_computed_at <= registered_at` (TR-9). The verdict
was `killed_null` — a real decision from a real null, not a rubber stamp. The fallback-tercile
disclosure honestly reveals that the fixture's candidates and comparators separate perfectly by
fallback fraction; that is the disclosure doing its job.

*Floor check.* The conservative reading of an uninitialized exposure registry ("nothing proven ⇒ zero
OOS") is the right direction to fail, and the refusal names the exact shortfall against the pinned
`WF_TRAIN_MIN_SESSIONS`/`WF_FOLD_MIN_SIGNAL_SESSIONS` constants rather than inventing a floor. No new
threshold was introduced anywhere in the diff, `config_fingerprint` is unchanged, and the source-level
guard proving `evaluate_mode_b_fold` is never named on this path is real.

*Scope discipline.* Studies 1 and 3 are frozen in source with fully constructed fields, are named as
deferred in the dev handoff, and are structurally unreachable through the route, the CLI, and the
manager — TC-7 proves the negative directly, and the browser lane's UT-05 confirmed it against the
served JSON. Study 1's comment is candid that its `refill_consistent` co-occurrence needs
two-feature machinery that does not exist yet, rather than faking it.

The one place the implementation drifted from the spec's narrative is the walk-forward story: the
floor-check row goes to the **Scout** ledger (the reviewer flagged the wording mismatch; both
handoffs disclose it), and until this audit it went nowhere at all outside a test.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/research/scout.py` | `run_scout_grid_and_record` gains an optional `exposure_registry`; when given, each request runs through `register_screen_and_walkforward_check` (screen row + floor-check row) instead of `register_and_screen_candidate`. Returns the same one-row-per-request shape, so no existing caller changes. |
| 2 | Important | `apps/backend/app/research/scout.py` | `ScoutComputeManager.trigger` gains `exposure_registry`, **required** for `grid_selector="delta_divergence_pilot"` (mirrors the existing `resolver` requirement) and ignored for the default grid, which stays screen-only. |
| 3 | Important | `apps/backend/app/research/scout.py` | CLI `main()`'s pilot branch builds the registry from `resolve_micro_exposure_registry_dir(config.dataset_dir_resolved())` — the same durable registry `POST /walkforward/compute` reads — and passes it through. |
| 4 | Important | `apps/backend/app/research/micro_routes.py` | `POST /scout/compute` constructs `ExposureRegistry(exposure_registry_dir)` for a non-default selector only; `get_micro_exposure_registry_dir` relocated above its first `Depends(...)` use (a `Depends` default is evaluated at def time — same file, same body, one seam, still test-overridable). |
| 5 | Important | `apps/backend/tests/test_scout.py` | Two regression tests: the pilot route writes **two** rows under one `candidate_id` (stage `walkforward_floor_check`, `killed_insufficient_n`, `oos_session_count 0`, the `WF_TRAIN_MIN_SESSIONS` shortfall string, one variant, two trials served by `GET /scout`), hermetic via an empty bar store + fresh registry; and the default grid run is still screen-only. |

Post-fix verification: `pytest tests/` → **3316 passed, 8 skipped, 0 failed, 0 errors** (638.91 s);
targeted run of the new + adjacent tests → 4 passed; non-vacuity probe → the new test fails against
the pre-fix wiring; `Config().config_fingerprint()` → `08e471b10130e1e2`; `git status` shows my edits
confined to the three files above, with no `referee_*.py`, config, frontend, or journey-script change.

---

## 5. Recommended Next Step

Proceed to the next iteration. Before any pilot study is run against the real `.data/` corpus, two
things must land, in this order:

1. **B2 — durable-cache the band-touch count** keyed on `(dataset checksum, resolver map key)`,
   publishing only on a resolved map, mirroring `MicroReadinessCache`. Until then, every `/desk` load
   pays a measured 22.3 s, growing with each warmed tradability map.
2. **B3 — make `_extract_divergence_anchors` linear** (hoist `_trade_rows` out of the per-pair loop,
   walk touch pairs against a single sorted cursor, and replace `trade_rows.index(...)` with the
   index the locator already computed). Today a real-corpus pilot run cannot finish and cannot be
   cancelled mid-candidate.

Then Studies 1 and 3 can be screened as goal.md's priority order intends — Study 1 additionally needs
the two-feature (`failed_aggression_score` × `refill_consistent`) co-occurrence condition its own
frozen comment names as unbuilt.
