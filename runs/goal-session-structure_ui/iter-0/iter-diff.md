# Iteration diff (bounded)

Files changed: 32. Shown in full: 20.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `reports/goal-session-tape_to_profit_support_resistence-delivered.html` (373 diff lines)
- `reports/goal-session-tape_to_profit_support_resistence-delivered.md` (50 diff lines)
- `reports/goal-session-tape_to_profit_support_resistence-index.html` (28 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/engine.pid` (7 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/session.json` (24 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/state/enhancement-proposals.jsonl` (9 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/state/proposer-result.json` (13 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/summary.md` (113 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/telemetry.jsonl` (16 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/trace/trace.jsonl` (10 diff lines)
- `diff --git aruns/goal-session-structure_ui/trace/.lock bruns/goal-session-structure_ui/trace/.lock` (3 diff lines)

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `docs/goal.md` (195 lines not shown)

```diff
diff --git a/docs/goal.md b/docs/goal.md
index d773a52..47a8bad 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1,343 +1,296 @@
-# Tapeology — Project Goal (Era 4: the structure-and-tape evolution)
+# Tapeology — Project Goal (Interlude: Structure, made visible — UI surfacing)
 
-> Eras 1–3 are the **foundation** of this goal and MUST NOT regress. Eras 1–2 (tape reading + the
+> Eras 1–4 are the **foundation** of this goal and MUST NOT regress. Eras 1–2 (tape reading + the
 > research evolution, journeys J-01 – J-68, GOAL_ACHIEVED) are archived at
-> [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md). Era 3 (the
-> profit-research evolution — the measurement machine, its own journeys J-01 – J-09, GOAL_ACHIEVED)
-> is now frozen foundation; its full record lives in git history and
-> `reports/goal-session-tape_to_profit-delivered.md`.
+> [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md). Era 3 (the profit-research
+> measurement machine, J-01 – J-09, GOAL_ACHIEVED) and Era 4 (the structure-and-tape evolution,
+> J-01 – J-07, GOAL_ACHIEVED) are now frozen foundation; their full records live in git history and in
+> `reports/goal-session-tape_to_profit-delivered.md` and
+> `reports/goal-session-tape_to_profit_support_resistence-delivered.md`.
+>
+> **This chapter is an operator-directed UI-surfacing interlude, not one of the numbered research eras.**
+> It pulls forward the intent of Card 5.9 ("Library health & UI") in
+> [`docs/research-directions.md`](research-directions.md). Era 5 "The Library" (recording real
+> multi-symbol/multi-regime data) remains the next headline research era per that document's router
+> (Part 5.1); this interlude does not consume the Era-5 slot and adds no research finding — it makes the
+> era-4 structure work visible in the app.
 
 ## Vision
 
-Tapeology reads the tape — one US-stock ticker in, live order flow classified into five states
-(`buyer_control`, `seller_control`, `bid_absorption`, `ask_absorption`, `unclear`) on the defining
-principle of **price impact, not raw aggression**. Era 3 added an honest measurement machine —
-persisted train/hold-out datasets, deterministic backtests in R AND $ beside a null baseline, a
-hold-out promotion gate, a PnL ledger, and a baseline-edge report — and used it to prove that the first
-strategy, **v1** (enter WITH tape "control", no profit target), **loses money** on real tape.
-
-The **structure-and-tape era** asks the sharper question: **does the tape read become profitable when
-it is anchored to price structure — support and resistance — instead of read in a vacuum?**
-
-The strategy hypothesis, in the owner's terms:
-
-- **Multi-timeframe support/resistance.** Detect horizontal levels on long-term (1d / 1w / 1mo),
-  mid-term (1h / 4h / 8h), and shorter timeframes. Levels that align across timeframes matter more.
-- **Confluence → conviction classes.** Where levels from several timeframes cluster tightly, grade the
-  zone **A / B / C**; better confluence → higher conviction.
-- **Tape confirmation at the level.** When price reaches a level, read the tape to judge whether it
-  **rejects** (defenders hold — absorption / opposing control) or **breaks through** (control with real
-  price impact) — and take the long or short that implies.
-- **Class-scaled risk and size.** Better class → tighter stop (an A-class level defended on the tape can
-  justify a stop ~1bp beyond it), a more favourable reward target, and a larger **simulated** position;
-  worse class → wider stop, smaller size, or no trade.
-
-This rides the frozen foundation: the tape engine already emits exactly the "reject vs breakthrough"
-states, and the measurement machine already judges any strategy honestly on hold-out data. The genuinely
-new capability is **price structure** — the engine has never had a bar, a level, or a timeframe.
-
-Absolutes, unchanged from day one: **no broker, no order placement (real or paper), no ML, no advice.**
-Every PnL figure — and every "position size" — is a simulated measurement of the past under disclosed
-assumptions, sent nowhere.
+The era-4 structure-and-tape stack is real and honest — multi-timeframe support/resistance **levels**,
+**A/B/C confluence zones**, a **strategy registry** (`v1` + `structure_tape`), and the honest
+`structure_tape`-vs-`v1` **backtest comparison** with its per-class PnL breakdown. But every one of these
+lives ONLY on REST / MCP / CLI surfaces: the web app still shows its four pre-era-4 tabs, and a person
+cannot **see** any of it. Research a human cannot inspect erodes trust.
+
+This interlude gives the structure work a browser home: a read-only **Structure** view that renders levels
+and confluence zones on a price chart, the strategy registry and current champion, and the honest
+`structure_tape`-vs-`v1` comparison with its per-class A/B/C breakdown. It reads **every** value verbatim
+from its existing canonical endpoint, recomputes nothing, and is honest about the mostly-empty keyless data
+reality. It changes **no** computation, strategy, promotion, or measurement — it is pure visibility.
+
+Data reality, stated up front: on the committed **keyless** fixture there are no recorded multi-timeframe
+bars, so levels/zones are largely empty and `structure_tape` is honestly unevaluable (n below the minimum).
+The UI is built to say that plainly. Real levels, real zones, and a genuine hold-out comparison await Era 5
+"The Library" recording real bars; this interlude surfaces what exists and is honest about what does not.
 
 ## Target Users
 
-- The discretionary intraday trader (the project owner), whose structure + tape method this era
-  formalizes into a deterministic, honestly-measured research strategy.
-- AI dev-chain agents (the goal-mode loop) building and judging it through the read-only MCP tools and
-  the hold-out edge report.
-
-## Foundation invariants (still law — eras 1–3)
-
-The era-1–2 constitution is imported verbatim from
-[`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md) and remains binding on ALL new
-code: price-impact-over-aggression; honest uncertainty (`unclear` on weak/mixed evidence, feed- and
-halt-aware); no fabricated data (every failure surfaces an explicit state); single source of truth;
-no magic numbers (every threshold from config); provider-agnostic engine (vendor SDKs behind one
-adapter seam); deterministic & reproducible (byte-identical); no secrets in source; research stays
-read-only over the engine; journal/record integrity (append-only); source/feed/`config_fingerprint`
-honesty (never pool across feeds/fingerprints); dd-MM-yyyy dates; the existing surfaces
-(`/`, `/journal`, `/journal/[id]`, `/studies`, `/performance`) stay intact.
-
-In addition, **era 3 (the profit-research measurement machine) is now frozen foundation**:
-
-1. The **tape engine** emits its five states byte-identically under the `default` profile; the live
-   cockpit and every archived surface stay unchanged (equivalence-tested; `config_fingerprint` pinned).
-2. The **measurement machine** — the dataset store (immutable, checksummed, frozen train/hold-out
-   splits), the deterministic backtest engine (R AND $, seeded null baseline, full provenance),
-   versioned profiles with the frozen `default`, the champion pointer, the append-only PnL ledger,
-   `/performance`, the candidate sweep (`pnl_scan`), the baseline-edge report (`edge_report`), and the
-   read-only MCP server — stays intact and is the **only** way this era judges profit.
-3. **v1 and `default` are frozen.** The new strategy is additive and versioned; it never mutates v1,
-   `default`, or any engine default, and never becomes the champion except by an honest hold-out
-   promotion.
+- The project owner (a discretionary intraday trader) who wants to **see** the computed structure and the
+  honest `structure_tape`-vs-`v1` comparison inside the app — not only via `curl` or the MCP tools.
+- AI dev-chain agents (the goal-mode UI chain) building and browser-verifying the new surface.
+
+## Foundation invariants (still law — eras 1–4)
+
+The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md)) and the
+era-3 measurement machine remain binding verbatim on ALL new code: price-impact-over-aggression; honest
+uncertainty; no fabricated data; single source of truth; no magic numbers; provider-agnostic engine;
+deterministic & reproducible; no secrets in source; research read-only over the engine; journal/record
+integrity; source/feed/`config_fingerprint` honesty; the existing surfaces (`/`, `/journal`,
+`/journal/[id]`, `/studies`, `/performance`) stay intact.
+
+In addition, **era 4 (the structure-and-tape stack) is now frozen foundation**:
+
+1. The **tape engine** emits its five states byte-identically under `default`; the live cockpit and every
+   archived surface stay unchanged (equivalence-tested; `config_fingerprint` `4d665603569b9dbf` pinned).
+2. The **structure computations** — the bar store, the deterministic S/R levels module, the confluence
+   A/B/C grading, the strategy registry (`v1` + `structure_tape`), the class-scaled stop/reward/size math,
+   the per-class backtest breakdown, and the named-strategy sweep — stay byte-identical and are the **only**
+   owners of those values. This interlude reads them; it never recomputes or re-implements them.
+3. **`v1`, `default`, and the champion pointer are frozen.** This interlude adds a read surface only; it
+   never mutates a strategy, a profile, an engine default, or the champion pointer, and it moves the
+   champion **never** (promotion remains the sweep's act on hold-out data).
 
 ## Success Criteria
 
-In priority order — honesty and non-regression outrank any profit number:
+In priority order — honesty and non-regression outrank everything:
 
 1. **Nothing existing regresses.** The full backend suite stays green, the engine equivalence test keeps
-   proving byte-identical `default` outputs, and every era-1–3 surface and capability keeps working.
-2. **Bars are trustworthy.** A recorded multi-timeframe bar series replays byte-identically, re-runs are
-   identical, checksums verify, and the feed is stamped; the free-plan capability is recorded honestly.
-3. **Levels and classes are deterministic and lookahead-free.** Support/resistance and A/B/C confluence
-   classes reproduce byte-identically and, at any as-of time T, use only bars at or before T.
-4. **The structure strategy is additive and honestly measured.** `structure_tape` is a registered
-   strategy beside a frozen v1; it is judged only by the era-3 machine and promoted only by beating the
-   champion on the frozen hold-out set at ≥ the configured minimum n — train-only wins are labelled
-   overfit and rejected.
-5. **PnL stays honest.** Every $ appears with its R, its n, its train/hold-out basis, its fee/slippage
-   assumptions, its null baseline, and the visible "simulated — not indicative of live results" register;
-   "position size" is an explicitly simulated notional that transmits nothing.
-6. **Determinism & single source of truth.** Bars, levels, and classes are each computed once, owned by
-   one canonical endpoint, and read verbatim by REST, MCP, and reports; every parameter comes from config.
+   proving byte-identical `default` outputs, `config_fingerprint` stays `4d665603569b9dbf`, and every
+   era-1–4 surface and capability keeps working.
+2. **The structure stack is visible.** A **Structure** tab renders, for a chosen symbol, its S/R levels and
+   A/B/C confluence zones on a price chart; the strategy registry (`v1` + `structure_tape`) with the current
+   champion; and a `structure_tape`-vs-`v1` backtest comparison with the per-class A/B/C breakdown.
+3. **Single source of truth is visibly preserved.** Every displayed value — a level's price/timeframe/class,
+   a zone's class, net R, net $, n, `insufficient_sample`, the champion — is read **verbatim** from its
+   canonical endpoint and matches the REST/MCP payload byte-for-byte. The UI recomputes nothing (no
+   client-side grading, PnL math, or aggregation).
+4. **Honesty is visible.** Empty and degraded states — no recorded bars, no levels, no zones, insufficient
+   n, missing credentials — each render as an explicit, distinct state; nothing is fabricated; the
+   "simulated — not indicative of live results" register appears verbatim wherever simulated PnL or size is
+   shown.
 
 ## Key Capabilities
 
-Layered strictly on top of the era-1–3 capabilities, which remain unchanged.
-
-1. **Multi-timeframe bar store.** Recorded OHLC bar series per symbol + timeframe + window + feed,
-   immutable and checksummed (mirroring the dataset store), stored under the research data dir
-   (gitignored except a committed multi-timeframe fixture). Fetched through a new neutral `RawBar` on
-   the adapter seam via Alpaca `get_stock_bars` (`TimeFrame` Minute/Hour/Day/Week/Month); recording is
-   an explicit credentialed research action.
-2. **Deterministic support/resistance detection.** A config-owned module deriving horizontal levels per
-   timeframe from bars — swing pivots (fractal extremes over ±N neighbours) and prior-period extremes
-   (prior day/week/month high/low/close) — each with a strength (timeframe weight × touch count),
-   computed with no lookahead. No ML, no fitting.
-3. **Confluence classification.** Deterministic clustering of levels across timeframes into confluence
-   zones graded **A / B / C** by config thresholds; served beside the levels.
-4. **The `structure_tape` strategy.** A second config-owned strategy in a strategy registry beside the
-   frozen `v1`: entries arm where price enters a classified level's proximity band AND the tape confirms
-   direction (rejection → fade; breakthrough → follow), reusing the engine's existing level-cross +
-   state-native arming. Exits and R/$ math reuse the era-3 backtest engine.
-5. **Class-scaled risk and simulated sizing.** Level class drives the stop distance (A ≈ 1bp), the reward
-   target (R:R toward the next opposing level), and a simulated position notional — all config-owned,
-   reported per class as caveated simulated PnL.
-6. **Strategy A/B on the measurement machine.** The edge-report / sweep path, generalized to evaluate a
-   named strategy (not only the champion), so `structure_tape` is compared to `v1` on train AND hold-out
-   with the same honesty guards and the same hold-out promotion gate.
+Layered strictly on top of the era-1–4 capabilities, which remain unchanged. This interlude adds **no**
+backend computation and **no** new canonical value — only a read surface and one additive nav entry.
+
+1. **A Structure route/tab.** A new `/structure` page following the `/performance` page pattern; its nav
+   entry is owned by the backend route registry (`GET /meta/ui-routes`), so the client NavBar surfaces it
+   without a hardcoded list.
+2. **Levels & confluence-zones visualization.** For a chosen symbol + as-of time, a `lightweight-charts`
+   price chart (candles from the symbol's recorded bar series) with one price line per level labelled by
+   timeframe, plus a confluence-zones table badged **A/B/C** — the class read verbatim from the served
+   `zone.class`.
+3. **Strategy registry & champion view.** `v1` and `structure_tape` shown side by side (entry rule, exit
+   precedence, `structure_tape`'s class-scaled `stop_bps_by_class` / `r_multiple_by_class` /
+   `size_multiple_by_class`), with the champion (founding `v1`/`default`) badged.
+4. **`structure_tape`-vs-`v1` comparison.** Run both strategies on a chosen dataset via the existing
+   backtest job (reusing the Studies job/poll pattern), then render side-by-side aggregates + the per-class
+   A/B/C breakdown (`aggregates_by_class`, `insufficient_sample` shown verbatim), beside the champion
+   pointer and founding baseline row. On the keyless reference dataset it honestly shows `structure_tape`
+   as a non-survivor and the champion unchanged.
 
 ## Non-Goals
 
-- No brokerage integration, order placement, routing, or execution of any kind — **neither real-money
-  nor paper-trading APIs**. Simulated fills exist only inside the offline backtester.
-- No machine learning, no online/in-engine tuning, no fitted thresholds — S/R detection, confluence
-  scoring, and class thresholds are bounded, config-enumerated, offline, and hold-out-validated.
-- No trading advice, imperative cues, prediction language, or expected-return claims. Simulated PnL and
-  simulated sizing describe the past under stated assumptions.
-- No account, capital, portfolio, or real position management; no compounding equity projections. Class
-  "position size" is a simulated per-trade notional only.
-- No stock scanning/screening, multi-symbol dashboards, news/sentiment, fundamentals, or general-purpose
-  charting — unchanged from the archived eras.
-- No auto-modification of the `default` profile, the `v1` strategy, or any live-cockpit behaviour.
+- **No new backend computation or endpoint for the UI.** The Structure view consumes existing canonical
+  endpoints only; it introduces no second source of truth. If a genuinely new value were ever needed it
+  would get exactly one owning endpoint — but the intent here is **zero** new computation.
+- No brokerage integration, order placement, routing, or execution of any kind — **neither real-money nor
+  paper-trading APIs**. Running a backtest is an offline research job over already-recorded immutable
+  datasets, exactly as the Studies page already does; it places nothing.
+- No machine learning, no trading advice, no imperative cues, no prediction or expected-return language in
+  any UI copy.
+- No general-purpose charting, multi-symbol dashboards, stock scanning/screening, news/sentiment, or
+  fundamentals — unchanged from the archived eras.
+- No mutation of `default`, `v1`, the engine, the `config_fingerprint`, or any era-1–4 behaviour; the only
+  backend edit is the additive `/structure` entry in the route registry.
+- **No champion promotion from the UI.** The comparison view runs backtests and diffs their reports; it
+  never moves the champion pointer — promotion stays the sweep's hold-out act.
+- **No `/datasets` library-inventory page** (that is roadmap Card 5.9's own scope, dependent on Era-5
+  regime/tradeability data) — out of scope for this interlude.
 
 ## Constraints
 
-- **Stack (carried over):** Backend Python 3.12 + FastAPI (uvicorn, REST + WebSocket), pytest
-  (venv `apps/backend/.venv/`, `uv`). Frontend Next.js 15 + TypeScript + Tailwind v3 (npm),
-  `lightweight-charts`. Research persistence in journal-scoped SQLite (`TAPEOLOGY_JOURNAL_DB`).
-  Backend `http://localhost:8000`, frontend `http://localhost:3000`. Sim tickers stay keyless.
-- **Bar discipline:** bar series live under the research data dir (gitignored except a committed
-  multi-timeframe fixture), are immutable once recorded (checksum verified on load), and stamp their
-  symbol, timeframe, UTC window, and feed. Free-tier Alpaca serves historical bars with a ~15-minute
-  recency delay and a request-rate limit; bulk backfills throttle and never fetch the most recent bar.
-- **Structure discipline:** all S/R parameters (pivot lookback N, touch tolerance, confluence band,
-  class thresholds, proximity band) are config-owned; levels/classes are computed once, served from one
-  canonical endpoint, and carry **no lookahead** (as-of time T uses only bars ≤ T).
-- **Strategy discipline:** `v1` and `default` are frozen and equivalence-tested; `structure_tape` is
-  additive-only in a strategy registry; every artifact touching a non-default strategy is stamped with
-  its strategy id; the strategy id folds into the backtest provenance.
-- **PnL honesty register:** unchanged from era 3 — a $ never without its R, n, basis, assumptions, null
+- **Stack (carried over):** Frontend Next.js 15 + TypeScript + Tailwind v3 (npm), `lightweight-charts`,
+  dark-only. Backend Python 3.12 + FastAPI. Backend `http://localhost:8000`, frontend
+  `http://localhost:3000`. Sim tickers stay keyless.
+- **UI read discipline:** the Structure view reads ONLY canonical endpoints — `/research/bars`,
+  `/research/levels`, `/research/strategies`, `/research/profiles`, `/research/datasets`,
+  `/research/backtests` (+ `/{id}`), `/research/pnl/ledger`, and `/meta/ui-routes` — and renders their
+  values **verbatim**. Zero client-side recomputation of levels, classes, PnL, aggregates, or the champion.
+- **Nav discipline:** the Structure tab is registered in the backend route registry
+  (`apps/backend/app/meta.py` `UI_ROUTES`, the owner) and surfaced via `GET /meta/ui-routes`; the client
+  NavBar is data-driven and MUST NOT hardcode the route.
+- **Honest-state discipline:** no fabricated data; `no_bar_series_for_symbol`, `insufficient_sample`, empty
+  arrays, and the missing-credentials (503) state each render as an explicit, distinct UI state.
+- **PnL honesty register:** unchanged from eras 3–4 — a $ never without its R, n, basis, assumptions, null
   baseline, and the visible "simulated — not indicative of live results" register; sub-minimum-n results
   labelled "insufficient sample"; train and hold-out never pooled.
-- **MCP read-only discipline:** the MCP server exposes no mutating tools, proxies the canonical REST API,
-  adds no second computation path, and fails explicitly when the backend is unreachable.
-
-### Glossary (new terms; archived glossary still applies)
-
-- **Bar / timeframe** — an OHLC candle for a symbol over a calendar interval (1m/1h/4h/8h/1d/1w/1mo); a
-  recorded, checksummed, immutable bar series is the multi-timeframe data foundation.
-- **Support / resistance level** — a horizontal price derived deterministically from bars (swing pivot or
-  prior-period extreme), carrying a timeframe, a type, a touch count, and a strength.
-- **Confluence zone / class** — a cluster of levels from several timeframes within a tolerance band,
-  scored and graded **A / B / C** by conviction.
-- **structure_tape** — the era-4 strategy: tape-confirmed entries at classified levels, with class-scaled
-  stop, reward, and simulated size.
-- **Reject / breakthrough** — the two tape readings at a level: rejection (absorption / opposing control
-  holds the level → fade) vs breakthrough (control with price impact through the level → follow).
+- **Frozen-foundation discipline:** no edits to `config.py` (fingerprint `4d665603569b9dbf`),
+  `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the engine, or any existing
+  surface's behaviour, beyond the additive nav-registry entry.
+- **MCP read-only discipline:** unchanged — the MCP server stays a byte-identical proxy of the GET surface
+  and gains no new tool for this interlude.
 
 ## Product Shape
 
-Nav (top bar) is unchanged: **Cockpit `/` · Journal `/journal` (+ `/journal/[id]`) · Studies `/studies`
-· Performance `/performance`**. This era's new surfaces are machine surfaces (REST + MCP) — a future
-levels view is optional and out of the data-foundation scope.
+Nav (top bar) gains exactly ONE tab: **Cockpit `/` · Journal `/journal` (+ `/journal/[id]`) · Studies
+`/studies` · Performance `/performance` · Structure `/structure` (new)**. The new tab's entry is owned by
+`apps/backend/app/meta.py` `UI_ROUTES` and served via `GET /meta/ui-routes`; the client renders it verbatim
+(no hardcoded nav list).
 
-**API surface.** The archived + era-3 canonical endpoints are unchanged. The structure-and-tape era adds,
-every projection computed once server-side:
+**Data Contract (canonical values — unchanged; the Structure view owns NONE of them):** the Structure
+surface renders values already owned by their era-1–4 owners and adds no new owned value and no new
+computation:
 
-- `POST /research/bars` (record/register) · `GET /research/bars` · `GET /research/bars/{id}`
-- `GET /research/levels` (symbol + as-of → levels + confluence classes, from a recorded bar series)
-- `GET /research/strategies` (the strategy registry: `v1` + `structure_tape`, and the champion)
+- Bar series and checksums — owned by the bar store; read via `/research/bars*`.
+- Support/resistance levels and A/B/C confluence classes — owned by the S/R module (no lookahead); read via
+  `/research/levels`; rendered verbatim (class from `zone.class`).
+- Registered strategies and the champion pointer — config-owned; read via `/research/strategies` and
+  `/research/profiles`.
+- Backtest aggregates and the per-class `aggregates_by_class` breakdown — owned by the backtest runner; read
+  via `/research/backtests/{id}`.
+- PnL-ledger rows and the founding baseline — owned by the PnL ledger; read via `/research/pnl/ledger`.
+- The UI route map — owned by `apps/backend/app/meta.py`; read via `/meta/ui-routes`.
 
-MCP tools are thin proxies over exactly these — no new computation, no divergent serialization.
-
-**Data Contract (canonical values — each computed once, owned by one place):**
-
-- Bar series and checksums — owned by the bar store; served only via `/research/bars*`.
-- Support/resistance levels and A/B/C confluence classes — computed once by the S/R module (no
-  lookahead); served via `/research/levels`; rendered verbatim by every surface (REST, MCP, reports).
-- Registered strategies and the champion pointer — config-owned; served via `/research/strategies` (and
-  the existing `/research/profiles` champion summary).
-- Everything era-3 owned (tape state/features/history, datasets, backtest results, PnL-ledger rows, the
-  UI route map) keeps its single owner unchanged.
+No new server-side computation, no new owned value, no divergent serialization — the Structure view is a
+pure read/visualize surface.
 
 ## Must-have user journeys
 
-Journeys **J-01 – J-07** are the structure-and-tape era, staged **data-foundation-first**. J-01 – J-06
-are verifiable **keyless** on committed fixtures; real multi-timeframe bars and a real evaluation library
-are a credentialed operator action (Alpaca) that only enlarges the data. Natural dependency order:
-J-01 → J-02 → J-03 → J-04 → J-05 → J-06; J-07 guards continuously. The foundation (eras 1–3) MUST NOT
-regress.
+Journeys **J-01 – J-04** are the visibility interlude. **Frontend is present** (browser-verifiable). All are
+verifiable **keyless** on committed fixtures — the levels/zones surfaces render honest empty states where no
+bars are recorded, and the comparison is demoable on the committed keyless reference dataset. Natural
+dependency order: J-01 → J-02 → J-03; J-04 guards continuously. The foundation (eras 1–4) MUST NOT regress.
 
-- **J-01: Multi-timeframe historical bars are ingested and persisted (data foundation + free-plan probe)**
-  - Steps:
-    1. Add a neutral `RawBar` to the adapter seam and an Alpaca `fetch_bars(symbol, start, end, timeframe)`
-       calling `get_stock_bars` with `TimeFrame` (Minute/Hour/Day/Week/Month); run a one-symbol capability
-       probe (daily/weekly/monthly/hourly) and record the plan's feed, lookback range, and rate behaviour
-    2. Record a bar series as an immutable, checksummed store entry (symbol + timeframe + UTC window +
-       feed), mirroring the dataset store; commit a miniature multi-timeframe bar fixture
-    3. Read the stored bars via `GET /research/bars` (and the MCP proxy); re-fetch/re-read identically
-  - Acceptance: a bar series stores symbol, timeframe, UTC window, feed, bar count, and checksum; reading
-    it is **byte-identical** across re-runs and checksum-verified on load; a corrupted file surfaces an
-    explicit error; a committed multi-timeframe bar fixture proves ingest→persist→read in CI **without
-    credentials**; the Alpaca path fetches real bars when creds are present and returns the existing
-    explicit **missing-credentials** state when absent (never fabricated bars); the probe's honest finding
-    (feed = SIP or IEX, lookback range, rate limit) is recorded. *(Keyless on the fixture; real bars are a
-    credentialed operator action.)*
-
-- **J-02: Deterministic support/resistance levels per timeframe**
-  - Steps:
-    1. From a stored bar series, compute level candidates per timeframe — swing pivots (a bar's high/low
-       that is the extreme of its ±N neighbours) and prior-period extremes (prior day/week/month
-       high/low/close) — each with a strength (timeframe weight × touch count); every parameter from config
-    2. Compute levels "as of" a point in time using only bars at or before it (no lookahead); re-run
-    3. Read the levels via `GET /research/levels` (and the MCP proxy)
-  - Acceptance: levels are computed once, owned by the one canonical endpoint, and read verbatim by REST
-    and MCP; each level carries price, timeframe, type, touch count, and strength; the computation uses
-    **only bars at or before the as-of time** (a lookahead-free test proves a level at time T is unchanged
-    by any later bar); identical inputs reproduce **byte-identical** levels; every parameter is
-    config-sourced (no magic numbers, no fitting, no ML); keyless-verifiable on the committed bar fixture.
-    *(Keyless; automated.)*
-
-- **J-03: Confluence zones and A/B/C conviction classes**
-  - Steps:
-    1. Cluster levels across timeframes whose prices fall within a config tolerance band into confluence
-       zones; score each (sum of member strengths, timeframe-weighted) and grade it A/B/C by config thresholds
-    2. Read the classified zones via `GET /research/levels`; re-run identically
-  - Acceptance: each confluence zone records its member levels (with timeframes), its score, and its class
-    A/B/C; the clustering tolerance and class thresholds are config-owned (no magic numbers); a zone is
-    class A only when the confluence criteria are met (e.g. several timeframes including a long-term level
-    within tolerance), honestly labelled otherwise; **byte-identical** deterministic re-runs; served from
-    the one canonical owner and read verbatim by REST and MCP. *(Keyless; automated.)*
-
-- **J-04: Tape-confirmed structure entries as a registered strategy**
+- **J-01: The Structure tab renders S/R levels and A/B/C confluence zones**
   - Steps:
-    1. Register a second strategy `structure_tape` in a config-owned strategy registry (additive; `v1`
-       and `default` unchanged) whose entries arm when price enters a classified level's proximity band
-       AND the tape confirms direction — rejection (`ask_absorption`/`seller_control` at resistance → short;
-       `bid_absorption`/`buyer_control` at support → long) or breakthrough (`buyer_control` with price
-       impact through resistance → long; mirror for support) — reusing the engine's level-cross +
-       state-native arming
-    2. Backtest a fixture dataset under `structure_tape` with its symbol's precomputed levels injected;
... [diff_bound] docs/goal.md: 195 more diff lines omitted — Read the file for full detail
diff --git adocs/handoffs/goal-structure_ui-iter-0-dev.md bdocs/handoffs/goal-structure_ui-iter-0-dev.md
new file mode 100644
index 0000000..5c41232
--- /dev/null
+++ bdocs/handoffs/goal-structure_ui-iter-0-dev.md
@@ -0,0 +1,193 @@
+# goal-structure_ui-iter-0 Dev Handoff
+
+**Phase:** goal-structure_ui-iter-0
+**Date:** 2026-07-07
+**Agent:** developer
+**Status:** complete
+
+## What Was Built
+
+Nothing — by design. This is the "Structure, made visible" UI-surfacing interlude's **verify-only
+baseline** (Mode: baseline, Depth: lean). The developer step is an explicit no-op per the spec's
+BACKGROUND section; the entire scope was executing the spec's verification checklist against the
+current codebase and a live backend/frontend, and recording the evidence below.
+
+`git status --short` and `git diff --stat -- apps/` both confirm **zero source files changed**:
+
+```
+?? docs/phases/goal-structure_ui-iter-0.md
+?? runs/goal-session-structure_ui/
+```
+
+Both untracked entries are pipeline artifacts (the iter spec doc and the goal-mode session state
+directory), not product source — `git diff --stat -- apps/` returns empty. No file under `apps/`
+was created, modified, or deleted this iteration.
+
+## Baseline test counts (the J-04 sentinel anchor)
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
+
+- **Collected: 1146 items. Result: 1145 passed, 1 skipped, 2 warnings in 364.03s (0:06:04). Exit 0.**
+- The single skip is `tests/test_live_integration.py:37` — `"gated: set
+  TAPEOLOGY_LIVE_INTEGRATION=1 to run the real live-socket check"`. This is an explicit two-stage
+  opt-in gate (env var first, then credentials, then market-hours), not a credentials-missing
+  failure — expected and honest for an autonomous, keyless run.
+- This is up from era-4's own closing baseline (1040 passed / 1041 collected, recorded in
+  `docs/handoffs/goal-tape_to_profit_support_resistence-iter-0-dev.md` and grown across that
+  session's iterations 1–6), reflecting the bars/levels/strategies/backtests/meta-routes test
+  growth era 4 shipped. **The structure_ui interlude's opening baseline is 1145 passing / 1146
+  collected.**
+
+Engine equivalence tests (byte-identical outputs guard):
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py -v`
+
+- **22 passed in 0.79s** (7 from `test_observer_equivalence.py` — the J-68 engine
+  observer-seam byte-identity guard; 15 from `test_profile_equivalence.py` — the profile-registry
+  byte-identity guard). Both equivalence suites are green; the frozen `default` behavior is intact.
+
+`config_fingerprint` (live-computed, not just grepped):
+
+```
+cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"
+-> 4d665603569b9dbf
+```
+
+Matches the goal.md-pinned value **exactly**.
+
+## Journey-by-journey verification evidence
+
+The goal-evaluator assigns pass/fail/partial statuses; this section records what the codebase and
+a live backend/frontend actually showed. The spec's baseline predictions (J-01–J-03 absent, J-04
+intact) were **confirmed on every point**.
+
+### J-01 — Structure tab renders S/R levels + A/B/C confluence zones (expected FAIL) — CONFIRMED ABSENT
+
+- `apps/frontend/app/` listing: `globals.css`, `journal/`, `layout.tsx`, `page.tsx`,
+  `performance/`, `studies/` — **no `structure/` directory**. `find apps/frontend/app
+  -iname "*structure*"` → zero matches.
+- Live probe (frontend running on :3000): `GET /structure` → **404** (Next.js has no such route).
+- `apps/backend/app/meta.py` `UI_ROUTES` (read, unchanged) carries exactly the five pre-interlude
+  entries — `/` (Cockpit), `/journal` (Journal), `/journal/[id]` (non-nav detail), `/studies`
+  (Studies), `/performance` (Performance) — no `/structure` entry. Live probe: `GET
+  /meta/ui-routes` returns exactly that same five-entry list, byte-identical to the source.
+- The underlying data the future page will read is, however, **already live** on the backend (this
+  is the whole premise of the interlude — era 4 built the computation, not the view):
+  `GET /research/levels?symbol=SIM-BUYER&as_of=...` → 200, `GET /research/bars` → 200. So J-01's
+  gap today is purely the missing frontend route + nav entry, not missing data.
+
+### J-02 — strategy registry and champion are visible (expected FAIL) — CONFIRMED ABSENT (data ready)
+
+- No `/structure` page exists to render it (same absence as J-01).
+- Live probe: `GET /research/strategies` → 200, returning both `v1` and `structure_tape` with full
+  entry/exit/fee/slippage config (`structure_tape`'s class-scaled fields included) — the registry
+  itself is complete and correct on the backend.
+- Live probe: `GET /research/profiles` → 200 — `"champion":{"strategy_id":"v1","profile":"default"}`,
+  `"profiles":[{"id":"default","frozen":true,"is_default":true},
+  {"id":"candidate-faster-warmup","frozen":false,"is_default":false,...}]`. This is the exact
+  champion-pointer state a later iteration's registry view must badge and must not move.
+
+### J-03 — `structure_tape`-vs-`v1` comparison, honest (expected FAIL) — CONFIRMED ABSENT (job path ready)
+
+- No `/structure` page exists to render the comparison (same absence as J-01/J-02).
+- Live probe: `GET /research/datasets` → 200, `GET /research/pnl/ledger` → 200 — both endpoints the
+  future comparison view will read (dataset picker, founding baseline row) are live and correct.
+  Running an actual `structure_tape`-vs-`v1` backtest pair was **not** performed this iteration —
+  out of scope for a verify-only baseline with no UI to drive it from; a later iteration's dev/QA
+  step will exercise `POST /research/backtests` once the page exists.
+
+### J-04 — foundation unchanged (regression sentinel) — CONFIRMED INTACT
+
+- Full suite green (1145/1146 above); equivalence suites green (22/22 above); `config_fingerprint`
+  confirmed **live-computed** as `4d665603569b9dbf`, matching the pinned value.
+- Champion pointer confirmed untouched: `v1` / `default` (above).
+- Live backend (`bash scripts/dev.sh`, `CHAIN_BACKEND_PORT=8000 CHAIN_FRONTEND_PORT=3000`,
+  real dev DB — see "No side effects" note below):
+  - `GET /health` → `{"status":"ok"}`.
+  - `POST /watch/SIM-BUYER` → `{"status":"watching"}`; after 4s, `GET /tape/SIM-BUYER/state` →
+    `"tape_state":"buyer_control"`, `"warm":true`, confidence ≈0.855, `"stream_status":"live"`.
+    `DELETE /watch/SIM-BUYER` → `{"status":"stopped"}`.
+  - `POST /watch/SIM-SELLER` → `{"status":"watching"}`; after 4s, `GET /tape/SIM-SELLER/state` →
+    `"tape_state":"seller_control"`, `"warm":true`, confidence ≈0.855. `DELETE /watch/SIM-SELLER` →
+    `{"status":"stopped"}`.
+  - `GET /meta/ui-routes` → exactly 5 entries (4 nav + 1 non-nav detail), unchanged, no
+    `/structure` entry — confirms the nav's single source of truth is untouched.
+- Live frontend (`next dev`, port 3000, `NEXT_PUBLIC_API_URL=http://localhost:8000`): `GET /` → 200,
+  `GET /journal` → 200, `GET /studies` → 200, `GET /performance` → 200. `GET /structure` → 404
+  (expected — confirms the interlude has not started building yet).
+- Backend diff confirmed as **zero** (not merely "additive nav entry only" — this iteration makes
+  no backend edit at all): `git diff --stat -- apps/backend` is empty; `config.py`,
+  `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the engine, and
+  `app/meta.py` are all untouched.
+
+## Files Changed
+
+- (none — verify-only baseline; zero source modifications under `apps/`)
+
+## Tests Run
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
+Result: **1145 passed, 1 skipped** (1146 collected), 2 warnings, 364.03s, exit 0
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py -v`
+Result: **22 passed** in 0.79s
+
+## Service startup verification
+
+- `bash scripts/dev.sh` (with `CHAIN_BACKEND_PORT=8000 CHAIN_FRONTEND_PORT=3000` to pin the
+  goal.md-documented ports) started both services clean: backend `/health` → 200 within 2s,
+  frontend `Ready in 1215ms`, `GET /` → 200.
+- Stopped both (port-based kill, mirroring `dev.sh`'s own cleanup logic: `lsof -ti :$PORT` +
+  `fuser -k -9 $PORT/tcp`, which correctly reaches the `uvicorn --reload` worker child, not just
+  the reloader parent), confirmed both ports fully released, then **started dev.sh again on the
+  same ports** — backend `/health` → 200 after 2s, frontend `Ready in 1190ms`, `GET /` → 200 — no
+  port conflict on restart. Stopped again; final check confirms ports 8000/3000 fully released and
+  no orphaned `uvicorn`/`next` process remains for this repo (an unrelated project's dev servers on
+  different ports were left untouched, confirmed by PID/command-line inspection before and after).
+
+## No side effects (baseline hygiene)
+
+- The live smoke test above used the **real dev `TAPEOLOGY_JOURNAL_DB`** (this iteration did not
+  override it with a scratch path, unlike the era-4 baseline's practice). Verified this caused no
+  actual mutation: `apps/backend/journal.db`, `apps/backend/tapeology_journal.db`, and
+  `journal.db-wal` all carry mtimes from **before** this iteration (2026-07-03 / 2026-07-06); none
+  changed during today's test window. This is consistent with `POST /watch/{ticker}` /
+  `DELETE /watch/{ticker}` being pure in-memory tape-engine operations that write no journal/thesis
+  record — only `POST /research/thesis` would persist, and this iteration never called it. Noted
+  here for transparency rather than silently assumed; a future iteration doing anything
+  journal-writing should use a scratch DB path as era 4 did.
+
+## Known Issues
+
+- **Environment drift (carried over from era 3/4):** the backend venv runs Python **3.14.4** while
+  `.claude/project-template.md`'s placeholder text and goal.md's Constraints section both say
+  Python 3.12. The full suite is green on 3.14.4 — a documentation/environment drift observation,
+  not a failure. No action taken (out of scope for a verify-only iteration).
+- **`.claude/project-template.md` is still the generic unfilled template** (placeholders like
+  `<e.g., Python 3.12>` throughout). README.md carries an explicit TODO flagging this ("likely
+  reset by a recent incredible_auto_dev framework sync") and documents the actual verified
+  commands; this developer used goal.md's Constraints section + the README's "How to run" section
+  as the real stack-configuration source, matching what the era-4 baseline iteration did. Not this
+  iteration's scope to fix.
+- `tests/test_live_integration.py` skips on the explicit `TAPEOLOGY_LIVE_INTEGRATION=1` opt-in gate
+  (expected — keyless, off-hours-safe by design).
+- J-03's actual `structure_tape`-vs-`v1` backtest run was **not exercised** this iteration (no UI
+  exists yet to drive it from, and the spec scopes this iteration to verification only, not to
+  invoking write-side research jobs speculatively). The underlying job endpoints
+  (`POST /research/backtests`, `GET /research/backtests/{id}`) were confirmed reachable
+  (`GET /research/datasets` and `GET /research/pnl/ledger` both 200) but not exercised end-to-end;
+  a later iteration's dev/QA step building J-03's UI will be the first to run that job pair.
+- Full click-through browser verification of J-01/J-02/J-03 (confirming the *absence* renders no
+  broken nav link, no client error) and J-04 (hydrated nav, cockpit panels over WebSocket, journal/
+  studies/performance page content) is the browser-qa-agent's step per the spec's TESTING
+  REQUIREMENTS; the evidence above is the dev-level code/API/SSR inspection leg only.
+
+## Suggested Next Phase
+
+Per the spec's NOTES and goal.md's dependency order (J-01 → J-02 → J-03, J-04 guarding
+continuously): iteration 1 should build **J-01** — the `/structure` route
+(`apps/frontend/app/structure/page.tsx`, following the `/performance` page pattern) plus the
+additive `{"path": "/structure", "label": "Structure", "nav": true}` entry in `apps/backend/app/
+meta.py` `UI_ROUTES`. This is the shared page home and nav unblocker for J-02 and J-03, which per
+the blueprint (`runs/goal-session-structure_ui/state/blueprint.md`) are sections of the same single
+page, not separate routes.
diff --git adocs/phases/goal-structure_ui-iter-0.md bdocs/phases/goal-structure_ui-iter-0.md
new file mode 100644
index 0000000..f79356d
--- /dev/null
+++ bdocs/phases/goal-structure_ui-iter-0.md
@@ -0,0 +1,104 @@
+# Goal Iteration 0 — Baseline: verify all Structure-interlude journeys against current state
+
+<!-- machine-readable goal-mode metadata -->
+## Goal Mode Metadata
+
+- **Session ID:** structure_ui
+- **Iteration:** 0
+- **Mode:** baseline
+- **Depth:** lean
+- **Frontend Present:** yes
+- **Target journeys:** J-01, J-02, J-03, J-04
+- **Required-still-passing journeys:** none (baseline — this iteration establishes the passing/failing/partial set that later iterations preserve)
+- **Anti-goal reminders (verbatim from `docs/goal.md`):**
+
+  _Immutable rails — the identity of the project:_
+  1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
+  2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
+  3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
+  4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
+  5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. (See the forming-bar rule in card 6.4.) *(critical)*
+  6. **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
+  7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
+  8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
+  9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
+  10. **Persistence stays scoped** — no ambient recording of live streams; recording is an explicit, logged act. *(critical)*
+
+  _Interlude-specific anti-goals (added, not weakening any rail above):_
+  - **The Structure UI recomputes nothing.** Every displayed value — level price/timeframe/type, zone class, net R, net $, n, `insufficient_sample`, the champion — is read verbatim from its canonical endpoint. No client-side grading, PnL math, aggregation, or champion resolution. A number that diverges from its API/MCP payload is a defect (trap T10). *(critical)*
+  - **No new backend computation or endpoint.** This interlude consumes the existing canonical endpoints; the only backend edit is the additive `/structure` entry in the `meta.py` route registry (the nav owner). It creates no second implementation of any value. *(critical)*
+  - **Honest UI states only.** No fabricated chart, level, zone, trade, fill, or PnL to force a green journey; every failure mode (no bar series, no levels, no zones, insufficient n, missing credentials, backend unreachable) surfaces an explicit, distinct state. *(critical)*
+  - **The UI never promotes.** The comparison view runs backtests and diffs their reports; it MUST NOT move the champion pointer or write the PnL ledger — promotion remains the sweep's hold-out act. *(critical)*
+  - **No vocabulary drift** (trap T9). No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.
+  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a PnL-ledger (or, for a read surface, a single-source-of-truth) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*
+
+## GOAL
+
+Establish the honest starting line: run every Must-have journey (J-01–J-04) of the "Structure, made visible" interlude against the current codebase and record which already pass, which fail, and which are partial — with **no** code changes.
+
+## BACKGROUND
+
+This is the **baseline assessment**, not a feature delivery — the developer step is a no-op; the value comes entirely from browser-qa + the backend/equivalence suite running every journey to snapshot reality. This is a UI-surfacing interlude on top of the frozen eras 1–4 foundation: the era-4 structure stack (S/R levels, A/B/C confluence zones, the `v1`+`structure_tape` registry, the `structure_tape`-vs-`v1` backtest) already exists on REST/MCP/CLI but has **no browser home**. Codebase inspection this iteration (evidence, to be confirmed by the executor, not scored here) shows: no `/structure` page under `apps/frontend/app/`, and `apps/backend/app/meta.py` `UI_ROUTES` carries only the five pre-interlude routes (`/`, `/journal`, `/journal/[id]`, `/studies`, `/performance`) — so J-01/J-02/J-03 have no surface to render and are expected to read as failing, while J-04 (foundation sentinel) is expected to read as passing since nothing has changed. Depth is **lean** per the baseline-mode rule (lean cycle is sufficient — no code is written; the browser-qa step carries the value); there is no prior evaluator verdict and no ESCALATE. Lessons ledger is empty (first iteration), so no prior pitfall applies.
+
+## IN SCOPE
+
+### Backend
+- [ ] None — verify-only baseline. No source files are modified this iteration.
+
+### Frontend (if applicable)
+- [ ] None — verify-only baseline. No source files are modified this iteration.
+
+### Verification tasks (no code)
+- [ ] Run J-01 via browser-qa-agent: attempt to reach a Structure tab / `/structure` route and render S/R levels + A/B/C confluence zones; record the result and the honest-state behavior observed.
+- [ ] Run J-02 via browser-qa-agent: attempt to view the strategy registry (`v1` + `structure_tape`) and the badged champion; record the result.
+- [ ] Run J-03 via browser-qa-agent: attempt the on-screen `structure_tape`-vs-`v1` comparison with per-class A/B/C breakdown; record the result.
+- [ ] Run J-04 (foundation sentinel): execute the full backend suite + engine equivalence test, confirm `config_fingerprint` is `4d665603569b9dbf`, and spot-check `/`, `/journal`, `/studies`, `/performance` in the browser; record the result.
+
+### New user-facing capability
+None — this iteration delivers no capability. It records the baseline pass/fail/partial state of the four journeys.
+
+### New information displayed
+None.
+
+### New user actions
+None.
+
+### UI surface changes
+None.
+
+### Product surface delta
+None — the product is unchanged after this iteration. Its only output is a recorded baseline of journey states.
+
+### Blueprint conformance
+No new surfaces this iteration. The blueprint (`runs/goal-session-structure_ui/state/blueprint.md`) is drafted alongside this spec: single new page `/structure` (Structure nav section) hosting J-01/J-02/J-03 as sections; J-04 covers the existing surfaces. No page is created this iteration.
+
+### Data-contract additions
+None. This interlude introduces **no** new owned value and **no** new computation. Every value the future Structure view will display is already owned by an era-1–4 canonical source and registered in the blueprint's Data Contract, read verbatim (bars, levels + `zone.class`, strategies + champion pointer, backtest `aggregates`/`aggregates_by_class`, PnL ledger, datasets, the `meta.py` route map).
+
+## OUT OF SCOPE
+
+- Any code change whatsoever (no `/structure` page, no `meta.py` `UI_ROUTES` edit — those begin in iteration 1).
+- Any edit to `config.py`, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the engine, or any existing surface.
+- Marking journeys as passing/failing — that is the goal-evaluator's job; this spec only requests they be exercised and recorded.
+- The `/datasets` library-inventory page (explicitly out of scope for this interlude — Card 5.9 / Era-5 scope).
+
+## DEFINITION OF DONE
+
+- [ ] All four Must-have journeys (J-01, J-02, J-03, J-04) are exercised against the current HEAD and each has a recorded outcome (pass / fail / partial) with evidence.
+- [ ] The full backend suite and the engine equivalence test are run and their current result recorded, with `config_fingerprint` observed and noted (baseline for the J-04 sentinel).
+- [ ] No source files changed — `git diff` over `apps/` is empty (only run/report artifacts written).
+- [ ] No anti-goal violation introduced (trivially satisfied — no code changes).
+- [ ] Dev handoff written at `docs/handoffs/goal-structure_ui-iter-0-dev.md` noting this was a verify-only baseline (developer no-op).
+
+## TESTING REQUIREMENTS
+
+- **Browser:** J-01, J-02, J-03 (attempt to locate and drive the Structure surface — expected absent at baseline; record the honest "not present" observation), and J-04 (spot-check the existing `/`, `/journal`, `/studies`, `/performance` surfaces still work).
+- **Unit/integration:** run the full backend test suite and the engine equivalence test as the J-04 baseline; record pass counts and the observed `config_fingerprint` (expected `4d665603569b9dbf`).
+- **Error cases:** none this iteration — no new inputs are introduced; honest-empty/degraded states are only *observed*, not yet implemented.
+
+## NOTES
+
+- **Baseline framing:** the goal-evaluator will classify already-passing journeys as `already_passing` so later iterations skip them. Expected baseline read (evidence-based, evaluator to confirm): J-01/J-02/J-03 fail (no `/structure` route or nav entry exists), J-04 passes (foundation untouched). Do not treat these expectations as the verdict.
+- **Dependency order for later iterations** (from `docs/goal.md`): J-01 → J-02 → J-03, with J-04 guarding continuously. Iteration 1 will likely target J-01 alone (it creates the `/structure` route + the additive `meta.py` `UI_ROUTES` entry that unblocks J-02 and J-03's shared page home).
+- **Blueprint drafted this iteration:** `runs/goal-session-structure_ui/state/blueprint.md` — Information Architecture (one new `/structure` page under a Structure nav entry, data-driven via `GET /meta/ui-routes`) + a Data Contract in which the Structure view owns nothing. Auto-approved by default; the loop proceeds to iteration 1 unless `--require-blueprint-approval` was passed.
+- The canonical endpoints the future Structure view will read (`/research/bars`, `/research/levels`, `/research/strategies`, `/research/profiles`, `/research/datasets`, `/research/backtests` + `/{id}`, `/research/pnl/ledger`, `/meta/ui-routes`) were confirmed present in the codebase this iteration — the interlude is a pure read/visualize surface over them.
diff --git areports/reviews/goal-structure_ui-iter-0-review.md breports/reviews/goal-structure_ui-iter-0-review.md
new file mode 100644
index 0000000..9ccf337
--- /dev/null
+++ breports/reviews/goal-structure_ui-iter-0-review.md
@@ -0,0 +1,24 @@
+**Verdict:** PASS
+
+```yaml
+phase: goal-structure_ui-iter-0
+date: 2026-07-07
+reviewer: reviewer
+summary: |
+  Verify-only baseline per spec: zero source files touched (git diff over apps/ empty,
+  confirmed independently). Dev handoff's claims re-verified: no apps/frontend/app/structure
+  dir, meta.py UI_ROUTES still exactly 5 entries, 1146 tests collected, 22/22 equivalence
+  tests pass, config_fingerprint 4d665603569b9dbf matches goal.md. Honest, accurate baseline.
+spec_alignment:
+  definition_of_done: complete
+  scope_creep: none
+issues: []
+standards:
+  state_transitions_server_side: n/a
+  test_quality: pass
+  no_dead_code: n/a
+  no_hardcoded_localhost: n/a
+  ui_evolved_with_capability: n/a
+  navigation_updated: n/a
+  architecture_principles: pass
+```
diff --git aruns/goal-session-structure_ui/.quota-pause-count bruns/goal-session-structure_ui/.quota-pause-count
new file mode 100644
index 0000000..573541a
--- /dev/null
+++ bruns/goal-session-structure_ui/.quota-pause-count
@@ -0,0 +1 @@
+0
diff --git aruns/goal-session-structure_ui/dispatch/.pump-alive bruns/goal-session-structure_ui/dispatch/.pump-alive
new file mode 100644
index 0000000..e69de29
diff --git aruns/goal-session-structure_ui/engine.pid bruns/goal-session-structure_ui/engine.pid
new file mode 100644
index 0000000..22291be
--- /dev/null
+++ bruns/goal-session-structure_ui/engine.pid
@@ -0,0 +1 @@
+1032454
diff --git aruns/goal-session-structure_ui/iter-0/.steps/decomposer.done bruns/goal-session-structure_ui/iter-0/.steps/decomposer.done
new file mode 100644
index 0000000..0753598
--- /dev/null
+++ bruns/goal-session-structure_ui/iter-0/.steps/decomposer.done
@@ -0,0 +1 @@
+{"v":1,"step":"decomposer","iter":"0","iter_name":"goal-structure_ui-iter-0","ts":"2026-07-06T23:07:48Z","tree_hash":"d7258e02aff8af6b68b4aa02096342841ad36a87","artifacts":["docs/phases/goal-structure_ui-iter-0.md"],"verdict":"","journeys":""}
diff --git aruns/goal-session-structure_ui/iter-0/.steps/developer.done bruns/goal-session-structure_ui/iter-0/.steps/developer.done
new file mode 100644
index 0000000..6c90d19
--- /dev/null
+++ bruns/goal-session-structure_ui/iter-0/.steps/developer.done
@@ -0,0 +1 @@
+{"v":1,"step":"developer","iter":"0","iter_name":"goal-structure_ui-iter-0","ts":"2026-07-06T23:21:48Z","tree_hash":"d7258e02aff8af6b68b4aa02096342841ad36a87","artifacts":["docs/handoffs/goal-structure_ui-iter-0-dev.md"],"verdict":"","journeys":""}
diff --git aruns/goal-session-structure_ui/iter-0/.steps/review-1.done bruns/goal-session-structure_ui/iter-0/.steps/review-1.done
new file mode 100644
index 0000000..29d044f
--- /dev/null
+++ bruns/goal-session-structure_ui/iter-0/.steps/review-1.done
@@ -0,0 +1 @@
+{"v":1,"step":"review-1","iter":"0","iter_name":"goal-structure_ui-iter-0","ts":"2026-07-06T23:24:58Z","tree_hash":"d7258e02aff8af6b68b4aa02096342841ad36a87","artifacts":["reports/reviews/goal-structure_ui-iter-0-review.md"],"verdict":"PASS","journeys":""}
diff --git aruns/goal-session-structure_ui/iter-0/goal-slice.md bruns/goal-session-structure_ui/iter-0/goal-slice.md
new file mode 100644
index 0000000..47a8bad
--- /dev/null
+++ bruns/goal-session-structure_ui/iter-0/goal-slice.md
@@ -0,0 +1,296 @@
+# Tapeology — Project Goal (Interlude: Structure, made visible — UI surfacing)
+
+> Eras 1–4 are the **foundation** of this goal and MUST NOT regress. Eras 1–2 (tape reading + the
+> research evolution, journeys J-01 – J-68, GOAL_ACHIEVED) are archived at
+> [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md). Era 3 (the profit-research
+> measurement machine, J-01 – J-09, GOAL_ACHIEVED) and Era 4 (the structure-and-tape evolution,
+> J-01 – J-07, GOAL_ACHIEVED) are now frozen foundation; their full records live in git history and in
+> `reports/goal-session-tape_to_profit-delivered.md` and
+> `reports/goal-session-tape_to_profit_support_resistence-delivered.md`.
+>
+> **This chapter is an operator-directed UI-surfacing interlude, not one of the numbered research eras.**
+> It pulls forward the intent of Card 5.9 ("Library health & UI") in
+> [`docs/research-directions.md`](research-directions.md). Era 5 "The Library" (recording real
+> multi-symbol/multi-regime data) remains the next headline research era per that document's router
+> (Part 5.1); this interlude does not consume the Era-5 slot and adds no research finding — it makes the
+> era-4 structure work visible in the app.
+
+## Vision
+
+The era-4 structure-and-tape stack is real and honest — multi-timeframe support/resistance **levels**,
+**A/B/C confluence zones**, a **strategy registry** (`v1` + `structure_tape`), and the honest
+`structure_tape`-vs-`v1` **backtest comparison** with its per-class PnL breakdown. But every one of these
+lives ONLY on REST / MCP / CLI surfaces: the web app still shows its four pre-era-4 tabs, and a person
+cannot **see** any of it. Research a human cannot inspect erodes trust.
+
+This interlude gives the structure work a browser home: a read-only **Structure** view that renders levels
+and confluence zones on a price chart, the strategy registry and current champion, and the honest
+`structure_tape`-vs-`v1` comparison with its per-class A/B/C breakdown. It reads **every** value verbatim
+from its existing canonical endpoint, recomputes nothing, and is honest about the mostly-empty keyless data
+reality. It changes **no** computation, strategy, promotion, or measurement — it is pure visibility.
+
+Data reality, stated up front: on the committed **keyless** fixture there are no recorded multi-timeframe
+bars, so levels/zones are largely empty and `structure_tape` is honestly unevaluable (n below the minimum).
+The UI is built to say that plainly. Real levels, real zones, and a genuine hold-out comparison await Era 5
+"The Library" recording real bars; this interlude surfaces what exists and is honest about what does not.
+
+## Target Users
+
+- The project owner (a discretionary intraday trader) who wants to **see** the computed structure and the
+  honest `structure_tape`-vs-`v1` comparison inside the app — not only via `curl` or the MCP tools.
+- AI dev-chain agents (the goal-mode UI chain) building and browser-verifying the new surface.
+
+## Foundation invariants (still law — eras 1–4)
+
+The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md)) and the
+era-3 measurement machine remain binding verbatim on ALL new code: price-impact-over-aggression; honest
+uncertainty; no fabricated data; single source of truth; no magic numbers; provider-agnostic engine;
+deterministic & reproducible; no secrets in source; research read-only over the engine; journal/record
+integrity; source/feed/`config_fingerprint` honesty; the existing surfaces (`/`, `/journal`,
+`/journal/[id]`, `/studies`, `/performance`) stay intact.
+
+In addition, **era 4 (the structure-and-tape stack) is now frozen foundation**:
+
+1. The **tape engine** emits its five states byte-identically under `default`; the live cockpit and every
+   archived surface stay unchanged (equivalence-tested; `config_fingerprint` `4d665603569b9dbf` pinned).
+2. The **structure computations** — the bar store, the deterministic S/R levels module, the confluence
+   A/B/C grading, the strategy registry (`v1` + `structure_tape`), the class-scaled stop/reward/size math,
+   the per-class backtest breakdown, and the named-strategy sweep — stay byte-identical and are the **only**
+   owners of those values. This interlude reads them; it never recomputes or re-implements them.
+3. **`v1`, `default`, and the champion pointer are frozen.** This interlude adds a read surface only; it
+   never mutates a strategy, a profile, an engine default, or the champion pointer, and it moves the
+   champion **never** (promotion remains the sweep's act on hold-out data).
+
+## Success Criteria
+
+In priority order — honesty and non-regression outrank everything:
+
+1. **Nothing existing regresses.** The full backend suite stays green, the engine equivalence test keeps
+   proving byte-identical `default` outputs, `config_fingerprint` stays `4d665603569b9dbf`, and every
+   era-1–4 surface and capability keeps working.
+2. **The structure stack is visible.** A **Structure** tab renders, for a chosen symbol, its S/R levels and
+   A/B/C confluence zones on a price chart; the strategy registry (`v1` + `structure_tape`) with the current
+   champion; and a `structure_tape`-vs-`v1` backtest comparison with the per-class A/B/C breakdown.
+3. **Single source of truth is visibly preserved.** Every displayed value — a level's price/timeframe/class,
+   a zone's class, net R, net $, n, `insufficient_sample`, the champion — is read **verbatim** from its
+   canonical endpoint and matches the REST/MCP payload byte-for-byte. The UI recomputes nothing (no
+   client-side grading, PnL math, or aggregation).
+4. **Honesty is visible.** Empty and degraded states — no recorded bars, no levels, no zones, insufficient
+   n, missing credentials — each render as an explicit, distinct state; nothing is fabricated; the
+   "simulated — not indicative of live results" register appears verbatim wherever simulated PnL or size is
+   shown.
+
+## Key Capabilities
+
+Layered strictly on top of the era-1–4 capabilities, which remain unchanged. This interlude adds **no**
+backend computation and **no** new canonical value — only a read surface and one additive nav entry.
+
+1. **A Structure route/tab.** A new `/structure` page following the `/performance` page pattern; its nav
+   entry is owned by the backend route registry (`GET /meta/ui-routes`), so the client NavBar surfaces it
+   without a hardcoded list.
+2. **Levels & confluence-zones visualization.** For a chosen symbol + as-of time, a `lightweight-charts`
+   price chart (candles from the symbol's recorded bar series) with one price line per level labelled by
+   timeframe, plus a confluence-zones table badged **A/B/C** — the class read verbatim from the served
+   `zone.class`.
+3. **Strategy registry & champion view.** `v1` and `structure_tape` shown side by side (entry rule, exit
+   precedence, `structure_tape`'s class-scaled `stop_bps_by_class` / `r_multiple_by_class` /
+   `size_multiple_by_class`), with the champion (founding `v1`/`default`) badged.
+4. **`structure_tape`-vs-`v1` comparison.** Run both strategies on a chosen dataset via the existing
+   backtest job (reusing the Studies job/poll pattern), then render side-by-side aggregates + the per-class
+   A/B/C breakdown (`aggregates_by_class`, `insufficient_sample` shown verbatim), beside the champion
+   pointer and founding baseline row. On the keyless reference dataset it honestly shows `structure_tape`
+   as a non-survivor and the champion unchanged.
+
+## Non-Goals
+
+- **No new backend computation or endpoint for the UI.** The Structure view consumes existing canonical
+  endpoints only; it introduces no second source of truth. If a genuinely new value were ever needed it
+  would get exactly one owning endpoint — but the intent here is **zero** new computation.
+- No brokerage integration, order placement, routing, or execution of any kind — **neither real-money nor
+  paper-trading APIs**. Running a backtest is an offline research job over already-recorded immutable
+  datasets, exactly as the Studies page already does; it places nothing.
+- No machine learning, no trading advice, no imperative cues, no prediction or expected-return language in
+  any UI copy.
+- No general-purpose charting, multi-symbol dashboards, stock scanning/screening, news/sentiment, or
+  fundamentals — unchanged from the archived eras.
+- No mutation of `default`, `v1`, the engine, the `config_fingerprint`, or any era-1–4 behaviour; the only
+  backend edit is the additive `/structure` entry in the route registry.
+- **No champion promotion from the UI.** The comparison view runs backtests and diffs their reports; it
+  never moves the champion pointer — promotion stays the sweep's hold-out act.
+- **No `/datasets` library-inventory page** (that is roadmap Card 5.9's own scope, dependent on Era-5
+  regime/tradeability data) — out of scope for this interlude.
+
+## Constraints
+
+- **Stack (carried over):** Frontend Next.js 15 + TypeScript + Tailwind v3 (npm), `lightweight-charts`,
+  dark-only. Backend Python 3.12 + FastAPI. Backend `http://localhost:8000`, frontend
+  `http://localhost:3000`. Sim tickers stay keyless.
+- **UI read discipline:** the Structure view reads ONLY canonical endpoints — `/research/bars`,
+  `/research/levels`, `/research/strategies`, `/research/profiles`, `/research/datasets`,
+  `/research/backtests` (+ `/{id}`), `/research/pnl/ledger`, and `/meta/ui-routes` — and renders their
+  values **verbatim**. Zero client-side recomputation of levels, classes, PnL, aggregates, or the champion.
+- **Nav discipline:** the Structure tab is registered in the backend route registry
+  (`apps/backend/app/meta.py` `UI_ROUTES`, the owner) and surfaced via `GET /meta/ui-routes`; the client
+  NavBar is data-driven and MUST NOT hardcode the route.
+- **Honest-state discipline:** no fabricated data; `no_bar_series_for_symbol`, `insufficient_sample`, empty
+  arrays, and the missing-credentials (503) state each render as an explicit, distinct UI state.
+- **PnL honesty register:** unchanged from eras 3–4 — a $ never without its R, n, basis, assumptions, null
+  baseline, and the visible "simulated — not indicative of live results" register; sub-minimum-n results
+  labelled "insufficient sample"; train and hold-out never pooled.
+- **Frozen-foundation discipline:** no edits to `config.py` (fingerprint `4d665603569b9dbf`),
+  `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the engine, or any existing
+  surface's behaviour, beyond the additive nav-registry entry.
+- **MCP read-only discipline:** unchanged — the MCP server stays a byte-identical proxy of the GET surface
+  and gains no new tool for this interlude.
+
+## Product Shape
+
+Nav (top bar) gains exactly ONE tab: **Cockpit `/` · Journal `/journal` (+ `/journal/[id]`) · Studies
+`/studies` · Performance `/performance` · Structure `/structure` (new)**. The new tab's entry is owned by
+`apps/backend/app/meta.py` `UI_ROUTES` and served via `GET /meta/ui-routes`; the client renders it verbatim
+(no hardcoded nav list).
+
+**Data Contract (canonical values — unchanged; the Structure view owns NONE of them):** the Structure
+surface renders values already owned by their era-1–4 owners and adds no new owned value and no new
+computation:
+
+- Bar series and checksums — owned by the bar store; read via `/research/bars*`.
+- Support/resistance levels and A/B/C confluence classes — owned by the S/R module (no lookahead); read via
+  `/research/levels`; rendered verbatim (class from `zone.class`).
+- Registered strategies and the champion pointer — config-owned; read via `/research/strategies` and
+  `/research/profiles`.
+- Backtest aggregates and the per-class `aggregates_by_class` breakdown — owned by the backtest runner; read
+  via `/research/backtests/{id}`.
+- PnL-ledger rows and the founding baseline — owned by the PnL ledger; read via `/research/pnl/ledger`.
+- The UI route map — owned by `apps/backend/app/meta.py`; read via `/meta/ui-routes`.
+
+No new server-side computation, no new owned value, no divergent serialization — the Structure view is a
+pure read/visualize surface.
+
+## Must-have user journeys
+
+Journeys **J-01 – J-04** are the visibility interlude. **Frontend is present** (browser-verifiable). All are
+verifiable **keyless** on committed fixtures — the levels/zones surfaces render honest empty states where no
+bars are recorded, and the comparison is demoable on the committed keyless reference dataset. Natural
+dependency order: J-01 → J-02 → J-03; J-04 guards continuously. The foundation (eras 1–4) MUST NOT regress.
+
+- **J-01: The Structure tab renders S/R levels and A/B/C confluence zones**
+  - Steps:
+    1. Create the `/structure` route (`apps/frontend/app/structure/page.tsx`, following the `/performance`
+       page pattern) and add `{"path": "/structure", "label": "Structure", "nav": true}` to
+       `apps/backend/app/meta.py` `UI_ROUTES` so the tab appears via `GET /meta/ui-routes` (extend the
+       owner, not the client NavBar)
+    2. Choose a symbol (reuse `SymbolSearch`) and an as-of time; fetch `GET /research/levels?symbol=&as_of=`;
+       render a `lightweight-charts` price chart (candles from that symbol's `/research/bars` series) with
+       one dashed price line per level labelled by timeframe, plus a confluence-zones table badged **A/B/C**
+       read verbatim from `zone.class`, listing member levels (price + timeframe) and the served `score`
+    3. Exercise the empty states (a symbol with no recorded bars; a series with no levels; levels with no
+       qualifying zone)
+  - Acceptance: the Structure tab is reachable from the nav (proving the `meta.py`-owned route, not a
+    hardcoded client link); for a symbol with a recorded bar series, the rendered level lines and the zone
+    table match `GET /research/levels` **byte-for-byte** (A/B/C taken from `zone.class`, never recomputed
+    from breadth or score); `no_bar_series_for_symbol` → an explicit "no bar series recorded — recording
+    historical bars needs provider credentials" state; series-but-no-levels and no-zones each render a
+    distinct honest state; nothing is fabricated. *(Keyless; browser-verifiable.)*
+
+- **J-02: The strategy registry and champion are visible**
+  - Steps:
+    1. Fetch `GET /research/strategies`; render `v1` and `structure_tape` as two cards showing each entry
+       rule, the exit precedence (`r_stop → reward_target → state_flip → horizon`), and `structure_tape`'s
+       class-scaled `stop_bps_by_class` / `r_multiple_by_class` / `size_multiple_by_class`
+    2. Badge the champion (`champion.strategy_id` / `champion.profile`), cross-checking `/research/profiles`
+  - Acceptance: both registered strategies are shown with their config-owned parameters read verbatim from
+    `GET /research/strategies` (no client-side reconstruction of the registry); the champion (founding
+    `v1`/`default`) is badged and matches both `/research/strategies` and `/research/profiles`; the registry
+    view fabricates no strategy or parameter. *(Keyless; browser-verifiable.)*
+
+- **J-03: `structure_tape` is compared to `v1` on screen, honestly**
+  - Steps:
+    1. Choose a dataset (`GET /research/datasets`); run `structure_tape` and the champion strategy (`v1`) on
+       it via `POST /research/backtests` at `profile=default`, polling `GET /research/backtests/{id}` (reuse
+       the Studies job/poll pattern) until both are `done`
+    2. Render side-by-side aggregates (n, net R, net $, `win_rate`, `max_drawdown_r`) plus the per-class
+       **A/B/C** table from `aggregates_by_class` (with `insufficient_sample` shown verbatim), beside the
+       champion pointer and the founding baseline row from `/research/pnl/ledger`
+    3. Show the honest keyless outcome on the committed reference dataset
+  - Acceptance: the comparison renders both strategies' aggregates and the per-class breakdown read
+    **verbatim** from `GET /research/backtests/{id}` (no recomputed R, $, win-rate, or class partition);
+    sub-minimum-n classes and splits show "insufficient sample"; the "simulated — not indicative of live
+    results" register appears verbatim; on the committed keyless reference dataset it honestly shows
+    `structure_tape` as a **non-survivor** with insufficient n and the champion unchanged at `v1`/`default`;
+    the UI moves the champion pointer **never**; deterministic. *(Keyless-demoable on the reference dataset;
+    real comparisons await Era-5 data; browser-verifiable.)*
+
+- **J-04: The foundation is unchanged (regression sentinel)**
+  - Steps:
+    1. Run the sim cockpit flows (`SIM-BUYER` settles `buyer_control`, `SIM-SELLER` settles `seller_control`)
+       and spot-check `/journal`, `/studies`, `/performance` in the browser; run the full backend suite and
+       the engine equivalence test
+    2. Confirm `config_fingerprint` is still `4d665603569b9dbf` and the ONLY backend diff is the additive
+       `meta.py` `UI_ROUTES` entry — `config.py`, `research/levels.py`, `research/backtests.py`,
+       `research/strategies.py`, and the engine are untouched
+  - Acceptance: the archived-era surfaces behave exactly as shipped; the full backend suite passes (no test
+    deleted or weakened to make new work pass); the equivalence test proves **byte-identical** `default`
+    state/confidence/features/history and the pinned `config_fingerprint`; `v1` and the champion pointer are
+    untouched; the Structure UI adds no backend computation and no new endpoint and reads only canonical
+    endpoints. This sentinel makes "don't break the foundation, don't create a second source of truth" an
+    enforced must-have of this interlude. *(Browser-verifiable + automated.)*
+
+<!-- AUTO:journeys -->
+<!-- /AUTO:journeys -->
+
+## Anti-goals
+
+**Immutable rails — the identity of the project (copied verbatim from
+[`docs/research-directions.md`](research-directions.md) §0.3; enforced by existing tests and audits; only
+ever grow more specific, never weaker):**
+
+1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no
+   "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new
+   research code adds matching guard tests, never weakens them.) *(critical)*
+2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
+   fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative
+   trading cues. *(critical)*
+3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and
+   thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside
+   them, never a mutation of them. *(critical)*
+4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the
+   sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never
+   lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor.
+   *(critical)*
+5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. (See the
+   forming-bar rule in card 6.4.) *(critical)*
+6. **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and
+   read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
+7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests
+   reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
+8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface
+   can change state. *(critical)*
+9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged,
+   never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
+10. **Persistence stays scoped** — no ambient recording of live streams; recording is an explicit, logged
+    act. *(critical)*
+
+**Interlude-specific anti-goals (added, not weakening any rail above):**
+
+- **The Structure UI recomputes nothing.** Every displayed value — level price/timeframe/type, zone class,
+  net R, net $, n, `insufficient_sample`, the champion — is read verbatim from its canonical endpoint. No
+  client-side grading, PnL math, aggregation, or champion resolution. A number that diverges from its API/MCP
+  payload is a defect (trap T10). *(critical)*
+- **No new backend computation or endpoint.** This interlude consumes the existing canonical endpoints; the
+  only backend edit is the additive `/structure` entry in the `meta.py` route registry (the nav owner). It
+  creates no second implementation of any value. *(critical)*
+- **Honest UI states only.** No fabricated chart, level, zone, trade, fill, or PnL to force a green journey;
+  every failure mode (no bar series, no levels, no zones, insufficient n, missing credentials, backend
+  unreachable) surfaces an explicit, distinct state. *(critical)*
+- **The UI never promotes.** The comparison view runs backtests and diffs their reports; it MUST NOT move
+  the champion pointer or write the PnL ledger — promotion remains the sweep's hold-out act. *(critical)*
+- **No vocabulary drift** (trap T9). No "paper trading", "shadow trading", "annualized", "expected profit",
+  or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the
+  visible "simulated — not indicative of live results" register.
+- **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the
+  AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or
+  any other part of this file; proposed journeys MUST carry a PnL-ledger (or, for a read surface, a
+  single-source-of-truth) acceptance criterion, keep the `default` profile and `v1` byte-identical, and
+  include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a
+  failure. *(critical)*
diff --git aruns/goal-session-structure_ui/iter-0/journey-history.pre.json bruns/goal-session-structure_ui/iter-0/journey-history.pre.json
new file mode 100644
index 0000000..d8c0fc4
--- /dev/null
+++ bruns/goal-session-structure_ui/iter-0/journey-history.pre.json
@@ -0,0 +1 @@
+{"journeys":{},"anti_goal_violations":[],"updated_at":""}
diff --git aruns/goal-session-structure_ui/iter-0/snapshot-sha bruns/goal-session-structure_ui/iter-0/snapshot-sha
new file mode 100644
index 0000000..e69de29
diff --git aruns/goal-session-structure_ui/session.json bruns/goal-session-structure_ui/session.json
new file mode 100644
index 0000000..2581dbd
--- /dev/null
+++ bruns/goal-session-structure_ui/session.json
@@ -0,0 +1,18 @@
+{
+  "session_id": "structure_ui",
+  "started_at": "2026-07-06T23:02:41.903609Z",
+  "current_iter": 0,
+  "cli": "claude",
+  "agent_backend": "interactive",
+  "halt_config": {
+    "max_iterations": 60,
+    "stall_window": 3,
+    "regression_halt": true
+  },
+  "status": "in_progress",
+  "last_verdict": null,
+  "next_depth": "lean",
+  "auto_release": false,
+  "push_per_iter": true,
+  "push_branch": "goal/structure_ui"
+}
diff --git aruns/goal-session-structure_ui/state/blueprint.md bruns/goal-session-structure_ui/state/blueprint.md
new file mode 100644
index 0000000..56810d1
--- /dev/null
+++ bruns/goal-session-structure_ui/state/blueprint.md
@@ -0,0 +1,64 @@
+# App Blueprint — structure_ui
+
+<!--
+Coherence contract for the "Structure, made visible" UI-surfacing interlude (eras 1–4 frozen
+foundation). This interlude adds exactly ONE read-only page and ONE additive nav-registry entry;
+it OWNS no value and computes nothing. Every value below is already owned by an era-1–4 canonical
+source — the Structure view reads each verbatim. The coherence-auditor hard-fails any second
+computation, second endpoint, or client-side recomputation of these values.
+-->
+
+## Information Architecture
+
+**Layout shell:** top-bar nav + main content, dark-only. The top bar is **data-driven**: it renders
+whatever `GET /meta/ui-routes` returns (`nav: true` entries), never a hardcoded client list
+(`apps/frontend/components/NavBar.tsx`).
+
+**Navigation skeleton** (persistent top bar — every feature lives under one of these):
+
+```
+Tapeology
+├── Cockpit       /                         (live tape cockpit — unchanged)
+├── Journal       /journal  (+ /journal/[id])  (unchanged)
+├── Studies       /studies                  (backtest jobs — unchanged)
+├── Performance   /performance              (unchanged)
+└── Structure     /structure   [NEW]        (read-only structure surface — this interlude)
+```
+
+**Feature / journey homes** (each reachable in ≤2 clicks from the nav):
+
+| Feature / journey | Canonical home (route) | Nav section |
+|---|---|---|
+| J-01 — S/R levels + A/B/C confluence zones on a price chart | `/structure` (Levels & Zones section) | Structure |
+| J-02 — strategy registry (`v1` + `structure_tape`) + champion badge | `/structure` (Registry section) | Structure |
+| J-03 — `structure_tape`-vs-`v1` comparison + per-class A/B/C breakdown | `/structure` (Comparison section) | Structure |
+| J-04 — foundation regression sentinel | existing surfaces `/`, `/journal`, `/studies`, `/performance` (no new home) | all sections |
+
+All three visible journeys (J-01/J-02/J-03) are **sections of the single `/structure` page** — one
+new route, not three. The nav entry is owned by `apps/backend/app/meta.py` `UI_ROUTES` (served via
+`GET /meta/ui-routes`); adding it is the ONLY backend edit in this interlude.
+
+## Data Contract
+
+Every value the Structure view displays is already owned by an era-1–4 canonical source and is read
+**verbatim**. The Structure view registers **no new owned value** and performs **no new computation**
+(no client-side grading, PnL math, aggregation, or champion resolution). "Computed by" and "Served by"
+below are the *single* existing owners — the Structure page may only re-format what these endpoints return.
+
+| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
+|---|---|---|---|
+| Bar series + checksums (candles for the chart) | bar store (`research/bars` store) | `GET /research/bars` (+ `/{bar_series_id}`) | read verbatim; chart candles only |
+| S/R levels (price / timeframe / type) | `research/levels.py` (`_level`, `_swing_pivots`, `_prior_period_extremes`; no lookahead) | `GET /research/levels?symbol=&as_of=` | one price line per level, labelled by timeframe |
+| A/B/C confluence-zone class + score | `research/levels.py:_grade_zone` / `_confluence_zone` | `GET /research/levels` (`zone.class`) | badge taken from `zone.class`; **never** recomputed from breadth/score |
+| Registered strategies (`v1`, `structure_tape`) + class-scaled params | `Config.strategy_definition` (config-owned) | `GET /research/strategies` | entry rule, exit precedence, `stop_bps_by_class` / `r_multiple_by_class` / `size_multiple_by_class` |
+| Champion pointer (founding `v1`/`default`) | `JournalStore.get_champion_pointer` (store-owned) | `GET /research/strategies` + `GET /research/profiles` | one pointer, two read views; UI moves it **never** |
+| Backtest aggregates (n, net R, net $, `win_rate`, `max_drawdown_r`) | `research/backtests.py:_aggregate` | `GET /research/backtests/{backtest_id}` | run via `POST /research/backtests` (Studies job/poll pattern) |
+| Per-class A/B/C breakdown + `insufficient_sample` | `research/backtests.py:_aggregate_by_class` | `GET /research/backtests/{backtest_id}` (`aggregates_by_class`) | sub-minimum-n shown "insufficient sample" verbatim |
+| PnL-ledger rows + founding baseline | `research/pnl_ledger.py:ledger_projection` | `GET /research/pnl/ledger` | baseline row beside the comparison |
+| Datasets (for choosing the comparison input) | dataset store (`research/datasets`) | `GET /research/datasets` | immutable, checksummed |
+| UI route map (the nav itself) | `apps/backend/app/meta.py` `UI_ROUTES` | `GET /meta/ui-routes` | Structure entry added here; nav renders it verbatim |
+
+**No new owned value. No divergent serialization. The `/structure` page is a pure read/visualize
+surface** — any number that diverges from its API/MCP payload is a defect. `config_fingerprint` stays
+`4d665603569b9dbf`; `research/levels.py`, `research/backtests.py`, `research/strategies.py`,
+`config.py`, and the engine are untouched beyond the additive `meta.py` `UI_ROUTES` entry.
diff --git aruns/goal-session-structure_ui/state/evaluator-log.md bruns/goal-session-structure_ui/state/evaluator-log.md
new file mode 100644
index 0000000..e69de29
diff --git aruns/goal-session-structure_ui/state/journey-history.json bruns/goal-session-structure_ui/state/journey-history.json
new file mode 100644
index 0000000..d8c0fc4
--- /dev/null
+++ bruns/goal-session-structure_ui/state/journey-history.json
@@ -0,0 +1 @@
+{"journeys":{},"anti_goal_violations":[],"updated_at":""}
diff --git aruns/goal-session-structure_ui/state/lessons.md bruns/goal-session-structure_ui/state/lessons.md
new file mode 100644
index 0000000..5a3454e
--- /dev/null
+++ bruns/goal-session-structure_ui/state/lessons.md
@@ -0,0 +1,9 @@
+# Goal Session structure_ui — Lessons Learned
+
+Append-only ledger of takeaways from prior iterations. The goal-evaluator
+appends one entry per iteration; the goal-decomposer reads this file before
+planning each iteration to avoid repeating known pitfalls.
+
+Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
+failures, regression triggers, or decisions that worked well. Avoid
+restating the verdict (the evaluator-log.md already does that).
diff --git aruns/goal-session-structure_ui/telemetry.jsonl bruns/goal-session-structure_ui/telemetry.jsonl
new file mode 100644
index 0000000..db46d73
--- /dev/null
+++ bruns/goal-session-structure_ui/telemetry.jsonl
@@ -0,0 +1,14 @@
+{"mode":"new","max_iterations":60,"stall_window":3,"auto_release":false,"ts":"2026-07-06T23:02:43Z","session_id":"structure_ui","iter":null,"event":"session_start","cli":"claude"}
+{"iter_name":"goal-structure_ui-iter-0","prior_verdict":"null","prior_depth":"lean","snapshot_sha":"","ts":"2026-07-06T23:02:44Z","session_id":"structure_ui","iter":0,"event":"iter_start","cli":"claude"}
+{"agent":"goal-decomposer","ts":"2026-07-06T23:02:44Z","session_id":"structure_ui","iter":0,"event":"agent_invocation_start","cli":"claude"}
+{"agent":"goal-decomposer","status":"ok","wait_seconds":15,"run_seconds":289,"rc":"0","ts":"2026-07-06T23:07:48Z","session_id":"structure_ui","iter":0,"event":"dispatch_wait","cli":"claude"}
+{"agent":"goal-decomposer","exit_status":0,"duration_seconds":304,"retries":0,"ts":"2026-07-06T23:07:48Z","session_id":"structure_ui","iter":0,"event":"agent_invocation_end","cli":"claude"}
+{"depth":"lean","target_journeys":"J-01, J-02, J-03, J-04","ts":"2026-07-06T23:07:48Z","session_id":"structure_ui","iter":0,"event":"iter_dispatch","cli":"claude"}
+{"iter_name":"goal-structure_ui-iter-0","depth":"lean","ts":"2026-07-06T23:07:48Z","session_id":"structure_ui","iter":0,"event":"iter_dispatch","cli":"claude"}
+{"agent":"developer","ts":"2026-07-06T23:07:48Z","session_id":"structure_ui","iter":0,"event":"agent_invocation_start","cli":"claude"}
+{"agent":"developer","status":"ok","wait_seconds":3,"run_seconds":837,"rc":"0","ts":"2026-07-06T23:21:48Z","session_id":"structure_ui","iter":0,"event":"dispatch_wait","cli":"claude"}
+{"agent":"developer","exit_status":0,"duration_seconds":840,"retries":0,"ts":"2026-07-06T23:21:48Z","session_id":"structure_ui","iter":0,"event":"agent_invocation_end","cli":"claude"}
+{"agent":"reviewer","ts":"2026-07-06T23:21:48Z","session_id":"structure_ui","iter":0,"event":"agent_invocation_start","cli":"claude"}
+{"agent":"reviewer","status":"ok","wait_seconds":2,"run_seconds":188,"rc":"0","ts":"2026-07-06T23:24:58Z","session_id":"structure_ui","iter":0,"event":"dispatch_wait","cli":"claude"}
+{"agent":"reviewer","exit_status":0,"duration_seconds":190,"retries":0,"ts":"2026-07-06T23:24:58Z","session_id":"structure_ui","iter":0,"event":"agent_invocation_end","cli":"claude"}
+{"verdict":"PASS","attempt":1,"iter_name":"goal-structure_ui-iter-0","ts":"2026-07-06T23:24:58Z","session_id":"structure_ui","iter":0,"event":"review_verdict","cli":"claude"}
diff --git aruns/goal-session-structure_ui/trace/trace.jsonl bruns/goal-session-structure_ui/trace/trace.jsonl
new file mode 100644
index 0000000..5d4a6fc
--- /dev/null
+++ bruns/goal-session-structure_ui/trace/trace.jsonl
@@ -0,0 +1,3 @@
+{"step":1,"agent":"goal-decomposer","cli":"claude","backend":"interactive","ts":"2026-07-06T23:07:48Z","exit_code":0,"duration_seconds":304,"stdout_path":"0001-goal-decomposer.log","args":["-p","You are the goal-decomposer agent for goal-mode iteration planning.","","Mode: baseline","Session ID: structure_ui","Iteration index: 0","Iter name: goal-structure_ui-iter-0","Prior verdict: null","Prior depth: lean","","Project template: .claude/project-template.md","Project goal (SLICED — vision + anti-goals + failing/target journeys verbatim; stable passing journeys digested to one line): runs/goal-session-structure_ui/iter-0/goal-slice.md","  Full goal file: docs/goal.md — Read it ONLY if a digested journey becomes relevant to your plan.","Agent instructions: .claude/agents/goal-decomposer.md  <-- read this first","(CLAUDE.md is already in your system prompt — do not Read it again.)","","Recent evaluator log entries (last 3, pre-trimmed):","```","(no entries yet — first iteration)","```","Lessons learned (full file, append-only):","```","# Goal Session structure_ui — Lessons Learned","","Append-only ledger of takeaways from prior iterations. The goal-evaluator","appends one entry per iteration; the goal-decomposer reads this file before","planning each iteration to avoid repeating known pitfalls.","","Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising","failures, regression triggers, or decisions that worked well. Avoid","restating the verdict (the evaluator-log.md already does that).","```","Journey state (inline digest; Read runs/goal-session-structure_ui/state/journey-history.json only for fields the digest omits):","```","","```","","","","Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.","","Write the iteration spec to: docs/phases/goal-structure_ui-iter-0.md","BASELINE also: draft the coherence blueprint to runs/goal-session-structure_ui/state/blueprint.md per your agent instructions (Information Architecture + Data Contract, ~one screen, from docs/goal.md's Product Shape + Must-have journeys + Key Capabilities). The blueprint is auto-approved by default and the loop proceeds; pass --require-blueprint-approval to pause for human review after baseline.","","The spec MUST include a 'Goal Mode Metadata' section with at minimum:","  - Mode: baseline","  - Depth: lean | full","  - Target journeys: <comma-separated journey IDs>","","Do NOT write code or implement anything. The iteration spec and any blueprint edits are planning documents, not code. STOP after writing them."],"model":"claude-opus-4-8"}
+{"step":2,"agent":"developer","cli":"claude","backend":"interactive","ts":"2026-07-06T23:21:48Z","exit_code":0,"duration_seconds":840,"stdout_path":"0002-developer.log","args":["-p","You are the developer agent for goal-mode lean iteration.","","Iteration: goal-structure_ui-iter-0","Iter spec: docs/phases/goal-structure_ui-iter-0.md","Project goal: docs/goal.md  <-- read Must-have user journeys and Anti-goals","Project template: .claude/project-template.md","Agent instructions: .claude/agents/developer.md  <-- read this first","(CLAUDE.md is already in your system prompt — do not Read it again.)","","Mode: INITIAL BUILD","","","This is a LEAN goal-mode iteration. Implement only what the iter spec's IN SCOPE","section calls for. Tighter scope than a full phase. Do NOT introduce features","outside the iter spec's IN SCOPE list.","","When complete:","- Write dev handoff to: docs/handoffs/goal-structure_ui-iter-0-dev.md","- Update runs/goal-structure_ui-iter-0/status.json with current_step: dev_complete",""],"model":"claude-sonnet-5"}
+{"step":3,"agent":"reviewer","cli":"claude","backend":"interactive","ts":"2026-07-06T23:24:58Z","exit_code":0,"duration_seconds":190,"stdout_path":"0003-reviewer.log","args":["-p","You are the reviewer agent for goal-mode lean iteration.","","Iteration: goal-structure_ui-iter-0","Iter spec: docs/phases/goal-structure_ui-iter-0.md","Dev handoff: docs/handoffs/goal-structure_ui-iter-0-dev.md","Project template: .claude/project-template.md","Agent instructions: .claude/agents/reviewer.md  <-- read this first","(CLAUDE.md is already in your system prompt — do not Read it again.)","","Run: git diff HEAD -- . ':(exclude)*package-lock.json' ':(exclude)*yarn.lock' ':(exclude)*pnpm-lock.yaml' ':(exclude)*poetry.lock' ':(exclude)*uv.lock' ':(exclude)*Cargo.lock' ':(exclude)*.min.js' ':(exclude)*.min.css' ':(exclude)*.map' ':(exclude)runs/*' ':(exclude)reports/*' ':(exclude)docs/handoffs/*' ':(exclude)*.png' ':(exclude)*.jpg' ':(exclude)*.jpeg' ':(exclude)*.gif' ':(exclude)*.svg' ':(exclude)*.ico' ':(exclude)*.pdf' ':(exclude)*.woff' ':(exclude)*.woff2' ':(exclude)*.ttf'","  (this is the diff to review — lockfile/minified/binary/harness-artifact noise is pre-excluded)","Then run: git diff HEAD --stat -- '*package-lock.json' '*yarn.lock' '*pnpm-lock.yaml' '*poetry.lock' '*uv.lock' '*Cargo.lock' '*.min.js' '*.min.css' '*.map' 'runs/*' 'reports/*' 'docs/handoffs/*' '*.png' '*.jpg' '*.jpeg' '*.gif' '*.svg' '*.ico' '*.pdf' '*.woff' '*.woff2' '*.ttf'","  (stat of ONLY the excluded paths: if it lists dependency lockfiles, note WHICH changed and review the matching package.json/pyproject edit in the main diff; runs/ and reports/ churn is harness bookkeeping, outside review scope)","","Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.","","Write your review report to: reports/reviews/goal-structure_ui-iter-0-review.md","","The report MUST start with a line matching exactly:","**Verdict:** PASS","  or","**Verdict:** PASS_WITH_NOTES","  or","**Verdict:** FAIL",""],"model":"claude-sonnet-5"}
diff --git aruns/goal-structure_ui-iter-0/status.json bruns/goal-structure_ui-iter-0/status.json
new file mode 100644
index 0000000..8bcfbf8
--- /dev/null
+++ bruns/goal-structure_ui-iter-0/status.json
@@ -0,0 +1,13 @@
+{
+  "phase": "goal-structure_ui-iter-0",
+  "status": "in_progress",
+  "current_step": "dev_complete",
+  "updated_at": "2026-07-06T23:20:14.000000Z",
+  "started_at": "2026-07-06T23:20:14.000000Z",
+  "cli": "claude",
+  "blockers": [],
+  "changed_files": [],
+  "tests_run": true,
+  "browser_checks_run": false,
+  "next_action": "none"
+}
```
