# Goal Iteration 1 — Real-data foundation: vendor-agnostic adapter seam, credentials/availability contract, and the data-source selector

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-10, J-14 *(J-14 = the **no-credentials path only** this iteration; its other three cases are out of scope — see below)*
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09
- **Anti-goal reminders (verbatim from `docs/goal.md`; the ones this iteration most directly touches):**
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state and never a cockpit … missing credentials → explicit "unavailable". Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*
  - **No secrets in source.** Real-vendor API keys/tokens MUST come only from environment/config and MUST NOT be committed; with no keys the app runs simulator-only and real modes report an explicit "unavailable" rather than failing opaquely or fabricating data.
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed — live or historical — MUST NOT require engine or API changes. A concrete vendor SDK MUST appear in only one adapter module behind a vendor-neutral seam, so a second vendor is one new adapter; vendor specifics MUST NOT leak into the engine, providers, or API.
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no fundamental analysis, no chart-pattern or indicator charting, no portfolio/position management … MUST NOT be built here. *(critical)*
  - *All other anti-goals in `docs/goal.md` remain in force* (price-impact-over-aggression, honest uncertainty, no magic numbers, deterministic & reproducible, no ML in v1, no trade/profit claims).

## GOAL

A user can choose a data source — **Live / Historical / Simulated** — and see the controls each mode needs; choosing a **real** mode with **no credentials configured** yields an explicit, honest **"real-data provider unavailable"** instead of any fabricated read, while **Simulated** keeps working exactly as before.

## BACKGROUND

This is the first real-data slice, and the iter-0 evaluator recommended starting here at **full** depth: it establishes the **security- and architecture-critical foundation** — credential handling (*no secrets in source*), the single vendor-SDK **adapter seam** (*provider-agnostic engine*), and a new honest-failure state (*no fabricated data*) — before any vendor wiring. The **no-credentials path of J-14** is browser- and REST-verifiable **without** a live feed, market hours, or any key, so it is the safest first proof of the seam. The **data-source selector (J-10)** is bundled in because it is the UI entry point that makes the real-mode behavior reachable in the browser (you cannot browser-verify "provider unavailable" without a way to pick a real mode), and once the selector exists J-10 is satisfied for free. Everything lands under the already-approved blueprint home `/`; no nav-skeleton change.

**Lesson applied (iter-0).** Browser QA found that switching tickers via **Watch** does NOT stop the previous backend watch — only the explicit **Stop** teardown does — so re-submitting leaves orphaned engine instances alive. The lesson names *"the J-10 data-source selector"* explicitly. Wiring the selector + Watch now is exactly when a new Watch (or a source/symbol switch) must implicitly tear down the prior watch and close its socket, so the live provider (J-12) never leaks a vendor socket on a symbol switch. This is why watch-lifecycle hardening is in scope this iteration.

## IN SCOPE

### Backend
- [ ] **Vendor-agnostic adapter seam.** Add a vendor-neutral market-data adapter interface (suggested: `apps/backend/app/providers/adapters/base.py`) and **exactly one** concrete adapter `AlpacaAdapter` (suggested: `apps/backend/app/providers/adapters/alpaca.py`, free IEX feed by default). **This iteration the adapter implements only credential detection + `is_available()`** (are Alpaca key/secret present in the environment?). Any concrete vendor SDK, if imported at all, is confined to this one module; the engine, API, and existing providers import **none** of it.
- [ ] **Credentials / availability contract.** Read `ALPACA_API_KEY` / `ALPACA_API_SECRET` (and optional `ALPACA_FEED`, default `iex`) from **environment only** — never from committed source, and **not** inside the frozen engine `Config` (that dataclass is for engine thresholds; credentials are secrets, not tunable numbers). Derive one `real_data_available` boolean from credential presence — the single canonical source for the row-9 availability state. Add `apps/backend/.env.example` documenting the variable **names** with **empty** values (the only env file that may be committed).
- [ ] **Optional `{mode, start, end, speed}` watch body.** `POST /watch/{ticker}` accepts an **optional** JSON body with `mode ∈ {sim, live, historical}`. **Backward compatible:** no body / `{}` / absent `mode` / `mode == "sim"` → the existing simulated path, unchanged (existing tests post `/watch/{ticker}` with no body and MUST stay green). An unrecognized `mode` value → an explicit `4xx` (422/400) — never a silent default into a real feed.
- [ ] **No-credentials gate (the no-credentials path of J-14).** A `live` or `historical` watch when `real_data_available` is `False` → an explicit, distinct error: **HTTP 503** with `detail: "real-data provider unavailable"` plus a machine-readable reason (e.g. `reason: "provider_unavailable"`). **No engine instance is created**; no snapshot, trade, quote, price, or tape state is synthesized; there is **no** fall-back to the simulator.
- [ ] **Backend tests** (assert exact values): no-body & `mode:"sim"` still watch the sim engine (regression); `mode:"live"`/`mode:"historical"` with no creds → 503 `provider_unavailable` **and** a subsequent `GET /tape/{ticker}/state` → 404 (proves no engine was created — no fabricated snapshot); unknown `mode` → 4xx; `real_data_available` reflects env presence and absence (monkeypatch both ways); the vendor adapter / credential read lives in exactly one module.

### Frontend
- [ ] **Data-source selector** in the TopBar offering **exactly three** modes — **Live / Historical / Simulated**. Default = **Simulated** (preserves the current default flow).
- [ ] **Mode-specific control reveal** (the cockpit body itself stays identical):
  - **Simulated** → the existing ticker input + **Watch**.
  - **Live** → a **symbol search box** (free-text input this iteration; vendor-backed suggestions are J-13) + a **market-status indicator** + **Watch**.
  - **Historical** → a **symbol search box** + a **date + time-window picker** + a **replay-speed** control + **Watch**.
- [ ] **Honest non-cockpit state (no-credentials path of J-14).** When a Live/Historical **Watch** returns provider-unavailable, render an explicit **"real-data provider unavailable"** panel **in place of** the cockpit — never a fabricated cockpit, never a silent fall-back to Simulated.
- [ ] **Market-status indicator (Live).** Renders; with no creds it reads an honest **"unavailable"** (the real open/closed via `GET /market/clock` is deferred to the live slice). It MUST NOT fabricate an open/closed status.
- [ ] **Watch-lifecycle hardening (iter-0 lesson).** A new **Watch**, or switching the **data source / symbol**, FIRST tears down the prior watch (`DELETE /watch/{prevTicker}`) and closes its WebSocket before starting the new one — no orphaned backend watches/sockets. (Backend `DELETE /watch` already exists; this is a frontend lifecycle fix.)
- [ ] **Simulated mode unchanged end-to-end:** SIM-BUYER → buyer_control exactly as J-01/J-02.

### New user-facing capability
The user can pick a data source and see the controls appropriate to each mode; choosing a real mode with no credentials produces an explicit, honest "real-data provider unavailable" rather than any fabricated read; Simulated continues to work exactly as before.

### New information displayed
The data-source selector and its per-mode controls; the Live market-status indicator (honest "unavailable" with no creds); the "real-data provider unavailable" non-cockpit state.

### New user actions
Pick a data source; (Live/Historical) type a symbol into the search box; (Historical) choose a date/time window + replay speed; Watch in a real mode.

### UI surface changes
The TopBar gains the selector + mode-specific controls; the `/` cockpit area gains the in-place "provider unavailable" non-cockpit state. Still **exactly one screen**.

### Product surface delta
The cockpit gains its mode-selection shell, and the app now honestly distinguishes "no real-data credentials" from a working read — laying the live + historical foundation **without touching the engine or the canonical REST/WS reads**.

### Blueprint conformance
All surfaces live under the **existing** IA home **`/`** — the TopBar **data-source selector + mode-specific controls** and the **in-place honest non-cockpit states** are already specified in the approved Information Architecture (the blueprint app-shell + the `/` route). This iteration **instantiates** the blueprint's already-named **vendor-agnostic adapter** owner and implements **Data Contract row 6** (watched-source/mode descriptor) and **row 9** (real-data availability/failure — the no-credentials "provider unavailable" case). **No new displayed value, no nav-skeleton change → no blueprint edit and no re-approval required.**

### Data-contract additions
**None.** iter-1 implements existing rows 6 + 9 and creates the already-named vendor-agnostic adapter module (the canonical owner for rows 7–9). It introduces **no second computation or endpoint** for any existing value — Simulated keeps reading the same single engine snapshot (single source of truth preserved). `real_data_available` is the one canonical source for the availability state (row 9); it is not duplicated in the UI.

## OUT OF SCOPE

- The **actual** live stream, historical fetch+replay, vendor symbol search (`GET /symbols/search`), and market clock (`GET /market/clock`) — **J-11 / J-12 / J-13**. The Historical/Live controls **appear** (J-10) but their real-data wiring is deferred.
- The live/historical watch **with credentials present** (real serving) — deferred to J-11/J-12. iter-1 is verified **credentials-absent**; the with-credentials real-watch branch MUST NOT fabricate a cockpit — until the real providers land it surfaces an explicit non-cockpit state rather than synthesized data.
- **J-14's other three cases** — unknown/untradable symbol, empty historical window, market-closed (with next open). They require live vendor calls and land with J-13/J-11/J-12.
- `stream_status = "stale"` / feed-gap detection and the stale-gap timeout config — **J-15**. (`stream_status` already exists on the snapshot; do not extend it here.)
- Any change to the engine, classifier, feature windows, or the canonical `/state` `/features` `/summary` `/events` `WS /stream` reads (provider-agnostic anti-goal — the real-data half must not require engine/API changes).

## DEFINITION OF DONE

- [ ] **J-10 passes** via browser-qa-agent: the selector offers exactly Live/Historical/Simulated; **Live** reveals a symbol search + market-status indicator; **Historical** reveals a symbol search + date/time-window picker + replay-speed; **Simulated** reveals the ticker input; choosing **Simulated** and watching **SIM-BUYER** still resolves to **buyer_control**.
- [ ] **J-14 no-credentials path passes:** with no creds, a Live or Historical **Watch** shows the explicit "real-data provider unavailable" non-cockpit state in the browser **and** `POST /watch/{ticker}` returns 503 `provider_unavailable` via REST — **no** cockpit, **no** fabricated data, **no** sim fall-back. *(J-14's other three cases are out of scope this iteration.)*
- [ ] **Required-still-passing journeys J-01–J-09 remain green** (Simulated-mode regression; backend sim watch/stream unchanged).
- [ ] No anti-goal violation introduced (esp. no fabricated data, no secrets in source, provider-agnostic seam, single source of truth).
- [ ] Unit/integration tests pass; no regressions (the existing backend suite stays green).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-1-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** **J-10** (selector present with exactly three modes; per-mode control reveal; **Simulated → SIM-BUYER → buyer_control** no-regression) and the **J-14 no-credentials path** (Live/Historical **Watch** → "real-data provider unavailable" non-cockpit state, **no** cockpit rendered). Re-verify at least **J-01/J-02** through **Simulated** mode to confirm no regression of the cockpit.
- **Unit/integration:** watch-body routing (no-body/`sim` regression; `live`/`historical` with no creds → 503 `provider_unavailable`; unknown `mode` → 4xx); `real_data_available` derived from env presence/absence (monkeypatched both ways); credential read + vendor adapter confined to exactly one module; `GET /tape/{ticker}/state` → 404 after a rejected real-mode watch (no engine created).
- **Error cases:** live/historical with no creds → explicit provider-unavailable (**not** 500, **not** a cockpit); unknown `mode` → explicit 4xx; confirm **no** secret is read from anywhere but the environment and **no** key value is committed (`.env.example` holds names only, empty values).

## NOTES

- **Why `full` depth:** per the iter-0 evaluator — this first real-data slice establishes security- and architecture-critical surfaces (credential handling = *no secrets in source*; the single vendor-SDK adapter seam = *provider-agnostic engine*; the new honest-failure state = *no fabricated data*) plus the first new UI control that must not regress the sim cockpit. The full pipeline's audit + ux-regression + closure gate is worth running to lock the seam in correctly; later, well-bounded real-data slices can drop back to lean. Prior verdict was CONTINUE (not ESCALATE), so full is by recommendation, not mandate.
- **iter-0 lesson (orphaned watch on switch) applies directly here** — it names the J-10 selector. Make a new Watch / source-or-symbol switch implicitly `DELETE` the prior watch and close its socket, so the live provider (J-12) never leaks a vendor socket on a symbol switch.
- **J-14 is intentionally partial** this iteration (no-credentials path only). The remaining three cases (unknown symbol, empty window, market closed) require live vendor calls and land with J-13/J-11/J-12. The evaluator should expect J-10 to flip green and J-14's no-credentials sub-path to be demonstrated (J-14 overall stays `failing` until its four cases are complete).
- **Verification runs with NO credentials configured** (per `docs/goal.md`, the no-credentials path is verifiable without a live feed). Do **not** stub a fake live/historical cockpit to make a credentialed path look green.
- **Provider-agnostic guard:** the engine and the canonical reads (`/state`, `/features`, `/summary`, `/events`, `WS /stream`) must be **untouched** — real data flows through the same engine via a new provider behind the seam in later iterations; iter-1 only adds the seam + the credentials gate + the mode-selection shell.
