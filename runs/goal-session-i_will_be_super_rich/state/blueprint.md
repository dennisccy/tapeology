# Tapeology — Coherence Blueprint

> Goal session: `i_will_be_super_rich` · Status: **APPROVED** (J-01–J-15 built & in force) · **extended** at iter-5
> with the now-in-scope **analysis-fidelity** half (J-16–J-20): tick-test side resolution, the one focused
> price-candlestick + tape-state-marker chart, pause/resume, and local-time historical-window selection.
> Source: `docs/goal.md` (Product Shape, Must-have journeys J-01–J-20, Key Capabilities, Canonical values).
> Carries forward the **APPROVED** simulated blueprint from session `i_will_be_rich` (J-01–J-09) and the real-data
> half (J-10–J-15): live streaming + historical replay behind a vendor-agnostic adapter (Alpaca first, free IEX feed).
>
> **iter-5 extension is ADDITIVE** — same single `/` HOME, same nav skeleton, same one-engine source of truth. New
> rows 10–12 register the new displayed values; row 4 is clarified (not changed) to name the tick-test fallback inside
> its existing owner. No top-level nav section added/renamed/moved ⇒ **no re-approval requested**.

**Governing principle.** Tapeology is a single-ticker **tape cockpit**. Every tape state, confidence, and feature is
computed **exactly once in the engine** and read identically by REST, WebSocket, and the UI (anti-goal: *Single source
of truth*). The engine and API depend **only** on the **provider interface** (`TradeEvent` / `QuoteEvent`); the
simulator, the live provider, and the historical-replay provider are three swappable implementations of that one
interface — adding or swapping a data source touches **neither the engine nor the API**. A concrete vendor SDK lives in
**exactly one adapter module** behind a vendor-neutral seam (a second vendor = one new adapter). Classification is
**price impact, not raw aggression**. Real-data failures surface an **explicit, distinct state — never a fabricated
cockpit**. The one allowed chart is the focused price candlestick + tape-state-marker overlay — **no** indicators,
studies, or drawing tools, and **no** order/execution affordance (anti-goal: *Stay in scope*).

---

## Information Architecture

**App shell (persistent).** Top bar: app name **Tapeology** · **data-source selector (Live / Historical / Simulated)** ·
**mode-specific controls** (revealed by the selector, without changing the cockpit):
- *Simulated* → **ticker input** (e.g. `SIM-BUYER`).
- *Live* → **symbol search** + **market-status indicator** (open/closed, from `GET /market/clock`).
- *Historical* → **symbol search** + **date + time-window picker (local time, zone label, US-session quick-picks)** + **replay-speed** control.

…then **Watch** (`POST /watch/{ticker}` with an optional `{mode,start,end,speed}` body; empty body = sim) ·
**watched-source label** (the sim scenario, `live AAPL`, or `historical AAPL <window>`) · **stream-status** dot (the
engine's canonical `snapshot.stream_status` — connecting / live / stale / **paused** / closed) ·
**Pause / Resume** (`POST /watch/{ticker}/pause` · `POST /watch/{ticker}/resume`; freeze/continue without teardown) ·
**Stop** (`DELETE /watch/{ticker}`).
Calm dark surface, monospaced numerics; green = buy-side / positive impact, red = sell-side / negative impact,
amber = absorption / unclear / stale.

**Routes — still exactly one screen across all modes.**

- **`/` — Watch (the tape cockpit) — HOME.** Every Must-have journey lives here, ≤1 click after Watch. The cockpit body
  is **identical** for simulated, live, and replayed real data. Panels (unchanged from the simulated build):
  - **Quote panel** — bid / ask / spread / last (spread = ask − bid).
  - **Recent-trades panel** — price / size / **side** (buy/sell/unknown, color-coded). *Side resolved by the quote rule then a tick-test fallback (J-16); only genuinely undecidable prints stay `unknown`.*
  - **Features panel** — the 14 core features, per window (**10s / 30s / 60s / 180s / 300s**).
  - **Tape-state panel** — state (`buyer_control`|`seller_control`|`bid_absorption`|`ask_absorption`|`unclear`) + **confidence**.
  - **Observations panel** + **Event-log panel** — live over WS.
  - **Price chart (Simulated + Historical only)** — *above the cockpit:* a **candlestick** chart of the watched price with a **bar-size selector (10 / 30 / 60 s)** and **tape-state-transition markers** (green buyer_control, red seller_control, amber bid/ask_absorption; unclear unmarked), pan/zoom. Reads `GET /tape/{ticker}/history?bar=…` — never recomputes price/side/state. Empty window ⇒ empty chart. Hidden for Live.
  - **Idle/empty state** — before Watch and after Stop: empty cockpit, no stale numbers.
  - **PAUSED indicator** — when paused, the cockpit + chart **freeze** (no teardown, no fabricated catch-up); reads the engine's canonical paused state.
  - **Honest non-cockpit states** (real modes) — rendered *in place of* the cockpit, never alongside fabricated panels:
    *provider unavailable* (no credentials), *not a tradable symbol*, *no data for that window*, *market is closed
    (with next open)*.

**Canonical home per journey** (all on `/`, ≤1 click):
J-01 → whole cockpit · J-02 / J-03 / J-06 → tape-state panel · J-04 / J-05 → tape-state + absorption/refresh readouts ·
J-07 → event-log + observations · J-08 → `/` panels vs the REST endpoints (same values) · J-09 → Stop + idle state ·
**J-10 → data-source selector + its mode-specific control reveal** · **J-11 → Historical controls → cockpit** ·
**J-12 → Live controls + status → cockpit** · **J-13 → symbol search box** · **J-14 → the honest non-cockpit states** ·
**J-15 → stream-status dot (live ⇄ stale)** ·
**J-16 → recent-trades panel (resolved side)** · **J-17 / J-18 → price-chart pane above the cockpit (sim / historical)** ·
**J-19 → Pause/Resume controls + PAUSED indicator** · **J-20 → Historical date/time picker (local-zone label + quick-picks)**.

No second page, no watchlist grid, no dashboard, no execution/order controls, no general charting (anti-goals:
single-ticker UI; no execution path; one focused chart only).

---

## Data Contract

Every displayed value is computed once and read-only re-exposed elsewhere; `…/summary` and `WS …/stream` **re-expose**
the snapshot and MUST NOT recompute. `…/state` and `…/features` are the canonical REST reads. Rows 1–6 are the
**already-built** simulated contract (in force, unchanged); rows 7–9 are the **already-built** real-data additions;
rows 10–12 are the **analysis-fidelity additions**: rows 10 (J-17 chart **render-verified**; J-18 real-historical render closed at iter-8) and 11 (J-19 pause/resume) are **built & in force**; row 12 (J-20 local-time historical window) is **built at iter-8** (J-16 is folded into row 4).

| # | Displayed value | Canonical computing module (computed once) | Canonical serving endpoint | Re-exposed read-only by |
|---|---|---|---|---|
| 1 | **Tape state + confidence** | `TapeStateClassifier` (rule/threshold over features) → snapshot | `GET /tape/{ticker}/state` | `/summary`, `WS /stream` |
| 2 | **14 core features × 5 windows** | `FeatureEngine` (windows 10/30/60/180/300s) → snapshot | `GET /tape/{ticker}/features` | `/summary` (subset), `WS /stream` |
| 3 | **bid / ask / spread / last** (spread = ask − bid) | `MarketState` (latest Quote/Trade) → snapshot | `GET /tape/{ticker}/summary` | `WS /stream` |
| 4 | **Recent trades** (price / size / **side**) | **Aggressor classifier** — quote rule (≥ask⇒buy, ≤bid⇒sell) **then a tick-test fallback** (no quote yet **or** strictly mid-spread ⇒ uptick=buy / downtick=sell / zero-tick carries last non-zero dir; no quote **and** no prior trade ⇒ `unknown`) over provider TradeEvents | `GET /tape/{ticker}/events` | `WS /stream` |
| 5 | **Observations + event-log messages** | Engine **observation / transition emitter** | `GET /tape/{ticker}/events` | `WS /stream` |
| 6 | **Watched-source descriptor + watch/stream status** (sim scenario \| `live <SYM>` \| `historical <SYM> <window>`; status connecting/live/**stale**/**paused**/closed) | `WatchManager` (records mode + params at watch) / engine feeder (owns `stream_status`) | `GET /tape/{ticker}/summary` (+ `POST`/`DELETE /watch` responses) | `WS /stream` |
| 7 | **Symbol search results** (symbol + name) | **Vendor-agnostic adapter** (Alpaca first) behind the provider seam | `GET /symbols/search?q=` | — |
| 8 | **Market clock** (open/closed + next open/close) | **Vendor-agnostic adapter** / market-clock module | `GET /market/clock` | Live market-status indicator reads this |
| 9 | **Real-data availability / failure state** (`provider unavailable` \| `not a tradable symbol` \| `no data for that window` \| `market is closed`) | Live / Historical provider + adapter (credential check + vendor responses) | Explicit error from `POST /watch/{ticker}` (mid-stream feed-gap ⇒ `stream_status="stale"` on the row-6 snapshot) | UI renders the matching non-cockpit state |
| 10 | **Price history: OHLC bars (per 10/30/60 s) + tape-state-transition markers** (state + confidence + ts) | **Engine history buffer** (accumulates watched price → config-binned OHLC + meaningful-transition markers; computed once with the snapshot) | `GET /tape/{ticker}/history?bar=<10\|30\|60>` (pure projection; sim + historical only) | Chart reads this — never recomputes price/side/state |
| 11 | **Paused state** (boolean) | **Engine/feeder** (owns paused; pause freezes the feeder without teardown — no fabricated backfill) → snapshot | `GET /tape/{ticker}/summary` (set via `POST /watch/{ticker}/pause` · `POST /watch/{ticker}/resume`) | `WS /stream`; UI renders PAUSED + toggles the control |
| 12 | **Resolved historical window** (tz-aware start/end instants for the user's selected **local** window; explicit **local zone label** + **US-session quick-picks** Open 9:30 ET / Close 16:00 ET / Full RTH, each annotated with its local equivalent) | **Frontend datetime module** (`apps/frontend/lib/datetime.ts` — the resolution fn resolves the local selection AND the ET session anchors via the IANA `America/New_York` zone, DST-correct, → exact tz-aware UTC instants **once, before** the fetch; the 9:30/16:00 ET anchors are named preset constants, not engine thresholds) → request body | `POST /watch/{ticker}` body `{mode:"historical",start,end,speed}` (timezone-aware instants; backend `_parse_window_dt` honors the offset verbatim) | Historical provider fetches exactly the resolved window (no second tz conversion, no silent UTC shift) — **built at iter-8** |

**Provider & vendor seam (singularity — architectural, not a displayed value).**
- One **provider interface** (`TradeEvent`/`QuoteEvent`/[later]`BookLevelEvent`); `SimulatedProvider`, the **live
  provider**, and the **historical-replay provider** all implement it. The engine/API import **none** of them directly
  and **never** import the vendor SDK.
- The concrete vendor (**Alpaca**, free IEX feed) appears in **exactly one adapter module** behind a vendor-neutral
  interface; a second vendor (Polygon, Databento…) is **one new adapter**, no engine/API/provider change.
- Real vendor timestamps are mapped to the engine's **logical timeline** (quote-before-trade preserved) so the engine
  stays unchanged and deterministic per stream.
- The seam has a **synchronous** variant (`stream() -> Iterable`, used by the bounded simulated + historical-replay
  providers) and an **async** variant (`async stream() -> AsyncIterator`, used by the unbounded **live** provider) — the
  **same** interface in two shapes; both feed the **same** engine via `process_event` (no engine change). The **live
  feeder** is the single owner that flips row-6 `stream_status` to **`stale`** when no event arrives within
  `stale_gap_seconds` (and back to **`live`** on resume), fabricating no trades — there is no second `stream_status`
  writer and no parallel live state/feature path. **Pause** (row 11) is also a feeder-level freeze owned by the
  feeder/engine — distinct from `stop()` (which cancels + tears down); pause does NOT cancel the task and synthesizes no
  catch-up data on resume.

**Config (no magic numbers).** All window lengths, thresholds, large-print size, impact/absorption cutoffs, confidence
boundaries, the stale-gap timeout, **the OHLC bar sizes / marker-significance thresholds, and any tick-test tie/tolerance**
live in one config module — never inline literals in engine/classifier code. (The tick test itself is a pure rule with
no numeric cutoff; if any tolerance is introduced it MUST live in config.)

**Credentials.** Real-vendor keys come **only** from environment/config (never committed). With no keys, the app runs
simulator-only and the real modes report **row-9** `provider unavailable` — they never fall back to fabricated data.

**Singularity rules (coherence guardrails).**
- Each value in rows 1–6 has exactly **one producer** (the engine); REST, WS, and UI **read** — no recomputation in API
  or frontend. The same ticker shows **identical** values across `/state`, `/features`, `/summary`, `WS /stream`, and UI
  (J-08). Live/historical reads flow through the **same** rows 1–6 — real data does **not** add a parallel state/feature path.
- The new real-data values (rows 7–9) each have **one** computing owner + **one** endpoint; do not add a second lookup
  or a second clock.
- The analysis-fidelity values (rows 10–12) each have **one** computing owner + **one** endpoint/body: the chart reads
  row-10 OHLC/markers from the engine history buffer (it MUST NOT bin candles, infer side, or place markers itself); the
  PAUSED indicator reads row-11 from the snapshot (no UI-side guess); the historical window is resolved once by row-12
  before the fetch (no second tz conversion, no silent UTC reinterpretation).
- On a feed gap / provider failure the snapshot surfaces explicit **stale / no-data / unavailable** — nothing is
  fabricated to force a green journey (anti-goal: *No fabricated data*). An empty historical window ⇒ **empty** chart.

**Note on module names.** `TapeStateClassifier`, `FeatureEngine`, `MarketState`, the aggressor classifier,
`WatchManager`, the config module, the **vendor-agnostic adapter** + the live/historical providers, and (new) the
**engine history buffer** + the **frontend datetime module** are the **logical canonical owners**. The developer
chooses concrete file paths in the owning iteration, but each value keeps exactly one computing owner and one canonical
endpoint — that singularity is what the coherence-auditor enforces.
