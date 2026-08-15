# Iteration 10 — Coherence Audit

**Iteration:** goal-referee-iter-10
**Date:** 2026-08-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Diff reviewed: `git diff bf6e3b9d5d0052f67c2adb56736d540508b29e6e` (snapshot SHA matched
`runs/goal-session-referee/iter-10/snapshot-sha`), 11 files, +1910/-49, plus the `blueprint.md`
+16/-0 append-only note. No lockfile/dependency-manifest changes in the excluded-paths stat.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Adjudications (snapshots + pending fold) | OK | `apps/frontend/lib/api.ts:2153` `fetchRefereeAdjudications()` reads `GET /research/desk/referee/adjudications` (registered endpoint); `apps/frontend/app/desk/page.tsx` `RefereeAdjudicationsSection`/`RefereeAdjudicationEntryRow` (~4939-4996) render `entry.verdict`/`confirmatory_output_refused`/`refusal_reason`/`snapshot.*` verbatim, zero arithmetic |
| Registry (families/hypotheses/withdrawals/certificates) | OK | Adjudications and Runs sections each issue their own `fetchRefereeRegistry()` (page.tsx:8454-8464) against the SAME already-canonical `GET /research/desk/referee/registry` the shipped Registry section already owns — a second call to the one canonical source, not a second implementation; reasoning logged in `runs/goal-session-referee/state/assumptions.md` iter-10 "developer" entry |
| Null compute progress + runs | OK | `api.ts` `fetchRefereeNullRuns`/`triggerRefereeNullsCompute`/`fetchRefereeNullsCompute`/`cancelRefereeNullsCompute` map 1:1 onto the registered `GET .../nulls/runs` + `POST/GET/POST-cancel .../nulls/compute` endpoints; page.tsx `RefereeNullRunsSection`/`RefereeNullBuildControl` render response fields verbatim |
| Evaluation records + runs | OK | `api.ts` `fetchRefereeEvaluateRuns`/`triggerRefereeEvaluate`/`fetchRefereeEvaluate`/`cancelRefereeEvaluate` map 1:1 onto the registered `GET .../evaluate/runs` + `POST/GET/POST-cancel .../evaluate` endpoints; same verbatim-render pattern |
| Promotion authorization verdict (`authorize_promotion`) | OK | `referee_adjudicate.py` — only the module/function docstrings changed (dropped "unwired"); the function body, its `pnl_scan._promote` call site, and its return shape are untouched this iteration |
| Strategy-family evidence pooling (`_pool_strategy_trades`) | OK — not a duplicate | `referee_adjudicate.py:522-596` adds an optional `candidate` filter to the SAME existing function (narrows eligible input at certificate-mint time only); no second pooling implementation created. `run_evaluation_and_record` (~1255-1270) passes `certificate_mint["candidate"]` through only when `certificate_mint` is supplied; `None` (every existing caller) stays whole-corpus/unfiltered, byte-identical to before. Matches blueprint.md's own iter-10 rider note (lines 307-312) |
| MCP `desk_referee` / `desk_referee_registry` | OK | `apps/backend/app/mcp/__init__.py:141-142` registers both as byte-identical `_STATIC_PATHS` GET proxies of the two endpoints above (no new endpoint, no selector params); `test_mcp_server.py`'s new tests assert `result.content[0].text.encode("utf-8") == rest.content` against the live REST response in both empty and populated states — the byte-identity is test-enforced, not just asserted in a comment |
| "Seed identity" provenance line | OK — relabel, not new value | page.tsx renders `entry.hypothesis_id` (already served, already the row's own primary key) under the label "seed identity" rather than serving/hardcoding the `REFEREE_SEED` constant. Logged as a deliberate T-1 call in `assumptions.md` iter-10 "developer" entry, explicitly reasoned to avoid creating an unverified second copy of a backend constant or a new Data-Contract row — a re-format of an existing canonical field, which the coherence-audit skill treats as non-violating |

No new function/service/endpoint was found anywhere in the diff that independently recomputes an
already-registered value, and no new UI surface fetches a registered value from a non-canonical
source. The one new "displayed value not previously in the contract" (seed identity) resolves to
an existing canonical field re-labeled for display, not a new computation — so it needs neither a
WARN nor a Data-Contract addition, consistent with the iteration spec's own "Data-contract
additions: None" and the blueprint's own iter-10 note (lines 298-312).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` → "Referee Adjudications" section | OK | `apps/frontend/app/desk/page.tsx:10501-10515` (approx, per diff hunk `@@ -9614,6 +10501,48 @@`) inserts a `<CollapsibleSection>` directly below the existing Referee Registry `<section>`, inside the SAME `DeskPage` shell/`<main>` — matches blueprint.md's pre-registered J-06 IA row ("Desk → Referee Adjudications") verbatim |
| `/desk` → "Referee Runs" section | OK | Same file, immediately below Adjudications — matches blueprint.md's pre-registered J-04 IA row ("Desk → Referee Runs") verbatim |
| Nav skeleton (3 routes) | OK — unchanged | Full diffstat since snapshot touches only `apps/backend/app/mcp/__init__.py`, `apps/backend/app/research/referee_adjudicate.py`, 6 backend test files, and `apps/frontend/{app/desk/page.tsx, lib/api.ts, lib/types.ts}`. No layout/nav/router file (`layout.tsx`, any `Nav`/`Sidebar` component, `app/page.tsx`, `app/structure/*`) appears anywhere in the diff — Cockpit `/`, Structure `/structure`, Desk `/desk` stay exactly as before |
| Reachability | OK — ≤2 clicks (1 click + in-page expand) | Both sections sit on `/desk`, one top-nav click away from anywhere in the app, then an in-page `CollapsibleSection` toggle — the identical reachability pattern every other shipped `/desk` section already uses (Registry, Playbook Evidence, Skipped, etc.), so no regression in discoverability |
| Duplicate home | OK — none found | Grepped the pre-existing (untouched) `RefereeHypothesesTable` (Registry section, page.tsx:4872) for any prior "verdict" or run-ledger rendering — none exists; the only pre-diff "verdict" hit in the whole file is an unrelated tape/volume field (`spike_into_trigger_verdict`, line 6838). Adjudications and Runs are genuinely new entities with no prior home, not competitors to Registry |
| Parallel shell | OK — none found | Both sections use the page's established `CollapsibleSection`/`toggleSection`/`sectionReadIssuedRef` deferred-fetch pattern (page.tsx:8454-8464) identically to every other `/desk` section; no new layout, wrapper, or shell was introduced |

Cross-section integration: Adjudications and Runs each independently re-fetch the Registry
endpoint to join per-hypothesis fields (`null_spec_id`/`test_spec_id`) and to know which controls
to render — so the three Referee sections read from a shared canonical source rather than existing
as three disconnected panels, addressing the "bolted on" concern named in the dispatch note.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None beyond what is already resolved above. The two interpretation calls this iteration made
  (seed-identity relabeling; the two new sections each independently re-fetching the registry
  rather than assuming click order) are both logged with rationale and reversibility in
  `runs/goal-session-referee/state/assumptions.md`'s iter-10 entries, and both land on the
  non-violating side of the Data Contract / re-format rules — noted here for the record, not as
  a deduction.
