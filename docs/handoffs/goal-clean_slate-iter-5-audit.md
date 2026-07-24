# goal-clean_slate-iter-5 Audit Report

**Date:** 2026-07-24
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's own three-pillar goal is substantially and genuinely achieved: I independently
re-ran the full backend suite (1167 passed / 7 skipped / 0 failed, exit 0, live fingerprint
`08e471b10130e1e2`), confirmed the one product change is exactly scoped (flag flip + one sentence,
gate structure intact), and confirmed the J-05 browser walk genuinely exercised every kept surface
— including the actual Case Studies drill-in (a real row click, `data-testid="case-drillin"`
rendering with matching data and the honest "No recorded tape for this event." fallback, updating on
a second-row click). Two documented gaps keep this from a clean PASS: (B1) the third pillar — the
"session-wide diff-vs-inventory close-out" that claimed **zero residue** — actually missed **five
orphaned Pydantic request-body classes** left behind by iter-1's route demolition, a grep-provable
breach of the critical "deletion is complete, never cosmetic" anti-goal; and (F1) the newly-visible
Case Studies drill-in has no scroll-into-view on an unfiltered ~1,758-row table (a pre-existing
era-5B/5C UX condition now reaching users for the first time). Neither is fixed in-audit, on purpose
— see §4 — because both fixes are backend/UI edits that would violate this sentinel iteration's
explicit, verified single-file / zero-backend-edit scope contract.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (gap, unfixed — see §4 for why): Five orphaned request-body classes are dead code
from the demolished routes**

`apps/backend/app/research/routes.py` still defines five Pydantic body-model classes whose route
handlers were deleted in iter-1:

- `ThesisRequest` — line 85 ("Body for `POST /research/thesis`")
- `ResolveRequest` — line 103 ("Body for `POST /research/thesis/{id}/resolve`")
- `ActionRequest` — line 112 ("Body for `POST /research/thesis/{id}/action`")
- `StudyRequest` — line 122 ("Body for `POST /research/studies`")
- `ReviewRequest` — line 208 ("Body for `POST /research/thesis/{id}/review`")

Evidence this is genuinely orphaned dead code (not a false positive):
- `git grep -E "\b(ThesisRequest|ResolveRequest|ActionRequest|StudyRequest|ReviewRequest)\b"` across
  all of `apps/` (excluding `node_modules`) returns **only the five class-definition lines** — no
  route handler references them, nothing imports them, no test names them.
- Contrast the kept `BacktestRequest` (line 141), which is referenced at line 1136 as an actual route
  body parameter. The five suspect classes have no such second reference.
- `git show e7865b4:apps/backend/app/research/routes.py` (the pre-demolition baseline) shows all five
  were **live** body models there; iter-1 deleted their `@router.post(...)` handlers but left the
  schema classes. They persist at HEAD (committed), referenced nowhere.
- The five demolished routes correctly return 404 (verified by browser-qa UT-J-01 and the dev/QA curl
  sweeps), so the *surface* is functionally gone — but its *code* is not "gone from code…
  grep-provably" as the anti-goal requires.

Why this matters for THIS iteration specifically: the critical anti-goal states "Deletion is
complete, never cosmetic. No orphaned imports, dead components, unreachable routes, dangling MCP
tools, or skipped tests survive; a deleted surface is gone from code, routes, nav, MCP, types, and
tests alike — grep-provably." A request-body schema for `POST /research/thesis` is part of the thesis
surface's code. More pointedly, this iteration's own headline deliverable is the "session-wide
diff-vs-inventory close-out," and its cross-check artifact
(`runs/goal-session-clean_slate/iter-5/diff-vs-inventory-crosscheck.md`) concludes "**Zero
out-of-inventory changes found**" / "Zero residue," accounting for `routes.py` merely as "I-1/I-2
route+import strips" — it never noticed that the strip left five orphaned body models. That
completeness claim is therefore materially inaccurate. Four prior iterations' reviews/audits and this
iteration's own review + QA ("no_dead_code: pass") all missed it too — the audits grepped for deleted
*module* imports and *route* 404s but never for orphaned request/response *models* of the deleted
routes.

Functionally inert: FastAPI never registers these classes (no path references them, so they are not
in the OpenAPI schema), nothing imports them, and nothing breaks. This is why the finding is
IMPORTANT, not CRITICAL — no behavior fails, nothing is reachable, nothing leaks. (I was between GAP
and IMPORTANT and, per the rubric, chose the higher because it is a grep-provable breach of a
critical-tagged rail and it falsifies a stated deliverable's central claim.)

### Frontend Findings

**F1 — GAP (unfixed, out of scope): Case Studies row-click drill-in has no scroll-into-view feedback**

The one capability this iteration ships — the Case Studies panel becoming visible — is excellently
discoverable (1 click from home, on-screen in the first viewport, browser-verified UT-01/UT-16). The
**drill-in interaction**, however, renders immediately after the currently-rendered table rows; with
the table unfiltered at its default **~1,758 rows** the drill-in panel lands ~65,000px below the page
top. There is no auto-scroll-to-drill-in, no toast, and no inline expand/collapse, so a first-time
user who clicks a row near the top of the page (without first filtering) sees no change anywhere near
their cursor and will reasonably conclude the click did nothing. The data underneath is byte-correct
and the drill-in is provably reachable by manual scroll or by filtering (the prominent Symbol/Reaction
filters collapse the distance immediately). This is a pre-existing era-5B/5C condition, now user-facing
for the first time as a direct consequence of this iteration's flag flip. The ux-regression reviewer
independently caught this (`reports/phase-goal-clean_slate-iter-5-ux-regression.md`,
UX-REGRESSION-WARN) and I confirmed the drill-in wiring is genuinely correct (row `onClick={onSelect}`
at page.tsx:678 → drill-in state → `data-testid="case-drillin"` at :748). Recommendation logged for a
future iteration: scroll-into-view on row click (or inline expansion / pagination).

### Test Findings

**T1 — OBSERVATION: the QA-agent report soft-passes several browser TCs it did not personally exercise**

`reports/qa/goal-clean_slate-iter-5-qa.md` marks TC-06/TC-07/TC-08 as "Not directly tested" /
"Deferred" and TC-10 as "Drill-in control confirmed present and ready to interact" (i.e., it did not
itself click a row and observe the drill-in), yet still records PASS for all of them. That report by
itself overstates its own coverage. The finding is only OBSERVATION-level because the *authoritative*
browser evidence — the browser-qa-agent's `reports/phase-goal-clean_slate-iter-5-ui-test-results.md`
(20/20 PASS) — DID genuinely exercise every one of these: UT-04 clicks a Case Studies row and confirms
the drill-in appears with matching data (and re-clicks row 2), UT-10 switches the timeframe and reads
the updated caption, UT-11 measures live bar movement over 8s, UT-12 verifies Stop on a clean isolated
retest. Acceptance for J-05 is therefore soundly evidenced; the QA report's wording is just weaker than
the actual verification performed. Informational only.

---

## 3. Domain Assessment

The core domain question for this iteration is not algorithmic (no engine/strategy/fingerprint math
changed — `git diff` on the guard/chart-guard suites and both chart components is empty, and the live
fingerprint reads the pinned `08e471b10130e1e2`) but *product-integrity*: does the demolished two-page
product genuinely stand, and is the one restored surface honest?

On honesty and explicit failure handling the iteration is strong. Every Case Studies sub-state is real
and honest: loading, unavailable ("Backend unreachable — is the API running?" + "Nothing cached and
nothing fabricated is shown in its place." — browser-verified with the backend actually killed, UT-07),
true-empty, no-match ("No events match these filters.", UT-06), populated, and the drill-in's honest
"No recorded tape for this event." fallback (UT-04). The Edge Report shows its honest "Edge report not
computed yet." + Compute/Cancel state (UT-08). Ambiguous/absent data is surfaced honestly throughout —
nothing is fabricated. The single source of truth is respected (Case Studies reads verbatim from
`GET /research/setups`; the framing copy says so and it is true).

The one real domain defect is completeness of deletion (B1): the demolition removed the reachable
surfaces (routes 404, modules physically gone, MCP down to exactly 15 tools, nav down to 2, frontend
components/types/api trimmed — all independently confirmed) but left five inert schema classes behind.
The product still "stands," but the demolition is 99%-complete rather than the grep-provable 100% the
era's foundation invariant demands, and the sentinel's close-out reported it as clean.

---

## 4. Fixes Applied During This Audit

**None.** No source file was modified during this audit. This is a deliberate, scope-respecting
decision, not an omission:

| # | Finding | Why NOT fixed in-audit |
|---|---------|------------------------|
| B1 | 5 orphaned body-model classes in `routes.py` | The fix is a **backend source edit**. This iteration's defining, multiply-stated, and *already-verified* contract is "exactly one file touched (`apps/frontend/app/structure/page.tsx`), zero backend source changes" (IN SCOPE, OUT OF SCOPE, plan, and DoD checkbox TC-15). OUT OF SCOPE is explicit: "Re-implementing or re-litigating J-01–J-04's own code — this iteration only RE-VERIFIES them." Completing iter-1's demolition is exactly that. An auditor edit to `routes.py` would itself become the scope-drift the auditor exists to prevent, and would falsify TC-15/TC-1's "zero backend files changed" verification. Correct remedy: a dedicated, surgical cleanup iteration. |
| F1 | Drill-in scroll-into-view | Pre-existing era-5B/5C condition; the spec explicitly scopes this iteration to a pure gate flip ("only its rendering gate changes"; "no new handler"; "no restyle"). A scroll/affordance change is new UI behavior = out of scope. GAP-level, logged as a future follow-up (matches the ux-regression reviewer's own recommendation). |
| T1 | QA report wording | OBSERVATION-level; the actual verification exists in the browser-qa report. Nothing to fix in code. |

Post-audit self-verification performed (read-only, since no fix was applied): full suite re-run by me
(1167 passed / 7 skipped / 0 failed / exit 0); `git status` shows the working tree still touches only
`apps/frontend/app/structure/page.tsx` under `apps/` plus testing artifacts under `runs/`/`reports/`
— the audit introduced no diff of its own.

---

## 5. Recommended Next Step

**Accept this iteration** — its own primary deliverables (Case Studies restored and browser-verified
functional, full-suite-green regression under the new pin, kept-surface browser walk, historical
records untouched, exactly-one-file product scope) are genuinely met and independently re-verified.
J-05's acceptance (drill-in opens with correct/honest data) is satisfied; F1 and T1 do not block it.

**Then schedule a small, dedicated demolition-cleanup change** (a separate iteration, NOT folded into
this sentinel) to remove the five orphaned classes `ThesisRequest`, `ResolveRequest`, `ActionRequest`,
`StudyRequest`, `ReviewRequest` from `apps/backend/app/research/routes.py` (lines 85, 103, 112, 122,
208), then re-run the full suite. This finally makes the demolition grep-provably complete per the
"deletion is complete, never cosmetic" anti-goal.

**Lesson to carry forward** (for the closure/coherence lanes and any future "complete-deletion"
inventory close-out): a grep-provable deletion audit must also grep for orphaned request/response
*models* (and other schema/helper symbols) of the deleted routes — not only the deleted module
imports, the route 404s, the MCP tool list, and the nav rows. Route-handler deletion can silently
leave the handler's Pydantic body/response classes behind as dead code, as it did here across five
iterations. Optionally, add a source-introspection guard test that asserts every `BaseModel` subclass
in `routes.py` is referenced by at least one live route.
