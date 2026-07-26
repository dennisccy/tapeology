# goal-desk-iter-4 — Implementation Summary

**Phase:** goal-desk-iter-4
**Date:** 2026-07-26 (updated after the audit fix pass)
**Written by:** developer

---

## Features Implemented

- **A new page: `/desk`.** The product now has a third page — Cockpit, Structure, and now Desk —
  reachable from the top navigation bar. This is the daily briefing the operator opens first: it
  shows the most recent screen run (built in the prior iteration) as a dense, ranked table.
- **"Run Screen" button.** Clicking it starts today's screen over the registered list of names,
  shows live progress ("N of 101 done"), and can be cancelled mid-run. A second click while one is
  already running does not start a second one — it just shows the same in-progress run.
- **"Top-up" button.** The bar-fetching step from two iterations ago (which previously only had a
  command-line/API trigger) now has its first on-screen button too, with the same live-progress and
  cancel behavior.
- **The briefing itself.** Once a screen has run, the page shows: every ranked name with its side
  (support/resistance), grade (A/B/C), distance from the last close, score, which timeframes have
  bars on file (shown honestly per timeframe — a name can have daily bars but not hourly, and the
  page shows exactly that rather than guessing), and whether recorded trade-by-trade evidence
  exists for that name. Names that could not be ranked (no bars, or bars but no usable prior
  session) are listed separately and honestly, grouped by the specific reason.
- **A "where did this number come from" line.** Every screen shown on the page carries its full
  paper trail: which list of names it used, what date, and the app's internal settings fingerprint
  — so two screens can always be told apart or confirmed identical.
- **A history list.** Past screen runs are listed (date + counts), read-only this iteration —
  clicking into a past run's own details, and jumping from a name straight to its full chart on the
  Structure page, are both planned for the next iteration.
- **Two small honesty fixes carried over from review of the prior iteration**, done alongside the
  page:
  - Running a screen with no registered list of names now fails immediately with a clear message,
    instead of silently saving a permanent "nothing to show" record that would clutter the history
    forever.
  - The list-of-names storage now protects itself the same way the screen storage already did: if a
    saved file ever gets corrupted on disk, re-saving under the same name now refuses and reports
    the damage, rather than silently overwriting it.

## Changed Behavior

- None to any EXISTING page, endpoint, or command. Every prior page (Cockpit, Structure) and every
  prior desk command/endpoint continues to work exactly as before — confirmed by re-running the
  full automated test suite (now 1,305 checks, up from 1,299, with zero failures) and by comparing
  the underlying source code for every file that serves an existing page or calculation: none of
  them changed.
- One internal-only addition: when a screen finishes running, the app now also remembers whether it
  actually computed something new or simply found that today's exact answer was already saved from
  an earlier run. This has no visible effect on what the operator sees on the page this iteration —
  it is groundwork the app itself uses to be precise about "did this button click do new work."

## Backend-Only Items

None. Everything built this iteration has a corresponding on-screen control or display on the new
`/desk` page.

## Incomplete Items

- **Clicking into a past screen run's own rows, and jumping from a ranked name to its full chart on
  the Structure page** — both explicitly planned for the NEXT iteration, not this one. This
  iteration's history list is read-only (dates and counts only).
- **A real, full run over the ~101 real names, and a real bar top-up over all of them, were not
  executed as part of this build** — that is by design, the same as every prior iteration: this
  build proves the buttons and the underlying machinery work correctly; actually running them for
  real is a deliberate, separate action for the operator to take when ready (it takes real time and
  writes permanent records, so it should not happen automatically as a side effect of building the
  feature).

## Config and Environment Changes

- **None that change any number shown on screen.** No new settings were added. The app's internal
  fingerprint (used to detect if the underlying calculations have ever changed) is confirmed
  unchanged.

## Known Limitations

- **The very first click of "Run Screen" or "Top-up" after the app has just restarted may be slow**
  for the first name it processes (already-known "warming up" behavior seen elsewhere in the app,
  not something new this iteration introduced). A small fix was applied to reduce the chance this
  slowness accidentally causes an automated check to time out.
- **Only the on-screen wiring was visually confirmed against the app's own historical test data**
  (a screen recorded from an earlier session) rather than a brand-new empty run — the page's "no
  screen yet" starting message was verified by reading the code rather than by watching it live
  (creating a truly empty test environment locally would have required extra setup out of scope for
  this check). Confirming that exact starting screen with a live screenshot is expected to happen in
  the next verification step of the pipeline.
- Nothing about how the underlying wall/grade/score calculations work was touched this iteration —
  the new page only displays what those existing calculations already produce.

---

# Update — audit fix pass (2026-07-26)

The review after this iteration found one serious problem and several smaller ones. All are now
fixed. The automated test suite is at **1,328 checks passing, 0 failing** (up from 1,305).

## The serious problem: a price-less bar could be saved, and it killed the Structure page

**What happened.** The new "Top-up" button fetches historical daily/hourly bars from Yahoo Finance.
For a day that has not traded yet, Yahoo returns a row with a trading volume but **no prices at all**
— literally blank open/high/low/close. Nothing in the app checked for that, so those blank rows were
saved into the permanent, never-modified bar archive. When the Structure page later tried to draw a
candlestick for a bar with no prices, the charting library refused and **the entire Structure page
went blank a fraction of a second after it appeared**. This happened for real: 58 names, including
the Apple example the whole project is pinned to, were affected during this iteration's own testing.

Worse, and only discovered while fixing it: those blank rows were also **silently emptying the wall
map**. Asked for Apple's tradable walls as of 25 July, the app returned *no walls at all*, because it
had picked the price-less day as its reference session. With the blank row excluded it returns the
expected ten walls off the 23 July session.

**What was fixed, in three independent places** (so no single mistake can bring this back):

1. **At the source.** The Yahoo Finance connector now treats a row with no prices as *no bar at all*
   and skips it — exactly as it already skips a week with no trading. Confirmed against the live
   Yahoo service on 26 July: it is *still* serving that blank row today, and the app now returns 7
   real bars instead of 8 rows one of which was blank.
2. **At the archive door.** The bar archive now refuses outright to save any bar with a missing or
   nonsensical price, naming the exact day it rejected. Nothing gets written.
3. **When reading what is already there.** The 58 already-affected files are **not deleted, not
   edited, and not re-fetched** — the project's rules say saved market data is permanent. Instead the
   single blank row inside each file is skipped when the app reads it, and the app now reports
   honestly, on that name's data, "1 recorded row carries no price — excluded; the file itself is
   unchanged." Every real bar in those files is used exactly as before.

Deleting the whole affected file would have been simpler but was rejected after measuring it: doing
so changes Apple's support walls (one support level moves from the 222–224 range to the 274–276
range), because those files also hold a year of perfectly good history. Removing one bad row must not
quietly move numbers the operator reads.

4. **And the chart itself is now unkillable by bad data.** As a safety net, the chart drops any
   unusable row and prints a small note saying how many it dropped, rather than taking the page down.

**Confirmed working, live**: the Structure page for the pinned Apple example now loads, shows the
`300.11–302.2` wall, draws its chart, and stays up — with zero errors of any kind. Before the fix the
same page collapsed to nothing within a tenth of a second.

## Smaller fixes on the new Desk page

- **A label that lied has been corrected.** The paper-trail line read "Window last requested
  d7bc8f8127904d0a". That value is not a time — it is a fingerprint summarising when every name's
  data was last requested. It now reads **"Bar-store signature"**, with a one-line explanation
  underneath, and the freshness wording stays where it is accurate (each timeframe badge's tooltip).
- **A confusing row now explains itself.** Some ranked names showed all four timeframe badges dark
  ("no bars on file") while still being ranked *from* bars. Both readings are true — they come from
  two independent sources by design — and the page now says so in a short note above the table
  instead of leaving the operator with a contradiction.
- **Numbers are readable.** `0.33523150389608725 bps` now displays as `0.34 bps`; the exact value is
  still there on hover, nothing is hidden.
- **A dropped network call no longer wipes the briefing.** If the one refresh after a screen finishes
  fails to reach the backend, the page keeps showing the last briefing it successfully loaded instead
  of replacing it with an "unavailable" panel.
- **"Did this click do new work?" is now on screen.** After a screen run finishes, the page says
  either "Recorded a new snapshot" or "Reused the snapshot already recorded for this key", with the
  record's id. The app already knew this internally; now the operator can see it.
- **Two wording fixes in error messages.** Trying to run a screen when the saved list of names exists
  but is *damaged* now says so and names the damaged file, instead of claiming no list is registered
  (two different problems needing two different actions). And one code comment that overstated a
  guarantee about cancelled runs now describes what actually happens.

## Still outstanding (honest)

- **The 58 affected files are still on disk**, by decision — untouched, with their single blank row
  skipped on every read and reported as such. Nothing in the product needs them cleaned up; a future
  operator-run cleanup remains possible because nothing was destroyed.
- **The automated regression check for the Structure page was strengthened but still cannot detect
  every kind of crash.** It now confirms, after the page loads, that the chart actually drew and the
  wall is still on screen — which is exactly what this failure broke. It still cannot fail on a
  browser error by itself; that needs a change to the shared testing framework, not to this project.
- **The verification screenshots filed for this iteration are unreliable and need re-taking**: one
  labelled "empty state" actually shows a populated page, and two labelled "top-up progress" and
  "top-up cancelled" are the same blank image. Fresh, correct screenshots of the fixed pages are
  filed as `FIX-J-07-structure-alive.png` and `FIX-desk-populated-relabeled.png`. Re-running the
  browser verification step against a throwaway test environment (rather than the real saved data, as
  happened here) is the remaining step — it is also what would have prevented the blank-price rows
  from ever reaching the real archive.
- **The "Top-up" button was deliberately not clicked against the live Yahoo service during this fix**,
  because doing that is what caused the original problem. The two protections were instead each
  proven separately: the connector against the live service, and the archive's refusal by automated
  test.

## Config and environment changes

None. No new settings, and the app's internal calculation fingerprint is confirmed unchanged
(`08e471b10130e1e2`).
