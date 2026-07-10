# Goal Iteration 4 — Real S/R levels & A/B/C confluence zones on real Yahoo bars (J-04)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** yahoo_fetch
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-02, J-03, J-06
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No new levels/PnL/strategy/champion computation.** This era feeds real bars to the existing era-4 owners and adds no second computation of levels, zones, PnL, aggregates, strategies, or the champion; the only new backend computation is the Yahoo fetch + `4h` resample confined to `adapters/yahoo.py` and the derived lookup index. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Yahoo data is fetched-and-stored only, never re-tagged or pooled across feeds.** A `feed="yahoo"` series is append-only and checksummed; it is never merged with, re-tagged to, or analytically pooled with `sip` or any other feed. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **No fabricated bars, ever.** A symbol/window/timeframe Yahoo cannot serve (out of retention, unsupported interval, network failure) returns an explicit neutral error; the fetch never synthesizes, forward-fills across gaps, or pads a partial window to force a green journey. *(critical)*

## GOAL

Prove that the existing, frozen era-4 structure module computes **real, non-empty support/resistance levels and A/B/C confluence zones from real Yahoo bars** — `GET /research/levels?symbol=<S>&as_of=<T>` (and the MCP `levels` proxy) populate from stored `feed="yahoo"` data where the keyless surface was previously empty, with no second computation path.

## BACKGROUND

J-01–J-03 already fetch, store (canonical JSON `BarStore`), and store-first-index real Yahoo bars. The era-4 levels module (`research/levels.py`) is **vendor-neutral by construction**: `compute_levels(store, symbol, as_of_epoch, config)` reads a symbol's stored series through the shared `BarStore` (`store.list()` filtered by `symbol`), touching no vendor field — and `GET /research/levels` + the MCP `levels` tool already serve it. So the levels/zone values simply populate once Yahoo bars exist for a symbol; this iteration is a **verify-and-lock** journey, not a build: no production source change to `levels.py` (frozen byte-identical), its route, or the MCP layer is expected — the deliverable is a committed real-Yahoo fixture plus tests that prove real levels+zones on it, that REST and MCP agree byte-for-byte, that no lookahead leaks, and (the defining acceptance) that **no second levels/zone computation path** was introduced.

**Target selection (priority rubric):** no journey regressed (rule 1 n/a); iter-3 `coherence.md` was `COHERENCE-PASS` so no consolidation is owed (rule 2 n/a); J-04 is the natural next unblocker (rule 3) — it makes real levels+zones available for J-05's `/structure` fetch control to render, and it is the smaller of the two remaining failing journeys (rule 4), a single non-risky backend verification (rule 5). This matches the iter-3 evaluator's explicit next-step recommendation.

**Depth = full**, justified by three "Picking depth" triggers: (a) the iter-3 evaluator explicitly recommended full depth for J-04; (b) J-04's **defining acceptance is coherence-critical** — "no second levels/zone computation path exists (single source of truth — the coherence-auditor stays clean)" — which is only verified by the coherence + audit lanes that run in the full pipeline; (c) it requires new backend tests beyond browser smoke (levels-on-Yahoo, REST==MCP byte-for-byte, no-lookahead). (Prior verdict was CONTINUE, not ESCALATE, so full is chosen on these triggers, not mandated.)

**Lessons applied (from `lessons.md`):**
- **iter-1:** a committed `feed="yahoo"` fixture must NOT live under `apps/backend/tests/fixtures/bars/` — the frozen `test_bars.py::test_committed_fixture_loads_through_the_real_store_path_keyless` blanket-asserts `feed=="sip"` over that whole dir. The existing zone-fixture test (`test_levels_api.py::test_get_levels_confluence_zones_exact_values_on_the_committed_pg_fixture`) copies from `FIXTURE_BAR_DIR` (`tests/fixtures/bars/`); the J-04 Yahoo-zone test must mirror that pattern but source its fixture from **`tests/fixtures/yahoo/`** instead.
- **iter-3:** an exact-repeat `POST /research/bars` of the same `(symbol,timeframe,window)` now returns **200 store-first** (zero adapter calls), NOT 409 — if a J-04 test seeds bars via the POST path, a re-seed of the same window is a 200 store-first hit, not a 409. (Seeding fixtures directly into the temp bar dir, as the PG-zone test does, sidesteps this.)

## IN SCOPE

### Backend
- [ ] **Committed real-Yahoo fixture(s)** under `apps/backend/tests/fixtures/yahoo/` (real OHLCV, `feed="yahoo"`) that demonstrably yield, through `compute_levels` / `GET /research/levels`, **non-empty `levels` AND at least one `confluence_zones` entry** carrying an A/B/C `class`. The existing `AAPL_1d_20260601_20260604.json` + `AAPL_1h_20260601_20260603.json` mirror the PG fixture's 1h+1d cross-timeframe shape; verify they cluster into ≥1 qualifying (≥2-member) zone at a chosen `as_of`, and if not, commit a richer real-Yahoo window (still real bars — never synthesized) that does.
- [ ] **New tests** (hermetic, no network in the default suite):
  - Levels-on-Yahoo: seed the committed Yahoo fixture(s) into a temp store, `GET /research/levels?symbol=<S>&as_of=<T>` → `no_bar_series_for_symbol: false`, non-empty `levels`, ≥1 `confluence_zones` with an A/B/C `class` — mirroring the PG-zone test but sourced from `tests/fixtures/yahoo/`.
  - REST==MCP byte-for-byte: the MCP `levels` proxy and `GET /research/levels` return byte-identical JSON for the Yahoo-backed symbol at the same `symbol`/`as_of`.
  - No-lookahead on Yahoo bars: a level computed at `as_of` T is unchanged by a stored Yahoo bar timestamped after T (as-of truncation holds on the real Yahoo series).
- [ ] **Coherence-lock:** confirm `compute_levels` / `compute_confluence_zones` remain the **single owner** in `research/levels.py`, both the REST route and the MCP tool call it, and no second levels/zone derivation was added anywhere (route, adapter, frontend, or a helper).
- [ ] (Optional, integration-gated) an `integration`-marked live check under `TAPEOLOGY_LIVE_INTEGRATION=1`: fetch a real Yahoo window for a symbol, then `GET /research/levels` returns real non-empty levels+zones live.

**No production source change is expected to `research/levels.py`, `apps/backend/app/research/routes.py`'s `get_levels`, or `apps/backend/app/mcp/__init__.py` — they already serve this correctly. If the developer finds a change is genuinely required, it MUST be additive and MUST NOT alter `levels.py` (frozen byte-identical) or the levels/zone computation.**

### Frontend
- None. J-04 is backend/API-verifiable (keyless on the committed fixture). The `/structure` fetch control and provenance badge are **J-05** (next iteration).

### New user-facing capability
API/MCP capability only: `GET /research/levels` and the MCP `levels` tool now return real, non-empty S/R levels + A/B/C confluence zones for any symbol that has stored Yahoo bars (previously empty on the keyless store). No new UI control this iteration.

### New information displayed
Real S/R levels and A/B/C confluence zones — served from the **existing** `/research/levels` endpoint (and, incidentally, on the existing `/structure` read surface once a symbol has Yahoo bars). No new value type: both values are already registered owners in the Data Contract.

### New user actions
None. (The explicit "Fetch from Yahoo Finance" write action is J-05.)

### UI surface changes
None this iteration.

### Product surface delta
The previously-empty keyless structure/levels surface can now show **real** support/resistance structure computed on **real** Yahoo data through the existing read endpoints — satisfying J-04's "the previously-empty keyless structure surface now populates from real data."

### Blueprint conformance
`/structure` (Levels & Zones section — existing), already the registered canonical home for J-04 in the Information Architecture (`blueprint.md`). No new page, no new route, no nav-skeleton change → no blueprint edit and no re-approval required.

### Data-contract additions
**None.** J-04 introduces no new displayed value. "S/R levels (price / timeframe / type)" and "A/B/C confluence-zone class + score" are already registered in the Data Contract — both owned solely by `research/levels.py`, served by `GET /research/levels` (+ MCP `levels`). This iteration makes those existing (currently-empty) values populate from real data via their existing owner; it introduces no second computation and no second endpoint. `blueprint.md` is already current and is NOT edited.

## OUT OF SCOPE

- Any modification to `research/levels.py`, `research/backtests.py`, `research/strategies.py`, `config.py` (fingerprint `4d665603569b9dbf`), the tape engine, the JSON `BarStore`, or the Alpaca adapter — all stay byte-identical (frozen foundation).
- The `/structure` fetch control, the "Yahoo Finance" provenance badge, the `taxonomy.FEED_BASIS_LABELS` `"yahoo"` label, and **any** frontend change — that is **J-05**.
- A feed-scoped `?feed=` filter or feed-segregated levels computation. The mixed-feed pooling edge (a symbol holding both a Yahoo and an Alpaca series for overlapping timeframes) cannot be closed without touching frozen `levels.py`; it is not in J-04's acceptance and is deferred (see NOTES / assumption ledger).
- Champion promotion, PnL, strategies, backtests, datasets UI, tick-tape backfill — untouched.
- Audit carry-forwards **B2** (normalize a blank `?symbol=`/`?timeframe=` to `None`) and **B3** (auto-index legacy series) — these are **J-05** pre-work, not J-04.

## DEFINITION OF DONE

- [ ] A committed real-Yahoo fixture under `apps/backend/tests/fixtures/yahoo/` (never `tests/fixtures/bars/`) yields, via `GET /research/levels?symbol=<S>&as_of=<T>`, `no_bar_series_for_symbol: false`, a non-empty `levels` list, and ≥1 `confluence_zones` entry with an A/B/C `class` — asserted by a committed test.
- [ ] REST `GET /research/levels` and the MCP `levels` proxy return byte-for-byte identical JSON for the Yahoo-backed symbol at the same `symbol`/`as_of` — asserted by a committed test.
- [ ] No-lookahead holds on the Yahoo data: a stored Yahoo bar timestamped after `as_of` does not change the levels computed at `as_of` — asserted by a committed test.
- [ ] `research/levels.py` is byte-identical to its pre-iteration state; `compute_levels`/`compute_confluence_zones` remain single-owner (no second levels/zone computation path anywhere) — coherence-auditor returns `COHERENCE-PASS`.
- [ ] Target journey J-04 passes (backend/API-verifiable, keyless on the committed fixture).
- [ ] Required-still-passing J-01, J-02, J-03, J-06 remain green: full backend suite passes; `config_fingerprint` stays `4d665603569b9dbf`; engine equivalence 22/22; the JSON `BarStore` and the Alpaca adapter + its credentialed path stay byte-identical.
- [ ] No anti-goal violation introduced (scan-report CLEAN; no fabricated bars; no pooling across feeds in the tested path).
- [ ] Dev handoff written at `docs/handoffs/goal-yahoo_fetch-iter-4-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none load-bearing this iteration — J-04's acceptance is keyless/backend-verifiable on the committed fixture (`Frontend Present: no`). The browser lane may run for a J-06 smoke check but is not required for J-04's status. (The first genuinely browser-verified journey is **J-05**.)
- **Unit/integration:** the three new committed tests above (levels-on-Yahoo populating; REST==MCP byte-for-byte; no-lookahead on Yahoo bars). Optionally an `integration`-marked (`TAPEOLOGY_LIVE_INTEGRATION=1`) live end-to-end check. Reuse the existing `ctx`/temp-bar-dir + `TestClient` harness; source the Yahoo fixture from `tests/fixtures/yahoo/`.
- **Error cases:** confirm the existing honest states still hold on the Yahoo path — `no_bar_series_for_symbol: true` for a symbol with no stored series; an `as_of` before the symbol's first Yahoo bar returns an honest "no levels found" (empty `levels`, flag `false`), not the no-series state; malformed/blank `symbol`/`as_of` stay 422.

## NOTES

- **Feed-segregation interpretation (logged to the assumption ledger, iter-4):** the "never pooled across feeds" rail is satisfied for J-04 by scoping to the keyless single-feed path (the committed Yahoo fixture and default keyless flow give a symbol only `feed="yahoo"` series, which `compute_levels` reads exactly). A genuine mixed-feed guard would require touching frozen `levels.py` and is out of scope; reversible if the owner later wants feed-scoped levels.
- **Forward-flags for J-05 (do NOT act on them this iteration):** the orchestrator must finally provision reachable frontend `:3301` / backend `:8301` **and** Chrome MCP before the J-05 pipeline run — the browser lane silently no-op'd in iters 0/2/3 (services unreachable), and J-05 is the first journey with genuinely new `/structure` UI, so it cannot be evidenced without a real render (iter-0/iter-2 lessons). Also carry the iter-3 evaluator's J-05 pre-work into that iteration: close audit **B2** (blank `?symbol=`/`?timeframe=` → `None`) and ensure any pre-seeded J-05 fixture is **indexed** (recorded via the store-first POST path or a one-off `reindex()`) so the store-first "instant serve" triggers (audit **B3**).
- **Reference pattern:** `apps/backend/tests/test_levels_api.py::test_get_levels_confluence_zones_exact_values_on_the_committed_pg_fixture` proves zones end-to-end on the committed PG (`feed="sip"`) fixture pair (6 zones; classes C×5 + B; one cross-timeframe 1h+1d zone). Mirror it for the Yahoo fixture, sourcing from `tests/fixtures/yahoo/` and asserting real non-empty output (exact values may differ from PG — the acceptance is non-empty levels + ≥1 A/B/C zone, not specific prices).
