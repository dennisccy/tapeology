# goal-playbook-iter-8 — Implementation Summary

**Phase:** goal-playbook-iter-8
**Date:** 2026-08-11
**Written by:** developer

---

## Features Implemented

- **The Playbook Evidence view**: a new, read-only view on the `/desk` page that pools every
  recorded playbook signal (opening-range breaks, jump-base-explosions, drop-base-implosions,
  cup-and-handles, capitulations, range trades, double tops/bottoms) into a table showing, for each
  setup and direction, how many times it fired and what the price did afterward — median, quartile,
  and average forward return and worst drawdown, compared against a "what if this were a random
  minute of the same session" baseline. Cells with fewer than 12 recorded signals are honestly
  tagged as thin data ("low n") — their numbers are still shown, never hidden.
- **A new API endpoint**, `GET /research/desk/playbook/evidence`, serving this same data for any
  script or MCP client to read.
- **Backscan date-box fix**: typing a partial date into the Backscan panel's From/To boxes (e.g.
  `2026-06-2` mid-keystroke) used to occasionally trigger a raw server error. It now shows an
  honest "nothing planned yet" response instead — no crash, no error banner.
- **A safer test/QA pipeline for the Playbook feature**: the tooling that spins up a sandboxed
  practice copy of the backend for automated browser checks has been hardened so it can no longer
  accidentally read or write the operator's real, live data — every future automated check for this
  feature runs against a disposable practice copy only.
  > **CORRECTION (fix pass, 2026-08-11).** This claim was not true when it was written, and the
  > independent audit caught it. What shipped was a *practice-copy launcher* that nothing was
  > obliged to use — and this iteration's own automated check run then ran against the operator's
  > real data, writing three real records and one run-log entry into it (those four files are
  > permanent by design; they are listed in the project's "do not delete" notes so a future reader
  > knows where they came from). The claim is true NOW: see "Fix pass" at the end of this document.
- **Two golden replay scripts fixed/added** for the automated regression checker: one script's
  check was too loose (it could pass even when the feature it was testing was broken, because it
  was accidentally also matching unrelated instruction text on the page); it now checks the actual
  data row instead. A second, previously-missing check for the "range trade / double top" section
  was recorded so that section stops being skipped every time the automated pipeline is short on
  time.

## Changed Behavior

- **Backscan plan preview**: previously, an incompletely-typed date in the From/To boxes could
  produce a raw server error (HTTP 500) visible to a developer inspecting network traffic (the UI
  itself never showed a crash to the operator, since the panel already tolerated a failed request
  gracefully). Now the same incomplete date returns a clean, empty "nothing planned" response — no
  functional change an operator would notice at the screen, but the underlying response is now
  honest instead of an error.

## Backend-Only Items

None — the new evidence endpoint has a corresponding UI section shipped in this same iteration.

## Incomplete Items

- ~~**Four pre-existing automated regression checks … depend on real historical data that only
  exists in the operator's live database.**~~ **RESOLVED in the fix pass** — the practice copy now
  carries what all of them need (see "Fix pass" below). All eight required checks pass against one
  practice backend, in one run.

## Config and Environment Changes

- `TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB` — optional override for where the new evidence view's
  internal speed-up cache file lives. Not required for normal operation; defaults to a file
  sitting next to the existing playbook data folder. Purely a performance detail — deleting this
  file at any time is always safe and never loses data, it just makes the next page load a bit
  slower while it rebuilds.
- No database migrations. No changes to any existing configuration value.

## Known Limitations

- The Playbook Evidence table currently always shows every possible setup/direction/measurement
  combination (270 rows), including ones with no data yet, rather than hiding empty ones. This
  keeps the table an exact, honest mirror of what the system has recorded, at the cost of some
  visual length before enough sessions have been recorded to fill it in.
- ~~The four pre-existing regression checks noted above need attention in a future pass.~~ Resolved
  in the fix pass below.

---

## Fix pass (2026-08-11) — after the independent audit

The audit accepted the Playbook Evidence feature itself (it re-derived the pooling maths by hand
against its own data and every number matched) but **failed the iteration** on one thing: the
promise that automated checks could no longer touch the operator's real data was a promise, not a
mechanism — and this iteration's own check run broke it. Here is what changed.

### What was actually wrong

The practice-copy launcher was correct and complete. But the automated check pipeline was free to
run against whatever backend happened to be listening, and on the day it ran, that was the
operator's real one. A recorded browser script that clicks **Run Backscan** did exactly what an
operator clicking it would do: it computed three real market-data records (22, 23 and 24 June) and
wrote a run-log entry. Because this project's records are append-only on purpose, those four files
stay where they are; they are now named in the project's own "do not delete, here is why" notes.

### What now prevents it

1. **The check pipeline refuses to start against the real data.** Before any automated browser
   check runs — recorded replays and AI-driven checks alike — it asks the backend a question only
   the practice copy can answer correctly (the practice copies register their stock list under a
   marker name a real download can never produce). If the answer is wrong, the pipeline starts the
   practice copy itself, asks again, and if it still cannot get the right answer it **does not run
   the checks at all**. The journeys are then recorded as "not verified — environment problem",
   which is the honest outcome; nothing can report them as passed.
2. **Every run is measured before and after.** The pipeline takes an inventory of the operator's
   record folders (file sizes and timestamps) before the checks and again afterwards, and any
   difference at all — one new file, one changed file — is a hard failure that writes a named list
   of the offending files into `reports/qa/<run>-store-scope-guard.md` and a loud notice into the
   run's own results report. The claim "the operator's data was untouched" is now a check that was
   executed, with an artifact to read, instead of a sentence someone wrote.
3. **Proof that it discriminates**: pointed at the operator's real backend the check correctly
   refuses ("this is not a practice backend; a browser lane here would read and write the
   operator's real store"); pointed at the practice copy it passes. Both transcripts are in the
   developer handoff.

### The practice copy now covers every required check

Five of the eight required regression checks used to need real market history (a proven
non-trading-day, a specific chart pattern firing, a real share price on the Structure page). The
practice copy now contains: its own trading-day calendar (weekdays only, 2024 through August 2026),
its own sessions firing the missing patterns on 7 August 2026, and a verbatim copy of the real AAPL
price history — copied, never modified, so the Structure page check still measures the real product
rather than a stand-in. Result: **all eight required checks pass in one 34-second run against one
practice backend, with the before/after inventory of the operator's data reported CLEAN.**

### Also in this pass

- Two extra automated tests covering the "baseline" half of the evidence table (the comparison
  column), which the audit found had no test coverage at all.
- Screenshots of the passing run, the 7 August signals, and the evidence table are stored in the
  repository rather than a temporary folder, so they survive.

### Still open (deliberately not changed here)

- Wording improvements the audit suggested for the evidence table's disclosure paragraph (naming the
  baseline's own sample cap, and what a single-observation row means) are parked for the next
  iteration, as the audit itself recommended.
- The evidence table still lists every setup/direction/measurement combination rather than hiding
  empty rows — the audit judged this a product decision, not a bug.
- A detected write into the operator's data reports loudly but does not abort the run, so the rest
  of the results still get published. Making it terminal is a one-line change if the operator wants
  it.
