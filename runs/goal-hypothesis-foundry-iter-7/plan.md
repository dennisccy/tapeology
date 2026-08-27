# goal-hypothesis-foundry-iter-7 Execution Plan

## What to Build

- **Retire the coherence-auditor's `COHERENCE-FAIL`** on `exhaust_progress.frozen_ready_total`
  (`runs/goal-session-hypothesis-foundry/iter-6/coherence.md`, Blocking violation 1): the value is
  currently computed twice — once at `apps/backend/app/research/micro_routes.py:901`
  (`sum(f["variant_count"] for f in _EPOCH_MANIFEST_VIEW.get("families", []))`, the canonical
  serving path) and once at `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225`
  (`sum(len(fm.get("variants", [])) for fm in manifest.get("families", []))`, a different field of
  the same file). The second file is one of the 59 entries in
  `docs/hypothesis-foundry/freeze-set.json`, sealed since `2026-08-27T06:55:51Z` — it may NOT be
  edited. The only legal fix (per `iter-6/eval.md`'s own explicit fallback) is: consolidate
  ownership into a single named function in the non-sealed `micro_routes.py`, then add a permanent
  equivalence-pinning test proving the sealed CLI's own (transcribed, unedited) formula agrees with
  it on the real, frozen manifest.
- Extract the inline `_FOUNDRY_FROZEN_READY_TOTAL` expression at `micro_routes.py:901` into one
  clearly named, documented function (e.g. `compute_frozen_ready_total(epoch_manifest_view: dict) ->
  int`) that becomes the sole owner of this concept. Call it once at module import time exactly as
  today (`_FOUNDRY_FROZEN_READY_TOTAL = compute_frozen_ready_total(_EPOCH_MANIFEST_VIEW)`) —
  preserves the existing "computed once, served verbatim" / GET-never-computes convention already
  documented at that call site. Served value must stay `0` (unchanged) against the real
  `families: []` manifest.
- Add ONE new equivalence-pinning test (extend `test_run_hypothesis_foundry_real_exhaust.py` and/or
  `test_foundry_route.py`) that:
  - Loads the real committed `docs/hypothesis-foundry/epoch-manifest.json` directly via `json` (not
    via importing the sealed CLI module for this specific check).
  - Transcribes the sealed formula **literally, unedited**, exactly as it reads at
    `run_hypothesis_foundry_real_exhaust.py:225` today
    (`sum(len(fm.get("variants", [])) for fm in manifest.get("families", []))`), with a comment
    citing that exact file:line so a future reader can visually diff it against the frozen source.
    Do not import, call, or refactor `run_hypothesis_foundry_real_exhaust.py` to obtain this half of
    the comparison — the spec is explicit that file must not be touched or refactored into.
  - Calls the new `micro_routes.compute_frozen_ready_total(...)` (or reads the real
    `_EPOCH_MANIFEST_VIEW`/`read_epoch_manifest_view()`) against the same real manifest data.
  - Asserts both integers are equal. This is vacuously `0 == 0` today (`families: []`) — that is
    expected and matches the spec's own acknowledgment; the value of the test is pinning agreement
    permanently for this frozen, unchangeable manifest, not proving a non-trivial case.
- **Do not touch, under any circumstance:** any of the 59 `freeze-set.json` entries (including
  `foundry_runner.py`, `foundry_ledger.py`, `foundry_family.py`, and
  `run_hypothesis_foundry_real_exhaust.py` itself), `epoch_id`, `source-registry.json`, or
  `epoch-manifest.json` content. Verify with `git diff` / the existing store-scope guard after the
  change that zero sealed files were modified.
- If a fresh coherence-auditor pass still reports `DUPLICATE-COMPUTATION` for this row after the
  above, do NOT force a pass by touching a sealed file — record the finding plainly in the dev
  handoff and recommend an owner ruling (per `iter-6/eval.md`'s own fallback instruction), leaving
  the verdict as-is.
- `runs/goal-session-hypothesis-foundry/state/blueprint.md` was already updated by the
  goal-decomposer this iteration (the `exhaust_progress.frozen_ready_total` row is already split out
  at lines 141-142, correctly describing the target end-state: sole owner = one named helper in
  `micro_routes.py`). No blueprint edit is expected from the developer — just verify after the change
  that the row still matches reality (no further drift to record).
- **No production behavior changes anywhere else.** This is a pure internal consolidation behind an
  already-shipped, unchanged read surface (`GET /research/desk/micro/foundry`, `exhaust_progress`
  key) — no new endpoint, no new UI, no new user-facing capability.

## Agents Required

- backend-data: yes -- extract the sole-owner helper function in `micro_routes.py`, add the
  equivalence-pinning test, run the full backend suite, confirm zero sealed-file edits, write the
  dev handoff per Definition of Done (including the coherence-auditor re-run outcome).
- frontend-ux: no -- zero frontend files touched; the served value and rendered UI text are byte-
  identical to iter-6 (`/desk` → Hypothesis Foundry → Runner/Checkpoint already renders
  `frozen_ready_total` verbatim and needs no edit).

## Frontend Present
no

## Files to Create/Modify

- `apps/backend/app/research/micro_routes.py` -- extract the inline `frozen_ready_total` computation
  (currently ~line 901) into one named function; call it once at module import time as today; served
  value unchanged (`0`).
- `apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py` and/or
  `apps/backend/tests/test_foundry_route.py` -- add the new equivalence-pinning test described above.
  Do not modify the existing assertions at `test_foundry_route.py:223` (`progress["frozen_ready_total"]
  == 0`) or `test_run_hypothesis_foundry_real_exhaust.py:136`/`:332` (`result["frozen_ready_total"] ==
  0`/`== 1`) — they must still pass unchanged (TC-6).
- `docs/handoffs/goal-hypothesis-foundry-iter-7-dev.md` -- new dev handoff (required by Definition of
  Done): states plainly whether the fresh coherence-auditor pass PASSED, or (per the TC-5 fallback)
  recommends an owner ruling; lists the two carried OWNER-only anti-goal findings ("Persistence stays
  scoped," "No second real generation epoch") as still open/unresolved, not silently dropped; states
  test suite results.
- No file under `docs/hypothesis-foundry/` may change content this iteration
  (`freeze-set.json`, `freeze-record.json`, `epoch-manifest.json`, `source-registry.json`,
  `epoch_id`). No file in the 59-entry freeze-set may change at all.
- No `apps/frontend/**` file should need to change.

## Key Test Scenarios

- TC-1: `GET /research/desk/micro/foundry` against the real `epoch-manifest.json` (`families: []`)
  and the refactored `micro_routes.py` still returns `exhaust_progress.frozen_ready_total == 0`,
  unchanged from iter-6.
- TC-2: the new equivalence-pinning test — the transcribed sealed formula (from
  `run_hypothesis_foundry_real_exhaust.py:225`, unedited/untouched) and the new canonical helper
  function both evaluate the real `epoch-manifest.json` to the identical integer; test passes.
- TC-3: after the diff, all 59 `docs/hypothesis-foundry/freeze-set.json` entries remain byte-identical
  to their pinned sha256 hashes (store-scope/freeze-set guard stays CLEAN — zero sealed-file edits).
- TC-4 (post-dev, QA/coherence step): a fresh coherence-auditor pass over this iteration's diff
  reports no `DUPLICATE-COMPUTATION` finding for `exhaust_progress.frozen_ready_total`; if it still
  does, the dev handoff explicitly records the fallback recommendation to request an owner ruling,
  and no sealed file was edited to force a pass.
- TC-5 (post-dev, QA step): J-07 replays passing via browser-qa/deterministic replay, reading proof
  from the `-evidence/` lane (not from a QA report's own citation list — iter-6's lesson: a report
  cited one byte-identical blank PNG four times as "proof").
- TC-6: required-still-passing journeys J-01..J-06 replay green (full regression; the refactor
  touches the one shared serving module behind every Foundry Data-Contract row).
- TC-7: full backend suite passes with the same pre-existing assertions unchanged
  (`test_foundry_route.py:223`, `test_run_hypothesis_foundry_real_exhaust.py:136,332`), plus the one
  new test added; no regressions, no skips/xfails introduced.
- TC-8 (post-dev, evaluator step): the anti-goal disposition ledger still shows the two carried
  OWNER-only findings ("Persistence stays scoped," "No second real generation epoch") as open/
  unresolved — not silently removed — and no new anti-goal finding is recorded beyond the TC-5/TC-4
  coherence fallback disposition if it applies.
