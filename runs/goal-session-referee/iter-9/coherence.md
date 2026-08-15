# Iteration 9 — Coherence Audit

**Iteration:** goal-referee-iter-9
**Date:** 2026-08-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

<!-- COHERENCE-WARN: only advisory issues; does NOT block GOAL_ACHIEVED -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| **Promotion authorization verdict** (owner `referee_adjudicate.py`'s `authorize_promotion`; endpoint unchanged — surfaced inside `pnl_scan._promote`/the scan report's `promotion` block) — wired for real this iteration | OK | `pnl_scan.py:150` imports `authorize_promotion`/`REFEREE_GATE_VERSION`/`referee_parameters_hash` from `referee_adjudicate.py` verbatim; `pnl_scan.py:349` (`_promote`) calls the imported function directly — no reimplementation of the six-refusal-class decision logic in `pnl_scan.py`. `authorize_promotion`'s own body (unchanged this iteration — not in the diff's touched-line ranges) still lives in exactly one place, `referee_adjudicate.py:1723-1852`. `pnl_scan.py:287` (`_dataset_pin`) only narrows an existing `DatasetStore` metadata dict to `{id, checksum, split}` for the equality check — reformatting for comparison, not recomputing a value. |
| Same row — `CertificateStore`'s storage directory, read by the CLI sweep (`pnl_scan.py:594`) | OK | `resolve_referee_registry_dir(config.desk_universe_dir_resolved())` is called identically at `pnl_scan.py:594`, `referee_routes.py:239/243/247/251` (all four store dependencies), `referee_adjudicate.py:1846`, and `referee_registry.py:1289` — verified by grep across the whole backend: every call site feeds the same `desk_universe_dir_resolved()` value into the same resolver. No second, independently-resolved certificate location exists. |
| **Certificate record** — gains its first real writer this iteration | OK | `referee_adjudicate.py:1055` (`_mint_strategy_certificate`) is the only place `CertificateStore.record()` is called from production code (`referee_adjudicate.py:1113`); reachable only from `run_evaluation_and_record`'s fresh-checkpoint branch (never the dedup/reused path — confirmed both by reading the code and by `test_tc12_a_strategy_checkpoint_mints_exactly_one_certificate_through_the_real_rail`'s second-call dedup assertion). `pnl_scan.py` never constructs a certificate itself — it only reads via `authorize_promotion`. |
| **`shortlist_response()`** gains `family_id`/`family_q` — closes iter-8's coherence WARN F1 (the unowned `apps/frontend/app/desk/page.tsx` literal) | OK — verified, not just asserted | `referee_registry.py:167` (`REFEREE_DEFAULT_Q = 0.10`) and `:172` (`REFEREE_STARTER_FAMILY_ID`) are the new backend-owned constants; `referee_registry.py:1230-1231` serves them from `shortlist_response()`. The old frontend literals are deleted (`apps/frontend/app/desk/page.tsx`'s former `REFEREE_STARTER_FAMILY_ID`/`REFEREE_STARTER_FAMILY_Q` consts, confirmed removed from the diff, not merely superseded) and the POST body now reads `apps/frontend/app/desk/page.tsx:7772-7773` (`family_id: shortlist.family_id`, `family_q: shortlist.family_q`) from the fetched response. `apps/frontend/lib/types.ts:2164-2165` types the two new response fields. Grepped the whole frontend for `family_q`/`family_id`: the only live usages are this POST body and the type declaration — the value is still never *rendered*, so no display-duplication risk either. |
| `REFEREE_STARTER_FAMILY_SHORTLIST` gains S-6 (`range_trade:short at_wall`, estimand B) | OK | New tuple entry only (`referee_registry.py`, inside the existing `REFEREE_STARTER_FAMILY_SHORTLIST` constant) — reuses `_starter_context_readiness` verbatim, no new pooling function. Rendered by the pre-existing generic `shortlist.candidates.map((candidate) => {...})` at `apps/frontend/app/desk/page.tsx:4756` — zero new JSX branch, confirmed by reading the render call site. |
| Registry `accrual`/`discovery` blocks — context-predicate correctness fix (no new field) | OK | New shared helper `_signal_matches_hypothesis_cell` (`referee_registry.py:800-825`) is called from both `_hypothesis_accrual` (`referee_registry.py:856`) and `_hypothesis_discovery` (`:909`) — one implementation, not two independently-drifting walks — and reuses the same `resolve_occurrence_backing_bucket` primitive `_starter_context_readiness` already calls for the shortlist's own live readiness. `test_tc15_a_context_hypothesis_accrual_and_discovery_agree_with_the_shortlist_readiness` (`test_referee_registry.py`) directly cross-checks the registry-row numbers against the shortlist row's own numbers for the identical `(setup_id, side, context_predicate)` cell — exactly the "numbers must match" property this fix exists to establish. |
| Evaluation record's `evidence_family` enum gains a real `"strategy"` branch | OK | `referee_adjudicate.py:521` (`_pool_strategy_trades`) reuses `referee_evidence.strategy_observations()` (pre-existing function, confirmed already defined in `referee_evidence.py` before this iteration — that file is not among the 10 changed files) rather than re-joining trades to datasets a second way, and feeds the SAME downstream steps (`coverage`, permutation test, both bootstrap CIs, BH fold, snapshot) `run_evaluation_and_record` already used for the playbook estimands. `referee_stats.py` is untouched by this diff (confirmed via `git diff --stat`) — the "reuse permutation/BH primitives with zero diff to that module" claim holds. |
| `referee_parameters()`/`referee_parameters_hash()` (new spec-Sec1 aggregator) | OK | `referee_adjudicate.py:223`/`:237` combine four ALREADY-existing per-module `_parameters()` stubs (`referee_stats_parameters`, `null_tod_spec_parameters`, `null_context_spec_parameters`, `test_perm_spec_parameters`) into one dict, read fresh at call time — a legitimate one-time consolidation of scattered stubs the goal spec explicitly asked for, not a duplicate computation of any of them. |
| `promotion` block's three new fields (`promotion_eligible`, `refusal_class`, `reason`) | OK — not displayed | Grepped the whole frontend for `promotion_eligible`/`refusal_class`: zero matches. Matches this iteration's own explicit OUT-OF-SCOPE line ("no UI home is registered for it this era; it stays CLI/report-only") and `blueprint.md`'s existing J-08 IA row. Not a hidden-feature violation — the absence is a declared product-shape decision this iteration, not an accidental gap. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Referee Registry shortlist table (S-6 sixth row) | OK | Same home as iter-8 (`state/blueprint.md:39`, `/desk` → Referee Registry, already verified ≤2 clicks from `apps/frontend/components/NavBar.tsx`'s `GET /meta/ui-routes`-driven nav in the iter-8 audit). No route/section change this iteration — confirmed via the diff: `apps/frontend/app/desk/page.tsx` and `lib/types.ts` are the only frontend files touched, and neither adds a new `<section>`, component, or router entry. |
| `promotion` block | OK — correctly unhomed, per spec | No new page/route introduced for it. `blueprint.md:40` already registers "no new page" as this feature's home for this era; this iteration's own IN SCOPE / OUT OF SCOPE sections confirm rendering it is deliberately deferred. Not a "hidden feature" FAIL — a feature the product's own contract declares CLI/report-only this era is not an IA violation. |
| Nav skeleton (`app/meta.py` `UI_ROUTES`) | OK | Not in the changed-file list (`git diff --stat` against the snapshot SHA shows exactly the 10 files enumerated below); still 3 routes per `blueprint.md:15-27`. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Stale docstring on `authorize_promotion` — describes itself as still unwired.** `referee_adjudicate.py:6` (module docstring: "``authorize_promotion`` (the J-08 interlock's pure decision function, unwired this iteration)") and `referee_adjudicate.py:1720,1731-1732` (section header + function docstring: "NOT wired into ``pnl_scan._promote`` this iteration (J-08's job) -- a pure, unwired function only.") were accurate when written at iteration 7, which built `authorize_promotion` unwired and explicitly deferred wiring to J-08. This iteration (iter-9) *is* J-08 and, per the verified evidence above (`pnl_scan.py:150,349`), genuinely wires it — but neither docstring was updated to say so. Functionally this is harmless (verified above: there is still exactly one `authorize_promotion` implementation and exactly one call site; no duplication or bypass resulted from the stale text), so it does not meet the objective FAIL bar. It is flagged because a Data-Contract-critical function's own docstring now contradicts the code that calls it, which is exactly the kind of drift a future pass could act on incorrectly (e.g., "wire it, it says unwired" duplicate-wiring attempt). **Suggested fix for a future lean pass:** update `referee_adjudicate.py:6` to drop "unwired this iteration," and update `referee_adjudicate.py:1720` / the docstring at `:1731-1732` to state it is wired into `pnl_scan._promote` as of iteration 9, removing the "unwired... a pure, unwired function only" sentence.
- No other formatting/labeling drift observed. The `family_id`/`family_q` fix genuinely closes iter-8's F1 WARN (verified independently above, not merely asserted from the spec's own claim) — no open advisory carries forward from iter-8 into iter-9's own new work.

---

## Files reviewed

- Blueprint: `runs/goal-session-referee/state/blueprint.md` (IA + Data Contract, including the iter-9 note)
- Iteration spec: `docs/phases/goal-referee-iter-9.md`
- Bounded diff: `runs/goal-session-referee/iter-9/iter-diff.md`, plus `git diff a385f7e813ea89c4c25ea0d0b941d1a2722e8ab` for the two files it truncated (`test_pnl_scan.py`, `test_referee_adjudicate.py`)
- `git diff --stat` against the snapshot SHA confirms exactly 10 files changed, matching the bounded diff's file list one-for-one (no out-of-band change)
- Prior verdict: `runs/goal-session-referee/iter-8/coherence.md` (F1 WARN text, verified closed)
- No `reports/phase-goal-referee-iter-9-ui-surface-map.md` exists for this iteration (consistent with "no new user-facing capability" — surfaces derived directly from the diff instead)
- Source files read directly (not just diffed): `apps/backend/app/research/pnl_scan.py`, `referee_adjudicate.py`, `referee_registry.py`, `referee_routes.py`; `apps/frontend/app/desk/page.tsx`, `apps/frontend/lib/types.ts`
