# Tapeology — Coherence Blueprint

> Goal session: `i_will_be_super_rich` · Status: **APPROVED** (J-01–J-15 built & in force) · **extended** at iter-5
> with the now-in-scope **analysis-fidelity** half (J-16–J-20): tick-test side resolution, the one focused
> price-candlestick + tape-state-marker chart, pause/resume, and local-time historical-window selection.
> Source: `docs/goal.md` (Product Shape, Must-have journeys J-01–J-30, Key Capabilities, Canonical values).
> Carries forward the **APPROVED** simulated blueprint from session `i_will_be_rich` (J-01–J-09) and the real-data
> half (J-10–J-15): live streaming + historical replay behind a vendor-agnostic adapter (Alpaca first, free IEX feed).
>
> **iter-5 extension is ADDITIVE** — same single `/` HOME, same nav skeleton, same one-engine source of truth. New
> rows 10–12 register the new displayed values; row 4 is clarified (not changed) to name the tick-test fallback inside
> its existing owner. No top-level nav section added/renamed/moved ⇒ **no re-approval requested**.
>
> **iter-9 extension is ADDITIVE (no-silent-dead-clicks, J-21–J-24).** Same single `/` HOME, same nav skeleton, same
> one-engine source of truth. No new displayed engine value: every Watch click is guaranteed an immediate, bounded,
> honest UI response (pending/connecting → streaming | honest non-cockpit | explicit error | inline validation). Row 6
> and row 9 are clarified additively — the already-registered `connecting` status becomes a first-class pre-snapshot
> affordance, and a new `provider_timeout` failure reason is a sibling of the existing row-9 reasons on the SAME
> `POST /watch` failure path. A per-call `vendor_call_timeout_seconds` (backend config) and a `WATCH_REQUEST_TIMEOUT_MS`
> (frontend config) bound every outbound vendor call and the client request — config constants, not displayed values.
> No top-level nav section added/renamed/moved ⇒ **no re-approval requested**.
>
> **iter-10 extension is ADDITIVE (no mute cockpit / no silent return to idle, J-25–J-27).** Same single `/` HOME, same
> nav skeleton, same one-engine source of truth. **No new endpoint, no new producer, no new top-level value.** The work
> extends the **existing row-6 `stream_status`** (owned once by the engine/feeder) with two engine-owned post-connect
> outcomes so a connected watch is never a mute/idle dead-end: **`waiting`** (the watch connected but no first
> trade/quote has arrived yet — replaces a confident `live` over an empty tape) and **`failed`** (the background feeder
> raised / exited unexpectedly — logged server-side and surfaced, never swallowed, never frozen at cold-start). Both flow
> verbatim through the already-registered row-6 serving path (`/summary` + `WS /stream`); the cockpit renders an explicit
> waiting / failed treatment **in place of** blank panels (an in-place non-cockpit treatment, exactly like the existing
> honest-state clause — no new route). The bound that turns a silent no-first-event into `waiting`→`stale` is the
> **already-registered** `stale_gap_seconds` watchdog (no new config). J-28–J-30 (true vendor-call-boundary timeout
> enforcement, fast historical load, fast symbol search) are a SEPARATE later concern — explicitly out of scope here.
> No top-level nav section added/renamed/moved ⇒ **no re-approval requested**.
>
> **iter-11 extension is ADDITIVE (vendor responsiveness, J-28–J-30) — performance/honesty hardening, NO new value.**
> Same single `/` HOME, same nav skeleton, same one-engine source of truth. **No new endpoint, no new producer, no new
> displayed value, no new contract row.** The work hardens the *performance and honesty* of already-registered rows:
> - **Row 9** (`provider_timeout`) is now enforced by a **real call-level vendor deadline** — an HTTP/SDK timeout at the
>   one adapter boundary (`providers/adapters/alpaca.py`), not only the iter-9 `asyncio.wait_for` wrapper a
>   blocking/large-response call can defeat — and the backend-effective bound MUST stay **shorter than** the frontend
>   `WATCH_REQUEST_TIMEOUT_MS` so the backend's honest error wins. An **oversize/high-volume Historical window** maps to an
>   **actionable** message variant ("try a shorter range") on the SAME `POST /watch` failure path — a sibling message, not
>   a new reason endpoint. (J-28)
> - **Rows 10–12 / the historical fetch** keep their single owners; the Historical provider fetch is optimized — **trades
>   + quotes fetched concurrently**, the **needless `_require_tradable` pre-flight removed** (unknown-symbol/no-data
>   honesty preserved), a **bounded in-process window cache** keyed by (symbol, start, end, feed) so a re-watch is
>   near-instant (cached = the SAME real records, never fabricated), and a **prompt bounded warm-up fast-forward**
>   (delivery pacing only — engine math stays logical/deterministic; same stream ⇒ identical features/state/confidence).
>   The fetch wait shows the already-registered row-6 `waiting` treatment, never a blank screen. (J-29)
> - **Row 7** (`Symbol search results`) keeps its single computing owner (the vendor-agnostic adapter) and single endpoint
>   (`GET /symbols/search?q=`); the **tradable-symbol universe is warmed at startup** (existing `lifespan` hook → existing
>   module-level `_ASSET_UNIVERSE` cache; no second store) and optionally background-refreshed, and the **frontend cancels
>   stale in-flight searches** (AbortController) with a sensible **min-query** — performance properties of the same row, no
>   second lookup. A vendor hiccup still yields an empty list, never an error. (J-30)
> New config constants (the call-level HTTP deadline, the window-cache size/age, any warm/refresh interval or fast-forward
> bound, the frontend debounce-ms / min-query) are **config values, not displayed values** (no magic numbers).
> No top-level nav section added/renamed/moved ⇒ **no re-approval requested**.
>
> **iter-12 extension is ADDITIVE (true-clock chart axis + dd-MM-yyyy dates, J-31 / J-35).** Same single `/` HOME, same
> nav skeleton, same one-engine source of truth. It adds **one new contract row (row 13)** and no new top-level surface:
> - **NEW row 13 — Canonical display/epoch anchor.** The engine/feeder preserves, **once and additively**, the real UTC
>   epoch origin (historical/live = the first record's real epoch) or a **synthetic session-start** instant (simulated),
>   alongside the existing logical timeline. The engine still **bins on its deterministic logical timeline** and reads no
>   wall-clock for classification — the anchor is **display metadata only**. It is served read-only through the existing
>   **`GET /tape/{ticker}/history`** projection (and the snapshot serializer); the **chart reads it verbatim** to render
>   **true clock time** (`dd-MM-yyyy HH:mm:ss`, local zone label) on the axis / crosshair / markers — it still recomputes
>   no price/side/state and still reads OHLC/markers from **row 10**. This introduces no second timeline, no second
>   history endpoint, and no recomputation outside the engine. (J-31)
> - **Row 12 / `lib/datetime.ts`** keeps its single owner; J-35 adds **one shared `dd-MM-yyyy` formatter** there that every
>   UI date render is routed through, and replaces the native `<input type="date">` with a **custom validated `dd-MM-yyyy`
>   text input** — a **presentation change only** (no new computed/served value, no new row). Timezone correctness is
>   **unchanged**: the field still carries the explicit local zone label and resolves to the **same** tz-aware instant via
>   the existing row-12 resolver (no silent UTC shift); **J-20** holds. (J-35)
> No top-level nav section added/renamed/moved ⇒ **no re-approval requested**.

**Governing principle.** Tapeology is a single-ticker **tape cockpit**. Every tape state, confidence, and feature is
computed **exactly once in the engine** and read identically by REST, WebSocket, and the UI (anti-goal: *Single source
of truth*). The engine and API depend **only** on the **provider interface** (`TradeEvent` / `QuoteEvent`); the
simulator, the live provider, and the historical-replay provider are three swappable implementations of that one
interface — adding or swapping a data source touches **neither the engine nor the API**. A concrete vendor SDK lives in
**exactly one adapter module** behind a vendor-neutral seam (a second vendor = one new adapter). Classification is
**price impact, not raw aggression**. Real-data failures surface an **explicit, distinct state — never a fabricated
cockpit**. The one allowed chart is the focused price candlestick + tape-state-marker overlay — **no** indicators,
studies, or drawing tools, and **no** order/execution affordance (anti-goal: *Stay in scope*). Every vendor-gated Watch
is bounded by a **real call-level deadline** (backend bound < frontend bound) and interactive vendor paths are **fast by
design** (concurrent fetch, cached windows, warmed search) — never fast by lengthening timeouts, never by fabricating or
dropping data (anti-goal: *Bounded, honest, performant vendor calls*).

---

## Information Architecture

**App shell (persistent).** Top bar: app name **Tapeology** · **data-source selector (Live / Historical / Simulated)** ·
**mode-specific controls** (revealed by the selector, without changing the cockpit):
- *Simulated* → **ticker input** (e.g. `SIM-BUYER`).
- *Live* → **symbol search** + **market-status indicator** (open/closed, from `GET /market/clock`).
- *Historical* → **symbol search** + **date + time-window picker (local time, zone label, US-session quick-picks)** + **replay-speed** control.

…then **Watch** (`POST /watch/{ticker}` with an optional `{mode,start,end,speed}` body; empty body = sim) ·
**watched-source label** (the sim scenario, `live AAPL`, or `historical AAPL <window>`) · **stream-status** dot (the
engine's canonical `snapshot.stream_status` — connecting / **waiting** / live / stale / **paused** / **failed** / closed) ·
**Pause / Resume** (`POST /watch/{ticker}/pause` · `POST /watch/{ticker}/resume`; freeze/continue without teardown) ·
**Stop** (`DELETE /watch/{ticker}`).
Calm dark surface, monospaced numerics; green = buy-side / positive impact, red = sell-side / negative impact / failed,
amber = absorption / unclear / stale / waiting.

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
  - **Connected-but-no-data (waiting) treatment** — when the watch connected but no first trade/quote has arrived (row-6
    `stream_status == "waiting"`): an explicit, human-readable "Connected to <SYMBOL> (<mode>) — waiting for the first
    trade…" panel **in place of** blank panels under a bare `live` dot (J-26). It reads the canonical status — no
    client-side guess; the status NEVER reads a confident `live` over an empty tape. *This same waiting/progress treatment
    fills the Historical fetch wait while a busy window loads (J-29) — never a blank/idle screen.*
  - **Feeder-failure treatment** — when the background feeder raised / exited unexpectedly (row-6
    `stream_status == "failed"`): the existing failure panel / error banner, rendered in place of the cockpit (J-23/J-27).
    The failure is logged server-side and surfaced — never swallowed, never left frozen at cold-start.
  - **Honest non-cockpit states** (real modes) — rendered *in place of* the cockpit, never alongside fabricated panels:
    *provider unavailable* (no credentials), *not a tradable symbol*, *no data for that window*, *market is closed
    (with next open)*, and *provider timed out* (with an **actionable** "try a shorter range" variant for an oversized
    high-volume Historical window — J-28).

**Canonical home per journey** (all on `/`, ≤1 click):
J-01 → whole cockpit · J-02 / J-03 / J-06 → tape-state panel · J-04 / J-05 → tape-state + absorption/refresh readouts ·
J-07 → event-log + observations · J-08 → `/` panels vs the REST endpoints (same values) · J-09 → Stop + idle state ·
**J-10 → data-source selector + its mode-specific control reveal** · **J-11 → Historical controls → cockpit** ·
**J-12 → Live controls + status → cockpit** · **J-13 → symbol search box** · **J-14 → the honest non-cockpit states** ·
**J-15 → stream-status dot (live ⇄ stale)** ·
**J-16 → recent-trades panel (resolved side)** · **J-17 / J-18 → price-chart pane above the cockpit (sim / historical)** ·
**J-19 → Pause/Resume controls + PAUSED indicator** · **J-20 → Historical date/time picker (local-zone label + quick-picks)** ·
**J-21 → synchronous pending/connecting cockpit treatment** · **J-22 → bounded error banner (provider_timeout / unreachable)** ·
**J-23 → feeder/connect-failure treatment (StreamFailedState + banner)** · **J-24 → inline Watch-input validation** ·
**J-25 → the watch always leaves idle for a non-idle terminal state (status dot + the in-place treatments above), real modes + off-hours** ·
**J-26 → the connected-but-no-data (waiting) treatment** · **J-27 → the waiting→stale/closed bound + the feeder-failure treatment** ·
**J-28 → the actionable provider-timeout / oversize-window error on the failure panel (real call-level deadline behind it)** ·
**J-29 → the Historical fetch wait (waiting/progress treatment) → a fast-loaded cockpit (concurrent fetch + cached window + prompt warm-up)** ·
**J-30 → the symbol search box (warmed universe, cancellable, min-query — crisp/instant)** (all on the same `/` cockpit area; no new surface).

No second page, no watchlist grid, no dashboard, no execution/order controls, no general charting (anti-goals:
single-ticker UI; no execution path; one focused chart only).

---

## Data Contract

Every displayed value is computed once and read-only re-exposed elsewhere; `…/summary` and `WS …/stream` **re-expose**
the snapshot and MUST NOT recompute. `…/state` and `…/features` are the canonical REST reads. Rows 1–6 are the
**already-built** simulated contract (in force, unchanged); rows 7–9 are the **already-built** real-data additions;
rows 10–12 are the **analysis-fidelity additions**: rows 10 (J-17 chart **render-verified**; J-18 real-historical render closed at iter-8) and 11 (J-19 pause/resume) are **built & in force**; row 12 (J-20 local-time historical window) is **built at iter-8** (J-16 is folded into row 4). **iter-11 adds NO row** — it hardens the *performance/honesty* of rows 7 and 9 and the historical-fetch path (see the iter-11 header note). **iter-12 adds row 13** (the additive display/epoch anchor for the true-clock chart axis — J-31; J-35's shared `dd-MM-yyyy` formatter is presentation-only, no row) — see the iter-12 header note.

| # | Displayed value | Canonical computing module (computed once) | Canonical serving endpoint | Re-exposed read-only by |
|---|---|---|---|---|
| 1 | **Tape state + confidence** | `TapeStateClassifier` (rule/threshold over features) → snapshot | `GET /tape/{ticker}/state` | `/summary`, `WS /stream` |
| 2 | **14 core features × 5 windows** | `FeatureEngine` (windows 10/30/60/180/300s) → snapshot | `GET /tape/{ticker}/features` | `/summary` (subset), `WS /stream` |
| 3 | **bid / ask / spread / last** (spread = ask − bid) | `MarketState` (latest Quote/Trade) → snapshot | `GET /tape/{ticker}/summary` | `WS /stream` |
| 4 | **Recent trades** (price / size / **side**) | **Aggressor classifier** — quote rule (≥ask⇒buy, ≤bid⇒sell) **then a tick-test fallback** (no quote yet **or** strictly mid-spread ⇒ uptick=buy / downtick=sell / zero-tick carries last non-zero dir; no quote **and** no prior trade ⇒ `unknown`) over provider TradeEvents | `GET /tape/{ticker}/events` | `WS /stream` |
| 5 | **Observations + event-log messages** | Engine **observation / transition emitter** | `GET /tape/{ticker}/events` | `WS /stream` |
| 6 | **Watched-source descriptor + watch/stream status** (sim scenario \| `live <SYM>` \| `historical <SYM> <window>`; status connecting / **waiting** / live / **stale** / **paused** / **failed** / closed) — **`waiting`** = connected but no first event yet (J-26; replaces a confident `live` over an empty tape; also fills the J-29 Historical fetch wait); **`failed`** = the feeder raised / exited unexpectedly (J-23/J-27; logged + surfaced, never swallowed). One owner: the engine/feeder; NO second `stream_status` writer | `GET /tape/{ticker}/summary` (+ `POST`/`DELETE /watch` responses) | `WS /stream` |
| 7 | **Symbol search results** (symbol + name) | **Vendor-agnostic adapter** (Alpaca first) behind the provider seam — the tradable-symbol universe is the module-level `_ASSET_UNIVERSE` cache, **warmed at startup** via the existing `lifespan` hook (and optionally background-refreshed); a re-fetch per keystroke is forbidden (J-30). One owner, no second universe store | `GET /symbols/search?q=` (min-query enforced; vendor hiccup ⇒ empty list, never an error) | — (the frontend debounces + **cancels stale in-flight searches** via AbortController so a late response can't overwrite a newer one — J-30; presentation only) |
| 8 | **Market clock** (open/closed + next open/close) | **Vendor-agnostic adapter** / market-clock module | `GET /market/clock` | Live market-status indicator reads this |
| 9 | **Real-data availability / failure state** (`provider unavailable` \| `not a tradable symbol` \| `no data for that window` \| `market is closed` \| **`provider_timeout`** — a bounded vendor/clock/fetch call that exceeded its deadline) | Live / Historical provider + adapter (credential check + vendor responses). The bound is a **real call-level deadline at the adapter HTTP/SDK boundary** (an HTTP/SDK timeout — J-28), backstopped by the watch endpoint's `asyncio.wait_for(..., vendor_call_timeout_seconds)`; the backend-effective bound stays **shorter than** the frontend `WATCH_REQUEST_TIMEOUT_MS` so the backend's honest error wins. A hung/oversized vendor yields `provider_timeout`, **never** an unbounded wait and **never** a fabricated tape; an oversize/high-volume Historical window yields an **actionable** message variant ("try a shorter range"), not a misleading generic retry | Explicit error from `POST /watch/{ticker}` (mid-stream feed-gap ⇒ `stream_status="stale"` on the row-6 snapshot; a post-connect feeder failure ⇒ `stream_status="failed"` on the row-6 snapshot — same single failure ownership; `provider_timeout` is a sibling reason / message, not a new endpoint) | UI renders the matching non-cockpit state / error banner |
| 10 | **Price history: OHLC bars (per 10/30/60 s) + tape-state-transition markers** (state + confidence + ts) | **Engine history buffer** (accumulates watched price → config-binned OHLC + meaningful-transition markers; computed once with the snapshot) | `GET /tape/{ticker}/history?bar=<10\|30\|60>` (pure projection; sim + historical only) | Chart reads this — never recomputes price/side/state |
| 11 | **Paused state** (boolean) | **Engine/feeder** (owns paused; pause freezes the feeder without teardown — no fabricated backfill) → snapshot | `GET /tape/{ticker}/summary` (set via `POST /watch/{ticker}/pause` · `POST /watch/{ticker}/resume`) | `WS /stream`; UI renders PAUSED + toggles the control |
| 12 | **Resolved historical window** (tz-aware start/end instants for the user's selected **local** window; explicit **local zone label** + **US-session quick-picks** Open 9:30 ET / Close 16:00 ET / Full RTH, each annotated with its local equivalent) | **Frontend datetime module** (`apps/frontend/lib/datetime.ts` — the resolution fn resolves the local selection AND the ET session anchors via the IANA `America/New_York` zone, DST-correct, → exact tz-aware UTC instants **once, before** the fetch; the 9:30/16:00 ET anchors are named preset constants, not engine thresholds) → request body | `POST /watch/{ticker}` body `{mode:"historical",start,end,speed}` (timezone-aware instants; backend `_parse_window_dt` honors the offset verbatim) | Historical provider fetches exactly the resolved window (no second tz conversion, no silent UTC shift) — **built at iter-8** |
| 13 | **Canonical display/epoch anchor** (the real UTC epoch origin for historical/live = the first record's real epoch; a **synthetic session-start** instant for simulated) — **additive display metadata**, NOT a second timeline | **Engine/feeder** (preserved once alongside the logical timeline; the engine still bins on the **deterministic logical timeline** and reads no wall-clock for classification — the anchor never feeds features/state/confidence) | exposed read-only via the existing **`GET /tape/{ticker}/history?bar=<10\|30\|60>`** projection (+ the snapshot serializer) | Chart reads it **verbatim** to stamp the axis / crosshair / markers with **true clock time** (`dd-MM-yyyy HH:mm:ss`, local zone label); `WS /stream` / `/summary` re-expose as applicable — the chart still reads OHLC/markers from **row 10** and recomputes no price/side/state — **built at iter-12** |

**Provider & vendor seam (singularity — architectural, not a displayed value).**
- One **provider interface** (`TradeEvent`/`QuoteEvent`/[later]`BookLevelEvent`); `SimulatedProvider`, the **live
  provider**, and the **historical-replay provider** all implement it. The engine/API import **none** of them directly
  and **never** import the vendor SDK.
- The concrete vendor (**Alpaca**, free IEX feed) appears in **exactly one adapter module** behind a vendor-neutral
  interface; a second vendor (Polygon, Databento…) is **one new adapter**, no engine/API/provider change. The **real
  call-level HTTP/SDK deadline** (J-28), the **concurrent trades+quotes fetch** + **bounded window cache** (J-29), and
  the **warmed symbol universe** (J-30) all live inside this one adapter / its serving endpoints — vendor specifics do
  not leak into the engine, providers, or API.
- Real vendor timestamps are mapped to the engine's **logical timeline** (quote-before-trade preserved) so the engine
  stays unchanged and deterministic per stream. The J-29 concurrent fetch and prompt warm-up are **delivery/fetch
  optimizations only**: the merged stream keeps quote-before-trade ordering and the engine math stays purely logical and
  deterministic (same ordered stream ⇒ identical features/state/confidence); a cached window replays the **same real**
  records (no fabrication, no drop).
- The seam has a **synchronous** variant (`stream() -> Iterable`, used by the bounded simulated + historical-replay
  providers) and an **async** variant (`async stream() -> AsyncIterator`, used by the unbounded **live** provider) — the
  **same** interface in two shapes; both feed the **same** engine via `process_event` (no engine change). The **live
  feeder** is the single owner that flips row-6 `stream_status` to **`stale`** when no event arrives within
  `stale_gap_seconds` (and back to **`live`** on resume), fabricating no trades — there is no second `stream_status`
  writer and no parallel live state/feature path. The **same feeders** are the single owner of the row-6
  **`waiting`** (held before the first event) and **`failed`** (on a feeder exception/early-exit) statuses — no second
  writer. **Pause** (row 11) is also a feeder-level freeze owned by the feeder/engine — distinct from `stop()` (which
  cancels + tears down); pause does NOT cancel the task and synthesizes no catch-up data on resume.

**Config (no magic numbers).** All window lengths, thresholds, large-print size, impact/absorption cutoffs, confidence
boundaries, the stale-gap timeout, the **per-call `vendor_call_timeout_seconds`** (the bound on a single outbound
vendor/clock/fetch call that gates a Watch — distinct from the mid-stream `stale_gap_seconds` delivery watchdog),
the **real call-level HTTP/SDK deadline** (J-28; backend-effective bound < frontend `WATCH_REQUEST_TIMEOUT_MS`),
the **historical-window cache size/age** and any **warm-up fast-forward bound** (J-29), any **symbol-universe warm /
refresh interval** (J-30), **the OHLC bar sizes / marker-significance thresholds, and any tick-test tie/tolerance**
live in one config module — never inline literals in engine/classifier code. (The tick test itself is a pure rule with
no numeric cutoff; if any tolerance is introduced it MUST live in config.) The frontend's matching client-side request
backstop (`WATCH_REQUEST_TIMEOUT_MS`) and the **symbol-search debounce-ms / min-query** (J-30) likewise live in one
`lib/config.ts` — no inline millisecond/length literal. The connected-but-no-first-event → `stale` bound (J-26/J-27)
reuses the **already-registered** `stale_gap_seconds` — no new timeout constant is introduced for it.

**Credentials.** Real-vendor keys come **only** from environment/config (never committed). With no keys, the app runs
simulator-only and the real modes report **row-9** `provider unavailable` — they never fall back to fabricated data. The
J-30 startup universe-warm is a **no-op without credentials** (search stays an empty list, never an error).

**Singularity rules (coherence guardrails).**
- Each value in rows 1–6 has exactly **one producer** (the engine); REST, WS, and UI **read** — no recomputation in API
  or frontend. The same ticker shows **identical** values across `/state`, `/features`, `/summary`, `WS /stream`, and UI
  (J-08). Live/historical reads flow through the **same** rows 1–6 — real data does **not** add a parallel state/feature path.
- The new real-data values (rows 7–9) each have **one** computing owner + **one** endpoint; do not add a second lookup
  or a second clock. The J-30 warmed universe reuses the **one** `_ASSET_UNIVERSE` cache (no second store); the J-28
  call-level deadline and J-29 window cache live in the **one** adapter (no second fetch path).
- The analysis-fidelity values (rows 10–12) each have **one** computing owner + **one** endpoint/body: the chart reads
  row-10 OHLC/markers from the engine history buffer (it MUST NOT bin candles, infer side, or place markers itself); the
  PAUSED indicator reads row-11 from the snapshot (no UI-side guess); the historical window is resolved once by row-12
  before the fetch (no second tz conversion, no silent UTC reinterpretation). The J-29 concurrent fetch / cache / warm-up
  do **not** move any computation out of the engine — OHLC/markers/features are still computed once in the engine.
- **The display/epoch anchor (row 13) is additive display metadata with one owner** — the engine/feeder preserves it
  once alongside the logical timeline; the chart reads it **verbatim** to render true clock time and still reads OHLC/markers
  from row 10. It introduces **no second timeline** (the engine still bins on the deterministic logical timeline, reads no
  wall-clock for classification), **no second history endpoint**, and **no recomputation** of price/side/state in the UI
  (single source of truth + determinism hold). The shared `dd-MM-yyyy` formatter (J-35) is presentation-only — it computes
  no value and the historical window still resolves once via row 12 (no silent UTC shift; J-20 holds).
- On a feed gap / provider failure the snapshot surfaces explicit **stale / no-data / unavailable / failed / timed-out** —
  nothing is fabricated to force a green journey (anti-goal: *No fabricated data*). An empty historical window ⇒ **empty**
  chart. A cached window replays the **same real** records.
- **No silent dead-clicks (J-21–J-24).** Every Watch click resolves to exactly one visible state within a bounded
  time: a pre-snapshot **connecting** affordance (row-6 status, shown synchronously before the round-trip), then
  streaming data | an honest non-cockpit panel (row 9) | an explicit error (incl. **`provider_timeout`** from the
  bounded vendor call, and a client-side `WATCH_REQUEST_TIMEOUT_MS` backstop on a hung backend) | an inline
  validation message (empty symbol / invalid window). No empty `catch`, no dropped promise, no unbounded external
  wait. These are presentation states only — they add **no** client-side recomputation of an engine value (rows 1–6
  stay single-source-of-truth); the timeout values are config constants, not displayed values.
- **No mute cockpit / no silent return to idle (J-25–J-27).** AFTER the click resolves, a valid Watch lands on a
  **non-idle terminal state** and never silently returns to / remains on idle: streaming data, an explicit honest panel
  (row 9), an explicit error, the **`waiting`** connecting/waiting treatment, or **`stale`/`closed`/`failed`**. The
  cockpit MUST NOT present a confident **`live`** over an empty tape — an empty tape reads **`waiting`** (then `stale`
  once `stale_gap_seconds` is exceeded). A feeder exception/early-exit flips row-6 to **`failed`** (logged + surfaced),
  never swallowed, never frozen at cold-start, never a fabricated `live`. An off-hours **Live** watch lands on the
  explicit **`market_closed`** panel (or, if the clock is indeterminate, the **`waiting`→`stale`/`failed`** path) —
  never idle, never a fake-`live` empty cockpit. These are all the **one** engine-owned row-6 `stream_status` rendered
  read-only by the UI — no second status writer, no client-side recompute of any rows 1–6 value.
- **Bounded, honest, performant vendor calls (J-28–J-30).** Every vendor-gated Watch is bounded by a **real call-level
  deadline** (an HTTP/SDK timeout at the adapter boundary, not only the `asyncio.wait_for` wrapper), and the
  backend-effective bound is **shorter than** the frontend `WATCH_REQUEST_TIMEOUT_MS` so the backend's honest error
  wins. Interactive vendor paths are **fast by design**: a legitimate high-volume Historical window loads within budget
  via a **concurrent** trades+quotes fetch, **no needless pre-flight**, a **cached/reused** window, and a **prompt
  warm-up** — never by lengthening timeouts; symbol search reads a **warmed/cached** universe (no per-keystroke
  re-fetch), **cancels** stale requests, and enforces a **min-query**. Any timeout/oversize error is **actionable for
  the real cause** ("shorten the window"), never a misleading retry. Every optimization preserves correctness — **no
  fabricated or dropped trades/quotes, no recomputation outside the engine** (single source of truth holds); a cached
  window is the same real data, and a vendor hiccup in search is an empty list, never an error.

**Note on module names.** `TapeStateClassifier`, `FeatureEngine`, `MarketState`, the aggressor classifier,
`WatchManager`, the config module, the **vendor-agnostic adapter** + the live/historical providers, and (new) the
**engine history buffer** + the **frontend datetime module** are the **logical canonical owners**. The developer
chooses concrete file paths in the owning iteration, but each value keeps exactly one computing owner and one canonical
endpoint — that singularity is what the coherence-auditor enforces.
