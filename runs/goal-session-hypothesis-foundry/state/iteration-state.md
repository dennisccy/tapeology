# Iteration State — hypothesis-foundry

**After iteration:** 5 · **Date:** 2026-08-27 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01..J-06) · 2 failing (J-07 J-08) — 8 total. Execution-Order step 7 CROSSED: the real epoch is frozen in commit `dff64eaa` (ancestor of HEAD), so J-07 is the next legal target. The epoch compiled ZERO candidates (all 11 sources blocked/excluded/aliased) — goal.md's own valid ending 1.

## Active blockers

- **OWNER** — ratify or reject the discarded first real epoch (`ded18b8b…`→`ed40dbc2…`; disclosed in `reports/hypothesis-foundry/source-registry-audit.md:9-40`, auditor B5). Recorded as a MINOR unresolved anti-goal: total=2 / resolved=1 / blocking=1 / non-blocking=0 / critical=0. Also owner-owned: approving any amendment to the already-committed frozen artefacts below.
- **DEV (B1)** — `docs/hypothesis-foundry/freeze-set.json` keys all 55 entries by absolute machine-local path, so the §8.5 lock is only verifiable in this one checkout.
- **DEV (B2)** — `freeze_commit` `55c42ee3` lacks the science bytes the freeze set pins (`foundry_compiler.py` was still uncommitted at generation time).
- **DEV (B7 + evaluator)** — freeze set omits the 3 tracked Foundry JSONs + the generation CLI §8.4 names; `freeze-record.json` omits §8.4's "era-open evidence-class contract" field.
- **DEV** — `_load_existing_manifest_store` (`generate_hypothesis_foundry_real_epoch.py:858-875`) returns `{}` when the manifest file is absent, so deleting it bypasses §8.3's refusal silently.
- **PROCESS** — sixth consecutive budget breach (iter-5 ≈ 3h07m on 1h); `--max-iter` 60→80 pending.

## Last 2 verdicts

- iter 5: ESCALATE — epoch frozen, 3 journeys green; iter-6 writes the §8.5 one-way lock with three open freeze-integrity findings, and a CONTINUE would have been demoted to lean.
- iter 4: ESCALATE — read surface landed (J-03/J-04 green) but the lean pass missed three "claims a proof it does not show" gaps plus a frozen-function mutation in the serving process.

## Do not redo

- Real epoch generated, fresh-context audited, committed (`dff64eaa`; 5 tracked files). **Never regenerate** — §8.1 permits no second epoch; repairs must not re-mint an `epoch_id`.
- Zero compiled candidates is settled and independently audited — never rescue/re-threshold/re-partition to raise yield.
- J-02 fixed: Sources/Compiler shows all 3 additive fields, both alias siblings (8 rows), audit ref.
- J-05 fixed: `kill_type_mapping` + `best_of_n_disclosure` render; `outcome_types_present` row-derived (`foundry_hermetic_summary.py:301-317`).
- `scout._two_sided_p` anti-goal CLOSED — never re-patch a frozen module for a `killed_fragile` row.
- `tests/test_foundry_real_epoch_artifacts.py` (14 read-only guards) exists — extend, don't rewrite.
