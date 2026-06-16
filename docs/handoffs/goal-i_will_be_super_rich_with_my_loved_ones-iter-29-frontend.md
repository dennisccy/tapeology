# goal-i_will_be_super_rich_with_my_loved_ones-iter-29 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-29
**Date:** 2026-06-16
**Agent:** developer
**Status:** complete

## Nature of this iteration (frontend)

**No frontend source change.** This is a verification-only pass that exercises EXISTING UI
surfaces against a real live IEX feed. No new page, panel, control, component, style token, or
effect was added. The live status indicator and the `FeedBasisBadge` already render; this
iteration proves they work on a real feed.

## UI Surfaces Exercised (unchanged, verified on a real live feed)

- **`/` cockpit status area — live status indicator (J-15):** reads the canonical row-6
  `stream_status` (`connecting | live | stale | paused | closed`). On the live IBM watch the
  backend's canonical `GET /tape/IBM/summary` flipped `live → stale → live` across genuine IEX
  record lulls (see the dev handoff and `…-iter-29-evidence/j15-stale-sequence-rest.md`). The UI
  renders that value verbatim; `stale` is the degraded (amber/neutral) treatment, visibly distinct
  from `live` (green) in the same status area per the DESIGN SYSTEM color semantics. No UI-side
  derivation — the frontend reads the single canonical value.
- **`/` cockpit status area — `FeedBasisBadge` (J-67):** `components/FeedBasisBadge.tsx` reads
  the snapshot's `data_feed` (row 29) and, when it is `iex`, renders the IEX label plus the
  IEX-vs-SIP disclosure line owned by `GET /research/taxonomy`'s `feed_basis` block ("live
  verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and
  prints differ"). The live IBM watch served `data_feed: "iex"`, so this badge + disclosure
  render over the live cockpit. The frontend hardcodes none of the copy — it reads the
  taxonomy-owned strings.
- **`/journal` rows (J-67):** the live-declared thesis produced a journal row whose `data_feed`
  stamp is `iex` (proving no SIP/IEX pooling). The `/journal` table renders the stored stamp
  verbatim.

## Files Changed (frontend)

- **None.** Verified with a LIVE `git status --porcelain apps/frontend/` (empty) and
  `git diff --stat HEAD -- apps/frontend/` (empty).

## Browser pixel evidence

The pixel capture (a still that VISIBLY contains the `stale` indicator across a real lull; the
live `FeedBasisBadge` + IEX disclosure in the viewport; the `data_feed = iex` journal row) is the
downstream browser-QA leg. The binding canonical proof is the REST `stream_status` sequence + the
gated integration run (both captured in the dev handoff). Capture discipline for the transient
`stale` state: hold/await-stabilize the still during one of the multi-second stale spans (a 15s
span was observed), prefer full-page stills, and `md5sum` the evidence dir before citing
(iter-22/iter-14 lesson).

## Known Issues

- The `stale` indicator is transient on a liquid IEX name (the next quote recovers `live` within
  seconds). Quieter names / off-peak minutes lull >10s comfortably; IBM produced repeated
  multi-second stale spans this session.
- No frontend defect was surfaced on the real live feed — the badge renders over a live IEX
  watch and `stale` is visibly distinct from `live`, so the conditional fix-in-place scope did
  not trigger.
