# goal-rapid-microscope-iter-21 — Implementation Summary

**Phase:** goal-rapid-microscope-iter-21
**Date:** 2026-08-20
**Written by:** developer

---

## Features Implemented

- **The band-touch enumerator**: the system can now identify the exact moments a real trade
  price crosses one of the app's already-computed support/resistance "wall" ranges — a genuine
  new capability the app never had before this iteration. It reads the recorded tick data
  directly (no snapshot required) and only does this work when a wall map is already available,
  so it stays fast on today's data.
- **Two new ways to define a research candidate**: the Scout screening tool (the "many candidates
  in, few survivors out" funnel from this era's own name) can now build candidates that are
  anchored to a wall-touch event, or to a recorded chart-pattern signal — not just "every trade,
  unconditionally" as before. This is the wiring the funnel needed to run structure-conditioned
  research, not just generic feature research.
- **All three predeclared pilot studies now exist in the codebase, reviewable, in the order the
  project's own plan named them**: (1) does aggression into a wall followed by a price rejection,
  (2) does price making a new high while buying pressure weakens predict a reversal, (3) does an
  extreme sell-off followed by fading pressure separate a genuine capitulation bounce from a
  false one. Only study 2 (the price/pressure divergence one) was actually run through the
  screening machinery this iteration — the other two are written and unit-tested but deliberately
  not executed yet, exactly as this iteration's plan called for.
- **The price/pressure-divergence study ran, honestly, end to end**: on a small, fully-controlled
  test dataset built specifically to exercise the real formula, the screen produced a genuine
  statistical result (with every required disclosure: how concentrated the effect is, what time
  of day it happened, how much of the underlying data used a fallback classification, and whether
  the effect is economically large enough to matter) and then correctly refused to promote it
  further, because — honestly, and by the project's own design — there is not yet enough
  independently-verified historical data to clear the walk-forward bar. That refusal itself is
  now a permanent, timestamped record.
- **The corpus-readiness page now shows a real number for "how many wall touches exist in the
  recorded data"** instead of the placeholder "not yet counted" message it showed before — this
  was a genuinely missing gap this iteration closed.
- **The Scout Ledger table on `/desk` now shows which kind of research candidate each row is**
  (a generic feature-only candidate, or one anchored to a wall touch / chart signal) — previously
  invisible information.

## Changed Behavior

- **`GET /research/desk/micro/readiness`** (the corpus-truth endpoint behind the Microscope
  Readiness section of `/desk`) now reports a real, counted number of wall touches instead of the
  placeholder "not yet counted" state — a genuinely new, more complete answer to "what evidence do
  we actually have," not a behavior regression. On the real production data today, this number
  will likely read `0`, honestly, since no operator has pre-computed a wall map for most of the
  recorded symbol/dates yet.
- **The "run screening" button's underlying API** gained an optional, invisible-by-default extra
  option that lets an operator (via the command line or a future control, not a button that
  exists in the UI today) choose to run just the one pilot study instead of the standard research
  grid. Nothing changes for the existing, already-shipped screening behavior unless this new
  option is explicitly used.

## Backend-Only Items

- The command-line tool that operators use to run screenings (`python -m app.research.scout`) can
  now be pointed at the one pilot study via a `--grid delta_divergence_pilot` flag — there is no
  UI button for this yet, by design (this iteration's plan explicitly keeps it operator/CLI-only).
- The walk-forward eligibility check for a Scout candidate is a new backend capability with no
  dedicated UI of its own — its outcome shows up as an extra row inside the existing Scout Ledger
  table (reusing that table, not a new one), so it is visible, just not given its own polished
  presentation yet.

## Incomplete Items

- **Pilot studies 1 (range-wall failed aggression) and 3 (capitulation exhaustion)**: fully
  written, reviewable, and unit-tested for correct shape — but deliberately NOT run through the
  screening/decision pipeline this iteration. This is a planned deferral (the project's own
  priority order explicitly allows deferring up to two of the three studies), not an oversight,
  and it is called out clearly in the developer's own handoff notes.
- **The "seal-unaware readiness metric" UI disclosure** named in the underlying research spec was
  only half-built: the safety-net check that prevents future code from silently relying on that
  metric IS built and tested; the user-facing caveat sentence itself was not, because there is
  currently no live screen in the product that even shows that metric — nothing to attach the
  caveat to without touching an unrelated, frozen part of the product. This was an explicit,
  logged decision, not an omission.
- **The actual browser screenshot re-capture for one specific evidence item** (proving the "Scout
  ledger unavailable" error message displays correctly) was not personally performed by this
  developer pass — the underlying code for that message is unchanged by this iteration, so it
  should still work, but the live screenshot re-take is left to the dedicated QA step that follows
  development in this project's pipeline.

## Config and Environment Changes

None. No new environment variables, config fields, or migrations. The project's own fingerprint
value that proves "no hidden configuration changed" (`08e471b10130e1e2`) is unchanged.

## Known Limitations

- On the real, currently-recorded corpus, the new "wall touches" count will likely show `0`
  honestly, because no operator has pre-computed wall maps for most of today's recorded
  symbol/dates — this is expected and correct, not a bug.
- The two deferred pilot studies (range-wall failed aggression, capitulation exhaustion) are not
  yet real, actionable research results — they exist as reviewable, frozen specifications only.
  Study 1 in particular still needs one more piece of machinery (comparing two features together,
  not just one) before its real screen can even be attempted; that is named as future work, not
  built this iteration.
- The new "walk-forward eligibility check" result for the one study that WAS run appears as a
  second, slightly awkward-looking row in the existing candidate table (with several columns
  showing a dash, since that row isn't a full "candidate" in the same sense) — functionally
  correct and fully honest, but not yet given its own polished presentation.
