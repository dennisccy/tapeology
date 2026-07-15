# Phase goal-tradable_wall-iter-9 — User-Visible Changes

**Phase:** goal-tradable_wall-iter-9
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Once an operator has let the Edge Report finish computing one time and the result cache is
  warm, opening `/structure` shows the **Edge Report** panel — the `v1` / `structure_tape` /
  `structure_tape_map` comparison, with per-cell N/R/$/`insufficient_sample` — resolving within
  an interactive time budget (seconds), on every visit, and this now survives a backend restart
  (the cache is written to disk, not just kept in memory). Previously this same panel had no
  practical way to finish loading in a normal browsing session, because every single request
  re-ran the full ~10+ hour backtest sweep from scratch.
- Nothing else becomes clickable or reachable. This is the same panel, at the same URL, showing
  the same fields — the change is purely "does it ever finish loading," not new content or new
  controls. No new button, form, page, or navigation entry was added anywhere in the app.

---

## What Changed in the Visible UI

- Structurally, nothing. Zero files under `apps/frontend/` were modified this iteration (verified
  against `git status`) — no page, panel, button, table, column, or label changed. The Edge Report
  panel's heading, explanatory caption, register banner, Train/Hold-out tables, and Surviving
  Cells table are markup-identical to before.
- The data the panel displays is also unchanged in shape: `GET /research/edge-report`'s response
  is byte-identical whether served from a cache hit or a fresh compute (confirmed in the dev
  handoff's diff — the route only gained an extra dependency parameter; the returned dict's
  fields are untouched). So even once warmed, the panel will show exactly the same kind of
  numbers it always would have — just sooner.

---

## What Old Behavior Changed

- **Edge Report load time, after a one-time warm-up.** Before this iteration, both the
  `/structure` Edge Report panel and a direct `GET /research/edge-report` (or its MCP `edge_report`
  proxy) call re-ran the entire ~10+ hour, ~9.1M-tick backtest sweep on *every single request* —
  in practice the panel almost always sat in its honest "still loading" placeholder
  (`data-testid="edge-report-loading"`), and a backend restart threw away any in-flight progress,
  so it effectively never finished for a normal user. Now, after an operator has let that compute
  finish once and the result is cached, the identical panel and identical endpoint resolve within
  an interactive budget on every subsequent request — including after a backend restart. **Before
  that one-time warm-up happens, behavior is completely unchanged**: the panel still shows the
  same honest loading state for as long as the (still ~10+ hour) first compute takes.
- No other existing behavior changed. The `/structure` page's Tradable Map, raw-levels toggle,
  Case Studies, cockpit chip/overlay, and the Founding-baseline PnL section are untouched by this
  iteration (zero frontend files changed; no other backend route's wiring changed).

---

## Not Visible Yet

- **The result cache itself** (`EdgeReportCache` — a SQLite file plus an in-process fast-path) is
  invisible plumbing behind `GET /research/edge-report`. There is nothing to see, click, or
  configure about it anywhere in the UI; its only observable effect is the load-time change above.
- **The new "record a completed Edge Report into the PnL history ledger" capability exists only as
  a command-line tool**, not as anything reachable in the web app: an operator (or a future
  session) runs `python -m app.research.pnl_history --append-report <path> --enhancement-id <id>
  --title <title>` from a terminal. There is no button or page in `/structure` (or anywhere else)
  that triggers this. The committed ledger file (`reports/pnl/pnl-history.md`) is untouched by
  this iteration — no real report has been appended yet; that first real compute-and-append is an
  explicit, separate operator action, not part of what shipped here.
- **Even after a future real append, the new ledger row type would still not become visible on
  `/structure` as it stands today.** The page's only consumption of the PnL ledger is looking up
  a single `founding` row (`ledger.rows.find(r => r.founding)`) to seed the Champion-vs-Challenger
  comparison view — it does not render a general table of all ledger rows. A newly-appended
  `kind: "strategy_comparison"` row would sit in the ledger with no rendering path in the current
  UI at all, until a future iteration adds one.
