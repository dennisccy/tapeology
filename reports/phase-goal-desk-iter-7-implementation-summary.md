# goal-desk-iter-7 — Implementation Summary

**Phase:** goal-desk-iter-7
**Date:** 2026-07-26
**Written by:** developer

---

## Features Implemented

- **Claude can now read the whole Desk over MCP.** Two new read-only tools, `desk_universe` and
  `desk_screen`, join the 15 already-shipped tools (15 -> 17 total). Through a Claude conversation
  connected to this project's MCP server, an operator can now ask for the registered universe
  snapshots and the latest/historical screen results directly — the exact same data `/desk` already
  shows in the browser, served byte-for-byte identically. Nothing was added that can change any
  data; both new tools are read-only, exactly like every other tool on this server.
- **A hover-tooltip honesty repair on the `/desk` page.** In the previous iteration, an audit found
  that hovering over a row's distance/score numbers or its coverage badges no longer showed the
  detailed tooltip it used to — the row's whole-row click link had started sitting "on top of"
  those numbers, silently blocking the browser from ever showing their tooltips. This iteration
  fixes that: hovering ANYWHERE on a briefing row now shows one combined tooltip with the exact
  distance, exact score, and each timeframe's "last requested" freshness. Clicking the row still
  works exactly as before — nothing about what happens when you click was touched.

---

## Changed Behavior

- **Hovering a `/desk` briefing row**: Previously, hovering directly over the distance number, the
  score number, or a coverage badge showed a small tooltip with more precise detail — but this had
  stopped working (the row's click-target had grown to cover the whole row, blocking those specific
  hover spots). Now, hovering ANYWHERE on the row (not just those specific spots) shows one combined
  tooltip with the same detail, restored. What you SEE on the page without hovering has not changed
  at all — this is purely about what appears on hover, and where you have to hover to see it.

---

## Backend-Only Items

- **`desk_universe` / `desk_screen` MCP tools** — these two new tools are only reachable through a
  Claude/MCP conversation, not through the `/desk` web page (the web page already showed this same
  data before this iteration; the MCP tools just make it Claude-readable too). No UI change was
  needed or made for this.

---

## Incomplete Items

None from this iteration's own scope. The one browser-verification pass this iteration calls for
(confirming, in an actual browser, that the whole kept product — cockpit, structure page, nav, and
the new 17-tool count — still works, plus a fresh screenshot proving the hover fix actually shows
the tooltip) is a separate QA step that runs after this development work, not part of it.

---

## Config and Environment Changes

None. No new `Config` field, no new environment variable, no new database table. Both new MCP tools
proxy endpoints that already existed before this iteration; the hover fix only changed where a
tooltip's text is attached in the page's markup.

---

## Known Limitations

- The hover-tooltip fix has not yet been confirmed with an actual screenshot of a mouse hovering
  over a row in a real browser — it has been verified by (a) the page still building/compiling
  correctly, and (b) an automated check that reads the page's own source code and confirms the
  tooltip text is built from the correct numbers. The visual, in-browser confirmation is the next
  QA step, not something this development pass performed.
- The two new MCP tools have not been exercised from an actual Claude conversation by an operator —
  they have been proven, in an automated test, to return byte-for-byte the same data as visiting the
  corresponding web address directly. That is the same level of proof every other tool on this
  server was shipped with.
