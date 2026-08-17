# Goal Iteration 2 (rapid-microscope) — Implementation Summary

**Phase:** goal-rapid-microscope-iter-2
**Date:** 2026-08-17
**Written by:** developer
**Revision:** 2 — updated after a code review found one critical honesty defect (see
"Correction made after review" below). The stored analysis for all 18 datasets was rebuilt.

---

## Features Implemented

- **The micro observer**: a new, invisible-to-users backend component that watches a recorded
  historical tick-by-tick trading tape (one already-recorded symbol-day at a time) and, as it
  reads each trade in order, computes a set of order-flow statistics — how much buying pressure
  vs. selling pressure has accumulated, whether recent trades are clustering on one side, how
  efficiently price is moving in response to aggressive trading, and whether the quoted bid/ask
  is thinning out or refilling. This is the foundation the project's later "rapid validation"
  research tools will build on; it does not itself produce any trading signal or claim.
- **A record of "what was built"**: an operator (or, later, the app) can ask the backend which of
  the 18 already-recorded tick datasets have had this analysis run on them, trigger the analysis
  to run for datasets that haven't been processed yet, watch its progress, cancel it if needed,
  and see a history of past runs. All 18 of the currently-recorded datasets have already had this
  analysis run once, successfully.
- **A documented sizing decision**: before committing to a storage format, the team measured three
  different ways of storing this analysis (one entry per single trade or quote tick, one entry per
  trade only, one coarse summary every 200 ticks) against the largest and one of the smallest real
  recorded datasets, and picked the "one entry per trade" format as the best balance of detail vs.
  storage size and speed. The measured numbers are recorded in the developer handoff.

---

## Changed Behavior

- None. Every existing page, report, and API endpoint behaves exactly as before. The one
  supporting-infrastructure change is to a QA/testing script (not a product surface): the isolated
  test environment used to verify the UI now has two small real tick datasets available to it,
  where before it had none, so a screenshot of the "Microscope Readiness" panel (built in the
  prior iteration) can finally show a real, non-empty table instead of an empty one.

---

## Backend-Only Items

- **The micro observer and its analysis output** — fully implemented and verified against all 18
  real recorded datasets, but there is no page or screen yet that displays this analysis to a
  user. It is reachable only through backend API calls today. Rendering it on the `/desk` page is
  planned for a later iteration.
- **The "build progress" / "cancel" / "run history" controls** — implemented as API endpoints only;
  no button or progress bar exists in the app yet.

---

## Incomplete Items

- **Displaying the analysis on any screen** — deliberately out of scope for this iteration (planned
  for a later iteration named J-08 in the project's roadmap).
- **Joining this analysis to chart patterns or support/resistance levels** ("does order flow behave
  differently near a specific price level") — deliberately out of scope this iteration; that is
  the very next planned iteration.
- **A widened test-environment dataset** — the test environment used for screenshotting now has 2
  small real recorded datasets (enough to prove the screen renders real data), not the full 18.
  Widening it further is deferred until a later iteration actually needs more data there.

---

## Config and Environment Changes

- `TAPEOLOGY_MICRO_SNAPSHOTS_DIR` — optional override for where this analysis's output is stored
  on disk; if unset, it defaults to a folder next to the existing recorded-datasets folder. No
  action needed for normal operation.
- No database migrations. No changes to any existing environment variable's meaning or default.

---

## Known Limitations

- Storing this analysis for all 18 currently-recorded datasets uses about 6.2 GB of disk space (the
  raw recorded data itself is about 0.92 GB) — this is expected given how much detail is captured
  per trade, and disk usage will grow further as more tick data is recorded in later iterations.
  This is a backend storage concern only; it has no effect on page load times or any existing
  feature.
- Two sub-parts of the analysis are built and proven correct on hand-checked examples but are not
  yet connected to anything that runs on real data. (1) Looking for "divergence" between price and
  buying/selling pressure at a specific price level — that connection is explicitly the next
  iteration's job. (2) A ratio comparing how much was traded at a price against how much quoted
  size came back there — this one is blocked by the same measurement-units question described
  below, and stays switched off until a dataset arrives with its units actually confirmed.

---

## Correction Made After Review

A code review found one defect serious enough to fail the iteration, and it has been fixed.

**What was wrong.** Some of the figures this analysis produces mix two different kinds of
measurement: how many shares actually traded, versus how big the displayed bid/ask quote was. For
those to be comparable, we have to know what unit the data vendor reported quote sizes in — and for
every one of our 18 recorded datasets, that has never been confirmed. The project's rules say such
a figure must be **refused outright**, with a stated reason, rather than reported as if it were
trustworthy. One figure — how much displayed size drained away at a price before that price moved —
was being reported as a plain number anyway, for all 18 datasets. It was reported honestly for what
it measured, but it should not have been reported at all.

**What changed.** That figure is now withheld whenever the dataset's units are unconfirmed. In its
place the analysis records an explicit refusal and the reason for it. Everything around it is still
reported — when the observation started, when it finished, at what price, and how many quote
updates it covered — because none of that depends on the units question. The figure comes back
automatically, with no code change, the first time a dataset arrives whose units have been properly
confirmed (that confirmation is part of a later iteration's recording work).

Related figures that compare quote sizes only to other quote sizes — the bid/ask balance and the
size-weighted price — are unaffected and still reported. They never had the units problem, and a
test now proves the new refusal does not over-reach and silently suppress them.

**What was re-done.** Because the stored analysis for all 18 datasets already contained the
unreliable figure, all 18 were rebuilt from scratch (about 9 minutes). Every one of the 1,824,729
affected entries across the rebuilt files was then re-read and checked: all 1,824,729 now carry the
refusal, and none carries a raw figure. Storage grew slightly, from about 6.23 GB to about 6.38 GB,
because the refusal reason takes a little more room than the number it replaced.

**Other things fixed in the same pass.** The test that had been checking this figure was asserting
the old, incorrect behaviour as correct; it has been split into two — one covering a dataset whose
units are confirmed, one covering a dataset whose units are not. Five further tests were added,
including two that scan a real recorded dataset end to end. Separately, two pre-existing tests
proved unreliable — they were timing-sensitive and failed roughly 60% of the time depending on how
fast the machine happened to be, regardless of this fix; both were made deterministic without
weakening what they check.

**Verification.** The full backend test suite passes: 2,828 tests passed, 8 skipped, none failed.
No existing behaviour changed anywhere else in the product.
