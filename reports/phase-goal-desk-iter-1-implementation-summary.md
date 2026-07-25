# goal-desk-iter-1 — Implementation Summary

**Phase:** goal-desk-iter-1
**Date:** 2026-07-25
**Written by:** developer

---

## Features Implemented

- **A new way to fetch the list of S&P 100 companies**: on command (via a REST call — no button
  in the app yet), the system can now go fetch the current S&P 100 membership list from Wikipedia,
  check that what it got back looks sane (a real company-symbol table, roughly 90–110 names, no
  garbled entries), and save it as a permanent, dated record. If anything about the fetched page
  looks wrong, it refuses and explains exactly why — it never guesses or saves a partial list.
- **A permanent record of every fetch**: each successful fetch is saved as its own dated,
  tamper-evident file. Fetching the exact same membership list twice is recognized as "already
  have this" and refused — nothing is silently overwritten or duplicated.
- **A way to read back what's been saved**: a second command lists every saved fetch and shows the
  most recent one's full company list. Before anything has ever been fetched, this honestly says
  "nothing here yet" rather than erroring out.
- **Special-character handling for dual-listed companies**: some companies (like Berkshire
  Hathaway) are listed with a period in their ticker on the source page (`BRK.B`) but need a dash
  for use elsewhere in this system (`BRK-B`). This conversion now happens automatically and
  correctly, while still keeping a record of exactly what the original page said.

## Changed Behavior

None. Nothing a user could already do behaves differently. This iteration only adds new,
currently-invisible backend capability.

## Backend-Only Items

- `POST /research/desk/universe/fetch` — fetches and saves a new company-list snapshot. Reachable
  today only via a direct API call, a command-line test, or an AI assistant using the app's
  read-only connection — there is no button for it in the app yet.
- `GET /research/desk/universe` — reads back the saved company-list snapshots. Same access
  situation: no page in the app shows this yet.
- Both will get an on-screen home on the upcoming "Desk" page, planned for a later step in this
  same chapter of work.

## Incomplete Items

None from this step's own plan — everything this step's plan asked for was built and verified,
including a real, successful test fetch against the live Wikipedia page (see "Known Limitations"
below for exactly what was and wasn't covered).

This step is deliberately narrow: it is ONE piece of a larger six-piece plan for a new "Desk"
page (a daily screening tool). The next pieces — checking which companies already have price
history on file, running an actual daily scan, and building the on-screen Desk page itself — are
separate, upcoming steps, not gaps in this one.

## Config and Environment Changes

- `TAPEOLOGY_DESK_UNIVERSE_DIR` — optional. Lets an operator choose where saved company-list
  snapshots are stored on disk. If not set, defaults to a folder inside the app's existing data
  directory. Nobody needs to set this for normal use.
- No database migration was needed.
- No new external software/library was added — the fetch uses tools already built into this
  project.

## Known Limitations

- This step does not add anything to look at on any page. It is entirely "plumbing" — the visible
  result (a page where an operator can click a button to run this fetch and see the list) comes
  in a later step of this same body of work.
- The live fetch against the real Wikipedia page was tested and works — but it required a small
  fix: Wikipedia's servers were initially refusing the request because it didn't identify itself
  clearly enough as an automated tool (this is a documented, standard requirement on Wikipedia's
  side, not a bug in this system). That's now fixed and verified working against the real page —
  101 real company tickers were fetched and saved successfully in the verification run.
- There is no "refresh this automatically" behavior, and there won't be one — by design, this
  system never fetches anything on its own. Every fetch has to be explicitly requested (a
  deliberate safety choice for this project, not a limitation to be fixed later).
- The automated test suite grew from 7 to 8 tests that are intentionally skipped by default (they
  only run when an operator explicitly asks to test against the real internet). This is expected
  and matches how this project has always added this kind of check — it is not a sign of anything
  broken.
