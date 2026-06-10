# Iteration 5 — Implementation Summary

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-5
**Date:** 2026-06-10
**Written by:** developer

---

## Features Implemented

- **Declaring a thesis now works on the real installation**: Previously, declaring a thesis against
  the running app's saved journal failed every time with a server error. The cause was a database
  upgrade that was added to the code but never applied to the already-existing journal file. This
  iteration adds a proper, versioned database upgrade that runs automatically when the app opens the
  journal — so the saved journal is brought up to date in place, and declaring a thesis returns a
  successful, live result instead of an error.
- **Safer thesis recording**: Recording a new thesis and its first journal entry now happen together
  as a single all-or-nothing step. If anything goes wrong, neither is saved — so the journal can
  never be left with a "half-recorded" thesis (which previously stranded two old theses and blocked
  new ones on the same ticker).
- **Automatic cleanup of stranded theses on startup**: When the app starts, any thesis left "active"
  by a previous run is automatically marked "expired" (and kept in the record, never deleted). This
  clears the two stranded theses that were blocking fresh declarations on SIM-BUYER and SIM-SELLER.

---

## Changed Behavior

- **Declare a thesis (POST /research/thesis)**: Previously returned a server error (503) against the
  app's real saved journal, and could be blocked by a stranded old thesis (409). Now returns the
  live thesis with its starting verdict.
- **App startup**: Now upgrades the saved journal's format in place (when needed) and cleans up any
  stranded active theses before serving requests. Old journal entries are preserved exactly — no
  past records are altered or invented.

---

## Backend-Only Items

- None. The single backend fix (the journal upgrade + safer recording) directly unblocks the
  existing on-screen thesis experience; there is no new backend capability without a UI.

---

## Incomplete Items

- None from this iteration's scope. This was a deliberate fix-only iteration: no new features were
  added (no chart thesis lines, no risk flags, no journal page, no studies, no cues — all explicitly
  out of scope and untouched). Browser verification of the now-unblocked verdict experience is the
  next step in the pipeline.

---

## Config and Environment Changes

- `journal_schema_version` — the journal database format version the app upgrades to on open —
  changed from `1` to `2`. No operator action is required: the upgrade runs automatically and is
  safe to run repeatedly.
- No new environment variables. The journal file location is still controlled by the existing
  `TAPEOLOGY_JOURNAL_DB` setting (default: `apps/backend/tapeology_journal.db`).
- No new dependencies. The upgrade uses Python's built-in SQLite only.

---

## Known Limitations

- The upgrade adds two new columns to the journal's verdict-event records but deliberately leaves
  them blank for entries written before the upgrade. This is intentional and correct: the journal is
  an append-only record, so past entries are never rewritten or back-filled with made-up values.
- The app's saved journal file is intentionally not stored in version control. Only a small,
  human-readable sample of the old format (used to prove the upgrade works) is committed; it contains
  research records only, no market/tape data.
- One automated test that needs live market-data credentials remains skipped (unchanged from prior
  iterations); it is unrelated to this fix.
