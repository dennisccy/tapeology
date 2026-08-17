# goal-rapid-microscope-iter-4 — Implementation Summary

**Phase:** goal-rapid-microscope-iter-4
**Date:** 2026-08-17
**Written by:** developer

---

## Features Implemented

- **The Scout (candidate screener)**: a new backend engine that takes a small, pre-registered list
  of candidate ideas ("does this order-flow signal relate to what price does next?"), tests each
  one against the recorded tick data using a statistically careful method (so noise doesn't get
  mistaken for a real pattern), and records a verdict for every single one — survive or one of six
  specific kill reasons. Nothing is ever silently dropped.
- **The candidate ledger**: a permanent, tamper-evident record of every candidate ever tested. Each
  entry is cryptographically linked to the one before it, so if any entry were ever edited or
  deleted after the fact, that tampering is detectable and points to the exact entry affected. This
  is the project's "lab notebook" for this kind of research — nothing gets erased, including
  failures.
- **Three new backend endpoints** (not yet wired to a screen — see "Backend-Only Items" below): one
  to read the ledger, one to trigger a new screening run (with progress you can check and cancel),
  and one to see the history of past runs.
- **Two small honesty fixes to the already-shipped corpus-readiness numbers**: (1) if a recorded
  playbook file is corrupted, that corruption now shows up explicitly in the response instead of
  silently shrinking a count; (2) a field that used to show a plain "0" for "we haven't built a
  wall-touch counter yet" now clearly says "not counted yet" instead — so nobody mistakes "we
  haven't measured this" for "we measured it and got zero."

## Changed Behavior

- **Corpus-readiness data (`joinable_corpus` field)**: previously, a corrupted signal record from
  the desk's setup log would silently vanish from the counts with no trace. Now the corruption is
  reported explicitly alongside the (still honest, still correct) count of everything that IS
  readable. Previously, "wall touches counted" always showed a plain `0`. Now it shows a small typed
  object explaining that number isn't measured yet — the underlying real numbers (how many setup
  signals are usable) are completely unchanged.

## Backend-Only Items

- `GET /research/desk/micro/scout`, `POST/GET/POST-cancel /research/desk/micro/scout/compute`,
  `GET /research/desk/micro/scout/runs` — the Scout's read/trigger/history endpoints exist and work,
  reachable via the API or a command-line tool, but there is no screen showing this yet. Rendering
  the candidate ledger on the `/desk` page is planned for a later iteration (already reserved a spot
  in the site's navigation plan).

## Incomplete Items

None from this iteration's own plan. Every item this iteration committed to build was built and
verified. One item is explicitly and deliberately deferred by design, not left incomplete: any
candidate conditioned on the "quote depletion" signal is excluded from this iteration's registered
list, because a related judgment call about that signal's exact timing is still awaiting an owner
decision — the plan flagged this in advance rather than guessing.

## Config and Environment Changes

- `TAPEOLOGY_MICRO_SCOUT_DIR` — where the candidate ledger is stored on disk — default: a sibling
  folder next to wherever the recorded tick data lives (no action needed for normal operation).
- No database migrations. No new third-party services or paid dependencies.

## Known Limitations

- **Performance on the full recorded tick history**: while double-checking that the new "run a
  screen" button actually works against real data (not just small test fixtures), it turned out the
  very first version would hang indefinitely — potentially for hours — when pointed at the full
  18-file recorded tick archive, and in the worst case could have used an unreasonable amount of
  this machine's memory. This was found and fixed before handoff: the underlying cause was that a
  few of the reused calculation helpers redid more work than necessary each time they were called,
  and that cost multiplied badly on datasets with hundreds of thousands of trades (a few of the
  recorded symbols have that much history in a single day). After the fix, the same run against a
  smaller slice of real recorded data (not synthetic test data) completes in well under a second.
  Against the ENTIRE 18-file archive, a full screening run is now bounded (it will not hang forever
  and will not risk crashing the machine), but it still takes several minutes, simply because there
  is a genuinely large amount of real history to check. This is flagged honestly for whoever reviews
  this work next: it may be worth a dedicated speed-focused pass later, the same way a couple of
  other slow spots in this project got their own follow-up fix in earlier chapters. It does not
  block anything this iteration's checklist actually requires — the official test scenario for this
  iteration uses a small, fast, purpose-built practice dataset, which was already fast.
- **No screen yet for the new feature**: as noted above, the data is fully readable through the API
  and a command-line tool, but nobody can see it on `/desk` yet. That is intentionally scheduled for
  a later iteration.
