# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-4 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-4
**Date:** 2026-06-10
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Watch a live, colored verdict chip on the thesis strip update in real time after declaring a
  thesis — the chip transitions from "pending" (slate) to "confirming" (emerald), "weakening"
  (amber), or "rejecting" (rose) as the tape evolves, without any page reload.
- Read a plain-language sentence beneath the verdict chip at all times (including while pending)
  that explains in present-tense what the tape is doing relative to the declared thesis — for
  example "buyers keep pressing price up (buy_price_impact +0.4000); the tape confirms your
  thesis."
- See an unambiguous terminal treatment when a thesis is invalidated by a decisive price print
  through the declared invalidation level — the strip shows a rose ringed chip prefixed with "✕",
  a "Thesis invalidated — resolved" notice line, and the offending evidence sentence, so the
  outcome is explicit and visible.
- Distinguish between a thesis that expired (watch stopped — strip returns to the idle declare
  affordance) and one that was invalidated (strip stays with the terminal rose treatment — never
  silently reverts to idle).

---

## What Changed in the Visible UI

- The thesis strip on the cockpit home (`/`) now shows a colored verdict chip (`data-testid="verdict-chip"`)
  in the top-right of the active-thesis row — previously this chip always showed a fixed "pending"
  badge in slate regardless of tape state.
- A plain-language evidence sentence (`data-testid="verdict-evidence"`) now appears beneath the
  thesis strip header row for every verdict state, color-matched to the chip (emerald for
  confirming, amber for weakening, rose for rejecting/invalidated, slate for pending).
- When the verdict is `invalidated`, the verdict chip gains a heavier ringed rose border
  (`ring-1 ring-rose-500/50`) and an "✕" prefix, and a second line reading
  "Thesis invalidated — resolved" appears in rose below the evidence sentence.
- The taxonomy is now fetched on the frontend whenever a thesis is active (not only when the
  declare form is opened), so verdict label copy is always taxonomy-owned and never blocked
  by the catalog load.

---

## What Old Behavior Changed

- **Verdict chip on the thesis strip**: Previously the active thesis always displayed a static
  "pending" chip in slate, regardless of how long the tape had been running or what the tape was
  doing. Now the chip reflects the live published verdict with its associated color semantics
  (confirming emerald / weakening amber / rejecting rose / invalidated rose terminal).
- **Post-invalidation strip display**: Previously when a thesis was resolved (for any reason) the
  strip silently reverted to the idle "Declare thesis" affordance. Now an *invalidated* thesis
  keeps the terminal treatment visible (rose chip, "Thesis invalidated — resolved" notice,
  offending evidence) until the user starts a new watch session. Only an *expired* thesis
  (watch stopped / stream ended) still clears the strip to idle.

---

## Not Visible Yet

- `GET /research/journal/{id}` — a new API endpoint that returns the complete append-only verdict
  timeline for a thesis (each verdict transition with timestamps and evidence). There is no
  dedicated journal page in the UI; the cockpit reads the live verdict over the existing WebSocket
  stream. This endpoint is available for a future timeline/review page.
