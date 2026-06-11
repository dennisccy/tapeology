# Tapeology

Standalone real-time tape-reading system for US stocks — given one ticker, it watches order flow and classifies the current tape state (buyer control, seller control, bid/ask absorption, or unclear), with a confidence score and plain-language observations.

<!-- AUTO:capabilities -->
## What it does

Tapeology watches a single US equity ticker and answers one question: what is the tape doing right now, and how confident are we? It distinguishes genuine directional control from absorption — high one-sided aggression with no corresponding price progress is absorption, not control. The engine is the single source of truth; REST, WebSocket, and the UI all read the same computed values. The app has two pages — a live Cockpit and a Journal — linked by a persistent top navigation bar.

Current capabilities:

- **Watch a ticker in real time** — the cockpit shows live bid/ask/spread/last, a recent-trades list, the core feature readouts (buy/sell aggression ratios, price impact, absorption score, spread, trade speed, and more), the current tape state with a confidence score, plain-language observations, and a running event log — all streaming over WebSocket.
- **Five tape states** — buyer_control, seller_control, bid_absorption, ask_absorption, and unclear — each with a confidence score and human-readable observations.
- **Three data-source modes** — Simulated (no credentials, deterministic), Historical replay (fetch a past window and replay at a chosen speed), and Live (real-time feed during market hours).
- **Seven deterministic sim scenarios** — SIM-BUYER, SIM-SELLER, SIM-BIDABS, SIM-ASKABS, and SIM-CHOP each resolve to their expected tape state with no credentials or network access. Two additional scenarios show realistic tape transitions: SIM-SHIFT starts under buyer control and honestly decays to unclear as price drifts back; SIM-REVERSAL shows heavy selling correctly read as absorption (price held, not falling), then buyers step in and lift price above the absorbed level.
- **Declare a thesis on the watched ticker** — a thesis strip between the price chart and the feature panels lets you declare a trade idea: choose a setup type (absorption reversal, trend continuation, level break-and-go, or failed-move fade), a direction (long or short), and a required invalidation price. For setups that need it (level break-and-go, failed-move fade) a level price field also appears. The setup catalog, labels, and statement wording all come from the backend — nothing is hardcoded on screen.
- **Live expected-behaviour statements** — each declared thesis carries a frozen list of plain-language statements describing what the tape should do if the idea is valid. Each statement shows a live status (met / not yet / violated) that updates in real time as the tape changes, with a coloured dot: emerald for met, slate for not yet, rose for violated. Statement statuses are judged by true directional dominance — a statement only reads "met" when favorable price impact genuinely outweighs adverse activity, and "violated" when adverse activity dominates.
- **Honest thesis validation** — a declaration is refused with a plain on-screen message if the invalidation price is on the wrong side of the current price, a required level is missing or a level is supplied for a setup that does not use one, there is already an active thesis, or the ticker is not being watched. Nothing is recorded when a declaration is refused.
- **Thesis persistence** — every declared thesis and its verdict timeline are written to a dedicated journal database (separate from live tape data). The timeline is append-only; entries are never edited or deleted. Stopping the watch, a stream ending, or a feed failure marks an active thesis "expired"; a startup sweep resolves any thesis left open across a restart with a distinct restart-reason, honest about exactly what happened.
- **Journal page** — a dedicated Journal page (reachable from the top navigation bar) shows every thesis you have ever declared — active, resolved, expired, and abandoned — in a filterable table. Each row is a link to the thesis detail page. You can filter by status; the table is honest about system-owned outcomes versus user-driven resolutions.
- **Journal detail page** — clicking any row in the Journal table opens a full detail page for that thesis. The page shows the frozen expected-behaviour statements — each with a final-status badge (MET / VIOLATED / NOT MET) recording whether that statement held at the moment the thesis closed, persisted once at resolution and never recomputed — the complete verdict timeline at true clock time (with per-transition plain-language evidence), your entry and exit marks, the entry risk flags recorded at declaration, and four machine-derived execution checks: whether you entered before the tape confirmed your thesis, whether you chased entry beyond the price where the tape condition first held, whether you exited beyond your own invalidation level, and whether you cut a confirming thesis early. Two outcome × process grade labels appear side by side — one for whether your thesis held or failed, one for whether your execution was disciplined or flagged. Being invalidated by price is never itself counted against your process grade; only failing your own execution checks counts.
- **Excursion outcomes (how far the tape went)** — for any resolved or ended thesis, the journal detail page shows two clearly separated sections of excursion data: one anchored at the moment the tape first confirmed your idea, one anchored at the moment you entered. Each section lists every time horizon with the maximum favorable move (MFE), the maximum adverse move (MAE), the ternary outcome (did price reach +1R first, −1R first, or neither within the horizon?), and the spread cost recorded at that anchor — all expressed in R units, never as a currency figure. Where the stream ended before a horizon could complete, the outcome is shown as "TRUNCATED" rather than hidden or fabricated. Theses that predate this feature show an honest "not measured" note.
- **Save review flow** — once a thesis is resolved, a Save Review panel on the detail page lets you confirm which mistakes you made by selecting from the backend's taxonomy of mistake tags, add a note when "Other" is selected, and save. On save the thesis is marked as reviewed, the confirmed tags and note are stored verbatim, and the journal list shows a Reviewed flag alongside the grade. A thesis can only be reviewed after it is resolved and cannot be reviewed twice. The Journal list shows additive Grade and Reviewed columns with an honest em-dash for rows predating the grade feature.
- **Journal analytics view** — the Journal page has a Theses / Analytics toggle. The Analytics view shows aggregated statistics across all past theses, broken down by setup type and direction. Results from different data sources and config fingerprints are never pooled together — each partition is shown separately. Abandoned theses are always counted in the denominator. Groups with too few entries say so clearly. No currency figures or win-rates are ever shown. An active thesis shows "not yet available"; a resolved thesis recorded before this feature shows "predates the feature" — the distinction is never conflated.
- **Source and feed provenance stamp** — the thesis strip shows which data source and feed (SIM / SIP / IEX) the thesis was declared on, so the context is always visible.
- **Mark entry and exit prices** — while a thesis is active, you can mark your actual entry price (prefilled from the current last-trade price, editable) and your actual exit price directly from the strip. Both are saved verbatim — no fills, no simulated execution. Once an entry is marked, the Abandon button is withdrawn; only "Played out" and "Mark exit" remain, so an open position cannot be silently discarded.
- **Realized-move readout** — after both entry and exit are marked, the strip shows the recorded prices with spread-at-mark and the realized move expressed in R units labeled as a journaled measurement, never as a currency profit or loss figure.
- **Symbol search** — find tradable US symbols by partial name or ticker (real-data modes); results appear quickly even on the very first search after a restart; rapid typing cancels older in-flight requests so results never pile up or arrive out of order.
- **Historical replay in local time** — enter a date in `dd-MM-yyyy` format and start/end times in your own local timezone; the app converts them to the correct absolute UTC instant automatically. A timezone label beside the inputs (e.g. `Asia/Hong_Kong`) shows exactly which zone your entry is interpreted in. No manual UTC conversion required.
- **US-session quick-pick buttons** — three one-click presets beside the Historical time inputs fill the window for the market open (Open 9:30 ET), market close (Close 16:00 ET), or the full regular trading day (Full RTH 9:30–16:00 ET). Each button shows both the New York time and its local-time equivalent for the date you picked. DST transitions are handled correctly for both summer and winter dates.
- **Long historical windows load** — choosing the "Full RTH 9:30–16:00" quick-pick or any multi-hour window for a busy stock loads the real tape data by fetching the window in parallel bounded pieces and stitching them in time order. The "try a shorter range" message appears only when a window is genuinely too large to load in time. Re-watching the same symbol and window is near-instant from a local session cache.
- **Live replay speed change** — while a historical replay is running, selecting a new speed (1x, 2x, 5x, or 10x) from the speed dropdown immediately re-paces the replay — no teardown, no spinner, no position loss. Before a watch starts, the dropdown stages the speed for the next Watch as before.
- **Honest "control" reads on real instruments** — the tape-state classifier judges whether a spread is wide relative to the stock's price level (in basis points) and whether price actually moved as a return, so a clear directional move on a real sub-$100 stock correctly resolves to buyer control or seller control. Genuinely uncertain tapes (spread wide for that price, or heavy one-sided pressure with no real price progress) still read "unclear" or "absorption" — no confident call is manufactured.
- **Live streaming** — during market hours with vendor credentials, streams real trades and quotes through the same engine as the simulator.
- **Market-status indicator** — shows open/closed with next open or close time displayed in `dd-MM-yyyy HH:mm` format with an explicit UTC-offset zone label.
- **Honest error states** — no credentials shows "provider unavailable"; unknown symbol, empty window, and closed-market each surface a distinct explicit message; no tape state is fabricated.
- **Waiting-for-first-trade screen** — when Watch connects successfully but no trade has arrived yet (quiet symbol, off-hours session, or the brief moment right after clicking Watch), the cockpit shows an explicit "Connected to SYMBOL — waiting for the first trade…" screen with an amber pulsing dot; the full panel grid is only rendered once real trade/quote data arrives, so the screen is never misleadingly blank.
- **Honest connection-state status light** — the status indicator has states for connecting, live, waiting (connected but no data yet), stale, paused, failed, and closed. The dot never shows a confident green "live" over an empty or broken tape.
- **Background feed failure surfacing** — if the data feed breaks after a successful Watch (mid-session connection drop), the cockpit immediately shows an explicit red error panel ("The tape feed failed after connecting. No tape is shown.") and the TopBar error banner updates, instead of silently freezing.
- **Stale detection** — a live-feed gap flips the status indicator to stale; recovery flips it back to live; no trades are invented during gaps. A quiet watch that connects but receives no trades also automatically advances from "waiting" to "stale" after a configurable interval, giving an honest terminal state rather than an endless spinner.
- **Resolved aggressor side on real data** — each trade is classified buy or sell using the quote rule (at/above ask = buy, at/below bid = sell), falling back to a tick test when the print is mid-spread or pre-quote; only a genuinely undecidable print remains unknown. On real historical data the unknown fraction is near zero.
- **Candlestick price chart with real clock times** — a dark candlestick chart appears above the cockpit showing the watched price over time; the time axis, crosshair tooltip, and tape-state markers all display genuine market clock times in `dd-MM-yyyy HH:mm:ss` format (local zone) — not elapsed playback seconds. For simulated data the axis shows a synthetic session clock starting at market open (09:30); for historical data it shows the real market times when those trades actually occurred. Colored arrow markers indicate tape-state transitions: green for buyer control, red for seller control, amber for absorption. A bar-size selector (10 s, 30 s, 60 s) lets you redraw the chart at a different candle granularity; the chart supports pan and zoom.
- **Thesis geometry on the price chart** — when a thesis is active, the chart draws labeled horizontal price-lines at the declared invalidation price (always) and level price (when the setup requires one). As the tape evolves, verdict markers appear below the candles at the exact moments each verdict was published. When you mark your entry, an entry marker appears at that time and price; a first-confirmation marker marks the first moment the tape agreed with the thesis. All geometry is computed once on the server from canonical values — the chart draws it verbatim and adds no interpretation of its own.
- **Consistent dd-MM-yyyy date format** — every date shown in the product (market-status times, the watched-source descriptor, the chart axis, the journal table) uses the same `dd-MM-yyyy` format from a single shared formatter. No locale-dependent browser formatting.
- **Inline date validation** — the historical date field is a plain typed `dd-MM-yyyy` entry box; impossible or malformed dates (e.g. `31-02-2026`) immediately outline the field in amber and show an error message; the Watch button stays disabled until the date is corrected.
- **Pause and Resume** — an amber Pause button beside Stop lets you freeze the cockpit, trades list, feature counters, tape-state readout, and price chart at a specific moment without closing the session; an amber "paused" status indicator replaces the green "live" dot while frozen. Click Resume to continue from exactly where you stopped — no invented catch-up data is shown. Works in Simulated, Historical, and Live modes.
- **Immediate Watch acknowledgement** — clicking Watch synchronously transitions the cockpit to a "Connecting to SYMBOL…" state (amber pulsing dot) before any network call completes; there is no silent dead-click or frozen idle screen in any mode.
- **Inline input validation** — the Watch button is disabled when the symbol field is empty or the Historical time window is missing or invalid; an inline message ("Enter a ticker symbol" / "Choose a valid time window") appears immediately and clears as soon as the field is corrected, with no network call needed to see the feedback.
- **Bounded provider timeouts** — every vendor call is enforced by a real network-level deadline so the app's honest error always appears before the browser gives up; if the provider is slow or unreachable the TopBar error banner shows a clear "Market data provider timed out…" message within a bounded time rather than hanging indefinitely.
- **Stream-failure panel** — if the initial tape stream connection fails after Watch, a dedicated "Couldn't connect to the tape stream" panel appears in the cockpit area (with a "Try Watch again" prompt) instead of leaving the screen in a silent connecting state.
- **Live thesis verdict** — once you declare a thesis, the cockpit continuously judges the live tape against it and shows a real-time colored verdict chip: confirming (emerald), weakening (amber), rejecting (rose), or pending (slate). A plain-language evidence sentence beneath the chip explains what the tape is doing right now relative to your idea — updating live as the tape evolves, never fixed at "pending".
- **Setup-aware judgement** — each setup type is judged on its own terms: an absorption-reversal only confirms when price actually lifts off the absorbed level; a level break-and-go stays pending until price crosses the declared level; a trend-continuation rejects when the opposing side takes over; a failed-move fade confirms while the push is being absorbed. A verdict only changes after the tape condition holds steadily for a short configurable period, so a single flickering moment never moves the verdict.
- **Hard invalidation with terminal display** — if price prints decisively through the declared invalidation level (a clear single break, or several consecutive prints leaking through), the thesis is resolved as "invalidated": the strip shows a rose ringed chip prefixed with "✕", a "Thesis invalidated — resolved" notice, and the offending evidence sentence. An invalidated thesis stays visible with the terminal treatment until a new watch session; only an expired thesis (watch stopped / stream ended) clears the strip back to idle.
- **User-driven thesis resolution** — while a thesis is active (and no entry mark has been recorded), two resolve controls appear on the strip: "Played out" (the idea ran its course) and "Abandon" (walking away). Either saves the resolution with a precise timestamp, shows a plain-language confirmation, and returns the strip to the declare state so the next idea can be declared immediately. System-owned outcomes (invalidated, expired) cannot be overwritten by user action.
- **Thesis survives watch interruption when entry is marked** — stopping the watch or losing the stream after an entry mark is recorded does not expire the thesis. The strip remains visible and labeled "NOT EVALUATED" with a message to re-watch the same source to resume. When you re-watch the same ticker and source, the thesis re-attaches automatically and resumes live evaluation; a single gap event is appended to the timeline to record the interrupted period. If no entry was marked when the watch stopped, the thesis closes with an honest `watch_stopped` reason — clearly distinct from a natural stream exhaustion.
- **Append-only verdict timeline** — every verdict transition is recorded in order to a permanent journal, including when the underlying tape condition first became true versus when the verdict was published. The full timeline is readable via the API and on the journal detail page.
- **Entry risk flags at declaration** — when you declare a thesis, six advisory conditions are evaluated instantly from the live tape snapshot and any that fire are shown as amber indicator chips: chasing an already-extended move, invalidation too tight relative to the spread, tape not yet warmed up, spread too wide for the price level, trade speed too low, or direction against the tape's expected state. Each chip shows the exact measured margin (e.g. "buy impact +0.42% already exceeds the +0.40% chase threshold"). A clean declaration shows no chips and no false reassurance. These flags are frozen at the moment you declare and never change as the tape evolves, so the record is always honest about the conditions at entry.
- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`.
<!-- /AUTO:capabilities -->

This project embeds the [`incredible_auto_dev`](https://github.com/dennisccy/incredible_auto_dev)
AI multi-agent dev-chain as a **git subtree** at `incredible_auto_dev/`, following the same
monorepo wiring as `trendora`.

## Project layout

```
incredible_auto_dev/                                  AI multi-agent dev-chain (git subtree; remote auto_dev, --squash)
.claude CLAUDE.md config scripts templates tests      symlinks → incredible_auto_dev/
```

The root-level `.claude`, `CLAUDE.md`, `config`, `scripts`, `templates`, and `tests` are
symlinks into `incredible_auto_dev/`, so the dev-chain configuration is active from the repo
root (single source of truth, no duplication).

## Syncing the dev-chain

The subtree tracks `auto_dev/main` (`git@github.com:dennisccy/incredible_auto_dev.git`).

```bash
# one-time, after a fresh clone (the remote is not stored in the repo)
git remote add auto_dev git@github.com:dennisccy/incredible_auto_dev.git

# pull the latest dev-chain from upstream
git subtree pull --prefix incredible_auto_dev auto_dev main --squash

# push local incredible_auto_dev/ changes back upstream
git subtree push --prefix incredible_auto_dev auto_dev main
```

<!-- AUTO:how-to-run -->
## How to run

### Prerequisites

- Python 3.12+
- Node.js (for Next.js frontend)
- `uv` package manager (pip-compatible); creates venv at `apps/backend/.venv/`
- (Optional) Alpaca API credentials in environment for real-data modes (`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`); without them the app runs simulator-only.

### Install

```bash
# Backend
cd apps/backend
uv pip install -e .        # or: pip install -e . inside the venv

# Frontend
cd apps/frontend
npm install
```

### Start backend

```bash
bash scripts/start-backend.sh
```

Backend runs at **http://localhost:8000**. Health check: `GET http://localhost:8000/health`

### Start frontend

```bash
bash scripts/start-frontend.sh
```

Frontend runs at **http://localhost:3000**

The frontend reads the backend URL from `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`). The WebSocket URL is derived automatically by swapping `http` to `ws`.

### Run tests

```bash
# Backend tests
cd apps/backend && .venv/bin/python -m pytest tests/ -v

# Frontend type-check + compile
cd apps/frontend && npm run build
```

### Local URLs

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:3000      |
| Backend  | http://localhost:8000      |
| Health   | http://localhost:8000/health |
<!-- /AUTO:how-to-run -->
