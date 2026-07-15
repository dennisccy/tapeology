# Phase goal-tradable_wall-iter-8 — User-Visible Changes

**Phase:** goal-tradable_wall-iter-8
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

No new actions were added this iteration — the plan scoped it as cleanup + verification only, and the phase spec is explicit ("New user actions: None"). Every button, filter, toggle, and click path that existed before this iteration works the same way. What changed is what two already-existing screens now have to show when you use them:

- Users can click a Case Studies row on the Structure page exactly as before, but for the pinned AAPL / June 22 2026 case (the ~$300 resistance band) that click now has real recorded market data behind it instead of a placeholder.

---

## What Changed in the Visible UI

- **Structure page → Case Studies → row drill-in.** Clicking the AAPL row for the 2026-06-22 session used to open a drill-in panel whose "Tape timeline" area said "No recorded tape for this event." Now that the operator has real recorded market data for that exact window, the same panel is expected to show a real, populated timeline of tape readings (state names like Buyer Control / Seller Control / Bid Absorption / Ask Absorption, each with a timestamp) in place of that empty message — the reaction ("rejected") and forward-return numbers were already showing and are unchanged. **Caveat:** this panel replays the entire recorded window from scratch every time it is opened (nothing is cached) — expect it to sit in its loading skeleton for several minutes on the pinned AAPL case, not appear instantly.
- **Structure page → Edge Report.** This section used to render with zero rows — no dataset previously had real recorded data to measure against. With the operator's 11 newly recorded windows now in place, the report is expected to show real rows (strategy × class × side × outcome), with an honest "insufficient sample" tag on any row backed by fewer than 5 examples, instead of the fully-empty shape. **Important caveat:** as of this iteration, nobody has actually watched this section finish loading in a browser — see "What Old Behavior Changed" below for why that matters.
- **Cockpit `/` price chart** (only visible while watching a Simulated or Historical ticker — still fully hidden in Live mode, unchanged). A very brief, easy-to-miss timing glitch was removed: right when you start watching a ticker or a historical replay, there used to be a split-second where the chart could ask the server for tradable bands using TODAY's date instead of the replayed day's date, which could flash the wrong band/chip for an instant before it corrected itself a moment later. That flash can no longer happen — the chart now simply waits until it knows the correct date before it asks for bands at all.

---

## What Old Behavior Changed

- **Cockpit price chart band-request timing.** Previously, if the chart didn't yet know which trading session it was showing, it fell back to asking for "right now" (the browser's current date). Now it simply waits and issues no request at all until it genuinely knows the correct date. Once that date is known, the request made and the bands/chip shown are identical to before — this change only affects the split-second before that point.
- **Structure page load times, on a freshly started backend.** This isn't something this iteration's code changed, but it's a real, new experience users will have: because the Case Studies drill-in and the Edge Report now replay real, large recorded datasets instead of small synthetic/empty ones, they can take dramatically longer to load than before. The developer measured a single Case Studies drill-in click taking about 13 minutes on a cold run, and estimated a first full Edge Report load could take on the order of 10+ hours, with no progress indicator beyond a generic pulsing loading animation. This slowness was already flagged as a known issue in earlier iterations — it's simply far more noticeable now that real data exists to actually replay. If the Structure page appears "stuck" loading Case Studies or the Edge Report, that is the expected current behavior, not something broken — unless it never resolves after a genuinely extended wait.

---

## Not Visible Yet

- There is still no page listing the operator's raw recorded datasets (symbol, session date, feed, checksum, split, etc.) — the 11 real recordings are only visible indirectly, through the Case Studies drill-in and Edge Report content they feed. A dedicated datasets page remains explicitly out of scope for this iteration.
- The cockpit's confluence chip still only shows the fixed phrase "measured history: edge report" — it does not display any live number pulled from the Edge Report itself. Adding a real figure there was explicitly deferred, not built.
- The claim that the Edge Report "now shows real data" is based on the developer directly cross-checking the underlying data (every one of the 11 recorded datasets does match a scored event), not on watching the Structure page actually render the finished report in a browser. Whether it renders correctly, and how long it actually takes in practice, still needs to be confirmed by someone opening the page.
