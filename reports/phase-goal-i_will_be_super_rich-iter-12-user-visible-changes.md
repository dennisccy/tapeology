# Phase goal-i_will_be_super_rich-iter-12 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-12
**Date:** 2026-06-08
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Read the price chart's time axis as actual market clock times (e.g. `08-06-2024 09:30:45`) instead of a raw counter climbing from 0 to 600 seconds. For a historical replay this is the real market time; for a simulated scenario it is a synthetic session clock starting at 09:30.
- Hover over any candle on the price chart and see the crosshair tooltip display the true clock date and time (`dd-MM-yyyy HH:mm:ss`, 24-hour, local zone) rather than an elapsed-seconds count.
- Read tape-state-marker timestamps on the chart in the same true clock format (`dd-MM-yyyy HH:mm:ss`), making it possible to tell when a labeled state (buyer control, seller control, absorption, etc.) occurred in real market time.
- Switch bar size between 10, 30, and 60 seconds while watching a historical or simulated tape and continue reading the chart's time axis in real clock time at each bar size.
- Enter historical dates in the `dd-MM-yyyy` format (e.g. `08-06-2024`) in the Historical date field, replacing the browser's native date picker whose format varied by locale.
- See inline validation when typing an impossible or malformed date (e.g. `31-02-2026`, a misspelling, or an empty field) — the field border turns amber and an error message appears; the Watch button stays disabled until the date is corrected.

---

## What Changed in the Visible UI

- **Price-chart time axis (` / ` home cockpit):** Axis tick labels changed from elapsed playback seconds (`0`, `60`, `120`, … `600`) to formatted clock times (`dd-MM-yyyy HH:mm:ss`, local zone). The crosshair and tape-state marker labels changed in the same way.
- **Historical date field (` / ` home cockpit, Historical mode):** The native browser `<input type="date">` (which showed in the browser's own locale format and depended on the OS date picker) is replaced by a plain text field with a `dd-MM-yyyy` placeholder. An amber border and inline message appear when the entry is invalid.
- **Market-status "next open" time (` / ` home cockpit, Live mode — when market is closed):** Dates that previously appeared in a locale-dependent "Jun 8" or ISO `YYYY-MM-DD` format now read `dd-MM-yyyy HH:mm` followed by the local UTC-offset label (e.g. `08-06-2024 09:30 UTC+08:00`).
- **Watched-source descriptor (` / ` home cockpit, top of the cockpit panel):** For historical watches the descriptor previously exposed raw ISO-8601 timestamps embedded in the string (e.g. `historical AAPL 2024-05-14T13:30:00.000Z–...Z`). It now shows `dd-MM-yyyy HH:mm` forms (e.g. `historical AAPL 14-05-2024 13:30–...`).

---

## What Old Behavior Changed

- **Price-chart time axis:** Previously labeled with elapsed logical playback seconds (the horizontal axis read `0 … 600`). Now labeled with `dd-MM-yyyy HH:mm:ss` clock times derived from the session's epoch anchor. The chart still reads the same `/history` data and computes no additional prices or states.
- **Historical date entry:** Previously used the browser's built-in date picker, which accepts dates in the browser/OS locale format (`MM/DD/YYYY` on some systems). Now always expects typed `dd-MM-yyyy` input. The resolved window (i.e. which point in time is actually fetched) is unchanged — the new field still resolves through the same row-12 timezone-aware resolver, so no UTC shift is introduced.
- **Market-status and closed-market panel date display:** Previously rendered dates in a locale-dependent "Jun 8" or ISO format via the old `formatMarketTime`. Now renders `dd-MM-yyyy HH:mm` with an explicit UTC-offset zone label via the shared formatter.
- **Historical watched-source descriptor:** Previously showed raw machine ISO instants inline (e.g. `2024-05-14T13:30:00.000Z`). Now reformats those to `dd-MM-yyyy HH:mm` (local zone) before display. The underlying watch source is unchanged.

---

## Not Visible Yet

- The `epoch_anchor` value is now included in the backend's `GET /tape/{ticker}/history` response. This is fully consumed by the chart — there is no backend capability that remains un-surfaced.
- **Recent-trades and event-log rows** have no timestamp column today, so J-35's "date format" requirement does not surface any change there. If a future iteration adds a trade-time column it will need to use `formatDateTimeDMY` plus the epoch anchor — that is not yet built.
