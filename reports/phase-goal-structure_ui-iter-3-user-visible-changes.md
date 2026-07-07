# Phase goal-structure_ui-iter-3 — User-Visible Changes

**Phase:** goal-structure_ui-iter-3
**Date:** 2026-07-07
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now choose a registered dataset from a dropdown on the `/structure` page's new **Comparison** section (below the existing Registry section), populated from every dataset the backend has on record (7 today on this machine) — no `curl` or MCP tool required.
- Users can now click "Run comparison" to start an offline research job that backtests both the champion strategy (`v1`) and the newer `structure_tape` strategy over the chosen dataset, both at the `default` profile, entirely from the browser.
- Users can now watch both backtests progress independently from "Queued…" to "Running…" (with a live events-processed count while running) and see the two result cards populate automatically once both finish — no manual refresh, no separate polling action.
- Users can now read, side by side, each strategy's trade count (`n`), net return in R-multiples, net return in simulated dollars, win rate, and maximum drawdown — with a strategy that took zero trades showing its `win_rate`/`max_drawdown_r` as the honest "no trades (n=0)" rather than a misleading `0`.
- Users can now see, below each strategy's headline numbers, a per-class (A/B/C confluence-grade) breakdown table with the same trade-count/net-R/net-$ figures per class, and an inline "insufficient sample (n < 5)" chip on any class below the configured minimum sample size — shown next to the real numbers, never hidden or swapped for a separate state.
- Users can now read the exact simulated-PnL honesty disclaimer — "simulated — assumed fees/slippage — not indicative of live results" — attached to each strategy's results, pulled verbatim from the same backend field used everywhere else in the app (never a shorter frontend paraphrase).
- Users can now see a read-only "Champion (moved never by this view)" panel confirming the champion strategy/profile pointer (today `v1`/`default`) every time they use the Comparison section, plus a "Founding baseline (PnL ledger)" panel showing the very first recorded ledger row (its title, plus the founding candidate's train and hold-out net R) for reference.
- Users now see six distinct, explicit messages instead of a blank area or a guessed result: no datasets registered yet; the dataset list unreachable; the idle state before a dataset is chosen/Run is clicked; a "could not be started" error if either POST fails; a per-side "failed" card carrying the backend's own error text; a per-side "cancelled" card that explicitly states no result is shown (never a partial number); and a poll-time "Backend unreachable while polling" notice that clears on its own once polling recovers.

---

## What Changed in the Visible UI

- The `/structure` page now has a third section, **Comparison** (`aria-label="structure_tape vs v1 comparison"`), appended directly below the existing Registry section — same page, no new route, no new nav entry.
- The page's top intro paragraph now reads "...the registered strategies and current champion, and a structure_tape-vs-v1 backtest comparison" instead of stopping after "for a chosen symbol and as-of time."
- The `structure-framing` read-only disclaimer line (present since J-01) now previews all three sections — "Read-only, in three sections: S/R levels and confluence zones on a price chart; the strategy registry and champion; and a structure_tape-vs-v1 comparison you can run over a chosen dataset..." — instead of describing only the Levels & Zones section.
- The new Comparison section contains, top to bottom: a two-column Champion / Founding-baseline row; a dataset `<select>` populated with `symbol · split · id-prefix`-labeled options plus a "Choose a dataset…" placeholder; a "Run comparison" button (disabled until a dataset is chosen, its label switching to "Running…" mid-flight); and, once a comparison has started, two side-by-side result cards labeled "v1 (champion strategy)" and "structure_tape."
- Each result card shows a definition list (`n`, `net R`, `net $`, `win_rate`, `max drawdown (R)`), a "Per-class (A/B/C)" table (columns: class, n, net R, net $, sample), and an amber-bordered register line — visually matching the existing Registry section's dark instrument-panel styling (font-mono numerics, amber for honesty/degraded states, rose for a failed backtest).
- The Comparison section's champion badge uses new, distinct data-testids (`comparison-champion-strategy` / `comparison-champion-profile`) from the pre-existing Registry section's badge (`champion-strategy` / `champion-profile`) — both now render simultaneously on the same page, showing the same underlying value from one shared fetch.
- `README.md`'s "Structure page" bullet was reworded from a single-section description to "...now with three read-only sections," and a new dedicated bullet, "structure_tape-vs-v1 comparison on the Structure page," was added describing the Comparison capability in full.

---

## What Old Behavior Changed

None. This iteration is purely additive to `/structure`:

- The existing Levels & Zones (J-01) section — the symbol/as-of form, the Load button, the price chart, the confluence-zones table, and its four honest states — is unchanged in logic and rendering.
- The existing Registry (J-02) section — the two strategy cards, the Champion panel, the champion cross-check caption — is unchanged in logic and rendering; its own `champion-strategy`/`champion-profile` testids and values are untouched. Only the new Comparison section below it reuses the same underlying champion data, exposed through newly-named testids so the two same-page instances never collide.
- No other route (`/`, `/journal`, `/studies`, `/performance`) or the 5-link top navigation was touched.
- Two lines of copy changed on `/structure` itself (the intro paragraph and the `structure-framing` disclaimer) to describe the page's new third section — the only pre-existing text on this page that reads differently than before.

---

## Not Visible Yet

- **The backtest's random-entry (`null_baseline`) comparison is not rendered in the Comparison section.** `GET /research/backtests/{id}`'s `result.null_baseline` (a seeded random-entry baseline with its own `n`/`net_r`/`net_usd`/`win_rate`/`max_drawdown_r` aggregate) is fully typed in `apps/frontend/lib/types.ts` (`BacktestResult.null_baseline`) and present in every terminal payload, but the new `BacktestResultBlock` component only renders `result.aggregates`, `result.aggregates_by_class`, and `result.register` — never `result.null_baseline`. This is not a defect against this iteration's spec (which never asked for it to be shown here); it is simply a fact worth knowing: a value the backend already computes for every backtest is not yet shown on this particular page.
- **No cancel control.** `POST /research/backtests/{id}/cancel` already exists on the backend (and is used by the Studies page for its own jobs), but the Comparison section has no cancel button — explicitly out of scope per the execution plan (its "New user actions" names only the dataset selector and "Run comparison"). The `cancelled` honest state renders correctly if a backtest is cancelled by other means (e.g., a direct API call), but there is no in-UI way to trigger it.
- **No history of past comparisons.** The Comparison section holds only the two backtest ids it just created, in React component state (no URL parameter, no localStorage). Reloading `/structure` — or simply revisiting it later — always starts from the idle "Choose a dataset, then Run comparison…" state, even if backtests were already run earlier in the same session, in a prior session, or via `curl`/MCP. `GET /research/backtests` (the plural list endpoint) is not called anywhere in the frontend, so there is no way to browse or resume a previously-run comparison from the UI.
- **A `/datasets` library/inventory page** (browsing all registered datasets' full metadata — event counts, checksum, source, timeframe coverage, etc.) still does not exist; the new dataset `<select>` shows only `symbol · split · id-prefix`, enough to pick one, not enough to inspect one. Confirmed out of scope for this iteration (roadmap Card 5.9).
