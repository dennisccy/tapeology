# goal-rapid-microscope-iter-28 Execution Plan

## What to Build
- Give `test_micro_readiness.py`'s module-scoped `real_readiness`/`real_dataset_records`
  fixtures (lines 460-479) a PERSISTENT, gitignored on-disk cache instead of a fresh
  `tmp_path_factory` dir each run: point `MicroReadinessCache` at a durable file AND pass
  `DatasetStore(..., index_db_path=<durable path>)` — reuse the exact same primitives
  `get_dataset_store()` already wires in `routes.py` (`resolve_micro_readiness_cache_db_path()`
  for the cache DB; the `TAPEOLOGY_DATASET_INDEX_DB`-env-or-sibling `dataset_index.db` pattern for
  the store index). No new cache class. TC-1..TC-5 stay byte-identical, just fast on a warm cache.
- Give `test_micro_join.py`'s two real-corpus tests (`test_tc16_real_corpus_joinable_corpus_
  arithmetic_is_unchanged_by_the_passenger_fixes` L943, `test_tc4_real_corpus_join_playbook_
  signal_is_unaffected_by_the_accessor_re_point` L967) the same durable `index_db_path=` treatment
  on their `DatasetStore(CONFIG.dataset_dir_resolved())` construction.
- Add a static-scan guard test (extend `test_micro_no_referee_evidence_guard.py` or add a sibling)
  asserting the spec §10.7 verbatim caveat sentence is defined EXACTLY ONCE as a shared string
  constant in the frontend source and matches `docs/rapid-validation-spec.md` §10.7
  character-for-character (see exact text below).
- Render that caveat sentence in `apps/frontend/app/desk/page.tsx`'s existing
  `referee-evidence-strategy-block` (lines 5152-5225), beside the already-served
  `Datasets`/`Trades`/tick-gate figures, under a NEW `data-testid` not reused from any existing
  shipped testid.
- Verify (no code change expected) all six `referee_*.py` files re-hash byte-identical to the
  iteration-0 SHA-256 listing (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md:75-81`).
- Write dev handoff with before/after wall-clock timing evidence for the two fixed test files.

## Verbatim caveat text (spec §10.7, character-for-character — use exactly this)
"Legacy Referee readiness metric — seal-unaware in the Rapid Microscope era. It may include
withheld/unexposed Rapid-Microscope shards and must not be used as the canonical Rapid-Microscope
readiness count."

## Agents Required
- backend-data: yes -- durable cache/index wiring in the two real-corpus test files + the new
  static-scan guard test + referee-module SHA-256 re-verification. No production backend code
  changes are anticipated (this is a test-infra fix); if a production change turns out to be
  needed, it must stay inside the already-existing `get_dataset_store()`/`MicroReadinessCache`
  primitives, never a new mechanism.
- frontend-ux: yes -- one new `<p>`/`<li>` caveat element inside the existing
  `referee-evidence-strategy-block` on `/desk`, sourced from a single shared string constant.

## Frontend Present: yes

## Files to Create/Modify
- `apps/backend/tests/test_micro_readiness.py` -- durable `MicroReadinessCache` DB path +
  `DatasetStore(index_db_path=...)` for the module-scoped `real_readiness`/`real_dataset_records`
  fixtures (lines ~460-479); pick a persistent, gitignored path (e.g. under
  `apps/backend/.data/` or a dedicated test-cache dir already covered by `.gitignore` — confirm
  before creating a new gitignore entry) so warm reuse survives across pytest invocations.
- `apps/backend/tests/test_micro_join.py` -- same durable `index_db_path=` treatment on the two
  real-corpus `DatasetStore` constructions at lines ~943 and ~967.
- `apps/backend/tests/test_micro_no_referee_evidence_guard.py` (or a new sibling test file in the
  same directory) -- static-scan test for the single shared caveat string constant, exact-match
  against `docs/rapid-validation-spec.md` §10.7.
- `apps/frontend/app/desk/page.tsx` -- new caveat element inside `referee-evidence-strategy-block`
  (lines 5152-5225), likely sourced from a shared constant near the top of the file (or a small
  `desk/copy.ts`-style module if one already exists for this kind of static copy — check
  `test_copy_discipline.py`'s expectations before inventing a new location).
- `docs/handoffs/goal-rapid-microscope-iter-28-dev.md` -- dev handoff with before/after timing
  evidence for both fixed test files, plus the referee SHA-256 re-check result.
- `docs/handoffs/goal-rapid-microscope-iter-0-dev.md` -- READ ONLY (lines 75-81 carry the
  iteration-0 SHA-256 baseline to re-verify against; do not edit).

## UI Evolution
- New user-facing capability: none (disclosure only, per spec — no new action, no new page).
- New information displayed: the verbatim seal-unaware disclosure sentence rendered beside the
  Referee Registry → Strategy Family block's existing Datasets/Trades/tick-gate figures on
  `/desk`.
- New user actions: none.
- UI surface changes: one new element inside the already-shipped
  `referee-evidence-strategy-block`. No new section, no new page, no nav change.
- Navigation changes: none.

## Visual Requirements
- Component patterns: match the existing block's style exactly — reuse the same `<p>`/`<ul><li>`
  treatment already used for `referee-evidence-strategy-tick-gate` /
  `referee-evidence-strategy-basis-caveats` (`text-[11px] text-slate-400`/`text-slate-500`
  classes), so the new line reads as part of the same disclosure family, not a new visual unit.
- Layout: inline within the existing table/caveat stack in `referee-evidence-strategy-block` —
  do not create a new card, panel, or section.
- Key visual effects: none new — this is static disclosure copy, not an interactive element; no
  color implies advice (per Design Direction: class labels render verbatim, no color implies
  advice).
- States to handle: none new (static text, always rendered whenever the block itself renders;
  no loading/empty/error state of its own since it is not computed).

## Key Test Scenarios
- TC-1: `MicroReadinessCache` DB + `DatasetStore.index_db_path` in `test_micro_readiness.py` point
  at a persistent on-disk location; run `pytest tests/test_micro_readiness.py -k real` twice back
  to back with no source changes — the second (warm) run completes in <60s wall-clock, and both
  runs produce byte-identical TC-1..TC-5 results.
- TC-2: same durable `index_db_path=` treatment in `test_micro_join.py`'s two real-corpus tests;
  run twice back to back — second (warm) run completes in <30s combined, and
  `counts["playbook_signal_count"] == 2`, `counts["by_setup_id"] == {"range_trade": 2}`,
  `counts["playbook_integrity_errors"] == []` hold unchanged both runs.
- TC-3: full `pytest tests/` run completes with an explicit pass/fail summary line (never killed
  mid-run); combined `test_micro_readiness.py` + `test_micro_join.py` runtime is NOT the largest
  single contributor to total suite wall-clock on a warm cache.
- TC-4: grep frontend source for the verbatim sentence — found exactly once, sourced from a
  single shared string constant, matching spec §10.7 character-for-character.
- TC-5: `/desk` loaded live (backend+frontend booted, `rm -rf apps/frontend/.next` + rebuild per
  T-9) with Referee Registry expanded; browser-qa captures the Strategy Family block as an
  ELEMENT-scoped screenshot (never a full-page stitch) showing the new caveat text beside the
  Datasets/Trades figures, under a data-testid distinct from every existing shipped testid in
  that block.
- TC-6: `test_micro_no_referee_evidence_guard.py`'s existing 4 tests (TC-10, committed iter-21)
  still pass unmodified after this iteration's changes.
- TC-7: all six `referee_*.py` files re-hash byte-identical to the iteration-0 SHA-256 listing
  (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md:75-81`); `git diff` on each is empty.
- TC-8/TC-9: J-01's and J-10's stored goldens (`journey-scripts/J-01.json`, `J-10.json`) replay
  end to end with 0 failed steps post-change (J-10's step-12 "variants tried" assertion
  unaffected by the new caveat markup elsewhere on the page).
- TC-10: a deliberately corrupted dataset file planted in a scratch copy of the store used by
  `test_micro_readiness.py`'s real-corpus fixtures, built against that scratch copy with a WARM
  durable index/cache pointed at a DIFFERENT store's content, still surfaces as an
  `integrity_errors` row — the cache never masks or bypasses checksum verification for content it
  has not actually verified.
- TC-11 (passenger, not planned scope): while browser-qa live-drives J-01/J-10, also capture an
  element-scoped screenshot of the Scout Ledger family row (`data-testid=
  "scout-ledger-families-block"`) showing "N variants tried" in frame — satisfies J-08's owed
  make-up capture as a byproduct, never claimed as this iteration's own goal.

## Anti-Goal / Scope Guardrails (binding, from the phase spec)
- Do NOT edit `referee_evidence.py`, `referee_routes.py`, or any other `referee_*.py` file —
  verification-only re-hash against the iteration-0 baseline.
- Do NOT intercept or wrap `DatasetStore`/`referee_evidence` to change frozen Referee behavior
  indirectly — the caveat is frontend-only static copy, never a computed value.
- Do NOT invent a new caching mechanism — reuse `MicroReadinessCache` +
  `DatasetStore(index_db_path=...)` exactly as `get_dataset_store()` in `routes.py` already does.
- Do NOT rebuild or modify `test_micro_no_referee_evidence_guard.py`'s existing 4 tests — only
  extend it (or add a sibling) and re-run the existing 4 unmodified.
- Do NOT record new tape, expose/assign any sealed shard, run J-09 against the real recorded
  corpus, or move the fingerprint pin `08e471b10130e1e2`.
- Do NOT add any new `Config` field, fold/grid/threshold change, or playbook detector change.
- Do NOT treat the two make-up captures (Desk readiness figures — already closed per iter-27; Scout
  Ledger "variants tried" row) or demo-step-04 regeneration as planned deliverables — they may ride
  passenger on this round's own browser-qa pass over J-01/J-10, never as a goal.
- Browser evidence must be ELEMENT-scoped (`data-testid`-targeted) for J-10's sentinel and any
  Scout Ledger make-up capture — a full-page stitched `/desk` capture is NOT acceptable evidence
  (iter-27's own lesson: duplicated headers, mid-table truncation).
- `rm -rf apps/frontend/.next` + rebuild before any browser pass (T-9); no screenshot ⇒ `unknown`,
  never `passing` (T-10).

## Notes for the Developer
- This is a re-dispatch of iter-27's identical, previously undelivered plan — the diagnosis is
  already fully verified in the phase spec's BACKGROUND section; no re-derivation needed.
- Before writing any claim, open and read the actual screenshot/log content cited — do not narrate
  from a step name (iter-27's most frequent defect class, 5+ occurrences).
- Target journeys J-01 and J-10 need genuine browser-qa (LLM) verification this round, not a
  replay-only claim — the deterministic replay lane structurally cannot execute a target journey's
  own golden in the round that touches it.
