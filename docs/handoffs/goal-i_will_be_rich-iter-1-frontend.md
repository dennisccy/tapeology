# goal-i_will_be_rich-iter-1 Frontend Handoff

**Phase:** goal-i_will_be_rich-iter-1
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## What Was Built

The first build of the `/` **tape cockpit** (Next.js 15 App Router + TypeScript + Tailwind v3).

**App shell (persistent top bar)** — app name **Tapeology**; a ticker input + **Watch** button
that issues `POST /watch/{ticker}`; a watched-ticker label; a scenario indicator
(`scenario: buyer_control`); and a stream-status dot (idle / connecting / live / closed).

**Six panels** (responsive grid: 1 col → 2 col `md` → 3 col `lg`):
- **Tape State** — large color-coded state label + confidence (decimal) + a confidence bar; a "Warming up…" note before the warm-up floor.
- **Quote** — bid (green) / ask (red) / spread / last, monospaced.
- **Features** — a per-window selector (10s / 30s / 60s / 180s / 300s, defaults to the engine's primary window) and the nine implemented features; buy/sell price impact and net volume are color-coded by sign.
- **Recent Trades** — a price / size / side table; rows colored green (buy) / red (sell) / slate (unknown) by aggressor side.
- **Observations** — the engine's current human-readable evidence list.
- **Event Log** — appended transition messages, newest first.

**States handled** — idle/empty (no ticker watched: empty cockpit, no fabricated numbers),
connecting/warm-up, live, stream closed (status dot), and watch error (unknown ticker shows an
explicit message). A footer disclaims: "Descriptive only — not trading advice."

## How Data Flows (single source of truth)

- On **Watch**, the UI calls `POST /watch/{ticker}` (`lib/api.ts`). On success it sets the watched ticker; an unknown ticker surfaces the backend's explicit error.
- `lib/useTapeStream.ts` then does the **initial REST paint** (assembling one snapshot from `/summary` + `/features` + `/events`) and opens `WS /tape/{ticker}/stream` for **live updates**.
- Every panel renders the engine's values **verbatim**. The frontend contains **no** tape logic — it never recomputes spread, the aggressive ratios, price impacts, or confidence. Numbers are only *formatted* (fixed decimals) for display.
- The backend base URL comes from `NEXT_PUBLIC_API_URL` (the QA harness sets it; `NEXT_PUBLIC_API_BASE` is an accepted alias), defaulting to `http://localhost:8000`; the WS URL is derived by swapping `http` → `ws`.

## Files Changed (all new)

- `app/layout.tsx`, `app/page.tsx` (the cockpit, holds watched-ticker + stream state), `app/globals.css`.
- `components/`: `Panel.tsx` (Panel/Metric/EmptyHint primitives), `TopBar.tsx`, `Cockpit.tsx`, `QuotePanel.tsx`, `RecentTradesPanel.tsx`, `FeaturesPanel.tsx`, `TapeStatePanel.tsx`, `ObservationsPanel.tsx`, `EventLogPanel.tsx`, `IdleState.tsx`.
- `lib/`: `types.ts` (snapshot types mirrored from the backend), `config.ts` (API/WS base), `format.ts` (color/label/number helpers), `api.ts` (REST client), `useTapeStream.ts` (WS hook).
- `package.json`, `tsconfig.json`, `next.config.mjs`, `postcss.config.mjs`, `tailwind.config.ts`, `.env.example`.

## Tests Run

- `npm run build` → compiled successfully; types check; static generation OK (Next 15.5.19).
- Live browser verification on `SIM-BUYER`: idle state → Watch → all six panels populate with live values updating over the WebSocket without a page reload; resolves to **Buyer Control @ ~0.88**; trade rows color-coded by side; clean single event-log transition; no console errors. UI values matched the REST endpoints (J-08).

## Visual / Design

Calm dark surface (slate-950), monospaced numerics, restrained effects. Color semantics are
consistent everywhere: green = buy-side / positive impact, red = sell-side / negative impact,
amber = absorption / unclear. Interactive elements (input, Watch button, window tabs) have
hover/focus/active states. No profitability claim and nothing presented as trading advice.

## Known Issues / Limitations

- No **Stop** control yet (deferred to J-09 — there is no `DELETE /watch` this iteration).
- The Features panel shows the nine implemented features; the five deferred blueprint features are not displayed yet.
- Reserved tickers (`SIM-SELLER`, etc.) can be watched but stay `unclear` (no events emitted yet) — by design.
