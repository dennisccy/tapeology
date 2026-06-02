# Tapeology — Coherence Blueprint

> Goal session: `i_will_be_rich` · Status: **DRAFT (baseline iter 0) — awaiting human approval before any feature is built.**
> Source: `docs/goal.md` (Product Shape, Must-have journeys, Key Capabilities, Canonical values).

**Governing principle.** Tapeology is a single-ticker **tape cockpit**. Every tape state,
confidence, and feature is computed **exactly once in the engine** and read identically by
REST, WebSocket, and the UI (anti-goal: *Single source of truth*). The engine and API depend
only on the **provider interface**; the Phase-1 simulator is swappable for a live feed without
touching either. Classification is **price impact, not raw aggression** — high one-sided
aggression with no price progress resolves to *absorption*, never *control*.

---

## Information Architecture

**App shell (persistent).** Top bar: app name **Tapeology** · **ticker input + Watch button**
(submits `POST /watch/{ticker}`) · **watched-ticker label** · **scenario indicator** (which
simulated scenario is replaying) · **stream-status** dot (connected / stale / closed) · **Stop**
control (`DELETE /watch/{ticker}`). Calm dark surface, monospaced numerics; green = buy-side /
positive impact, red = sell-side / negative impact, amber = absorption / unclear.

**Routes — Phase 1 is exactly one screen.**

- **`/` — Watch (the tape cockpit) — HOME.** Every Must-have journey lives here; all of it is
  visible in ≤1 click after a ticker is submitted. Panels:
  - **Quote panel** — bid / ask / spread / last (spread = ask − bid).
  - **Recent-trades panel** — rolling list: price / size / **side** (buy/sell/unknown, color-coded).
  - **Features panel** — the 14 core features, per window (**10s / 30s / 60s / 180s / 300s**).
  - **Tape-state panel** — current state (`buyer_control` | `seller_control` | `bid_absorption`
    | `ask_absorption` | `unclear`) + **confidence**; color encodes side/impact.
  - **Observations panel** — current human-readable observations.
  - **Event-log panel** — appended transition/observation messages (live over WS).
  - **Idle/empty state** — before a ticker is watched, and after Stop: empty cockpit, no stale numbers.

**Canonical home per journey** (all on `/`, ≤1 click):
J-01 → whole cockpit · J-02 / J-03 / J-06 → tape-state panel · J-04 / J-05 → tape-state +
features (absorption / refresh readouts) · J-07 → event-log + observations panels ·
J-08 → `/` panels vs the REST endpoints below (same values) · J-09 → Stop control + idle state.

No second page, no watchlist grid, no dashboard (anti-goal: single-ticker UI only).

---

## Data Contract

Every displayed value is computed once in the per-ticker engine instance and serialized from one
snapshot. `…/summary` and `WS …/stream` **re-expose** that snapshot read-only — they MUST NOT
recompute. `…/state` and `…/features` are the canonical REST reads (per goal.md).

| Displayed value | Canonical computing module (computed once) | Canonical serving endpoint | Re-exposed read-only by |
|---|---|---|---|
| **Tape state + confidence** | `TapeStateClassifier` (rule/threshold over features) → engine snapshot | `GET /tape/{ticker}/state` | `/summary`, `WS /stream` |
| **14 core features × 5 windows** | `FeatureEngine` (rolling windows 10/30/60/180/300s) → snapshot | `GET /tape/{ticker}/features` | `/summary` (headline subset), `WS /stream` |
| **Current bid / ask / spread / last** (spread = ask − bid) | `MarketState` tracker (latest QuoteEvent / TradeEvent) → snapshot | `GET /tape/{ticker}/summary` | `WS /stream` |
| **Recent trades** (price / size / **side**) | **Aggressor classifier** (price ≥ ask ⇒ buy, ≤ bid ⇒ sell, else unknown) over provider TradeEvents | `GET /tape/{ticker}/events` | `WS /stream` |
| **Observations + event-log messages** | Engine **observation / transition emitter** (on state change & meaningful events) | `GET /tape/{ticker}/events` | `WS /stream` |
| **Watched-scenario label + watch/stream status** | `WatchManager` / `SimulatedProvider` registry (scenario bound per reserved sim ticker) | `GET /tape/{ticker}/summary` (+ `POST` / `DELETE /watch/{ticker}` responses) | `WS /stream` |

**Config (no magic numbers).** All window lengths, thresholds, large-print size,
impact/absorption cutoffs, and confidence boundaries live in one config module read by the
engine/classifier — never inline literals in engine/classifier code.

**Singularity rules (coherence guardrails).**
- Tape state, confidence, and each feature have exactly **one producer** (the engine). REST, WS,
  and UI **read** them — no recomputation in the API layer or frontend. `spread`, the aggressive
  ratios, price impacts, and confidence are all engine-side; the UI never re-derives them.
- The same ticker shows **identical** values across `/state`, `/features`, `/summary`, `WS /stream`,
  and the UI (J-08 verifies this).
- The engine and API depend **only** on the provider interface (`TradeEvent` / `QuoteEvent` /
  [later] `BookLevelEvent`); swapping the simulator for a live feed touches neither.
- On a provider gap/failure the snapshot surfaces an explicit **stale / no-data** state — nothing
  is fabricated to force a green journey.

**Note on module names.** `TapeStateClassifier`, `FeatureEngine`, `MarketState`, the aggressor
classifier, `WatchManager`, and the config module are the **logical canonical owners**. The
developer may choose concrete file paths in iter 1, but each value keeps exactly one computing
owner and one canonical endpoint as listed above — that singularity is the contract the
coherence-auditor enforces.
