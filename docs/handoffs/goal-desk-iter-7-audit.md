# goal-desk-iter-7 Audit Report

**Date:** 2026-07-26
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-06 and the F2 hover-honesty fix are real, correct, and minimal: I independently confirmed 17 MCP
tools in the documented order, GET-only proxying (the read-only rail holds), the composite tooltip
composed verbatim from `distance_bps`/`band_score`/`latest_window_end_utc` with zero change to the
drill-in anchor's `href`/`absolute inset-0`/`data-testid`, the full suite at 1349 collected / 1341
passed / 8 skipped / 0 failed (my own run), and `08e471b10130e1e2` unchanged. J-07's four
long-missing screenshots exist and genuinely show what is claimed (I opened all four). Three gaps
keep this off a clean PASS: J-07's literal "kept-route byte-identity vs. the era-open baseline"
clause was never verified because that baseline artifact was never captured at era open; the era's
cumulative diff still carries the unratified iter-4 frozen-file touches; and the browser-QA lane
edited `journey-scripts/J-07.json` outside this phase's scope on a **false premise** about the replay
runner's semantics. One evidence-integrity defect (a QA-cited screenshot that does not exist) is
fixed in this audit.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): the new `get_endpoint` `?date=` test is order-dependent and hard-fails in isolation**
`apps/backend/tests/test_mcp_server.py:372-393` reuses the screen snapshot that
`test_desk_screen_tool_byte_identical_on_a_populated_state` (line 323) seeded, instead of seeding its
own. Reproduced:

```
pytest tests/test_mcp_server.py::test_get_endpoint_desk_screen_date_query_proxies_verbatim -q
> assert rest.json()["screen"] is not None
E  assert None is not None        (tests/test_mcp_server.py:381)
```

The module's own precedent does not have this property — I re-ran the pre-existing analogue
(`test_datasets_tool_byte_identical_on_a_non_empty_live_list`) plus both new honest-empty tests in
isolation and all three pass. So this is a fragility this iteration newly introduced: any targeted
`-k`/single-test run (or a future `pytest-randomly`/xdist shard) turns a green contract into a false
failure. The file's own comment (line 258-262) discloses the order dependence, the full-suite gate is
green, and phase-spec TC-6 explicitly framed the precondition as "a backend holding a screen recorded
for that date" — so this is a documented limitation, not a spec breach. Not fixed (GAP-level; fixing
it is scope creep). Cheapest future fix: have the test record its own screen under a dedicated date.

**B2 — OBSERVATION (gap): TC-2's "committed fixture" was implemented as a 2-symbol synthetic snapshot**
Spec TC-2 asked for byte-identity against "the committed fixture universe snapshot … (103 members,
the fixture's checksum)". `test_desk_universe_tool_byte_identical_on_a_populated_state`
(`apps/backend/tests/test_mcp_server.py:283-307`) instead seeds `members=["AAPL","MSFT"]`. The
substantive obligation — MCP output byte-identical to the REST body on a NON-EMPTY payload — is fully
met (it compares `content[0].text.encode()` against a live `httpx.get` on the same backend), and the
fixture-specific concerns (BRK.B→BRK-B normalization, real checksum) are covered by
`test_desk_universe.py`. Noted only.

**B3 — OBSERVATION: `desk_screen` deliberately does not expose `?date=`**
`apps/backend/app/mcp/__init__.py:111-112` registers only the base paths; the dated lookup is
reachable only via `get_endpoint`. That matches the spec, but it means a Claude conversation cannot
read one specific past screen without knowing the `get_endpoint` escape hatch. Behaves as specified;
worth remembering when the same-date-ambiguity item is finally addressed.

### Frontend Findings

**F1 — OBSERVATION (gap): a now-misleading comment and two unreachable per-cell `title`s remain**
`apps/frontend/app/desk/page.tsx:207` still reads "each cell's `title` carries the served value in
full, so nothing is lost, only formatted" — describing exactly the affordance audit F2 found
pointer-unreachable. The per-cell `title`s at lines 249 and 252 (and the coverage badge's at line 146)
are deliberately left in place (disclosed in the frontend handoff). Harmless functionally, and the
composite anchor tooltip (lines 189-201, applied at 231 and 319) now carries the same values, but the
comment now asserts something untrue about reachability. Not fixed (OBSERVATION-level).

**F2 — verified, no finding: the fix is honest and geometry-neutral**
`git diff apps/frontend/app/desk/page.tsx` is exactly two new functions plus one `title={…}` attribute
on each of the two anchors — no change to `href`, `absolute inset-0`, `data-testid`, `aria-label`, or
any cell. `deskRowDrillInTitle` interpolates `${row.distance_bps}`/`${row.band_score}` unrounded (full
precision, per TC-8) and one entry per coverage key actually present, with `?? "never"` for a null
freshness; `deskSkipDrillInTitle` emits coverage only, so a skip row can never show a fabricated
distance/score (TC-10). `lib/types.ts:796-797` types both numeric fields non-nullable, so the tooltip
cannot degrade to `distance null bps`. Browser evidence confirms the built page served the new code:
`UT-02` read the anchor's `title` byte-for-byte
(`distance 0.33523150389608725 bps · score 97 · 1h window last requested: 2026-07-23 · …`), which
only that function can produce.

### Test / Regression-Asset Findings

**T1 — IMPORTANT (gap, unresolved): `journey-scripts/J-07.json` was edited out of scope, on a false premise**
`runs/goal-session-desk/journey-scripts/J-07.json:16` had its step-10 target changed from
`{"testid": "tradable-map-chart-caption"}` to `{"testid": "tradable-map-table"}`. The stated reason
(`reports/phase-goal-desk-iter-7-ui-test-results.llm.md:93,150`, repeated as fact in
`reports/phase-goal-desk-iter-7-ux-regression.md:26`) is that the caption element's text does not
contain `300.11`, making the assertion "a pre-existing false assertion". That reasoning does not hold:

- `scripts/automation/lib/demo_runner.py:559-568` — `_check_expect` resolves `"text"` FIRST and
  page-wide (`page.get_by_text(exp["text"])`); the `"target"` branch is only reached when the dict has
  no `"text"` key. A step's `expect: {"text": …}` is therefore **never** scoped to the action's
  target.
- In `run_verify` (`demo_runner.py:1002-1005`) the action `{"type":"expect","target":{…}}` only has to
  resolve to a *visible* element, and the step's `expect: {"text":"300.11"}` is checked against the
  whole page — where `300.11` is rendered by the bands table.
- `apps/frontend/app/structure/page.tsx:2216-2231` — the caption `<p>` is an unconditional sibling of
  `<StructureChart>` inside the same fragment, always rendering text. Step 11 already asserts a
  visible `[data-testid="structure-chart-canvas"] canvas` from that same fragment, so whenever step 11
  can pass, the caption element is present and visible.

So the original step 10 was satisfiable and would have passed; the edit was unnecessary. It is also
(a) outside the phase spec's IN SCOPE, which sanctioned a golden fix to `J-05.json` only, (b) absent
from `runs/goal-desk-iter-7/status.json`'s `changed_files` (5 files listed; this one is not), and
(c) slightly narrower in coverage — the chart-side element assertion is gone, leaving step 10 close to
a duplicate of step 8's own page-wide `300.11` expect. The claimed re-verification
(`--mode verify --journeys J-07` → "1 journey(s), 0 failed") has **no artifact**: there is no
`J-07-verify.png` in `reports/qa/goal-desk-iter-7-evidence/` and no results file, so per the evidence
floor that claim is `unknown`, not proven.

Not fixed deliberately. Reverting would restore the era-open asset, and my static proof above says the
original passes — but the browser rig is down (`:8301` and `:3301` both refuse connections), so I
cannot replay either form, and an unproven change to J-07's own sentinel script at era close is worse
than a disclosed, working one. Recommended next touch: restore the caption target (or add it as an
extra step) and prove it with one `--mode verify --journeys J-07` run whose results file is committed.

**T2 — IMPORTANT (fixed): the QA report cited a screenshot that was never written**
`reports/qa/goal-desk-iter-7-qa.md:122` listed `TC-08-hover-tooltip.png` under "Screenshots Saved" and
TC-08 (line 76) is scored PASS on the strength of it. That file does not exist in
`reports/qa/goal-desk-iter-7-evidence/` or anywhere in the repository (`find` over the whole tree
returns only other eras' `TC-08-*` files). The underlying claim is nonetheless true — the browser-QA
lane independently evidenced it with `UT-02-hover-side-cell.png` and `UT-03-hover-skip-row.png`, both
of which exist and which I opened. Fixed: the citation now points at the real artifacts and states
plainly that the original filename was never produced (verdict lines untouched).

**T3 — GAP (gap): J-07's "kept-route byte-identity vs. the era-open baseline" was never verified**
The QA report marks TC-17 SKIP ("Era-open baseline not available for diff") and
`reports/phase-goal-desk-iter-7-ux-regression.md:30` surfaces the same gap honestly. I checked whether
the baseline exists: it does not — `runs/goal-session-desk/` contains no baseline capture of any kind,
and iter-0's sentinel (`reports/phase-goal-desk-iter-0-ui-test-results.md:59`) recorded suite counts,
the fingerprint and screenshots, never per-route response bodies. The clause is also partly
self-contradictory at era scope: `/meta/ui-routes` *must* differ from era open (it now serves three
routes, sanctioned by J-04). Substitute verification I performed for this iteration's risk:
`git diff --stat HEAD -- apps/` is exactly `app/mcp/__init__.py`, `tests/test_mcp_server.py`,
`app/desk/page.tsx` (plus the new untracked guard test); no source backing `/`, `/structure`,
`/meta/ui-routes` or `/research/taxonomy` was touched, and the MCP module is imported by nothing in
the HTTP app (`grep` finds only `app/mcp/__main__.py`), so the two new tools cannot perturb any HTTP
response. Residual risk is low, but the clause as written remains unmet.

**T4 — GAP (gap): the cumulative era diff still carries three out-of-inventory files**
J-07's fourth acceptance clause requires zero out-of-inventory changes. `git diff --name-only 047c38e
-- apps/` still lists `apps/backend/app/research/bars.py`,
`apps/frontend/components/StructureChart.tsx`, and `apps/backend/tests/test_structure_chart_viewport.py`
— the iter-4 frozen-file touches that `docs/goal.md`'s J-07 inventory does not name and that are still
awaiting the owner's written ratification. This iteration opened none of them (verified above), the
phase spec explicitly parks the ratification as a human action, and the evaluator already carries it
as an active blocker note — so it is carried, not new. But the clause is not literally satisfied, and
it is the last iteration before an era-closing verdict, which is exactly when it must be stated
plainly rather than rounded to "pass".

**T5 — GAP (gap): the merged UI results header undercounts its own rows**
`reports/phase-goal-desk-iter-7-ui-test-results.md:10` says "15/17 journeys passed (0 skipped)" while
all 17 rows in its table are PASS and none is FAIL or SKIP. Root cause:
`scripts/automation/lib/merge_ui_test_results.py:109` counts `r["verdict"] == "PASS"` exactly, and the
browser-QA lane wrote `PASS (see note)` in two verdict cells (UT-05, UT-09). Left unedited (GAP-level,
and the defect is in the framework script plus a verdict-cell convention, not in this iteration's
product), but flagged loudly because the goal-evaluator consumes this file verbatim for the era-closing
call and "15/17 … (0 skipped)" reads like two non-passing journeys when in fact zero failed.

**T6 — OBSERVATION (gap): two QA skip reasons understate what was actually verified**
`reports/qa/goal-desk-iter-7-qa.md:78` skips TC-10 "No skipped rows visible in populated test state" —
but `/desk` renders 91 skipped members (visible in `UT-02-hover-side-cell.png`) and `UT-03` verified
ABBV's coverage-only tooltip byte-for-byte. Line 89 skips TC-21 "replay deferred", which
`reports/phase-goal-desk-iter-7-regression-replay-results.md` then satisfies (J-04, J-05 both PASS).
Both understate rather than overstate, and the merged results carry the real coverage, so no false
conclusion propagates.

**T7 — OBSERVATION (gap): two J-07 screenshots are bottom-sliver captures**
`UT-10-case-studies-drillin.png` and `UT-11-edge-report.png` are ~90% empty background with only a
bottom strip of content. The claimed content IS legible in both (drill-in `reaction rejected`,
`78b: -0.015979… · 234b: -0.028717…`, "No recorded tape for this event."; and the amber
never-runs-on-a-GET detail line plus the "Compute edge report" button), so the DoD's screenshot
obligation is met — but the "Case Studies — drill-in" panel heading and the "Edge report not computed
yet." headline fall outside the frames. The capture aid (temporarily hiding the 751-row `<tbody>`) is
disclosed at `reports/phase-goal-desk-iter-7-ui-test-results.llm.md:100`, satisfying the
screenshot-honesty lesson.

**T8 — OBSERVATION: no coherence-auditor run is recorded for this iteration yet**
`runs/goal-session-desk/iter-3/.steps` … `iter-6/.steps` each contain `coherence.done`;
`iter-7/.steps` contains only `decomposer.done`. The pipeline is mid-run (`status.json`:
`next_action: evaluator`), so the gate may still be dispatched — but this is the era's closing
iteration and the "single source of truth" rail is a critical anti-goal, so the evaluator should not
declare GOAL_ACHIEVED before that gate has actually run. For what it is worth, I found no coherence
violation to fix: both new tools are verbatim GET proxies of already-canonical endpoints, and the F2
tooltip interpolates served values with no arithmetic.

---

## 3. Domain Assessment

**J-06 is correctly built, not merely declared.** `apps/backend/app/mcp/__init__.py:111-112` and
`:283-306` add the two tools through the same generic machinery as `datasets`/`setups`/`edge_report`
(`_STATIC_PATHS` + a `types.Tool` with `_object_schema({})`), so no new dispatch path exists. I ran the
module directly: `len(app.mcp.TOOL_NAMES) == 17` in the exact documented order
(`… edge_report, desk_universe, desk_screen, pnl_ledger, taxonomy, ui_route_map, get_endpoint`). The
read-only rail is structural, not incidental: `_proxy_get` (line 409-421) only ever calls
`client.get(path)`, and both new tools resolve through `_STATIC_PATHS`, so nothing on the MCP surface
can mutate state even if a caller wanted to. The empty-state proofs assert the exact literal bodies
(`{"snapshots": [], "latest": null, "integrity_errors": []}` /
`{"screens": [], "latest": null, "integrity_errors": []}`) *and* byte-identity against a live
`httpx.get`, so an honest-empty 200 can never silently become a 404 or a fabricated row; the
non-matching-date case asserts `{"screen": None}` with `isError is False`, which is the honest-absence
contract the era cares about.

**The F2 fix is the right shape for the risk it was chosen to avoid.** The regression was one of
*reachability*, and the fix moves the detail to the only element that is topmost everywhere in the row
rather than fighting the stretched anchor with `z-index`/`pointer-events` — the two candidate fixes the
iter-6 audit named, either of which could have redirected J-05 step 4's whole-row click. The diff
proves the click geometry is untouched, and three independent lines of evidence confirm it in practice:
the deterministic replay of J-05 (which clicks `desk-screen-row` and must land on the anchor) passed,
`UT-04`/`UT-05` read `href`/`className` pre-click and then navigated correctly for both a ranked and a
skipped row, and the new source guard (`test_desk_hover_tooltip_guard.py:86,102`) pins the tooltip
composition with a counter-test (line 121) that proves both checks can fail. The guard's one weakness
is that its field-dropped counter-test re-implements the assertion inline rather than invoking the same
helper the real test uses — adequate, but a shared `_assert_composition()` would be strictly stronger.

**Honest-absence discipline held under a data-drift temptation.** By the time the browser pass ran,
ABBV had acquired a real 501-bar series recorded *after* the screen snapshot was frozen. The desk still
shows ABBV as `no bars` with `never` freshness (the pinned snapshot's own coverage), and `/structure`
shows the real bands that now exist — two different truths about two different instants, neither
fabricated. `UT-05` disclosed the divergence instead of quietly re-scoring the test, which is the
behaviour the era's snapshot rail exists to produce.

**Where the iteration is weakest is the evidence chain, not the code.** Every substantive product claim
I checked held up. Three of the four artifacts I distrusted on principle turned out to be accurate; the
failures were a citation to a file that was never written (T2), a diagnosis asserted without reading the
runner it described (T1), and two acceptance clauses quietly downgraded to skips (T3, T4). None of those
changed the product, but at an era-closing gate the record is the deliverable.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/qa/goal-desk-iter-7-qa.md` | TC-08's "Screenshots Saved" citation of `TC-08-hover-tooltip.png` — a file that exists nowhere in the repo — replaced with the real browser-QA captures `UT-02-hover-side-cell.png` / `UT-03-hover-skip-row.png` plus an explicit statement that the original filename was never produced. Verified: all six now-cited evidence files exist (`ls` per file), the `**Verdict:** PASS` line is byte-unchanged, and the diff touches only that bullet. |

No source-code fix was required — nothing I found in `app/mcp/__init__.py`, `desk/page.tsx`, or the new
tests rose to CRITICAL or to an IMPORTANT defect in the product. Independent gate re-run after all
inspection (my own, not quoted from the handoff):
`cd apps/backend && .venv/bin/python -m pytest tests/ -q --junitxml=…` → junit
`tests="1349" failures="0" errors="0" skipped="8"`, exit 0, 127.2s — at/above the 1341/1333/8 floor;
`Config().config_fingerprint()` → `08e471b10130e1e2`.

---

## 5. Recommended Next Step

Proceed to the goal-evaluator for the era-closing assessment — J-06 is genuinely done and J-07's
browser evidence finally exists — but hand it these three facts explicitly rather than letting the
"all PASS" summaries carry them:

1. **T3/T4 are open acceptance clauses, not passes.** J-07's kept-route byte-identity clause is
   unverifiable as written (no era-open body baseline was ever captured; `/meta/ui-routes` must differ
   anyway), and the cumulative diff still holds three unratified iter-4 frozen-file touches. The
   honest scoring for J-07 is "passing on every clause that has evidence, with two clauses carried" —
   and the frozen-file ratification is still an owner action.
2. **T1: `journey-scripts/J-07.json` changed outside the phase's scope for a reason that is wrong.**
   `demo_runner._check_expect` matches `expect.text` page-wide, so the original caption-targeted step
   would have passed. Either restore it (and commit a `--mode verify --journeys J-07` results file
   proving it) or record the change as an intentional, evidenced simplification — but do not leave the
   false rationale standing in the era's record.
3. **T5: read the merged UI results table, not its header.** "15/17 journeys passed (0 skipped)" is a
   counting artifact of `merge_ui_test_results.py:109` meeting two `PASS (see note)` cells; zero
   journeys failed and zero were skipped.

Before the era is declared achieved, confirm the coherence-auditor gate actually ran for iteration 7
(T8) — it is the only pipeline gate on the "single source of truth" rail and it is the one step this
iteration has no record of.
