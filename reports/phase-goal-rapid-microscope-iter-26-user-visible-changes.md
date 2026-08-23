# Phase goal-rapid-microscope-iter-26 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-26
**Date:** 2026-08-23
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. This iteration adds no new button, form, page, or navigation entry. Every file the developer
touched this iteration is a Python backend module (`micro_readiness.py`, `micro_join.py`,
`micro_routes.py`) plus their unit tests — zero `.tsx`/`.css` files changed (`git diff --stat` shows
only the three backend modules and their test files). The `/desk` page's structure, section list, and
every rendered label are identical to before this iteration.

---

## What Changed in the Visible UI

None. No page, section, testid, heading, button, or table column was added, removed, or renamed. The
`/desk` page still has the same seventeen collapsible sections in the same order, including
"Microscope Readiness" and "Scout Ledger" rendered exactly as before (same `aria-label`s, same
`data-testid`s: `micro-readiness-section`, `scout-ledger-section`, and their child element testids).
The `GET /research/desk/micro/readiness` response schema is unchanged, so every field the page reads
off it renders the same way it did pre-iteration.

---

## What Old Behavior Changed

- **Microscope Readiness — "Joinable corpus — band touches" figure loads faster the second time it is
  requested.** Previously, every expansion of the "Microscope Readiness" section (or every call to
  `GET /research/desk/micro/readiness`) that needed the band-touch count re-scanned the raw recorded
  tick data for every relevant dataset from scratch — a cost that only grows as more tick data is
  recorded (already tens of minutes on the full real archive per the iter-25 evaluator's own
  measurement). Now, the first computation for a given dataset-and-band-map combination is stored in a
  small on-disk cache, and every later request for that same combination is served from the cache
  instead of re-scanning. **The number displayed does not change** — only how quickly it appears after
  the first load. A user opening the same dataset's readiness figure twice in a row will see the exact
  same "Joinable corpus — band touches" value both times, just faster on the second view.
- **Scout Ledger — internal wiring only, no visible change.** The backend logic that decides which of
  the three pilot studies needs a band map versus a playbook lookup previously kept two separate,
  hand-typed copies of that assignment list. It now reads a single canonical list directly. Nothing an
  operator can see on the "Scout Ledger" section changed as a result — the same pilot-study family
  rows and the same "variants tried" counts render exactly as before.

---

## Not Visible Yet

- None new to this iteration. (The referee-disclosure item flagged by the prior iteration's evaluator
  — surfacing that one Referee-owned readiness figure can go stale — remains deferred and out of
  scope; it was not built this iteration and was not built in any prior iteration either, so there is
  no newly-hidden backend capability to report here.)
