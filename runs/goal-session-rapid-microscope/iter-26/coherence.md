# Iteration 26 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-26
**Date:** 2026-08-23
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

The iteration's only Data-Contract-touching value is `joinable_corpus.band_touch_count`, already
registered under the "Corpus readiness truth ... + joinable-corpus counts" row (owner
`app/research/micro_readiness.py` + `micro_join.py`, endpoint `GET /research/desk/micro/readiness`,
blueprint.md lines 54, 128-131). Verified against the actual diff (`git diff
1bdf43ae39bb23bb8b780438d26b453d8be11485`):

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `joinable_corpus.band_touch_count` | OK | `apps/backend/app/research/micro_join.py:660-688` — the new `MicroBandTouchCache` lookup/publish path still terminates in the SAME canonical `enumerate_band_touches(meta, dataset_store, resolver)` call on both the cache-hit-miss branch (line 683) and the not-cacheable branch (line 686); the cache never independently computes a touch count. |
| Response shape at `GET /research/desk/micro/readiness` | OK | `apps/backend/app/research/micro_readiness.py:604-608` (the `joinable_corpus = joinable_corpus_counts(...)` call site) — only an additional optional `band_touch_cache=` kwarg was threaded through `build_readiness` → `joinable_corpus_counts`; the returned dict's construction (`micro_join.py:688-696`) is untouched, confirmed by an empty diff around every `return {` site in `micro_readiness.py`. |
| `enumerate_band_touches` (the underlying enumeration primitive, also used by `scout.py:475,553` for a different purpose — pilot-study anchor extraction) | OK — not a violation | `apps/backend/app/research/scout.py:475,553` calls the SAME `mj.enumerate_band_touches`, not a reimplementation; pre-existing, unchanged this iteration. |
| Scout pilot-selector→kind mapping | OK | `apps/backend/app/research/micro_routes.py:308-320` — `_pilot_selectors_by_kind()` now filters the ONE canonical `scout._PILOT_GRID_SELECTORS` table (`apps/backend/app/research/scout.py:1684-1689`) instead of restating two hand-written frozensets. Confirmed genuine derivation (not incidental equality) via `test_tc6b_a_synthetic_third_entry_in_a_local_copy_grows_the_derived_set` (`apps/backend/tests/test_scout.py:1893-1912`) and a source-scan guard with zero hand-written selector literals left in `micro_routes.py` (`test_tc6c_...`, `test_scout.py:1917-1931`), which I re-ran the grep for myself: `grep -rn "MicroBandTouchCache\|_pilot_selectors_by_kind" app/ tests/` shows the cache and selector-derivation function reached from the real route code (`micro_routes.py:110,356,360`), not only from tests — satisfying this iteration's own iter-21-lesson reachability check. |

No new displayed value is introduced this iteration (confirmed by the diff `--stat`: only
`micro_join.py`, `micro_readiness.py`, `micro_routes.py`, and three test files changed; zero
frontend files, zero new endpoints, zero new MCP tool files).

## Information Architecture check

Zero new pages/routes/features this iteration — the diff touches only three backend research
modules and their tests. No nav/sidebar/router file changed.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new feature/page/route this iteration) | OK | n/a — `git diff --stat` shows no `.tsx`/nav file changed; `reports/phase-goal-rapid-microscope-iter-26-ui-surface-map.md` independently confirms "Frontend surfaces changed: 0" |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. This iteration is a clean, narrowly-scoped internal caching layer (mirroring the existing
  `MicroReadinessCache` precedent byte-for-byte in contract, per the module's own docstring) plus a
  genuine single-source-of-truth dedup of a previously-duplicated selector table — exactly the kind
  of consolidation work this gate exists to reward, not flag.
