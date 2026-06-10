# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-5 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-5
**Date:** 2026-06-10
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Declare a thesis on the real, running installation by watching a ticker (e.g. SIM-BIDABS), filling in the declare form on the Cockpit (`/`), and submitting — the strip now returns the active thesis view instead of a server error.
- Watch the verdict chip update live (pending → confirming / weakening / rejecting / invalidated) in the thesis strip after declaring, because the backend persistence layer now accepts the declaration and starts the verdict engine.
- See the evidence line, frozen expected-behaviour statement statuses, bound source, and data-feed stamp in the active thesis view — all built in iter-4 but unreachable until now.
- Trigger and read inline validation messages (wrong-side invalidation, missing level, forbidden level, second active thesis) in-pixels in the declare form — these were always coded but only reachable once declaration itself works.
- Observe the terminal invalidated treatment (heavier rose chip, offending print as evidence) in the strip when the thesis is invalidated — this state was built in iter-4 and is now reachable on the persistent installation.

---

## What Changed in the Visible UI

- The thesis strip (`ThesisStrip` at `/`) now has a `data-testid="thesis-strip"` attribute on its root `<section>` element — this covers every strip state (idle declare affordance, loading, error, active thesis). No visual change; the strip looks identical.
- The thesis strip switches from the idle declare-affordance view to the active thesis view on a successful declaration — a transition that was blocked in iter-4 (always returned a server error on the persistent installation) and is now reachable for the first time.
- The verdict chip (pending: slate, confirming: emerald, weakening: amber, rejecting/invalidated: rose with terminal ring) and the evidence line render from live persisted data on the first successful declare.

---

## What Old Behavior Changed

- **Thesis declaration (`POST /research/thesis`):** Previously returned a 503 server error against the real saved journal (the persistent `tapeology_journal.db`). Now returns HTTP 200 with the full active-thesis projection. The response shape is unchanged — the endpoint simply stops failing.
- **App startup — orphan sweep:** Two previously stranded "active" theses (zero verdict events, left by the iter-4 atomicity defect) now automatically become "expired" on startup, clearing the 409 block they caused on SIM-BUYER and SIM-SELLER. Their rows are kept in the journal; they are never deleted.
- **Thesis declaration — all-or-nothing recording:** If anything fails while recording a new thesis, neither the thesis row nor its initial verdict event is saved. Previously the two could be saved independently, leaving a half-recorded thesis that blocked subsequent declarations on the same ticker.

---

## Not Visible Yet

- None. All backend changes in this iteration directly unblock existing on-screen UI that was already built in iter-4. There is no new backend capability without a corresponding UI surface.
