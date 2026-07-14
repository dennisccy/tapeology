# Tapeology — Project Goal (Era 5B — The Tradable Wall: structure × real tape at real levels)

> Eras 1–5 are the **foundation** of this goal and MUST NOT regress. Eras 1–2 (tape reading + the research
> evolution, J-01 – J-68, GOAL_ACHIEVED) are archived at
> [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md); the structure-UI interlude at
> [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md); **Era 5 "The Library"** (keyless
> Yahoo bars + derived SQLite index + the `/structure` fetch control, J-01 – J-06, GOAL_ACHIEVED 2026-07-12) at
> [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md). Era 3 (the profit-research
> measurement machine) and Era 4 (the structure-and-tape evolution) are frozen foundation; their records live in
> git history and in `reports/goal-session-tape_to_profit-delivered.md` and
> `reports/goal-session-tape_to_profit_support_resistence-delivered.md`.
>
> **This is Era 5B "The Tradable Wall"** — the **credentialed continuation** of Era 5 (roadmap cards 5.2
> tick-side and 5.7) fused with the trade-craft question the operator actually asked. The operator now supplies
> **Alpaca credentials**, unblocking real trade/quote recording for the first time. Deliberately NOT pulled
> forward: the era-6 "Referee" statistical gates (bootstrap CIs, multiple-testing control) and the `/datasets`
> library UI (card 5.9) — this era measures with the existing era-3/4 gates.

## Vision

Era 5 filled the library with real bars — and exposed the next honest problem: the structure computed on them
is **untradable as displayed**. Measured on real data: AAPL as of 2026-06-22 returns **1,800 levels and 212
confluence zones** (26 A / 13 B / 173 C), every one drawn on the chart; the strongest zone sits at ≈296.9
while the wall a trader actually saw was **300–302.4** — four daily rejection highs before 06-22 (300.75,
300.48, 302.07, 300.57), two more after (302.42 on 06-22, 301.64 on 06-23), then a −6% collapse to 275.15 on
06-25. The signal exists in the data; the product buries it.

This era turns structure into something the operator can trade **with the tape**:

1. **Distill** — a *tradable level map*: at most a handful of price **bands** per symbol per side, scored for
   quality (multi-timeframe breadth, daily touch history, recency, round-number confluence — the 300 wall IS a
   round number) and computed with **morning-markup discipline** (only data through the prior completed
   session's close), exactly like a trader marking charts before the open.
2. **Find the examples** — a scanner over the 12-symbol panel's stored 5m bars that finds every historical
   *band-touch event* and classifies what happened next (rejected / broke / chopped), building a case-study
   registry with AAPL 22-Jun-2026 ~300 as the pinned ground-truth case.
3. **Put the tape at the wall** — with the operator's Alpaca credentials, record real trade/quote windows
   around the best events, replay them through the frozen five-state tape engine, and show what the tape said
   at each touch (`ask_absorption` into a rejection, `buyer_control` through a break…).
4. **Measure what profits** — backtest `v1` vs the frozen `structure_tape` vs a new registered
   `structure_tape_map` (same archetype, armed on the tradable map) over identical recorded windows, and
   publish an honest edge report: per class × side × reaction cells, n≥5 or `insufficient_sample`,
   train/hold-out never pooled, null baseline, the full PnL register.
5. **Surface it where trading happens** — `/structure` defaults to the clean map + case browser + edge report;
   the **cockpit price chart** overlays the bands next to its existing tape-state markers and shows a
   **descriptive confluence chip** when price is inside a band and the tape state matches the config-owned
   rejection/breakthrough mapping — conditions and measured history, never advice.

## Target Users

- The project owner (a discretionary intraday trader) who wants the handful of levels worth trading — not
  1,800 — and the tape evidence at those levels, in the cockpit where trades are watched. The operator now
  supplies **Alpaca credentials** (env-only) for real tick recording.
- AI dev-chain agents (the goal-mode chain) building and browser-verifying the map, scanner, recordings,
  report, and both UI surfaces.

## Foundation invariants (still law — eras 1–5)

The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md)), the
era-3 measurement machine, the era-4 structure stack, and the era-5 keyless bar library remain binding
verbatim on ALL new code: price-impact-over-aggression; honest uncertainty; **no fabricated data**; single
source of truth; no magic numbers; provider-agnostic engine; deterministic & reproducible; no secrets in
source; research read-only over the engine; journal/record integrity; source/feed/`config_fingerprint`
honesty; the existing surfaces (`/`, `/journal`, `/journal/[id]`, `/studies`, `/performance`, `/structure`)
stay intact.

In addition, these stay **frozen foundation**:

1. The **tape engine** emits its five states (`buyer_control`, `seller_control`, `bid_absorption`,
   `ask_absorption`, `unclear`) byte-identically under `default`; `config_fingerprint` stays
   `4d665603569b9dbf` (equivalence-tested). Config additions for this era MUST NOT alter it.
2. The **structure computations** — `research/levels.py` (raw levels + A/B/C zones, its 5 bps touch and
   20 bps cluster parameters included), the strategy registry entries `v1` + `structure_tape`, the
   class-scaled math, the per-class backtest breakdown, and the named-strategy sweep — stay behaviorally
   byte-identical: identical inputs keep producing identical outputs. `research/backtests.py` and `config.py`
   may gain **additive** code/entries for `structure_tape_map` only; no existing definition, parameter, or
   output changes.
3. The **canonical bar store** (`apps/backend/app/research/bars.py`) and the era-5 layer over it — the Yahoo
   adapter (`adapters/yahoo.py`), the derived SQLite `bar_index` (a rebuildable cache, never a source of
   truth), the store-first coordinator, and the `/structure` fetch control + "Yahoo Finance" provenance badge
   — keep working exactly as shipped.
4. **`v1`, `default`, `structure_tape`, and the champion pointer are frozen.** New strategy work is a NEW
   registered definition beside them. The champion moves only through the existing sweep gate on hold-out
   data; this era may finally feed that gate real data, but it never hand-promotes.
5. The **Alpaca adapter and its credentialed path** stay byte-identical; this era USES them (recording) and
   never rewrites them. The **DatasetStore** stays the one owner of recorded tick datasets (append-only,
   checksummed, splits frozen at registration).

## Success Criteria

In priority order — honesty and non-regression outrank everything:

1. **Nothing existing regresses.** Full backend suite green, engine equivalence proves byte-identical
   `default` outputs, `config_fingerprint` stays `4d665603569b9dbf`, frozen strategies/levels/BarStore/Alpaca
   paths unchanged, every era-1–5 surface keeps working.
2. **Noise becomes signal on the pinned case.** For AAPL as of the 2026-06-22 session (map basis = the
   2026-06-18 close), the tradable map has **≤10 bands total**, and a resistance band covering the rejection
   cluster (containing 300.48 through 302.07, round-number 300 flagged) ranks in the **top 2** resistance
   bands by quality score — versus the 1,800-level / 212-zone raw output it distills.
3. **More examples exist.** The scanner finds **≥15 band-touch events across ≥8 of the 12 panel symbols**
   within the stored 5m window, each with a deterministic reaction classification and forward returns; the
   pinned AAPL 06-22 event appears as `rejected` with negative forward reaction.
4. **Real tape is recorded at the walls.** With operator credentials, **≥10 event windows across ≥5 symbols**
   (including the pinned AAPL 06-22 window) are recorded as registered datasets — append-only, checksummed,
   feed stamped verbatim, split-frozen — and each event's five-state timeline at the touch is visible.
5. **The edge report answers the profit question honestly.** `v1` vs `structure_tape` vs `structure_tape_map`
   on identical recorded windows; per-cell n≥5 or `insufficient_sample`; train/hold-out never pooled; null
   baseline; the full register. An empty-survivor report is a valid outcome.
6. **Both surfaces read canonical values verbatim.** `/structure` (map / cases / report) and the cockpit
   (band overlay + chip) recompute nothing; every displayed value is byte-equal to its owning endpoint.
7. **The rails hold.** Descriptive language only; no execution path; no lookahead (morning-markup as-of
   discipline); feeds never pooled; keys never committed.

## Key Capabilities

Layered strictly on top of the era-1–5 capabilities, which remain unchanged.

1. **The tradable level map** — new module `apps/backend/app/research/tradability.py`: consumes
   `compute_levels` output **verbatim** (plus bars for price-scale context), clusters into ≤K bands per side
   (config-owned cap), scores quality (distinct-timeframe breadth, daily touch count, recency, round-number
   confluence), inherits each band's A/B/C class from its best member zone (class stays owned by
   `levels.py`), and enforces prior-session-close as-of discipline. Owned endpoint: `GET /research/tradability`.
2. **The touch-event scanner + case registry** — new module `apps/backend/app/research/setups.py`: walks each
   panel symbol's stored 5m bars session by session against that session's morning map; emits band-touch
   events with deterministic reaction labels (`rejected` / `broke` / `chopped`, config-owned pre-registered
   definitions) and forward returns; pinned case: AAPL 2026-06-22 at the ~300–302 band. Owned endpoints:
   `GET /research/setups`, `GET /research/setups/{id}`.
3. **Event-windowed real tape recording (credentialed)** — the EXISTING recorder (`record_from_source`)
   records trade/quote windows around top scan events (config-owned padding, e.g. touch −60 min … +90 min)
   into registered datasets; feed stamp verbatim from the adapter tier (`iex` on free keys — honestly thinner
   than SIP and labeled as such); a committed fixture slice keeps CI keyless.
4. **Tape-at-the-wall join** — each recorded event's window replayed through the frozen `TapeEngine`; the
   five-state timeline and transitions joined onto the event drill-in (engine remains the state owner).
5. **`structure_tape_map`** — a NEW config-owned registry entry beside frozen `v1`/`structure_tape`: same
   entry/exit archetype as `structure_tape`, armed on tradable-map bands with the inherited class driving the
   existing class-scaled stops/rewards/size. Additive arming path in the backtest runner.
6. **The edge report** — new module `apps/backend/app/research/edge_report.py` aggregating the three
   strategies' backtests over the recorded windows into per strategy × class × side × reaction cells under
   the era-3/4 gates. Owned endpoint: `GET /research/edge-report`.
7. **`/structure` decluttered** — default view = the tradable map (bands on the chart + quality table), with
   the raw 1,800-level view behind an explicit toggle; a Case Studies browser (registry + per-event drill-in
   with chart, band, reaction, tape timeline); an Edge Report section. Era-5 fetch control preserved.
8. **Cockpit confluence** — `PriceChart` overlays the watched symbol's tradable bands (honest empty state for
   SIM-*/no-bars symbols) beside its existing tape-state markers, and shows a **descriptive confluence chip**
   when last price is inside a band AND the current tape state matches the config-owned
   rejection/breakthrough mapping for that side (mapping + labels read from `/research/strategies`).
9. **MCP read-only proxies** for the new GETs (`tradability`, `setups`, `edge_report`) — byte-identical
   proxies, read-only, superseding era-5's "no new tool" clause (which was era-scoped).

## Non-Goals

- **No execution path, ever** — no brokerage/order/trading integration of any kind, real or paper. Recording
  historical trades/quotes is a read of market data.
- **No era-6 "Referee" gates yet** — no bootstrap CIs, no multiple-testing control, no new statistical
  machinery; this era measures with the existing era-3/4 gates. (Era 6 remains the roadmap's next headline.)
- **No `/datasets` library-management UI** (roadmap card 5.9 stays deferred) and **no bulk full-day panel
  recording** — recording is event-windowed only (scoped persistence).
- **No mutation of the frozen raw structure computation** — `levels.py` and its 5 bps / 20 bps parameters stay
  untouched; the tradable map is a NEW derived layer with its own owner, not a re-tuning.
- **No ML, no prediction language, no trading advice, no imperative cues** — the chip and every report are
  descriptive and cite measured history.
- **No champion hand-promotion** — the pointer moves only if the existing sweep gate promotes on hold-out.
- **No new nav entry** — the era lives inside `/structure` and the cockpit; no new page.
- **No live-mode cockpit changes** — the price chart stays hidden in live mode, exactly as today.
- **No pooling** — `iex`, `sip`, and Yahoo-bar lineages never merge in any analysis cell, report row, or claim.

## Constraints

- **Stack (carried over):** Frontend Next.js 15 + TypeScript + Tailwind v3 (npm), `lightweight-charts`,
  dark-only. Backend Python 3.12 + FastAPI. Backend `http://localhost:8000`, frontend
  `http://localhost:3000`. Sim tickers stay keyless. No new runtime dependency.
- **Credentials discipline:** Alpaca keys live ONLY in the operator's environment (the existing adapter's
  variables); never committed, never logged, never echoed into artifacts/reports/fixtures. **Operator act
  required:** J-03 and J-06 verification need the keys configured; without them those journeys honestly
  report blocked — never simulated.
- **Feed honesty:** the `feed` stamp comes verbatim from the adapter/key tier. Free-tier historical ticks are
  `iex` — a thin slice of consolidated volume; every tape-derived surface labels the feed, and nothing
  equates `iex` with `sip`. Analyses never pool across feeds.
- **Morning-markup as-of discipline:** the tradable map used for any session's events, chips, or UI derives
  ONLY from bars fully completed by the prior session's close (e.g. the 2026-06-22 map derives from
  2026-06-18 — 06-19 was a market holiday). No forming-bar data enters a map, an event, or a chip.
- **Recording discipline:** recording is an explicit, logged, event-windowed act around registered scan
  events with config-owned padding; no ambient or scheduled recording; datasets append-only, checksummed,
  splits frozen at registration (config-owned seeded rule).
- **Config-owned everything:** the 12-symbol panel (`AAPL MSFT NVDA TSLA AMZN GOOGL META AMD NFLX SPY QQQ
  JPM`), band cap K, band-width scaling, quality-score weights, reaction definitions, forward-return
  horizons, recording padding, and split rule are config-owned constants — **pre-registered before
  measurement, no magic numbers, no post-hoc tuning to manufacture survivors.**
- **PnL honesty register (unchanged):** a $ never without its R, n, fee/slippage assumptions, basis
  (train/hold-out/forward), null baseline, and the visible "simulated — not indicative of live results"
  register; sub-minimum-n results labelled `insufficient_sample`; train and hold-out never pooled.
- **UI read discipline:** both pages read canonical endpoints (`/research/tradability`, `/research/setups`,
  `/research/edge-report`, `/research/bars`, `/research/levels`, `/research/strategies`, `/research/taxonomy`,
  `/tape/{ticker}/history`, `/meta/ui-routes`) and render values **verbatim**. The chip's condition is a
  display conjunction of two canonical values (price-in-band × mapped tape state); its mapping and labels are
  read from `/research/strategies` — never client-hardcoded. Zero client recomputation of scores, classes,
  reactions, PnL, or provenance.
- **Test discipline:** the default suite stays hermetic and keyless — `FakeAdapter` injection, the existing
  committed fixtures, plus ONE new small committed tick-fixture slice for the tape-at-the-wall path; live
  Yahoo fetch and credentialed Alpaca recording run only under the `integration` marker
  (`TAPEOLOGY_LIVE_INTEGRATION=1`) or as explicit operator-run steps.
- **MCP read-only discipline:** the MCP server stays a byte-identical read-only proxy of GET endpoints; the
  only additions are proxies of the new GETs.

## Design Direction

Unchanged from eras 4–5: dark-only, dense, professional, terminal-grade; `lightweight-charts` overlays
(price lines/areas for bands); no marketing gloss; honest empty/degraded states are first-class UI.

## Product Shape

Nav (top bar) is unchanged: **Cockpit `/` · Journal `/journal` (+ `/journal/[id]`) · Studies `/studies` ·
Performance `/performance` · Structure `/structure`**. Inside `/structure`: **Tradable Map (default) · Case
Studies · Edge Report** sections (era-5 fetch control preserved). The cockpit `PriceChart` gains the band
overlay + confluence chip.

**Data Contract (canonical values):** new owned values, each with exactly one owner:

- **Tradable level map** (bands: price range, side, quality score, member refs, round-number flag, inherited
  class) — owned by `research/tradability.py`; read via `GET /research/tradability`. Band **class** is a
  projection of the member zones' A/B/C (class itself stays owned by `research/levels.py`).
- **Touch events + reactions + forward returns + case registry** — owned by `research/setups.py`; read via
  `GET /research/setups` and `GET /research/setups/{id}` (drill-in includes the tape timeline for recorded
  events; tape **states** remain owned by the frozen engine replay).
- **Edge-report cells** — owned by `research/edge_report.py`; read via `GET /research/edge-report`.
- **`structure_tape_map` definition + the chip's rejection/breakthrough state mapping** — config-owned; read
  via `GET /research/strategies`.
- **Recorded tick datasets** — owned by the existing `DatasetStore` (append-only, checksummed, split-frozen);
  read via `GET /research/datasets`.
- Raw levels/zones, bar series + checksums, backtest aggregates, PnL ledger, taxonomy labels, UI route map —
  unchanged existing owners.

## Must-have user journeys

Journeys **J-01 – J-07** open Era 5B. **Frontend is present** (J-05/J-06 are browser-verifiable). J-03 and
J-06 carry a `*(Verified with Alpaca credentials configured)*` tag — the credentialed acts are
operator-gated and honestly report blocked when keys are absent; committed fixtures keep the default suite
and CI keyless. Natural dependency order: J-01 → J-02 → J-03 → J-04, then J-05/J-06 surface them; **J-07
guards continuously.** The foundation (eras 1–5) MUST NOT regress.

- **J-01: The tradable level map — from 1,800 levels to ≤10 bands**
  - Steps:
    1. Add `apps/backend/app/research/tradability.py`: consume `compute_levels(symbol, as_of)` output
       verbatim (never re-detect pivots/extremes), cluster levels into price **bands** with a config-owned
       price-scale-aware width, score each band (distinct-timeframe breadth, daily touch count, recency,
       round-number confluence), inherit the band class from its best member zone, keep at most K bands per
       side (config-owned cap, K ≤ 5), and enforce the morning-markup rule: for any `as_of`, use only bars
       fully completed by the prior session's close.
    2. Expose `GET /research/tradability?symbol=&as_of=` as the single owner; add the read-only MCP proxy
       `tradability`; repeat-call determinism (byte-identical JSON for identical requests).
    3. Pinned case: request AAPL with `as_of` inside the 2026-06-22 session (map basis = the 2026-06-18
       close, which already contained rejection highs 300.75 / 300.48 / 302.07 / 300.57).
  - Acceptance: the AAPL 2026-06-22 map has ≤10 bands total; a resistance band containing both 300.48 and
    302.07 (round-number 300 flagged) ranks in the top 2 resistance bands by quality score; identical
    requests return byte-identical JSON; REST and the MCP proxy agree byte-for-byte; the map derives from no
    bar newer than the 2026-06-18 close; `research/levels.py` and its raw output are byte-identical to
    before. *(Keyless on stored bars; automated.)*

- **J-02: The wide scan — a case-study registry across the 12-symbol panel**
  - Steps:
    1. Fetch panel bars via the existing era-5 Yahoo store-first flow (explicit acts): `1d` (long window),
       `1h`, `5m` (retention window) for the config-owned 12-symbol panel.
    2. Add `apps/backend/app/research/setups.py`: for each symbol and each session in the stored 5m window,
       compute that session's morning map (J-01), detect band-touch events in the session's 5m bars (first
       touch per band per session, config-owned re-arm rule), classify the reaction deterministically
       (`rejected` / `broke` / `chopped` — config-owned pre-registered definitions), and record forward
       returns at config-owned horizons (event-relative, measured strictly after the touch).
    3. Expose `GET /research/setups` (registry: filterable by symbol / reaction / band class) and
       `GET /research/setups/{id}` (drill-in); add the read-only MCP proxy `setups`.
  - Acceptance: the registry contains ≥15 events across ≥8 panel symbols; the AAPL 2026-06-22 event on the
    ~300–302 band appears with reaction `rejected` and negative forward-return fields; every event's map
    derives only from data before its session (no lookahead: shifting `as_of` earlier never changes an
    already-emitted event); identical scans are byte-identical; REST and MCP agree. *(Keyless on stored
    bars; automated.)*

- **J-03: Real tape at the wall — credentialed event-window recording**
  - Steps:
    1. With operator Alpaca credentials in env, record trade/quote windows around the top-ranked scan events
       — ≥10 events across ≥5 symbols, ALWAYS including the pinned AAPL 2026-06-22 ~300 test — via the
       existing `record_from_source` recorder with config-owned padding (touch −60 min … +90 min); each
       becomes a registered dataset: append-only, checksummed, `feed` stamped verbatim from the adapter tier,
       split assigned at registration by the config-owned seeded rule.
    2. Join the tape to each recorded event: replay the window through the frozen `TapeEngine` and attach the
       five-state timeline (states + transition times around the touch) to `GET /research/setups/{id}`.
    3. Commit ONE small fixture slice (a short recorded window) under `apps/backend/tests/fixtures/` so the
       join path is tested keyless in CI; full recording runs under the `integration` marker / as an
       operator-run step.
  - Acceptance: ≥10 event-window datasets exist (≥5 symbols, pinned AAPL 06-22 included), each append-only,
    checksum-verified, honestly feed-stamped, split-frozen at registration; the pinned event's drill-in shows
    the five-state timeline at the 300-test; the engine and recorder are byte-identical (reused, not
    modified); no credential appears in any file, log, or artifact; the default suite passes keyless via the
    committed fixture. *(Verified with Alpaca credentials configured.)*

- **J-04: The edge report — what actually profits, under the existing gates**
  - Steps:
    1. Register `structure_tape_map` as a NEW config-owned strategy beside frozen `v1`/`structure_tape`: the
       `structure_tape` entry/exit archetype armed on tradable-map bands (band proximity + the config-owned
       rejection/breakthrough tape-state mapping), the inherited band class driving the existing class-scaled
       stops/rewards/size. Extend the backtest runner with an additive arming path; existing strategies'
       outputs stay byte-identical on identical inputs.
    2. Run backtests for all three strategies over EACH recorded event dataset (levels/map from the bar
       store, tape from the dataset replay).
    3. Add `apps/backend/app/research/edge_report.py` + `GET /research/edge-report` (+ MCP proxy
       `edge_report`): aggregate per strategy × class × side × reaction cells — train cells with hold-out
       rows separate; each cell carries n, R stats, and $ with the full register; n<5 cells labelled
       `insufficient_sample`; a null-baseline comparison; a ranked list of surviving train cells with their
       hold-out status.
  - Acceptance: the report compares all three strategies on identical data; every $ carries R, n,
    fee/slippage assumptions, basis, null baseline, and the "simulated — not indicative of live results"
    register; train and hold-out are never pooled; feeds are never pooled; each cell either has n≥5 or is
    labelled `insufficient_sample` (an all-insufficient report is a valid outcome); no existing gate,
    minimum-n, or split rule is weakened; the champion pointer is untouched unless the EXISTING sweep gate
    independently promotes on hold-out. *(Keyless via the committed fixture; full run credentialed.)*

- **J-05: `/structure` decluttered — the map is the default, the noise is a toggle**
  - Steps:
    1. On `/structure`, make **Tradable Map** the default view: the chart renders candles + ≤10 band overlays
       (price areas/lines) + a map table (band range, side, quality score, inherited class, member count,
       round-number flag) read verbatim from `GET /research/tradability`; the prior all-levels rendering
       moves behind an explicit "raw levels" toggle (era-5 behavior preserved, off by default).
    2. Add the **Case Studies** section: the registry table from `GET /research/setups` with
       symbol/reaction filters; clicking a row opens the drill-in (5m chart around the event + band + reaction
       + forward returns + the tape timeline when recorded).
    3. Add the **Edge Report** section rendering `GET /research/edge-report` verbatim (register visible).
    4. Load AAPL as of 2026-06-22 and open the pinned case.
  - Acceptance: the default AAPL 2026-06-22 view shows ≤10 bands including the ~300–302 resistance band —
    not 1,800 lines; the toggle restores the raw view unchanged; the pinned case drill-in shows `rejected`
    with its forward returns (and the tape timeline once J-03 ran); every displayed value is byte-equal to
    its owning endpoint (zero client recomputation); the era-5 fetch control and provenance badge still work.
    *(Keyless on stored data; browser-verifiable.)*

- **J-06: Cockpit confluence — bands + tape markers + a descriptive chip**
  - Steps:
    1. In the cockpit `PriceChart` (sim/historical modes; live stays hidden), overlay the watched symbol's
       tradable bands (from `GET /research/tradability`, as-of the prior session close) beside the existing
       tape-state markers; symbols with no bar series (e.g. SIM-*) show an honest "no tradable map" state.
    2. Add the **confluence chip**: visible only while last price is inside a band AND the current tape state
       matches the config-owned rejection/breakthrough mapping for that band's side — mapping and labels read
       from `GET /research/strategies`, never hardcoded. Chip text is descriptive and cites the edge report
       (e.g. "Inside R-band 300.4–302.1 (class A) · tape: ask_absorption · measured history: edge report") —
       no imperative, no prediction.
    3. With credentials configured, watch AAPL in historical mode over the 2026-06-22 300-test window;
       observe markers, bands, and the chip during the test; screenshot. Verify a SIM ticker shows the chart
       + markers + the honest empty state, and that live mode is unchanged.
  - Acceptance: during the credentialed AAPL 06-22 replay the band overlay is visible and the chip appears at
    the 300-test with descriptive copy (and is absent when price is outside every band or the state is
    unmapped/`unclear`); the mapping/labels/bands are all endpoint-read (zero client recomputation and no
    client-hardcoded vocabulary); SIM tickers degrade honestly; the live-mode surface is byte-identical to
    before. *(Verified with Alpaca credentials configured; browser-verifiable.)*

- **J-07: The foundation is unchanged (regression sentinel)**
  - Steps:
    1. Run the full backend suite and the engine equivalence test; run the sim cockpit flows (`SIM-BUYER`
       settles `buyer_control`, `SIM-SELLER` settles `seller_control`) and spot-check `/journal`, `/studies`,
       `/performance`, and the era-5 `/structure` behaviors (fetch control, store-first reuse, provenance
       badge) in the browser.
    2. Confirm `config_fingerprint` is still `4d665603569b9dbf`; confirm `research/levels.py` raw output,
       `v1`, `structure_tape`, `default`, the champion pointer, the JSON `BarStore`, the `bar_index`
       store-first flow, the Alpaca adapter, and the recorder produce byte-identical results on identical
       inputs; confirm the only additive surfaces are those this era names.
  - Acceptance: the full backend suite passes (no test deleted or weakened); the equivalence test proves
    byte-identical `default` outputs and the pinned fingerprint; era-1–5 surfaces behave exactly as shipped;
    existing strategies' backtest outputs on identical inputs are byte-identical; the additive changes are
    exactly: `tradability.py`, `setups.py`, `edge_report.py`, the `structure_tape_map` registry entry + its
    additive arming path, the new config constants, the event-window recordings + one committed fixture, the
    three MCP read-only proxies, the `/structure` sections, and the cockpit overlay + chip. *(Browser-verifiable
    + automated.)*

<!-- AUTO:journeys -->
<!-- /AUTO:journeys -->

## Anti-goals

**Immutable rails — the identity of the project (copied verbatim from
[`docs/research-directions.md`](research-directions.md) §0.3; enforced by existing tests and audits; only
ever grow more specific, never weaker):**

1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no
   "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new
   research code adds matching guard tests, never weakens them.) *(critical)*
2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
   fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative
   trading cues. *(critical)*
3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and
   thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay
   byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the
   sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never
   lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor.
   *(critical)*
5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
6. **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and
   read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests
   reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface
   can change state. *(critical)*
9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged,
   never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit,
    logged act. *(critical)*

**Era-5B-specific anti-goals (added, not weakening any rail above):**

- **The tradable map is a lens, never a second levels engine.** `research/tradability.py` consumes
  `compute_levels` output verbatim (plus bars for scale context); it never re-detects pivots/extremes and
  never alters the frozen raw computation or its parameters. *(critical)*
- **Morning-markup discipline.** Any session's map derives only from bars fully completed by the prior
  session's close; no forming-bar data enters a map, an event, or a chip. *(critical)*
- **Descriptive, never imperative.** Chips, case studies, and reports state conditions and cite measured
  history — never "buy/sell/short now", no prediction or expected-return language, anywhere in UI copy.
  *(critical)*
- **Recording stays explicit, windowed, and logged** — only around registered scan events with config-owned
  padding; no ambient, scheduled, or full-day bulk recording; every dataset append-only, checksummed,
  split-frozen at registration. *(critical)*
- **Feed honesty — never pool across feeds.** The `feed` stamp comes verbatim from the adapter/key tier;
  `iex`, `sip`, and Yahoo-bar lineages are never pooled in any analysis cell, report row, or claim; `iex` is
  never presented as the consolidated tape. *(critical)*
- **No gate bending for a headline.** n≥5 per reported cell, train/hold-out separation, null baseline, and
  the full PnL register hold everywhere; an empty or all-`insufficient_sample` edge report is a valid,
  publishable outcome. *(critical)*
- **The champion moves only through the existing sweep gate on hold-out data.** This era may feed the gate;
  it never hand-promotes `structure_tape_map` or anything else. *(critical)*
- **New strategy code is additive and registered — never a mutation.** `structure_tape_map` is a new
  config-owned registry entry beside frozen `v1`/`structure_tape`; no frozen definition, parameter, or output
  changes; the `config_fingerprint` stays `4d665603569b9dbf`. *(critical)*
- **Keys never committed, never logged.** Alpaca credentials live only in the operator's environment; no
  secret in source, fixtures, logs, artifacts, or reports. *(critical)*
- **Live mode stays untouched.** The cockpit price chart remains hidden in live mode; no execution path,
  ever. *(critical)*
- **No vocabulary drift.** No "paper trading", "shadow trading", "annualized", "expected profit", or
  advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the
  visible "simulated — not indicative of live results" register.
- **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the
  `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or
  any other part of this file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger)
  acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged
  walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*
