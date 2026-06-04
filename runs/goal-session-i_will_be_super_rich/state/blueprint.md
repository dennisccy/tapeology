# Tapeology — Coherence Blueprint

> Goal session: `i_will_be_super_rich` · Status: **DRAFT — awaiting human approval after baseline iter 0.**
> Source: `docs/goal.md` (Product Shape, Must-have journeys J-01–J-15, Key Capabilities, Canonical values).
> Carries forward the **APPROVED** simulated blueprint from session `i_will_be_rich` (J-01–J-09, already built and
> in force) and **extends** it with the now-in-scope **real US-equity data** half (J-10–J-15): live streaming +
> historical replay behind a vendor-agnostic adapter (Alpaca first, free IEX feed).

**Governing principle.** Tapeology is a single-ticker **tape cockpit**. Every tape state, confidence, and feature is
computed **exactly once in the engine** and read identically by REST, WebSocket, and the UI (anti-goal: *Single source
of truth*). The engine and API depend **only** on the **provider interface** (`TradeEvent` / `QuoteEvent`); the
simulator, the live provider, and the historical-replay provider are three swappable implementations of that one
interface — adding or swapping a data source touches **neither the engine nor the API**. A concrete vendor SDK lives in
**exactly one adapter module** behind a vendor-neutral seam (a second vendor = one new adapter). Classification is
**price impact, not raw aggression**. Real-data failures surface an **explicit, distinct state — never a fabricated
cockpit**.

---

## Information Architecture

**App shell (persistent).** Top bar: app name **Tapeology** · **data-source selector (Live / Historical / Simulated)** ·
**mode-specific controls** (revealed by the selector, without changing the cockpit):
- *Simulated* → **ticker input** (e.g. `SIM-BUYER`).
- *Live* → **symbol search** + **market-status indicator** (open/closed, from `GET /market/clock`).
- *Historical* → **symbol search** + **date + time-window picker** + **replay-speed** control.

…then **Watch** (`POST /watch/{ticker}` with an optional `{mode,start,end,speed}` body; empty body = sim) ·
**watched-source label** (the sim scenario, `live AAPL`, or `historical AAPL <window>`) · **stream-status** dot (the
engine's canonical `snapshot.stream_status` — connecting / live / stale / closed) · **Stop** (`DELETE /watch/{ticker}`).
Calm dark surface, monospaced numerics; green = buy-side / positive impact, red = sell-side / negative impact,
amber = absorption / unclear / stale.

**Routes — still exactly one screen across all modes.**

- **`/` — Watch (the tape cockpit) — HOME.** Every Must-have journey lives here, ≤1 click after Watch. The cockpit body
  is **identical** for simulated, live, and replayed real data. Panels (unchanged from the simulated build):
  - **Quote panel** — bid / ask / spread / last (spread = ask − bid).
  - **Recent-trades panel** — price / size / **side** (buy/sell/unknown, color-coded).
  - **Features panel** — the 14 core features, per window (**10s / 30s / 60s / 180s / 300s**).
  - **Tape-state panel** — state (`buyer_control`|`seller_control`|`bid_absorption`|`ask_absorption`|`unclear`) + **confidence**.
  - **Observations panel** + **Event-log panel** — live over WS.
  - **Idle/empty state** — before Watch and after Stop: empty cockpit, no stale numbers.
  - **Honest non-cockpit states** (real modes) — rendered *in place of* the cockpit, never alongside fabricated panels:
    *provider unavailable* (no credentials), *not a tradable symbol*, *no data for that window*, *market is closed
    (with next open)*.

**Canonical home per journey** (all on `/`, ≤1 click):
J-01 → whole cockpit · J-02 / J-03 / J-06 → tape-state panel · J-04 / J-05 → tape-state + absorption/refresh readouts ·
J-07 → event-log + observations · J-08 → `/` panels vs the REST endpoints (same values) · J-09 → Stop + idle state ·
**J-10 → data-source selector + its mode-specific control reveal** · **J-11 → Historical controls → cockpit** ·
**J-12 → Live controls + status → cockpit** · **J-13 → symbol search box** · **J-14 → the honest non-cockpit states** ·
**J-15 → stream-status dot (live ⇄ stale)**.

No second page, no watchlist grid, no dashboard, no execution/order controls (anti-goals: single-ticker UI; no execution path).

---

## Data Contract

Every displayed value is computed once and read-only re-exposed elsewhere; `…/summary` and `WS …/stream` **re-expose**
the snapshot and MUST NOT recompute. `…/state` and `…/features` are the canonical REST reads. Rows 1–6 are the
**already-built** simulated contract (in force, unchanged); rows 7–9 are the **real-data additions** (to be built).

| # | Displayed value | Canonical computing module (computed once) | Canonical serving endpoint | Re-exposed read-only by |
|---|---|---|---|---|
| 1 | **Tape state + confidence** | `TapeStateClassifier` (rule/threshold over features) → snapshot | `GET /tape/{ticker}/state` | `/summary`, `WS /stream` |
| 2 | **14 core features × 5 windows** | `FeatureEngine` (windows 10/30/60/180/300s) → snapshot | `GET /tape/{ticker}/features` | `/summary` (subset), `WS /stream` |
| 3 | **bid / ask / spread / last** (spread = ask − bid) | `MarketState` (latest Quote/Trade) → snapshot | `GET /tape/{ticker}/summary` | `WS /stream` |
| 4 | **Recent trades** (price / size / **side**) | **Aggressor classifier** (≥ask⇒buy, ≤bid⇒sell, else unknown) over provider TradeEvents | `GET /tape/{ticker}/events` | `WS /stream` |
| 5 | **Observations + event-log messages** | Engine **observation / transition emitter** | `GET /tape/{ticker}/events` | `WS /stream` |
| 6 | **Watched-source descriptor + watch/stream status** (sim scenario \| `live <SYM>` \| `historical <SYM> <window>`; status connecting/live/**stale**/closed) | `WatchManager` (records mode + params at watch) / engine feeder (owns `stream_status`) | `GET /tape/{ticker}/summary` (+ `POST`/`DELETE /watch` responses) | `WS /stream` |
| 7 | **Symbol search results** (symbol + name) | **Vendor-agnostic adapter** (Alpaca first) behind the provider seam | `GET /symbols/search?q=` | — |
| 8 | **Market clock** (open/closed + next open/close) | **Vendor-agnostic adapter** / market-clock module | `GET /market/clock` | Live market-status indicator reads this |
| 9 | **Real-data availability / failure state** (`provider unavailable` \| `not a tradable symbol` \| `no data for that window` \| `market is closed`) | Live / Historical provider + adapter (credential check + vendor responses) | Explicit error from `POST /watch/{ticker}` (mid-stream feed-gap ⇒ `stream_status="stale"` on the row-6 snapshot) | UI renders the matching non-cockpit state |

**Provider & vendor seam (singularity — architectural, not a displayed value).**
- One **provider interface** (`TradeEvent`/`QuoteEvent`/[later]`BookLevelEvent`); `SimulatedProvider`, the **live
  provider**, and the **historical-replay provider** all implement it. The engine/API import **none** of them directly
  and **never** import the vendor SDK.
- The concrete vendor (**Alpaca**, free IEX feed) appears in **exactly one adapter module** behind a vendor-neutral
  interface; a second vendor (Polygon, Databento…) is **one new adapter**, no engine/API/provider change.
- Real vendor timestamps are mapped to the engine's **logical timeline** (quote-before-trade preserved) so the engine
  stays unchanged and deterministic per stream.

**Config (no magic numbers).** All window lengths, thresholds, large-print size, impact/absorption cutoffs, confidence
boundaries, **and the stale-gap timeout** live in one config module — never inline literals in engine/classifier code.

**Credentials.** Real-vendor keys come **only** from environment/config (never committed). With no keys, the app runs
simulator-only and the real modes report **row-9** `provider unavailable` — they never fall back to fabricated data.

**Singularity rules (coherence guardrails).**
- Each value in rows 1–6 has exactly **one producer** (the engine); REST, WS, and UI **read** — no recomputation in API
  or frontend. The same ticker shows **identical** values across `/state`, `/features`, `/summary`, `WS /stream`, and UI
  (J-08). Live/historical reads flow through the **same** rows 1–6 — real data does **not** add a parallel state/feature path.
- The new real-data values (rows 7–9) each have **one** computing owner + **one** endpoint; do not add a second lookup
  or a second clock.
- On a feed gap / provider failure the snapshot surfaces explicit **stale / no-data / unavailable** — nothing is
  fabricated to force a green journey (anti-goal: *No fabricated data*).

**Note on module names.** `TapeStateClassifier`, `FeatureEngine`, `MarketState`, the aggressor classifier,
`WatchManager`, the config module, and (new) the **vendor-agnostic adapter** + the live/historical providers are the
**logical canonical owners**. The developer chooses concrete file paths in the owning iteration, but each value keeps
exactly one computing owner and one canonical endpoint — that singularity is what the coherence-auditor enforces.
