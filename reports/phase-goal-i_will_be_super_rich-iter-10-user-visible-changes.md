# Phase goal-i_will_be_super_rich-iter-10 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-10
**Date:** 2026-06-07
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- When a watch connects but no trade has arrived yet (quiet symbol, off-hours market, or the brief moment right after clicking Watch), the user now sees an explicit "Waiting for the first trade…" screen labelled with the ticker symbol and data-source mode (Simulated / Live / Historical), instead of a wall of blank panels or a misleading "live" cockpit.
- When a data feed fails in the background after a successful Watch connection (for example, the backend drops the feed mid-session), the user now sees an explicit red error screen ("The tape feed failed after connecting. No tape is shown.") with a rose-coloured warning icon, instead of a frozen or silently blank cockpit.
- After a live watch connects but never receives a trade (off-hours or quiet symbol), the user now sees the connection eventually advance from "waiting" to "stale" automatically, giving an honest terminal state rather than an endless in-progress spinner.

---

## What Changed in the Visible UI

- The cockpit area at `/` gained a new **"Waiting for the first trade…" screen** (amber pulsing dot, monospaced ticker, mode label, explanatory text). This replaces what was previously a blank or misleading panel grid when the stream was connected but empty.
- The **status dot in the TopBar** gained two new states:
  - `waiting` — amber with a pulsing animation, reading the label "waiting" (never "live") while the connection is open but no first trade has arrived.
  - `failed` (snapshot-borne) — rose coloured, reading the label "failed" when the background feeder raises after connecting (distinct from the existing pre-snapshot connect failure dot, which also reads "failed" but is driven by the client connection status).
- The **price chart** is now hidden during the `waiting` and snapshot-borne `failed` states (in addition to the existing pre-snapshot failure state), ensuring no blank or fabricated chart is shown while the tape is empty.
- The **error banner** in the TopBar now also displays a message for a snapshot-borne failure: "The tape feed failed after connecting. No tape is shown."

---

## What Old Behavior Changed

- **The cockpit after a successful Watch with an empty tape**: previously, once any snapshot existed the app would render the full panel grid (quote, trades, features, state, observations, event log) — often a grid of blank or zeroed panels — which could look like a settled "live" cockpit over an empty tape. Now an empty, just-connected snapshot arrives carrying `stream_status === "waiting"` and the cockpit shows the explicit waiting screen instead. The full panel grid is only rendered once real trade and quote data has arrived.
- **Status dot truthfulness during the connect-but-quiet phase**: previously the dot could briefly show "live" or remain on "connecting" over an empty tape. Now it reads "waiting" (amber pulse) during this phase and advances to the correct terminal state ("live", "stale", or "failed") once the engine resolves.
- **Background feeder failure**: previously a feeder that raised an exception after connecting would leave the cockpit frozen (status unchanged, panels silent). Now it surfaces `stream_status === "failed"` in the snapshot, triggering the explicit failure screen and error banner.

---

## Not Visible Yet

- **J-28 / J-29 / J-30 (vendor responsiveness)**: making individual vendor API calls time out at the network level, loading busy historical windows faster, and a faster symbol search are explicitly deferred to a future iteration. No UI change related to these capabilities exists yet.
- **Pause during the waiting phase**: the Pause button remains hidden while `stream_status === "waiting"` (Pause only activates during connecting / live / stale). Stop is available throughout. This is intentional scope discipline, not a bug.
