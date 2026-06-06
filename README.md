# Tapeology

Standalone real-time tape-reading system for US stocks — given one ticker, it watches order flow and classifies the current tape state (buyer control, seller control, bid/ask absorption, or unclear), with a confidence score and plain-language observations.

<!-- AUTO:capabilities -->
## What it does

Tapeology watches a single US equity ticker and answers one question: what is the tape doing right now, and how confident are we? It distinguishes genuine directional control from absorption — high one-sided aggression with no corresponding price progress is absorption, not control. The engine is the single source of truth; REST, WebSocket, and the UI all read the same computed values.

Current capabilities:

- **Watch a ticker in real time** — the cockpit shows live bid/ask/spread/last, a recent-trades list, the core feature readouts (buy/sell aggression ratios, price impact, absorption score, spread, trade speed, and more), the current tape state with a confidence score, plain-language observations, and a running event log — all streaming over WebSocket.
- **Five tape states** — buyer_control, seller_control, bid_absorption, ask_absorption, and unclear — each with a confidence score and human-readable observations.
- **Three data-source modes** — Simulated (no credentials, deterministic), Historical replay (fetch a past window and replay at a chosen speed), and Live (real-time feed during market hours).
- **Five deterministic sim scenarios** — SIM-BUYER, SIM-SELLER, SIM-BIDABS, SIM-ASKABS, and SIM-CHOP each resolve to their expected tape state with no credentials or network access.
- **Symbol search** — find tradable US symbols by partial name or ticker (real-data modes).
- **Historical replay in local time** — enter a date and start/end times in your own local timezone; the app converts them to the correct absolute UTC instant automatically. A timezone label beside the inputs (e.g. `Asia/Hong_Kong`) shows exactly which zone your entry is interpreted in. No manual UTC conversion required.
- **US-session quick-pick buttons** — three one-click presets beside the Historical time inputs fill the window for the market open (Open 9:30 ET), market close (Close 16:00 ET), or the full regular trading day (Full RTH 9:30–16:00 ET). Each button shows both the New York time and its local-time equivalent for the date you picked. DST transitions are handled correctly for both summer and winter dates.
- **Live streaming** — during market hours with vendor credentials, streams real trades and quotes through the same engine as the simulator.
- **Market-status indicator** — shows open/closed with next open or close time.
- **Honest error states** — no credentials shows "provider unavailable"; unknown symbol, empty window, and closed-market each surface a distinct explicit message; no tape state is fabricated.
- **Stale detection** — a live-feed gap flips the status indicator to stale; recovery flips it back to live; no trades are invented during gaps.
- **Resolved aggressor side on real data** — each trade is classified buy or sell using the quote rule (at/above ask = buy, at/below bid = sell), falling back to a tick test (uptick = buy, downtick = sell, zero-tick carries the last direction) when the print is mid-spread or pre-quote; only a genuinely undecidable print (no quote and no prior trade) remains unknown. On real historical data the unknown fraction is near zero.
- **Candlestick price chart with tape-state markers** — in Simulated and Historical modes, a dark candlestick chart appears above the cockpit showing the watched price over time; colored arrow markers are placed at each tape-state transition: green for buyer control, red for seller control, amber for bid or ask absorption; unclear is deliberately unmarked. A bar-size selector (10 s, 30 s, 60 s) lets you redraw the chart at a different candle granularity; the chart supports pan and zoom. An honest empty state is shown before any price data arrives. The chart is hidden in Live mode.
- **Pause and Resume** — an amber Pause button beside Stop lets you freeze the cockpit, trades list, feature counters, tape-state readout, and price chart at a specific moment without closing the session; an amber "paused" status indicator replaces the green "live" dot while frozen. Click Resume to continue from exactly where you stopped — no invented catch-up data is shown. Works in Simulated, Historical, and Live modes.
- **Immediate Watch acknowledgement** — clicking Watch synchronously transitions the cockpit to a "Connecting to SYMBOL…" state (amber pulsing dot) before any network call completes; there is no silent dead-click or frozen idle screen in any mode.
- **Inline input validation** — the Watch button is disabled when the symbol field is empty or the Historical time window is missing or invalid; an inline message ("Enter a ticker symbol" / "Choose a valid time window") appears immediately and clears as soon as the field is corrected, with no network call needed to see the feedback.
- **Bounded provider timeouts** — the backend caps each vendor call at a configurable timeout; if the data provider is slow or unreachable the TopBar error banner shows a clear "Market data provider timed out…" message within a bounded time rather than hanging indefinitely.
- **Stream-failure panel** — if the initial tape stream connection fails after Watch, a dedicated "Couldn't connect to the tape stream" panel appears in the cockpit area (with a "Try Watch again" prompt) instead of leaving the screen in a silent connecting state.
- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`.
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
