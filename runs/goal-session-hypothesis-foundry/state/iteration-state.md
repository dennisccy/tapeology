# Iteration State — hypothesis-foundry

**After iteration:** 4 · **Date:** 2026-08-27 · **Verdict:** ESCALATE

## Journeys

3 passing (J-01 J-03 J-04) · 2 partial (J-02 J-05) · 3 failing (J-06 J-07 J-08) — 8 total

## Active blockers

- J-02 (dev): SourcesCompilerSubsection (`page.tsx`) omits `operative_formula_refs`,
  `superseded_fields`, `aliases_lineage_ids` that step 3 requires ON SCREEN; only 1 of the 2-variant
  family's records is surfaced. Step 5b needs J-06's committed source-registry-audit.md.
- J-05 (dev): step 3's Scout-kill → `foundry_state` mapping has no on-screen home (no per-row state in
  the payload); step 4's best-of-N line unrendered; `outcome_types_present` is a hard-coded label
  dict, not read off each row (`foundry_hermetic_summary.py:303-318`).
- ANTI-GOAL MINOR, unresolved/BLOCKING (dev): production code mutates the frozen `scout._two_sided_p`
  in the serving process (`foundry_hermetic_summary.py:75-82`,`:183-188`). total=1/blocking=1/crit=0.
- Process (human): every iteration breaches the 3600s budget (iter-4 = 7685s), so the depth arbiter
  demotes spec `Depth: full` to lean unless the PRIOR verdict was ESCALATE — raise the budget, or
  accept that only ESCALATE forces full. Session `--max-iter` 60→80 still open.

## Last 2 verdicts

- iter 4: ESCALATE — read surface shipped, J-03/J-04 now passing; the lean lane (no auditor) left 3
  "claims a proof it does not show" gaps + 1 minor anti-goal; next stage is the irreversible freeze.
- iter 3: CONTINUE — hermetic oracle suite proven; nothing operator-visible, so J-05 capped partial.

## Do not redo

- Binding Execution Order steps 1-5 DONE: era transition + baseline (J-01), compiler/registry, generic
  interpreter, family/ledger/freeze/runner machinery, hermetic oracles, and the `/desk` → Hypothesis
  Foundry read surface (4 subsections, all banner-labelled fixture). Next stage = J-06 (real registry
  audit + manifest gen, zero outcome reads); J-07/J-08 illegal until J-06's freeze commit.
- Repairs CLOSED: `lint_alternatives` sibling lint; crash-path `manifest_hash` check
  (`foundry_runner.py:114-121`); QA report cites J-01's replay file, not the pytest run.
- `GET /research/desk/micro/foundry` is GET-never-computes: 4 views built once at import
  (`micro_routes.py:764-800`), served verbatim; 3 route tests prove it. Do not rework. Evaluator
  re-verified: immutability hash `0892112d…`, interpreter decisions, freeze table, composite-epoch
  mapping; 75 Foundry tests pass; store-scope CLEAN; coherence PASS.
