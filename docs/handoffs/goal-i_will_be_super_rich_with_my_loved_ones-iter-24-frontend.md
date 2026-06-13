# goal-i_will_be_super_rich_with_my_loved_ones-iter-24 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-24
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built (UI)

Display + honesty labeling only — no new buttons, forms, controls, pages, routes, or nav changes.

- **Cockpit feed-basis badge** — `apps/frontend/components/FeedBasisBadge.tsx`, wired into
  `TopBar.tsx`'s `/` status area (gated behind `watched`, beside the watched-source indicator and
  the delivery-lag readout). Renders the served `snapshot.data_feed` (sim | iex | sip) VERBATIM
  with the taxonomy-owned per-feed label. When the served basis is the live IEX feed, the
  taxonomy-owned IEX-vs-SIP disclosure line renders beside it. Reads ONLY the served `data_feed`
  key — it never client-derives the basis from the `scenario` string.
- **Hint-log feed stamp** — `HintLog.tsx` gains a "Feed" column (header from the taxonomy
  `log_columns.feed`, value = each row's persisted `data_feed` stamp rendered verbatim with the
  taxonomy per-feed label).

## States Handled

- **Honest absence (no watch):** `TopBar` only mounts the badge when `watched` is true, and the
  badge itself self-guards (`if (!dataFeed) return null`) — so an idle cockpit shows NO badge and
  NO fabricated "live"/"iex" guess.
- **Pre-J-67 backend / taxonomy not loaded:** `data_feed` is optional on `TapeSnapshot`; an absent
  value renders nothing. The per-feed label falls back to the raw feed id if the taxonomy
  `feed_basis` block is missing (an honest, never-fabricated value). The hint-log column header
  falls back to "Feed".
- **Live disclosure conditional:** the disclosure line renders ONLY when the served basis is
  `iex` — so an operator who upgrades live to SIP (serving `sip`) correctly stops showing the IEX
  disclosure with zero frontend change.
- **Taxonomy fetch is lazy:** the badge requests `/research/taxonomy` only once a basis is actually
  served, so the idle cockpit costs no request.

## Design-System Conformance

- Neutral **slate** chip for both the badge and the hint-log stamp (a factual data-source stamp is
  NOT a side/impact signal, so it must not borrow the emerald/rose/amber side palette).
- `font-mono` on the feed label/stamp (numerics + identifiers register), muted slate for the
  disclosure line, Tailwind tokens only (`bg-slate-800`, `text-slate-300`, `text-slate-500`, the
  4px spacing grid) — no arbitrary values, no new visual effect.
- Copy discipline (J-66): the badge/stamp add no imperative or predictive word of their own — every
  visible string is backend-owned (the per-feed label + the disclosure line), proven clean by the
  backend `test_taxonomy_serves_feed_basis_copy_canary` forbidden-word scan.

## Data Flow

`snapshot.data_feed` reaches the UI by two paths, both verbatim, never recomputed:
- **REST initial snapshot:** `fetchInitialSnapshot` reads `summary.data_feed` into the `TapeSnapshot`.
- **WS frames:** `useTapeStream` parses each frame as `TapeSnapshot` directly (`JSON.parse`), and
  the backend's `serialize_stream` now includes `data_feed` from the SAME single mapping as
  `/summary` — so the badge reads one canonical basis identically across REST and WS.

## Tests Run

Type-check: `cd apps/frontend && node_modules/.bin/tsc --noEmit` → exit 0 (zero type errors).
Used `tsc --noEmit` rather than `npm run build` to avoid touching a shared `.next` (memorialized
QA caution); no tapeology dev server was running regardless.

## Known Issues

- None. User-visible behavior is covered by browser QA (no frontend unit suite). The live-declared
  `iex`-stamp confirmation is the credential-gated browser leg documented in the dev handoff — to
  be verified or documented by browser-qa, never faked.
