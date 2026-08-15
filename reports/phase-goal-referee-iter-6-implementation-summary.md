# goal-referee-iter-6 — Implementation Summary

**Phase:** goal-referee-iter-6
**Date:** 2026-08-15
**Written by:** developer

---

## Features Implemented

- **The hypothesis registry**: the system can now record a research question ("does setup X on
  side Y carry information beyond chance?") permanently, before any evidence exists to confirm
  or deny it. Once written down, a question and its rules (what counts as success, how many
  sessions of new data it needs, when its "clock" started) can never be edited — only withdrawn,
  and only before any real evaluation of it has happened.
- **An honest "clock start" date**: every registered question gets a boundary date computed from
  the moment it was written down. Only trading days strictly after that date will ever be allowed
  to count as evidence for it — old, already-seen data can never sneak in as if it were a fresh
  test.
- **A live readiness view**: for any registered question, the system reports how many trading
  days of new, qualifying evidence have accrued since its clock started, next to the target it
  needs to reach — so an operator can see "3 of 12 sessions so far" today, without waiting.
- **A withdrawal mechanism**: a registered question can be withdrawn (with an optional reason) as
  long as no real evaluation of it has happened yet. Once an evaluation exists, withdrawal is
  blocked — the question stays on the books and counts against the family's error-rate budget
  either way, so an operator can't quietly remove an inconvenient question after the fact.
- **A safety shelf for future "certificates"**: the storage location for the paperwork a trading
  strategy will eventually need before it's allowed to go live is now in place, though nothing
  writes to it yet — that's next iteration's job.
- **Both a command-line tool and an API endpoint** exercise the exact same registration and
  withdrawal logic, so an operator (or a future screen) can use whichever is convenient without
  behaving differently.

---

## Changed Behavior

- **A years-old measurement bug fixed**: on the matched-comparison-builder feature shipped last
  iteration, a specific edge case (a location was found on the map, but literally nothing was
  close enough to check against it) used to report "0% match" — which reads as "we checked, and
  nothing matched." It now correctly reports "not measurable," which reads as "nothing was even
  checked." The ordinary "we checked several things and none matched" case still reports 0%
  exactly as before — nothing else about that feature changed.

---

## Backend-Only Items

- The whole registry (writing a question down, seeing its status, withdrawing it) is reachable
  only through the command line and a raw API call today — there is no button or page for it yet.
  That is intentional: this iteration builds the mechanism and proves it works on test data; the
  actual screen, and the operator's real approval of 2–3 starter questions, is next iteration's
  job.

---

## Incomplete Items

- **No real questions have been registered yet.** This iteration only proves the mechanism works
  correctly on manufactured test scenarios — it does not register any of the five candidate
  questions the research spec proposed. That is a deliberate, explicit decision the operator
  makes next iteration, after reviewing each candidate's live evidence count.
- **The "does this question hold up" analysis (permutation tests, statistical significance,
  pass/fail verdicts) is not built yet.** This iteration only builds the filing cabinet for
  questions — the actual judge that reads the evidence and renders a verdict is a separate,
  future piece of work.
- **The safety shelf for strategy "certificates" has no way to actually produce one yet** — it
  can only be inspected for structural correctness with hand-planted test data. A certificate can
  only ever come from running the real evaluation process once that exists.

---

## Config and Environment Changes

- `TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR` — optional. Points the registry's storage location
  somewhere other than its automatic default (a folder next to the other research data). Not set
  by default; almost never needs to be touched by an operator.
- No database migrations. No changes to any existing settings.

---

## Known Limitations

- A registered question about "does this happen more near a specific price level than away from
  it" (one of the three question types) does not use a comparison-to-chance baseline the way the
  other two question types do — by design, since that specific question type is inherently a
  straight side-by-side comparison, not a comparison-to-a-random-baseline. This is a considered
  reading of the underlying research document, not an oversight — flagged for the reviewer.
- Live-checking the system against real, already-recorded data touched two small, disposable
  internal bookkeeping files (used by an unrelated, already-shipped feature to speed up dataset
  lookups). Nothing about the actual recorded evidence — every existing research record on disk —
  changed even slightly; this was independently verified file-by-file.
- The full visual walkthrough of the whole product (cockpit, structure page, every desk section)
  was not re-run this pass, because nothing in this iteration touches any screen — it stays
  exactly as it looked before. That full walkthrough happens at the end of the research chapter,
  once the registry actually has something to show on screen.
