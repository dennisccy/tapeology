# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-29 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-29
**Date:** 2026-06-16
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

No new capabilities were added this iteration. All user actions described below already existed in the product. This iteration confirmed they work correctly against a real live market feed during open US market hours.

---

## What Changed in the Visible UI

No UI source files changed. The application is byte-for-byte identical to the previous iteration. The following surfaces were verified to function correctly on a real live IEX feed — their behavior is unchanged, but their correctness on a live feed was proven for the first time:

- The `/` cockpit status area live status indicator correctly displays `live` (green treatment) when a real IEX stock feed is actively delivering data, switches to `stale` (amber/neutral treatment, visibly distinct) when the feed goes quiet for more than ten seconds, and recovers back to `live` the moment new market data arrives — all observed on a real IBM/Ford IEX feed.
- The `/` cockpit `FeedBasisBadge` correctly renders "IEX (live)" with the IEX-vs-SIP disclosure line ("live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ") when the active watch is on a live IEX stream.
- The `/journal` table rows correctly display `data_feed = iex` on thesis rows produced during a live IEX watch, confirming live (IEX) and historical (SIP) records are never pooled together.

---

## What Old Behavior Changed

None. No existing behavior changed. The application code is identical to before this iteration.

---

## Not Visible Yet

None. Every capability verified this iteration was already exposed in the UI. The binding canonical proof (REST `stream_status` sequence, live integration test) is backend evidence; the corresponding UI surfaces that display those values were verified to render correctly.

The browser pixel screenshots of the `stale` indicator, the live `FeedBasisBadge`, and the `iex`-stamped journal row are the downstream browser-QA step — the surfaces exist and are functional; the pixel capture is the evidence artifact, not a new capability.
