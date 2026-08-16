# Iteration 13 — Coherence Audit

**Iteration:** goal-referee-iter-13
**Date:** 2026-08-16
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Summary

J-12 gives `GET /research/desk/referee/evidence` (registered since iter-0, owner
`app/research/referee_evidence.py`) its first direct UI reader: `fetchRefereeEvidence()` in
`apps/frontend/lib/api.ts:2122-2150`, new types in `apps/frontend/lib/types.ts:2429-2476`, and a
new `RefereeEvidenceReadinessSection` component in `apps/frontend/app/desk/page.tsx:4990-5199`,
rendered below the shipped registered-hypotheses table inside the already-existing "Referee
Registry" section on `/desk`. Backend diff is test-only (`test_desk_ui_guards.py`,
`test_referee_evidence.py`) — confirmed via `git diff 027a7f7..HEAD -- apps/backend` touching zero
production files. Full file list (5, matches the bounded diff exactly, cross-checked against
`git diff 027a7f7 --stat`): `apps/backend/tests/test_desk_ui_guards.py`,
`apps/backend/tests/test_referee_evidence.py`, `apps/frontend/app/desk/page.tsx`,
`apps/frontend/lib/api.ts`, `apps/frontend/lib/types.ts`.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Referee evidence coverage + per-family readiness (owner `referee_evidence.py`, endpoint `GET /research/desk/referee/evidence`) | OK | `apps/frontend/lib/api.ts:2126` fetches the exact registered path; `apps/frontend/app/desk/page.tsx:4990-5199` renders `evidence.playbook_occurrence.*` / `evidence.strategy_trade.*` fields verbatim, zero arithmetic between fields (only `.length === 0` ternaries for empty-state branching) |
| Playbook-family aggregate (`records`, `distinct_sessions`, `signals_at_current_basis`) vs. the shipped shortlist's per-candidate readiness (`n`, `n_sessions`) — PUMP NOTE item (a) | OK — distinct fold, not a duplicate | Shortlist columns at `apps/frontend/app/desk/page.tsx:4802-4812` (`Candidate`/`Estimand`/`Setup / Side`/`n`/`Sessions`/`Accrual / day`/`Projected days`/`Projected sessions` — one row per S-1..S-6 candidate, filtered to that candidate's own `(setup_id, side)` cell) vs. the new block's `Records`/`Distinct sessions`/`Signals at current basis` (whole-corpus aggregate, `page.tsx:5040-5068`). Different labels, different granularity, different question answered (per-hypothesis registration readiness vs. corpus-wide coverage/staleness/integrity health) — not the same displayed fact under two names. Both ultimately read the SAME server-side pooling (`playbook_occurrence_readiness()`), so there is no drift risk: the new block reads the endpoint's top-level aggregate fields, the shortlist reads the same endpoint's `per_setup_side` cells (via `referee_registry.py`'s reuse of the shared function, per blueprint.md's iter-8 note) — one computation, two legitimate views. Also checked `PlaybookEvidenceSection` (`page.tsx:4666-4701`, fed by a *different* Data Contract row/endpoint, `DeskPlaybookEvidence`/per-cell signal counts) for a possible second overlap — different owner, different endpoint, different question (screening signal detail vs. referee statistical-evidence coverage); no overlap |
| `integrity_errors` shape binding (`{file, error}[]` in `types.ts:2451,2466` vs. the iter-13 spec's own shorthand `[string, ...]`) | OK, not a coherence issue | Verified against `apps/backend/app/research/referee_evidence.py:304,354` (`"integrity_errors": errors`, sourced from each store's own `.list()` return) and the universal store-error shape used across this codebase (`errors.append({"file": path.name, "error": str(exc)})` — 9+ call sites incl. `desk_forward.py:896`, `desk_topup_log.py:158`, `desk_playbook_log.py:147`). The frontend type matches the real served shape (and the established `DeskTopupRunsListResult`-style precedent at `types.ts:1020`); the iteration spec's prose shorthand was imprecise, not the code — no live Data Contract drift |
| No new/unregistered value introduced | OK | Every field the new component reads (`records`, `distinct_sessions`, `signals_at_current_basis`, `detector_basis`, `config_fingerprint`, `stale_basis_dates`, `integrity_errors`, `dataset_count`, `per_split_counts.train/holdout`, `trade_count`, `tick_gate_statement`, `basis_caveats`) was already part of the registered response shape since iter-0/iter-4; zero new field added by this diff |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| New "Evidence Readiness" blocks inside `/desk` → Referee Registry | OK | No new route/page: `apps/frontend/app/desk/page.tsx` is the only route file touched (not a new file under `apps/frontend/app/`). Reachable in the same 2 clicks as the already-shipped J-05/J-07/J-11 content in this section (nav → `/desk`, then expand the existing "Referee Registry" `CollapsibleSection`) — `page.tsx:4990-4996` (`RefereeRegistrySection` appends `<RefereeEvidenceReadinessSection .../>` immediately after the shipped `<RefereeHypothesesTable/>`, no new collapsible, no new toggle). State/fetch wiring is a third call added to the *existing* `"refereeRegistry"` branch of `toggleSection` (`page.tsx:8724-8727`), not a new `useEffect` |
| Blueprint IA table edit (`runs/goal-session-referee/state/blueprint.md`) | OK — additive, honest | `git diff 027a7f7 -- runs/goal-session-referee/state/blueprint.md`: the J-01 row's "Canonical home" cell changed from the bare endpoint string to `` `/desk` → **Referee Registry** ``, and one new J-12 row was added pointing at the same home — matches what actually shipped. No nav-skeleton line touched (still exactly 3 top-level routes). Confirmed no `blueprint.reapproval-requested` marker file was created (correctly not required for this additive edit) |
| New `data-testid`s / headings collide with shipped ones | OK | All new testids are under the `referee-evidence-*` namespace (`referee-evidence-section`, `-playbook-block`, `-playbook-table`, `-playbook-records`, `-strategy-block`, `-strategy-tick-gate`, etc.) — none reuse a shipped `referee-shortlist-*`/`referee-registry-*`/`referee-hypotheses-*` id; new heading "Evidence Readiness" doesn't collide with any shipped section heading |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. (Candidates considered and ruled out during this audit: possible label collision between
the new aggregate counts and the shortlist's per-candidate `n`/`n_sessions` column — labels are
textually distinct, `Records`/`Distinct sessions` vs. `n`/`Sessions`, no confusable overlap;
possible numeric-formatting inconsistency — the shortlist itself already renders raw integers
without a `fmt()` helper, so the new block's plain `{value}` rendering matches the established
convention, not a new drift.)
