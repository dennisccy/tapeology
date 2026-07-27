# Phase goal-desk-iter-7 — User-Visible Changes

**Phase:** goal-desk-iter-7
**Date:** 2026-07-26
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- **In a Claude conversation connected to this project's MCP server**, an operator can now ask
  Claude to read the registered universe snapshots directly (`desk_universe` tool) — the same
  103-member S&P constituents list, checksum, and registration history the `/desk` page's
  Provenance panel already shows.
- **In a Claude conversation connected to this project's MCP server**, an operator can now ask
  Claude to read the screen ledger directly (`desk_screen` tool) — the same meta-only history list
  plus the latest full ranked/skipped snapshot the `/desk` page's Briefing/Skipped Members/Screen
  History panels already show.
- **On the `/desk` page**, hovering anywhere over a ranked briefing row (not just the small
  distance/score numbers or a coverage badge) now shows one combined tooltip with that row's exact
  (unrounded) `distance_bps`, exact `band_score`, and each timeframe's "window last requested"
  freshness value — this detail had become impossible to see on hover in the previous iteration.
- **On the `/desk` page**, hovering anywhere over a skipped-member row now shows a tooltip with each
  timeframe's coverage-freshness value for that row (skip rows have no distance/score, so the
  tooltip never invents one).

---

## What Changed in the Visible UI

- Nothing changed in what a user sees on the `/desk` page without interacting with it — no new
  page, panel, button, column, or label. The page's rows, table layout, and at-rest appearance are
  byte-identical to the previous iteration.
- The ONLY visible change is where the hover tooltip lives on a briefing/skip row: it moved from
  several small per-cell hover targets (the distance number, the score number, each coverage badge)
  onto the row's own whole-row click link. A user can now get the full-detail tooltip by hovering
  ANYWHERE in the row, not just those specific small spots.

---

## What Old Behavior Changed

- **Hovering a `/desk` briefing or skipped row**: in the previous iteration, hovering directly over
  the small distance number, score number, or a coverage badge showed a small tooltip with more
  precise detail — but this had silently stopped working once the row's whole-row click link began
  covering the whole row (an audit-found regression, not an intentional prior change). This
  iteration restores the detail by moving it onto the row's own click link, so it now shows on
  hover anywhere in the row instead of only those specific spots. Clicking a row is unchanged —
  clicking anywhere in a ranked or skipped row still opens that symbol on the `/structure` page at
  the same date exactly as before; no click/navigation behavior was touched.

---

## Not Visible Yet

- The two new MCP tools (`desk_universe`, `desk_screen`) are only reachable through a Claude/MCP
  conversation — there is no new button, link, or panel on the `/desk` web page itself for them,
  because the web page already displayed this same data before this iteration. This is intentional:
  the goal was to make the data Claude-readable, not to add a redundant UI surface for data the page
  already shows.
