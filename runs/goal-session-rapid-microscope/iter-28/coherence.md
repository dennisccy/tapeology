# Iteration 28 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-28
**Date:** 2026-08-23
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope of this iteration's diff

Snapshot SHA `d397ad4bdfcd3850870dfbb1ab7ad7a0c48273c6` → current tree. Noise-excluded
`git diff --stat` shows exactly 3 tracked files changed (160 insertions, 7 deletions), plus 1 new
untracked test file:

- `apps/backend/tests/test_micro_readiness.py` — test-fixture-only change.
- `apps/backend/tests/test_micro_join.py` — test-fixture-only change.
- `apps/backend/tests/test_micro_readiness_seal_unaware_caveat.py` (new) — test-only, guards the
  frontend caveat's single-source-of-truth property.
- `apps/frontend/app/desk/page.tsx` — 1 new `<p>` element + 1 new string constant inside the
  already-shipped `RefereeEvidenceReadinessSection`.

No `app/research/*.py`, `app/routes.py`, or `referee_*.py` production file changed. No new route,
page, endpoint, or nav element. This matches the iteration spec's IN SCOPE list exactly.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Corpus readiness truth / `micro_readiness` (registered row) | OK | `apps/backend/tests/test_micro_readiness.py:388-419` (fixture rewire only, calls the same `build_readiness`/`MicroReadinessCache`/`DatasetStore` from `app/research/micro_readiness.py`, no new computation) |
| Joinable-corpus counts / `micro_join` (registered row) | OK | `apps/backend/tests/test_micro_join.py:54-64,966,990` (new `_real_corpus_dataset_store()` helper only changes which `index_db_path` a `DatasetStore` is constructed with; calls the unchanged `micro_join.joinable_corpus_counts`) |
| `referee_evidence.strategy_trade_readiness` (Unchanged-owners row: `referee_evidence.py` / `GET /research/desk/referee/evidence`) | OK | `apps/frontend/app/desk/page.tsx:5017-5029,5210-5216` — new `<p>` renders a static disclosure string next to the already-served `strategy_trade` fields; it does not fetch, recompute, or reformat any value. `referee_evidence.py`/`referee_routes.py` are untouched (confirmed via diff — zero hunks in either file) |
| New disclosure sentence (spec §10.7, r5 owner ruling) | OK — verified verbatim, single source | `apps/frontend/app/desk/page.tsx:5028-5029` matches `docs/rapid-validation-spec.md` §10.7 character-for-character (confirmed by direct extraction/comparison); defined once as `REFEREE_EVIDENCE_SEAL_UNAWARE_CAVEAT`, referenced exactly once at `page.tsx:5214`; no other occurrence anywhere in `apps/frontend/app` or `components` |

Both production caching primitives the test fixtures now reuse
(`resolve_micro_readiness_cache_db_path`, `TAPEOLOGY_DATASET_INDEX_DB`-env-or-sibling
`dataset_index.db`) are the SAME ones `routes.py`'s `get_dataset_store()` already wires for the
live backend — no second/new caching mechanism was introduced, and no registered value gained a
second computation path.

The disclosure sentence is not a computed/fetched value — it carries no data, so it is not itself
a "new displayed value" requiring a Data Contract row (Data Contract rows exist for values a
module computes and an endpoint serves). The iteration spec explicitly frames it as "the one
deliberate, owner-authorized exception to Foundation invariant 5 — descriptive copy only, never a
computed value" and blueprint.md's Data Contract table already lists the parent
`referee_evidence`/`strategy_trade` fields it sits beside under "Unchanged owners."

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` → Referee Registry → Strategy Family (new caveat line) | OK | No nav change — the element is added inside the already-shipped `RefereeEvidenceReadinessSection` component, itself already nested under the Desk → Referee Registry section per blueprint.md's IA table ("Unchanged owners" row). Confirmed no new route/page/component tree via the noise-excluded diff (only `page.tsx` line-range 5017-5216 touched) and via `reports/phase-goal-rapid-microscope-iter-28-ui-surface-map.md` ("New pages/routes: 0", "Navigation changes: no"). |

No new page, no parallel shell, no duplicate home. The one new UI element lands exactly in its
blueprint-designated home.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. This is a clean, narrowly-scoped iteration: two test-fixture caching fixes (reusing existing
production primitives, zero production-code diff) plus one static disclosure string rendered once,
from one constant, verbatim-matching its spec source, beside its already-canonical registered
value. No coherence drift introduced.
