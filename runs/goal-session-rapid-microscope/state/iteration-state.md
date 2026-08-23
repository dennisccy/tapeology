# Iteration State — rapid-microscope

**After iteration:** 25 · **Date:** 2026-08-23 · **Verdict:** ESCALATE

## Journeys

**10 passing (J-01..J-10)** · 0 partial/failing/unknown. J-06 closed (fresh Vault photograph +
expose-flip probe). All iter-25-stamped except J-07 (iter-24; no golden by design, diff-durable).

## Active blockers

- **Era NOT certifiable while 8 minor anti-goal items stay open** (0 critical). Verbatim text + evidence: `state/journey-history.json` → `anti_goal_violations` idx 17, 21, 29, 35, 37, 39, 44, 45.
- **Golden coverage (dev).** Replay lane drove 8/9 — it is scoped to Required-still-passing, which
  EXCLUDES the target journey, so `J-06.json`'s new Vault assertion has only run dev-locally. Drive
  all nine in ONE recorded run (3rd round with this finding).
- **Desk readiness ~22s on the real store (dev).** `micro_routes.py:108` → `micro_join.py:639-643`,
  no cache. Fix = durable per-dataset touch count keyed on (dataset checksum, resolver map key),
  publishing ONLY a resolved answer, never "none". The one item the operator actually feels.
- **Duplicated pilot-selector frozensets (dev).** `micro_routes.py:284-287` restates `scout.py:1684-1689`'s `_PILOT_GRID_SELECTORS`. One line: derive, don't restate.
- **Referee disclosure + guard never built (dev).** Owner ruled r5 pt 7 (KEEP THE FREEZE, DISCLOSE) 2026-08-18; freeze holds (6/6 hashes re-checked iter-25), the disclosure does not exist.
- **Owner-owned:** chain-ledger identity commitment — its "minor" grounds EXPIRED at iter-23 (store
  now holds 21 sealed shards; `micro_chain_ledger.py:184-190` still verifies a DELETED ledger as
  clean; r8 forbids designing it ad hoc). Passenger: `desk_micro_readiness` MCP times out on the
  real store (10s vs ~13.5s); money floor; the ~150-symbol-day gate reads unmet at 80 (passing).

## Last 2 verdicts

- iter 25: ESCALATE — J-06 green; refused GOAL_ACHIEVED on 8 open minor items, one of which lost
  the factual premise its severity rested on.
- iter 24: CONTINUE — seal-time leak closed, but the round shipped a wrong-date Vault cell, fixed
  and never re-photographed → J-06 partial.

## Do not redo

- **J-06 is DONE** (`reports/qa/goal-rapid-microscope-iter-25-evidence/UT-J-06-result.png`). Do not re-shoot.
- **Keep the iter-25 sealed fixture:** `seed_micro_vault_iter25_sealed_fixture.py` + launcher wire-up + `test_vault.py` TC-1/TC-8 (proven non-vacuous).
- **`J-08.json` step 3 / `J-10.json` step 12 assert `"variants tried"`** (grep-unique, order-independent) — do not revert.
- **Do NOT re-record tape, expose/assign any sealed shard, or run J-09's studies on the real corpus;** `recording-runs.json` stays byte-untouched.
- **Readiness serving `80` (whole pool), not `21`, is CORRECT** (r5 anti-subtraction); **J-07 cannot have a golden** (iter-19).
- **`page.tsx:6807` `formatDayMarker` + `vault.py:1486-1497` coarsening are correct and pinned;** `assigned_at`/`exposed_at` keep the instant formatter (their "20:00 ET" is a real midnight-UTC fixture value, verified iter-25).
