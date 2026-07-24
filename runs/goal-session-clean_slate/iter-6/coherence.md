# Iteration 6 — Coherence Audit

**Iteration:** goal-clean_slate-iter-6
**Date:** 2026-07-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration (why the checks below are short)

This is a backend dead-code-removal + hardening iteration with an explicit "no new features" mandate,
independently confirmed from three sources:

- The iteration spec's own "New user-facing capability / New information displayed / New user
  actions / UI surface changes" fields all read **None**, and "Blueprint conformance" states no
  `blueprint.md` edit is required.
- `reports/phase-goal-clean_slate-iter-6-ui-surface-map.md` (ui-impact-analyst): 0 `.tsx`/`.ts` files
  changed, 0 new pages, 0 modified components, nav unchanged (2 items).
- The actual diff since snapshot `82d6d4d563a8e63ff1190660c93c414977f00779` (via `git diff <sha> --
  .` with the standard noise excludes, cross-checked against `git status`): the only product-code
  change anywhere is `apps/backend/app/research/routes.py` — 67 deletions, 0 insertions, removing 5
  already-dead Pydantic request-body classes (`ThesisRequest` line 85, `ResolveRequest` 103,
  `ActionRequest` 112, `StudyRequest` 122, `ReviewRequest` 208, all pre-existing orphans of an
  earlier iteration's route demolition) — plus one new untracked test file,
  `apps/backend/tests/test_routes_no_orphaned_request_models.py` (an AST-based structural guard, not
  a product code path). I independently confirmed via grep that all 5 named classes now show `0`
  occurrences and the 4 kept classes (`BacktestRequest`, `DatasetRecordRequest`, `BarRecordRequest`,
  `EdgeReportComputeRequest`) each still show exactly 2 (def + a live `body:` route parameter) — no
  new class, function, or route decorator was added anywhere in the file.

The README.md hunk visible in the raw `git diff <snapshot-sha>` output (Case Studies wording) is
iter-5's own already-landed showcase/README-maintainer change, not this iteration's — the provided
snapshot SHA is a stash object created on top of iter-5's final commit (`3485637`) but before iter-5's
showcase-artifacts commit (`ca5a663`) landed, so that commit's content re-appears in the "since
snapshot" diff. This iteration's own dev/audit trail (dev handoff, ui-surface-map, and the
independent pipeline-auditor's report) all agree README.md was **not edited** this iteration (the 3
stale sentences were already gone). Confirmed with `git diff HEAD -- README.md` = empty. Not
attributed to this iteration; not a coherence concern either way (a prose correction describing an
already-shipped, already-registered surface, not a new value or page).

Everything else in the noise-excluded diff (`runs/*`, `reports/*`, telemetry/trace/dispatch
bookkeeping, iter-5 report re-renders) is harness/showcase churn outside this gate's scope per the
agent's own instructions.

## Data Contract check

No value in the blueprint's Data Contract was touched by any new computation or serving path this
iteration — the only backend edit is a pure subtraction of inert classes that were never wired to a
route (each had exactly 1 occurrence — its own def line — before this iteration, per the iteration
spec's planning-time verification trail and independently re-confirmed by grep above). No new
function, service, or endpoint was added anywhere in the diff.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Bands (tradable map) | OK — untouched | `tradability.py` unchanged; no diff |
| Touch events / setups | OK — untouched | `setups.py` unchanged; no diff |
| Edge cells + not-computed payload | OK — untouched | `edge_report.py` unchanged; no diff |
| Edge-report compute snapshot | OK — untouched | `edge_report_compute.py` unchanged; no diff |
| PnL ledger rows | OK — untouched | `pnl_ledger.py` unchanged; no diff; `reports/pnl/pnl-history.md` byte-identical (TC-17) |
| Bars / candles | OK — untouched | `bars.py` unchanged; no diff |
| Levels / zones | OK — untouched | `levels.py` unchanged; no diff |
| Strategy registry + champion pointer | OK — untouched | `strategies.py` unchanged; no diff |
| Datasets | OK — untouched | `datasets.py` unchanged; no diff |
| Backtests | OK — untouched | `backtests.py` unchanged; no diff |
| Profiles | OK — untouched | `profiles.py` unchanged; no diff |
| Research labels (taxonomy) | OK — untouched | `taxonomy.py` unchanged; `GET /research/taxonomy` reconfirmed 200 w/ same slimmed payload |
| Route / nav inventory | OK — untouched | `app/meta.py` unchanged; nav reconfirmed 2 items |
| `config_fingerprint` | OK — unchanged | reconfirmed live at `08e471b10130e1e2`, matching pre-iteration value |
| (deleted-concept classes: thesis/verdict/hint/study bodies) | OK — deletion, not a new computation | `apps/backend/app/research/routes.py:85,103,112,122,208` now removed; these classes belonged to entities the blueprint already lists as "Removed entirely this interlude" (active thesis, verdict timeline, hints, study jobs/results) — deleting their now-orphaned request schemas *completes* the blueprint's own removal mandate, it does not introduce anything |

No new displayed value or entity is introduced this iteration (spec: "New information displayed:
None"; ui-surface-map: 0 modified components) — Data Contract §A5 (unregistered-new-value) does not
apply.

## Information Architecture check

No new page, route, or feature exists in this iteration to evaluate against the IA — 0 frontend
files changed, 0 new routes, nav unchanged at exactly "Cockpit" + "Structure" (re-confirmed by the
iteration's own TC-11 evidence and the ui-surface-map).

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| *(none — no new feature/page/route this iteration)* | OK | `app/meta.py` ROUTES unchanged (no diff); nav re-verified at 2 items per `reports/phase-goal-clean_slate-iter-6-ui-surface-map.md` |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The pipeline auditor's own report (`docs/handoffs/goal-clean_slate-iter-6-audit.md`, finding T1)
  flags an undeclared edit to `runs/goal-session-clean_slate/journey-scripts/J-05.json`
  (`default_timeout_ms` 20000→30000) that is missing from this iteration's "zero out-of-inventory
  changes" accounting. I confirm this is real (visible in `git diff <snapshot-sha>` under the
  excluded `runs/*` path) but it is outside this gate's Data-Contract/IA scope: it is a test-replay
  timing knob in a golden script, not a displayed value with a canonical source and not a page/route.
  Flagging only so it isn't mistaken for something this audit missed — it does not affect this
  verdict and is already correctly owned by the auditor's report as a GAP, not a coherence defect.
- No unregistered-but-new value, no label drift, no formatting inconsistency to report — there is
  no new UI surface this iteration to exhibit either.
