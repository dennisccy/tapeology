# goal-i_will_be_super_rich_with_my_loved_ones-iter-9 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-9
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

The thesis strip gains an honest **active-but-not-evaluated** presentation variant for a surviving
entry-marked position (J-47), and the `/` cockpit surface keeps the strip rendered after Stop when a
marked thesis survives. All copy is read VERBATIM from the backend projection — the frontend infers
no lifecycle state and composes no notice text.

- **`NotEvaluatedThesis` strip variant** (`components/ThesisStrip.tsx`): when the projection's
  `monitor_status === "not_evaluated"`, the strip renders the surviving thesis — setup / direction /
  invalidation (mono), recorded marks (entry/exit price + realized R in R units only), the bound
  source + feed stamp, a neutral (slate) "⏸ not evaluated" chip (NOT a live green/red verdict), and
  the backend-owned `monitor_notice` line rendered verbatim. No live verdict chip, no statement
  statuses (they would be misleading off-stream), and NO mark/resolve controls (those need a live
  tape). This same variant renders both the not-currently-evaluated notice and the mismatched-source
  notice (both arrive as `monitor_notice`).
- **Post-stop survival fetch** (`app/page.tsx`): after a Stop, the page reads
  `GET /research/thesis/active?ticker=` for the stopped ticker (new `fetchActiveThesis` helper). If an
  entry-marked thesis survives (`monitor_status: "not_evaluated"`), the strip stays on the cockpit
  surface (above the idle declare line) instead of dropping to the bare idle screen — a real position
  is never silently dropped. An unmarked thesis auto-expired backend-side, so the read returns null
  and the idle screen shows as before. The surviving thesis is cleared the instant a new watch starts
  (the live WS `thesis` key becomes the source of truth again) or the source mode changes.
- **Re-attach renders live again automatically**: re-watching the bound source restarts the WS, whose
  `thesis` key carries an `ok` projection again, so the strip returns to its normal live
  `ActiveThesis` display (verdict chip + statement statuses + mark/resolve controls). The
  `watch_restarted` gap event is visible in the journal timeline via REST (`GET /research/journal/{id}`).
- **Types** (`lib/types.ts`): `ThesisProjection.monitor_status` widened to
  `"ok" | "failed" | "not_evaluated"`; added optional `monitor_notice`.

## Design System Conformance
- Dark instrument-panel surface preserved (`slate-900/60` panel, `slate-800` border) — the same
  `StripShell` as the live strip.
- Color semantics held: the not-evaluated chip is neutral slate (deliberately NOT green/red — the tape
  is not being judged); the notice uses amber (`amber-300/90`), consistent with the unclear/attention
  semantics; realized-R keeps emerald/rose by sign. Monospace for all prices.
- "Descriptive only — not trading advice" stays in frame on the variant.
- Interactive elements unchanged in this variant (it is read-only) — the existing live strip's hover/
  focus/active states are untouched.

## Tests Run
Command: `cd apps/frontend && NEXT_DIST_DIR=.next-iter9-verify npx next build`
Result: compiled + type-checked successfully. (Built into an isolated dist dir to avoid clobbering the
QA harness's shared `.next` / `.next-qa`; the verify dir and the transient `next-env.d.ts`/`tsconfig`
edits were reverted afterward.)

## Known Issues
- Browser pixel verification of the not-evaluated strip (UT-J-47-A/B captures) runs in the qa/browser
  step; the dev-side proof is the clean type-check + the live backend REST flow documented in the dev
  handoff.
- No new user actions were added (no buttons/forms) — this iteration is lifecycle honesty for the
  existing Stop/Watch/declare/mark flows.
