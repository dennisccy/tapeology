# goal-i_will_be_super_rich-iter-1 Execution Plan

> First real-data slice: the **vendor-agnostic adapter seam**, the **credentials/availability
> contract**, the optional `{mode}` watch body with an honest **no-credentials gate**, and the
> **data-source selector** UI. Targets **J-10** and the **no-credentials path of J-14**.
> Verified with **NO credentials configured**. The engine and all canonical reads
> (`/state`, `/features`, `/summary`, `/events`, `WS /stream`) are **untouched**.

## What to Build

**Backend**
- **Vendor-neutral adapter seam:** new `app/providers/adapters/base.py` defining a vendor-neutral
  `MarketDataAdapter` interface (a `name` + `is_available() -> bool`). No vendor specifics, no
  credential names here.
- **Exactly one concrete adapter:** new `app/providers/adapters/alpaca.py` (`AlpacaAdapter`)
  implementing **only** credential detection + `is_available()` — reads `ALPACA_API_KEY` /
  `ALPACA_API_SECRET` (and optional `ALPACA_FEED`, default `iex`) **from the environment only**.
  This is the **single module** where credential names / vendor specifics live. **Do NOT import or
  install the Alpaca SDK this iteration** — `is_available()` is pure env-var presence detection, so
  no new dependency and no supply-chain gate.
- **Canonical `real_data_available` boolean** derived from `AlpacaAdapter().is_available()` — the
  one source for the row-9 availability state. **Not** placed in the engine `Config` dataclass
  (that holds engine thresholds, not secrets).
- **`apps/backend/.env.example`** documenting the variable **names** with **empty** secret values
  (`ALPACA_API_KEY=`, `ALPACA_API_SECRET=`; `ALPACA_FEED` may show its non-secret default `iex`).
  The only committable env file (`.gitignore` already allows `!.env.example`).
- **Optional `{mode, start, end, speed}` body on `POST /watch/{ticker}`** (Pydantic model, all
  fields optional). Routing:
  - no body / `{}` / no `mode` / `mode == "sim"` → **existing sim path, unchanged** (regression must stay green).
  - `mode ∈ {live, historical}` **and `real_data_available` is False** → **HTTP 503**,
    `detail: "real-data provider unavailable"`, `reason: "provider_unavailable"`. **No engine is
    created** (raise before `manager.watch()`); nothing synthesized; no sim fall-back.
  - unrecognized `mode` → explicit **4xx** (Pydantic `Literal`/enum → 422 is acceptable; or explicit 400). Never a silent default into a real feed.
  - `mode ∈ {live, historical}` **with creds present** → real serving is **out of scope** (J-11/J-12).
    Until the real providers land this branch must still return an **explicit non-cockpit error
    (never a fabricated cockpit)**. Since verification is credentials-absent this is a guard, not a
    feature (see Assumptions).

**Frontend** (the cockpit body itself stays identical across modes)
- **Data-source selector** in the TopBar — exactly three modes **Live / Historical / Simulated**, default **Simulated**.
- **Mode-specific control reveal:** Simulated → existing ticker input + Watch; Live → symbol search
  (free-text) + market-status indicator + Watch; Historical → symbol search + date + time-window
  picker + replay-speed control + Watch.
- **Honest non-cockpit state:** a Live/Historical Watch that returns 503 provider-unavailable
  renders a **"real-data provider unavailable"** panel **in place of** the cockpit — never a cockpit, never a silent fall-back to Simulated.
- **Market-status indicator (Live):** renders an honest **"unavailable"** with no creds; MUST NOT
  fabricate open/closed (real clock via `GET /market/clock` is deferred — see Assumptions).
- **Watch-lifecycle hardening (iter-0 lesson):** a new Watch — or switching data source / symbol —
  FIRST tears down the prior watch (`DELETE /watch/{prevTicker}`) and closes its WS before starting
  the new one. No orphaned backend watches/sockets.
- **Simulated unchanged end-to-end:** SIM-BUYER → buyer_control exactly as J-01/J-02.

## Agents Required
- **backend-data: yes** — adapter seam, credentials/availability contract, watch-body routing + 503 gate, backend tests.
- **frontend-ux: yes** — data-source selector, per-mode controls, provider-unavailable non-cockpit state, watch-lifecycle teardown.
- developer: yes — implements both halves above with TDD.

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

**Create**
- `apps/backend/app/providers/adapters/__init__.py` — package marker.
- `apps/backend/app/providers/adapters/base.py` — vendor-neutral `MarketDataAdapter` interface (`name`, `is_available()`).
- `apps/backend/app/providers/adapters/alpaca.py` — `AlpacaAdapter`: env-only credential detection + `is_available()`; **only** module with `ALPACA_*` names. Exposes the canonical `real_data_available`.
- `apps/backend/.env.example` — variable names, empty secret values.
- `apps/backend/tests/test_real_data_gate.py` (or extend `test_api.py`) — watch-body routing, 503 gate, no-engine-created 404, `real_data_available` env presence/absence, single-module credential confinement.
- `apps/frontend/components/DataSourceSelector.tsx` — the three-mode segmented control.
- `apps/frontend/components/ProviderUnavailable.tsx` — the "real-data provider unavailable" non-cockpit panel.

**Modify**
- `apps/backend/app/main.py` — accept optional `WatchRequest` body on `POST /watch`; route sim vs. real; raise the 503 gate **before** creating an engine. (Do not touch the read endpoints or WS.)
- `apps/frontend/components/TopBar.tsx` — host the selector + mode-specific controls (Live: search + market-status; Historical: search + date/time-window + replay-speed).
- `apps/frontend/app/page.tsx` — hold `mode` + per-mode params; on Watch/switch, `DELETE` the prior watch first; render `ProviderUnavailable` in place of the cockpit on a 503.
- `apps/frontend/lib/api.ts` — `watchTicker` accepts an optional `{mode,start,end,speed}` body; distinguishes the 503 `provider_unavailable` result from a generic error.
- `apps/frontend/lib/types.ts` — add the `DataSourceMode` type and any watch-result shape needed (no engine-value duplication).

**Do NOT touch:** `app/engine/*`, `app/config.py`, `app/serializers.py`, `app/providers/base.py`, `app/providers/simulated.py`, `watch_manager.py` internals (the sim watch path), and the canonical read/stream endpoints. Real data flows through the same engine via a provider behind the seam in **later** iterations.

## UI Evolution
- **New user-facing capability:** pick a data source (Live / Historical / Simulated) and see the controls each mode needs; choosing a real mode with no credentials yields an explicit, honest "real-data provider unavailable" instead of any fabricated read; Simulated works exactly as before.
- **New information displayed:** the data-source selector + per-mode controls; the Live market-status indicator (honest "unavailable"); the "real-data provider unavailable" non-cockpit state.
- **New user actions:** pick a data source; (Live/Historical) type a symbol; (Historical) choose a date/time window + replay speed; Watch in a real mode.
- **UI surface changes:** TopBar gains the selector + mode-specific controls; the `/` cockpit area gains the in-place provider-unavailable state. Still **exactly one screen**.
- **Navigation changes:** none — everything stays under the existing IA home `/` (no nav-skeleton change, no blueprint edit).

## Visual Requirements
- **Component patterns:** reuse the existing hand-built `Panel` for the provider-unavailable state and the mode controls; the selector is a 3-way segmented control styled like the existing TopBar buttons. No new component library.
- **Layout:** selector + mode-specific controls live inline in the TopBar (the existing flex header); the provider-unavailable panel replaces the cockpit grid in `<main>`.
- **Color semantics (load-bearing):** amber/muted for "unavailable" and the provider-unavailable panel (amber = unavailable/unclear); keep emerald for the active Watch CTA; monospaced numerics for any symbol/window readouts. No new palette tokens.
- **States to handle:** Simulated (idle → cockpit, unchanged); Live/Historical with no creds (provider-unavailable panel, market-status "unavailable"); selector switch while watching (prior watch torn down, return to idle/empty before the new mode's controls). No loading spinner needed (the 503 is immediate).

## Key Test Scenarios

**Backend (pytest, assert exact values)**
- no-body `POST /watch/SIM-BUYER` → 200 sim watch (regression); `{"mode":"sim"}` → 200 sim watch (regression).
- `{"mode":"live"}` with no creds → **503**, `detail == "real-data provider unavailable"`, `reason == "provider_unavailable"`; then `GET /tape/{sym}/state` → **404** (proves no engine created — no fabricated snapshot).
- `{"mode":"historical", ...}` with no creds → 503 `provider_unavailable`; `GET …/state` → 404.
- unknown `{"mode":"bogus"}` → **4xx**; no engine created.
- `real_data_available` is **True** when `ALPACA_API_KEY`+`ALPACA_API_SECRET` are monkeypatched present, **False** when absent.
- **Single-module confinement:** `ALPACA_API_KEY` / `ALPACA_API_SECRET` appear in **exactly one** file under `app/` (the alpaca adapter) — assert via a source scan; the engine/API/sim-provider import no vendor SDK.
- **No regression:** the existing backend suite (68 passing) stays green.

**Browser (J-10 + J-14 no-credentials path)**
- Selector offers exactly Live / Historical / Simulated; **Live** reveals symbol search + market-status indicator; **Historical** reveals symbol search + date/time-window picker + replay-speed; **Simulated** reveals the ticker input.
- **Simulated → SIM-BUYER → buyer_control** (re-verify J-01/J-02; no cockpit regression).
- **Live Watch (no creds)** → "real-data provider unavailable" non-cockpit state, **no** cockpit rendered; same for **Historical Watch (no creds)**.
- (Lifecycle) switching source/symbol while watching does not leave the prior watch alive.

## Documented Assumptions
1. **No vendor SDK this iteration.** `is_available()` reads env vars only; `alpaca-py` is NOT installed/imported (keeps iter-1 dependency-free and avoids the install gate). The SDK lands with the real provider (J-11/J-12).
2. **Market-status indicator = static honest "unavailable"** this iteration. `GET /market/clock` is out of scope, so the indicator does not call a clock endpoint and does not fabricate open/closed; it shows "unavailable" until the live slice wires the real clock (J-12). This adds **no** new GET endpoint and does not duplicate `real_data_available` (data-contract additions: None).
3. **With-credentials real watch** (creds present) is **deferred** (J-11/J-12). To honor *no fabricated data*, that branch returns an explicit non-cockpit error rather than a cockpit; exact code is at developer discretion (e.g. 503 with a distinct reason) but MUST NOT synthesize a snapshot. Verification runs credentials-absent, so the canonical tested path is the no-creds 503 `provider_unavailable`.
4. **`.env.example` secret values are empty** (`ALPACA_API_KEY=`, `ALPACA_API_SECRET=`). `ALPACA_FEED` may show its non-secret default `iex` with a comment. No key value is ever committed.
5. **Symbol search is free-text only** (vendor-backed suggestions = J-13); the date/time-window + replay-speed controls render and feed the (rejected) historical watch body but drive no real fetch this iteration.

## Scope / Anti-goal Guardrails (this is a security- & architecture-critical iteration)
- **No fabricated data:** real-mode-with-no-creds MUST surface the explicit 503 / non-cockpit state — never a cockpit, never a sim fall-back, never a synthesized snapshot (404 on the post-rejection read proves no engine).
- **No secrets in source:** credentials come only from the environment; `.env.example` holds names with empty values; never committed.
- **Provider-agnostic engine:** the engine, `Config`, providers `base.py`/`simulated.py`, and the canonical reads/WS are untouched; vendor specifics live in the single alpaca adapter module.
- **Single source of truth:** Simulated keeps reading the same one engine snapshot; `real_data_available` is the single availability source and is not recomputed in the UI.
- **No execution path / stay in scope:** no broker/order/scanner/news/charting/portfolio surfaces — selector + honest-failure shell only.
- **Blueprint conformance:** all surfaces stay under the existing `/` home; this instantiates the already-named vendor-agnostic adapter and implements Data Contract rows 6 + 9 — **no blueprint edit / re-approval required**.
- **Out of scope (exclude):** the real live stream, historical fetch+replay, `GET /symbols/search`, `GET /market/clock`, J-14's other three cases (unknown symbol / empty window / market-closed), and `stream_status="stale"` feed-gap detection (J-15).
```
