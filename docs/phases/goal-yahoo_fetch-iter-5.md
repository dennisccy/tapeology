# Goal Iteration 5 — Fetch from the app: the /structure Yahoo fetch control + "Yahoo Finance" provenance

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** yahoo_fetch
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-06
- **Anti-goal reminders** (verbatim from `docs/goal.md`; the immutable rails + the era-5-specific rails this UI iteration must respect):
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **The SQLite index is a derived cache, never a source of truth.** Canonical bars stay the append-only, checksummed JSON `BarStore`; every served candle is checksum-verified from it; the index holds metadata only, is rebuildable via `reindex()`, and its loss or corruption loses and fabricates nothing. A second authoritative bar store is a defect. *(critical)*
  - **Fetching is explicit and store-first.** Historical data is fetched only on an explicit user action; an already-stored window is served from storage without re-hitting Yahoo; there is no ambient or background polling. *(critical)*
  - **Yahoo data is fetched-and-stored only, never re-tagged or pooled across feeds.** A `feed="yahoo"` series is append-only and checksummed; it is never merged with, re-tagged to, or analytically pooled with `sip` or any other feed. *(critical)*
  - **No fabricated bars, ever.** A symbol/window/timeframe Yahoo cannot serve (out of retention, unsupported interval, network failure) returns an explicit neutral error; the fetch never synthesizes, forward-fills across gaps, or pads a partial window to force a green journey. *(critical)*
  - **No new levels/PnL/strategy/champion computation.** This era feeds real bars to the existing era-4 owners and adds no second computation of levels, zones, PnL, aggregates, strategies, or the champion; the only new backend computation is the Yahoo fetch + `4h` resample confined to `adapters/yahoo.py` and the derived lookup index. *(critical)*
  - **The UI fetch stores bars only.** The `/structure` fetch control performs an explicit bar fetch/store; it computes no levels, PnL, or champion, and it never promotes. *(critical)*
  - **Yahoo default must not break the Alpaca path.** Making Yahoo the default bar vendor is additive: the Alpaca adapter, its credential gate, and its bar/tick/live paths stay byte-identical and selectable (opt-in). *(critical)*
  - **No vocabulary drift.** No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.

## GOAL

On `/structure`, a person picks a symbol + timeframe + date range, clicks **Fetch from Yahoo Finance**, and the page renders the real candles + real S/R level lines + A/B/C confluence-zone table read verbatim from `/research/bars` + `/research/levels`, badged with the taxonomy-owned "Yahoo Finance" provenance — closing Era 5's final journey (J-05).

## BACKGROUND

J-05 is the only remaining failing journey and the last one in the era; J-01–J-04 and J-06 all pass and iter-4's coherence was `COHERENCE-PASS`, so this is new feature work, not a consolidation pass. The full backend fetch/store/index/levels stack already exists (`POST /research/bars` store-first, `GET /research/bars?symbol=&timeframe=`, `GET /research/levels?symbol=&as_of=`, frozen `levels.py`); what is missing is the **UI write action** — the `/structure` page today only has a read-only "Load" form and no provenance badge, and `taxonomy.FEED_BASIS_LABELS` has no `"yahoo"` entry. Depth is **full** for three converging triggers (per "Picking depth"): this crosses backend (taxonomy label + a small GET-filter fix) and frontend (the new write control, render flow, provenance badge), it is the **first genuinely browser-verifiable journey** (new `/structure` UI that cannot be evidenced without a real render), and the iter-4 evaluator explicitly recommended `full` — so the ux-regression + audit + coherence + closure lanes must run. Target selection follows the rubric: J-05 is the sole failing journey (no regressed/consolidation work outranks it).

## IN SCOPE

### Backend
- [ ] Add `"yahoo": "Yahoo Finance"` to `apps/backend/app/research/taxonomy.py` `FEED_BASIS_LABELS`. `taxonomy_payload()` already builds `feed_basis.feeds` from this dict, so `GET /research/taxonomy` then serves `{"id": "yahoo", "name": "Yahoo Finance"}` automatically — this is the single owner of the badge label (no new field, no route change). Update any test that pins the exact `FEED_BASIS_LABELS` set / `feed_basis.feeds` list to include the new entry. `config.py` is NOT touched — `config_fingerprint` stays `4d665603569b9dbf` (taxonomy copy is not fingerprinted).
- [ ] **Close audit carry-forward B2** in `GET /research/bars` (`routes.py::list_bar_series`): a blank/whitespace `?symbol=` (or `?timeframe=`) must normalize to `None` **before** the `symbol is None and timeframe is None` short-circuit, so `GET /research/bars?symbol=` (blank, no timeframe) returns **byte-identical** to the no-param `store.list()` call. Today line ~1724 uses `is None` while the normalization at ~1728–1729 uses falsy checks, so a blank `?symbol=` silently routes through `index.list(None, None)` (index-only, missing un-indexed legacy series) instead of the byte-identical path. Fix is additive; the no-param path and the real-filter path stay byte-identical to iter-3.

### Frontend
- [ ] Add a POST `/research/bars` client helper in `apps/frontend/lib/api.ts` (following the existing `createStudy`/`declareThesis` POST precedent; body `{symbol, timeframe, start, end}`, returns the `{bar_series}` result or a `{ok:false,error}`-shaped failure). No POST-bars helper exists today (`fetchBarSeriesList` is GET-only).
- [ ] Add the **fetch control** to `apps/frontend/app/structure/page.tsx` — symbol (reuse `SymbolSearch`), a **timeframe** selector offering the era-5 supported set (`1w 1d 4h 1h 5m 1m`), a **date range** (start/end mapping to the POST `start`/`end` ISO datetimes), and a **"Fetch from Yahoo Finance"** button (disabled until symbol + timeframe + range are set, matching the existing `canSubmit` pattern). This is the one new explicit write action in the app; the existing read-only Levels "Load" flow (J-04) stays intact.
- [ ] On submit, POST `/research/bars` (the store-first flow serves-or-fetches), then render: the real candles via the existing `StructureChart`, the real level lines + A/B/C zone table read verbatim from `GET /research/bars` + `GET /research/levels` (reuse the existing `ZoneRow`/chart rendering — zero client recomputation), and a **provenance badge** showing "Yahoo Finance".
- [ ] The provenance badge reads its label **verbatim from `GET /research/taxonomy` (`feed_basis.feeds`)** keyed by the served bar-series `feed` field — the `FeedBasisBadge` pattern. Either widen the existing `FeedBasisBadge` (currently typed `"sim"|"iex"|"sip"`) to accept the bar-series `feed`, or add a sibling that reads the same taxonomy label. **No hardcoded "Yahoo Finance" literal in the frontend.**
- [ ] Honest states (distinct copy each; never fabricate a candle/level/zone): a symbol with no stored bars → the existing distinct empty state; a store-first hit → renders instantly; a POST error surfaces the backend's own distinct message (422 unsupported-timeframe, 422 no-data-for-window, 504 vendor-timeout, 503 unavailable, 409 already-registered) — folded into the page's established honest degraded treatment, never a silent blank or a generic single error.

### New user-facing capability
The user fetches real historical bars from Yahoo Finance directly in the app (keyless, on an explicit click) and immediately sees the computed structure (S/R levels + A/B/C zones) on that real data, with an honest "Yahoo Finance" provenance stamp.

### New information displayed
Real Yahoo candles on the chart for the fetched window, and the "Yahoo Finance" provenance badge beside the series (both already backend-owned; newly surfaced in the UI). Levels + zones were already displayed (J-04) and are unchanged in ownership.

### New user actions
The **"Fetch from Yahoo Finance"** button (+ its timeframe selector and date-range inputs) — the one new explicit write action in the app.

### UI surface changes
A fetch-control section + a provenance badge added to the existing `/structure` page. No new route, no nav change.

### Product surface delta
`/structure` goes from a read-only view of pre-existing data to a page where the user can pull real bars on demand and watch the era-4 structure stack compute on them — the era's headline "fetch-from-the-app" moment.

### Blueprint conformance
No new surface. The fetch control + provenance badge live on `/structure`, which is already the registered canonical home for J-05 in the Information Architecture (blueprint IA table: "J-05 — fetch-from-the-app control + 'Yahoo Finance' provenance badge | `/structure` | Structure"). Nav skeleton unchanged — no re-approval requested.

### Data-contract additions
**None.** J-05 introduces no new owned value. Both values it surfaces are **already-registered rows** in the Data Contract: (1) `"Yahoo Finance"` human label for `feed="yahoo"` → owned by `research/taxonomy.py` `FEED_BASIS_LABELS`, served by `GET /research/taxonomy` (this iteration adds the missing dict entry; the row already exists); (2) bar-series provenance `feed="yahoo"` → owned by `BarStore` stamped from the Yahoo adapter, served by `GET /research/bars*`. The UI reads both verbatim and recomputes nothing. `blueprint.md` needs no edit.

## OUT OF SCOPE

- **Any mutation of frozen `research/levels.py` to enforce mixed-feed segregation (audit B1).** J-05 is the first surface that could let one symbol hold both a `feed="yahoo"` and an Alpaca `feed="sip"` series over overlapping timeframes; `compute_levels` is feed-blind and fingerprint-locked. Segregation is satisfied at the fetch/store/display layer (distinct append-only records + the "Yahoo Finance" badge), verified keyless on a single-feed fixture. A feed-scoped levels read, if ever built, is a versioned path BESIDE `levels.py`, never an edit — deferred (see NOTES + assumption ledger iter-5).
- The **live cache-miss Yahoo network fetch** as a keyless browser assertion — that path (out-of-retention / vendor-timeout / real-network) is integration-gated (`@pytest.mark.integration`, `TAPEOLOGY_LIVE_INTEGRATION=1`). The browser leg verifies the **store-first (no-network)** click on a pre-seeded fixture.
- Any new backend computation beyond the taxonomy label + the B2 GET normalization — no second levels/zones/PnL/strategy/champion computation; `levels.py`, `backtests.py`, `strategies.py`, `config.py`, the engine, the JSON `BarStore`, and the Alpaca adapter stay byte-identical.
- Champion promotion, mutation, or any write beyond the explicit bar fetch/store. The fetch control moves the champion **never**.
- A new MCP tool (MCP stays a byte-identical GET proxy), a new route/page, `/datasets` library-management UI, the tick-tape recorder, and the 15-symbol panel (roadmap; out of this chapter).

## DEFINITION OF DONE

- [ ] **J-05 passes via browser-qa-agent**: on `/structure` with a **pre-seeded, INDEXED** committed Yahoo fixture, the fetch control is present; clicking **Fetch from Yahoo Finance** with the fixture's symbol/timeframe/window serves **store-first (zero network)** and renders real candles + level lines + the A/B/C zone table + a **"Yahoo Finance"** provenance badge — captured in a screenshot (the browser lane MUST actually run and emit the screenshot; see NOTES).
- [ ] The provenance badge label "Yahoo Finance" is read from `GET /research/taxonomy` — `grep -r "Yahoo Finance" apps/frontend` (excluding `.next`) returns **no** hardcoded literal.
- [ ] `taxonomy.FEED_BASIS_LABELS["yahoo"] == "Yahoo Finance"` and `GET /research/taxonomy` returns `{"id":"yahoo","name":"Yahoo Finance"}` in `feed_basis.feeds` — asserted by a unit test with exact values.
- [ ] A symbol with **no** stored bars renders the distinct honest empty state (browser or unit).
- [ ] **B2 fixed**: a unit test asserts `GET /research/bars?symbol=` (blank, no timeframe) returns byte-identical JSON to `GET /research/bars` (no param); the no-param path and the real `?symbol=&timeframe=` filter remain byte-identical to iter-3.
- [ ] Coherence `COHERENCE-PASS`: the displayed candles, level prices, and zone class/score equal their `/research/bars` + `/research/levels` payloads verbatim (zero client recomputation); no second computation/endpoint/bar-store introduced.
- [ ] **Required-still-passing** J-01/J-02/J-03/J-04/J-06 remain green — `git diff <snapshot> --` over `levels.py`, `backtests.py`, `strategies.py`, `config.py`, `bars.py`, `bar_index.py`, `providers/adapters/`, the Alpaca path is EMPTY; `config_fingerprint == 4d665603569b9dbf`; engine equivalence 22/22; full backend suite green.
- [ ] No anti-goal violation introduced (scan-report CLEAN; no execution path; no advice/prediction/vocabulary-drift copy in the new control/badge; the UI computes no levels/PnL/champion and never promotes; the repeat/store-first POST stays `200` — no `409` "restored").
- [ ] Unit/integration tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-yahoo_fetch-iter-5-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-05):** on reachable frontend `:3301` + backend `:8301` + Chrome MCP (HARD pre-flight — see NOTES). Pre-seed the committed Yahoo fixture through the **store-first POST path (or a one-off `reindex()`)** so it is INDEXED (audit B3), and drive the fetch control with the fixture's exact `(symbol, timeframe, start, end)` so `index.lookup` hits and the click serves store-first with **no network**. Assert: candles render, one level line per `levels[]` entry, the A/B/C zone table matches `confluence_zones[]`, the provenance badge reads "Yahoo Finance", and a no-stored-bars symbol shows the distinct empty state. Spot-check J-04 (levels/zones still render) and J-06 (existing `/`, `/journal`, `/studies`, `/performance` surfaces intact) did not regress.
- **Unit/integration:** taxonomy `"yahoo"` label + `feed_basis.feeds` exact assertion; the B2 blank-param byte-identity test; the new POST-bars client helper (happy + error-shaped result); the fetch-control render flow reads bars/levels verbatim (no client recomputation). The store-first "repeat window POST = `200`, zero second fetch" route contract is already covered — do NOT restore a `409` there (iter-3 lesson).
- **Error cases:** blank symbol → button disabled / `422`; a config-valid-but-Yahoo-unsupported timeframe → distinct `422` copy (keyless static raise, if the selector can surface it). The live out-of-retention / vendor-timeout / real-network paths stay integration-gated (`TAPEOLOGY_LIVE_INTEGRATION=1`), not asserted in the default suite or the keyless browser leg.

## NOTES

- **HARD pre-flight (blocking for J-05 evidence).** The browser-qa lane silently no-op'd in iters 0/2/3 (services unreachable / Chrome MCP absent). J-05 is the first journey with genuinely new `/structure` UI; per the iter-0 and iter-2 lessons, its browser lane MUST have both services started and Chrome MCP available, or J-05 cannot be evidenced — a "passing" without a real render screenshot is unevidenced for a UI journey and must be scored `unknown`, not `passing`. The zero-frontend-diff fallback that covered iters 2/3 does not exist once this control lands.
- **iter-3 lesson (store-first route contract):** a duplicate `POST /research/bars` of the same `(symbol, timeframe, window)` returns **`200`, served store-first (zero adapter calls)** — NOT `409`. The fetch control's "click again / pre-seeded window" behaviour and its tests must expect `200` store-first; do not "restore" a `409` on a repeat-window POST. (The store-LEVEL content-duplicate `409`, a different window whose content matches, is a separate frozen path and stays.)
- **iter-1 lesson (fixture placement):** any committed `feed="yahoo"` fixture for the browser test must live under `apps/backend/tests/fixtures/yahoo/` (NOT `.../fixtures/bars/`, whose frozen test blanket-asserts `feed=="sip"` over the whole dir). Keep the Yahoo default confined to `get_bar_fetch_adapter()` on `POST /research/bars` — never the shared/global adapter resolver.
- **iter-4 lesson + assumption ledger iter-5 (mixed-feed pooling):** frozen `compute_levels` selects a symbol's series by symbol alone (feed-blind), so it would pool a Yahoo and an Alpaca series across timeframes. J-05's "honestly segregated from Alpaca `sip`" is met at the fetch/store/display layer (distinct append-only records + the "Yahoo Finance" badge) and browser-verified on a single-feed (yahoo-only) fixture — NOT by a new levels computation. Do NOT edit `levels.py` to add segregation (fingerprint-locked, a critical anti-goal); if ever needed it is a versioned path beside it. Logged to `runs/goal-session-yahoo_fetch/state/assumptions.md` (iter-5).
- **iter-0 lesson (evidence floor):** since J-05 is browser-verifiable, confirm the browser lane actually ran and emitted a screenshot before claiming `passing`.
- If J-05 passes, this is the final Must-have journey — the evaluator can consider `GOAL_ACHIEVED` once all deterministic gates hold.
