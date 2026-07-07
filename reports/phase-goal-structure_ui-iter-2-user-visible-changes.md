# Phase goal-structure_ui-iter-2 — User-Visible Changes

**Phase:** goal-structure_ui-iter-2
**Date:** 2026-07-07
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now view the full strategy registry — both `v1` and `structure_tape` — directly on the `/structure` page, as two cards, without needing `curl` or an MCP tool to see it.
- Users can now see each strategy's entry rule and exit rules (`r_stop`, `reward_target` where the strategy defines one, `state_flip`, `horizon_seconds`, `dataset_end`) printed on the page.
- Users can now see, for `structure_tape` specifically, three small tables showing how its stop distance, reward target, and simulated position size scale across confluence classes A/B/C.
- Users can now see a "Champion" panel on `/structure` showing which strategy/profile pair is currently favored (today: `v1` on the `default` profile) — the same information previously visible only on `/performance`.
- Users can now read a one-line note confirming the champion shown on `/structure` agrees with the one shown on `/performance` (both are read from the same underlying record).
- Users can now see all of the above immediately on opening `/structure` — no symbol, no as-of time, and no click on the Load button is required; the Registry section fetches and renders on page load.
- Users now see an explicit "registry unavailable" message (rather than a blank area) if `/structure`'s new section can't reach the backend.

---

## What Changed in the Visible UI

- The `/structure` page now has a new **Registry** section, appended directly below the existing "Confluence zones" section (same page, no new route, no new nav entry).
- The Registry section shows two cards, one per strategy (`v1` and `structure_tape`), each headed by the strategy's id and listing: entry rule, `r_stop`, `reward_target` (only on `structure_tape` — `v1` genuinely has none, so its card omits that row rather than showing a blank or a zero), `state_flip`, `horizon (seconds)`, and `dataset_end`, plus a static caption describing the exit-check order.
- The `structure_tape` card additionally shows three labeled tables — "stop (bps by class)", "reward target (R-multiple by class)", "size (multiple by class)" — each listing a value per confluence class (currently A/B/C, e.g. stop bps A=1/B=5/C=10).
- A "Champion" panel appears at the top of the Registry section showing `strategy` and `profile` values, plus a small caption narrating whether this matches the champion shown by the `/research/profiles` data source.
- A short italicized note above the Champion panel states the section is read-only and every value is read verbatim from the backend — nothing is calculated in the browser.
- If the registry endpoint can't be reached, an amber "unavailable" panel takes the place of the whole Registry section, with the message "Backend unreachable — is the API running?" (or the backend's own error text) — no strategy cards, no champion badge, and no guessed `v1`/`default` fallback are shown in that state.
- While the fetch is in flight, a brief loading placeholder appears in the Registry section's place.

---

## What Old Behavior Changed

None. This iteration is purely additive to `/structure`:

- The existing Levels & Zones section above the new Registry section — the symbol/as-of form, the Load button, the price chart, the confluence-zones table, and its four existing honest states (needs-credentials, no-levels-found, no-qualifying-zone, backend-unreachable) — is byte-unchanged and behaves exactly as before.
- No other page (`/`, `/journal`, `/studies`, `/performance`) or the 5-link top navigation was touched.

One item is a **re-verification, not a change**, and testers should not expect new behavior here: a prior iteration's fix to `/structure`'s price-chart empty state (showing "No candles to draw at this as-of time." instead of a silent blank box when there are no bars to plot) was confirmed still present by direct code read this iteration — the component file itself (`StructureChart.tsx`) was not edited. Independent, live re-confirmation of that fix is this iteration's other deliverable, alongside the new Registry section.

---

## Not Visible Yet

- **Side-by-side backtest comparison** (`structure_tape` vs. `v1`, run on demand from the UI) — explicitly deferred to a future iteration; no comparison or backtest-triggering UI exists yet anywhere in the app.
- **Three of the four champion "cross-check" messages are not reachable in normal use today.** The Registry section is wired to show one of four distinct captions depending on whether the champion shown here agrees with the one on `/research/profiles` — "still checking," "cross-check unavailable," "confirmed match," or "mismatch" — but because both sources currently share the exact same underlying record, only "confirmed match" can actually appear; the other three exist as honest safety nets for a state the system cannot currently produce, not as gaps in what was built.
