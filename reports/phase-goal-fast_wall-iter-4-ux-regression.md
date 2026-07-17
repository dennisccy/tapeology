# Phase goal-fast_wall-iter-4 — UX Regression Review

**Date:** 2026-07-17

**Verdict:** UX-REGRESSION-WARN

---

## New Capability Discoverability

**Capability: "Compute edge report" button on `/structure`'s Edge Report section.**

- **Navigation path:** Home (Cockpit, `/`) → **Structure** nav-bar link → scroll to the "Edge Report"
  panel (3rd of 6 sections: Tradable Map, Case Studies, **Edge Report**, Fetch from Yahoo Finance,
  Registry, Comparison). That is **1 click** from home — `/structure` was already a top-level,
  backend-driven nav entry (`components/NavBar.tsx` renders links from `GET /meta/ui-routes`; the
  approved nav skeleton in `runs/goal-session-fast_wall/state/blueprint.md` lists
  `└── Structure /structure (Tradable Map · Case Studies · Edge Report)`). No new nav entry was
  added — correct, since the plan/goal.md explicitly anti-goal this ("No new nav entries or
  pages") and the button lives inside an already-linked page.
- **Label clarity:** "Compute edge report" / "Computing…" / "Retry compute" is unambiguous for this
  app's operator persona and matches the spec's own terminology exactly — verified directly against
  `apps/frontend/app/structure/page.tsx:299-351` (`NotComputedPanel`).
- **Visual feedback:** Confirmed at the code level — a progress line
  (`{backtests_done} / {backtests_total} backtests`), a distinct red error line for a failed job vs.
  a distinct red line for a client-side trigger failure, and a disabled/relabeled button while
  running. The button and panel reuse the exact pre-existing amber degraded-state container and the
  exact `structure-load-button` Tailwind classes byte-for-byte (verified via `git diff` — zero new
  classes, zero new colors introduced).
- **Gap — no live screenshot exists anywhere in this phase's pipeline.** I attempted to independently
  verify the rendered button via Chrome MCP myself (`list_tabs`) and got the identical failure every
  prior agent this iteration reported: `"Chrome did not become ready on port 9222 within 15000ms"`.
  This is now the **third** independent agent (developer, browser-qa/QA, and this review) to hit the
  exact same failure signature in this environment, which strengthens the case that this is a
  session/sandbox-level infrastructure constraint, not per-agent flakiness. As a result, "is there
  visual feedback when the capability is used" is answered by strong code-level and live-backend
  HTTP evidence (curl-verified full trigger → running → done/failed cycle against a real scoped
  backend, per the dev handoff), but **not by an actual observed render**. Per this project's own
  established discipline ("no screenshot ⇒ unknown, never passing"), this capability's visual
  discoverability should be treated as **unknown-but-well-evidenced**, not confirmed.
- **QA report overclaim (correcting the record for the auditor):** `reports/qa/goal-fast_wall-iter-4-qa.md`'s
  "UI Evolution Audit" asserts `Reachability: PASS` and `Visibility: PASS` citing "SSR HTML confirms
  the button is wired into the page structure at mount (no client-side-only render, button
  accessibility verified by testid presence)." I traced this directly: `structure/page.tsx`'s
  `edgeReportResult` state initializes to `useState<...>(null)` and is populated only inside a
  `useEffect` that runs post-mount, client-side, after `fetchEdgeReport()` resolves
  (`page.tsx:1249,1328-1339`); the Edge Report section's own render branch shows `LoadingPanel
  testid="edge-report-loading"` whenever `edgeReportResult === null` (`page.tsx:1978-1979`) — i.e.
  the actual pre-hydration SSR HTML can **only** ever contain the loading skeleton, never the
  `edge-report-compute-button` testid the QA report claims it verified. This matches what the more
  careful `ui-test-results.md` independently found via a raw `curl` of the SSR HTML ("confirmed it
  renders only the `edge-report-loading` skeleton in the raw curl HTML"). The QA report's "UI-PASS"
  verdict is therefore not supported by the evidence it cites for Reachability/Visibility — it is a
  reasonable inference from the code (which I also independently confirm is correctly wired), but it
  is not the visual confirmation it is phrased as. This does not change my verdict on the capability
  itself (the code is right), but the auditor should not treat QA's "UI-PASS" as a substitute for an
  actual browser observation.

**Assessment: discoverable-by-design, code-and-API-confirmed, not yet visually confirmed.** This is
a WARN-level gap, not a FAIL — the navigation path, label, and rendering logic are all directly
verifiable in source and are correct; what's missing is a literal screenshot, and that gap is an
infrastructure limitation disclosed honestly by every agent in this phase (except QA's specific
Reachability/Visibility framing, corrected above).

---

## Regression Risk

| Shared component | Prior feature it serves | This iteration's change | Risk |
|---|---|---|---|
| `NotComputedPanel` (`structure/page.tsx`) | J-01 (era-fast_wall): frozen "Edge report not computed yet." headline/detail/register render | Gains `compute`/`onTriggerCompute`/`triggering`/`triggerError` props, a button, a progress line, two error lines | **Low.** Verified via `git diff`: the headline (`<p>Edge report not computed yet.</p>`) and detail (`<p>{detail}</p>`) lines are byte-unchanged; every new element is appended below them and is conditionally rendered (`isFailed`, `triggerError`, `isRunning` are all false in the untouched cold state), so a page that has never had a compute run shows the identical headline/detail text plus one new, always-idle, enabled button. This is the intentional, documented evolution of J-01's dead-end panel into an actionable one — not a regression. |
| `StructurePage`'s mount `useEffect` (`fetchEdgeReport().then(...)`) | J-01's initial fetch-and-render | Gains one additional line seeding `computeSnapshot` from the response's `compute` field | **Low.** Purely additive; `setEdgeReportResult(result)` (the only thing J-01/J-07 depend on) is unchanged. |
| `EdgeReportNotComputed.compute` type (`lib/types.ts`) | J-01's typed payload | Widened from a `null`-only literal to `EdgeReportComputeSnapshot \| null` | **Low.** Grepped the entire frontend for consumers of `EdgeReportNotComputed`/`EdgeReportComputeSnapshot` — they exist in exactly 3 files (`api.ts`, `types.ts`, `structure/page.tsx`), all touched intentionally this iteration. No other page or component reads this type, so the widening cannot silently break an unrelated consumer. |
| `/structure`'s other 5 sections (Tradable Map, Case Studies, Fetch from Yahoo Finance, Registry, Comparison) | Eras 1–5B, yahoo_fetch, structure_ui, tradable_wall | None | **None.** `git diff` for `structure/page.tsx` shows the only render-call-site change is the `NotComputedPanel` invocation; no other section's JSX or state was touched. |
| `NavBar.tsx`, Cockpit (`/`), `/journal`, `/studies`, `/performance` | J-51/structure_ui-era nav skeleton, all prior journeys | None | **None.** `git status --short` confirms zero diff on any of these files this iteration. |
| J-02 (`bars.py`/`datasets.py`/`dataset_index.py`), J-03 (`levels.py`/`tradability.py`/`backtests.py`'s arm memo) | Backend accelerators, no dedicated UI panel | None | **None.** Confirmed zero diff via `git status`; these are backend-only journeys with no frontend surface to regress. |

**J-07 regression-sentinel FAIL signal — investigated and resolved as a false positive.**
`reports/phase-goal-fast_wall-iter-4-regression-replay-results.md` (the deterministic Playwright
golden-replay) reports `UT-J-07: FAIL — step 03 expected "buyer_control" did not appear`, with
evidence at `reports/qa/goal-fast_wall-iter-4-evidence/J-07-verify.png`. I viewed this screenshot
directly: it shows the Cockpit page with **"Backend unreachable — is the API running?"** in red and
**"navigation unavailable — backend unreachable"** in the nav bar — i.e., the Watch action never
reached a live backend at all, so "buyer_control" (a tape-state label that only appears once live
data streams in) had no way to appear. This is a backend-connectivity failure, not a tape-reading
logic defect. Corroborating evidence:
- File timestamps: `J-07-verify.png` and `regression-replay-results.md` were written seconds apart
  (14:37:55), confirming the screenshot was produced by *this* replay run, not stale evidence from
  an earlier iteration.
- The task-assigned backend at port 8301 was unreachable at the start of my own review session too
  (connection refused), and the LLM browser-qa report independently found the same backend's log
  showed one `GET /health 200` immediately followed by a shutdown.
- This iteration's diff touches zero cockpit/tape-state files on either side (backend:
  `edge_report_compute.py`, `edge_report.py`, `routes.py`; frontend: `structure/page.tsx`, `api.ts`,
  `types.ts` — none of which the Cockpit page or its tape-watch flow import).

**Assessment: not a genuine regression, but not a re-confirmed PASS either** — it rests on strong
circumstantial evidence (screenshot content + timestamps + logs + diff scope), not a clean re-run
against a live backend. Flagging for the auditor to either accept this reasoning or re-run J-07's
golden replay once a backend is confirmed reachable, rather than carrying an open "FAIL" against the
regression sentinel into phase closure without explanation.

---

## UI vs Backend Parity

| Backend capability (this iteration) | UI exposure | Assessment |
|---|---|---|
| `POST /research/edge-report/compute` (trigger, single-flight) | "Compute edge report" / "Retry compute" button | Exposed |
| `GET /research/edge-report/compute` (poll snapshot) | Progress line + mount-time state resume | Exposed |
| Failed-job `error` string | Red error line, verbatim | Exposed |
| Trigger-POST-itself failure (e.g. unreachable backend) | Separate red line, distinct from a failed job | Exposed |
| Finished report (`state: "done"`) | Falls through to the pre-existing `EdgeReportBody` render | Exposed (reuses, not duplicates, existing rendering) |
| `POST /research/edge-report/compute/cancel` | **No UI control anywhere.** `cancelEdgeReportCompute()` exists in `lib/api.ts`, fully implemented and tested, but no button calls it. | **Backend-only this iteration — intentional, not a gap.** The plan's own "UI Evolution" section names only the trigger button; goal.md's J-04 scope and three independent handoffs (dev, frontend, implementation-summary) all disclose this identically as deliberately deferred, not an oversight. By the skill's literal definition this is a "hidden capability" (exists, no nav/UI path), so I record it here for completeness, but it does not warrant a blocking flag — it is consciously scoped, consistently documented, and reachable via direct API call for the rare case an operator needs to stop a job (a research-tool, not consumer-product, context). |
| `force: true` (recompute over a warm key) | **No UI control.** Backend route and CLI `--force` both support it; the browser button always sends `force: false`. | **Intentional, documented, matches plan scope exactly.** Same reasoning as cancel. |
| `backtests_from_cache` progress field | Code path exists (`"(N from cache)"` annotation) but is permanently `0` this iteration (no sub-cache exists until J-05) | **Not a gap** — there is nothing to display yet; this is correctly a forward-compatible placeholder, not dead UI. |
| CLI warmer (`python -m app.research.edge_report_compute`) | None — terminal-only by design | **Correctly out of UI scope.** goal.md positions this as a parallel, unattended operator tool, not a browser feature; it shares the same cache the button reads from, so a CLI-warmed result appears in the UI automatically on next load. Not a "hidden" capability in the discoverability sense — it was never meant to have a button. |

**Overall parity is strong.** Every capability the phase spec's "New user actions"/"New information
displayed" sections call for has a real, correctly-styled UI counterpart. The three items with no UI
control (cancel, force, CLI) are all explicitly out of this iteration's scope per the plan, the phase
spec, and goal.md's own dependency-order reasoning (J-04 ships the button; J-05 gives `force`-adjacent
and cache-annotation behavior real teeth) — this reads as deliberate incremental delivery, not
backend racing ahead of a UI that never catches up.

---

## Flags

### Hidden Capabilities
- **Cancel-in-flight-compute** — `POST /research/edge-report/compute/cancel` and
  `cancelEdgeReportCompute()` exist and are fully tested, but no button or control in
  `structure/page.tsx` calls it. Non-blocking: explicitly out of this iteration's scope per the plan,
  consistently disclosed across three handoffs. Recorded here per the skill's definition, not as an
  action item for this phase — worth a nav/UI entry point in a future iteration if operators
  routinely need to abort a long sweep before J-05's parallelism ships.

### Undiscoverable Capabilities
- None. The one new capability this iteration ships (the compute button) is reachable in exactly 1
  click from home and sits inside the page/section the blueprint pre-registers as its home — no
  capability requires >2 clicks or obscure navigation.

### Potential Regressions
- **J-07 golden-replay FAIL (`UT-J-07`, `reports/qa/goal-fast_wall-iter-4-evidence/J-07-verify.png`)**
  — investigated in depth above; assessed as a backend-unreachable-at-replay-time false positive, not
  a product regression, based on the screenshot's own content (explicit "Backend unreachable" /
  "navigation unavailable" text), matching timestamps, corroborating backend logs, and a diff that
  touches zero cockpit/tape-state files. Recommend the auditor either accept this evidence chain or
  require one clean re-run once a backend/Chrome-MCP-capable session is available, rather than
  silently carrying an unexplained sentinel FAIL past phase closure.
- No other shared-component regression risk found — the full diff for every touched frontend file
  was traced line-by-line against every prior-phase feature's owned surface (see table above); all
  other `/structure` sections, the nav bar, and every other page have zero diff this iteration.

### Visual Consistency
- New elements (button, progress line, two error lines) reuse existing patterns byte-for-byte: the
  button copies `structure-load-button`'s exact Tailwind class string; the panel container is the
  pre-existing `UnavailablePanel`/not-computed amber treatment (`border-amber-800/60
  bg-amber-900/20`); the error lines use `text-red-300`, matching the same page's pre-existing
  `comparisonError`/`fetchError` red-line precedent. Confirmed directly via `git diff` — zero new
  colors, zero new component patterns, zero arbitrary Tailwind values introduced.
- This project's `.claude/project-template.md` DESIGN SYSTEM section is the unfilled generic
  template (placeholder color/typography values, not project-specific ones), so there are no
  project-defined design tokens to check against directly — I instead verified consistency against
  established sibling patterns on the same page and prior-phase conventions, which is what the phase
  spec's own "Visual Requirements" section (reuse `structure-load-button`, reuse the amber container,
  "no new visual language") explicitly commits to and what the diff delivers.
- No visual inconsistency found.

---

## Recommendation

1. **Non-blocking, carry forward:** close the Chrome-MCP verification gap before or during the next
   browser-dependent iteration. Three independent agents in this phase (developer, QA/browser-qa, and
   this review) hit the identical `"Chrome did not become ready on port 9222"` failure — this is
   very likely an environment/session-level issue worth a direct fix (or a documented workaround)
   rather than continuing to retry per-agent. Until resolved, treat every "browser-verified" claim in
   this phase's reports as code-and-API-evidenced, not visually confirmed.
2. **Non-blocking, informational for the auditor:** `reports/qa/goal-fast_wall-iter-4-qa.md`'s "UI
   Evolution Audit" Reachability/Visibility "PASS" claims cite SSR HTML evidence that, per the page's
   own client-fetch architecture, cannot actually contain the button (SSR only ever emits the
   `edge-report-loading` skeleton for this section). The underlying capability is still correctly
   implemented (verified directly against source), so this does not change my verdict, but the claim
   itself should not be relied on as a substitute for a real screenshot.
3. **Non-blocking, informational:** the J-07 golden-replay "FAIL" is very likely a false positive from
   a backend that was down at replay time, not a product regression — see evidence above. Worth one
   clean re-run when a browser session is available, but no product fix is indicated.
4. **No action required** on UI vs. backend parity — the cancel/force/CLI gaps are all intentionally
   scoped out of this iteration and consistently documented; they are natural candidates for J-05 or a
   later iteration's UI Evolution section, not defects of this one.
