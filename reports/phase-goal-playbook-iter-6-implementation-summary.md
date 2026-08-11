# goal-playbook-iter-6 — Implementation Summary

**Phase:** goal-playbook-iter-6
**Date:** 2026-08-11
**Written by:** developer

---

## Features Implemented

- **Range Trade signals**: The Playbook now detects "test the low/high twice and hold" range
  setups on the desk's own recorded bars — a support-bounce (long, buying near the bottom of a
  well-tested range) and a resistance-fade (short, selling near the top). Each signal shows how
  wide the range was, how many times each edge was tested, and two extra notes: whether price
  swung all the way through the middle of the range on its way to the signal, and whether a
  slow, high-volume bar sat right at the tested edge (a sign of quiet buying/selling pressure).
- **Double Top and Double Bottom signals**: The Playbook now detects the classic two-peaks (or
  two-valleys) reversal pattern — two touches at roughly the same level, then a break through the
  low point between them (for a double top) or the high point between them (for a double bottom).
  Each signal shows how close the two peaks/valleys were to each other, how far apart in time,
  how deep the dip/rally between them was, and the full risk of the pattern (measured from the
  worse of the two peaks/valleys, never understated).
- **All nine of the book's setups are now on the desk.** Combined with the five setups already
  shipped (opening-range breaks, jump-base-explosion, drop-base-implosion, cup-and-handle,
  capitulation), the Playbook now recognizes the complete set of intraday patterns the book
  describes, plus the euphoria marker. Running the Playbook for any session now shows every one
  of these signal types side by side, with the same honest measurement (what happened afterward,
  compared to picking a random moment) on every one.

---

## Changed Behavior

- **The Playbook's summary sentence**: Previously named five setup families ("opening-range-break,
  jump-base-explosion, drop-base-implosion, cup-and-handle, and capitulation"). Now names all
  eight ("...capitulation, range-trade, double-top, and double-bottom") in both places this
  sentence appears on the `/desk` page (the "not computed yet" message and the section's own
  intro blurb) — this is copy only; no existing signal, number, or behavior changed.
- No other previously-shipped `/desk` behavior changed. All five already-shipped setup families
  render exactly as before; the session-date input, Run Playbook button, and every existing
  section on `/desk` work identically to how they worked before this iteration.

---

## Backend-Only Items

None — every new field this iteration adds is rendered on the `/desk` Playbook Signals section.

---

## Incomplete Items

None from this iteration's own scope. The back-scan (walking every recorded session automatically)
and the evidence view (pooling every recorded signal into a distribution table) are separate,
future pieces of work — they were never part of this iteration's plan.

---

## Config and Environment Changes

None. No new settings were added. (Two existing, already-documented environment variables —
`TAPEOLOGY_DESK_PLAYBOOK_DIR` and `TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR` — were used together this
iteration, alongside two more existing ones, purely to verify a new automated test script against
an isolated, throwaway set of test data, never touching the real recorded data. Nothing about how
the app is configured or run changed.)

---

## Known Limitations

- **The Range Trade setup is explicitly the "first draft" of the nine. The book's own guidance for
  this pattern is the vaguest of the nine, so this iteration's reading of two of its descriptive
  notes ("did price swing through the middle of the range" and "was there a quiet, high-volume bar
  at the tested edge") required this developer to make a specific, documented judgment call where
  the book's own instructions did not spell out an exact rule. The core pattern (test twice, hold,
  bounce) follows the book's rule precisely; only these two supporting notes involved a judgment
  call, and it is written up plainly in the developer notes for anyone who wants to review it.
- **One new automated browser check (for the capitulation signal family from last iteration) was
  verified against a small, single-symbol practice setup rather than the exact multi-symbol
  practice setup a prior QA pass used** (that exact setup was never saved anywhere reusable). The
  check itself was proven to work correctly in a real browser; there's a small chance it needs a
  minor tweak once it runs against a busier practice page with more signals on it, which the next
  QA pass will catch if so.
- **Two old, orphaned records were found and explained, not fixed.** While investigating a loose
  end from a prior iteration, this developer found two leftover "run" entries in the operator's
  real (not practice) data pointing to files that no longer exist. These are harmless — they don't
  affect anything the operator sees or does — and by design the app never deletes or rewrites old
  records, so they can't be silently cleaned up either. The likely cause (a browser test that
  briefly touched the real data instead of a practice copy) has been fixed going forward for this
  iteration's own tests; full details are in the developer handoff.

---

# Addendum — audit-fix pass (2026-08-11)

The hard audit of the work above returned **FAIL** on one of the three new detectors. This pass
fixes it. In plain terms: **the Range Trade detector was too lenient, and in one rare case could
record a signal that contradicted itself.** Nothing else in the iteration was disturbed.

## What was wrong, and what changed

**1. Range Trade fired on one-sided ranges (the main defect).** The rulebook
(`docs/playbook-detector-spec.md`) says a range trade only counts when price has tested **both**
edges of the range **twice each**, and has **held** — each retest failing to push the extreme much
further. The shipped code only checked the side it was trading, and never checked "held" at all.
So an ordinary support test inside a one-way slide could be recorded as a range trade. It now
requires both edges, twice each, each retest holding within the pre-registered tolerance. The very
signal shown in this iteration's own screenshot (a range with the high edge touched only once) is
one the corrected detector will not produce.

**2. A Range Trade long could be recorded with its invalidation level above its own entry.** The
rulebook's formula for the invalidation level assumes the trigger sits above the range low. In a
narrow corner (a small bar sliding just below the range low, still inside the tolerance) that
assumption breaks and the arithmetic flips, producing a long signal that is already invalid the
moment it is written down. The detector now treats that shape as degenerate and records nothing.

Because that second rule is **not** something the rulebook spelled out, it was written into the
rulebook first (as a dated clarification that only ever removes signals, never adds one) and then
implemented — and it is flagged for the project owner to ratify or reject. **If the owner rejects
it, the honest alternative is to drop Range Trade from the shipped setup list** rather than serve
self-contradictory signals; that decision is recorded, not assumed.

## What operators should know

- **No recorded data changed, and none was reinterpreted.** No playbook record in the real store
  contains a Range Trade signal — the setup family ships for the first time in this iteration — so
  the stricter rule cannot alter anything already written down. Recorded files remain untouched.
- **Fewer Range Trade signals than the earlier build would have produced.** This is the point: the
  ones removed are the ones the rulebook never admitted.
- **Double Top / Double Bottom are unchanged.** The audit examined them clause by clause and found
  them correct; this pass did not touch them.
- **The on-screen Range Trade line is unchanged in shape, only in its numbers** — e.g. "range 5.00
  MBR wide · low zone touches 2 · high zone touches 2 · broke at slot 7 · crossed midrange". No
  new field, no layout change, no new click path.
- **The evidence screenshots taken for Range Trade before this fix no longer describe the shipped
  behaviour** and need re-taking; a repeatable rig now exists so that is a one-command job
  (`apps/backend/scripts/qa_playbook_iter6_fixture_scoped_backend.sh`).

## Two housekeeping items closed

- The stored replay script for the earlier "capitulation + euphoria" journey had never actually
  been run end to end. It has now been executed against a live rig and passes, with a screenshot.
- The automated no-peeking-into-the-future checks now also cover the mirrored halves of the new
  detectors (the short range trade and the double bottom), not just one side of each.

## Incident disclosed

While building the repeatable test rig, a scripting mistake wrote four synthetic test files into
the operator's real data store (three fake symbols' bars and, more seriously, a universe snapshot
dated today listing only those three fake symbols, which the desk would have read as its newest
membership list). They were removed, copies were archived outside the project for inspection, and
the seeding script now refuses to run at all unless every storage location it will write to is
inside a disposable test folder. The real playbook records and run history were never touched.
Full file-level accounting is in the dev handoff.

## Config / environment changes

None. No new configuration fields; the configuration fingerprint still prints
`08e471b10130e1e2`. Two new developer scripts were added under `apps/backend/scripts/`; neither
runs in production and neither is wired into the app.

## Verification

Full backend test suite: **2105 passed, 8 skipped** (up 7 tests, all of them new checks on the
corrected rules; nothing removed or skipped). No changes to any of the protected, frozen modules.
