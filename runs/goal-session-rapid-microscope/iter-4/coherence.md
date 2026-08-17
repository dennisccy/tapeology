# Iteration 4 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-4
**Date:** 2026-08-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Scout trials, kills, denominators, screens | OK | Served exactly at the pre-registered endpoints (`GET /research/desk/micro/scout`, `POST/GET/POST-cancel .../scout/compute`, `GET .../scout/runs`) — `apps/backend/app/research/micro_routes.py:334-402`, wired into the existing router (no new router file, no new prefix). Sole computation lives in the two blueprint-named owner modules: `apps/backend/app/research/scout_ledger.py` (chain storage/verification) + `apps/backend/app/research/scout.py` (screen). `grep -rl scout apps/backend/app apps/backend/tests` returns only these two modules, `micro_routes.py` (the wiring), their two test files, and two pre-existing, untouched docstring cross-references in `micro_features.py:12` / `micro_snapshots.py:329` (neither file appears in `git diff <snapshot-sha> --stat` for this iteration). No competing implementation anywhere. |
| Corpus readiness truth / joinable-corpus counts (`band_touch_count`, `playbook_integrity_errors` passenger fixes) | OK | Both fixes stay inside the already-registered owner `apps/backend/app/research/micro_join.py:192-257` and the already-registered endpoint `GET /research/desk/micro/readiness` (via `micro_readiness.py:377-292`, unchanged call boundary). No second endpoint, no second computation. `apps/backend/tests/test_micro_join.py`'s TC-16 (`:541-558`) independently re-verifies the real-corpus enumerated arithmetic (`playbook_signal_count == 2`, `by_setup_id == {"range_trade": 2}`) is byte-unchanged by either fix — only the honesty/typing of the response shape changed. |
| Outcome/join primitives (`outcome_rows_at_position`, `outcome_row_at_single_horizon`, rewritten `_shares_horizon_row`/`_clock_horizon_row`) | OK — not a duplicate | New/rewritten code lives inside the SAME canonical owner (`micro_join.py:114-179, 229-248`), calls the SAME core (`_outcome_rows_after`/`_build_outcome`) the pre-existing `outcome_rows_after_trigger` already used, and is proven byte-identical by dedicated tests: `test_outcome_rows_at_position_matches_outcome_rows_after_trigger_exactly`, `test_outcome_row_at_single_horizon_matches_the_corresponding_entry_of_the_full_closed_set`, `test_shares_and_clock_horizon_rows_are_unchanged_by_the_index_iteration_rewrite` (`apps/backend/tests/test_micro_join.py:568-649`). A perf-motivated second entry point into one still-single implementation, not a second computation of the value. |
| Scout's statistical screen (`compute_p_screen`, block-permutation null, `scout_stream`) | OK — genuinely new value, already registered | This IS the newly-built "screens" half of the Scout Ledger row above, not a synonym of anything pre-existing. Verified distinct from the Referee's own statistics (`referee_stats.py`, a different era/domain, untouched by this diff — confirmed via `git diff --stat` showing no `referee_*.py` file changed and TC-17 re-checking all 6 referee hashes). `scout.py:1-59` docstring discloses the "mirrored, not imported" interpretation call for the stream-recipe technique, the same class of call `micro_join.py` already logs for a sibling mirror — not a duplicate of a registered value. |
| `chain_verification` (new field on `GET /research/desk/micro/scout`) | OK — sub-field of the registered row, not a new value | Computed by `ScoutLedger.verify_chain()` (`scout_ledger.py:290-322`), the same already-registered owner/endpoint pair as the rest of the Scout Ledger row; it is the ledger's own tamper-honesty guarantee ("kills … denominators"), not an independently computed concept. |
| Any UI-side fetch/recompute of the above | OK — none exists | `git diff <snapshot-sha> --stat -- apps/frontend` is empty; zero `.tsx`/`.ts` files changed. `reports/phase-goal-rapid-microscope-iter-4-user-visible-changes.md` and `-ui-surface-map.md` both independently confirm zero UI surface this iteration. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/desk/micro/scout*` (new backend routes) | OK — no UI surface to place this iteration | `Frontend Present: no` (iter spec metadata); no page/route was added to the app shell. The blueprint's IA table already pre-registers J-04's canonical home ("Scout + candidate ledger (J-04) → `/desk` → Scout Ledger → Desk") and explicitly defers rendering to J-08 — `blueprint.md:38-42`. This is the identical "served ahead of UI wiring" pattern the coherence audit already approved at iter-2 (J-02's snapshot endpoints) and re-confirmed at iter-3 (J-03's `joinable_corpus`), per `blueprint.md`'s own iter-3 footnote (`blueprint.md:77-80`). No nav-skeleton edit was made or needed. |
| `desk_scout` MCP tool / `EXPECTED_TOOLS` bump | OK — correctly absent | Explicitly OUT OF SCOPE per the iter spec ("Rendering the Scout Ledger section on /desk, the desk_scout MCP tool, or the EXPECTED_TOOLS bump to 26 — J-08"). Verified absent: `grep -rn desk_scout apps/backend/` returns nothing; `EXPECTED_TOOLS` appears only in the untouched `test_mcp_server.py`; no `*mcp*` files appear in this iteration's diff. |

No new page, sidebar entry, or parallel shell was introduced. Nothing to check for click-depth this iteration — there is nothing new for a user to reach.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The independent post-QA auditor (`docs/handoffs/goal-rapid-microscope-iter-4-audit.md`) found and fixed four IMPORTANT correctness/integrity bugs in the Scout ledger this iteration (unverified tamper-serving, undetectable tail truncation, an evaluations-vs-variants denominator inflation bug, an anti-conservative null on shares/clock horizons — since refused via `ScoutUnsupportedHorizonError`). All four fixes stayed strictly inside the single registered owner module/endpoint pair — none introduced a second computation path, a second endpoint, or a UI-side workaround — so none of them are coherence violations under this gate's charter. Noted here only for continuity; functional correctness is the auditor's domain, not this gate's.
- The same audit also flagged that TC-20's browser regression pass (J-01/J-02/J-03 re-verify + J-10's full kept-product sentinel) was recorded as a blanket SKIP rather than executed, on an iteration whose regression set was deliberately widened after iteration-3's ESCALATE. This is a regression-evidence gap for the goal-evaluator to weigh, not a structural coherence issue (no scattered navigation or duplicate value resulted) — flagged here for visibility only, outside this gate's own pass/fail authority.
- `playbook_integrity_errors` and `chain_verification` are new response sub-fields not individually spelled out as their own Data Contract rows in `blueprint.md`. Judged non-issues (see table above: both are honesty/integrity refinements of an already-registered composite value, same owner, same endpoint, matching the iter spec's own "Data-contract additions: None" claim, which this audit independently verified as accurate) rather than unregistered new values — recorded here so the reasoning is auditable if a future iteration disagrees.
