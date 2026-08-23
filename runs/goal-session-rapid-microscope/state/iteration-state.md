# Iteration State — rapid-microscope

**After iteration:** 24 · **Date:** 2026-08-23 · **Verdict:** CONTINUE

## Journeys

9 passing (J-01..J-05, J-07..J-10) · 1 partial (J-06) · 0 failing · 0 unknown — 10 total. J-07 + J-09 now carry FRESH iter-24 stamps, closing last round's two `DEFERRED-BUDGET` skips.

## Active blockers

- **J-06 needs ONE photograph (dev/QA).** Product fixed, picture missing. Restart `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` + frontend and re-shoot UT-03: the Vault "Sealed at" cell must read a bare date (e.g. `2026-05-01`), no clock time. Pre-fix proof: `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-03-fail.png`.
- **UT-05 (r5 "sealed rows stay opaque") unrunnable for 3 rounds (dev).** The rig's only shard is already `exposed`. Add one `seal_shard` call to the iter-18 seeder; give `journey-scripts/J-06.json` a Vault assertion (today it only asserts "No integrity errors.").
- **Replay lane drove 7 of 9 goldens (dev).** `J-06.json` + new `J-09.json` never ran through the harness; DoD "AND via the stored golden" rests on a dev-local claim. Run all nine.
- **`J-08.json` step 3 / `J-10.json` step 12 both assert "Ledger chain verification:"** — appears twice in `page.tsx` (`:6282`, `:6518`). Order-dependent; pick a section-unique string.
- Passenger, unchanged: `desk_micro_readiness` MCP tool times out on the real store (10s vs ~13.5s).
- Owner-owned, blocking no journey: sealed judge's money floor (`micro_sealed_evaluation.py:316`); the ~150-symbol-day gate reads unmet at 80 — a passing state.

## Last 2 verdicts

- iter 24: CONTINUE — seal-time leak CLOSED (both halves re-proved by the evaluator), but the round introduced a wrong-date Vault display; auditor fixed it, never re-photographed → J-06 partial.
- iter 23: ESCALATE — J-06 green on real-store evidence; the clock deferred J-07/J-09.

## Do not redo

- **Sealing-time leak CLOSED.** `vault.py:1486-1497` coarsens the SERVED `sealed_at` at one point (21 shards → one `2026-08-21` bucket); widened `stage_tr2()` keys on SERVED buckets, proven non-vacuous. Do NOT edit `reports/j06-tranche/recording-runs.json` — it stays byte-untouched.
- **Vault "Sealed at" formatter FIXED** — `page.tsx:6807` uses `formatDayMarker`, pinned by `tests/test_desk_vault_sealed_at_day_marker_guard.py`; `assigned_at`/`exposed_at` keep the instant formatter. Do not revert either.
- **Do NOT re-record tape** (80/80 on disk), **do NOT expose/assign any sealed shard**, **do NOT run J-09's studies on the real corpus** (irreversible; breaks J-10's golden).
- **Readiness serving `80` (whole pool), not `21`, is CORRECT** (r5 anti-subtraction) — do not "fix". **J-07 cannot have a golden** (iter-19) — it stays on the LLM lane.
