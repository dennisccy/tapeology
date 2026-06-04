# Goal Iteration 2 — Wire the first real provider: historical replay + symbol search

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-11, J-13
- **Also advances (not a hard pass target this iter):** J-14 (its unknown-symbol + empty-window cases; the market-closed case stays with J-12)
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No fabricated data.** "The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state and never a cockpit … Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*"
  - **Provider-agnostic engine.** "The engine and API MUST depend only on the provider interface … A concrete vendor SDK MUST appear in only one adapter module behind a vendor-neutral seam, so a second vendor is one new adapter; vendor specifics MUST NOT leak into the engine, providers, or API."
  - **Single source of truth.** "Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*"
  - **No secrets in source.** "Real-vendor API keys/tokens MUST come only from environment/config and MUST NOT be committed; with no keys the app runs simulator-only and real modes report an explicit 'unavailable' rather than failing opaquely or fabricating data."
  - **Deterministic & reproducible.** "Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness."
  - **No execution path / Stay in scope.** "Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API." No scanner/news/charting/portfolio surfaces.
  - **No magic numbers.** "Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code."

## GOAL

Watching a real US symbol in **Historical** mode fetches that symbol's **real** trades + quotes for a chosen past window from Alpaca and replays them through the **same** engine, populating the full cockpit (J-11); a **symbol search** returns real tradable matches to fill the watch box (J-13) — with every real-data failure surfacing an explicit, distinct non-cockpit state and never a fabricated tape.

## BACKGROUND

iter-1 landed the data-source selector (J-10) and the no-credentials honest-unavailable state (J-14, 1 of 4). The evaluator's recommendation for iter-2 is the **safest first real-provider slice: J-11 historical replay** (reproducible, no live-market-hours dependency) **bundled with J-13 `GET /symbols/search`** (they share the adapter, credential, and dependency plumbing). This is the first real third-party dependency (`alpaca-py`), the first real network I/O, and the first real-timestamp → logical-timeline mapping — security- and architecture-critical, must not regress J-01–J-10 — hence **full** depth.

Two prior lessons govern this iteration and MUST be heeded:

- **iter-1 — credential-name trap (blocks the creds-present path).** The untracked operator `apps/backend/.env` carries Alpaca paper credentials, but under the variable name `ALPACA_SECRET_KEY`, while the adapter (`app/providers/adapters/alpaca.py`) reads `ALPACA_API_SECRET` — and nothing loads `.env` at all (no loader; `start-backend.sh` does not source it). Until the env names are aligned to the adapter's (`ALPACA_API_KEY` / `ALPACA_API_SECRET`) **and** a loader/export is added, `real_data_available()` returns `False` with valid keys present, so the historical branch can never run. Fix this first. **Never commit `.env`** (it is gitignored — keep it that way; `.env.example` carries names with empty values only).
- **iter-0 — orphaned-watch-on-switch.** A new Watch (or source/symbol switch) must implicitly tear down the prior watch and cancel its feeder. The frontend already does this (`page.tsx teardownActiveWatch`); ensure the new historical feeder task is cancellable and `WatchManager.stop` cancels it (no leaked replay task on switch/stop).

The iter-1 coherence audit (COHERENCE-PASS) left two forward-notes: (1) the Live market-status pill is a static literal until J-12 wires `GET /market/clock` — **out of scope here**; (2) the creds-present "not yet serving" 503 (`provider_not_implemented`) has no dedicated honest non-cockpit UI — **this iteration replaces that branch for historical mode with the real provider and gives the new historical failure modes their own distinct honest states.**

## IN SCOPE

### Backend

- [ ] **Align credentials + add a `.env` loader.** Correct the operator `.env` variable name to the adapter's canonical `ALPACA_API_SECRET` (do **not** rename the adapter; the adapter names are the contract). Add a minimal loader so both `pytest` and the uvicorn process (`start-backend.sh`) see env from `apps/backend/.env` — prefer a tiny stdlib loader or an explicit `set -a; source .env` in `start-backend.sh` over adding a dependency. Confirm `.env` stays untracked.
- [ ] **Add `alpaca-py` through the supply-chain gate.** Run `./scripts/automation/check-install.sh "pip install alpaca-py"` first; only on a pass add a **pinned** `alpaca-py==<version>` to `apps/backend/requirements.txt` and install into `apps/backend/.venv`.
- [ ] **Extend the Alpaca adapter (the ONE vendor module).** Add to `app/providers/adapters/alpaca.py` (and nowhere else): `fetch_historical(symbol, start, end) -> list[raw trade/quote records]` and `search_symbols(query) -> list[{symbol, name}]`, using `alpaca-py`. This is the **only** module that may import the Alpaca SDK or name Alpaca. Keep `is_available()` / `real_data_available()` as the single availability source.
- [ ] **`HistoricalProvider` implementing the `Provider` interface** (new module under `app/providers/`). Given `(ticker, start, end, speed)` it asks the adapter for the real window, then yields an ordered `TradeEvent`/`QuoteEvent` stream. Trades are yielded as `Side.UNKNOWN` — the engine's aggressor classifier re-derives side from the interleaved quotes (preserve **quote-before-trade** at the same instant). Map real vendor timestamps → the engine's **logical** seconds (monotonic non-decreasing offsets from window start); no wall-clock in the events.
- [ ] **WatchManager: real-provider lifecycle.** Let a watch be started with the `HistoricalProvider` (e.g. a `watch_with_provider` path) without touching the sim registry. The replay feeder paces delivery by inter-event logical gaps **divided by the selected `speed`**, bounded by a config cap so a large gap never stalls the cockpit. The feeder task must be cancellable and torn down by `stop()` and by a switch (iter-0 lesson). Engine math stays purely logical/deterministic; wall-clock only paces delivery.
- [ ] **`main.py` historical branch.** When `mode == "historical"` and `real_data_available()` is true: validate params (`start` < `end`, parseable; `speed` within the allowed bounded set) → **422** on invalid (no engine); build the `HistoricalProvider` and watch. Replace the historical use of the `provider_not_implemented` stub. Real-data failures each raise an explicit, distinct error with **no engine created**: missing creds → `503 provider_unavailable` (unchanged); unknown/untradable symbol → `4xx` `symbol_not_tradable` ("not a tradable symbol"); empty window → `4xx` `no_data_for_window` ("no data for that window"). (Live mode keeps its current behavior — out of scope.)
- [ ] **`GET /symbols/search?q=`** (Data Contract row 7) — returns `[{symbol, name}, …]` real tradable matches via the adapter; empty/short query → empty list (not an error). Free-text watch entry remains possible regardless.
- [ ] **Config additions (no magic numbers).** Any new tunable — allowed replay-speed set/default, the replay inter-event pacing cap, the symbol-search result limit — lives in `app/config.py`, never inline.

### Frontend

- [ ] **Populate the cockpit on a successful historical watch.** A successful `POST /watch` (historical) drives the existing `Cockpit` exactly as sim does — no new cockpit, no mode-specific panels. The watched-source label reads `historical <SYM> <window>` from the canonical snapshot (row 6).
- [ ] **Symbol search box (J-13).** In Live/Historical mode the symbol input offers suggestions from `GET /symbols/search?q=` (symbol + name); selecting one fills the symbol. Free-text entry still works. Debounce the lookup; no business logic — render adapter results verbatim.
- [ ] **Distinct honest non-cockpit states (J-14).** `lib/api.ts` must carry the distinct `reason` (not only `provider_unavailable`); `page.tsx` renders a distinct panel per reason: provider unavailable (creds) / **not a tradable symbol** / **no data for that window**. Generalize `ProviderUnavailable` (or add sibling panels) — amber, in place of the cockpit, never alongside fabricated panels.

### New user-facing capability

Watch a **real** US symbol over a chosen **past date/time window** and see its real tape replayed through the engine at a selectable speed; find a symbol by typing a partial name/symbol; see an explicit, honest message (not a cockpit) when a real symbol is untradable or a window has no data.

### New information displayed

Real bid/ask/spread/last, real recent trades, real feature readouts, a real tape state + confidence, observations and event log for a replayed historical window (all the **existing** cockpit values — now fed by real data); live symbol-search suggestions; the `historical <SYM> <window>` source label; the "not a tradable symbol" and "no data for that window" honest states.

### New user actions

Type a partial symbol → pick a suggestion; pick a past date + time window + replay speed → Watch (these controls already render from J-10; this iteration makes them fetch real data).

### UI surface changes

No new page or route. The cockpit, the TopBar controls, and the honest non-cockpit area on `/` are reused; the symbol input gains a suggestions dropdown and the non-cockpit area gains two new distinct messages.

### Product surface delta

Tapeology becomes a real tape reader for the first time: the identical cockpit now renders real historical order flow, proving the provider seam (sim ⇄ real changes neither engine nor API), while staying honest when real data is missing.

### Blueprint conformance

All surfaces remain on **`/` (Watch — HOME)** within the existing persistent app shell — no new route, still exactly one screen. This iteration **implements already-registered Data Contract rows**: **row 7** (symbol search → `GET /symbols/search?q=`) and **row 9** (real-data failure states → explicit error from `POST /watch`), and **feeds the existing rows 1–6** (engine snapshot) from the new `HistoricalProvider` through the **same** engine — real data adds **no parallel state/feature path**. No new displayed value and no nav-skeleton change are introduced, so **no `blueprint.md` edit and no re-approval are required** this iteration.

### Data-contract additions

**None.** Rows 7 and 9 are already in the contract (created in iter-1 as the vendor-agnostic adapter's responsibilities); rows 1–6 are unchanged and must not be recomputed. Do not introduce a second computation or a second endpoint for any existing value — the historical path reads/feeds the canonical engine snapshot and serves failures via the row-9 `POST /watch` error.

## OUT OF SCOPE

- **J-12 live streaming** (real-time socket). Its controls + static market-status pill already render; do not wire the live socket, and do **not** add `GET /market/clock` (Data Contract row 8) — both belong to J-12.
- **J-15** stale-gap → recover.
- **J-14 market-closed case** (needs Live mode → J-12).
- Level-2 book events; persistence; the predictive/backtest harness; any extended tape states.
- Any change to the engine, classifier, config thresholds, serializers, `providers/base.py`, or `providers/simulated.py` beyond what the provider seam strictly requires — the sim path (J-01–J-10) must stay behavior-identical.

## DEFINITION OF DONE

- [ ] **J-11 — deterministic real-fixture replay (required, in-loop):** a committed **real** captured Alpaca fixture (see NOTES — captured via a committed operator script using real creds; never synthesized) replayed through `HistoricalProvider` + `TapeEngine` populates **every** cockpit value (bid/ask/spread/last, recent trades with price/size/side, the feature readouts, a tape state + confidence, observations, event log); a second identical run yields **identical** state/confidence/features (reproducible + deterministic).
- [ ] **J-11 — live confirmation (operator creds wired):** a real Historical watch of a fixed past window populates the cockpit in the browser with real values and REST agrees with the UI (single source of truth). If the QA environment cannot reach the vendor, this is recorded as a gated/operator confirmation and the in-loop J-11 evidence rests on the deterministic real-fixture test above plus the historical controls + honest states rendering.
- [ ] **J-13:** `GET /symbols/search?q=` returns real matching tradable symbols (symbol + name); selecting one fills the watch box; free-text entry still works.
- [ ] **J-14 advances:** an unknown/untradable historical symbol → "not a tradable symbol" and a no-data window → "no data for that window" each render as a **distinct** honest non-cockpit state with **no engine created** (verified via the API `reason` and a subsequent `/state` 404). (Market-closed remains for J-12.)
- [ ] **Required-still-passing J-01–J-10 remain green** — the sim path is behavior-identical (no-body / `{}` / `mode:"sim"` watches unchanged); selector, stop/re-watch, and SSOT unaffected.
- [ ] **No anti-goal violation introduced:** `alpaca-py`/the Alpaca SDK + the vendor name appear in **exactly one** module (`providers/adapters/alpaca.py`); engine, config, serializers, `providers/base.py`, `providers/simulated.py` reference no vendor; credentials are env-only and `.env` stays untracked; every real-data failure is an explicit distinct state with no fabricated cockpit; historical replay is deterministic; no broker/order/execution code.
- [ ] **Unit + integration tests pass; no regressions** — the existing 84 backend tests stay green and new tests are added (below).
- [ ] **Dev handoff written** at `docs/handoffs/goal-i_will_be_super_rich-iter-2-dev.md`.

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent):**
  - **J-11** — Historical mode → cockpit populates with real values; REST `/state` + `/features` match the UI (SSOT). (Live fetch with operator creds, or the fixture-backed historical watch.)
  - **J-13** — typing a partial symbol shows real suggestions; selecting fills the box.
  - **J-14** — unknown historical symbol → "not a tradable symbol"; no-data window → "no data for that window"; no-creds (regression) → "real-data provider unavailable". Each shows no cockpit.
  - **No regression** — J-10 (selector + per-mode reveal), J-01/J-02 (SIM-BUYER → buyer_control), J-09 (Stop → idle).
- **Unit / integration (pytest):**
  - `HistoricalProvider` timestamp mapping: logical, monotonic non-decreasing, quote-before-trade preserved at the same instant.
  - **Deterministic real-fixture replay:** committed real fixture → populated snapshot; rerun → identical state/confidence/features.
  - Adapter confinement (extend `test_real_data_gate.py`): `alpaca-py` import + the Alpaca name confined to `providers/adapters/alpaca.py`; engine/config/serializers/`providers/base`/`providers/simulated` reference no vendor (the existing guard tests must still pass).
  - WatchManager historical lifecycle: feeder is cancellable; `stop()` and a switch tear it down (no orphaned replay task).
  - `GET /symbols/search` parsing/limit; short/empty query → empty list.
  - Honest-failure reasons are distinct (`provider_unavailable` / `symbol_not_tradable` / `no_data_for_window`) and each creates **no** engine (subsequent `/state` → 404).
- **Error cases (must be rejected, no engine, no fabrication):** missing creds → 503 `provider_unavailable`; unknown symbol → `symbol_not_tradable`; empty window → `no_data_for_window`; invalid params (`end` ≤ `start`, unparseable date/time, out-of-bounds `speed`) → 422; unknown `mode` → 422 (existing).

## NOTES

- **Credentialed verification strategy (decided up front — addresses the evaluator's planning constraint #1).** J-11's "real fetch" cannot be browser-verified with no creds, and J-11 explicitly requires the read be **reproducible for a fixed symbol + window**. Strategy: **a recorded real-vendor fixture (VCR-style) captured from real Alpaca data is the canonical, deterministic, in-loop evidence**, with a **live operator-creds historical fetch** as browser confirmation.
  - Add a committed capture script (e.g. `apps/backend/scripts/capture_alpaca_fixture.py`) that, using the operator's real creds, fetches one fixed symbol + past window and writes a fixture (e.g. `apps/backend/tests/fixtures/alpaca/<sym>_<window>.json`). The fixture is **real captured market data** (committable — it is not a secret and not synthesized), so future iterations re-verify J-11 deterministically and offline.
  - **No-fabrication boundary (critical).** The fixture MUST be real captured data. **Never synthesize or hand-write a fixture to force a green J-11** — that is exactly the *no-fabricated-data* anti-goal. If a real capture is impossible in the environment (invalid/missing creds, no network, no data entitlement), **STOP and escalate** in the dev handoff rather than fabricating; the evaluator will score J-11 on the honest evidence available (controls + honest states + the provider seam) rather than on faked data.
  - Tests inject a fake adapter (constructor/dependency injection) returning the committed real fixture — a standard test seam, **not** a production env-var backdoor in the live code path.
- **Historical data is not market-hours-gated** — a fixed *past* window can be fetched any time creds are present, so the live confirmation does not require the market to be open (unlike J-12 live streaming).
- **Scope guard:** if symbol search (J-13) proves harder than expected, it must degrade gracefully to free-text entry (already working) so it cannot block J-11; flag any slip for the evaluator rather than expanding scope.
- References: evaluator recommendation in `runs/goal-session-i_will_be_super_rich/iter-1/eval.md`; lessons (inlined in the decomposer prompt) for the `.env` name trap and orphaned-watch-on-switch; iter-1 coherence forward-notes in `runs/goal-session-i_will_be_super_rich/iter-1/coherence.md`.
