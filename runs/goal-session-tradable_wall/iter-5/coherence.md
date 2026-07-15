# Iteration 5 — Coherence Audit

**Iteration:** goal-tradable_wall-iter-5
**Date:** 2026-07-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

`Frontend Present: no` (confirmed by `reports/phase-goal-tradable_wall-iter-5-ui-surface-map.md`: "N/A —
Backend-only phase... No UI surfaces affected"). `git status` confirms the iteration's real diff is exactly
three files: `apps/backend/app/research/setups.py`, `apps/backend/tests/test_setups.py`,
`apps/backend/tests/test_setups_api.py`. (The passed snapshot SHA `832ea80b` is a pre-dispatch stash commit
that happens to predate the already-committed iter-4 showcase commit on this branch, so `git diff
832ea80b...` also surfaces README.md's iter-4 AUTO:capabilities bullets — those are prior, already-landed
work, not part of this iteration; `git status` is the ground truth for what iter-5 touched and is what this
audit reviews.) No IA check applies — no page/route/nav changed. This audit is Data Contract only.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Touch events + reaction labels + forward returns + case registry (existing row, single computer `setups.py`) | OK | `apps/backend/app/research/setups.py:364` `compute_setups` keeps its exact pre-iter-5 signature `(store, config) -> dict`; its only callers remain `apps/backend/app/research/routes.py:1882` (list), `:1904` (detail), `apps/backend/app/research/edge_report.py:447` (report) — none of those three call sites or their files changed (`git status` shows `routes.py`/`edge_report.py` absent from the diff) |
| B1 — `effective_reaction_horizon_bars` + `reaction_boundary_truncated` (new additive fields on the existing setups event) | OK — pre-registered, additive, not a duplicate | `apps/backend/app/research/setups.py:216-268` (`_reaction_and_forward_returns`, computes both fields alongside the untouched `reaction`/`forward_returns` logic), `:280-309` (`_event`, adds the two fields to the payload without touching `reaction`); registered in `runs/goal-session-tradable_wall/state/blueprint.md` line 54 as an additive "(iter-5)" note on the existing setups Data-Contract row, not a new row. `reaction` itself is provably unmutated: `apps/backend/tests/test_setups.py:508-514` re-asserts the pre-existing pinned AAPL 2026-06-22 fields byte-identical, and `apps/backend/tests/test_setups_api.py:87-88` only adds the two new field names to the existing `_EVENT_FIELDS` contract set |
| B3 — process-local memoized scan (`_SCAN_CACHE`) wrapping the one full-panel scan | OK — rebuildable accelerator, not a second source | `apps/backend/app/research/setups.py:347` (`_SCAN_CACHE`, module-local dict, never disk-persisted), `:350-361` (`_store_signature`, keyed off the *existing* per-series `checksum` from `store.list()` — reuses an already-computed value, does not introduce a new independent hash), `:364-380` (`compute_setups`, the public wrapper: cache hit returns the memoized result verbatim, cache miss delegates to `:382` `_run_full_panel_scan` — the renamed, byte-identical original scan body, algorithm untouched). Matches the blueprint's explicit instruction (blueprint.md:54-55, iter spec NOTES) to reuse the `bar_index.py` "cache, never a source of truth" contract |
| B3 byte-identity / cache-correctness proof | OK | `apps/backend/tests/test_setups.py:879` (cache hit == fresh uncached `_run_full_panel_scan`), `:898` (scan body runs exactly once across repeated reads via call-count spy), `:923` (a new registered series busts the cache and forces a re-scan), `:955` (an enriched `/setups/{id}`-style read never leaks into the shared cached list — copy-on-write safety) |
| Architecture guard: setups scan must never reference the DatasetStore (keeps the tape-join a single-owner concern of `enrich_with_tape_timeline` only) | OK | `apps/backend/tests/test_setups.py:495-505` (existing test extended to check both `compute_setups` and the newly-named `_run_full_panel_scan` for a `"dataset"` string) |

No new function/service/endpoint computes any registered value independently of `setups.py`, and no new UI
surface exists this iteration to fetch a value non-canonically (there is no UI change at all). Both new
fields are additive attributes on the existing, already-registered setups value — not a new value, not a
synonym/re-derivation of any other registered concept — and the blueprint already carries the iter-5 note
registering them, so neither the Part A4 (duplicate-of-existing) nor Part A5 (unregistered-new-value) case
applies.

## Information Architecture check

N/A — no page/route/feature added or changed this iteration (`Frontend Present: no`, confirmed by the
ui-surface-map and by the absence of any frontend file in the diff).

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Out of scope for this gate, noted for the reviewer/auditor's awareness only (not a coherence finding —
  no duplicate source, no cross-surface drift): `_SCAN_CACHE` (`apps/backend/app/research/setups.py:347`)
  is keyed in part on `id(config)`. In production this is safe — every route/report caller shares the one
  process-lifetime `CONFIG` singleton, so its id never changes or gets reused. Inside the test suite,
  however, each test constructs its own short-lived `Config(...)`, and nothing resets `_SCAN_CACHE` between
  test functions (no such fixture in `apps/backend/tests/conftest.py`); CPython can reuse a freed object's
  id for a later allocation, so a coincidental id + matching store-signature collision between two test
  functions could in principle serve a stale cache entry to a later test. This would surface as a flaky
  test (the call-count assertions in `test_setups.py:898`/`:923` are the ones that would notice), never as
  a wrong value served to a user or a second source of truth — production always has exactly one `CONFIG`
  object. Does not affect this verdict.
