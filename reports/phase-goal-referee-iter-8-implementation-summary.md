# goal-referee-iter-8 — Implementation Summary

**Phase:** goal-referee-iter-8
**Date:** 2026-08-15
**Written by:** developer

---

## Features Implemented

- **A "shortlist" of five pre-approved research questions, with live sample-size numbers.** On
  `/desk`, a new "Referee Registry" panel shows the five statistical questions the project
  pre-decided are worth asking about the trading patterns the desk already tracks — for example,
  "does the capitulation reversal pattern actually predict a bounce in the next 5 minutes?" Each
  row shows how much historical evidence already exists for that question (how many occurrences,
  how many trading sessions) and a plain-English sentence explaining why that question was
  chosen.
- **A one-click way to formally register a question for real testing.** The operator can select
  one of the five questions, review its evidence numbers, confirm, and the system permanently
  records that the question is "on the clock" starting today. From that moment forward, only new
  evidence collected after today counts toward answering it — the system can never quietly use
  older evidence to make the answer look better after the fact.
- **A clear label for "before we asked" vs. "after we asked" evidence.** Every registered
  question now shows two separate counts: how much matching evidence existed *before* it was
  registered (labeled "discovery (exploratory)" — this is what inspired the question, but it
  never counts as proof) and how much has accrued *since* (the count that will eventually
  determine the answer).
- **Two safety fixes to the statistics engine's write path.** (1) If the engine's own internal
  self-check ever fails right when it's about to record a permanent verdict, it now refuses to
  record that verdict at all — previously the failure was only caught when someone later tried
  to *read* the verdict, meaning a bad verdict could already be permanently on file. (2) If one
  of the recorded question files on disk ever becomes corrupted, the system now says so plainly
  in its report instead of silently pretending that question doesn't exist.

## Changed Behavior

None. This is purely additive — every previously shipped screen, table, and number on `/desk`,
`/structure`, and the cockpit works exactly as before.

## Backend-Only Items

None this iteration — every backend addition has a corresponding piece of the new UI.

## Incomplete Items

- **The operator's own real 2–3 question registrations were not made.** This was explicitly
  optional for this iteration (the spec's own acceptance criteria treat "operator hasn't acted
  yet" as a valid, honest state, not a failure) — the shortlist and the empty registered-questions
  list are both confirmed working against the real system today. The operator can register real
  questions themselves whenever ready, using the new "Referee Registry" panel on `/desk`.
- **A full click-through browser test of the new panel** (selecting a question, confirming, and
  seeing it appear in the list) has not yet been run — that verification step runs next in the
  pipeline, not as part of this build step.

## Config and Environment Changes

None. No new environment variables, no new configuration, no database migration. The system's
internal "fingerprint" (a hash proving nothing behavioral changed under the hood) is confirmed
unchanged.

## Known Limitations

- Two of the five readiness numbers the system tracks internally (a per-question sample-size
  floor and a target number of trading sessions) are not shown as their own columns in the new
  table — only the four numbers most useful for a quick read (occurrence count, session count,
  accrual rate, and estimated days until enough evidence has accrued) are shown. This was a
  deliberate choice to keep the table simple; the underlying numbers are still recorded and
  available if a future update wants to surface them.
- If the operator selects a question that (unbeknownst to them, e.g. from another browser tab)
  was already registered a moment earlier, the system will show a plain error message rather
  than silently succeeding or silently failing — this is by design, matching how every other
  action on this page already handles conflicts.
