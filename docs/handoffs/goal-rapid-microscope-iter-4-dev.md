# goal-rapid-microscope-iter-4 Dev Handoff

**Phase:** goal-rapid-microscope-iter-4
**Date:** 2026-08-17
**Agent:** developer
**Status:** complete

## What Was Built

### J-04: the Scout and the exploratory candidate ledger

- **`app/research/scout_ledger.py`** (new) — a hash-chained, append-only JSONL candidate ledger
  (spec §5.1/§5.2), genuinely linked (each row's `row_hash` commits to its own content AND the
  previous row's `row_hash` — a real chain, not the `desk_playbook_log.py` per-row-checksum
  pattern that inspired it, since that pattern cannot localize a tamper/deletion to a single row).
  `ScoutLedger.append_row` is a pure storage primitive (hash-chains and persists whatever it's
  given, enforcing no business rule); `verify_chain()` reports `{"ok", "failed_at_row", "reason"}`,
  never raises. `variants_tried_for_family` is the union-N denominator across every `grid_version`
  ever registered for a family. `compute_family_root_id` implements the r2 formula
  (`sha256(canonical(feature_family_name, structure_context_kind, outcome_horizon_family))[:16]`).
- **`app/research/scout.py`** (new) — the screening engine:
  - `extract_anchors` reads eligible trade-anchored snapshot rows and their outcomes through
    `micro_join.py`'s already-tested machinery (no second outcome implementation);
    `structure_context.kind` is validated against the closed 3-value vocabulary but only `"none"`
    has a wired read path this iteration (pilot-study joins are J-09's scope).
  - `screen_candidate` (spec §5.3/§5.4/§5.5): membership via a `threshold` transform, the observed
    session-clustered effect, a within-session circular BLOCK-PERMUTATION null
    (`SCOUT_BLOCK_PERMUTATIONS = 2,000` draws, vectorized via numpy — see "A numpy interpretation
    call" below), every mandatory disclosure (concentration, ToD buckets via
    `referee_null.tod_bucket_for_epoch`, fallback-tercile stratification for aggressor-derived
    features only, the best-of-N Bonferroni-style corrected-threshold disclosure), the
    economic-relevance column with the frozen proxy sentence verbatim, and the seven-way
    closed-vocabulary decision (`survive` or one of the six kill reasons, all reachable and each
    covered by a dedicated unit test).
  - `register_and_screen_candidate` is the ONE production registration boundary: builds the frozen
    spec, enforces TR-9 (registration-ordering) and the 24-variant grid cap BEFORE any ledger row
    is written, then screens and appends.
  - `default_fixture_grid` / `run_scout_grid_and_record` / `ScoutComputeManager` / `main()` mirror
    `micro_snapshots.py`'s manager+CLI pattern exactly (single-flight, pollable progress,
    cooperative cancel, terminal-state-only ledger writes — a mid-run exception resolves to
    `"failed"`, never a silently-short ledger).
  - `_plain_shuffle_null_deltas` is the TR-8 banned-shuffle counter-test null — reachable only from
    `tests/test_scout.py`, never from any production path (source-checked by a dedicated test).
- **`app/research/micro_routes.py`** — three new routes wired alongside the existing
  readiness/snapshot routes: `GET /research/desk/micro/scout`, `POST` + `GET` +
  `POST .../compute/cancel` on `/research/desk/micro/scout/compute`, `GET
  /research/desk/micro/scout/runs`. Reuses `get_dataset_store` verbatim; a new
  `get_scout_ledger_dir` resolver + `ScoutComputeManager` singleton mirror the snapshot routes'
  own wiring precedent.
- Fixture grid: 3 features spanning the three Wave-1 families (`cumulative_delta`/F-FLOW,
  `failed_aggression_score`/F-RESPONSE, `quote_imbalance`/F-LIQUIDITY) × 2 threshold directions =
  6 candidates, run end to end through both the manager and the CLI over the committed
  `tests/fixtures/datasets/` + `tests/fixtures/datasets_j03/` fixtures (all one session date) —
  every candidate honestly reads `killed_insufficient_n` (goal.md's own Vision: "zero survivors is
  a passing grade"). Zero registered candidates condition on `quote_depletion` (TC-13) — that
  feature name is structurally absent from `FEATURE_FAMILY_OF`, so it cannot even be registered.

### Passenger fixes (`micro_join.py`, carried from iteration 3's next-step recommendation)

- **Corrupt-record surfacing**: `joinable_corpus_counts` now captures BOTH halves of
  `playbook_store.list()` (`records, errors`) and serves `errors` verbatim as a new
  `playbook_integrity_errors` key — a corrupted playbook file used to vanish silently from
  `total`/`playbook_signal_count`/`by_setup_id` (`playbook_store.list()[0]`, the discarded second
  element); it is now surfaced and the healthy records still count correctly.
- **`band_touch_count` typed shape**: replaced the bare `0` literal with
  `{"status": "not_enumerated", "count": None}` (`BAND_TOUCH_STATUS_NOT_ENUMERATED`) — a reader
  can no longer mistake "no detector exists yet" for "counted and found zero". `total` is now
  `playbook_signal_count` alone (numerically identical to before, since the bare `0` never
  contributed to the sum either). `micro_readiness.py`'s own no-playbook-store fallback shape was
  updated to match.

## Files Changed

- `apps/backend/app/research/scout_ledger.py` -- NEW: the hash-chained candidate ledger.
- `apps/backend/app/research/scout.py` -- NEW: the screening engine, compute manager, CLI.
- `apps/backend/app/research/micro_routes.py` -- MODIFY: 3 new scout routes + resolver + manager
  singleton.
- `apps/backend/app/research/micro_join.py` -- MODIFY: the two passenger fixes, PLUS a discovered
  performance fix (see "Known Issues" — `outcome_rows_at_position`, `outcome_row_at_single_horizon`,
  and an index-iteration rewrite of `_shares_horizon_row`/`_clock_horizon_row` that eliminates a
  per-call O(n) slice copy). All additive/behavior-preserving; zero change to any existing function's
  output.
- `apps/backend/app/research/micro_readiness.py` -- MODIFY: pass through the new
  `band_touch_count`/`playbook_integrity_errors` shape in the no-playbook-store fallback.
- `apps/backend/tests/test_scout_ledger.py` -- NEW: TC-1, TC-2, TC-3, TC-4, TC-9, TC-13.
- `apps/backend/tests/test_scout.py` -- NEW: TC-5 through TC-8, TC-10 through TC-12, plus direct
  unit coverage of every decision branch, `extract_anchors`, and the pure statistical core.
- `apps/backend/tests/test_micro_join.py` -- MODIFY: TC-14, TC-15, TC-16, plus 5 new equivalence
  tests for the perf-fix functions.
- `apps/backend/tests/test_micro_readiness.py` -- MODIFY: TC-15 (typed `band_touch_count` at the
  readiness route), plus updated assertions for the changed shape.

No `docs/goal.md`, `blueprint.md`, or `docs/rapid-validation-spec.md` edit — confirmed accurate for
this scope at planning time, re-confirmed true after the build.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/` (no extra `-q` per the iter-0
lesson; `pyproject.toml`'s own `addopts = "-q"` already applies).

Result: **2934 passed, 8 skipped, 0 failed** (baseline was 2,866 pass / 8 skip; net +68 tests: 15
in `test_scout_ledger.py`, 41 in `test_scout.py`, 5 new in `test_micro_join.py` for TC-14/15/16 plus
the perf-fix equivalence proofs, 2 new in `test_micro_readiness.py` for TC-15, plus 5 more
equivalence tests added after the perf-fix discovery — see the exact per-file counts in the "Known
Issues" section below).

Re-verification checks (TC-17/TC-18/TC-19, run directly, not through the browser rig — TC-20 is
`browser-qa-agent`'s job):
- `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged).
- `git diff` over `app/engine/`, `desk_playbook.py`, `desk_playbook_context.py`, and all 6
  `referee_*.py` files → empty (byte-untouched).
- The 18 real-corpus snapshot `.jsonl` files' row total → `3,815,933` (unchanged; this iteration's
  diff never touches `micro_features.py`/`micro_observer.py`, so no rebuild was expected or
  triggered).
- Full suite: 2,934 ≥ 2,866, 8 skip (matches), 0 new failures.

Service-startup verification: `uvicorn app.main:app` started cleanly on the project's deterministic
port (8301), served `/health` and the new `/research/desk/micro/scout*` routes at HTTP 200, was
stopped by its exact recorded PID, and restarted cleanly on the same port with no conflict.

## Known Issues

**A genuine, discovered-and-fixed performance defect (not in either report — no prior report
existed; this is INITIAL BUILD).** While verifying the compute manager against the REAL live
backend (not just fixtures — the pre-handoff checklist's own "verify it actually runs" bar), `POST
/research/desk/micro/scout/compute` against the real 18-dataset legacy tick corpus hung
indefinitely (still `candidates_done: 0` after 60+ seconds, unable even to honor a cancel request).
Root-caused to three compounding issues in the extraction path this iteration's own new caller
(`scout.extract_anchors`, iterating every anchor of a whole dataset) was the first to exercise at
this scale:

1. `micro_join.outcome_rows_after_trigger`'s internal `trade_rows.index(anchor_row)` is an O(n)
   scan — fine for its existing callers (once per playbook signal/band touch), O(n²) overall for a
   caller evaluating every anchor of a dataset. Fixed by adding `outcome_rows_at_position` (an
   additive, position-taking twin that skips the lookup — byte-identical output, regression-tested).
2. `micro_join._shares_horizon_row`/`_clock_horizon_row` re-sliced the remaining trade list
   (`trade_rows[anchor_pos + 1:]`) on EVERY call regardless of how quickly the loop broke — another
   O(n)-per-call cost, summed to O(n²) again. Fixed by iterating with an explicit index
   (`range(anchor_pos, len(trade_rows))`) instead of slicing — behavior-unchanged (regression-tested
   against a hand-computed reference), pure performance fix.
3. `_outcome_rows_after` always computes the FULL 7-horizon closed set even when a caller wants
   exactly one — wasteful when called once per anchor across a large dataset. Fixed by adding
   `outcome_row_at_single_horizon` (computes only the requested horizon, reusing the SAME
   per-horizon-kind row-finders — no second implementation; regression-tested against the matching
   entry of the full set).

After these three fixes, the compute manager completes in well under a second against small/medium
real corpora (verified live against 7 genuinely-recorded, non-fixture PG datasets) and no longer
risks the pathological blow-up. `default_fixture_grid` was ALSO changed to use only trade-count
horizons (`trades_20`, resolved by direct index arithmetic, genuinely O(1) per anchor) rather than a
`clock_seconds` horizon, which still requires a bounded forward scan.

**A remaining, disclosed limitation (not a bug, an inherent cost): the FULL 18-dataset real legacy
corpus (~3.8M events, several single-symbol sessions of 200K–929K trades each) still takes several
minutes for the default 6-candidate grid**, because (a) reading+extracting a session with hundreds
of thousands of trades takes tens of seconds even at O(1)-per-anchor cost, and (b) the block-
permutation null (2,000 draws × every usable session) is genuinely O(draws × session-size) work —
this iteration ALSO added memory-bounded batching (`_NULL_DRAW_BATCH_MAX_ELEMENTS`) to the null
computation after discovering that the UNBATCHED vectorized approach would have tried to allocate a
`(2,000, ~900,000)` array (~14 GB) for NVDA's single session alone — a genuine host-stability risk on
this shared, host-guard-governed machine, not merely a slow path. After batching, peak memory is
bounded regardless of corpus size; wall-clock time for the full real corpus is still on the order of
minutes, consistent with this project's own precedent for "heavy" real-corpus computations (the
edge-report sweep's own cold-run time). This iteration's own acceptance scope (TC-1 through TC-13)
is the bounded FIXTURE grid, which completes in well under a second — verified, not assumed. Flagging
this real-corpus runtime honestly for the reviewer/auditor/product-manager to weigh in on whether a
dedicated performance iteration (this project's own precedent — see the "Edge-report perf fix" and
"Structure load latency fix" entries in prior-session memory) is warranted before J-06's real
~150-symbol-day corpus lands.

**Interpretation calls made this iteration** (T-1: the spec fixes the CONTRACT; several
implementation-level judgment calls were still required and are logged here, not invented silently):

- `decision` and `reason` are the SAME closed-vocabulary token on every row (spec §5.2 names them as
  two fields without further disambiguation); `notes` carries the free-text elaboration.
- `family_id` (the grid-registration/24-cap bucket) is `f"{feature.name}__{structure_context.kind}
  __{horizon_key}"` — finer-grained than `family_root_id` (the coarser, rename-resistant lineage key
  spec §5.1 defines by formula), matching the spec's own distinction between the two fields.
- Structural (never outcome-tuned) floors this iteration had to choose since the spec does not name
  them explicitly: `SCOUT_MIN_SESSION_CLUSTERS = 2` (the mathematical minimum for a between-cluster
  comparison), `SCOUT_MIN_OBSERVATIONS_PER_CELL = 5`, `SCOUT_MAX_TOP1_CONCENTRATION = 0.8` (and,
  specifically, the symbol-share half of that ceiling only gates when a candidate's own corpus
  genuinely spans more than one symbol — a single-symbol `corpus_manifest`, like this iteration's own
  fixture grid, trivially reads `top1_symbol_share == 1.0` always, which is a structural fact about
  the corpus, never a concentration risk to kill on). All three are frozen module constants, chosen
  before any outcome was read, never tuned from a result.
- `killed_fragile`'s check (leave-out-the-most-represented-session sign stability) is a real,
  reachable branch with its own direct unit test AND an indirect proof through `screen_candidate`
  itself (via a monkeypatched `_two_sided_p` to force significance, since hand-tuning a fixture that
  is simultaneously significant, concentration-clean, econ-interesting, AND fragile proved
  impractical) — logged as a deliberate test-design choice, not a shortcut on the implementation.
- `_block_length_for_horizon` uses the smallest trade-count horizon (20) as a conservative floor for
  shares/clock horizons, since their own event span varies row to row and the spec ties block length
  to "the label span in events".
- The best-of-N disclosure is a Bonferroni-style corrected null threshold (`quantile(|null|, 1 -
  alpha/N)`), not a literal "expected value" computation — spec §5.4 only requires it be "a
  disclosure, never a decision rule", which this satisfies.
- Numpy is used to vectorize the 2,000-draw permutation null (both variants); the RANDOMNESS decision
  still runs through this module's one seeded `scout_stream` (`random.Random`) constructor per the
  spec's own recipe — a numpy `Generator` seeded from `rng.getrandbits(63)` is used purely as a fast
  bulk-arithmetic ENGINE for a stream whose seed lineage is already fully determined. Numpy is an
  existing project dependency (already used by `levels.py`), not a new one.

No gaps against this iteration's own DEFINITION OF DONE — every listed TC-1 through TC-19 item is
implemented and verified; TC-20 is `browser-qa-agent`'s scope (J-04 has no browser surface this
iteration; J-01/J-02/J-03/J-10 are the required-still-passing regression set for that agent to
re-verify).
