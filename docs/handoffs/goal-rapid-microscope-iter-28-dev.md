# goal-rapid-microscope-iter-28 Dev Handoff

**Phase:** goal-rapid-microscope-iter-28
**Date:** 2026-08-23
**Agent:** developer
**Status:** complete

## What Was Built

This iteration was a re-dispatch of iter-27's identical, previously-undelivered plan (iter-27's
own spec diagnosed the problem correctly but the engine's SPEED-9 evidence backstop demoted the
round before any developer touched code). Two independent fixes:

1. **Test-infra fix — durable-cache reuse for the two real-`.data`-corpus test files.**
   `test_micro_readiness.py`'s module-scoped `real_readiness`/`real_dataset_records` fixtures and
   `test_micro_join.py`'s two real-corpus tests (`test_tc16_real_corpus_joinable_corpus_
   arithmetic_is_unchanged_by_the_passenger_fixes`, `test_tc4_real_corpus_join_playbook_signal_
   is_unaffected_by_the_accessor_re_point`) each constructed a fresh `DatasetStore` with no
   `index_db_path=` and a throwaway `tmp_path_factory` `MicroReadinessCache` DB on every single
   pytest invocation, forcing a full re-parse + re-checksum of the entire real `.data/datasets`
   directory (now 26 GB / 98 files — the J-06 recorder's sealed tranche lives in the same store)
   on every run. Fixed by pointing both files' real-corpus `DatasetStore` construction at the
   SAME durable, production-shape cache primitives `get_dataset_store()` already wires in
   `routes.py`: `TAPEOLOGY_DATASET_INDEX_DB`-env-or-sibling `dataset_index.db` for the
   `DatasetStore`'s own metadata index, and `resolve_micro_readiness_cache_db_path()` (already
   imported) for `MicroReadinessCache`'s DB. No new cache class or mechanism was introduced —
   this is exactly the same content-checksum/`(size, mtime_ns)`-keyed, "owns nothing" derived
   cache the live backend already relies on, so sharing it with the running backend is the
   intended reuse (both files already live under the gitignored `.data/` tree).
2. **New test coverage: TC-10 (this iteration's own), corrupted-file-with-warm-cache.** Added
   `test_tc10_corrupted_dataset_surfaces_with_a_warm_durable_index_from_a_different_store` to
   `test_micro_readiness.py`, proving a durable index db warmed against a completely different
   store's content never masks a checksum failure in a brand-new store's own files (the index
   keys on absolute file path, so a scratch copy's never-before-seen path is always a genuine
   miss and the full verifier still runs).
3. **The r5-point-7 owner-ruled disclosure sentence.** `referee_evidence.strategy_trade_
   readiness`'s served metric is seal-unaware (counts dataset FILES through its own enumeration,
   may include withheld/unexposed Rapid-Microscope shards). `referee_evidence.py`/
   `referee_routes.py` stay byte-frozen this whole era, so the verbatim spec §10.7 caveat
   sentence is now rendered at the FRONTEND layer only, inside the already-shipped Referee
   Registry → Strategy Family block on `/desk`, beside the existing Datasets/Trades/tick-gate
   figures. This is the iteration's one deliberate, owner-authorized exception to Foundation
   invariant 5 — static disclosure copy only, never a computed value, never a behavior change.
4. **A static-scan guard proving the caveat is exact and singular.** New sibling test file
   `test_micro_readiness_seal_unaware_caveat.py` (deliberately never touching the existing,
   frozen `test_micro_no_referee_evidence_guard.py`) asserts the caveat sentence is defined
   exactly once as a shared frontend string constant, is actually rendered, and matches
   `docs/rapid-validation-spec.md` §10.7 character-for-character (with a non-vacuity
   counter-test proving a paraphrase would fail the check).

## Files Changed

- `apps/backend/tests/test_micro_readiness.py` — `real_readiness`/`real_dataset_records`
  fixtures (was lines 460-479) now construct `DatasetStore` with the production `index_db_path=`
  resolution and `MicroReadinessCache(resolve_micro_readiness_cache_db_path(dataset_dir))`
  instead of a fresh `tmp_path_factory` dir; added `import os`; added new test
  `test_tc10_corrupted_dataset_surfaces_with_a_warm_durable_index_from_a_different_store`.
- `apps/backend/tests/test_micro_join.py` — added `_real_corpus_dataset_store()` helper
  (mirrors `get_dataset_store()`'s `index_db_path=` resolution) and pointed both real-corpus
  tests (`test_tc16_...`, `test_tc4_...`) at it instead of a bare
  `DatasetStore(CONFIG.dataset_dir_resolved())`; added `import os`.
- `apps/backend/tests/test_micro_readiness_seal_unaware_caveat.py` — **new file.** 4 tests:
  spec-sentence extractability, frontend-exactly-once-as-shared-constant, character-for-character
  match, and a paraphrase counter-test proving the scan can fail.
- `apps/frontend/app/desk/page.tsx` — added the module-level `REFEREE_EVIDENCE_SEAL_UNAWARE_
  CAVEAT` string constant (single-line, verbatim spec §10.7 text) just above
  `RefereeEvidenceReadinessSection`; added a new `<p data-testid="referee-evidence-strategy-
  seal-unaware-caveat">` element inside the existing `referee-evidence-strategy-block`, right
  after `referee-evidence-strategy-tick-gate` and before `referee-evidence-strategy-basis-
  caveats`, reusing the same `text-[11px] text-slate-500` treatment as the sibling caveat lines.
- `docs/handoffs/goal-rapid-microscope-iter-0-dev.md` — read only (iteration-0 SHA-256 baseline,
  re-verified, not edited).

## Before/After Timing Evidence (TC-1/TC-2/TC-3)

Measured directly by stashing the fix, timing the ORIGINAL fixtures against the real corpus, then
popping the stash and re-timing. All runs used
`cd apps/backend && PYTHONPATH=. .venv/bin/pytest ...` (venv `.venv/bin/pytest`, project's own
test command).

**`test_micro_readiness.py` real-corpus tests (TC-1/TC-2, before the fix — fresh `tmp_path_factory`
every run):**
```
tests/test_micro_readiness.py::test_tc1_real_corpus_distinct_symbol_days_and_datasets
tests/test_micro_readiness.py::test_tc2_real_corpus_session_equivalents_and_tick_gate
real  14m38.763s
```

**Same two tests, after the fix (durable production cache/index):**
```
Run 1: real  0m0.659s
Run 2 (warm): real  0m0.580s
```
Full `test_micro_readiness.py` file (51 tests, including the new TC-10): `2.85s` total.

**`test_micro_join.py` real-corpus tests (TC-16 + J-05 TC-4, before the fix):**
```
tests/test_micro_join.py::test_tc16_real_corpus_joinable_corpus_arithmetic_is_unchanged_by_the_passenger_fixes
tests/test_micro_join.py::test_tc4_real_corpus_join_playbook_signal_is_unaffected_by_the_accessor_re_point
real  27m57.617s
```

**Same two tests, after the fix:**
```
Run 1: real  0m6.903s
Run 2 (warm): real  0m6.537s (pytest-reported: 2 passed in 6.33s)
```
Full `test_micro_join.py` file (50 tests): `7.08s` total.

Both files' warm second runs are far inside TC-1's <60s and TC-2's <30s-combined thresholds — the
"warm" state is the production cache's own steady state (the live backend has already warmed
`.data/dataset_index.db` and `.data/micro_readiness_cache.db` from ordinary operation), so even
the FIRST post-fix run of each file was already fast.

## Tests Run

Command: `cd apps/backend && PYTHONPATH=. .venv/bin/pytest tests/ --durations=25` (project's
`.venv/bin/pytest`; `PYTHONPATH=.` needed in this shell since the package is not installed
editable — `apps/backend/scripts`/CI wrappers set this automatically).

**Result (TC-3): `3480 passed, 8 skipped, 2 warnings in 2093.12s (0:34:53)`, exit code 0** — an
explicit pytest summary line, not a truncated/killed process. Grew from the era-open baseline
(2,691 pass / 8 skip, `docs/handoffs/goal-rapid-microscope-iter-0-dev.md`) with 0 regressions and
the identical skip count. `test_micro_readiness.py` and `test_micro_join.py` do **not** appear
anywhere in the top-25 slowest-durations report — the slowest file by nearly two orders of
magnitude is `test_micro_snapshots.py` (`test_tc12_real_corpus_...`, ~830s each, out of this
iteration's scope), fully satisfying TC-3's "not the largest single contributor" requirement.

Note on evidence-gathering: an earlier run of this exact suite that explicitly passed `-q` on the
command line (redundant with the project's own `addopts = "-q"` in `pyproject.toml`, stacking to
pytest's quiet-level 2) printed all-dots-no-failures and exit code 0 but suppressed pytest's own
final summary phrase — a pytest-9.1.1 quiet-level interaction, not a truncated run (confirmed by
reproducing it on a 4-test file and showing the summary line reappears at quiet-level 1, i.e. the
project's own documented `pytest tests/` invocation without an extra `-q`). Recorded here so a
future reader does not mistake a missing summary LINE for a truncated RUN — the two are
distinguishable by the explicit exit-code echo and the zero-`F` dot stream either way, and the
canonical command above shows the summary cleanly.

Also run and passing (all unmodified — regression checks, not part of the phase spec's new
files):
- `tests/test_micro_no_referee_evidence_guard.py` — 4/4 pass, unmodified (TC-6).
- `tests/test_micro_readiness_seal_unaware_caveat.py` — 4/4 pass (new, TC-4).
- `tests/test_copy_discipline.py` — 30/30 pass (the new caveat sentence and code comments do not
  trip the imperative/prediction/claim lexicon).
- `tests/test_meta_routes.py`, `tests/test_desk_ui_guards.py` — all pass, unmodified (no route or
  numeric-field change was made — the caveat is a static string, not a served number, so
  `_PRICE_ARITHMETIC_FIELDS` needed no addition).
- `apps/frontend`: `npx tsc --noEmit -p tsconfig.json` — clean, zero errors.

**Referee-module SHA-256 re-check (TC-7):** all six `referee_*.py` files re-hash byte-identical to
the iteration-0 listing (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md:75-81`) — verified via
direct `sha256sum`, no code change made to any of them:
```
6dd807b5ab69af033686a395484b1b10515d0f453a79c0943e534a578259786c  referee_adjudicate.py
482f38a11740bc839038290fc2a0e131f649a23f17265cbca0f2aa19fe07e1c5  referee_evidence.py
34917e381e4169aa029f5d0e18228fde75e4d3db5acec516f937e3ef3b371603  referee_null.py
03840c863b1e1f382ad2588d3bb6d8dc0e36a70582c3cb7a716638dabef32d99  referee_registry.py
0cc3a06f7b382c63d544886ec74a47f2414612fc77dd3dac444b00cc35216140  referee_routes.py
fba8816a5d4901ea1eeb7faa71e350538f546a2a3af1f9edb5f6f5aa1ec5271c  referee_stats.py
```
All six match exactly.

## Known Issues

- **TC-5, TC-8, TC-9, TC-11 (browser/golden-replay evidence) are NOT covered by this dev pass** —
  per the plan's own division of labor, target journeys J-01/J-10 need genuine browser-qa (LLM)
  verification this round (the deterministic replay lane structurally cannot execute a target
  journey's own golden in the round that touches it). These are the downstream browser-qa-agent's
  responsibility: `rm -rf apps/frontend/.next` + rebuild (T-9) before any element-scoped
  screenshot capture of `referee-evidence-strategy-seal-unaware-caveat` and the sentinel sections,
  plus replaying `J-01.json`/`J-10.json` and capturing the Scout Ledger "N variants tried"
  make-up shot (TC-11, passenger only, never claimed as this iteration's own scope).
- Manual visual check only via `tsc --noEmit` (types) and reading the rendered JSX — no live
  browser render was performed by this dev pass; the new `<p>` element's actual on-screen
  placement/wrapping should still be confirmed by browser-qa against the real `/desk` page.
- No production backend code was changed — this was purely test-infra (cache reuse) plus one
  frontend copy addition, matching the plan's expectation ("No production backend code changes
  are anticipated").
