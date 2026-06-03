# goal-i_will_be_rich-iter-7 Frontend Handoff

**Phase:** goal-i_will_be_rich-iter-7
**Date:** 2026-06-03
**Agent:** developer
**Status:** complete

## What Was Built (UI)

The first real frontend code change since iter-1: a **Stop** control that completes the watch
lifecycle in the UI (start → read → **stop** → re-start).

- **Stop button** in the top bar — appears only while a ticker is watched, sitting immediately
  after the "Watching <TICKER>" label. Clicking it stops watching and returns the screen to the
  idle/empty state ("No ticker watched") with no stale numbers and no frozen last frame.
- **No new value, no new panel, no new route.** Everything stays on `/`. The cockpit/idle toggle
  and the status dot already existed; this iteration only adds the action that drives the cockpit
  back to idle on demand.

## How it works (data flow)

1. Click **Stop** → `TopBar` fires `onStop` → `page.tsx#handleStop`.
2. `handleStop` calls `stopTicker(ticker)` (`DELETE /watch/{ticker}`), then `setTicker(null)` and
   clears any error banner.
3. `setTicker(null)` does two things at once:
   - the page body switches from `<Cockpit/>` to `<IdleState/>`;
   - `useTapeStream(null)` runs its effect cleanup, which **closes the WebSocket client-side** —
     this is the "no further updates" mechanism and does **not** depend on the server closing the
     socket.
4. Re-entering a ticker and pressing **Watch** starts a fresh read from cold (the backend built a
   brand-new engine because Stop removed the old one).

`stopTicker` treats a **404 as effectively-stopped** (the ticker is not watched either way) and,
on a network failure, the UI still returns to idle — idle is the truthful end state regardless.

## Files Changed

- `apps/frontend/lib/api.ts` — add `StopResult` interface and `stopTicker(ticker)` (mirrors
  `watchTicker`'s shape and error handling; 404 = success).
- `apps/frontend/components/TopBar.tsx` — add `onStop: () => void` prop and the **Stop** button
  inside the existing `{watched && …}` block.
- `apps/frontend/app/page.tsx` — add `handleStop`, import `stopTicker`, pass `onStop={handleStop}`.

## Visual / Design-system compliance

- **Style:** restrained **rose ghost** button (rose text + rose/70 border, transparent surface),
  matching the design system's `rose = stop / sell-side` semantic and the hand-built TopBar idiom
  (no component library in this project).
- **Static Tailwind class only** (iter-2/iter-3 lesson): the `className` is a single literal
  string — never runtime-concatenated — so the JIT scanner emits every variant. Confirmed present
  in the built CSS bundle: `border-rose-500/70`, `hover:bg-rose-500/10`, `active:bg-rose-500/20`,
  `hover:text-rose-300`, `focus:ring-rose-400`.
- **Interaction states:** hover (rose tint + brighter text), focus (rose ring, no default
  outline), active (deeper rose tint) — all present.
- **States handled:** the button is **absent** in idle (only rendered when `watched` is set); on
  click the cockpit empties to `<IdleState/>` and the status dot returns to **idle**;
  `stopTicker` failure/404 still returns the UI to idle.
- Accessibility: `aria-label="Stop watching"`.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: **passed** — compiled successfully, type-check clean, 4/4 static pages generated.
Dev-server boot check: `next dev` started clean and served `GET / → 200` (then killed).

## Known Issues

- None. Browser-driven J-09 verification (cockpit-live → press Stop → post-Stop idle → re-watch
  fresh, with evidence screenshots) is the designated gate and runs in the browser-qa stage. To
  reliably catch the "still live" window, that run MAY widen delivery pacing via
  `TAPEOLOGY_FEED_PACE=0.12` (delivery pacing only — does not change classification determinism);
  the idle-return and re-watch-fresh assertions hold even if the bounded stream exhausts before
  the click, because the Stop handler drives idle client-side regardless of server stream state.
