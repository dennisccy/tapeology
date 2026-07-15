# Phase goal-tradable_wall-iter-7 — User-Visible Changes

**Phase:** goal-tradable_wall-iter-7
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see the watched symbol's tradable support/resistance bands drawn directly on the
  **cockpit price chart** — the `/` page's existing "Price Chart — Tape-State Markers" panel —
  while watching a symbol in **Simulated** or **Historical** mode. Previously these bands were
  visible only on the separate `/structure` page (shipped in iter-6/J-05); the cockpit is where the
  operator actually watches a symbol live or replayed, so the tradable wall is now visible at the
  moment and place trades are watched, not only on a separate research page.
- Users can now see a **descriptive confluence chip** appear below the cockpit chart at the moment
  the last traded price sits inside one of those bands AND the current tape reading matches that
  band's configured rejection/breakthrough state. The frontend handoff documents the chip's exact
  copy format: *"Inside R-band 300.05–300.17 (class A) · tape: Ask Absorption (rejection) ·
  measured history: edge report."* The chip never tells the user to buy/sell and never predicts an
  outcome — it only states the current condition and points to the Edge Report as measured history.
  (See "Not Visible Yet" below — this exact chip firing was not personally witnessed on screen
  during this iteration's own verification session, only the mechanism and its inputs.)
- Users watching one of the built-in **simulated tickers** (e.g. `SIM-BUYER`, which has no real
  recorded bar history) now see an explicit **"No tradable map for SIM-BUYER."** hint below the
  chart, instead of the area simply showing nothing — confirming there genuinely is no map for that
  symbol rather than leaving the user to guess whether the feature is broken.

---

## What Changed in the Visible UI

- The cockpit's existing **"Price Chart — Tape-State Markers"** panel (shown only in
  Simulated/Historical mode, unchanged) now draws one or two **solid** horizontal price lines per
  tradable band on the same chart canvas as the candles and tape-state markers — rose-colored for
  resistance bands, emerald for support bands — each labeled via the chart's axis label with
  side/class/quality-score/round-number (e.g. "R class A · score 153 · round"). These solid band
  lines sit alongside, and are visually distinct from, the chart's pre-existing **dashed** thesis
  price-lines (the user's own declared trade thesis, unchanged).
- A new small slate-gray text banner (the confluence chip, `data-testid="confluence-chip"`) can
  appear directly beneath the chart canvas, inside the same panel — never overlapping the candles or
  markers — describing the band/tape-state condition currently in effect.
- A new small inline hint ("No tradable map for {ticker}.", `data-testid="no-tradable-map"`) can
  appear in the same location for tickers with no resolvable band map.
- No new page, no new route, no new navigation entry, and no new button/form/control anywhere —
  every addition is a passive, display-only layer on the existing cockpit chart panel. The bar-size
  selector and the Watch flow are unchanged.

---

## What Old Behavior Changed

- None to the chart's own pre-existing content: candles, the five-state tape-state markers, and the
  user's own dashed thesis price-lines on the cockpit chart render exactly as they did before this
  iteration — the band overlay, chip, and empty hint are purely additive underneath them. The
  fetches that populate them are non-blocking: if the bands request fails or is still loading, the
  chart and markers render exactly as before, with no overlay and no chip.
- **Live mode is unchanged.** The whole "Price Chart — Tape-State Markers" panel — old elements and
  new ones alike — still does not render at all when watching a symbol in Live mode; the pre-existing
  mode gate in `page.tsx` that hides the chart in Live mode was not touched by this iteration
  (verified live by the developer: watching AAPL in Live mode showed no "Price Chart" section in the
  DOM at all).
- `/structure`'s own Tradable Map (iter-6/J-05) is unaffected — no file under
  `apps/frontend/app/structure/` changed in this iteration.

---

## Not Visible Yet

- No backend capability is newly exposed by this iteration — every value the overlay and chip read
  (`GET /research/tradability`, `GET /research/strategies`, `GET /tape/{ticker}/history`) was
  already fully implemented and already shown somewhere in the product (on `/structure`) before this
  iteration. This iteration is pure UI wiring of already-existing endpoints into a new surface (the
  cockpit), not new backend capability.
- **Verification gap worth flagging for downstream testers/QA:** the developer confirmed the band
  overlay itself renders correctly — including during a real credentialed historical replay of the
  pinned AAPL 2026-06-22 session, correctly resolving to the 2026-06-18 prior-session basis — but did
  not personally witness the confluence chip actually appear on screen during that session. Price
  approached the drawn band, but the observation window did not happen to catch the exact moment the
  tape state also matched the mapped confirming state. The chip's matching logic is wired to real,
  verbatim served data and is covered by 9 keyless source-inspection tests
  (`apps/backend/tests/test_price_chart_confluence.py`), but a real "chip visibly appears on screen"
  screenshot from a live/credentialed session is still outstanding — the natural next browser-QA
  target, per the phase's own Testing Requirements.
