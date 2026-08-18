# Iteration State — rapid-microscope

**After iteration:** 9 · **Date:** 2026-08-18 · **Verdict:** CONTINUE

## Journeys

5 passing (J-01..J-05) · 2 partial (J-06 step 3 of 5 done; J-10 traps 19/22, sentinel green) · 3 failing (J-07 J-08 J-09) — 10 total

## Active blockers

- **HUMAN (owner ruling #3, blocks J-06 steps 4-5 — do NOT record/seal real tape):** sealed membership is still recoverable by closing `GET /research/datasets` under the universe's cartesian product and subtracting (audit B2, 5 of 5 recovered WITH the B1 fix in place). Nothing inside `apps/backend/app/research/vault.py` can close it. Options: withhold the whole tranche's symbol/date until fully exposed · add decoy symbol-days · accept in writing that hiding protects DATA not MEMBERSHIP.
- **HUMAN (same sitting):** (a) audit B4 — withholding predicates read `all_rows()` without `verify_chain()`, so a truncated `vault_shard_ledger.jsonl` fails OPEN across 11 consumers (`vault.py:568`); (b) audit B5 — `referee_evidence.py:333` counts withheld shards, a genuine r4-vs-frozen-hash collision; (c) carried since iter-2 — the one-quote-early depletion stamp (`micro_observer.py:636/:657`).
- **DEV (do after blocker 1 sets direction):** audit B3 — `GET /research/desk/micro/recorder/compute` serves each chunk's symbol/date/raw `dataset_id` (`micro_routes.py:475`).
- All of the above are INERT today: no vault ledger exists under `.data`, `seal_shard` has zero production callers, `withheld_dataset_ids` empty on both stores.

## Last 2 verdicts

- iter 9: CONTINUE — vault step 3 genuinely landed (opaque pre-exposure serving + TR-2/4/12/20 proven by the evaluator directly); suite 3,166/0 failures re-run after every edit; but §7.3's headline guarantee is not achieved as built, so J-06 stops at step 3.
- iter 8: ESCALATE — recorder step 2 landed, but the engine demoted full→lean on budget so the auditor never ran on a high-risk diff.

## Do not redo

- **J-06 steps 1-3 are DONE**: Card-5.1 preservation fields, `tick_recorder.py`, and `vault.py` (universe registration, HMAC seal, one-way `sealed→assigned→exposed`, surrogate ids, salted commitment). Traps TR-2/4/12/20 green (`tests/test_vault.py`, 42 tests).
- **Spec revisions r3 and r4 are SETTLED owner rulings** (`docs/rapid-validation-spec.md` §7.5; rationale in `state/assumptions.md`). Do not re-litigate; a change is a further named revision.
- **CLOSED, verified in code by the evaluator:** the iter-6 exposure-registry sealed filter (`walkforward.py:1267` passes `vault.currently_sealed_dataset_ids`) and the iter-8 §2.6 rule-text + verification-note gap (`tick_recorder.py:484-485`, checksum-excluded).
- **Frozen foundations re-verified iter-9:** fingerprint `08e471b10130e1e2`; six `referee_*.py` hashes match iteration 0; `EXPECTED_TOOLS` still 22; real `.data/datasets` = `f7bbcf28…`, 18 files.
- **Golden replay scripts now exist** for J-01..J-06 and J-10 at `runs/goal-session-rapid-microscope/journey-scripts/` — J-02..J-05 no longer need an LLM lane, so stop letting them be trimmed first.
- **Next target is J-07 (`micro_graduation.py`, absent on disk)** — fixture-only, needs no owner ruling, next in dependency order. Not J-06 step 4.
