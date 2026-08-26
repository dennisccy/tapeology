# Tapeology Research Directions — The Post-Era-4 Reservoir

**Authored 2026-07-06 by Claude Fable 5** (session-grounded in the codebase at era-4 completion,
red-teamed against the actual harness). This document is the **direction reservoir for roughly one
year of demand-driven evolution**. It is written so that **less capable models can execute it
without inventing judgment**: every idea carries its formulas, its file-level extension points, its
honest evaluation plan, its kill criteria, and the traps most likely to catch an inattentive
executor.

**Standing of this document**: `docs/goal.md` is the constitution of the *current* era; this file
is the reservoir that *feeds future rewrites* of `docs/goal.md`. When an era completes, come back
here, update the status table (Part 5.2), and let the router (Part 5.1) name the next eligible era.
This file is data, not law: the immutable rails in Part 0.3 outrank everything in it.

---

## Table of contents

- **Part 0 — How to use this document** (era protocol, immutable rails, fingerprint protocol, global traps, card template, glossary)
- **Part 1 — The year at a glance** (era table, dependency graph, router pointer)
- **Part 2 — Era chapters** (Eras 5–16, ~70 idea cards)
- **Part 3 — Cross-cutting rules** (statistics discipline, cost sensitivity, determinism, escalation)
- **Part 4 — DO-NOT list** (banned directions, with reasons)
- **Part 5 — Operating system for the year** (router, status table, proposer amendment, perpetual workstreams, contingency tree)

---

# Part 0 — How to use this document

## 0.1 Who reads this and how

- **The human operator (Dennis)**: picks the next era when he has time (cadence is fully
  demand-driven — there is no calendar), performs the few operator-gated actions (running the
  recorder with Alpaca credentials, approving a Databento purchase, activating a proposer
  amendment), and commits.
- **The goal-decomposer / planning model of a future session**: turns ONE era chapter into a new
  `docs/goal.md` using the protocol in 0.2, then goal mode runs it.
- **The goal-proposer** (already active via `project-extensions/proposer-guidance.md`): treats this
  document as its ranked idea reservoir — see the amendment protocol in Part 5.3.

Rules of engagement for any model using this file:

1. Execute **one era per goal session**. Never mix cards from different eras into one goal.md
   unless the router explicitly says so (some cards are marked *portable*).
2. If an era chapter contradicts the live codebase (a file moved, a function renamed), **trust the
   codebase and update this document** — cite the correction in the status table. File paths here
   were verified on 2026-07-06; symbol names were preferred over line numbers because lines rot.
3. If you do not understand a card well enough to write its falsifiable acceptance test, **do not
   improvise** — pick a different card and note the skip in the status table. An honest skip is
   cheap; a corrupted measurement poisons the ledger forever.

## 0.2 The era protocol — turning a chapter into `docs/goal.md`

Follow this mechanically (the shape matches `templates/project-goal.md` and every archived goal in
`docs/goal-archive/`):

1. **Archive** the current constitution: copy `docs/goal.md` to
   `docs/goal-archive/goal-<YYYY-MM-DD>.md` (the existing convention — see
   `docs/goal-archive/goal-2026-07-03.md`).
2. **Write the new `docs/goal.md`** with these sections, in this order: Vision (the era's mission
   paragraph from its chapter), Success Criteria, Key Capabilities, Non-Goals, Constraints,
   Product Shape (navigation + canonical values — every new shared value gets ONE owning
   endpoint), Must-have user journeys, Anti-goals.
3. **Journeys**: convert the era's cards into 5–8 journeys (J-01, J-02, …), **staged
   data-first** — the proven era-3/4 pattern:
   - J-01 = the data/plumbing the era needs (ingestion, store, schema);
   - middle journeys = computation → strategy/detector → measurement, one card cluster each;
   - second-to-last journey = the era's **honest measurement** (sweep/edge-report/atlas run whose
     acceptance allows "no survivor" as a passing state);
   - **last journey = the regression sentinel** (always): full backend suite green, `default`
     engine byte-identical, pinned `config_fingerprint` unchanged (or epoch-bumped per 0.4),
     archived-era behavior untouched.
   - Each journey needs numbered browser/CLI-checkable steps and an "Acceptance" line naming an
     observable end state. If an era has more than ~8 journeys of work, split it into two
     sessions at the seam its chapter marks with **[SPLIT-POINT]**.
4. **Anti-goals**: copy Part 0.3's immutable rails **verbatim**, then add the era-specific
   anti-goals listed at the end of the era chapter. Anti-goals only ever grow more specific —
   never weaker.
5. **Run goal mode** (`incredible_auto_dev/docs/goal-mode-quickstart.md` — the framework is
   vendored there; CLAUDE.md's `docs/…` link resolves through the root symlinks), with a fresh
   `--session-id` named after the era (e.g. `library_era`).
6. **On completion**: append the era's row to the status table in Part 5.2 of this file; record
   the key finding in one sentence; consult the router for the next eligible era.

## 0.3 Immutable rails — copy into EVERY future era's Anti-goals, verbatim

These are not era decisions. They are the identity of the project. All are enforced by existing
tests and audits; several are load-bearing for legality and honesty.

1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
   trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
   tier-1 guard; new research code adds matching guard tests, never weakens them.)
2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
   fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
   imperative trading cues.
3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
   states and thresholds, and archived-era behavior stay byte-identical. New work is additive and
   versioned beside them, never a mutation of them.
4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
   through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are
   labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
   feeds/fingerprints to manufacture a survivor.
5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
   (See the forming-bar rule in card 6.4.)
6. **Single source of truth** — each shared value is computed once, owned by one canonical
   endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
   violations.
7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
   requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
   research artifact.
8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
   MCP surface can change state.
9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never
   re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
10. **Persistence stays scoped** — no ambient recording of live streams; recording is an explicit,
    logged act.

**Era-variable rules** (decided per era in goal.md, not immutable): the no-ML rule (eras 5–13 keep
it; era 14 relaxes it under the tripwires of that chapter), the single-champion rule (era 16
extends it to per-regime cells under a documented rail amendment), and the intraday-only rule
(era 12 extends horizons on the bar store).

## 0.4 The config-fingerprint evolution protocol

`Config.config_fingerprint()` hashes the entire config minus an explicit exclusion set
(`apps/backend/app/config.py`), and the founding fingerprint `4d665603569b9dbf` is pinned by a
literal assertion (`apps/backend/tests/test_profile_equivalence.py`) and stamped on the founding
PnL-ledger row. *(Epoch note 2026-08-14: the founding pin was retired by the era-5D "Clean
Slate" Path B bump — the CURRENT pinned epoch is `08e471b10130e1e2`, and
`tests/test_fingerprint_epoch_retirement.py` guards the retired literal out of `apps/`. The
protocol below is unchanged.)* **Almost every era below adds Config fields.** There are exactly two lawful moves;
a weak model that improvises a third will corrupt the honesty machinery:

- **Path A — exclusion (the default)**: when a new field is read ONLY by new code paths (a new
  strategy, detector, metric, or report — never by the frozen `v1`/`default` replay), add it to the
  fingerprint **exclusion set in the same commit**, plus (i) a fingerprint-stability test proving
  the pin is unchanged and (ii) a counter-test proving the field genuinely alters the NEW path's
  output (so the exclusion isn't hiding a dead knob). Provenance duty: the new field's value must
  be embedded in the new path's own report payload (the `structure_tape_*` fields are the worked
  example of this pattern).
- **Path B — fingerprint epoch bump (rare, deliberate, operator-approved)**: when a change
  legitimately alters a value the fingerprint must cover (e.g. the card-6.4 lookahead fix changes
  level computation for everyone). Steps: (1) document the bump in the era's goal.md as a
  journey of its own; (2) update the pinned literal; (3) re-run and re-seed founding baselines;
  (4) append a ledger row noting the epoch change so no cross-epoch numbers are ever pooled;
  (5) the era's sentinel journey asserts the NEW pin. Cross-epoch comparisons are forbidden —
  treat each epoch as its own universe.
- **Never**: edit the pinned literal just to make a red test green, exclude a field that shapes
  frozen-path output, or let the pin drift silently.

## 0.5 Global weak-model traps (apply to every era; repeated per-era where acute)

| # | Trap | Rule |
|---|------|------|
| T1 | Bucketing raw timestamps by "time of day" | Engine timestamps are **logical seconds from window start**. Wall-clock = `epoch_anchor + logical_ts`, converted to **America/New_York with DST**. Raw-ts buckets are vacuous once all windows start at 09:30. |
| T2 | Treating `insufficient_sample` as failure | It is an **answer**. The honest responses are: record more data, or report "insufficient n". Never lower a min-n floor, widen a window, or pool across feeds/epochs to escape it. |
| T3 | "Fixing" immutability errors | `DatasetAlreadyRegistered` and checksum refusals are the store **working**. Never delete/re-tag/perturb data to get past them. |
| T4 | Peeking before splitting | Train/holdout/forward assignment is a **deterministic function of the date** decided before any results are computed. A model that looks at a day's PnL before assigning its split has destroyed the holdout. |
| T5 | In-sample calibration | Any threshold calibrated from data (quantiles, percentiles, personality stats) comes from **TRAIN data of PRIOR sessions only**, is frozen before holdout is touched, and its provenance is recorded. |
| T6 | Sweep explosion | Every sweep pre-registers its full candidate count in the experiment ledger (card 6.3) **before** results are seen — counting "candidates evaluated", not "candidates reported". |
| T7 | Vacuous tests | A test that passes because n<5 makes every CI span zero proves nothing. Statistical machinery is oracle-tested on a **seeded synthetic population with a known answer**. |
| T8 | Fingerprint improvisation | Only Path A or Path B of 0.4. No third move exists. |
| T9 | Vocabulary drift | Banned terms: "paper trading", "shadow trading", "annualized" anything, "expected profit", advice/imperative phrasing. The forward ledger is "**forward replay measurement**". |
| T10 | Second sources of truth | Never recompute a served value in a new code path; read it from its canonical owner. If a new value is needed, create ONE owner. |
| T11 | Quiet scope creep into frozen code | New strategies/detectors dispatch **beside** `v1`'s branch; classifier thresholds, `warmup_min_events`, and the five states are untouchable outside an explicit epoch bump. |
| T12 | Units mixing | *(Amended 2026-08-16, rapid-microscope r2 — the old universal "SIP quote sizes are round lots; trade sizes are shares" pin is superseded: Alpaca CTA/UTP displayed quote sizes are SHARES from 2025-11-03.)* Trade sizes and displayed-liquidity sizes must never be added or ratioed except under the ACTIVE dataset-level size-unit/schema-basis contract (`quote_size_unit`, rapid-validation-spec §2.6); cross-basis arithmetic fails closed when units are unverified or incompatible; legacy datasets stay `unverified` until an auditable verification act. |

## 0.6 Idea-card template legend

Research cards (the default) carry, in the heading line, a feasibility tag and an effort tag:

- **Feasibility**: `[F1]` runnable on today's committed data · `[F2]` needs the era-5 library ·
  `[F3]` needs a new data kind (vendor/purchase) · `[F4]` needs an era-variable rule relaxed
  (0.3's era-variable list).
- **Effort**: `[S]` ≤1 iteration · `[M]` 1–2 iterations · `[L]` 2–4 iterations (split if larger).

Fields: **Hypothesis** (one falsifiable sentence) · **Mechanism** (the market-structure reason it
could be true) · **Prerequisites** (cards/eras/data) · **Build** (extension points with file
paths) · **Formulas** (exact; a weaker model must not have to invent math) · **Evaluate** (which
harness, which null, what min-n, what counts as a positive) · **Kill** (the observation that ends
the idea — write the negative result to the ledger and stop) · **Traps** (the specific mistakes
this card invites).

Infrastructure cards (plumbing/UI/process) replace Hypothesis/Mechanism/Evaluate/Kill with
**Purpose** and **Acceptance**.

## 0.7 Glossary

- **R** — risk unit: per-trade result divided by the entry-to-stop distance basis. All edges are
  stated in net R (after fees/slippage) with n. **$** figures are simulated notional companions,
  never shown without R and n.
- **Dataset / split** — an immutable, checksummed recorded window of trades+quotes
  (`apps/backend/app/research/datasets.py`), tagged `train` or `holdout` at registration (era 5
  adds `forward`).
- **Bars / BarStore** — immutable OHLCV series `1m…1mo` (`apps/backend/app/research/bars.py`).
- **Aggressor side** — derived per print: quote rule (`price ≥ ask` ⇒ buy, `≤ bid` ⇒ sell), then
  Lee-Ready tick test, else `unknown` (`apps/backend/app/engine/aggressor.py`).
- **Tape states** — `buyer_control`, `seller_control`, `bid_absorption`, `ask_absorption`,
  `unclear` (`apps/backend/app/engine/classifier.py`).
- **Features** — the 13 rolling-window tape features (`apps/backend/app/engine/features.py`).
- **Levels / zones / class A-B-C** — S/R levels (swing pivots + prior-period extremes) clustered
  into confluence zones graded by distinct-timeframe breadth
  (`apps/backend/app/research/levels.py`).
- **Setups** — `absorption_reversal`, `trend_continuation`, `level_break`, `failed_move_fade`
  (`apps/backend/app/research/taxonomy.py`).
- **Backtest runner** — event-driven replay with fees, spread-fraction slippage, seeded
  random-entry null baseline, single open trade
  (`apps/backend/app/research/backtests.py`).
- **Sweep / survivor / overfit** — `pnl_scan` evaluates candidates vs champion on train, then
  holdout; survivor = holdout net R>0 AND $>0 AND n ≥ minimum; train-positive non-survivor =
  overfit (`apps/backend/app/research/pnl_scan.py`).
- **Champion pointer** — the single persisted `(strategy_id, profile)` the product treats as
  current best; moves only via the sweep's promotion writes.
- **Edge report** — read-only per-dataset ranking of the frozen champion's holdout edge
  (`apps/backend/app/research/edge_report.py`); its honest empty state is the literal
  `"no positive-edge dataset"`.
- **MFE / MAE / ternary excursions** — max favorable/adverse excursion machinery and
  +1R-first/−1R-first/neither outcomes (`apps/backend/app/research/excursions.py`,
  `studies.py`).
- **Fingerprint / epoch** — see 0.4.
- **Era / goal session / iteration / journey** — an era = one goal.md constitution executed as one
  goal-mode session of N iterations; journeys are its must-have acceptance scenarios.
- **Feed basis** — `sip` vs `iex` (and later `databento-*`); results from different feeds are
  never pooled.

---

# Part 1 — The year at a glance

Twelve research eras + the operating system. Dependency order below; the **router in Part 5.1**
picks the next eligible era at any moment — you do not need this table's order to be a schedule.

| Era | Name | Mission (one line) | Hard prerequisites | Gate to open it | Cost | Effort (iterations) |
|-----|------|--------------------|--------------------|-----------------|------|---------------------|
| 5 | The Library | Kill the data starvation honestly ($0, free-tier backfill, 15-symbol panel) | none | era 4 done (it is) | $0 | 9–12 **[SPLIT-POINT after 5.4]** |
| 6 | The Referee | Statistics strong enough to survive many candidates | 5 | library ≥ ~150 symbol-days | $0 | 9–12 **[SPLIT-POINT after 6.6]** |
| 7 | Trade Craft I | Fix the trade skeleton (stops/fills/timing) before measuring signals | 5, 6 | referee gates live | $0 | 6–8 |
| 8 | Volume Structure | Volume-derived levels into the confluence engine | 5, 6 (6.4 fix) | — | $0 | 7–9 |
| 9 | The Microscope | New tape detectors, two waves, atlas-gated | 5, 6 (atlas) | atlas published | $0 | 10–14 **[SPLIT-POINT between waves]** |
| 10 | Compression & Bar Anatomy | Classic price-action families; candle-vs-tape head-to-head | 5, 6 | — | $0 | 5–7 |
| 11 | Trade Craft II | Trailing/scale-out/re-entry (architecturally expensive) | 7 + a surviving strategy | any survivor exists | $0 | 6–9 |
| 12 | Swing Bridge | Multi-day horizons on the bar store, tape-timed entries | 5, 6 | operator OKs swing scope (already granted in principle) | $0 | 7–10 |
| 13 | Context | Index/sector bars as regime veto and RS filter | 5, 6 | — | $0 | 5–7 |
| 14 | Learning From the Tape | Cheap local ML: veto-only meta-labeling + signature retrieval | 5, 6, 7; goal.md + proposer §9 amended | operator amends the no-ML rule for the era | $0 | 7–10 |
| 15 | Depth | L2 via one-off Databento purchase; mechanism studies first | 5, 6; L1 analogue results from 9 | operator approves purchase (~$0–150, credits first) | ~$0–150 | 8–11 |
| 16 | Champion Council | Champion pointer per regime cell (documented rail amendment) | 6, 13; ≥2 surviving strategies OR 1 survivor + strong regime conditioning | operator approves rail amendment | $0 | 5–8 |

Dependency graph (arrows = "needs"):

```
5 ──> 6 ──> 7 ──> 11
      6 ──> 8
      6 ──> 9 (atlas gates wave 2)
      6 ──> 10
      6 ──> 12
      6 ──> 13 ──> 16
      6,7 ──> 14
      6,9 ──> 15
```

Standing physics of the year (why demand-driven still takes a year): **forward-OOS evidence
accrues only in calendar time.** The forward replay ledger (card 5.6) gains one row per recorded
trading day; consolidation reviews (Part 5.4) are only meaningful after weeks of accrual. Agent
effort can compress everything except elapsed market days — plan around that, not against it.

*(Amended 2026-08-16, rapid-microscope opening: the paragraph above is now scoped to
**live-confirmatory** evidence only — the Referee's genuinely-post-registration sessions and
the forward ledger. `historical_oos`-class evidence (rapid-validation-spec §0: clean-horizon
folds and sealed backfilled shards) accrues at RECORDING speed, not calendar speed — a
credentialed backfill can add months of never-inspected history in an afternoon. Only live
confirmation still requires elapsed market days.)*

---

# Part 2 — Era chapters

## ERA 5 — The Library

**Mission**: end the data starvation, honestly and for $0. Every era-3/4 result is
`insufficient sample`; the measurement machine has never had enough real data to say anything.
This era builds the recorded library every later era consumes — and because the dataset store is
**immutable**, the plumbing cards (5.1–5.4) MUST land before the first bulk recording: whatever is
recorded first is what the whole year gets.

**Why now**: it is the only era with no prerequisites, and nothing else can produce a real finding
without it. `reports/goal-session-tape_to_profit-delivered.md` already concluded: "What's left is
not more building but more data."

**[SPLIT-POINT after 5.4]** — session A = plumbing (5.1–5.4), session B = recording + labeling +
forward + UI (5.5–5.9).

---

#### Card 5.1 — Event-schema enrichment (conditions, venue, units) `[infra] [F1] [M]`

> *(Status note 2026-08-16, rapid-microscope r2: the DATA-PRESERVATION portion of this card is
> BROUGHT FORWARD as a HARD prerequisite of the rapid-microscope era's bulk recording (goal.md
> J-06 step 1 / rapid-validation-spec §7.1, trap TR-19) — optional conditions/exchange/venue
> fields land before any tranche is recorded, absent-key backward compatible, engine-ignored.
> The card's **units pin below is SUPERSEDED**: "SIP quote `bid_size`/`ask_size` are ROUND
> LOTS" stopped being universally true when Alpaca moved CTA/UTP displayed quote sizes to
> SHARES effective 2025-11-03 — the rule is now a per-dataset `quote_size_unit` contract
> stamped at record time from the dated vendor rule, with every legacy dataset `unverified`
> and all cross-unit liquidity arithmetic refused until verified
> (rapid-validation-spec §2.6, trap TR-18). The card text below stands as the historical
> record.)*

- **Purpose**: the Alpaca adapter currently discards trade condition codes and exchange/venue
  (`apps/backend/app/providers/adapters/alpaca.py` builds `RawTrade(ts, price, size)` only;
  `RawTrade`/`RawQuote` in `apps/backend/app/providers/adapters/base.py`). Without conditions,
  opening/closing auction crosses, average-price prints, and off-exchange (TRF) prints all
  masquerade as ordinary aggressive prints — poisoning block analytics (9.10), auction analytics
  (5.6), and any print-level study. Datasets are immutable, so this must precede bulk recording.
- **Build**: add OPTIONAL `conditions: list[str]` and `exchange: str` fields to `RawTrade`,
  `TradeEvent` (`apps/backend/app/providers/base.py`), and the dataset event rows
  (`apps/backend/app/research/datasets.py`). Optional = old committed fixtures still parse and
  their checksums still verify (absent key, not null-rewrite). Thread through
  `HistoricalProvider` (`apps/backend/app/providers/historical.py`) and the replay path. Document
  the **units pin** in both dataclasses' docstrings: SIP quote `bid_size`/`ask_size` are ROUND
  LOTS; trade `size` is SHARES (trap T12).
- **Acceptance**: a freshly captured fixture (`apps/backend/scripts/capture_alpaca_fixture.py`)
  round-trips conditions/exchange; all existing fixtures load byte-identically; the frozen
  `default` engine equivalence test is untouched (the engine may ignore the new fields — they are
  for research consumers).
- **Traps**: do not make the fields required (breaks every committed fixture, invites T3
  "fixes"); do not let the engine's feature/classifier code read them (frozen surface, T11).

#### Card 5.2 — The backfill recorder job + the frozen 15-symbol panel `[infra] [F1] [L]`

> *(Status note 2026-08-16: BROUGHT FORWARD into the rapid-microscope era — the recorder job,
> the deterministic sha256 split rule, and the panel below are built there (goal.md J-06), with
> two additions the era's spec owns: pre-registered recording universes (no cherry-picked
> symbol-days) and an orthogonal opaque HMAC seal assignment feeding the new Validation Vault.
> The card's ≥150-symbol-day library target is NOT satisfied by that era's ~30–50-symbol-day
> starter tranche — W1 top-ups continue toward it afterward. The card text below stands.)*

- **Purpose**: an automated, resumable, free-tier recorder that grows the library to hundreds of
  full-session symbol-days. The interactive record endpoint CANNOT do this: it runs a single-shot
  fetch under a ~6s vendor deadline (`vendor_http_timeout_seconds` /
  `vendor_call_timeout_seconds` in `apps/backend/app/config.py`) and will always time out on a
  6.5-hour window.
- **Build**: a new JobManager-pattern job (`RecorderJobManager`, twin of `BacktestJobManager` in
  `apps/backend/app/research/backtests.py`) that (a) fetches via the EXISTING chunked path
  `iter_historical_chunks` (`apps/backend/app/providers/adapters/alpaca.py`); (b) adds a
  **tick-fetch throttle** — bar fetches are already throttled (`_throttle_bar_fetch`,
  same file) but tick fetches are NOT, and the free plan allows 200 req/min; (c) checkpoints
  per-chunk so a killed job resumes without re-fetching; (d) registers each completed session
  through the existing `DatasetStore.record` path (explicit act — never the live watch path);
  (e) never requests the most recent 15 minutes (free-plan rule, already a J-01 constraint in
  `docs/goal.md` lineage); (f) assigns the split at registration by the deterministic date rule
  below. Also record matching **bar series** (1m…1d) per symbol via the existing BarStore path.
- **The panel** (frozen here; tiers matter — record ALL tiers, analyze per tier):
  - Tier A mega-cap (5): `PG` (continuity with all prior eras), `AAPL` (fixture continuity),
    `MSFT`, `NVDA`, `JPM` — sector spread: staples, tech, semis, financials.
  - Tier B mid-cap (5, provisional — re-screen at recording time): `DKNG`, `ETSY`, `AFRM`,
    `SOFI`, `RKLB`. **Screen criteria (the criteria are the contract; the names are
    provisional as of 2026-07)**: market cap $2–20B; price $15–100; 30-day ADV ≥ 3M shares;
    median RTH spread ≤ 8 bps; primary US listing; no pending M&A. Record the screen output
    next to the panel registration.
  - Tier C ETFs (5): `SPY`, `QQQ`, `IWM`, `XLF`, `XLE` — regime/context references (era 13
    reuses them).
  - Optional stress symbol: `GME` (fixture continuity; high-vol special case; never pooled with
    tiers).
- **Volume reality**: ultra-liquid names (AAPL/SPY/QQQ) can print millions of quotes/session; if
  full-session JSON is impractical (see 5.3), the sanctioned fallback is **curated windows**:
  09:30–11:00 + 15:00–16:00 ET, recorded as two datasets with window provenance — session-anchored
  ideas (8.2, 9.1) then apply only to symbols with full sessions. Record mid-caps and PG
  full-session first; they are the primary research tier.
- **Split rule (trap T4)**: `holdout` iff `sha256(f"{symbol}:{YYYY-MM-DD}").hexdigest()` last hex
  digit ∈ {0,1,2} (≈19% holdout), else `train` — decided at registration, before any replay,
  never revisited. Top-up recordings of days after the era-5 recording date register as
  `forward` (card 5.8).
- **Targets**: ≥ 60 sessions per Tier-B symbol + PG; ≥ 20 per remaining Tier-A; ≥ 20 per ETF
  (bars only is acceptable for ETFs if tick volume is impractical); spanning ≥ 3 months of
  distinct dates. Free-plan math: historical SIP is available beyond 15 minutes at 200 req/min —
  a full session in ~10k-event pages is hundreds of requests per symbol-day; budget multi-day
  wall-clock and let the job run unattended (operator action: leave it running overnight).
- **Acceptance**: library summary endpoint reports per-symbol/split/regime counts matching
  targets (or an honest shortfall note); every dataset passes checksum verification; a killed
  and resumed job produces byte-identical registrations.
- **Traps**: T3 (immutability errors are the store working); T4 (split before results); never
  record via the live cockpit stream (scoped-persistence rail); do not "optimize" by weakening
  the double-checksum on write.

#### Card 5.3 — Library index & scale `[infra] [F1] [M]`
- **Purpose**: `DatasetStore.list()` currently parses and checksum-verifies EVERY file
  (`apps/backend/app/research/datasets.py`); the committed 10-minute PG window is ~1.25MB, a
  full session is tens of MB, and a 300-day library is gigabytes — every sweep/edge-report
  currently calls `list()` first. Without an index, era 6 times out against its own store.
- **Build**: a manifest file (one JSON: id → {meta, checksum, byte_length}) maintained
  atomically on every registration; `list()` reads the manifest and **spot-verifies** a seeded
  deterministic subsample (e.g. 3 files per call) plus ALWAYS fully verifies any file actually
  opened for replay. Full-verify remains available (`verify_all()`, used by the sentinel journey
  and the quality gate). Optional: gzip event payloads (`.json.gz`) for new datasets —
  transparent on read, old files untouched.
- **Acceptance**: `list()` on a 300-dataset library completes in < 1s; replay still
  full-verifies; a corrupted file is still caught (by replay-verify always, and by
  `verify_all()` in the sentinel).
- **Traps**: NEVER weaken verification on the replay path — the manifest accelerates listing,
  it does not replace content verification where data is consumed (T3-adjacent).

#### Card 5.4 — Multi-dataset promotion pooling `[infra] [F1] [M]`
- **Purpose**: `pnl_scan._promote` refuses automatic promotion unless there is EXACTLY one train
  and one holdout dataset (`apps/backend/app/research/pnl_scan.py`, the
  `len(train_datasets) != 1 or len(holdout_datasets) != 1` guard). The moment 5.2 lands, the
  sweep can evaluate but never promote. This card generalizes the gate to the pooled shape
  everything later assumes.
- **Build**: pooled promotion = summed holdout delta positive on net R AND net $ across ALL
  holdout datasets, with pooled n ≥ `promotion_min_sample_size`; the ledger row
  (`apps/backend/app/research/pnl_ledger.py`) gains per-dataset breakdown in its payload
  (additive key) while keeping the existing single-row append semantics; `_promote`'s
  exactly-one guard becomes the pooled rule. Era 6 will tighten this gate further (CI + BH);
  build it so the gate is a single function with one owner.
- **Acceptance**: on a synthetic 3-train/2-holdout fixture library, a known-good candidate
  promotes exactly once with a per-dataset breakdown row; a train-only winner is labeled
  overfit; zero-survivor runs exit 0 with the honest note.
- **Traps**: keep the two ordered writes (ledger row THEN pointer move) exactly as documented in
  `pnl_scan.py`'s module docstring; `pnl_scan` stays the ONLY caller of
  `set_champion_pointer` (source-scan enforced).

#### Card 5.5 — Day-type regime taxonomy + intraday RVOL curves `[infra+stats] [F2] [M]`
- **Purpose**: label every recorded day so every later edge number can be conditioned on regime
  ("edge exists only on trend days" is a first-class finding, and "no edge anywhere" is only
  credible if regimes were separated).
- **Formulas** (all from bars; day D's own label uses day-D completed bars — see trap):
  - `gap_pct = (open_D − close_{D−1}) / close_{D−1}`; classes: |g| < 0.3% `none`, 0.3–1%
    `small`, 1–3% `medium`, > 3% `large` (thresholds config-owned).
  - True range `TR_D = max(high−low, |high−close_{D−1}|, |low−close_{D−1}|)`;
    `ATR14` = Wilder smoothing (`ATR_D = (13·ATR_{D−1} + TR_D)/14`).
  - Trend day: `|close−open|/(high−low) ≥ 0.7` AND `(high−low) ≥ 1.3·ATR14_{D−1}`.
    Range day: `|close−open|/(high−low) ≤ 0.35` AND `(high−low) ≤ 0.9·ATR14_{D−1}`.
    Else `mixed`. Combined with gap class and direction → the day-type label set.
  - `RVOL_D = volume_D / median(volume_{D−20..D−1})`; buckets: < 0.7 `low`, 0.7–1.5 `normal`,
    > 1.5 `high`.
  - Intraday RVOL curve: for ET minute-of-day m, `rvol_m = vol_m / median(vol_m over the prior
    20 sessions of the same symbol)` — stored per session, powers 9.4's burst baseline and
    6.5's time-of-day work.
- **Build**: a deterministic labeling module beside `apps/backend/app/research/levels.py`
  (e.g. `research/regimes.py`), one canonical endpoint (`/research/regimes/<symbol>`), labels
  persisted per dataset id (additive store payload or sidecar keyed by dataset id — ONE owner),
  MCP proxy via the generic pattern in `apps/backend/app/mcp/__init__.py`.
- **Acceptance**: every library dataset carries a day-type, gap class, RVOL bucket; labels
  byte-stable across reruns; a fixture day with hand-computed labels matches exactly.
- **Traps (acute)**: a day's trend/range label is an **end-of-day fact** — legal for post-hoc
  conditioning of results, ILLEGAL as an entry-time feature (T5). Entry-time-legal variants
  must be explicitly as-of: gap class (known at open), RVOL-so-far, ATR from D−1. Label which
  is which in the endpoint payload (`entry_time_legal: true/false` per field). T1 for
  minute-of-day (ET via `epoch_anchor`).

#### Card 5.6 — Data-quality gate + scheduled-news calendar `[infra] [F2] [M]`
- **Purpose**: bad windows must be flagged before they contaminate measurements; scheduled-news
  days (earnings) behave differently and must be separable.
- **Formulas / heuristics**: median spread bps (flag > 50 or ≤ 0); crossed/locked-quote fraction
  (flag > 5%); possible-halt = no trades AND no quote updates for > 60s during RTH (flag);
  LULD-suspect = trade-to-trade move > 5% within 1s (flag); aggressor-confidence = fractions
  classified by quote rule / tick test / unknown (`apps/backend/app/engine/aggressor.py`
  derivation; flag unknown > 10%); condition/venue composition once 5.1 lands (odd-lot %,
  TRF %, auction prints present/absent).
- **Build**: a quality module + one endpoint; flags stored beside the regime labels (same
  owner); flagged datasets stay in the library but every downstream report EXCLUDES flagged
  datasets by default and says so (config toggle to include). Earnings calendar: committed CSV
  per panel symbol (`apps/backend/.data/calendars/earnings.csv`, columns
  `symbol,date,timing(before_open|after_close)`), maintained quarterly by the operator (manual,
  ~15 min — an explicitly operator-gated task); datasets on D−1/D/D+1 get an
  `earnings_window` tag.
- **Acceptance**: quality report runs across the whole library; a synthetically corrupted
  fixture triggers each flag exactly; earnings-window tags visible in the datasets page.
- **Traps**: flags EXCLUDE by default but never delete (T3); the calendar is data, not a fetch —
  no new vendor dependency for it.

#### Card 5.7 — Economic tradeability scoring `[stats] [F2] [S]`
- **Hypothesis**: some panel symbols cannot host any honest edge at retail cost assumptions
  because round-trip costs exceed a class-stop's R denominator.
- **Mechanism**: an edge in R is only meaningful if 1R ≫ round-trip cost; wide-spread symbols
  make small-stop classes structurally untradeable.
- **Prerequisites**: 5.2 library (spread measurements per symbol).
- **Build**: per symbol: `median_spread_bps`; one-way cost bps
  `= 0.5 · slippage_fraction · median_spread_bps + fee_bps` where
  `fee_bps = strategy_fee_per_share / price · 10⁴`; round-trip `cost_R(stop_bps) =
  2 · one_way_bps / stop_bps`. Tradeable at class X iff `cost_R(class_stop_bps) ≤ 0.35`
  (config). Report = a per-symbol × per-class tradeability matrix on the library summary
  endpoint.
- **Evaluate**: descriptive — the matrix itself is the deliverable, and every later per-class
  edge report prints the matrix cell beside the result.
- **Kill**: n/a (a lens, not a bet).
- **Traps**: use TRAIN-split medians only (T5); the matrix conditions interpretation, it never
  silently filters candidates (that would be an unregistered sweep dimension, T6).

#### Card 5.8 — `forward` split + champion forward replay ledger `[infra] [F2] [M]`
- **Purpose**: true out-of-sample-by-time evidence. A strategy validated on holdout can still
  fail forward; an append-only forward record accumulates the strongest genuinely-new-time
  evidence — because those observations did not exist when the strategy was frozen — and it is
  the only evidence that directly tests whether an effect still exists in the CURRENT/future
  market regime. *(Amended 2026-08-16, rapid-microscope opening: the original "the only
  evidence that cannot be overfit" wording predates the rapid era's sealed/clean historical
  OOS class — sealed `historical_oos` evidence under a frozen spec is also independent of the
  spec's authoring, but it tests past regimes, not the current one; the two claims are served
  separately and neither substitutes for the other. Consistent with the Part-1
  standing-physics amendment: only `live_confirmatory` evidence is calendar-constrained.)*
- **Build**: (a) add `forward` to `VALID_SPLITS` (`apps/backend/app/research/datasets.py`) —
  additive; (b) recorder top-up mode registers post-era-5 days as `forward`; (c) a job replays
  the CURRENT champion once on each new forward dataset and appends one row to a new
  append-only **forward ledger** (pattern-copy of `apps/backend/app/research/pnl_ledger.py`:
  one row per dataset id, duplicate append refused), served at a canonical endpoint + MCP
  proxy + a "Forward record" section on `/performance`
  (`apps/frontend/app/performance/page.tsx`); (d) **graduation rule**: at a consolidation
  review (Part 5.4), forward datasets older than 90 days graduate IN BULK (all-or-none, by
  date only) into train/holdout via the SAME date-hash rule as 5.2 — never cherry-picked.
- **Acceptance**: recording a new forward day auto-appends exactly one forward-ledger row;
  rerunning is refused as duplicate; `/performance` shows the forward record with n, net R,
  net $, and the simulated-register disclaimer verbatim.
- **Vocabulary (T9)**: this is **forward replay measurement** — the words "paper" and "shadow"
  must not appear in code, payloads, UI, or docs for this feature.
- **Traps**: graduation is bulk + date-hash (T4); the forward ledger never feeds promotion
  directly (promotion stays a train/holdout act; forward is a report of record).

#### Card 5.9 — Library health & datasets UI page `[infra/polish] [F2] [M]`
- **Purpose**: the operator currently cannot SEE the library (datasets/backtests/bars/levels
  have no browser surface — `README.md` capabilities list). Research a human can't inspect
  erodes trust.
- **Build**: a `/datasets` page in `apps/frontend/app/` (pattern: `performance/page.tsx`;
  NavBar entry comes from `GET /meta/ui-routes` — extend its owner, not the client): table of
  datasets (symbol, date, split, regime labels, quality flags, event counts, feed) + the
  library summary (counts per symbol×split×regime, tradeability matrix from 5.7). Read ONLY
  canonical endpoints; zero client-side recomputation (T10).
- **Acceptance**: browser-qa journey: open `/datasets`, filter by symbol, see counts matching
  the API byte-for-byte; flagged datasets visibly badged.

**Era-5 kill test**: if after the throttle/index work a mid-liquidity full session STILL cannot be
recorded end-to-end on the free plan (persistent 429/timeout), fall back to curated windows
(sanctioned in 5.2) and record the limitation in the status table; if > 20% of recorded days fail
the 5.6 quality gate, the free vendor path is inadequate — that finding accelerates the era-15
purchase decision. A forward ledger showing sustained negative champion R is a finding about the
champion, not a failure of this era.

**Era-5 anti-goal additions**: recording is explicit and job-scoped (never ambient); split
assignment is date-deterministic and precedes any replay; no dataset deletion/re-tagging; the
recorder never requests the most-recent-15-minutes window; "forward" vocabulary per T9.

---

## ERA 6 — The Referee

**Mission**: make the statistics strong enough that the coming eras' many candidates cannot
manufacture a false champion. Today's gate (holdout R>0 AND $>0 AND n≥5) is honest for TWO
candidates; it will not survive twenty. Build the referee BEFORE the signal factories.

**Why now**: eras 7–14 generate dozens of pre-registered candidates. Multiple-testing correction,
CIs, cost sensitivity, and the atlas must exist first, or every later "survivor" is suspect.

> **ERA-6 OPENING NOTE (2026-08-14, session `referee`, under §5.6 "goal.md wins").** The era
> opens against a repository this chapter did not foresee: the Desk (Era B) and the Playbook
> (Era B2, plus the R-4 band-context interlude) built a SECOND evidence family — bar-measured
> Playbook occurrences (210 append-only records / 156 sessions; 3,222 signals at the current
> detector basis) — while the tick library this era's gate names was never built (Card 5.2:
> ~12 partial 2.5-hour windows on disk vs the "≥ ~150 symbol-days" gate). The gate is therefore
> re-scoped PER EVIDENCE FAMILY, honestly: the Referee core (6.2-as-amended, 6.3-as-amended,
> the 6.6 matched-null concept) opens NOW against the Playbook family + a strategy-family
> adapter (expected honest verdict at today's tick corpus: `insufficient_sample`); the
> tick-dependent lenses (6.7 costs, 6.9 atlas, 6.10 loser mining) and the strategy-sweep cards
> (6.1 metrics, 6.4 Part 2 walk-forward, 6.5, 6.8, 6.11) stay gated on their own data and are
> NOT smuggled in. **Card 6.4 Part 1 (the forming-bar as-of fix) is explicitly DEFERRED by
> operator decision 2026-08-14**: the defect is real and still live (`levels._bars_as_of` keeps
> `epoch ≤ as_of`), it is disclosed as a served `basis_caveats` entry on strategy-family
> evidence, and the fix remains this card — the opening gate of the next structure-measurement
> era. The era's constitution is [`docs/goal.md`](goal.md); its statistical rulebook is
> [`docs/referee-statistical-spec.md`](referee-statistical-spec.md).

**[SPLIT-POINT after 6.6]** — session A = gates (6.1–6.6), session B = lenses (6.7–6.11).

---

#### Card 6.1 — Metrics v2 `[stats] [F1] [S]`
- **Hypothesis**: n/a (measurement plumbing with exact definitions).
- **Build**: extend `_aggregate()` in `apps/backend/app/research/backtests.py` (additive keys
  only — existing payloads byte-stable under golden tests means new keys must be added in the
  same deterministic sorted-key render; expect golden-file updates, which is a lawful test
  refresh, not a behavior change).
- **Formulas** (all on per-trade **net R**, all unitless, NONE annualized):
  `profit_factor = Σ(wins) / |Σ(losses)|` (∞-safe: null when no losses);
  `expectancy = mean(R)`; `stdev_r = sample stdev`; `sharpe_pt = mean/stdev` (per-trade);
  `downside_dev = sqrt(mean(min(R,0)²))`; `sortino_pt = mean/downside_dev` (null-safe);
  `max_consec_losses`; `exposure = Σ(holding_seconds)/Σ(dataset_seconds)`.
- **Evaluate**: golden fixture with hand-computed values; a **guard test asserting the string
  "annualized" appears nowhere in research payloads** (this repo's guard-test idiom).
- **Kill**: n/a.
- **Traps**: per-trade only (T9 — annualizing simulated R is an implied live claim); null-safe
  division everywhere; keys sorted for byte-identical renders.

#### Card 6.2 — Seeded bootstrap CIs + promotion gate v2 `[stats] [F1→F2] [M]`

> **AMENDED 2026-08-14 (era-6 opening; statistical correction — the original procedure below is
> preserved for the record but is superseded where it conflicts).** Two corrections, canonical in
> [`docs/referee-statistical-spec.md`](referee-statistical-spec.md):
> 1. **The bootstrap p-value is retracted.** `p = (1 + #{resample_mean ≤ 0})/(B + 1)` over
>    ordinary resamples is a CI-inversion probability centered at the OBSERVED mean — not the
>    probability of the observed statistic under H0. Its size under a true null is uncontrolled
>    for skewed, heavy-tailed, clustered data at modest n, and BH's FDR guarantee assumes valid
>    (super-uniform) p-values. Bootstrap machinery is CI-ONLY; every p that feeds BH comes from a
>    null-calibrated randomization test (within-cluster group-label permutation; spec §3), proven
>    by seeded oracles. "Resample trades, not days" is likewise superseded for the Playbook
>    family: cluster-level (session) resampling and cluster-aware testing are first-class, not a
>    future variant.
> 2. **The seed is not a Config field.** `bootstrap_seed` via Path A is superseded by the
>    era-B2/desk pattern: a module-constant seed (`REFEREE_SEED`) embedded in the procedure's own
>    parameters blob and hashed into its result identity — zero Config fields, fingerprint
>    untouched by construction. Path A remains the fallback if a Config field ever becomes
>    genuinely necessary.
> Gate v2's SHAPE stands (survivor gate AND interval AND BH membership) and is implemented in
> era 6 as the fail-closed promotion certificate interlock (spec §8): promotion requires a valid
> candidate-specific Referee certificate; sweep computation and survivor labelling keep working
> without one; no bypass exists.

- **Hypothesis**: point-estimate positivity at small n is noise; interval-based gating changes
  which candidates survive.
- **Procedure (original text, superseded per the amendment above)**: B = 10,000 resamples,
  seed = new config `bootstrap_seed` (Path A exclusion + counter-test per 0.4). Each resample:
  draw n trades with replacement, record `mean(net R)`. `CI95 = [P2.5, P97.5]` of the resample
  means; one-sided `p = (1 + #{resample_mean ≤ 0}) / (B + 1)`. Report CI and p beside every
  aggregate.
- **Gate v2**: survivor requires (pooled 5.4 gate) AND `CI95_low > 0` AND the 6.3 BH pass.
  Expect a long no-promotion period — **that is the system working** (do not loosen; T2).
- **Build**: one bootstrap module with one owner (e.g. `research/statistics.py`), consumed by
  `pnl_scan.py`, `edge_report.py`, and the forward ledger job. *(Era 6 ships this as
  `research/referee_stats.py`.)*
- **Evaluate (oracle, trap T7)**: seeded synthetic populations with KNOWN answers — all-+1R
  (CI excludes 0), zero-mean (CI spans 0 ≈ 95% of seeds), known-mean-0.2R at n=100 (CI covers
  0.2). The oracle test is the acceptance; fixture-only tests prove nothing at n<5. *(Era 6
  extends the oracle set with null-calibration, clustered-failure, and mis-sizing
  demonstrations; spec §6.)*
- **Kill**: n/a (referee machinery; its kill is failing its own oracle — then it must not ship).
- **Traps**: T7; seeds recorded and streamed per row, never wall-clock; CI-inversion is never a
  p-value (the amendment's correction #1).

#### Card 6.3 — Experiment registry (multiple-testing ledger) + edge dashboard `[stats+infra] [F1] [M]`
- **Hypothesis**: without a trial ledger, the year's true candidate count is unknowable and
  every later "discovery" is statistically uninterpretable.
- **Build** *(AMENDED 2026-08-14, era-6 opening: the store design below is superseded — era 6
  ships the registry as append-only sibling JSON stores on the desk store pattern
  (`referee_registry.py`: immutable family + hypothesis + withdrawal + certificate records,
  appended evaluation records, adjudication snapshots; status DERIVED by fold, never updated in
  place — strictly more auditable than update-to-evaluated rows; spec §5). The pre-registration
  protocol and denominator rule below stand verbatim.)*: new append-only table `experiments`
  (schema migration in `apps/backend/app/research/store.py`, next version, following the
  `pnl_ledger` single-writer pattern): row = `{sweep_id, registered_wall_ts, candidate_id,
  family, params_hash, split_basis, status(planned|evaluated), result_summary(JSON), p_value}`.
  **Pre-registration protocol (T6)**: a sweep writes ALL its planned candidate rows BEFORE the
  first backtest runs; the BH denominator is the count of planned rows of that sweep —
  "evaluated", never "reported".
- **BH procedure (exact)**: sort the sweep's one-sided p-values ascending `p_(1)…p_(m)`;
  `k* = max{k : p_(k) ≤ (k/m)·q}` with `q = 0.10` (config, fixed BEFORE the sweep);
  BH-survivors = candidates 1…k*. Promotion additionally requires membership here.
- **Polish**: an `/edge` dashboard page — PnL ledger + edge report + forward ledger + registry
  counts, each read verbatim from its canonical endpoint ("is anything working yet?" at a
  glance).
- **Evaluate**: oracle test — a synthetic sweep of 20 known-null candidates + 1 known-positive:
  BH admits ≈ the positive only, across seeds.
- **Kill**: n/a.
- **Traps**: T6 (the denominator is planned count); q fixed pre-sweep; registry rows immutable
  (append/update-to-evaluated only, no deletes).

#### Card 6.4 — Walk-forward robustness + the forming-bar as-of fix `[stats+fix] [F2] [M]`

> *(Status note 2026-08-14: Part 1 verified still live on `main` and DEFERRED out of era 6 by
> operator decision — see the era-6 opening note. Until the fix lands, strategy-family referee
> evidence carries the forming-bar `basis_caveats` disclosure.)*

- **Part 1 — the fix (do this FIRST; everything in eras 7–12 stacks on it)**:
  `_bars_as_of` in `apps/backend/app/research/levels.py` keeps every bar with
  `epoch ≤ as_of` — for INTRADAY timeframes this admits the still-forming bar, whose stored
  high/low/close embed up to a full bar-length of future within-bar information. Pivot CENTRES
  are already safe (they need `lookback` bars after them), but the forming bar still
  participates as a strictness NEIGHBOUR and in `_touch_count` — so a level computed as-of
  15:10 can be suppressed or strengthened by 15:10–16:00 prices. **Fix**: for intraday
  timeframes keep a bar only if `epoch + timeframe_seconds ≤ as_of` (the completed-bar rule
  the prior-period path already applies). Add a synthetic regression test: a forming bar whose
  late extreme would flip a pivot/touch must NOT affect the as-of output.
- **Fingerprint/basis note**: this is a CODE change, not a Config change — the pinned
  fingerprint does not move, and `v1`/`default` (which consume no levels) stay byte-identical.
  But `structure_tape`-family measurements change: stamp `levels_basis: "v2"` into
  backtest/scan payloads for level-consuming strategies and never compare v1-basis numbers
  with v2-basis numbers (0.4's epoch discipline, applied to a code basis).
- **Part 2 — walk-forward robustness report**: parameters here are config-enumerated (no
  fitting), so walk-forward validates STABILITY, not tuning: order train datasets by date;
  folds = expanding origin with a 1-CALENDAR-DAY embargo between fold-end and validation day;
  per candidate report `fold_consistency = fraction of folds with positive delta`. Added to
  the scan report; read as a robustness lens beside `robust/speculative`.
- **Evaluate**: fix = the synthetic regression test; walk-forward = golden fixture with
  hand-checkable folds.
- **Kill**: n/a.
- **Traps**: folds partition TRAIN days only — holdout days never enter a fold (T4); the
  frozen split tags are never re-tagged (folds are computed at run time, not stored as
  splits); embargo is in calendar days between datasets, not logical seconds (T1).

#### Card 6.5 — Regime × time-of-day conditioned edge report `[stats] [F2] [M]`
- **Hypothesis**: the champion's edge (or its absence) is regime-concentrated; unconditioned
  aggregates hide cells where an edge exists (or where losses concentrate).
- **Build**: extend `apps/backend/app/research/edge_report.py`: group per-trade results by
  `(day_type, tod_bucket)` with ToD buckets `open` 09:30–10:30, `mid` 10:30–15:00, `close`
  15:00–16:00 ET (epoch_anchor conversion, T1); per cell report n, net R, CI (6.2), and an
  `insufficient` flag below min cell n (config, default 5). Uses 5.5 labels.
- **Evaluate**: descriptive report; a cell is a FINDING only if its CI clears 0 AND it was
  pre-registered as a hypothesis in the 6.3 registry (post-hoc cells are hypothesis
  generators, labeled so).
- **Kill**: n/a (lens).
- **Traps**: day-type is post-hoc conditioning (5.5's trap); do not let a post-hoc cell
  silently become an entry filter — that is a NEW candidate for a pre-registered sweep (T6).

#### Card 6.6 — Null-baseline upgrades `[stats] [F2] [M]`

> *(Scope note 2026-08-14: era 6 ships this card's CONCEPT for the Playbook family — the
> ToD-matched null `referee-null-tod-v1` and the context-matched null `referee-null-context-v1`,
> spec §4, measured through the desk forward rail's own conventions. The strategy-side builds
> below — the `_null_trades` time-matched and random-levels variants — remain future work gated
> on the tick library and are unchanged here.)*

- **Hypothesis**: the current uniform-random-entry null is too weak; matched nulls isolate
  WHAT the strategy adds.
- **Build** (both beside `_null_trades()` in `apps/backend/app/research/backtests.py`, both
  seeded, both through the SAME exit/fee/slippage code path):
  - **Time-matched null**: random entries drawn (seeded) to match the candidate's entry
    time-of-day bucket histogram — kills "the edge is just the open" artifacts.
  - **Random-levels null**: for level-consuming strategies, replace the real level set with
    uniform-random levels (seeded) within the day's price range, same count and class mix,
    then run the SAME strategy — if real-levels edge ≤ random-levels edge, S/R **placement**
    adds nothing (the whole era-4 hypothesis, finally isolable).
- **Evaluate**: each null is reported beside the strategy in scan/edge payloads; a candidate's
  edge claim must beat ITS matched null, not only the uniform null.
- **Kill**: n/a (referee machinery).
- **Traps**: same exit/fee path as real trades (the existing null's discipline); seeds
  config-owned; random levels get the same A/B/C class distribution (else the comparison
  confounds class scaling).

#### Card 6.7 — Cost-model calibration & sensitivity `[stats] [F2] [M]`
- **Hypothesis**: the assumed cost model (0.5 × spread slippage + per-share fees) materially
  understates or overstates real costs; edges that die at 2× assumed costs are not edges.
- **Build**: (a) calibration: at each simulated fill, measure `effective_spread_bps =
  2·|fill_price − mid_at_decision|/mid · 10⁴` from recorded quotes; report its distribution
  vs the assumed model per symbol; (b) sensitivity: rerun aggregates at
  `strategy_slippage_spread_fraction × {1, 2, 3}` (three deterministic reruns) — every scan
  and edge report gains a `costs` block `{x1: net_r, x2: net_r, x3: net_r}`.
- **Evaluate**: a promotion-grade survivor must stay positive at ×2 (config-gated; the ×3
  number is reported, not gated).
- **Kill**: n/a — but note the finding class: "edge exists gross, dies at ×1 costs" is a REAL
  and reportable result (it feeds contingency C3, Part 5.5).
- **Traps**: mid from the quote AT the decision event, not a later quote (T-lookahead);
  sensitivity reruns share seeds with the base run.

#### Card 6.8 — Cross-symbol replication gate `[stats] [F2] [S]`
- **Hypothesis**: a real microstructure edge generalizes directionally to at least one sibling
  symbol; a single-symbol "edge" at these sample sizes is indistinguishable from luck.
- **Build**: in the scan, after a candidate passes all other gates on the primary symbol,
  run it unchanged (no re-tuning) on every other panel symbol with library data; require
  positive holdout delta on ≥ 1 sibling; otherwise label `single_symbol: true` and block
  promotion (config flag `promotion_require_replication`, default true).
- **Evaluate**: part of the promotion gate; reported per sibling in the scan payload.
- **Kill**: n/a.
- **Traps**: replication uses the SAME frozen parameters (any per-symbol re-tuning is a new
  registered candidate, T6); tier context matters — report the sibling's tier with the result.

#### Card 6.9 — Feature→outcome atlas + state-calibration atlas `[stats] [F2] [L]`
- **Hypothesis**: of the 13 engine features (and each later detector), only a few carry any
  forward information at any horizon — and the five tape states have never been scored as
  predictions.
- **Mechanism**: rank-IC is the cheapest honest screen for "is there anything here at all";
  building detectors (era 9 wave 2) for atlas-zero families is wasted work.
- **Build**: a study-harness extension (`apps/backend/app/research/studies.py` JobManager
  pattern): per dataset, sample the feature vector at every arm-eligible event (extend the
  path observer ONCE, additively — see era-9 infrastructure note); forward mid-return
  `r_h = (mid_{t+h} − mid_t)/mid_t · 10⁴` for h ∈ {10, 30, 60, 120}s.
- **Formulas**: per dataset × feature × h: Spearman
  `ρ = 1 − 6·Σd_i²/(k(k²−1))` over the k sampled events (tie-corrected implementation);
  aggregate per symbol × regime: `median ρ`, IQR, `sign_consistency = fraction of datasets
  sharing the median's sign`. **State calibration**: `P(r_h > 0 | state, confidence bucket)`
  vs the unconditional base rate, with n per cell — report as lift.
- **Evaluate**: the atlas is a descriptive deliverable (JSON + rendered MD under `reports/`).
  **Era-9 wave-2 gate (config-owned)**: a family qualifies iff `|median ρ| ≥ 0.03` AND
  `sign_consistency ≥ 0.7` on TRAIN datasets across ≥ 60% of symbols with data.
- **Kill**: if EVERY feature and state shows |median ρ| < 0.02 with no regime cell exceeding
  0.05 on train — the tape features as built carry no measurable short-horizon information;
  era 9 wave 2 is dead as specified, and the honest routes are era 8 (structural levels),
  era 12 (longer horizons), or contingency C0.
- **Traps**: TRAIN datasets only (holdout stays sealed for strategies, T5); sampled events
  must be arm-eligible moments, not every tick (else the IC measures autocorrelation of dense
  sampling); forward returns from mid, not last (bid-ask bounce artifact).

#### Card 6.10 — Loser mining `[stats] [F2] [M]`
- **Hypothesis**: the champion's losing trades share identifiable pre-entry traits
  (regime/ToD/class/approach) whose absence in winners is quantifiable — a deterministic
  hypothesis generator for filters.
- **Build**: analytics job over champion TRAIN trades: for each trait dimension (day-type,
  ToD bucket, zone class, approach speed = signed mid-return over the 60s before arm, spread
  regime at arm), compute the odds ratio
  `OR = (losers_with / losers_without) / (winners_with / winners_without)` with a bootstrap
  CI (6.2 machinery). Output: ranked trait list with ORs, n, CIs → written to `reports/` as
  the era's hypothesis feed.
- **Evaluate**: descriptive. Every filter idea it generates becomes a PRE-REGISTERED sweep
  candidate later (T6) — this card never applies a filter itself.
- **Kill**: all ORs' CIs span 1 → losses are trait-random at current n; nothing to mine yet;
  revisit after the library doubles.
- **Traps**: train only; traits computed as-of entry (T5); multiple-testing applies to the
  MINING too — report the trait count as the registry's planned count for this analysis.

#### Card 6.11 — Symbol personality profiling `[stats] [F2] [M]`
- **Hypothesis**: panel symbols split into mean-reverters and trenders at intraday horizons,
  and setup families perform differently across that split.
- **Formulas**: on 1m bar log returns per session (TRAIN sessions only), variance ratio
  `VR(q) = Var(r_t + … + r_{t−q+1}) / (q · Var(r_t))` computed with overlapping windows,
  q ∈ {5, 15, 30}; per symbol take the median across sessions. Lag-1…5 autocorrelations of
  1m returns, median across sessions. Classification (config thresholds): `mean_reverter` if
  median VR(15) < 0.85; `trender` if > 1.15; else `neutral`. Frozen per fingerprint/data
  epoch with provenance.
- **Build**: extends 5.5's regimes module (same owner); personality appears as a conditioning
  dimension in 6.5's report and the atlas.
- **Evaluate**: descriptive; a finding only via pre-registered conditioned sweeps later.
- **Kill**: if VR ≈ 1 everywhere (all neutral), personality carries nothing — drop the
  dimension.
- **Traps**: T5 (train, frozen, provenance); log returns; overlapping-window variance needs
  the standard small-sample correction — document the exact estimator in code.

**Era-6 kill test**: this era cannot "fail by finding nothing" — its machinery is judged by its
own oracles (6.2/6.3): if the oracles cannot be reproduced, the machinery must not ship.
Secondary honest stop: a power analysis (given achievable n from the library and observed trade
rates) showing the minimum detectable edge exceeds any plausible tape edge ⇒ stop testing
candidates and route to library growth (Part 5.4 workstream W1) — record that in the status
table.

**Era-6 anti-goal additions**: no annualized metrics anywhere (guard test); registry rows
immutable; BH `q` and all gate thresholds fixed before each sweep; oracle tests mandatory for
every statistical procedure; `levels_basis` stamped on level-consuming results after the 6.4
fix.

---

## ERA 7 — Trade Craft I

**Mission**: fix the trade SKELETON — stops, fills, and timing — before the signal eras, so every
later confirm/veto delta is measured once, against the final skeleton, instead of twice. Exits and
fills change the R denominator of everything downstream.

**Prerequisites**: era 5 (library), era 6 (gates live). Craft variants are **new registered
candidate strategies** (config-owned branches beside `v1`/`structure_tape` in
`Config.strategy_definition`, swept via `pnl_scan --strategy`), never mutations of frozen
definitions.

---

#### Card 7.1 — Excursion-driven stops `[craft] [F2] [M]`
- **Hypothesis**: stops placed at empirical MAE quantiles of winning trades beat the uniform
  per-class bps stops on holdout.
- **Mechanism**: the current class stops (1/5/10 bps) are hand-set; recorded MFE/MAE
  distributions (`apps/backend/app/research/excursions.py`) know how much adverse excursion
  actual winners survive — a stop tighter than winners need donates R to noise; looser donates
  it to losers.
- **Build**: from TRAIN champion trades per setup×class, take the MAE distribution of trades
  that ended positive; candidate stop = MAE quantile q ∈ {0.75, 0.90} (two pre-registered
  candidates), converted to bps on the entry basis, **frozen with provenance** (dataset ids +
  epoch) before holdout runs. New strategy variants dispatch in
  `apps/backend/app/research/backtests.py` beside `_class_scaled_invalidation`.
- **Evaluate**: `pnl_scan --strategy` vs champion; gates 6.2/6.3/6.7/6.8 apply; registry rows
  pre-registered (2 candidates).
- **Kill**: neither quantile variant beats the champion's uniform stops on pooled holdout →
  empirical stops dead for this strategy generation; record and keep uniform stops.
- **Traps**: T5 is the whole card — quantiles from TRAIN only, frozen, never recomputed on the
  data being evaluated; winners-only MAE (using all trades bakes the current stop into the
  estimate).

#### Card 7.2 — Entry fill realism: limit-at-level `[craft] [F2] [M]`
- **Hypothesis**: limit entries at the zone edge (vs market-on-confirm) improve net R after
  accounting for missed fills.
- **Mechanism**: market-on-confirm pays the spread and slippage at the worst moment (post-
  confirmation urgency); a resting limit at the level collects the spread — but misses the
  best trades (price never comes back). Which effect wins is measurable.
- **Build**: fill simulation rule (**strict, queue-free, conservative — T-critical**): a
  resting buy limit at P fills ONLY when a recorded trade prints STRICTLY BELOW P (an at-price
  print does NOT fill you — without queue modeling, at-touch fills manufacture edge).
  Timeout after K seconds unfilled → cancel (variant A) or convert to the existing
  market-on-confirm (variant B). Two pre-registered variants, K from config.
- **Evaluate**: sweep vs champion; report fill_rate, adverse-selection stat (post-fill 30s mid
  drift), and net R delta; 6.7 cost block mandatory (limit fills still pay fees; slippage
  model differs — document the fill price = limit price exactly, zero slippage, fees
  unchanged).
- **Kill**: both variants lose on pooled holdout → market-on-confirm stands; record fill_rate
  findings anyway (they inform 9.x detector thresholds).
- **Traps**: the strict-print-through rule is non-negotiable (weak models WILL fill at-touch
  and "discover" edge); timeout in logical seconds is fine (T1 does not apply — it is
  trade-relative, not time-of-day).

#### Card 7.3 — Time-of-day filters + time-decay exits `[craft] [F2] [S]`
- **Hypothesis**: excluding structurally hostile windows (or exiting stagnant trades) improves
  net R more than the trades it forgoes.
- **Build**: pre-registered no-entry window candidates: {first 5 min, first 15 min,
  11:30–13:30 ET, last 10 min} (4 registered candidates, ET via `epoch_anchor`, T1);
  time-decay exit: age > A seconds AND unrealized < +0.25R → exit, A ∈ {60, 120}
  (2 candidates). Each is a registered strategy variant.
- **Evaluate**: sweep vs champion; 6.5's conditioned report shows WHERE the delta comes from.
- **Kill**: no filter variant survives → the champion trades all hours; note which cells 6.5
  flags for future pre-registered hypotheses.
- **Traps**: these 6 candidates are the registered count (T6) — resist adding "one more
  window" mid-sweep; a filter idea from 6.10's loser mining is a NEW registration, next sweep.

#### Card 7.4 — Opening-range family `[setup] [F2] [M]`
- **Hypothesis**: the first-K-minutes range, once broken WITH tape confirmation (or faded at
  its extremes WITH absorption), carries follow-through beyond the matched null.
- **Mechanism**: the open concentrates overnight information discovery; its range is the
  day's first auction balance — breaks from it are the classic momentum seed, fades at its
  extremes the classic trap.
- **Build**: elegant minimal path — a new **level source** `opening_range` in
  `apps/backend/app/research/levels.py` (OR-high/OR-low computed from the first K = 15 min of
  1m bars, available only after 09:45, own config weight) feeding the EXISTING zone engine +
  `structure_tape` grammar (breakthrough map for breaks, rejection map for fades); plus two
  setup entries in `apps/backend/app/research/taxonomy.py` (`or_breakout`, `or_fade`) with
  frozen expected-behaviour statements.
- **Evaluate**: study harness first (occurrence → ternary outcomes vs time-matched null at the
  open — 6.6's null matters here MOST); strategy sweep second, only if the study shows lift.
- **Kill**: study shows OR-break outcomes indistinguishable from the time-matched null →
  family dead (the open's edge is just the open); do not build the strategy leg.
- **Traps**: OR levels must not exist before 09:30+K (as-of discipline — the 6.4 completed-bar
  rule makes this natural); needs full-session or 09:30–11:00 curated windows (5.2 fallback
  suffices).

#### Card 7.5 — Closing-hour family `[setup] [F2] [M]`
- **Hypothesis**: last-hour trend persistence (15:00→15:45 direction continuing into
  15:45→16:00) is conditionally predictable from tape + structure, beyond the matched null.
- **Build**: STUDY FIRST, strategy only on lift: persistence stat
  `P(sign(r_{15:45→16:00}) = sign(r_{15:00→15:45}) | conditioners)` with conditioners = day
  type (post-hoc), RVOL bucket, distance to nearest class-A/B zone, tape state at 15:45;
  no imbalance-feed proxies invented (no MOC data exists — T-honesty). Positions never
  survive the session (dataset-end exit already forces this).
- **Evaluate**: study vs time-matched null; n per conditioner cell with `insufficient` flags.
- **Kill**: no conditioner cell clears its CI → closing hour is noise at this granularity;
  record and stop.
- **Traps**: 15:00/15:45/16:00 are ET wall-clock cuts (T1); "auction print" analytics need
  5.1's condition codes — without them, exclude the 16:00 cross from return math explicitly.

**Era-7 kill test**: if NO craft variant (7.1–7.3) beats the frozen-exit champion on pooled
holdout after the 6.3 haircut, craft is dead for this strategy generation — keep the champion's
simple exits, write to the ledger that added complexity bought nothing, and route forward (the
router prefers era 8 next). 7.4/7.5 are setup families and are killed individually by their
studies.

**Era-7 anti-goal additions**: fill rules conservative-only (strict print-through; no queue
models, no at-touch fills); every craft variant is a new registered strategy id (frozen ids
untouched); pre-registered candidate counts named in the goal.md journeys themselves.

---

## ERA 8 — Volume Structure

**Mission**: add the volume-derived level family — volume profile, VWAP, round numbers — to the
existing confluence engine, and measure (via 6.6's random-levels null) whether volume-defined
placement carries information that pivot/extreme placement does not.

**Prerequisites**: era 5; era 6 (specifically the 6.4 completed-bar fix — all of this stacks on
the levels seam — and the 6.6 random-levels null). New level sources slot into
`apps/backend/app/research/levels.py` + `compute_confluence_zones`; every new source gets a
config weight and a `type` string; `structure_tape` consumes them with zero new strategy code.

---

#### Card 8.1 — Bars-based session VWAP + coarse volume profile `[levels] [F1] [M]`
- **Hypothesis**: VWAP and high-volume price bins act as intraday support/resistance —
  price interacting with them + tape confirmation outperforms the random-levels null.
- **Mechanism**: VWAP is the institutional benchmark price (execution desks work orders
  against it); high-volume bins are prices where positions actually changed hands — both are
  "memory" prices with real participants anchored to them.
- **Build (works on TODAY'S bar store — no tick sessions needed)**: from 1m bars: typical
  price `tp = (H+L+C)/3`; `VWAP_t = Σ(tp_i · vol_i) / Σ(vol_i)` over completed 1m bars of the
  session (as-of = last completed bar, 6.4 rule); σ bands:
  `σ_t = sqrt(Σ vol_i·(tp_i − VWAP_t)² / Σ vol_i)`, bands at ±1σ, ±2σ. Coarse profile: bin
  `tp` to `bin_bps` (config, default 10 bps of session open), accumulate bar volume; POC =
  argmax bin. New level types `vwap`, `vwap_band`, `poc_coarse` with config weights.
- **Evaluate**: study harness — touch events of each new level type → ternary outcomes vs the
  **random-levels null** (6.6) AND vs existing pivot levels (is volume placement better than
  swing placement, or the same?). Strategy sweep only after study lift.
- **Kill**: touches of volume levels ≈ random-levels null on train studies → the family is
  dead before any strategy work; retain VWAP as cockpit context only (polish).
- **Traps**: completed bars only (6.4); VWAP resets at session boundaries (ET, T1); tp-based
  VWAP is an approximation — label it `vwap_basis: "bars_tp"` so the 8.2 exact version is
  never silently pooled with it.

#### Card 8.2 — Tape-built exact volume profile `[levels] [F2] [M]`
- **Hypothesis**: the exact print-level profile (POC / value area / LVN-HVN) defines levels
  the coarse bar profile misses, with measurably better touch behavior.
- **Build**: on full-session tick datasets: bin every RTH print (exclude auction/irregular
  conditions once 5.1 fields exist; document the approximation where absent) to
  `bin_size = max(1 tick, session_open · bin_bps/10⁴)`; POC = max-volume bin; **value area
  (exact procedure)**: start at POC, repeatedly add the ADJACENT bin (above or below) with
  the greater volume until cumulative ≥ 70% of session volume; VAH/VAL = the VA's extremes.
  HVN/LVN: local maxima/minima of the 3-bin-smoothed histogram with a config prominence
  floor. Developing (as-of) variant uses prints ≤ T only. New level types `poc`, `vah`,
  `val`, `lvn`, `hvn`.
- **Evaluate**: as 8.1 (study vs random-levels null; head-to-head vs `poc_coarse`).
- **Kill**: exact ≈ coarse everywhere → drop the tick-built version (cheaper wins); coarse ≈
  null → family already dead via 8.1.
- **Traps**: developing profile at T uses prints ≤ T ONLY (no end-of-day profile leaked into
  intraday touches — the classic profile lookahead); full-session windows only (5.2's
  curated-window symbols are out of scope for session profiles — say so per symbol).

#### Card 8.3 — Naked/virgin prior-day POCs `[levels] [F2] [S]`
- **Hypothesis**: prior-day POCs never revisited since ("naked") attract price and produce
  stronger touch reactions than revisited ones.
- **Build**: from stored sessions: prior-day POC is naked at day D iff no D′ ∈ (POC-day, D)
  traded within `sr_touch_tolerance_bps` of it; level type `naked_poc`, strength decays
  `λ^age_days` (λ config, e.g. 0.8) or expires after N days (config). Needs consecutive
  recorded sessions (the recorder's per-symbol date continuity matters).
- **Evaluate**: touch study, naked vs revisited POCs vs null; n will be small — respect T2.
- **Kill**: naked ≈ revisited → drop nakedness, keep plain prior-day POC if 8.1/8.2 survived.
- **Traps**: nakedness is computable only from days actually recorded — a gap in the library
  makes a POC's status UNKNOWN, not naked (honest absence; never guess).

#### Card 8.4 — Anchored VWAPs `[levels] [F2] [M]`
- **Hypothesis**: VWAPs anchored at information events (session open, medium+ gap opens, the
  prior day's max-volume minute) act as dynamic S/R beyond the session VWAP.
- **Build**: same VWAP formula, anchor set (pre-registered, exactly 3): session open; gap
  open when |gap| ≥ the 5.5 `medium` class; close ts of prior day's max-volume 1m bar.
  Level type `avwap_<anchor>`, each with config weight.
- **Evaluate**: touch studies per anchor type vs null; the 3 anchors are the registered
  count.
- **Kill**: no anchor's touches beat the null → session VWAP (8.1) is the only VWAP that
  matters (or none, if 8.1 also died).
- **Traps**: anchor definitions are as-of-computable facts (gap class known at open; prior-day
  max-volume bar known before today's open) — never anchor on "today's max-volume bar"
  (end-of-day fact, T5).

#### Card 8.5 — Round-number levels `[levels] [F1] [S]`
- **Hypothesis**: dollar and half-dollar prices produce measurable touch reactions
  (order-clustering memory) worth a small confluence weight.
- **Build**: level type `round`: integer dollars always; half-dollars for price < $50;
  $5 multiples additionally for price ≥ $100 (config map by price band); constant strength,
  low default weight; zero data needed.
- **Evaluate**: touch study vs null; also measure whether EXISTING pivot levels cluster near
  round numbers (confound check — if pivots ARE round numbers, the source adds nothing).
- **Kill**: no touch lift OR full confound with pivots → drop the source.
- **Traps**: the confound check comes FIRST (weak models will double-count the same physical
  level as two sources and call it confluence).

#### Card 8.6 — Confluence v2: unified weighted zone scoring `[levels] [F2] [M]`
- **Hypothesis**: a zone score combining pivot/extreme/volume/VWAP/round sources with tuned
  source weights grades zones better (higher touch-reaction separation between A/B/C) than
  the current timeframe-breadth-only grade.
- **Build**: extend `compute_confluence_zones` + `_grade_zone`
  (`apps/backend/app/research/levels.py`): member strength gains a `source_weight(type)`
  factor (config vector). **Sweep discipline (T6)**: exactly 5–7 pre-registered weight
  vectors (hand-chosen, named, e.g. `equal`, `volume_heavy`, `structure_heavy`,
  `vwap_heavy`, `no_round`) — NEVER a grid search over weight space.
- **Evaluate**: per weight vector: A/B/C touch-reaction separation on train studies; the
  winner (if any) goes to a strategy sweep vs the current grading as champion basis.
- **Kill**: no vector separates classes better than timeframe-breadth alone on holdout →
  keep the simple grade; write it down.
- **Traps**: weight vectors are the registered candidates; class thresholds
  (`sr_class_a_min_timeframes` etc.) stay FIXED during this sweep (sweeping both = explosion).

**Era-8 polish card**: levels/zones overlay on the cockpit price chart
(`apps/frontend/components/PriceChart.tsx` — `lightweight-charts` price lines/areas from the
canonical levels endpoint; read-only, zero client recomputation) — the operator finally SEES
what the strategies see.

**Era-8 kill test**: if on train studies tape behavior at volume-derived levels is
indistinguishable from the random-levels null AND no confluence-v2 vector survives, volume
structure is dead as signal for this panel — retain VWAP/profile as cockpit context (the
polish card ships regardless), write the negative result to the ledger, and route to era 9.

**Era-8 anti-goal additions**: developing-profile as-of discipline (prints ≤ T); every new
level source carries `entry_time_legal` provenance; no grid searches over weights; bars-basis
vs tape-basis VWAP never pooled.

---

## ERA 9 — The Microscope

**Mission**: the heart of "tapeology" — new tape-event detectors built as measurable objects.
Two waves: **Wave 1** = cheap per-event features + studies (no strategy code); **Wave 2** =
detectors that arm or veto setups — built ONLY for families Wave 1's atlas extension ranked
non-zero (the 6.9 gate: `|median ρ| ≥ 0.03` AND `sign_consistency ≥ 0.7` on train).

**[SPLIT-POINT between waves]** — and Wave 2's card list is written at split time from the
atlas result, not from enthusiasm.

**Infrastructure note (do this ONCE, first)**: Wave-1 features are computed in the **research
observer layer** (the same replay observer 6.9 extended), NOT by modifying
`apps/backend/app/engine/features.py` for the default profile — the frozen-default equivalence
test pins the default engine's outputs, and engine-surface additions risk moving them (T11).
Rule: research features live beside the engine, reading the same replayed events in the same
pass (never a second replay, never a second source of truth — T10). An engine-surface addition
is allowed ONLY with proof the equivalence test's pinned scope is unaffected, and is otherwise
a documented basis decision.

> **RAPID-MICROSCOPE OPENING NOTE (2026-08-16, operator pivot, under §5.6 "goal.md wins").**
> The operator opened **"The Rapid Microscope"** (session `rapid-microscope`, constitution
> `docs/goal.md`, canonical methodology `docs/rapid-validation-spec.md`) — an operator-directed
> era outside the router's numbering (the Era-B/B2 precedent) that brings **Wave 1 of this era
> forward NOW** and adds the rapid-validation machinery this catalog never specified (Scout +
> exploratory candidate ledger, origin-fenced chronological walk-forward, sealed Validation
> Vault, graduation contract). Dispositions, card by card:
>
> - **Brought forward into the rapid-microscope era — as CONCEPTS, with every operational
>   window/constant re-frozen in `docs/rapid-validation-spec.md` (r2), superseding the old
>   cards' symbolic or lookahead-unsafe choices where they conflict**: 9.1 (the `CD_t`
>   accumulator verbatim; the symmetric divergence window SUPERSEDED by a trailing as-of
>   definition — see the dated amendment on the card itself; it is pilot study 2), 9.3
>   (top-of-book imbalance — quote-size features, now under the per-dataset
>   `quote_size_unit` contract of spec §2.6), 9.4 (burst/climax — event-time burst features
>   with a frozen trailing-baseline count + the capitulation-exhaustion pilot), 9.5 (spread
>   dynamics — spread level/change features over frozen windows), 9.6 (same-side flow-runs —
>   the run-persistence feature; its seeded within-session shuffle null is SUPERSEDED by the
>   spec's session-clustered block permutation, which is strictly more dependence-honest),
>   9.7 (event-time feature windows — last-N-trades / last-X-shares are first-class
>   representations at frozen sizes).
> - **Deferred unchanged**: 9.2 (delta-by-price profile; still needs Card 8.2's binning).
> - **Wave 2 (9.8–9.11) stays gated.** The 6.9 "atlas" this era's gate names was never built
>   (executed era 6 re-scoped per evidence family). The gate is therefore RE-POINTED, not
>   waived: Wave-2 detector cards open only on `historical_oos`-class Scout/walk-forward
>   evidence from the rapid-microscope machinery meeting the same thresholds in spirit
>   (`|median ρ| ≥ 0.03` AND `sign_consistency ≥ 0.7` on discovery-class data, per-family).
>   Card 9.10 additionally stays blocked on condition codes for the LEGACY corpus — but the
>   rapid era's Card-5.1 preservation prerequisite (spec §7.1) means every NEW recording
>   carries conditions/venue from 2026-08-16 on, so 9.10's data prerequisite accrues going
>   forward instead of staying permanently empty.
> - The era-9 polish cards (chart markers, replay annotation) remain future work (Era C for
>   the annotation tool).
>
> The catalog-era-6 atlas concept (6.9) is superseded by the rapid-microscope Scout +
> temporal-stability views; this note is the dated record required by §5.6.
>
> **HYPOTHESIS-FOUNDRY OPENING NOTE (2026-08-26, operator pivot, under §5.6 "goal.md wins").**
> The Rapid Microscope is CLOSED — GOAL_ACHIEVED 2026-08-24 (session `rapid-microscope`,
> two-key confirmed; zero survivors is the era's honest result; its terminal session and
> research ledgers are immutable). The operator opened **"The Hypothesis Foundry"**
> (constitution `docs/goal.md`; predecessor archived at
> `docs/goal-archive/goal-2026-08-26.md`) — a FINITE, predeclared candidate-compilation and
> exhaustion era over the already-ratified source scope (parked Studies 1/3 and the Wave-1
> concepts the 2026-08-16 note above brought forward). Binding rules, from `docs/goal.md`:
>
> - Unresolved scientific ambiguity BLOCKS (typed `BLOCKED_*` dispositions); there is no
>   mid-run case-by-case owner tuning.
> - The complete real candidate manifest is generated once and committed to Git BEFORE the
>   first new diagnostic outcome read (freeze-before-read barrier + first-read hash lock).
> - Real trials are recorded on a dedicated Foundry hash-chained trial ledger and reuse the
>   existing frozen Scout statistical decision rail (`scout.screen_candidate`) unchanged;
>   the Scout ledger receives no Foundry rows this era.
> - No fresh OOS acquisition, corpus-era registration, retention probe, withheld release,
>   Vault consumption, graduation, or Referee work belongs to this era; a Scout survivor
>   terminates as `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` only.
> - This era has NO post-achievement self-extension: the continuous-improvement proposer
>   guidance is archived at `docs/goal-archive/proposer-guidance-2026-08-26.md`, so the
>   framework's two-file opt-in (`project-extensions/hooks/post-goal.sh` +
>   `project-extensions/proposer-guidance.md`) is deliberately unsatisfied for this era;
>   Part 5.3's amendments remain historical record.
>
> This note is the dated record required by §5.6.

---

### Wave 1 — features + studies

#### Card 9.1 — Session cumulative delta + divergence-at-level `[tape] [F2] [M]`

> *(AMENDED 2026-08-16, rapid-microscope r2: the `CD_t` session-anchored accumulator below is
> carried VERBATIM. The divergence comparison is NOT — its `price_extreme(τ)` "over the 120s
> window **around** the touch" is symmetric and therefore lookahead at τ, and its
> `δ = 0.25 · median 120s volume "(config fraction)"` would have been a Config field. The
> rapid era's operative definition (rapid-validation-spec §3, r2) uses a TRAILING as-of window
> `[τ − 120s, τ]` with `available_at = τ`, and freezes both choices as module constants
> (`DIVERGENCE_TRAILING_SECONDS = 120.0`, `DIVERGENCE_DELTA_VOLUME_FRACTION = 0.25`) — never
> Config fields. The original text below is preserved for the record and is superseded where
> it conflicts.)*

- **Hypothesis**: at consecutive tests of the same zone, price making a new extreme while
  cumulative delta does not (divergence) predicts rejection better than the tape state alone.
- **Mechanism**: a second push to the same level on LESS net aggression = the aggressor is
  exhausting; classic tape-reading, now falsifiable.
- **Formulas**: `CD_t = Σ_{i≤t, side_i ≠ unknown} sign(side_i)·size_i` (session-anchored,
  RTH prints, shares). Divergence between consecutive touches τ1 < τ2 of the SAME zone:
  bearish if `price_extreme(τ2) > price_extreme(τ1)` AND `CD(τ2) ≤ CD(τ1) − δ` where
  `δ = 0.25 · median 120s volume` (config fraction); bullish mirrored. `price_extreme(τ)` =
  max/min mid over the 120s window around the touch.
- **Evaluate**: atlas extension (rank-IC of divergence flag vs forward returns at touches) +
  study: touch-with-divergence vs touch-without, ternary outcomes, matched null.
- **Kill**: 6.9 gate fails on train → no Wave-2 detector for delta.
- **Traps**: EXCLUDE `unknown`-side prints explicitly and report their fraction (5.6's
  aggressor-confidence — a high-unknown dataset makes CD untrustworthy); zone identity via
  the zone engine, not raw price equality.

#### Card 9.2 — Delta-by-price profile `[tape] [F2] [S]`
- **Hypothesis**: price bins where heavy net delta produced NO price progress (absorption
  bins) mark defended prices that outperform volume-only bins as levels.
- **Build**: 8.2's binning, accumulating SIGNED volume; absorption bin = |delta_bin| ≥ p90 of
  session bins AND price traversal count through the bin ≥ K (it kept coming back). Level
  type `delta_wall` (feeds the zone engine like any source).
- **Evaluate**: touch study vs volume-profile bins vs null.
- **Kill**: `delta_wall` touches ≈ `poc/hvn` touches → signed adds nothing over unsigned;
  drop.
- **Traps**: same as 9.1 (unknown-side fraction); developing as-of variant only (8.2's trap).

#### Card 9.3 — Top-of-book imbalance `[tape] [F2] [M]`
- **Hypothesis**: L1 size imbalance at a zone touch (bid-heavy at support) adds confirm/veto
  information beyond the trade-derived features.
- **Formulas**: `I_t = EWMA(bid_size / (bid_size + ask_size))`, halflife 5s (config), sizes
  in ROUND LOTS on both sides (ratio is unit-safe; never mixed with share counts — T12).
  Sampled at arm-eligible events.
- **Build**: research-observer feature (see infrastructure note); quote sizes are ALREADY in
  the dataset rows (`bid_size`/`ask_size` per `QuoteEvent` — `apps/backend/app/providers/base.py`).
- **Evaluate**: atlas (rank-IC at touches, by regime); PG fixture density ≈ 18 quotes/s is
  ample.
- **Kill**: 6.9 gate fails → no Wave-2 use; note that L1 imbalance failing here LOWERS the
  prior on era-15 depth imbalance (record that explicitly for the era-15 purchase decision).
- **Traps**: T12; EWMA seedless determinism (initialize at 0.5, document).

#### Card 9.4 — Burst / climax detection `[tape] [F2] [M]`
- **Hypothesis**: trade-arrival bursts at session extremes mark exhaustion (reversal lift);
  bursts at zone breaks mark genuine breaks (continuation lift).
- **Formulas**: burst z-score over w = 5s windows: `z = (n_w − μ_m·w/60) / sqrt(μ_m·w/60)`
  (Poisson), where `μ_m` = expected trades/min at ET minute m from the 5.5 intraday
  RVOL/arrival baseline (prior 20 sessions, T5). Burst iff z ≥ 4 (config). Volume climax:
  1m volume ≥ p95 of minute-of-day baseline AND price at a session extreme.
- **Evaluate**: atlas + study: (burst at extreme → ternary outcomes) and (break with burst vs
  break without) vs matched nulls.
- **Kill**: 6.9 gate fails in both contexts → drop; if only one context passes, register only
  that context for Wave 2.
- **Traps**: baseline from PRIOR sessions only (a same-day baseline makes every open a
  "burst"); ET minute alignment (T1).

#### Card 9.5 — Spread-dynamics regime `[tape] [F2] [S]`
- **Hypothesis**: spread widening (EWMA_fast/EWMA_slow ≥ threshold) marks instability where
  entries underperform — a veto; narrowing + one-sided 9.3 imbalance precedes breaks.
- **Formulas**: spread bps EWMAs, halflifes 10s/120s (config); widening iff ratio ≥ 1.5
  (config).
- **Evaluate**: atlas; veto value measured later as a Wave-2/era-7-style registered filter.
- **Kill**: 6.9 gate fails → drop.
- **Traps**: `average_spread` already exists per window — the NEW content is the two-scale
  ratio; do not duplicate the existing feature (T10).

#### Card 9.6 — Same-side flow-runs persistence `[tape] [F2] [S]`
- **Hypothesis**: long same-side print runs continue beyond chance (flow herding), and run
  length at a zone touch adds confirm information.
- **Formulas**: run = consecutive same-side prints (unknowns break runs, counted); observed
  `P(next same | run ≥ k)` for k ∈ {5, 10, 20} vs a seeded within-session shuffle of the
  side sequence (permutation baseline, 1,000 shuffles, seeded).
- **Evaluate**: the permutation comparison IS the study; then atlas for run-length-at-touch.
- **Kill**: observed ≈ shuffled at all k → runs are the volume clock in disguise; drop.
- **Traps**: shuffle within-session (cross-session shuffles break stationarity); seeded.

#### Card 9.7 — Event-time feature windows `[tape] [F2] [M]`
- **Hypothesis**: features over the last-N-trades / last-X-shares beat fixed-seconds windows
  at the open and lunch (where a 30s window means wildly different event counts).
- **Build**: research-observer variants of the existing 13 features over windows
  N ∈ {50, 200} trades and X ∈ {10k, 50k} shares (4 registered window variants; the frozen
  engine's five fixed-seconds windows are untouched — infrastructure note applies).
- **Evaluate**: atlas head-to-head — same feature, clock vs event windows, same events; the
  question is purely "which windowing has higher |ρ| where".
- **Kill**: event-time ≤ clock-time everywhere → drop (a real, publishable negative).
- **Traps**: comparisons on identical event samples (else the comparison measures sampling);
  windows are the registered variants (T6).

### Wave 2 — detectors that arm or veto (atlas-gated; build only survivors of the 6.9 gate)

#### Card 9.8 — Iceberg / defended-level inference `[detector] [F2] [M]`
- **Hypothesis**: repeated executions at one price while displayed L1 size refills mark
  hidden liquidity; zones flagged "defended" reject better.
- **Formulas**: at price p (zone member): refill event = bid_size at p increases after a
  trade consumed it (round lots, T12); `iceberg_score = consumed_shares_at_p /
  max(displayed_round_lots_before · 100, 1)` with ≥ K refill cycles (K config, e.g. 3);
  defended iff score ≥ threshold (config).
- **Evaluate**: study (defended-zone touches vs undefended vs null) → registered veto/confirm
  candidate on `structure_tape` via sweep.
- **Kill**: defended ≈ undefended on train study → drop before any strategy work.
- **Traps**: this extends the EXISTING `bid_refresh_score`/`ask_refresh_score` family — reuse
  their machinery, don't duplicate (T10); L1-only inference is noisy — the honest claim is
  "refill-consistent", never "iceberg proven".

#### Card 9.9 — Stop-run sweep-and-reclaim detector `[detector] [F2] [M]`
- **Hypothesis**: a fast penetration beyond a class-B+ zone that RECLAIMS within T seconds
  (with a burst during penetration and dry-up after) is a fade entry better than the
  existing `failed_move_fade` arming.
- **Formulas**: penetration ≥ p_bps beyond the zone edge (p ∈ {3, 10} registered) within
  ≤ 120s of first breach; reclaim = mid back on the original side for ≥ 30s sustained;
  volume signature: 9.4 burst during penetration AND post-reclaim 60s volume ≤ 0.5× the
  penetration window's (config).
- **Build**: arms the EXISTING `failed_move_fade` setup (`apps/backend/app/research/taxonomy.py`
  — `requires_level: true`) as a registered strategy variant.
- **Evaluate**: study → sweep vs champion; 6.6 random-levels null is the crucial control
  (does the LEVEL matter, or does any sweep-reclaim shape fade?) — run both.
- **Kill**: fade edge ≈ random-levels-null fade edge → the level is decoration; record which
  half (shape vs placement) carried whatever signal existed.
- **Traps**: "sustained reclaim" uses mid, not last (bounce artifact); p and T are the
  registered grid — 4 candidates total, no widening.

#### Card 9.10 — Large-print analytics v2 `[detector] [F2] [M]`
- **Hypothesis**: per-symbol-calibrated large prints (p99 of TRAIN print sizes, replacing the
  global 500-share constant), their clusters, and their at-bid/at-ask asymmetry near zones
  carry directional information the flat count misses.
- **Formulas**: threshold = p99 of print-size distribution from PRIOR train sessions, frozen
  with provenance (T5 — never the session under evaluation); cluster = ≥3 large prints
  within 30s AND 10 bps; asymmetry near a zone = (large-at-ask − large-at-bid) /
  (large-at-ask + large-at-bid) within the zone band; post-block drift study: mid return at
  h ∈ {30, 120, 300}s after an ISOLATED large print, conditioned on at-bid/at-ask ×
  near-zone/far.
- **Evaluate**: the drift study is the gate; only drift-positive conditions become registered
  confirm/veto candidates.
- **Kill**: no conditional drift clears its CI → large prints are (at this granularity)
  informationless; keep the existing count feature untouched and stop.
- **Traps**: 5.1's condition codes matter — exclude auction/average-price prints from
  "blocks" once available (an opening cross is not an institutional block); p99 recomputed
  only at documented epochs.

#### Card 9.11 — Absorption-exhaustion timing `[detector] [F2] [S]`
- **Hypothesis**: absorption that ENDS (score collapses while price holds the zone) precedes
  breaks in the direction the absorber was fighting — the "defender left" moment.
- **Formulas**: pattern = `absorption_score ≥ H` sustained ≥ D seconds, then `< L` within the
  zone band while |mid drift| ≤ b bps (H/L/D/b config, one registered set); outcome = break
  direction/magnitude within 120s.
- **Evaluate**: study vs matched null; registered arm candidate only on lift.
- **Kill**: post-pattern breaks ≈ base rate → drop.
- **Traps**: uses the EXISTING `absorption_score` (T10); the pattern is a TIMING claim — the
  study must compare against absorption-that-continues, not against no-absorption.

**Era-9 polish cards**: detector/burst/divergence markers on the cockpit chart (read-only from
canonical endpoints); **replay annotation tool** — bookmark+note moments during replay
(explicit save via the journal store pattern in `apps/backend/app/research/store.py`; additive
table; scoped persistence honored) — builds the human-labeled moment library that era 14's
signature retrieval and any future validation can use.

**Era-9 kill test**: per detector via the 6.9 gate and its study; if Wave 1 kills everything,
**do not build Wave 2** — write the atlas verdict to the ledger and route (era 10 or 12). A
fully-dry Microscope is a major, honest finding: the engine's event stream carries no
exploitable short-horizon signal at this data granularity — it re-prices every later era's
prior and strengthens the case for eras 12/15 or contingency C0.

**Era-9 anti-goal additions**: research-observer rule (no engine-surface changes without
equivalence-scope proof); every detector's thresholds pre-registered before its study; no
detector output feeds the frozen classifier; `unknown`-side fractions reported wherever
aggressor-derived quantities are used.

---

## ERA 10 — Compression → Expansion & Bar Anatomy

**Mission**: the classic price-action families the catalog was missing — range compression as an
expansion predictor, and candle anatomy at zones — culminating in the head-to-head the product
has never run: **does tape confirmation actually beat bar-close confirmation?** That comparison
is the empirical test of tapeology's founding bet.

**Prerequisites**: eras 5, 6. Everything here runs on bars + the existing zone engine + the
existing study/sweep harnesses; it is the cheapest research era in the catalog.

---

#### Card 10.1 — Range-compression detectors → expansion conditionals `[bars] [F2] [M]`
- **Hypothesis**: compressed days (inside day / narrowest-range-k / multi-day squeeze) are
  followed by expansion days at a rate the base rate does not explain — predicting MAGNITUDE,
  not direction.
- **Mechanism**: volatility clusters and mean-reverts; balance precedes imbalance (the auction
  logic the profile eras exploit spatially, applied temporally).
- **Formulas** (daily bars, all as-of D using completed days ≤ D): inside day:
  `high_D ≤ high_{D−1} AND low_D ≥ low_{D−1}`; NR-k: `range_D = min(range_{D−k+1..D})` with
  k = 7; squeeze: `mean(range, 5 days) / mean(range, 20 days) ≤ 0.6` (config). Expansion
  conditional: `P(range_{D+1} ≥ 1.5·ATR14_D | compression_D)` vs unconditional base rate,
  with CI (6.2).
- **Evaluate**: descriptive study first (per symbol × personality tier). Strategy leg (only on
  lift): next-day opening-range breakout **gated on prior-day compression** — composes
  directly with card 7.4's OR machinery; registered as one candidate.
- **Kill**: expansion conditional ≈ base rate across the panel → compression carries no
  magnitude information here; drop the family (a clean, publishable negative).
- **Traps**: compression is a D-close fact — legal as a NEXT-day (D+1) entry conditioner, T5
  compliant by construction; do not invent a direction claim (the study is magnitude-only;
  direction comes from the OR break).

#### Card 10.2 — Wick-rejection ratios at zones `[bars] [F2] [S]`
- **Hypothesis**: a zone-touch bar closing with a long rejecting wick (shadow through the zone,
  close back on the near side) predicts rejection follow-through better than a touch without.
- **Formulas**: on the touch bar (intraday timeframe, completed per 6.4):
  `upper_wick_frac = (high − max(open, close)) / (high − low)`;
  `lower_wick_frac = (min(open, close) − low) / (high − low)`. Resistance-rejection evidence:
  touch of a resistance zone with `upper_wick_frac ≥ 0.6` (config) AND close below the zone
  band; support mirrored.
- **Evaluate**: touch study — wick-touches vs plain touches vs null, ternary outcomes.
- **Kill**: wick ≈ plain on train → anatomy adds nothing at this timeframe; try exactly one
  alternative timeframe (pre-registered) before dropping.
- **Traps**: degenerate bars (`high == low`) → skip, never divide by zero; the touch bar must
  be COMPLETED before any signal is claimed (6.4 rule — a forming bar's wick is future
  information).

#### Card 10.3 — Reversal bar anatomy at levels `[bars] [F2] [S]`
- **Hypothesis**: two-bar reversal shapes (engulfing; close-location flip) at zones add
  rejection evidence beyond 10.2's wicks.
- **Formulas**: engulfing at support: `close_B > open_B` (up bar) AND body of B covers body of
  B−1 (`open_B ≤ close_{B−1}` AND `close_B ≥ open_{B−1}`) with B−1 a down bar; close-location
  value `CLV = (close − low)/(high − low)`; flip = `CLV_{B−1} ≤ 0.3 AND CLV_B ≥ 0.7`
  (support side; resistance mirrored; thresholds config).
- **Evaluate**: touch study as 10.2; report overlap with 10.2 (if wick and anatomy flag the
  same touches, they are one signal, not two — the 8.5-style confound check).
- **Kill**: no lift, or full overlap with 10.2 → keep at most one anatomy signal.
- **Traps**: completed bars; two-bar patterns need BOTH bars completed; overlap check FIRST.

#### Card 10.4 — Bar-close vs tape confirmation, head-to-head `[showdown] [F2] [M]`
- **Hypothesis**: at identical zone-touch opportunities, tape-state confirmation (the existing
  `structure_tape` maps) produces better holdout net R than 1m bar-close confirmation — the
  founding bet of the product, never yet measured.
- **Build**: three registered strategy variants on IDENTICAL zone-touch events:
  (A) tape confirmation (existing rejection/breakthrough maps); (B) bar-close confirmation
  (1m bar completes back-inside for fades / beyond for breaks); (C) both required. Identical
  exits/fees/sizing.
- **Evaluate**: sweep vs champion, but the REPORT is the pairwise comparison table (A vs B vs
  C on pooled holdout, CI on the differences, cost blocks). This is a flagship honest result
  whatever it says.
- **Kill**: n/a — every outcome is a finding: A>B (the tape earns its complexity), B≥A (the
  candle is enough — a profound, product-shaping negative), C>both (they are complementary).
- **Traps**: the touch-opportunity set must be IDENTICAL across variants (same zones, same
  as-of levels, same eligibility) — any drift in opportunity sets invalidates the comparison;
  bar-close lag means B enters later — that latency difference is PART of the honest result,
  not a bug to correct.

**Era-10 kill test**: individual per card. If 10.1–10.3 all die AND 10.4 says B≥A, this era has
delivered one of the most valuable results in the catalog: simple bars match the tape at this
granularity — re-price every remaining tape era accordingly (the router then favors 12/15/C0).

**Era-10 anti-goal additions**: magnitude claims never silently become direction claims;
completed-bar discipline on every anatomy signal; identical-opportunity-set proof required for
the 10.4 comparison.

---

## ERA 11 — Trade Craft II

**Mission**: the architecturally expensive craft — trailing stops, scale-outs, re-entry — built
only if something survives to deserve it.

**Gate**: at least one surviving (promoted or near-gate) strategy exists. **Prerequisite**:
era 7. If nothing has survived by the time the router reaches here, skip forward (this era
polishes an edge; it cannot create one).

---

#### Card 11.1 — Structural trailing stops `[craft] [F2] [M]`
- **Hypothesis**: trailing the stop behind the most recent COMPLETED swing pivot (from the 1m
  bar levels machinery, as-of) beats the fixed stop on holdout for trend-side setups.
- **Build**: for longs: `stop = latest completed 1m swing-pivot low − buffer_bps` (buffer
  config), updated ONLY when a new pivot completes (never tick-by-tick trailing); reuses
  `_swing_pivots` (`apps/backend/app/research/levels.py`) at the 1m timeframe. One registered
  variant per setup family.
- **Evaluate**: sweep vs the 7.1-era champion exits; excursion analytics show WHERE the R
  moved (fewer give-backs vs more premature exits).
- **Kill**: no holdout improvement → fixed stops stand (trailing is a comfort feature, not an
  edge — record it).
- **Traps**: pivot completion needs `lookback` bars AFTER the pivot (the levels engine already
  enforces this — trust it, don't reimplement); trailing only tightens, never loosens.

#### Card 11.2 — Scale-out policies `[craft] [F2] [L]`
- **Hypothesis**: taking partial profit at +1R and letting a runner seek the next opposing
  level beats all-in/all-out on holdout expectancy.
- **Build (real architecture work)**: the runner currently closes a trade in ONE
  `_close_trade` call (`apps/backend/app/research/backtests.py`); scale-out = a trade with
  N legs, each leg carrying the SAME entry/R basis, per-leg exits, trade-level result =
  share-weighted sum of leg R (document the exact accounting so "$ never without R" holds
  per leg AND per trade). Registered policies (exactly 3): `all_at_target` (current),
  `half_1R_half_next_level`, `half_1R_half_trailing` (needs 11.1).
- **Evaluate**: sweep; expectancy + max_drawdown_r comparison (6.1 metrics).
- **Kill**: neither split policy beats all-in/all-out → single-exit stands; the architecture
  remains for era 16 reuse (per-leg accounting is generally useful).
- **Traps**: leg accounting is where weak models create $-without-R bugs — the acceptance
  test must reconcile Σ(leg $) with trade $ and Σ(leg R · weight) with trade R exactly;
  fees charged per leg exit (real brokers do).

#### Card 11.3 — Bounded re-entry `[craft] [F2] [M]`
- **Hypothesis**: after a stop-out, ONE re-entry when the arming conditions re-establish
  FRESH recovers more R than it spends (the level was right, the timing was early).
- **Build**: registered variant: within 300s of a stop-out, if the arming premise
  re-establishes as a **fresh event-to-event cross** (the era-4 audit-B1 lesson: a static
  "price is in the band" test inflates arming — require the condition to become true anew,
  edge-triggered), allow exactly ONE re-entry at the SAME size (config-fixed — never a
  martingale), sharing the day's one-open-trade discipline.
- **Evaluate**: sweep vs no-re-entry champion.
- **Kill**: re-entry loses on holdout → one shot per setup stands.
- **Traps**: edge-triggered arming discipline (B1); same-size only; ONE re-entry (a counter
  in the trade state, tested).

**Era-11 kill test**: if all three cards die, exits stay simple — write to the ledger that
craft complexity bought nothing at this sample size and prefer routing to data (W1) over more
craft.

**Era-11 anti-goal additions**: no martingale/size-escalation anywhere; leg accounting
reconciliation test mandatory; re-entries edge-triggered and counted.

---

## ERA 12 — Swing Bridge

**Mission**: extend horizons — structure from daily/weekly levels, tape only for entry timing,
holds measured in DAYS on the bar store. This is the gated "longer horizons" scope the operator
approved; it is also the natural fallback if intraday tape edges keep dying (costs shrink
relative to R as horizons grow).

**Prerequisites**: eras 5, 6. **[SPLIT-POINT after 12.1]** — the runner is its own session if
needed.

---

#### Card 12.1 — Bar-based swing backtest runner `[infra] [F2] [L]`
- **Purpose**: a second runner MODE over the BarStore for multi-day holds; the tape engine and
  the intraday runner stay untouched.
- **Build**: trade opens at a tape-timed intraday entry (from the tick dataset of entry day
  D); the swing leg then walks DAILY bars: stop checked against each day's low/high, target
  against opposing daily/weekly levels, max-hold N days (config). **Gap accounting (the
  honesty core)**: if day D+k OPENS through the stop, the exit fills at the OPEN price, not
  the stop price — overnight gaps pay what they pay. Fees per side unchanged; no financing
  modeled (cash equity; state it in the register string). New JobManager-pattern runner
  beside `apps/backend/app/research/backtests.py`, own report shape, own golden tests.
- **Acceptance**: synthetic bar fixtures with a gap-through-stop day reproduce the open-fill
  arithmetic exactly; byte-identical reruns; the intraday runner's goldens untouched.
- **Traps (acute)**: **split leakage** — a swing trade entered on a train day that holds into
  a holdout day leaks. RULE: a trade is eligible ONLY if its entire maximum hold window
  (entry day + N days) lies within same-split days; otherwise the opportunity is skipped and
  counted in a disclosed `skipped_cross_split` tally. Daily bars completed-only (6.4 rule at
  the daily scale); exits never use intraday information the runner doesn't have (the daily
  bar's OHLC order is unknown — resolve stop-vs-target collisions on the SAME day
  conservatively: stop first, always, and say so in the register string).
- **Effort**: L — this is the era's main build.

#### Card 12.2 — Daily-S/R swing setups with tape-timed entries `[swing] [F2] [M]`
- **Hypothesis**: class-A/B zones from daily/weekly timeframes, entered intraday on tape
  confirmation and held for days, clear the cost hurdle that kills intraday edges.
- **Mechanism**: the cost floor (6.7) is fixed per round-trip; a 200-bps swing R dwarfs it
  where a 5-bps intraday stop cannot. If tape reading has ANY value, its cheapest expression
  may be entry timing on structural swing trades.
- **Build**: zones from existing `1d/1w/1mo` levels (machinery exists); entry = the existing
  zone-touch + tape-confirmation grammar on day D's tick data; swing leg via 12.1; stops =
  structural (beyond the zone) with the class-R framework rescaled to daily ATR units
  (config).
- **Evaluate**: 12.1-runner sweep vs a null of random-day entries at the same zones (seeded);
  6.7 cost block (which now flatters instead of kills — report it honestly both ways).
- **Kill**: swing zone-entries ≈ random-day null on pooled holdout → structure adds no swing
  timing value; the honest residue is 12.3's gap statistics.
- **Traps**: 12.1's split-window rule bites hard here (max-hold shrinks eligible entries);
  n will be SMALL — T2 discipline, report insufficiency rather than loosening.

#### Card 12.3 — Gap statistics family `[swing] [F2] [M]`
- **Hypothesis**: gap-fill and gap-continuation rates are conditionally predictable (gap
  class × day type × personality tier) well beyond base rates.
- **Formulas**: `gap-fill(D) = price touches close_{D−1} during RTH of D`;
  `gap-and-go(D) = close_D beyond open_D in the gap direction`; rates per (gap class from
  5.5 × RVOL bucket × personality from 6.11) with CIs; minimum cell n enforced.
- **Evaluate**: descriptive study first; strategy candidates ONLY from cells that clear CIs:
  fade-small-gaps-toward-fill / follow-large-gaps, tape-confirmed at the OR (composes with
  7.4), registered individually.
- **Kill**: no cell clears its CI at achievable n → gaps are efficient at this panel; record.
- **Traps**: gap class is known AT THE OPEN (entry-time legal); day-type of D is NOT (T5);
  the cell count is the registered trial count for the study (T6).

#### Card 12.4 — Multi-day follow-through after class-A breaks `[swing] [F2] [S]`
- **Hypothesis**: a confirmed break of a class-A zone (era-4 grammar) is followed by
  same-direction closes at D+1/D+3/D+5 beyond base rate — a swing runner candidate.
- **Formulas**: `P(close_{D+k} beyond zone | confirmed break on D)` for k ∈ {1, 3, 5} vs the
  symbol's unconditional directional base rate; CI per k.
- **Evaluate**: study → 12.1 runner candidate on lift (hold-through-k with structural stop).
- **Kill**: no k clears CI → class-A breaks have no multi-day memory; record.
- **Traps**: "confirmed break" reuses the era-4 breakthrough definition — with the B1
  edge-trigger discipline (11.3's rule), not the loose static test.

#### Card 12.5 — Earnings-window rule for swing holds `[rule] [F2] [S]`
- **Purpose**: holds never span an earnings date — forced exit at the last session close
  before the 5.6 calendar's date (a risk RULE, not a hypothesis; scheduled binary events are
  not the edge being tested).
- **Acceptance**: a synthetic fixture with an earnings date mid-hold exits on schedule and
  says why in the trade record.

**Era-12 kill test**: if 12.2 and 12.4 both die and 12.3 finds nothing, longer horizons don't
rescue the structure thesis on this panel — a major routing input for the year (C0 leans
whitepaper-ward). The 12.1 runner remains as permanent, reusable infrastructure regardless.

**Era-12 anti-goal additions**: gap fills at open price (never stop price) on gap-throughs;
same-day stop-vs-target collisions resolve stop-first; cross-split holds skipped and tallied;
no financing/overnight-fee modeling claims (absence stated in the register string).

---

## ERA 13 — Context

**Mission**: the traded symbol does not move in a vacuum — give the research layer an index and
sector reference (bars-based) and measure whether context vetoes and relative strength improve
single-name entries. **Everything stays single-traded-symbol**: context filters entries; it never
becomes portfolio management (immutable rail 0.3 vocabulary: no capital allocation).

**Prerequisites**: eras 5, 6. Tier-C panel ETFs (SPY/QQQ/IWM/XLF/XLE) already recorded as bars by
5.2. **Bars, not tick** — a SPY tick stream would swamp the JSON store for no measurable gain;
if a bars-based context result ever earns tick-level refinement, that is a NEW registered
follow-up.

---

#### Card 13.1 — Reference-bars alignment layer `[infra] [F2] [S]`
- **Purpose**: align the traded symbol's events with reference-symbol 1m bars by ABSOLUTE epoch
  (never logical ts — T1's cross-symbol corollary: two datasets' logical clocks share nothing).
- **Build**: a research-layer join utility: given the traded dataset's `epoch_anchor + ts`,
  return the reference symbol's last COMPLETED 1m bar (6.4 rule) as-of that instant, from the
  BarStore. Sector map: config-owned symbol → sector-ETF table (PG→XLP is absent from the
  panel — either add XLP bars in a 5.2 top-up or map PG→SPY only; record the choice).
- **Acceptance**: a synthetic two-symbol fixture with known offsets joins correctly across a
  DST boundary; joins are byte-stable.
- **Traps**: absolute epoch only; completed reference bars only (a forming SPY bar leaks the
  future); missing reference data = honest absence (`context: unknown`), never a default value
  that silently means "bullish".

#### Card 13.2 — Index-regime entry veto `[context] [F2] [M]`
- **Hypothesis**: single-name entries AGAINST the index's concurrent direction underperform
  entries aligned with it; a veto on counter-index entries improves holdout net R.
- **Formulas**: index state as-of entry = sign and magnitude of SPY return over the trailing
  {15, 60} completed minutes (2 registered windows) + SPY's position vs ITS session VWAP
  (8.1 machinery on SPY bars). Veto rule (registered, exactly 2 variants): block
  counter-trend fades when |SPY 60m return| ≥ threshold; block counter-trend breaks when SPY
  is on the wrong side of its VWAP.
- **Evaluate**: registered filter sweep vs champion (era-7 style); 6.5's conditioned report
  shows which cells the veto helped.
- **Kill**: no veto variant survives → single-name tape/structure is index-independent at
  this horizon; record and skip 13.4.
- **Traps**: trailing-window returns from completed bars as-of entry (T5-legal); the veto only
  REMOVES trades — if a "veto" ever adds or flips a trade, the build is wrong.

#### Card 13.3 — Relative-strength filter `[context] [F2] [M]`
- **Hypothesis**: entries in the direction of the symbol's relative strength vs SPY
  (RS = symbol return − beta-free simple difference over trailing 60 completed minutes)
  outperform counter-RS entries.
- **Formulas**: `RS_60 = r_symbol,60m − r_SPY,60m` (simple return difference, no beta fitting
  — beta estimation is a fitted parameter and stays out until era 14 discipline exists);
  filter: longs require RS_60 ≥ 0 (shorts mirrored) — one registered variant.
- **Evaluate**: filter sweep vs champion.
- **Kill**: no survival → RS carries nothing at this horizon; record.
- **Traps**: simple difference, NOT a regression residual (no silent parameter fitting); both
  legs from completed bars.

#### Card 13.4 — Sector sympathy confirmation `[context] [F2] [S]`
- **Hypothesis**: entries confirmed by the sector ETF moving the same direction over the
  trailing 15 completed minutes outperform unconfirmed ones.
- **Build/Evaluate**: one registered confirm variant, sweep as above. **Run ONLY if 13.2 or
  13.3 survived** — sympathy is downstream of the same "context matters" hypothesis; if
  index context died, sector context inherits the verdict (router-enforced skip).
- **Kill**: as parents.
- **Traps**: sector map honesty (13.1); skip rule respected.

**Era-13 kill test**: if 13.2 and 13.3 both die, context is dead at this horizon — skip 13.4,
write the negative, and carry the finding into era 16's gate (a council routed by regime makes
no sense if context showed no conditioning power).

**Era-13 anti-goal additions**: context joins live in the research layer (never inside
`TapeEngine` — the engine stays single-symbol); filters only remove trades; no beta/regression
fitting; missing context = honest unknown.

---

## ERA 14 — Learning From the Tape (ML, gated)

**Mission**: cheap, local, deterministic ML in the narrowest honest role — a **veto-only**
filter on rule-based entries, plus retrieval ("similar past moments") and a clustering
cross-check. Nothing here generates signals; nothing here runs in the cloud; everything fits
the existing seeded-determinism regime.

**GATE (operator actions before the era starts)**: (1) the era's goal.md explicitly relaxes the
no-ML rule FOR THIS ERA with the tripwire constitution below written into its Anti-goals;
(2) `project-extensions/proposer-guidance.md` §9 ("No ML") is amended in the same commit to
match (Part 5.3's protocol) — the proposer and the constitution must never disagree.
**Prerequisites**: eras 5, 6, 7; a champion trade population as large as the library allows.

**Standing constraints**: sklearn-class models on CPU (seconds-to-minutes); every fit seeded;
model artifacts committed as JSON (coefficients/trees + scaler params + the pinned sklearn
version); inference at replay time is a pure function of the committed artifact — logistic
scoring is hand-rolled from the JSON (no runtime sklearn dependency); a GBT artifact ships as
an exported tree dump scored by a hand-rolled walker, or does not ship.

---

#### Card 14.1 — Meta-labeling veto filter `[ml] [F2/F4] [L]`
- **Hypothesis**: a small classifier predicting P(win) from the entry-context vector can veto
  the worst rule-based entries, improving holdout net R over the unfiltered champion.
- **Mechanism**: the rule decides WHEN and WHICH WAY (unchanged); the model only estimates
  HOW OFTEN that rule wins in this context — the meta-labeling division of labor that keeps
  the strategy interpretable.
- **Labels**: the EXISTING ternary excursion outcomes (`apps/backend/app/research/excursions.py`)
  at the champion's horizon: +1R-first = 1, −1R-first = 0, neither = excluded (2-class,
  cleanest; the exclusion count is reported). Labels use future data BY DESIGN — they are
  labels; the leakage rule applies to FEATURES.
- **Features (as-of entry ONLY — the leakage checklist)**: the 13 engine features at arm;
  zone class + distance-to-zone bps; spread bps; ToD bucket one-hot; RVOL-so-far; 6.11
  personality; 9.x survivors if any. Scaler (z-score) fit on TRAIN features only, committed
  in the artifact.
- **Models (exactly 2 registered)**: logistic regression (primary — hand-rolled inference);
  gradient-boosted trees (secondary, small: ≤ 100 trees depth ≤ 3, seeded). Veto thresholds
  τ ∈ {0.40, 0.50} registered ⇒ 4 candidates total in the registry.
- **Evaluate**: fit on TRAIN trades only → **run 14.4's tripwires BEFORE any holdout read**
  → then one holdout evaluation per candidate through the standard sweep (vetoed-champion vs
  champion), 6.2/6.3/6.7/6.8 gates in full.
- **Kill**: tripwire failure at any point (hard stop, not a tuning signal); or no candidate
  survives holdout → ML is dead THIS CYCLE; keep the atlas/report as documentation and
  re-enter only after the library materially grows (router notes the re-entry condition).
- **Traps**: the veto may only REMOVE trades (never add, never flip direction — tested);
  features as-of entry (any feature whose computation window extends past entry ts is
  leakage); class imbalance handled by threshold choice, never by resampling the holdout;
  sklearn version pinned in the artifact and asserted at fit time.

#### Card 14.2 — Tape signature library (k-NN retrieval) `[ml] [F2/F4] [M]`
- **Hypothesis**: the outcome distribution of the k most similar PAST tape windows (by
  feature-vector distance) is informative about the current moment — the tape-reader's
  "I've seen this before", made deterministic.
- **Formulas**: window vector = the 13 features (+ 9.x survivors) z-scored by TRAIN stats;
  distance = Euclidean; k = 25 (config); retrieval universe = TRAIN windows only; output =
  the neighbors' forward ternary outcome distribution + the top neighbors' dataset/ts
  references.
- **Build**: a study-harness tool + a cockpit "similar moments" panel (polish — read-only,
  from one canonical endpoint; the 9.x annotation tool's human-labeled moments enrich the
  display). As a VETO candidate (neighbors' outcome distribution below a threshold), it is
  one more registered candidate through the 14.1 sweep path.
- **Evaluate**: retrieval quality first (do neighbor outcomes beat the base rate on train?
  — a calibration study), veto sweep second.
- **Kill**: neighbor outcomes ≈ base rate on train → retrieval is a UI curiosity, not a
  filter; ship the panel (it is honest context), skip the veto.
- **Traps**: retrieval universe is TRAIN only even at cockpit display time (a holdout
  neighbor shown in the UI leaks holdout into the operator's judgment); z-scaler from train;
  ties broken by dataset id + ts (determinism).

#### Card 14.3 — Regime clustering vs the hand taxonomy `[ml] [F2/F4] [S]`
- **Hypothesis**: seeded k-means clusters over day-feature vectors (gap %, RVOL, trend ratio,
  realized range) condition the champion's edge better than 5.5's hand-made day types.
- **Build**: k = 4 (primary, config; silhouette scores for k ∈ {3,4,5} reported, not swept);
  seeded init; centroids committed as JSON with train-data provenance.
- **Evaluate**: 6.5-style conditioned edge report under both groupings; the comparison
  metric: which grouping produces more cells whose CI clears zero (with the SAME total n and
  the SAME registered cell count).
- **Kill**: clusters ≤ hand labels → keep the interpretable taxonomy (interpretability wins
  ties by rule).
- **Traps**: day-feature vectors from completed days (T5); cluster ASSIGNMENT of new days is
  nearest-centroid from the committed artifact, never a refit.

#### Card 14.4 — Overfit tripwires (mandatory, run before holdout) `[ml-guard] [F2] [M]`
- **Purpose**: the two tests that make era-14 survivable by weaker models. BOTH run after
  fitting, BEFORE any holdout read; failure = the era stops (hard, recorded).
- **Label-permutation test**: refit the full pipeline on train with labels shuffled
  (seeded), 100 repetitions; the veto's train-side improvement under true labels must exceed
  the 95th percentile of the shuffled improvements — else the pipeline is fitting noise.
- **Random-feature test**: add one seeded pure-noise feature to the feature set and refit; if
  the noise feature's |coefficient| (logistic, standardized) or importance (GBT) is NOT in
  the bottom quartile of all features, the fit is unstable at this n — FAIL.
- **Acceptance**: both tests are implemented with oracle fixtures (a known-signal synthetic
  population passes; a known-noise population fails) BEFORE being trusted on real data (T7).
- **Traps**: tripwires never become tuning loops ("re-run until they pass" is the exact
  failure they exist to prevent — one attempt per registered candidate set, results
  recorded).

**Era-14 kill test**: tripwire failure or zero holdout survivors ⇒ ML dead this cycle; the
re-entry condition (library ≥ 2× current trade population) is written into the status table.
The atlas, the retrieval panel, and the tripwire machinery remain as permanent assets.

**Era-14 anti-goal additions**: veto-only (never generate/flip); features as-of entry; train-only
fitting/scaling/retrieval; committed JSON artifacts with pinned versions; tripwires
before holdout, once, hard-stop semantics; no cloud/GPU/external training services.

---

## ERA 15 — Depth (gated: the Databento one-off)

**Mission**: the only era that buys data. Un-reserve the `BookLevelEvent` seam, ingest MBP-10
depth for a SMALL mechanism sample, and answer one question before any bulk spend: **does
visible depth add information beyond its L1 proxies (refresh scores, 9.8 iceberg inference,
9.3 imbalance)?**

**GATE (operator)**: approve the purchase path — new Databento account, **$125 free credits
first** (re-verify pricing at purchase time; figures here are as of 2026-07); mechanism sample
≈ 10–20 symbol-days of MBP-10 (Nasdaq TotalView-ITCH) for 2–3 mid-cap panel symbols. Bulk
purchase happens ONLY if 15.3 shows depth beating its L1 proxies. **Prerequisites**: eras 5, 6;
era 9's L1 results (they are the comparison baseline — and if 9.3/9.8 died at the atlas, say
so in the purchase decision: a dead L1 imbalance LOWERS the depth prior).

> *(Amendment 2026-08-16, rapid-microscope opening: the "era 9's L1 results" prerequisite now
> reads through the rapid-microscope machinery — the exact evidence that would justify opening
> this era is an L1 LIQUIDITY-family candidate (quote imbalance / depletion /
> `refill_consistent` replenishment) reaching `walkforward_survivor` on
> `historical_oos`-class evidence there, which both raises the depth prior and becomes 15.3's
> named comparison baseline. Those families dying at the Scout LOWERS the prior, exactly as
> Card 9.3's kill note already says. Diagnostic-class results count for neither direction.)*
>
> *(Follow-up 2026-08-18, "The Rapid Microscope" J-07 step 3, documentation-only — no code, no
> threshold, no purchase decision: the mechanism the amendment above promised now exists.
> `micro_graduation.py` (`docs/rapid-validation-spec.md` §8) implements the literal
> `walkforward_survivor`/`sealed_survivor` states this amendment names as the Depth-purchase
> evidence; either verdict for an L1 liquidity-family candidate — including a diagnostic-class
> `no survivor` at the Scout, which counts for neither direction per the amendment above and this
> era's own §10 disclosed L1-only-measurement limits — reads directly off that ledger when a
> future Era-15 kickoff needs it, rather than requiring re-derivation.)*

---

#### Card 15.1 — Databento adapter + depth events `[infra] [F3] [L]`
- **Purpose**: second vendor behind the EXISTING neutral seam.
- **Build**: new adapter module beside `apps/backend/app/providers/adapters/alpaca.py`
  implementing the same neutral interface (`apps/backend/app/providers/adapters/base.py`);
  vendor names confined to the adapter (the repo's provider-agnostic rail — `config.py`
  forbids vendor names even in comments); un-comment/implement `BookLevelEvent`
  (`apps/backend/app/providers/base.py` reserves it); dataset rows gain optional depth
  events (additive, like 5.1); `data_feed` basis strings for the new feed (e.g.
  `"itch_mbp10"`) — **depth-era results are never pooled with L1-era results** (feed-basis
  discipline).
- **Acceptance**: a committed small depth fixture replays deterministically; checksums,
  immutability, and split rules identical to 5.2's; all existing L1 datasets and tests
  untouched.
- **Traps**: the engine stays L1 (depth consumers live in the research observer, era-9
  infrastructure note applies doubly); adapter-confined vendor vocabulary; the purchase
  itself is an operator act — agents PREPARE the adapter against Databento's committed
  sample fixtures, they do not spend money.

#### Card 15.2 — Liquidity walls (executed-against only) `[depth] [F3] [M]`
- **Hypothesis**: large displayed size near a zone that gets EXECUTED AGAINST (not pulled)
  marks genuine defense; zones with executed-against walls reject better.
- **Formulas**: wall = displayed size at a price within the top-10 book ≥ W× the median
  top-10 level size (W config); **executed-against** = ≥ E prints trade at the wall's price
  while it stands (E config); pull-rate = walls removed without execution / all walls —
  measured and reported SEPARATELY (a high pull-rate is the spoof-noise finding, not a
  defense signal).
- **Evaluate**: study — zone touches with executed-against walls vs without vs L1-only
  proxies (9.8's score on the same events).
- **Kill**: executed-against walls ≈ 9.8's L1 inference → depth adds nothing here; feeds the
  15.3 verdict.
- **Traps**: counting posted-then-pulled size as defense is the canonical spoof trap — the
  executed-against discipline IS the card; round lots vs shares (T12) at depth scale too.

#### Card 15.3 — Depth-absorption rate vs L1 proxies (the purchase verdict) `[depth] [F3] [M]`
- **Hypothesis**: consumed-liquidity rate at a zone (`consumed / (initial displayed +
  refills)` over the touch window) predicts rejection/break better than the L1 absorption
  and refresh scores on the SAME events.
- **Evaluate**: head-to-head rank-IC (6.9 machinery) on identical touch events: depth
  measures vs `absorption_score`/`bid_refresh_score`/9.8 — the deliverable is the
  incremental-information verdict, with CIs.
- **Kill / verdict rule**: depth ≤ L1 proxies ⇒ **no bulk purchase** — the era closes with a
  written negative ("visible depth adds nothing beyond L1 inference at this granularity"),
  the seam stays implemented for the future, total spend ≈ $0 (credits). Depth > proxies ⇒
  the operator decides bulk scope with the measured effect size in hand.
- **Traps**: identical-event comparison (10.4's discipline); mechanism sample is TRAIN-only
  by declaration (too small to split — say so; nothing from it promotes anything).

#### Card 15.4 — One-sided thinning as breakout precursor `[depth] [F3] [S]`
- **Hypothesis**: near-side top-5 depth declining ≥ X% over Y seconds while price holds at a
  zone precedes breaks in that direction beyond base rate.
- **Formulas**: `thinning = (depth_near,t−Y − depth_near,t) / depth_near,t−Y` with
  X ∈ {30%, 50%}, Y = 60s (registered); outcome = break within 120s.
- **Evaluate**: study on the mechanism sample; registered-candidate follow-up only under a
  bulk purchase.
- **Kill**: as 15.3's verdict.
- **Traps**: displayed-depth decline has two causes (pulls vs executions) — report the split;
  only execution-driven thinning is "absorption failing", pull-driven thinning is
  information of a different kind (label them separately).

**Era-15 kill test**: the 15.3 verdict IS the era's kill test. Either way the outcome is
recorded in the status table with the spend total, and the adapter/seam remains.

**Era-15 anti-goal additions**: agents never spend money (operator-gated purchases); feed-basis
never pooled; mechanism sample never promotes; spoof-resistance (executed-against) discipline
on every "defense" claim.

---

## ERA 16 — Regime-Routed Champion Council (gated)

**Mission**: if the year produced conditioning evidence (6.5/13/14.3) and more than one
credible strategy, extend the champion concept to a **routing table: one champion per regime
cell**, still one trade at a time — "different tools for different days", honestly promoted
per cell.

**GATE (operator, documented rail amendment)**: the single-champion-pointer rule is an
era-variable rule (0.3); amending it requires: the era's goal.md states the new pointer schema
explicitly; the amendment note lands in the PnL ledger (like an epoch bump); the `default`
routing for any cell without a promoted specialist is the GLOBAL champion (the system degrades
to today's behavior, never to nothing). **Prerequisites**: eras 6 and 13; plus ≥ 2 surviving
strategies OR 1 survivor + at least one 6.5 cell whose CI cleared zero. If the year ends with
zero survivors, this era is unreachable — by design.

---

#### Card 16.1 — Routing table + per-cell promotion `[architecture] [F2/F4] [L]`
- **Build**: champion pointer becomes `{cell → (strategy_id, profile)}` with cells =
  day-type × (optionally ToD bucket) — the cell grammar is config-enumerated and SMALL
  (≤ 6 cells; every extra cell divides scarce n); promotion per cell runs the SAME gates
  (pooled 5.4 + CI 6.2 + BH 6.3 + costs 6.7 + replication 6.8) computed on that cell's
  trades only, with the cell's OWN min-n (which will be brutal — T2 applies with full
  force); `pnl_scan` remains the only pointer writer.
- **Acceptance**: a synthetic library where strategy A wins trend cells and B wins range
  cells promotes each into its cell and routes correctly on replay; any unpromoted cell
  routes to the global champion.
- **Traps**: cell entry-time legality — routing reads the cell AS-OF entry, so only
  entry-time-legal labels can route (gap class, RVOL-so-far — NOT the end-of-day trend
  label; 5.5's flag exists exactly for this); n-splitting means most cells stay unpromoted
  for a long time — that is correct behavior, not failure.

#### Card 16.2 — Council vs single champion, the final showdown `[evaluation] [F2] [M]`
- **Hypothesis**: the routed council beats the best single champion on pooled holdout AND on
  the accumulated forward ledger.
- **Evaluate**: one registered comparison: council vs global champion, pooled across cells,
  CI on the difference, cost blocks, forward-ledger corroboration (5.8's record is finally a
  decisive input — this is why it ran all year).
- **Kill**: council ≤ single champion ⇒ the routing table collapses back to the global
  pointer (the schema supports this natively: all cells → global) and the negative is
  recorded. Complexity must pay for itself or die.
- **Traps**: the forward ledger is corroboration, not the promotion basis (5.8's rule);
  entry-time-legal routing double-checked here because it is the #1 way this era fakes a
  win.

**Era-16 kill test**: 16.2 IS the kill test.

**Era-16 anti-goal additions**: cells config-enumerated and few; unpromoted cells route to
global; routing labels entry-time-legal only; the rail amendment documented in goal.md + ledger
before any code.

---

# Part 3 — Cross-cutting rules

## 3.1 The measurement-journey checklist

Every era's honest-measurement journey (the second-to-last journey, per 0.2) must satisfy ALL of
these before its acceptance can pass. Copy this checklist into the journey's acceptance criteria:

1. **Registered**: the full candidate/trial count was written to the 6.3 registry BEFORE results
   were computed (T6).
2. **Split-clean**: candidates fitted/calibrated on TRAIN only; holdout touched once; forward
   never feeds promotion (T4/T5).
3. **Null-matched**: the claim beats its MATCHED null (time-matched or random-levels where
   applicable), not only the uniform null (6.6).
4. **Interval-based**: CI reported (6.2); "positive" means CI low > 0, not point > 0.
5. **Haircut**: BH pass within the sweep's registered count (6.3).
6. **Costed**: the ×1/×2/×3 cost block present; promotion-grade claims survive ×2 (6.7).
7. **Replicated**: direction-consistent on ≥1 sibling symbol, or labeled `single_symbol` (6.8).
8. **Insufficiency-honest**: every cell/aggregate below min-n says `insufficient` and the claim
   text says so too (T2).
9. **Basis-stamped**: `levels_basis`, feed basis, fingerprint epoch, and (era 12+) runner mode
   stamped in the payload; no cross-basis pooling anywhere.
10. **Reproducible**: identical request ⇒ byte-identical report (seeded, sorted keys).

## 3.2 Negative-results discipline

A killed idea is a DELIVERABLE, not a failure. Its record goes three places: one line in the
status table (Part 5.2), the registry rows marked `evaluated` with their results (6.3), and — for
era-level kills — a short dated note in `reports/` (pattern:
`reports/research/negative-<era>-<slug>.md`, ~10 lines: hypothesis, n, CI, verdict). The year's
credibility is the sum of its honest negatives; the C4 whitepaper is assembled FROM these notes.

## 3.3 Determinism & seeds recap

*(AMENDED 2026-08-14, era-6 opening: the PRIMARY seed pattern is now the desk/playbook one —
a module-constant seed embedded in the procedure's own `*_parameters()` blob and hashed into
its result identity via per-row streams (`DESK_FORWARD_BASELINE_SEED`/`PLAYBOOK_BASELINE_SEED`
= 1729 and `REFEREE_SEED` = 271828 are the worked examples): zero Config fields, the
fingerprint untouched by construction, and the seed's provenance embedded verbatim in every
payload it shaped. Config-owned seeds via fingerprint Path A remain the FALLBACK for a seed a
frozen path must read.)* Config-owned seeds per procedure (`bootstrap_seed`, null seeds,
shuffle seeds, k-means seed, noise seed); every new Config-field seed follows fingerprint
Path A with counter-test; no wall-clock in any research payload; every served list explicitly
sorted; EWMA/stateful features document their initial state. If a procedure cannot be made
deterministic, it does not ship.

## 3.4 Escalation guidance for weaker models

Stop and ask the operator (or leave a status-table note and pick a different card) when:

- A card's Build contradicts the codebase and the fix is not obvious within one iteration.
- Any action would require a third fingerprint move (0.4 has exactly two).
- A gate seems to "want" loosening (min-n, BH q, CI level, kill threshold). Gates never loosen
  mid-year; if a gate blocks everything, that is a power-analysis finding — route to W1.
- You cannot state a card's kill criterion as an executable check.
- A result looks too good (CI far from zero at small n): assume leakage first; re-run the 3.1
  checklist; check T1/T4/T5 before believing it.

First reads when confused: `.claude/letter-to-future-sessions.md`, `.claude/anti-patterns.md`,
`.claude/judgment-rubrics.md`, then this document's Part 0.

---

# Part 4 — DO-NOT list (banned directions, with reasons)

1. **Sub-second / latency-sensitive strategies** — SIP consolidated timestamps, 15-min-delayed
   free data, and (permanently) no execution path: untestable AND unusable here.
2. **Options flow, dark-pool attribution, short-interest intraday, social sentiment** — no data
   source in scope; inventing proxies from L1 prints is fabrication, not research.
3. **Live or paper trading, ever, including "just to validate"** — tier-1 guard
   (`apps/backend/tests/test_no_execution_path.py`); identity rail 0.3.1.
4. **Deep learning / cloud training / external ML services** — cost rule, determinism rule, and
   at these sample sizes statistically indefensible. Era 14's sklearn-class ceiling is the max.
5. **Unbounded sweeps / grid searches** — every candidate set is small, named, pre-registered
   (T6). A grid over weights or thresholds is how false champions are manufactured.
6. **Annualized Sharpe / annualized returns / "expected profit" language** — an implied live
   claim from simulated fills (guard-tested from era 6 on).
7. **Weakening checksums, immutability, or verify-on-replay for convenience or speed** — 5.3
   provides the sanctioned fast path (manifest + spot-verify).
8. **Deleting, re-tagging, or content-perturbing datasets** (including "to fix a split") — T3/T4.
9. **Editing the pinned fingerprint literal outside 0.4 Path B** — the single most likely way a
   weak model corrupts the honesty machinery.
10. **Loosening min-n, BH q, CI level, or any gate to "unblock progress"** — T2; gates only
    tighten mid-year.
11. **News-driven event trading** — no news feed exists; the 5.6 earnings calendar is
    exclusion-only, never a signal source.
12. **New markets this year (HK equities, futures, crypto)** — *parked, not banned*: a second
    market means a new adapter, new session grammar, new microstructure priors, and a split
    research focus. Revisit as a year-2 question once this panel has verdicts. (The neutral
    adapter seam built in era 15 makes a future HK adapter cheaper.)
13. **Spoof/manipulation detection as a signal product** — 15.2 measures executed-against
    defense only; classifying other participants' intent is out of scope and unverifiable here.

---

# Part 5 — Operating system for the year

## 5.1 The router — "what do we do next?"

Run this algorithm whenever a session ends (no judgment required):

```
1. If a contingency trigger (5.5) is active → follow that branch first.
2. Candidate set = eras whose status is not {done, killed, skipped-this-pass} in the
   status table, whose prerequisites (Part 1 table) are ALL 'done', and whose gate is open.
3. If an era's gate needs an operator act (12 scope confirm, 14 amendment, 15 purchase,
   16 amendment) and the operator is absent → mark 'skipped-this-pass' in the status
   table and continue; revisit next pass.
4. Pick the lowest-numbered candidate. Ties do not exist (numbering is total).
5. If ANY era's kill test or power analysis said "grow the library" → run W1 before or
   alongside the picked era.
6. If the candidate set is empty → run W3 (consolidation); if still empty after W3,
   the catalog is exhausted → C4 (the year's honest synthesis) or year-2 planning.
Special rule: after era 6 completes, apply the 5.3 proposer amendment once. Proposer
journeys then handle small evidence-backed items INSIDE sessions; this catalog governs
era-scale direction. They do not conflict: the proposer is bound by the same gates.
```

## 5.2 The status table (append-only; every completed session adds one row)

Columns: `date · era/workstream · session id · verdict (done | killed | split | skipped-this-pass
| blocked) · key finding (ONE sentence) · corrections to this doc (or "none")`.

| Date | Era | Session | Verdict | Key finding | Corrections |
|------|-----|---------|---------|-------------|-------------|
| 2026-07-05 | 3 (tape_to_profit) | `tape_to_profit` | done | Honest measurement machine complete; `v1` loses money on real tape; edge report correctly finds "no positive-edge dataset". | none |
| 2026-07-06 | 4 (structure-and-tape) | `tape_to_profit_support_resistence` | done | All 7 journeys shipped; `structure_tape` honestly unevaluable on committed data (n=1 < 5) — the founding question remains empirically open pending the library. | none |
| 2026-07-12 | 5 (The Library) — REDEFINED in execution | `yahoo_fetch` | done | The era pivoted to a keyless Yahoo Finance BAR library (6 journeys; 4h honestly resampled from 1h; derived SQLite index); the Card-5.2 tick-recorder library (≥150 symbol-days of trade/quote windows) was NOT built — bars and tick datasets are different data families. | Era-6 gate re-scoped per evidence family (era-6 opening note, 2026-08-14). |
| 2026-07-16 | interlude (outside catalog) — "Tradable Wall" | `tradable_wall` | done | Tradable ≤10-band map + 12-symbol scan registry + 3-way edge report; 11 durable feed=sip tick windows / 10 symbols recorded into the persistent dataset store — the REAL tick corpus to date (~12 partial 2.5h windows). | none |
| 2026-07-17 | interlude (outside catalog) — "Fast Wall" | `fast_wall` | done | Store stat-caches + durable dataset index, operator-run edge-report compute (GETs never compute), resumable parallel sweep, setups scan cache. | none |
| 2026-07-24 | interlude (outside catalog) — "Clean Slate" demolition | `clean_slate` | done | Journal era deleted (14 routes, 3 pages → two-page product); the one product move = fingerprint epoch bump `4d665603569b9dbf` → `08e471b10130e1e2` (§0.4 Path B). | §0.4 epoch note added (2026-08-14). |
| 2026-07-31 | B (operator pivot, outside catalog) — "The Desk" | `desk` | done | `/desk`: fetched S&P100 universe, append-only screen ledger + ranked briefing, touch-anchored forward-return rail v2, deep fine-bar backfill; 21 journeys. | none |
| 2026-08-11 | B2 (operator pivot, outside catalog) — "The Playbook" | `playbook` | done | Nine pre-registered Graifer/Schumacher intraday detectors on the desk's own 5m/1m bars; append-only playbook corpus + back-scan + descriptive evidence view with seeded same-session anchors; zero statistics gates (deliberately era-6's). | none |
| 2026-08-13 | operator interlude (outside catalog) — band context | main `9e65bb0`…`83c24a8` | done | Read-side band-context lens v1→v2 (bracket frame)→v3 (basis-bounded cache) + the 9-key cohort vocabulary + refresh-chain steps 6–7 + `/desk` context columns/filters/drill-ins; ratified as R-4 in the era-6 goal. | `docs/playbook-detector-spec.md` §6 version string reconciled v2→v3 (2026-08-14). |
| 2026-08-16 | 6 (The Referee) | `referee` | done | Fail-closed confirmatory layer shipped (evidence contract, seeded permutation/CI/BH core with oracle attestation, ToD/context-matched nulls, immutable pre-registration boundary, one permanent checkpoint per hypothesis, `pnl_scan` certificate interlock, 3 `/desk` sections, MCP v5 = 22 tools); 12 journeys, zero `corroborated` at close — the system working as designed. | Row appended 2026-08-16 at the rapid-microscope opening (the referee session's closing agent omitted it); §5.3 proposer amendment applied in the same commit. |
| 2026-08-24 | operator pivot (outside catalog) — "The Rapid Microscope" | `rapid-microscope` | done | Rapid-validation funnel shipped (observer/snapshots, Scout + hash-chained trial ledger, walk-forward, sealed Vault, graduation, MCP → 28 tools): 13 real candidates, 0 survivors (killed_null 10 · killed_economic 6 · killed_insufficient_n 3), Study 2 killed on the merits (p 0.366), Studies 1/3 parked pending owner spec, zero `historical_oos`, Vault sealed/untouched — the funnel kills honestly. | Row appended 2026-08-26 at the hypothesis-foundry opening. |
| _(next session appends here)_ | | | | | |

Protocol: the row is written by the human operator or the session's closing agent AT session
end, in the same commit as the session's showcase artifacts. One sentence per finding — the
details live in the session's reports; this table is the year's map.

## 5.3 Proposer amendment protocol (self-evolution hook)

`project-extensions/proposer-guidance.md` ALREADY exists and drives the goal-proposer. Apply
these amendments **once, right after era 6 completes** (one commit, operator-approved):

1. **§1 (usefulness lens), append**: "Consult `docs/research-directions.md`: rank enabling work
   that unblocks the router's current or next eligible era (Part 5.1) above other speculative
   work; never propose a journey that belongs to an era whose gate is closed; never propose a
   journey that contradicts a kill verdict recorded in the status table (Part 5.2)."
2. **§2 (survey protocol), append**: "Read `docs/research-directions.md` Part 5.2 (status
   table) before proposing."
3. **§3 (proposal schema)**: add optional field `"catalog_ref": "<card id or 'none'>"`.
4. **§9 (hard limits)**: leave UNTOUCHED until a gated era formally amends a rule. When era 14
   (ML) or era 16 (council pointer) opens, the SAME commit that rewrites `docs/goal.md` for
   that era updates the matching §9 line — e.g. era 14 replaces "No ML, no online tuning, no
   fitted thresholds" with "No ML beyond the committed frozen artifacts of the
   learning-from-the-tape era's registered candidates; no refitting outside a registered era;
   veto-only" — and the era's closing commit re-tightens it to cover only what was actually
   promoted. The proposer file and goal.md must NEVER disagree about a rule.

## 5.4 Perpetual workstreams (run demand-driven, forever; none is an era)

- **W1 — Recorder top-up**: operator starts the 5.2 job for new dates/symbols; agents run the
  5.6 quality gate and confirm forward-ledger auto-append. Every top-up buys statistical power
  and forward evidence — W1 is always a productive default when nothing else is eligible.
- **W2 — Forward-ledger review** (read-only, monthly-ish): compare the champion's forward
  record vs its holdout expectation (same metrics, 6.1); divergence is an input to W3, never a
  reason to hot-patch anything.
- **W3 — Consolidation review** (small session): re-run the edge report + conditioned reports
  on the grown library; graduate forward datasets per 5.8's bulk date-hash rule; re-run the
  power analysis; update the status table; re-check whether any skipped gate should reopen.
- **W4 — Basis audit** (small, periodic): enumerate active bases (fingerprint epoch,
  `levels_basis`, feed bases, runner modes) and grep reports for cross-basis pooling; confirm
  the pinned fingerprint still matches its documented epoch.
- **W5 — State-of-the-edge report** (annual, or at C4): assemble Part 3.2's negative notes +
  the ledger + the forward record into one honest document: what was tried (registry counts),
  what survived, what died, what it cost, what the edge is (or that there is none at this
  granularity). W5 is the year's deliverable to the human regardless of outcome.

## 5.5 Contingency tree

- **C0 (trigger check, evaluated at W3)**: eras 7–10 all done with ZERO promoted survivors AND
  the library met its 5.2 targets AND the 6.x power analysis says a plausible edge WAS
  detectable. → Operator picks exactly one pivot:
  - **C1 — Universe pivot**: re-run the key registered sweeps on tier-B-only (or a new screen
    per 5.2's criteria — wider-spread names where inefficiency is likelier, costs honestly
    reported). One era-sized session.
  - **C2 — Horizon pivot**: prioritize era 12 if not yet run; if run and dead, register ONE
    longer intraday horizon variant set (exit horizons × {2, 4} — small, named).
  - **C3 — Cost re-examination**: if 6.7's calibration showed the ASSUMED cost model exceeds
    MEASURED effective costs, re-run the promotion gates at calibrated costs (pre-registered
    as its own sweep — this is a legitimate model correction, not gate-loosening; the
    direction of the correction is fixed by measurement, not by desire). If edges exist gross
    but die at calibrated net: that IS the whitepaper finding — "the tape reads truly, but the
    edge is smaller than retail costs."
  - **C4 — The whitepaper era**: run W5 as a full era: `reports/state-of-the-edge.md` —
    methodology, every registry trial, every negative note, CIs, the honest conclusion, and
    the product's residual value (a disciplined journal/training/measurement instrument is a
    real product even with no demonstrated trading edge). **C4 is a legitimate success of the
    honesty machine, not an admission of failure** — it is the difference between this project
    and every backtest-porn repository on the internet.
- **C0-negative** (survivors exist somewhere): no contingency; the router continues normally.

## 5.6 Maintaining this document

- The status table (5.2) is append-only; corrections to card content are edited in place with a
  one-line note in the row that prompted them.
- New idea cards may be ADDED (by the operator, or by the proposer via a `catalog_ref: none`
  proposal that the operator accepts) — they join an existing era or a clearly-marked appendix,
  with the full card template. Cards are never deleted; a dead card keeps its kill verdict.
- If this document and `docs/goal.md` conflict, goal.md wins for the running era; fix this
  document afterward.
- Pricing facts (era 15) are "as of 2026-07" — re-verify before any purchase.

---

*Closing note from the author: the system you inherit is unusually honest — it has proven it can
say "no edge yet" and survive. Guard exactly that. The library will tempt you with patterns;
the registry, the gates, and the kill criteria are how you tell the ones that are real. Ship
negatives proudly, spend calendar time (not just tokens) where forward evidence requires it,
and if the year ends at C4, end it there without flinching: an honest "no" is worth more than
every false "yes" ever promoted. — Fable 5, 2026-07-06*





