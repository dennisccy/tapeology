# Phase goal-hypothesis-foundry-iter-3 — Implementation Summary

**Phase:** goal-hypothesis-foundry-iter-3
**Date:** 2026-08-26
**Written by:** developer

---

## Features Implemented

- **A full end-to-end proof run of the Foundry machinery, using made-up test data.** The Foundry is
  built from five separate pieces (the source compiler, the candidate interpreter, the family/quota
  tracker, the trial ledger, and the exhaust runner). Earlier iterations built and tested each piece on
  its own. This iteration is the first time all five pieces were run together, back to back, on one
  practice run that intentionally contains every possible result the system can produce at once: a
  blocked idea, an excluded idea, an aliased idea, a candidate that dies from too little data, five
  candidates that die for each of the five different statistical reasons the system can reject a candidate,
  and one candidate that genuinely survives the screen. Every one of those outcomes landed exactly where
  it should, in the right order, with the right paperwork attached.
- **A "what if the power goes out mid-run" proof.** A 20-candidate practice run was started, stopped
  partway through (simulating a crash), and then restarted from scratch with no memory of where it had
  left off. The system correctly recognized which candidates were already finished and skipped
  re-running them, while still finishing the rest — with no duplicate records and nothing done twice.
- **A "what if a candidate tries to read data it isn't allowed to see" proof.** A practice run was set
  up so that, partway through gathering the information for one candidate, the system hits data marked
  off-limits. The Foundry correctly refuses to write any result for that candidate at all — it does not
  fabricate a pass, a fail, or any other outcome for evidence it wasn't allowed to touch.
- **A record-keeping repair.** If the exhaust process is interrupted and restarted, it was already
  smart enough to notice when a candidate had only been "started" but not "finished," and to check its
  numbers matched before continuing. That same safety check is now also applied to candidates that were
  already fully finished before the interruption — closing a small gap where a finished candidate could,
  in theory, have been resumed with silently different numbers than the ones it actually finished with.
- **Two missing pieces of paperwork added to every source idea's record.** Every ratified idea the
  Foundry tracks now carries (1) a tamper-evident fingerprint of its own cited source text, and (2) an
  explicit note of which other idea(s), if any, it is a legitimate alternate version of. Neither of these
  can be typed in by a person — both are computed/verified automatically so they can never drift out of
  sync with the record they describe.

---

## Changed Behavior

- **Resuming a fully-finished candidate now double-checks its paperwork before handing back the result.**
  Previously, if a candidate had already fully finished, the system would hand back its saved result
  without re-checking that the request asking for it still matched the original conditions. Now it
  re-checks first and refuses (with a clear error) if something has changed. A normal resume, where
  nothing changed, behaves exactly as before.

---

## Backend-Only Items

- Everything in this iteration is backend proof-of-mechanism work — practice/test runs only, using
  fabricated data. There is no new screen or button for an operator to click, and nothing new is shown
  on `/desk` this iteration. This matches the plan: the operator-facing Foundry screen is being built
  later, once the underlying machinery (proven this iteration) and the real list of source ideas
  (next iteration) both exist.

---

## Incomplete Items

- **The real list of 11 source ideas has not been written yet.** This iteration only used made-up
  practice ideas to prove the machinery works. Writing up the real ideas from the existing research
  notes, and running them through the machinery for real, is intentionally left for a later step.
- **No screen to look at this yet.** The Foundry still has no dedicated page/section on `/desk` — that
  is planned for a single later step once the real source ideas exist.
- **The "which files are locked in" list-builder still only looks one folder deep.** This is a known,
  disclosed gap carried over from the prior iteration; it does not affect anything built so far because
  every relevant file already lives in the one folder it checks. It only matters once the real,
  final freeze is put together.

---

## Config and Environment Changes

- None. No new environment variables, settings, or database changes.

---

## Known Limitations

- The "what if a candidate tries to read forbidden data" proof reuses the exact same error types the
  rest of the system already uses for that situation — it does not yet wire the real data-access guard
  into the practice run; it proves the Foundry *reacts correctly* if that guard ever fires, using a
  stand-in that fires it on purpose. Wiring the real guard in for real historical data is planned for a
  later step.
- No new user-visible screen exists yet for any of this — it can only be verified by running the
  automated test suite, not by clicking through the app.
