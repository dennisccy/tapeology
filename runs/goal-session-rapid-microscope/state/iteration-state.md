# Iteration State — rapid-microscope

**After iteration:** 13 · **Date:** 2026-08-19 · **Verdict:** ESCALATE

## Journeys
6 passing (J-01..J-05, J-07) · 2 partial (J-06 steps 3/5, J-10 traps 24/29) · 2 failing (J-08, J-09) — 10 total

## Active blockers
- **Vault identity commitment — owner-DEFERRED by r8, MUST close before J-06 step 4.** Deleting the
  ledger AND its tail anchor together (two plain `rm`s, no forgery) makes `verify_chain()` report
  `ok: True` over an empty ledger and every sealed shard re-sealable — reproduced end to end by BOTH the
  auditor (B2) and this evaluator (P4), at `micro_chain_ledger.py:186-189` (`_verify_tail`). Unreachable
  today (0 universes, 0 sealed shards, no `micro_vault`). Needs a NAMED spec revision (ordered row
  identities / canonical checkpoint / Merkle manifest); r8 forbids designing it ad hoc. Second argument:
  post-B1 an anchor-lag crash strands the vault even for an honest operator (P3). Nothing else waits on
  the owner — r6/r7/r8 settled every ruling.
- Evidence debt (passengers, never their own round): replay lane wrote NO `J-0{1..5}-verify.png` though
  the results table cites them; J-07 cut for time (`DEFERRED-BUDGET`), which blocks GOAL_ACHIEVED until
  re-verified; `state/golden-gaps` auto-deleted a 3rd time (J-07 correctly has no golden).

## Last 2 verdicts
- iter 13: ESCALATE — recovery hole genuinely closed (evaluator probes P1/P2), but J-08 next builds the
  opaque-pool panels and only an ESCALATE line binds the arbiter to keep the auditor, which has caught
  this fault class 5 times after review+QA both passed.
- iter 12: ESCALATE — arbiter downgraded a prose request for full depth; no auditor ran on
  safety-critical vault machinery and the evaluator found the recovery hole itself.

## Do not redo
- **`recover_shard_ledger` is DONE and hardened** (r8 halt-only, 5 conjuncts incl. the audit's
  `len(candidate_rows) >= preserved_row_count`). Never reintroduce a graded/union-marking branch; never
  resurrect `STATE_EXPOSURE_UNKNOWN` (deleted, zero dangling). Row-count equality is never identity
  evidence — settled by r8. `seal_shard`/`assign_shard`/`expose_shard` gate their OWN shard ledger only
  — documented, pinned by TC-7, paired-deferred with the missing universe-ledger recovery primitive.
- **Frozen rails re-verified by the evaluator:** fingerprint `08e471b10130e1e2`, six `referee_*.py` =
  iteration-0 hashes, `EXPECTED_TOOLS` 22, zero frontend diffs, zero `Config` fields,
  `micro_chain_ledger.py` byte-untouched, real `.data` = 18 datasets / no `micro_vault`. **Suite
  baseline 3228 / 3220 passed / 8 skipped / 0 failed** (re-run by the evaluator); the handoff's
  3227/3219 predates the auditor's +1 test — do not quote it.
- **J-06 steps 4-5 stay shut** (no vendor call, no real-tape recording) until the blocker above closes.
