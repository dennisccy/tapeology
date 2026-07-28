# Phase goal-desk-iter-13 — UX Regression Review

**Date:** 2026-07-28

**Verdict:** UX-REGRESSION-WARN

---

## Summary

This iteration made **zero product/application code changes** — independently reconfirmed via
`git diff --stat -- apps/backend/app apps/frontend` (empty output) and `git status --porcelain`
(only `docs/handoffs/`, `docs/phases/`, `reports/`, `runs/`, and `README.md`/dispatch/telemetry
process files touched). At the running-application level this is therefore a clean, uneventful
iteration: nothing a user can reach changed, and nothing regressed.

However, this iteration's *entire purpose* was to produce one specific artifact — a `[NEW]`-flagged
demo-narrator walkthrough proving the `/desk` Top-up Runs panel discloses its full lifecycle
"end to end" (`docs/goal.md:616`), after two prior iterations (11: `CONTINUE`, 12: `ESCALATE`)
already failed to close this exact clause. Having read the actual produced artifact
(`reports/phase-goal-desk-iter-13-demo.json`, `-demo-script.md`, `-demo-results.md`, and the
rendered `reports/demo/goal-desk-iter-13/step-0*.png` images) rather than only the upstream reports
that describe it, I find it **does not contain the honest-empty state at all** — only the populated
state is shown, despite both captures existing on disk and being explicitly handed off for exactly
this assembly. This is a WARN, not a FAIL: it does not affect the live product (the empty state is
genuinely present and reachable in the running app, confirmed by browser-QA), but it is a material,
specific gap in this iteration's own deliverable that no upstream report in this iteration's own
pipeline (review, QA, ui-impact-analyst) has yet caught, because all of them ran before the
demo-narrator lane produced its output. Full detail below.

---

## New Capability Discoverability

**No new capability was added this iteration** (confirmed: `reports/phase-goal-desk-iter-13-user-visible-changes.md`
"What Users Can Now Do: None"; zero diff on all 16 named product files). Nothing to assess for new
navigation paths.

The pre-existing capability this iteration re-verifies — the `/desk` "Top-up Runs" panel, shipped
iteration 11 — remains discoverable exactly as before:

- **Navigation path:** Home (Cockpit `/`) → **Desk** nav link (1 click) → plain scroll to the last of
  6 sections. No tab, toggle, or hidden control. Re-confirmed live this iteration by browser-QA
  (`UT-01`, `UT-14` in `reports/phase-goal-desk-iter-13-ui-test-results.md`): "Top-up Runs" is the
  final heading reached by ordinary scroll, same as every other section on the page.
- **Label clarity:** unchanged, no new labels introduced.
- **Visual feedback:** unchanged; the panel's own independent fetch/poll behavior (from iteration 11)
  was not touched.

No hidden or undiscoverable capabilities found in the running application.

---

## Regression Risk

`ui-surface-map.md`'s "Changed-File Classification" table lists zero files in the
`frontend-direct`/`backend-api`/`full-stack` categories — every file this iteration touched is
documentation or an evidence screenshot outside `apps/backend/app/` and `apps/frontend/`. I
independently re-ran `git diff --stat -- apps/backend/app apps/frontend` myself rather than trusting
the report's claim, and it returns no output, confirming zero intersection with any shared component
prior features depend on (`apps/frontend/app/desk/page.tsx`, `lib/api.ts`, `lib/types.ts`,
`StructureChart.tsx`, `PriceChart.tsx`, `desk_routes.py`, etc. — all byte-unmodified).

| Shared surface | Prior feature(s) it serves | This iteration's change | Risk |
|---|---|---|---|
| `apps/frontend/app/desk/page.tsx` (all sections) | J-01, J-02, J-03, J-04, J-05, J-08, J-09 | None — zero diff | None |
| `apps/frontend/lib/api.ts` / `lib/types.ts` | Every fetch on `/desk`, `/structure`, `/` | None — zero diff | None |
| `StructureChart.tsx` / `PriceChart.tsx` | J-05 drill-in, J-07 sentinel chart | None — zero diff | None |
| Nav bar (Cockpit / Structure / Desk) | All journeys | None — zero diff; UT-01/UT-10 reconfirm all 3 links present, Desk `aria-current="page"` | None |

**Explicit regression evidence (not just inferred from the empty diff):** the smoke-replay set
(`reports/phase-goal-desk-iter-13-smoke-replay-results.md`) reports J-01–J-05, J-07, J-08 all PASS,
0 failed steps, on the final reported run; browser-QA independently re-walked the same 7 journeys
live and confirms the same (22/23 tests PASS, 1 SKIP for J-06's no-browser-surface reason, 0 FAIL).
One already-disclosed, already-investigated item, carried forward rather than newly flagged by me:
browser-QA's `UT-12`/`UT-J-07` note that the `tradable-map-chart-caption` test-plan wording is looser
than its literal DOM text (the "300.11" figure is genuinely on the page, just in the tradable-map
table and chart overlay rather than literally inside that one paragraph's text) — QA traced this to
`demo_runner.py`'s existing target/text-independent matching behavior, pre-existing and unrelated to
any file this iteration touched (`StructureChart.tsx` carries zero diff). Not a regression; no action
needed from this review.

No potential regressions found.

---

## UI vs Backend Parity

No backend capability changed this iteration (zero diff on `desk_topup_log.py`,
`desk_topup_compute.py`, `desk_routes.py`, and all other named backend files), so there is no new
backend surface to check against the UI. The already-shipped `GET /research/desk/topup/runs`
contract's fields all remain rendered exactly as iteration 11's own UX regression review already
verified field-by-field (`reports/phase-goal-desk-iter-11-ux-regression.md`, "UI vs Backend Parity").

**Where a real gap exists is not in the live UI, but in this iteration's own showcase artifact** —
which is close enough to "UI vs backend parity" in spirit (does the evidence surface what the backend
already proves end to end?) that I am flagging it here in detail, then again under Flags below.

### The `[NEW]`-flagged J-09 walkthrough omits the honest-empty state entirely

This iteration's stated goal (`docs/phases/goal-desk-iter-13.md` GOAL, DEFINITION OF DONE bullet 1,
TC-4) and `docs/goal.md:616`'s own acceptance text all require the walkthrough to show, **in one
artifact, in sequence**, both (a) the honest "No top-up runs recorded yet." state and (b) the
populated state. The developer lane produced both raw captures correctly, in the correct order, on
one never-restarted rig (`docs/handoffs/goal-desk-iter-13-dev.md` §5 and §7:
`UT-J-09-empty-fullpage.png` / `-empty-topup-section.png` captured first, `-populated-fullpage.png` /
`-populated-topup-section.png` captured second) and explicitly handed off assembly to the
demo-narrator lane (dev handoff "Known Issues": *"the demo-narrator lane owns assembling the
`[NEW]`-flagged walkthrough JSON from the developer's two same-rig captures"*).

I read the actual assembled output — `reports/phase-goal-desk-iter-13-demo.json`,
`reports/phase-goal-desk-iter-13-demo-script.md`, `reports/phase-goal-desk-iter-13-demo-results.md`,
and opened the rendered images in `reports/demo/goal-desk-iter-13/` — rather than trusting the
"Demo Verdict: RECORDED" label. Findings:

- The only steps tagged `"journey": "J-09"` are `n:2`, `n:3`, `n:4` (demo.json lines 21–64). All
  three are **live click actions against the already-populated rig** (`desk-topup-runs-table`,
  `desk-topup-run-latest-detail`, `desk-topup-run-latest-failed`) — every one captures the populated
  state only. I opened `reports/demo/goal-desk-iter-13/step-02.png` directly: it shows the 3-row run
  table (`done 404/404`, `cancelled 3/404`, `done 404/404`) and the latest-run detail block — the
  same populated view as `UT-J-09-populated-topup-section.png`, not the empty view.
- Neither `UT-J-09-empty-fullpage.png` nor `UT-J-09-empty-topup-section.png` (the two pre-existing,
  correctly-sequenced honest-empty captures the dev lane produced specifically for this purpose) is
  referenced anywhere in `demo.json`, `demo-script.md`, or `demo-results.md`. `grep -n "empty"` across
  all three files returns only prose inside step 2's narration text — no step, screenshot, or `expect`
  clause represents the empty state.
- **Step 2's own narration/screenshot pairing is internally inconsistent**, which is sharper than a
  mere omission: the narration reads *"A brand-new Desk starts with no runs recorded — an honest,
  empty starting point. From the very first run onward, every result is saved for good..."* — but the
  screenshot attached to that exact step shows 3 runs already recorded, 404/404 pairs attempted, one
  failure. A viewer of this walkthrough reads a claim about an empty starting point while looking at a
  populated table. This is the precise failure mode `docs/phases/goal-desk-iter-13.md` TC-4 itself
  warns against: *"narration matching what each paired screenshot actually shows (no claim
  unsupported by the image next to it)."*
- **Likely root cause, for whoever picks this up:** `demo-results.md` states this run used
  `demo_runner.py`'s **record** mode against a live browser. By the time the demo-narrator lane runs
  (after dev, review, ui-impact-analyst, ui-test-designer, and browser-qa-agent, per full-depth
  ordering), the rig's honest-empty window has already permanently closed — checkpoint 1 was recorded
  hours earlier (dev handoff §6, timestamps in the `topup-2026-07-28-*` run ids). A live "goto /desk"
  step executed now can only ever show the current (populated) state; it cannot re-derive the empty
  state by driving the browser. The only way to include real empty-state evidence in this artifact is
  to splice in the pre-existing static screenshot as a non-live step, which none of the three files
  do. This is the same one-way-door constraint browser-QA's own `UT-05` explicitly worked around by
  "reviewing, not recapturing" the archived screenshots — the demo-narrator lane needed the equivalent
  accommodation and, on this evidence, did not apply it.

**Why this matters enough to flag rather than note in passing:** this is the third consecutive
iteration built specifically around closing this one clause (iteration 11: `CONTINUE`; iteration 12:
`ESCALATE`, the session's first). Every other required condition this iteration set out to fix
(depth=full so the lane runs before the evaluator; capture order so both states exist on one
never-restarted rig) was verified and holds. But the one output the whole exercise exists to produce
— "both captures in sequence, in ONE artifact" — is not, on the evidence I can see, actually true of
what shipped. None of `reports/reviews/goal-desk-iter-13-review.md` (ran before the demo-narrator
lane), `reports/qa/goal-desk-iter-13-qa.md` (marks TC-04 explicitly `PENDING`/deferred, does not
independently verify it), or `reports/phase-goal-desk-iter-13-user-visible-changes.md` (written before
`phase-goal-desk-iter-13-demo.json` existed, says the assembly "has not yet happened") checked the
demo-narrator's actual output against TC-4 — this review is the first pipeline stage to do so.

---

## Flags

### Hidden Capabilities
None. No capability is hidden or unreachable in the running application.

### Undiscoverable Capabilities
None. The Top-up Runs panel (both states) remains 1-click-plus-scroll from home, unchanged from
iteration 11's verified baseline.

### Potential Regressions
None. Zero diff on every shared component; full smoke-replay + live browser-QA regression set both
report 7/7 PASS on J-01–J-05, J-07, J-08, plus J-06's MCP contract independently held (17 tools,
35/35 tests).

### Visual Consistency
No inconsistencies found. Opened `reports/demo/goal-desk-iter-13/step-02.png` and
`reports/qa/goal-desk-iter-13-evidence/UT-J-09-empty-topup-section.png` directly: both use the same
dark/dense/terminal-grade table styling as the rest of `/desk` (same `Panel`/`EmptyState` components,
same header/cell classes, same amber accent for warning/cancelled states) — consistent with iteration
11's original design-system conformance and with every other section on the page. No arbitrary values,
no new visual pattern introduced (expected, since zero frontend code changed).

### Showcase Artifact Gap (this iteration's own primary deliverable)
- **What:** the `[NEW]`-flagged J-09 demo-narrator walkthrough
  (`reports/phase-goal-desk-iter-13-demo.json` / `-demo-script.md` / `-demo-results.md`, and their
  rendered images in `reports/demo/goal-desk-iter-13/`) contains only the populated Top-up Runs state
  (steps `n:2`–`4`). It never shows, references, or captures the honest-empty state, and step 2's
  narration describes the empty state while its attached screenshot shows the populated one.
- **Why it's not "hidden capability" in the canonical sense:** the empty state itself is genuinely
  present and was captured correctly and legibly by the developer lane
  (`UT-J-09-empty-fullpage.png`, `UT-J-09-empty-topup-section.png`, both reviewed and confirmed
  legible by browser-QA's `UT-05`) — the gap is specifically in the assembled walkthrough artifact,
  not in the running product.
- **Action:** the demo-narrator lane (or its next dispatch) should re-open
  `reports/phase-goal-desk-iter-13-demo.json` and add a step before `n:2` that presents
  `UT-J-09-empty-fullpage.png`/`-empty-topup-section.png` as the opening state (a non-live/static
  reference, since the rig's empty window cannot be re-driven live), then keep the existing `n:2`–`4`
  populated-state steps as the "after." Step 2's narration should either move to pair with the new
  empty-state step, or be reworded so it no longer asserts "an honest, empty starting point" next to a
  populated screenshot.

---

## Recommendation

**Primary:** before this iteration is scored against its own Definition of Done / TC-4, re-open the
demo-narrator lane to add the missing empty-state step to
`reports/phase-goal-desk-iter-13-demo.json` (or wherever the walkthrough ultimately lives) using the
already-captured `UT-J-09-empty-fullpage.png`/`-empty-topup-section.png` assets — no new browser
capture or rig work is required, since both raw images already exist on disk from the developer's
correctly-ordered capture this iteration. This is a narrow, low-risk fix (one showcase artifact, zero
product code) but it is the difference between this iteration actually closing J-09's long-outstanding
acceptance clause a third time or leaving it silently unmet in a way that looks closed from the
"RECORDED" verdict label alone.

**Secondary (non-blocking, unrelated to this iteration's own scope):** the carried-forward items noted
in iteration 11's own UX regression review remain unchanged and still non-blocking — `/desk`'s growing
page length (six stacked sections) and the run-table lacking a cap are both explicitly out of scope
for this iteration and require no action here.

No action required on the running application itself — it is unchanged and unregressed.
