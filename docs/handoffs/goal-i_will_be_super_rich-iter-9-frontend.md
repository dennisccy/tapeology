# goal-i_will_be_super_rich-iter-9 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-9
**Date:** 2026-06-06
**Agent:** developer
**Status:** complete

## What Was Built (UI)

All changes live on `/` (the single tape-cockpit screen). No new route, page, component library,
or execution affordance. Existing affordances are reused, not forked.

- **Pending "Connecting to <SYMBOL>…" cockpit state (J-21):** the instant Watch is clicked the
  cockpit leaves the idle screen and shows the symbol with the amber pulsing connecting dot
  (`ConnectingState({ symbol })`). Set synchronously before any network round-trip, in sim / live /
  historical modes. The TopBar status dot reads "connecting" during this window.
- **Bounded timeout / connect-failure error (J-22 / J-23):** a client-side `AbortController`
  (timeout from the single `WATCH_REQUEST_TIMEOUT_MS` constant) turns a slow/hung request into a
  visible "Market data provider timed out…" banner. A failed initial snapshot fetch or a
  pre-snapshot WS error/close surfaces an explicit "Couldn't connect to the tape stream" — both a
  new `StreamFailedState` cockpit treatment (rose ⚠) and the reused TopBar error banner, with the
  status dot reading "failed" (rose). No spinner runs indefinitely; no failure is swallowed.
- **Inline input validation (J-24):** the Watch button is disabled and an inline amber message
  ("Enter a ticker symbol" / "Choose a valid time window") shows when the symbol is empty/whitespace
  or (Historical) the date/time window is missing or invalid (`end <= start`). The message clears as
  soon as the offending field changes.

## Files Changed

- `apps/frontend/lib/config.ts` -- `WATCH_REQUEST_TIMEOUT_MS`.
- `apps/frontend/lib/api.ts` -- `fetchWithTimeout` / `RequestTimeoutError` / `isTimeoutError`; timeout-aware `watchTicker` + `fetchInitialSnapshot`.
- `apps/frontend/lib/useTapeStream.ts` -- non-swallowed snapshot failure, `failed` status + `connError`, pre-snapshot WS failure surfaced.
- `apps/frontend/lib/types.ts` -- `ConnStatus` gains `"failed"`.
- `apps/frontend/app/page.tsx` -- synchronous `pending` acknowledgement; render Connecting / StreamFailed; route errors to the banner; empty-symbol guard.
- `apps/frontend/components/IdleState.tsx` -- `ConnectingState(symbol)`, new `StreamFailedState`.
- `apps/frontend/components/TopBar.tsx` -- inline validation + disabled Watch + `failed` dot.

## Design System Conformance

- Connecting / pending / validation use **amber** (needs-attention / unclear), connect-failure uses
  **rose** (negative) — the load-bearing palette from `.claude/project-template.md`. No new effects,
  no raw arbitrary color values; monospaced numerics unchanged.
- The pending and failure states occupy the same cockpit real estate as the existing idle/error
  treatments; the error banner is the existing TopBar banner. Single-column / panel-grid layout
  unchanged.

## States Handled

pending/connecting (new, first-class), bounded timeout error, connect-failure (new), inline
validation (new), plus the existing idle / cockpit / honest non-cockpit (`ProviderUnavailable`) /
paused states — no regression intended to J-14 honest panels or J-19 pause/resume.

## Single-Source-of-Truth Guard

The pending / timeout / connect-failure / validation states are pure UI presentation. None recompute
an engine value (state / confidence / features / spread); once data arrives the cockpit renders the
engine snapshot verbatim. `provider_timeout` is an additive row-9 reason on the one `POST /watch`
failure path — not a second producer.

## Verification Note

No JS unit-test runner in this project (`.claude/project-template.md`: frontend behavior is covered
by browser QA). `npx tsc --noEmit` passes clean. The browser-qa-agent must verify J-21–J-24 and
re-verify J-01/J-09/J-10/J-14 in an ISOLATED `NEXT_DIST_DIR` (never the shared `.next` on `:3650`),
capturing real rendered screenshots of the pending, bounded-error, and inline-validation states.
