# Phase N — User-Visible Changes

**Phase:** goal-i_will_be_rich-iter-5
**Date:** 2026-06-03
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now watch `SIM-BIDABS` (type it into the top-bar **Ticker** field and click **Watch**) and see the cockpit settle on **Bid Absorption** in amber — heavy selling is hitting the bid but the price holds, so the system reads *absorption*, not *seller control*.
- Users can now watch `SIM-ASKABS` and see the cockpit settle on **Ask Absorption** in amber — heavy buying into an offer that holds, so the price stalls rather than rising.
- Users can now read three new feature rows in the **Features** panel — **Absorption score**, **Bid refresh score**, **Ask refresh score** — the numbers that justify an absorption call (high one-sided aggression + flat price impact + a refreshing quote).
- Users can now see an absorption message in the **Event log** when an absorption read occurs — e.g. "Large sell print absorbed" and "Bid refreshing at 100.00" (real in-window values), alongside the existing "Tape state changed to …" line.
- Users can now trust the top-bar **stream-status dot**: it reflects the engine's authoritative stream status (connecting / live / stale / closed), so when a bounded sim stream ends the dot turns to **closed** instead of falsely staying "live".

---

## What Changed in the Visible UI

- The **Features** panel (`FeaturesPanel`) now shows **twelve** rows instead of nine — three rows (`Absorption score`, `Bid refresh score`, `Ask refresh score`) were appended below `Large prints`, rendered as monospaced neutral (slate) numerics at 3 decimals; an absent value shows "—".
- The **Tape-state** panel now reaches two previously-unreachable amber states, **Bid Absorption** and **Ask Absorption**, each with its confidence value and amber headline (`text-amber-400`) / confidence-bar (`bg-amber-500`).
- The **Event log** and **Observations** panels now display absorption-specific lines (e.g. "Large sell print absorbed", "Bid refreshing at <price>") on an absorption read.
- The top-bar **status dot** and its label (top-right of the `TopBar`) now derive from `snapshot.stream_status` whenever a snapshot is present, falling back to the client connection status only before the first snapshot arrives.

---

## What Old Behavior Changed

- **Top-bar status dot:** previously it showed only the browser's view of the WebSocket connection (`connStatus`), which could read "live" even after the underlying tape stream had closed. Now, once a snapshot is present, it shows the engine's canonical `stream_status` and tells the truth when a stream ends. The live dot on the SIM-BUYER / SIM-SELLER scenarios is unaffected.
- **`SIM-BIDABS` / `SIM-ASKABS` tickers:** previously these were known tickers that produced no data, so the read stayed an honest "unclear". Now they drive their full absorption scenarios and resolve to bid/ask absorption.
- **Features panel length:** previously nine feature rows; now twelve. The existing nine rows and their values are unchanged.

---

## Not Visible Yet

- The `stale` stream-status value is mapped to a dot color/label defensively, but no backend path currently emits `stream_status = "stale"` (no provider-gap detector yet), so the dot shows connecting / live / closed in practice.
- `SIM-CHOP` remains a known ticker that produces no data (reads as honest "unclear"); an *actively* choppy driven stream is deferred to J-06.
- No "Stop watching" / un-watch control is exposed (J-09); the stream-status-dot work here is groundwork for it.
- The `spread_change` and `liquidity_imbalance` features are not built, so they do not appear in the Features panel.
