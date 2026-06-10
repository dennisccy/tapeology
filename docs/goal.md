# Project Goal

## Vision

Tapeology is a **standalone, real-time tape-reading system for US stocks**. It does one
thing well: given a single ticker, it watches live order flow — trades, quotes, and
(later) the Level 2 book — and classifies the **current tape state**.

Its defining principle is **price impact, not raw aggression**. The question is never
just "are buyers buying?" but "when buyers buy aggressively, does price actually move
higher — or are they being absorbed?" — and symmetrically for sellers. A tape where
aggressive sell volume is high yet price refuses to fall is **bid absorption**, not
seller control, and Tapeology must say so.

Tapeology is deliberately narrow. It is **not** a scanner, not news/theme/fundamental
analysis, not a general charting/technical-analysis platform, not an execution or portfolio system — those are separate
projects. Tapeology receives a ticker (from a user or an upstream system) and answers, first:
*what is the tape doing right now, and how confident are we?* — and now, layered on top of that
read: *does the tape support my declared thesis, where is the idea invalidated, and is the system
itself measurably helping?*

The **deterministic, seedable simulator** proved the engine's correctness first and remains the
default, offline, no-keys foundation. **Real US-equity market data is now in scope**, in two
modes that reuse the exact same engine: **live** (streaming real trades/quotes in real time) and
**historical replay** (fetching a chosen past date/time window and replaying it at a selectable
speed). Both sit behind the same **replaceable provider interface**; **Alpaca** is the first real
vendor (**SIP** consolidated feed for historical replay — realistic spreads, free for data >15 min old;
free **IEX** feed for live) behind a **vendor-agnostic adapter**, so another vendor
(Polygon, Databento, …) can be added without touching the engine or API. The five tape states —
**buyer_control, seller_control, bid_absorption, ask_absorption, unclear** — are surfaced one
ticker at a time in a simple Next.js UI, identically for simulated, live, or replayed real data.

To turn that read into something **testable**, Tapeology also plots the watched price as a
**candlestick chart** and overlays **markers at meaningful tape-state transitions** (in **all
modes** — simulated, historical replay, and live), so a user can see whether a state actually
preceded the next move — the one focused chart the product allows, not a general charting
platform. The chart doubles as the **thesis canvas**: a declared thesis draws its invalidation
and level as labeled price-lines, with verdict-transition, entry, and confirmation marks at their
times. A watched session can be **paused and resumed** without losing what is on screen, and
historical windows are chosen in the user's **local time** with US-market-session quick-picks.

Tapeology now evolves from a tape **reader** into a narrow, real-market **tape decision-support
and research system**, built around four pillars:

1. **Setup types** — the user declares a **thesis** on the watched ticker from a small catalog of
   tape-native setups (**absorption reversal, trend continuation, level break-and-go, failed-move
   fade**), each long or short, each with a REQUIRED **invalidation price**.
2. **Tape confirmation** — the engine's existing states and features are continuously judged
   against the declared thesis: `pending | confirming | weakening | rejecting | invalidated`,
   every verdict carrying plain-language evidence, drawn as geometry on the price chart.
3. **Risk rules** — entry risk flags (chasing, too-tight invalidation, illiquidity, declaring
   against the tape), a hard invalidation trigger the system enforces, and — only after the
   evidence layer exists — an **entry checklist** whose named checks render **live margins**, so
   the moment-of-decision read is honest and glanceable rather than a naked signal.
4. **Review** — every thesis, verdict, hint, and the user's own logged entry/exit is recorded in
   a journal; review compares expected vs actual behaviour, tags mistakes, and grades **outcome
   and process on separate axes**, so "a good thesis that failed normally" is distinguishable
   from "a bad trade caused by poor execution".

The system is decision support, not a signal service: it never says buy or sell, never predicts,
and never claims an edge. It helps answer: *what kind of situation is forming? what should the
tape do if the thesis is valid? is the tape confirming, weakening, or rejecting it right now?
where is the idea invalidated? and — afterwards — was the review honest?* Because every hint,
verdict, stance, and study result is **recorded**, the system's own usefulness is itself
reviewable: **replay studies** re-run the setup grammar over real historical windows,
side-by-side with a seeded **random-arm-time null baseline**, so the user can check whether the
setups measurably help **before** trusting any cue live.

## Target Users

- A discretionary US-equity trader who already knows *which* ticker to watch and wants a
  fast, honest read on whether the current tape favors buyers, favors sellers, or is
  absorbing aggression.
- The same trader **at the moment of decision** in the real market: declaring a thesis on the
  watched ticker and needing an evidence-backed read on whether the tape confirms it, where it is
  invalidated, whether the entry conditions are met right now — and, while holding, whether the
  tape still supports the position.
- The trader **as their own researcher**: journaling theses and actual entries/exits, reviewing
  them honestly afterwards, and running replay studies over historical windows to check whether
  the system's setups measurably help before trusting any live cue.
- An upstream system (scanner, alerting, or another project) that pushes a ticker to
  Tapeology and consumes the resulting tape state over REST/WebSocket.
- The developer/operator validating the engine against known simulated scenarios.

## Success Criteria

The first success metric is **not** profit. In priority order:

- **Classifies known simulated scenarios.** For each of the five MVP scenarios
  (buyer_control, seller_control, bid_absorption, ask_absorption, unclear_chop) the engine
  reaches the expected tape state with reasonable confidence within a bounded warm-up,
  proven by an automated test per scenario.
- **Surfaces the read in the UI.** Watching a ticker shows, for that one ticker, live
  bid/ask/spread/last, recent trades, the core features, the current tape state, a
  confidence score, plain-language observations, and an event log — all driven by the
  engine and updating live over WebSocket.
- **Price impact, not aggression.** Absorption is detected specifically: high aggressive
  volume on one side with little/no price progress resolves to the matching absorption
  state rather than "control".
- **Single source of truth.** Tape state, features, and confidence for a ticker are
  computed exactly once in the engine and read identically by REST, WebSocket, and the UI.
- **Replaceable data.** The simulator and the real providers sit behind one provider interface;
  swapping the source (or the vendor) changes neither the engine nor the API.
- **Live real data.** With vendor credentials configured, watching a real US symbol during market
  hours streams real trades + quotes through the same engine and classifies the live tape state —
  the identical pipeline the simulator uses.
- **Historical replay.** Watching a real symbol over a chosen past date/time window fetches its
  real trades + quotes and replays them through the engine at a selectable speed; the resulting
  read is reproducible for a fixed symbol + window.
- **Real-data honesty.** An unknown symbol, an empty window, a closed market, missing credentials,
  and a live-feed gap each surface an explicit error or `stale` state — never a fabricated tape.
- **Resolved aggressor side.** On real (historical and live) data the aggressor side is resolved
  for the vast majority of prints via the quote rule plus a tick-test fallback; only a genuinely
  undecidable print (no quote and no prior trade) remains `unknown`. Historical recent-trades is no
  longer dominated by `unknown`.
- **Tape-state prediction chart.** For simulated data and historical replay, the cockpit plots the
  price as candlesticks (selectable 10 / 30 / 60 s bars) and marks meaningful tape-state
  transitions, so a user can visually judge whether a state preceded the subsequent price move. The
  chart's time axis shows **true clock time** — real market time for historical, a synthetic session
  clock for simulated — not elapsed playback seconds.
- **Pause / resume.** A watched session can be paused and resumed without tearing it down or
  clearing the UI; replay resumes deterministically and live resumes at current real data.
- **Local-time historical selection.** Historical windows are entered in the user's local timezone
  (with an explicit zone label and US-session quick-picks); the window fetched from the vendor
  matches the local window selected — no silent timezone shift.
- **Every Watch action gives immediate, honest feedback.** The instant a user clicks Watch — in
  simulated, live, or historical mode — the UI acknowledges the click with a pending/"connecting"
  state for that symbol, and every outcome (streaming data, empty window, provider unavailable,
  unknown symbol, market closed, request timeout, or unreachable backend) resolves to an explicit,
  distinct on-screen state within a bounded time. The UI never silently ignores a Watch click,
  never returns to or remains on the idle screen after a valid click, never leaves "Connecting…"
  running forever, and never shows a "live" cockpit that stays empty with no explanation — including
  on real feeds and off-hours.
- *(later)* **Predictive value, measured.** Beyond the visual chart read, an automated harness
  quantifies the directional edge of high-confidence tape states over the next 10 / 30 / 60 / 120
  seconds. ⚠️ **Realized — reshaped — by the research evolution:** validation is now done at the
  **setup-grammar** level by **replay studies** with null baselines (see below), not by
  state-edge measurement, and is a must-have rather than a later item.

The research evolution adds, in priority order:

- **A thesis can be declared and judged in all three modes.** Declaring a setup + direction +
  invalidation on the watched ticker yields deterministic, evidence-carrying verdicts
  (`pending → confirming / weakening / rejecting / invalidated`) — proven browser-side on seeded
  sim scenarios and identically available on live and historical data.
- **Invalidation is enforced, not advised.** A print through the declared invalidation resolves
  the thesis `invalidated` immediately (dwell-exempt, robust to a lone bad print), and the
  journal records the offending evidence.
- **The user's own actions are first-class.** Actual entries/exits are journaled verbatim;
  machine-derived execution checks (entered-before-confirmation, chased, held-through-stop,
  cut-confirming-early) ground review in recorded fact, and a holding-period **management
  stance** answers "does the tape still support this position?" descriptively.
- **Honest review, two axes.** Every resolved thesis is graded as outcome (`thesis_held |
  thesis_failed | no_read`) × process (`clean | flagged | violated`) from named, evidence-backed
  checks — distinguishing a good thesis that failed normally from poor execution. No composite
  scores.
- **The journal survives restarts** and never rewrites history: append-only verdict timelines,
  explicit gap events, explicit `expired` on data end.
- **The system's helpfulness is itself measurable.** Excursion outcomes in R units, segregated
  analytics (feed- and config-fingerprint-aware, abandonment always visible), and deterministic
  replay studies with seeded null baselines let the user check whether the setups help —
  **before** any live cue is trusted.
- **Cues come last and stay honest.** The entry checklist/stance (live margins, freshness
  checks) and setup-forming hints (descriptive, logged, baseline-citing) ship only after the
  evidence layer exists, and degrade explicitly (`no_fresh_tape`) when the tape is not live.
- **The engine keeps up, visibly.** Unpaced dense replay (studies) passes a CI-gated time budget
  and a `delivery_lag_seconds` metric makes any live processing lag explicit — never silent.
- **Nothing existing regresses.** J-01 – J-37 stay green; engine outputs are byte-identical with
  the research layer attached and no thesis declared.

## Key Capabilities

1. **Provider abstraction** for the event stream, selected by a watch **mode** (`sim` |
   `live` | `historical`): a deterministic, seedable **SimulatedProvider** (default; no network,
   no keys); a **live provider** that streams real trades/quotes in real time; and a
   **historical-replay provider** that fetches a past window and replays it at a chosen speed.
   The real providers talk to the vendor only through a **vendor-agnostic adapter** (Alpaca
   first — SIP consolidated feed for historical replay, free IEX feed for live; another vendor is one
   new adapter). The engine consumes provider events
   and never knows the source. Real timestamps are mapped to the engine's logical timeline
   (quote-before-trade preserved) so the engine stays unchanged and deterministic per stream. The
   real (and, for the simulator, a synthetic session-start) **epoch origin** is preserved alongside
   that logical timeline as a canonical **display anchor**, so the chart can render **true clock
   time** without the engine ever reading wall-clock (determinism unchanged).
2. **Core input events**: `TradeEvent` (ticker, timestamp, price, size, side ∈
   {buy, sell, unknown}); `QuoteEvent` (ticker, timestamp, bid, ask, bid_size, ask_size);
   and later `BookLevelEvent` (ticker, timestamp, side ∈ {bid, ask}, price, size, level).
3. **Trade aggressor classification (quote rule + tick-test fallback)**: trade price ≥ current
   ask ⇒ aggressive buy; price ≤ current bid ⇒ aggressive sell, using the quote in effect at the
   trade's timestamp. When no quote is in effect yet or the print is strictly between bid and ask,
   fall back to the **tick test** against the prior trade price (uptick ⇒ buy, downtick ⇒ sell,
   zero-tick ⇒ carry the last non-zero direction). Only a genuinely undecidable print — no quote
   **and** no prior trade — stays `unknown`. This rule is engine-level, so it sharpens **live** as
   well as historical; because far more prints get a side, real-data features and tape state read
   more truthfully than the quote-only rule did — an intended fidelity gain, not a regression.
4. **Rolling feature windows** maintained concurrently at **10s, 30s, 60s, 180s, 300s**.
5. **Core features** per window: `trade_speed`, `volume_speed`, `aggressive_buy_ratio`,
   `aggressive_sell_ratio`, `net_aggressive_volume`, `large_print_count`,
   `average_spread`, `spread_change`, `buy_price_impact`, `sell_price_impact`,
   `absorption_score`, `bid_refresh_score`, `ask_refresh_score`, `liquidity_imbalance`.
   *(later)* `liquidity_pull_score`.
6. **Tape-state classifier** mapping features → one MVP state + a confidence score + a
   short list of human-readable observations:
   - **buyer_control** — high aggressive_buy_ratio, positive buy_price_impact, stable
     spread, elevated trade_speed.
   - **seller_control** — high aggressive_sell_ratio, negative sell_price_impact, stable
     spread, elevated trade_speed.
   - **bid_absorption** — high aggressive sell volume, price does not move meaningfully
     lower, bid appears to refresh, seller impact weakens.
   - **ask_absorption** — high aggressive buy volume, price does not move meaningfully
     higher, ask appears to refresh, buyer impact weakens.
   - **unclear** — mixed signals, weak evidence, a spread **wide relative to the instrument's
     price / typical spread**, low trade_speed, or no clean price impact.
7. **Watch lifecycle**: start/stop watching a ticker; each watched ticker has an
   independent engine instance fed by the provider.
8. **REST + WebSocket API**: `POST /watch/{ticker}` (optional body selects mode + historical
   params; empty body = sim), `DELETE /watch/{ticker}`, `GET /tape/{ticker}/state`,
   `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`,
   `WS /tape/{ticker}/stream`, plus real-data helpers `GET /symbols/search` (tradable-symbol
   lookup) and `GET /market/clock` (open/closed + next open/close).
9. **Simple single-ticker Next.js UI** showing the panels in Success Criteria, with a live
   event log and observations — not a complex trading platform. A **data-source selector**
   (Live / Historical / Simulated) drives a **symbol search** (real modes), a **date + time-window
   picker** and **replay-speed** control (historical), and a **market-status** indicator (live);
   the cockpit itself is identical across modes.
10. **Event-log / observation generation**: the engine emits discrete, human-readable
    messages on meaningful transitions, e.g. "Buyer aggression increasing", "Seller
    aggression increasing", "Large sell print absorbed", "Large buy print absorbed", "Ask
    refreshing at <price>", "Bid refreshing at <price>", "Tape state changed to
    buyer_control", "Tape state changed to unclear".
11. **Five simulated scenarios** that deterministically drive the engine toward each MVP
    state: buyer_control, seller_control, bid_absorption, ask_absorption, unclear_chop.
12. **Engine price + marker history buffer**: alongside the per-tick snapshot, the engine
    accumulates the watched price as **OHLC bars at 10 / 30 / 60 s** and a series of **meaningful
    tape-state-transition markers** (state + confidence + timestamp), using config-driven
    thresholds (no magic numbers). Computed once in the engine and served read-only.
13. **Tape-state prediction chart (UI)**: a **candlestick** chart of the watched price with a
    **bar-size selector** (10 / 30 / 60 s) and **markers at meaningful tape-state transitions**
    (green buyer_control, red seller_control, amber bid/ask_absorption; unclear unmarked), with
    pan/zoom and a **true-clock time axis** (real market time for historical; a synthetic session
    clock for simulated — never elapsed playback seconds). Shown for **simulated and historical**
    only, built on a lightweight client-side financial-charting library. ⚠️ **Amended by the
    research evolution (capability 22):** the chart now renders in **all modes including live**
    (display-only epoch anchor from the first live record; determinism untouched) and carries the
    **thesis geometry** overlays of capability 25. J-17/J-18 semantics are unchanged.
14. **Pause / resume a watch**: freeze and continue a watched session **without** tearing it down
    or clearing the UI. Replay (sim/historical) resumes exactly where it left off; live freezes the
    view and resumes at current real data (no fabricated backfill). The paused state is surfaced in
    the snapshot; Stop still fully tears the instance down.
15. **Historical window selection in local time**: the date/time picker defaults to the user's
    local timezone with an explicit **zone label** and **US-session quick-picks** ("Open 9:30 ET",
    "Close 16:00 ET", "Full RTH"), each annotated with the local equivalent; the fetched window
    equals the user's selected local window.
16. *(nice-to-have, later)* Optional extended states: `fake_breakout_risk`,
    `fake_breakdown_risk`, `liquidity_pull`, `liquidity_stack`, `exhaustion`.
17. *(nice-to-have, later)* Level 2 book ingestion (`BookLevelEvent`) and
    `liquidity_pull_score` / liquidity-stack features.
18. *(nice-to-have, later)* Persistence (PostgreSQL / Redis / Parquet / DuckDB) — only if a
    concrete need arises; Phase 1 is in-memory. ⚠️ **Amended by the research evolution:** a
    **journal-scoped SQLite** store (capability 28) is now a must-have — research records only;
    tape data stays unpersisted.
19. *(nice-to-have, later)* Replay/backtest harness measuring predictive value of
    high-confidence states over 10 / 30 / 60 / 120 s. ⚠️ **Superseded by replay studies**
    (capability 32): setup-grammar validation with seeded null baselines, a must-have.

Capabilities **20 – 34** are the research evolution — decision support and validation layered
strictly on top of capabilities 1 – 19, which remain unchanged:

20. **Engine snapshot observers (the research seam)**: `TapeEngine` exposes a generic observer
    list — `on_event(event, snapshot)` invoked at the end of every processed event, and
    `on_status(status)` invoked on every stream-status change (status flips do not pass through
    events, so stale/closed/failed handling REQUIRES this hook). Observers are exception-isolated
    (an observer error is logged, surfaces `monitor_status: failed` on the research projection,
    and never kills the feeder), and the engine stays research-agnostic: the same stream yields
    **byte-identical** snapshots with observers attached or absent (automated equivalence test).
21. **Two new deterministic sim scenarios** (provider-level only; engine untouched):
    **`SIM-SHIFT`** — a sustained buyer-control phase, then an unclear/chop phase whose price
    band dips below the late-control price (drives weakening-after-confirmation,
    management-stance decay, and clean-process invalidation deterministically); and
    **`SIM-REVERSAL`** — a bid-absorption phase at a held price, then a buyer-control phase that
    lifts price (drives the absorption-reversal happy path, failed-move-fade confirmation, and
    positive excursions deterministically). Both seeded and documented like the existing five.
22. **Live chart + delivery-lag honesty**: the price chart (capability 13) renders in **live**
    mode via a **display-only epoch anchor** taken from the first live record (engine determinism
    untouched; the history buffer and `…/history` already accrue and serve live data). The
    snapshot carries a canonical **`delivery_lag_seconds`** (feeder-owned: latest record's epoch
    vs wall clock) so a dense tape that outruns processing is *visible*, never silent.
23. **Declared thesis**: on the watched ticker the user declares `setup_type ∈
    {absorption_reversal, trend_continuation, level_break, failed_move_fade}` × `long | short`,
    a REQUIRED `invalidation_price`, and a `level_price` (required for the two level setups,
    rejected otherwise). The thesis freezes its **entry context** (state, confidence, last,
    spread, primary-window features) and its derived **expected-behaviour statements** at
    creation (later config changes never rewrite journal history), and is **bound to the source
    identity** (the snapshot's scenario descriptor: the sim scenario / the exact historical
    window / live SYMBOL) — never to the bare ticker string. One active thesis per ticker
    (second → 409); theses are immutable (abandon + redeclare is the only edit; redeclares are
    linked via `redeclared_from`).
24. **Confirmation verdict engine**: a pure per-event evaluator maps each engine snapshot to
    `pending | confirming | weakening | rejecting | invalidated` via config-owned, per-setup rule
    tables composed ONLY of existing states/features. Every transition records
    **`rule_first_true`** (first logical instant + price at which the raw rule held) and
    **`published_at`** (after the per-setup, logical-time **dwell**, which restarts at thesis
    creation — confirmation requires post-declaration evidence by construction). Sustained
    premise alone never confirms: **absorption-reversal confirms on the reversal** (the flip to
    matching control with real impact), not on the absorption. Once confirmed, fading evidence
    reads `weakening`, never a silent return to `pending`. **Invalidation is dwell-exempt and
    robust**: one print beyond the level by ≥ a config spread-multiple, or k consecutive prints
    beyond (config), auto-resolves the thesis with the offending prints recorded as evidence.
    The published timeline is **append-only** (`logical_ts, wall_ts, verdict, evidence,
    tape_state, confidence, last, rule_first_true`) with explicit **gap events** (`paused`,
    `watch_restarted`, stale spans) — never interpolated. Stream end / stop / failure
    auto-resolves an active thesis `expired(reason)` — UNLESS it carries an entry mark (a real
    position must never be orphaned): then it survives as **active-but-not-evaluated**, shown
    honestly as such, and re-attaches only to a watch of the **matching source** (recording a
    `watch_restarted` gap event); a mismatched source shows an explicit notice and is never
    evaluated against the thesis.
25. **Thesis geometry on the chart**: the declared invalidation and level render as labeled
    price-lines; published verdict transitions, entry/exit marks, and the first-confirmation
    mark render as markers visually distinct from tape-state markers — in every mode, computed
    once server-side and drawn verbatim.
26. **Entry risk flags** (computed once at declaration; advisory, never blocking; frozen on the
    thesis): `before_warmup`; `invalidation_too_tight` (vs a config spread multiple);
    `chasing_entry` (recent directional impact beyond a config return threshold);
    `wide_spread_illiquid` / `low_trade_speed` (reusing the classifier's own stability gates — no
    new thresholds); `against_expected_tape` (setup-aware: a long absorption-reversal declared
    during bid_absorption is NOT flagged; declared during seller_control it is). Incoherent
    input (wrong-side invalidation, missing/forbidden level, unknown enums) is a **422, never a
    flag**.
27. **Action marks + management stance**: the user journals an actual **entry** and **exit**
    (price prefilled from the current last, recorded verbatim, never inferred — no mark, no
    realized metric). An entry-marked thesis cannot be abandoned (anti-survivorship). While
    entry-marked and unresolved, the strip shows the **management stance** — `thesis_intact |
    thesis_weakening | thesis_invalidated` — derived from the same verdicts, plus live
    **distance-to-invalidation** ($ and R) and **open R** (R = |entry − invalidation|).
    Machine-derived **execution checks** (entered before first confirmation; chased beyond the
    `rule_first_true` price + threshold; exited beyond invalidation; cut a confirming thesis
    early) auto-SUGGEST mistake tags at review — the user confirms.
28. **Journal persistence (SQLite, scoped)**: stdlib `sqlite3` — WAL, `busy_timeout`,
    `BEGIN IMMEDIATE`, a single writer queue (never written from event processing or the WS
    serialization path). Tables: theses, verdict_events (**append-only** — the repository
    exposes no update/delete), hints, actions, studies, study_occurrences, plus a
    `schema_version`. Every record is stamped with its **bound source**, its **`data_feed`**
    (`sip | iex | sim`), and a **`config_fingerprint`** hashed over the ENTIRE frozen config
    (verdicts depend transitively on every classifier threshold). **No tape data is persisted**
    (committed test fixtures excepted). The DB path is env-configured; tests inject a temp path
    via the existing dependency-override pattern.
29. **Review**: a journal page (`/journal`) with filterable rows and a detail view rendering the
    frozen expected-behaviour statements (with final statuses) beside the verdict timeline in
    true clock time; **mistake tags** from a backend-owned taxonomy (`chased`,
    `entered_before_confirmation`, `ignored_rejection`, `ignored_risk_flags`,
    `moved_invalidation` *(self-assessed)*, `no_clear_setup`, `wrong_setup_type`, `overstayed`,
    `other` + required note); and **outcome × process grading** — outcome `thesis_held |
    thesis_failed | no_read` (1:1 from resolution) × process `clean | flagged | violated`
    (a config-owned rule over named, evidence-backed checks; never a numeric score). Being
    invalidated is never by itself a process failure — the system enforces invalidation.
30. **Excursion outcomes**: from the first published confirmation (and separately from the entry
    mark — two populations, never pooled), max favorable / max adverse excursion in **R units**
    over config horizons, reported as a **ternary outcome** per horizon (`+1R_first | −1R_first |
    neither_within_horizon`), with **spread-at-mark** recorded and horizons cut short by stream
    end or gaps flagged **truncated** — never extrapolated.
31. **Journal analytics, segregated**: per setup × direction — n with the **abandonment bucket
    always visible**, ternary excursion distributions, median time-to-confirm, tag frequencies,
    the acted-trade R distribution (kept apart from confirmation-anchored stats), and **median
    spread / R** beside every +1R figure (the no-cost caveat as a number). Groups under the
    config minimum sample read "insufficient sample" (n always shown). Aggregates NEVER pool
    across `data_feed` or `config_fingerprint`.
32. **Replay studies**: from `/studies`, run the setup grammar over an explicitly chosen symbol +
    past window — an **unpaced offline replay** through a fresh engine (the proven fixture-test
    pattern) that **auto-arms** occurrences per state-native arming rules (absorption_reversal
    and trend_continuation; level setups only with a user-supplied level, labeled
    **`hindsight_level`** and excluded from cross-study aggregates), records per-occurrence
    verdict summaries + excursions, and reports them **side-by-side with a seeded
    random-arm-time null baseline** (same window, direction, R definition, and horizons).
    Studies run as cancellable background jobs with explicit status/progress; results are
    deterministic, feed- and fingerprint-stamped; and a committed **reference study** (a
    moderate-density real SIP fixture spanning the configured horizons — ≈10 minutes — plus the
    seeded sims) reproduces pinned results in CI without credentials.
33. **Decision-support cues (built LAST, on the evidence layer)**: the **entry checklist /
    stance** — named checks rendered as **live margins** in their own units (verdict confirming;
    warm; `feed_live`; `tape_lag_ok`; spread within the stability domain; trade speed ≥ floor;
    invalidation distance ≥ spread multiple; not chasing, anchored at the `rule_first_true`
    price) with a **nearest-counterevidence** line, publishing through its own small dwell to
    `conditions_met | conditions_not_met | tape_against | no_fresh_tape`; and **setup-forming
    hints** — watched-ticker-only, state-native patterns (sustained absorption; sustained
    control), sustain-dwell + cooldown gated, state-descriptive wording, one-click prefilled
    declaration (invalidation still typed by the user — one click never creates a thesis),
    **every shown hint logged**, and every card citing the user's own study baseline for that
    setup/feed or exactly "no studied baseline — unvalidated pattern". An optional sound cue
    defaults OFF, fires on transitions only, with a cooldown.
34. **Engine performance gate** (prerequisite for studies and dense live tape): rolling-feature
    maintenance MUST be truly incremental — no per-event full-window rescans after evictions
    (today the incremental refresh path degrades permanently after the first eviction) — with
    feature values **byte-identical** to before, or the change justified and re-pinned as its own
    iteration; a CI timing gate replays a committed dense fixture unpaced within a configured
    budget.

## Non-Goals

- No stock scanning or screening.
- No news, theme, or sentiment analysis.
- No chart-pattern scanning, technical-indicator studies, drawing tools, or multi-symbol /
  multi-pane charting. *(The one allowed chart is the focused price candlestick + tape-state-marker
  overlay for simulated/historical replay, used to evaluate whether a state predicts direction —
  not a general charting platform.)*
- No fundamental analysis.
- No trade execution, order placement, or broker/brokerage integration.
- No portfolio or position management.
- No machine learning in the first version — the MVP classifier is rule/threshold-based.
- No multi-ticker dashboard or watchlist grid — the UI shows one ticker at a time.
- No persistence of market/tape data. ⚠️ **Amended by the research evolution:** a
  **journal-scoped SQLite** store is now in scope for research records only (theses, verdict
  timelines, hints, actions, reviews, studies); trades/quotes/candles/feature series remain
  unpersisted (committed test fixtures excepted).
- No claim or implication that the system is profitable, and nothing presented as trading
  advice.
- No auto-detection or scanning: theses are user-declared on the one watched ticker; hints exist
  only there; studies run only over explicitly chosen windows; nothing watches the market for
  you.
- No position sizing, account, capital, or P&L management; no currency P&L, equity curves, or
  win-rate-as-edge presentation anywhere — R statistics are journaled measurements with visible
  caveats and baselines, never performance claims.
- No parameter optimizer, grid search, or auto-tuning of thresholds — research defaults are
  config-owned and validated by studies, never fitted by a machine.
- No new market indicators: confirmation, stance, hints, and studies compose the EXISTING engine
  features and states only.

## Constraints

- **Backend:** Python 3.12+, FastAPI (uvicorn ASGI). Python is the implementation language
  — explicitly not Rust.
- **Frontend:** Next.js (App Router) + TypeScript; a simple single-ticker UI. The price chart uses
  a lightweight client-side financial-charting library — no server-side rendering and no new
  backend dependency.
- **Real-time transport:** WebSocket for live state/feature/event push; REST for
  request/response.
- **Data sources:** the deterministic, seedable **simulator** is the default/offline foundation
  (no keys); **real US-equity data** is selectable in two modes — **live** streaming and
  **historical replay** — from a real vendor (**Alpaca**: **historical replay uses the SIP consolidated
  feed** for realistic quotes/spreads — free for data >15 min old — while **live** uses the free IEX
  feed) behind a
  **vendor-agnostic adapter** so another vendor can be added without touching the engine/API.
- **Provider interface:** trades, quotes, and (later) L2 come from a replaceable provider
  selected by watch mode; the engine and API are provider-agnostic.
- **Credentials:** real-vendor API keys come only from environment/config (never committed). With
  no keys configured, the app runs simulator-only and the real modes report an explicit
  "provider unavailable" — they never fall back to fabricated data.
- **Local-time windows:** historical date/time windows are entered and displayed in the user's
  local timezone (with an explicit zone label) and resolved to the exact instant selected before
  the vendor fetch — no silent UTC reinterpretation of a naive value. **Dates are entered and shown
  as `dd-MM-yyyy`** via a custom date input (not a locale-dependent native picker) and times as 24h
  `HH:mm`; **every date rendered anywhere in the UI uses `dd-MM-yyyy`** (one shared formatter).
- **In-memory Phase 1:** rolling windows and state live in process memory; optional
  PostgreSQL/Redis/Parquet/DuckDB only if later needed.
- **No magic numbers:** every window length, threshold, large-print size, impact/absorption
  cutoff, and confidence boundary comes from config — no such literal in engine code.
- **Deterministic engine:** the same ordered event stream (and seed) yields identical
  features, state, and confidence — no wall-clock or randomness in classification.
- **No unbounded waits.** Every outbound vendor call — market-clock check, historical fetch, and
  live-stream connect — runs under an explicit timeout from config (no magic numbers); no external
  call may block a Watch request indefinitely. The frontend also enforces a client-side request
  timeout as a backstop, so a slow or hung backend always resolves to a visible error rather than a
  frozen UI. (A connected feed that then goes quiet is the separate, intentional `stale` state and
  is out of scope here — this targets the pre-connection "Connecting…" phase and silent no-ops.)
- **Research layer is observer-only:** it attaches via the engine's snapshot observers
  (capability 20) and MUST NOT mutate engine/classifier/feature state; engine outputs stay
  byte-identical with or without it (equivalence-tested). Observer failures are isolated, logged,
  and surfaced as `monitor_status: failed` — never a dead feeder, never a silently-continuing
  verdict stream.
- **Journal store discipline:** SQLite via stdlib `sqlite3` only — WAL, `busy_timeout`,
  `BEGIN IMMEDIATE`, one writer queue; no writes from event processing or the WS serialization
  path; `verdict_events` is append-only at the repository level; tests inject a temp DB path;
  the schema is versioned.
- **Verdict timing semantics:** dwell is logical-time, per setup type, and restarts at thesis
  creation; invalidation is dwell-exempt with config-owned bad-print robustness (ε·spread or
  k-consecutive); chase checks anchor at the recorded `rule_first_true` price, never the
  post-dwell publish; the stance publishes through its own dwell (no per-tick flapping).
- **Honesty stamps:** every research record carries its bound source, `data_feed`, and a
  `config_fingerprint` hashed over the entire frozen config; analytics and studies MUST NOT pool
  across feeds or fingerprints; live surfaces MUST label the IEX basis wherever SIP-derived
  research is shown nearby (the feed-per-mode seam stays config-owned so a SIP-entitled operator
  can upgrade live with one config value).
- **Evidence before cues:** the entry checklist/stance and hints MUST NOT be built before the
  journal, excursions, and studies exist and their journeys pass; hints MUST cite a study
  baseline or declare themselves unvalidated.
- **Research config defaults:** every new research value (per-setup verdict dwell, stance dwell,
  chase return threshold, invalidation spread-multiple and ε / k robustness, hint sustain +
  cooldown, rejecting-overstay window, excursion horizons, timeline cap, minimum sample size,
  delivery-lag bound, study null-arm count) lives in config with its sim/fixture calibration
  documented as a **research default** — a starting point, never a validated edge; no such
  literal in research code (the no-magic-numbers rule extends).
- **Engine throughput honesty:** unpaced replay of the committed dense fixture MUST pass a CI
  timing budget (capability 34) before studies ship, and the snapshot MUST surface
  `delivery_lag_seconds` so processing that falls behind a dense live tape is visible, never
  silent.

## Design Direction

- **Visual style:** clean, dense, instrument-panel feel — a single-ticker "tape cockpit".
  Monospaced numerics for prices/sizes; calm dark surface, restrained color.
- **Color semantics:** green = buy-side aggression / positive impact; red = sell-side
  aggression / negative impact; neutral/amber = absorption or unclear. Color encodes side
  and impact consistently everywhere.
- **Mood:** fast, honest, legible at a glance; no clutter, no chrome that isn't
  information.
- **Reference:** the trade blotter / Level-2 montage of a pro trading terminal, distilled
  to one ticker and one verdict.
- **Prediction chart:** one candlestick pane sized to the tape's short horizon (10 / 30 / 60 s
  bars), with tape-state markers in the same green/red/amber semantics — a focused decision aid,
  not a studies canvas.
- **Verdict & stance semantics:** `confirming` green, `weakening` amber, `rejecting` /
  `invalidated` red (invalidated with a terminal treatment), `pending` slate — the existing
  side/impact palette extended, never repurposed. Checklist items render their live margin in
  their own units (bps, ratios, seconds, spread-multiples); stance copy is factual ("6/6 checks
  pass"), and the nearest counterevidence is always one line away.
- **Copy register:** every research string is thesis-attributed, present-tense, and descriptive
  ("the tape confirmed *your* thesis"), never imperative ("buy / sell / enter / exit now"), never
  predictive, never certain. The cockpit's existing "Descriptive only — not trading advice"
  discipline extends verbatim to the thesis strip, hints, journal, analytics, and studies.
- **Glossary (shared vocabulary, used consistently by every iteration):**
  - **Thesis** — the user's declared idea: one setup type × direction on the watched ticker, with
    a required invalidation price (and a level for level setups).
  - **Setup type** — one of the four tape-native situation templates in the catalog.
  - **Premise** — the part of a setup's expected behaviour that can hold *before* the trigger
    (e.g. "sellers are being absorbed"); premise-intact alone never reads `confirming`.
  - **Verdict** — the evaluator's published judgement of the tape against the thesis:
    `pending | confirming | weakening | rejecting | invalidated`.
  - **Stance** — the entry checklist's aggregate at the moment of decision: `conditions_met |
    conditions_not_met | tape_against | no_fresh_tape`; thesis-gated, never unsolicited. The
    **management stance** (`thesis_intact | thesis_weakening | thesis_invalidated`) is its
    holding-period counterpart.
  - **Hint** — a logged, descriptive "this pattern is forming" card; never a command, never a
    thesis by itself.
  - **Action mark** — the user's journaled actual entry/exit (price + time), recorded verbatim.
  - **R** — the invalidation distance |entry reference − invalidation|; the unit for excursions
    and realized moves (no currency P&L).
  - **Excursion** — the max favorable/adverse move in R after a mark, reported per horizon as
    `+1R_first | −1R_first | neither_within_horizon`.
  - **Study** — a deterministic, unpaced replay of the setup grammar over a chosen historical
    window, reported against a seeded random-arm-time **null baseline**.
  - **Config fingerprint** — a hash of the entire frozen config stamped on every record so
    results are never silently compared across different thresholds.

## Product Shape

### Navigation / information architecture

- **Watch (`/`)** — the single-ticker tape cockpit and the app's home. A **data-source selector**
  (Live / Historical / Simulated) plus a ticker control (`POST /watch` on submit) and the live
  read for the watched ticker: bid / ask / spread / last, recent trades, the core feature
  readouts, the current **tape state** + **confidence**, the **observations** list, and the
  **event log**. Everything streams over `WS /tape/{ticker}/stream`. The source selector reveals
  mode-specific controls — a **symbol search** (real modes), a **date + time-window picker** and
  **replay-speed** control (historical; speed changes apply **live** to the running replay), and a
  **market-status** indicator (live) — without
  changing the cockpit. It remains exactly one screen; a small indicator shows the source being
  watched (the sim scenario, "live AAPL", or "historical AAPL <window>"). Above the cockpit, a
  **price chart** — candlesticks with a bar-size selector, tape-state markers, a **true-clock
  time axis**, and (when a thesis exists) the **thesis geometry** (invalidation/level
  price-lines; verdict, entry, and confirmation marks) — is shown in **all modes** (live included,
  via the display-only epoch anchor). Between the chart and the panel grid sits the **thesis
  strip**: a one-line declare affordance when idle; when declared, the active thesis (setup,
  direction, invalidation in mono, expected-behaviour statuses, verdict + evidence, risk-flag
  chips, resolve / mark-entry / mark-exit controls) — and, once the cue layer exists, the entry
  checklist + stance or the holding-period management stance. A small **hint dock** under the
  tape-state panel shows the current setup-forming hint when one is active. The watch controls include **Pause / Resume** (freeze and
  continue without clearing) beside Stop, with a **PAUSED** indicator when paused. The Historical
  **date/time-window picker** defaults to **local time** (with a zone label; dates entered and shown
  as **dd-MM-yyyy** via a custom date input) and offers
  **US-session quick-picks** (Open 9:30 ET / Close 16:00 ET / Full RTH).

- **Journal (`/journal`)** — the research record: a filterable table of every thesis (ticker,
  bound source, data feed, setup, direction, declared date `dd-MM-yyyy`, resolution, outcome ×
  process grades, reviewed), plus the hint log and the **analytics** view (capability 31). A row
  opens **`/journal/[id]`** — the review detail: the frozen expected-behaviour statements with
  final statuses beside the verdict timeline in true clock time, entry risk flags, action marks,
  execution checks, excursions, the outcome × process quadrant, the mistake-tag picker + note,
  and a **"re-watch this window"** affordance that pre-fills the historical picker from the
  thesis's bound window (or a live thesis's anchored real window).

- **Studies (`/studies`)** — create and monitor replay studies (symbol + past window + setup +
  direction, optional manual level), with job status / progress / cancel, and read results:
  occurrence rows, aggregates side-by-side with the seeded null baseline, truncation and
  `hindsight_level` labels, feed + config-fingerprint stamps.

- The top bar carries the **Cockpit / Journal / Studies** navigation — the first multi-page
  surface; the cockpit remains the home and stays one screen.

### API surface (Phase 1)

- `POST /watch/{ticker}` — begin watching; spins up an engine instance fed by the provider. An
  optional JSON body selects the mode and historical params (`{mode, start, end, speed}`, where
  `start`/`end` are timezone-aware instants for the selected local window); an empty body = a
  simulated watch (backward compatible).
- `DELETE /watch/{ticker}` — stop watching; tears the instance down (a live socket is closed).
- `GET /symbols/search?q=` — tradable-symbol suggestions for the search box (real modes).
- `GET /market/clock` — market open/closed + next open/close (live-mode status).
- `GET /tape/{ticker}/state` — current tape state + confidence (canonical).
- `GET /tape/{ticker}/features` — current per-window feature values (canonical).
- `GET /tape/{ticker}/events` — recent trade/quote events + emitted observations.
- `GET /tape/{ticker}/summary` — compact snapshot (quote, last, state, confidence, headline
  features).
- `WS /tape/{ticker}/stream` — live push of state, features, quote/last, and event-log
  messages.
- `GET /tape/{ticker}/history?bar=<10|30|60>` — engine-computed **OHLC bars + tape-state markers**
  for the price chart (simulated + historical); a pure projection of the engine history buffer.
- `POST /watch/{ticker}/pause` and `POST /watch/{ticker}/resume` — freeze/continue the feeder
  **without** tearing the instance down; the engine, its snapshot, and the history buffer survive.
- `POST /watch/{ticker}/speed` — set the historical replay speed of a **running** watch (validated
  against the configured allowed speeds; out-of-set → 422, not-watched → 404). The change applies
  **immediately** to the in-progress replay (delivery pacing only — the engine stays deterministic),
  with no re-fetch and no restart.

The research evolution adds (every projection computed once server-side):

- `POST /research/thesis` — declare a thesis on a watched ticker (`{ticker, setup_type,
  direction, invalidation_price, level_price?}`); 404 not-watched, 409 an active thesis exists,
  422 incoherent input (wrong-side invalidation, missing/forbidden level, unknown enums).
  Returns the full thesis projection (id, frozen expected behaviour, entry risk flags, verdict
  `pending`).
- `GET /research/thesis/active?ticker=` — the active-thesis projection (`thesis: null` is a
  normal state, not an error); the canonical REST read that MUST equal the WS frame's `thesis`
  key verbatim.
- `POST /research/thesis/{id}/resolve` — body `{resolution: "played_out" | "abandoned"}` only —
  `invalidated` and `expired` are system-owned (422 if requested); 409 if already resolved.
  Process checks and both grades are computed once here.
- `POST /research/thesis/{id}/action` — record an entry or exit mark (`{kind, price}`), stamped
  at the current logical + wall time, recorded verbatim; an entry-marked thesis refuses
  `abandoned`.
- `POST /research/thesis/{id}/review` — `{mistake_tags, note?}` validated against the taxonomy;
  409 unless resolved; flips the thesis to `reviewed`.
- `GET /research/journal?ticker=&setup_type=&direction=&resolution=&status=&limit=&offset=` —
  compact journal rows; `GET /research/journal/{id}` — full detail (timeline incl. gap events,
  statements with final statuses, flags, marks, execution checks, excursions, grades, replay
  linkage).
- `GET /research/analytics` — the segregated aggregates (capability 31), partitioned by
  `data_feed` and `config_fingerprint`.
- `POST /research/studies` / `GET /research/studies` / `GET /research/studies/{id}` /
  `POST /research/studies/{id}/cancel` — create, list, read, and cancel replay-study jobs
  (status: queued | running | done | failed | cancelled, with progress).
- `GET /research/taxonomy` — the setup catalog (+ per-setup parameter requirements +
  expected-behaviour templates), risk-flag and mistake-tag catalogs, and verdict/stance enums
  with display copy — the single backend owner of every research label.
- `WS /tape/{ticker}/stream` gains one **additive `thesis` key** (the same projection as
  `…/thesis/active`; `null` when none) — the engine snapshot fields are untouched.

### Canonical values (single source of truth — computed once in the engine, displayed identically everywhere)

- **Tape state** (buyer_control | seller_control | bid_absorption | ask_absorption |
  unclear) — classified once per engine tick; REST, the WS stream, and the UI show the same
  value.
- **Confidence score** — produced once with the state by the classifier; never recomputed
  in the API or UI.
- **Core features** (the 14 MVP features, per window) — computed once in the feature
  engine; `…/features`, the stream, and the UI read the same numbers.
- **Current bid / ask / spread / last** — derived once from the latest quote/trade;
  identical across REST, WS, and UI (spread = ask − bid).
- **Observations & event-log messages** — generated once by the engine on transitions; the
  stream and UI render the same messages (no UI-side re-derivation).
- **Price history & tape-state markers** — OHLC bars (per selectable size) and meaningful-state
  markers are derived once in the engine's history buffer; `…/history` and the chart read the same
  series; the chart never recomputes side, state, or price.
- **Paused state** — owned once by the engine/feeder and surfaced in the snapshot; the UI reads it
  (no UI-side guess) to render the PAUSED indicator and toggle the control.
- **Stream status** (connecting | live | stale | paused | closed) — owned once by the engine/feeder;
  the UI's status indicator reads it. A live-feed gap flips it to **stale**; **pause** flips it to
  **paused** (without teardown) and resume restores the prior status; stop or stream exhaustion
  flips it to **closed** — never a fabricated "live".
- **Thesis projection** (thesis fields, expected-behaviour statuses, verdict + evidence, risk
  flags, monitor status) — produced once by the research monitor; REST `…/thesis/active`, the WS
  `thesis` key, the thesis strip, and the chart geometry read it verbatim.
- **Published verdict + evidence** — computed once by the verdict engine per event; the
  append-only timeline (with its gap events) is the only history and is never recomputed at read
  time.
- **Stance + per-check margins** (entry checklist and management stance) — computed once
  server-side; the UI renders the margins verbatim and derives nothing.
- **Expected-behaviour statements** — derived once at creation and stored frozen; review renders
  the stored statements, not re-derived ones.
- **Excursions, execution checks, and grades** — computed once at their defining moments (marks /
  resolution) and persisted; analytics aggregates the persisted rows only.
- **Hints** — pattern, evidence, and baseline citation produced once when shown; the hint log is
  the record.
- **Study results** (occurrence rows, aggregates, null baseline) — computed once by the study
  runner and persisted; the studies page renders stored results.
- **Taxonomies & research display copy** (setups, flags, tags, verdict/stance labels) — owned
  once by the backend (`/research/taxonomy`); the frontend hardcodes none of them.
- **Source / feed / config-fingerprint stamps** — assigned once at record creation; every view
  shows the stored stamp.
- **`delivery_lag_seconds`** — owned once by the feeder and surfaced in the snapshot; the UI lag
  readout and the `tape_lag_ok` check read the same value.

## Must-have user journeys

Journeys **J-01 – J-09** are browser-verifiable against simulated data. A watched sim ticker is
bound to a known scenario (reserved sim tickers), so the expected tape state is deterministic;
simulated scenarios run on an accelerated clock, so each resolves within seconds (a browser
journey need not wait the full 60–300 s of real window time). These remain must-haves — the
real-data work MUST NOT regress them.

Journeys **J-10 – J-15** add real-vendor data and assume provider credentials are configured in
the environment for verification. **Historical replay** is reproducible for a fixed symbol +
past window (verifiable any time a key is present). **Live streaming** needs market hours, so its
real-socket behavior is confirmed by an operator/gated check (e.g. a credentialed integration
run), while its UI controls and honest-degradation states are browser-verifiable on their own.
With **no credentials**, the real modes MUST show an explicit "unavailable" — itself a verifiable
journey requiring no feed.

- **J-01: Watch a ticker and see the live tape cockpit**
  - Steps:
    1. Visit `/`
    2. Enter the buyer-control sim ticker (`SIM-BUYER`) and submit (Watch)
    3. Wait for the stream to connect and the panels to populate
    4. Read the bid/ask/spread/last panel; the recent-trades list; the feature readouts;
       the tape-state panel; the confidence score; the observations list; the event log
  - Acceptance: within the scenario's warm-up, every panel renders live values —
    bid/ask/spread/last are numeric and spread = ask − bid; the recent-trades list shows
    trades with price/size/side; trade_speed, aggressive_buy_ratio, aggressive_sell_ratio,
    net_aggressive_volume, buy_price_impact, and sell_price_impact each show a number; the
    tape-state panel shows one of the five states with a confidence score; the observations
    list and event log each show at least one message; and values update over the WebSocket
    without a page reload.

- **J-02: Buyer-control scenario is identified**
  - Steps:
    1. Visit `/`, watch `SIM-BUYER`
    2. Let the scenario stream until the tape state stabilizes
    3. Read the tape-state panel, confidence, and the buy/sell price-impact readouts
  - Acceptance: the tape state settles on **buyer_control** with confidence ≥ the configured
    "reasonable" threshold; aggressive_buy_ratio reads high and buy_price_impact reads
    positive; the event log contains "Tape state changed to buyer_control".

- **J-03: Seller-control scenario is identified**
  - Steps:
    1. Visit `/`, watch `SIM-SELLER`
    2. Let it stream until the state stabilizes
    3. Read the tape-state panel, confidence, and price-impact readouts
  - Acceptance: the tape state settles on **seller_control** with confidence ≥ threshold;
    aggressive_sell_ratio reads high and sell_price_impact reads negative; the event log
    shows "Tape state changed to seller_control".

- **J-04: Bid absorption is detected (price impact, not aggression)**
  - Steps:
    1. Visit `/`, watch `SIM-BIDABS`
    2. Let it stream until the state stabilizes
    3. Read the tape state, the aggressive-sell readout, the last-price movement, and the
       absorption / bid-refresh readouts
  - Acceptance: although aggressive **sell** volume is high, the last price does **not** move
    meaningfully lower; the tape state settles on **bid_absorption** (not seller_control)
    with confidence ≥ threshold; absorption_score / bid_refresh_score read elevated and the
    event log shows an absorption message (e.g. "Large sell print absorbed" / "Bid
    refreshing at <price>"). This is the defining price-impact case: high aggression + no
    price progress ⇒ absorption.

- **J-05: Ask absorption is detected (price impact, not aggression)**
  - Steps:
    1. Visit `/`, watch `SIM-ASKABS`
    2. Let it stream until the state stabilizes
    3. Read the tape state, the aggressive-buy readout, the last-price movement, and the
       absorption / ask-refresh readouts
  - Acceptance: although aggressive **buy** volume is high, the last price does **not** move
    meaningfully higher; the tape state settles on **ask_absorption** (not buyer_control)
    with confidence ≥ threshold; absorption_score / ask_refresh_score read elevated and the
    event log shows an absorption message (e.g. "Large buy print absorbed" / "Ask refreshing
    at <price>").

- **J-06: Unclear / choppy tape is reported as unclear**
  - Steps:
    1. Visit `/`, watch `SIM-CHOP`
    2. Let it stream
    3. Read the tape-state panel and confidence
  - Acceptance: the tape state reads **unclear** (mixed signals / wide spread / low
    trade_speed / no clean price impact) with low confidence; the UI does not assert buyer
    or seller control. The system honestly says "unclear" rather than forcing a directional
    call.

- **J-07: Tape-state transitions are announced in the event log and observations**
  - Steps:
    1. Visit `/`, watch a scenario ticker from a cold start
    2. Watch the event log and observations as the engine warms up and the state resolves
    3. Note the messages emitted as the state changes
  - Acceptance: as the engine moves from its initial unclear read to the scenario's resolved
    state, the event log records a "Tape state changed to …" message at the transition and
    the observations list reflects current evidence (e.g. "Buyer aggression increasing",
    "Large sell print absorbed", "Ask refreshing at <price>"). Messages append live over the
    WebSocket.

- **J-08: REST and the live UI agree (single source of truth)**
  - Steps:
    1. Visit `/`, watch a scenario ticker and let the state stabilize
    2. Read the tape state, confidence, and key features shown in the UI
    3. In a new tab, open `GET /tape/{ticker}/state` and `GET /tape/{ticker}/features` for
       the same ticker
  - Acceptance: the tape state and confidence from the REST endpoint exactly match the UI for
    that ticker, and the feature values from `…/features` match the UI's feature readouts —
    one engine value per metric, read identically by REST, the WS stream, and the UI (no
    divergence between views).

- **J-09: Stop watching a ticker**
  - Steps:
    1. Visit `/`, watch a scenario ticker
    2. Use the UI control that issues `DELETE /watch/{ticker}`
    3. Observe the UI
  - Acceptance: after stopping, the live stream for that ticker closes and the cockpit
    returns to an idle/empty state with no further updates; re-watching the same ticker
    starts a fresh read.

- **J-10: Choose a data source (Live / Historical / Simulated)**
  - Steps:
    1. Visit `/`
    2. Use the data-source selector to switch between Live, Historical, and Simulated
    3. Observe which controls appear for each mode; then watch `SIM-BUYER` in Simulated
  - Acceptance: the selector offers exactly the three modes; selecting **Live** reveals a symbol
    search + a market-status indicator; **Historical** reveals a symbol search + a date/time-window
    picker + a replay-speed control; **Simulated** reveals the ticker input. Choosing Simulated and
    watching `SIM-BUYER` still resolves to **buyer_control** exactly as J-01/J-02 (no regression).

- **J-11: Replay a real historical session**
  - Steps:
    1. Visit `/`, select **Historical**, enter a real symbol (e.g. `AAPL`), pick a past
       date/time window and a replay speed, and submit (Watch)
    2. Wait for the backend to fetch the window and the cockpit to populate
    3. Read the cockpit and let the replay run
  - Acceptance: the backend fetches that window's **real** trades + quotes from the vendor and
    replays them through the **same** engine; every cockpit panel populates with real values
    (bid/ask/spread/last, recent trades with price/size/side, the feature readouts, a tape state +
    confidence, observations, event log), updating over the WebSocket; REST and the UI agree
    (single source of truth). The read is reproducible for a fixed symbol + window.
    *(Verified with credentials configured.)*

- **J-12: Stream a real live ticker**
  - Steps:
    1. Visit `/`, select **Live**, enter/search a real symbol (e.g. `AAPL`), and submit (Watch)
    2. Observe the cockpit and the status indicator
  - Acceptance: during market hours with credentials configured, the cockpit streams **real-time**
    trades + quotes from the vendor and classifies the live tape state + confidence, updating over
    the WebSocket, with the status reading **live**. *(Real-socket behavior confirmed by an
    operator/gated credentialed run; the Live controls + status render without a feed.)*

- **J-13: Find a symbol by search**
  - Steps:
    1. Visit `/`, select **Live** or **Historical**
    2. Type a partial symbol or name into the search box
    3. Pick a suggestion
  - Acceptance: the search returns matching tradable symbols (symbol + name) from the vendor and
    selecting one fills the ticker for the watch. Free-text entry remains possible.
    *(Verified with credentials configured.)*

- **J-14: Real-data edge cases are handled honestly (no fabricated data)**
  - Steps:
    1. Attempt each: a Live/Historical watch with **no credentials** configured; an **unknown**
       symbol (real mode); a Historical window with **no data**; a **Live watch while the market is
       closed**
    2. Observe the result in each case
  - Acceptance: each surfaces an explicit, distinct state and **never a cockpit/tape**: no
    credentials → "real-data provider unavailable"; unknown symbol → "not a tradable symbol";
    empty window → "no data for that window"; market closed → "market is closed" (with the next
    open). No trades, quotes, prices, or tape state are synthesized to force a green result.
    *(The no-credentials / unknown-symbol / closed-market paths are verifiable without a live feed.)*

- **J-15: A live-feed gap shows `stale`, then recovers**
  - Steps:
    1. Watch a real symbol in **Live** mode
    2. Observe the status indicator across a lull in the feed and when data resumes
  - Acceptance: when no live event arrives within the configured window the status flips to
    **stale** (and the engine fabricates **no** trades during the gap); when events resume it
    returns to **live**. *(Confirmed by an operator/gated credentialed run.)*

Journeys **J-16 – J-20** cover the side-classification fix, the prediction chart, pause/resume, and
local-time window selection. **J-17 and J-19 run on simulated data and are browser-verifiable with
no credentials**; **J-16, J-18, and the correct-window-fetch half of J-20 assume vendor credentials
are configured**, while their UI/control surfaces remain browser-verifiable without a feed. These
additions MUST NOT regress J-01 – J-15.

- **J-16: Historical recent-trades show a resolved side (not `unknown`)**
  - Steps:
    1. Visit `/`, select **Historical**, enter a liquid symbol (e.g. `AAPL`) over a past
       regular-hours window, and Watch
    2. Let the window replay and read the **recent-trades** list
  - Acceptance: the large majority of trades show **buy** or **sell** (not `unknown`); where a quote
    is in effect, at/above-ask reads buy and at/below-bid reads sell, and mid-spread / pre-quote
    prints are resolved by the tick test; only a genuinely undecidable print may remain `unknown`;
    the `unknown` fraction is far lower than before. *(Verified with credentials configured.)*

- **J-17: Price chart with tape-state markers on simulated data**
  - Steps:
    1. Visit `/`, watch `SIM-BUYER`
    2. Observe the price chart above the cockpit; switch the **bar size** between 10 / 30 / 60 s
    3. Watch `SIM-SELLER`, then `SIM-BIDABS` / `SIM-ASKABS`
  - Acceptance: a **candlestick** chart of price renders and updates during replay; the bar-size
    selector re-renders the candles; **markers** appear at meaningful tape-state transitions in the
    correct colors (green for buyer_control, red for seller_control, amber for absorption; unclear
    unmarked). `SIM-BUYER` trends up with buyer markers, `SIM-SELLER` trends down with seller
    markers, and the absorption scenarios show amber markers with price held. *(No credentials;
    browser-verifiable.)*

- **J-18: Inspect tape-state prediction on a real historical chart**
  - Steps:
    1. Visit `/`, select **Historical**, watch a real symbol over a past window
    2. Read the candlestick chart; switch bar size 10 / 30 / 60 s; pan/zoom to a meaningful marker
       and inspect the price that follows it
  - Acceptance: candlesticks reflect the **real** replayed prices; the bars match the engine-served
    `…/history` data at each bar size; markers align with tape-state transitions; the user can
    visually assess whether a marked state preceded the subsequent move. *(Verified with credentials
    configured.)*

- **J-19: Pause and resume a watch without losing state**
  - Steps:
    1. Visit `/`, watch `SIM-BUYER` and let the cockpit populate
    2. Click **Pause**; observe the tape, chart, counters, and tape state
    3. Click **Resume**; then later click **Stop**
  - Acceptance: on **Pause**, the recent trades, chart, features, and tape state **freeze**, a
    **PAUSED** indicator shows, and the session is **not** cleared (no teardown); on **Resume**, the
    stream continues from where it left off; **Stop** still closes the stream and returns the cockpit
    to idle. *(No credentials; browser-verifiable.)*

- **J-20: Pick a historical window in local time with US-session quick-picks**
  - Steps:
    1. Visit `/`, select **Historical**
    2. Read the timezone label on the date/time picker and the **quick-picks** ("Open 9:30 ET",
       "Close 16:00 ET", "Full RTH")
    3. Choose a date and click a quick-pick (e.g. **Open**); then Watch
  - Acceptance: the picker defaults to the user's **local** time with an explicit zone label; each
    quick-pick is annotated with its local equivalent and fills a valid regular-hours start/end;
    with credentials, the window fetched from the vendor **matches the selected local window** (no
    UTC shift). *(The local-time labels + presets are browser-verifiable without a feed; the
    correct-window fetch is verified with credentials.)*

- **J-21: A Watch click is always acknowledged immediately (no silent dead-click)**
  - Steps:
    1. Visit `/` (idle screen)
    2. Enter a valid symbol, choose **Live** (then repeat for **Historical** and **Simulated**), click **Watch**
    3. Observe the cockpit in the first ~1 second after the click, before any tape data arrives
  - Acceptance: within ~1s the cockpit leaves the idle screen and shows an explicit pending/"connecting"
    state labelled with the symbol (e.g. "Connecting to <SYMBOL>…" with the connecting status dot). The
    idle screen never remains after a valid Watch click, in any mode. *(Browser-verifiable.)*

- **J-22: A slow or hung request resolves to an explicit error, never an infinite spinner**
  - Steps:
    1. Trigger a Watch whose backend vendor call is slow/unreachable (live or historical against an
       unresponsive provider, or the backend itself down)
    2. Wait
  - Acceptance: the wait is **bounded** — backend vendor calls run under an explicit timeout and the
    frontend enforces a client-side timeout backstop. Within that bound the connecting state is replaced
    by a clear, distinct error (e.g. "Market data provider timed out" / "Backend unreachable"); the
    "Connecting…" spinner never runs indefinitely. The bound MUST be real — enforced at the vendor-call
    boundary, not only an async wrapper a blocking/large-response call can defeat — and the backend
    timeout MUST be shorter than the frontend client timeout (see J-28/J-29). *(Backend timeout proven
    by unit test with a mocked slow adapter; the client-side timeout proven by a non-resolving request.)*

- **J-23: A failed initial connection or stream surfaces an explicit error (no swallowed failures)**
  - Steps:
    1. Watch a symbol where the watch is accepted but the initial snapshot fetch or live stream then
       fails (backend becomes unreachable right after Watch, or no first event ever arrives)
  - Acceptance: the UI surfaces an explicit "couldn't connect to the tape stream" error (reusing the
    existing error banner / failure panel) within a bounded time; the connecting state does not persist
    forever, and no error path is silently swallowed (no empty `catch`, no dropped promise rejection).
    An empty cold-start snapshot does **not** by itself count as a successful connection: the
    failure/empty-resolution path stays armed until either real activity streams or an explicit honest
    empty-state is shown (see J-25/J-26). *(Browser-verifiable with the backend stopped after watch.)*

- **J-24: Invalid or empty Watch input gives immediate inline feedback**
  - Steps:
    1. With the symbol field empty (or whitespace), click **Watch**
    2. In **Historical** mode, also try Watch with a missing/invalid date-time window
  - Acceptance: the UI immediately shows a clear inline validation message (e.g. "Enter a ticker
    symbol" / "Choose a valid time window") or the Watch button is disabled until input is valid;
    clicking Watch never results in a silent no-op. *(No credentials; browser-verifiable.)*

Journeys **J-25 – J-27** harden the Watch lifecycle *after* the click resolves, on **real feeds and
off-hours** — the conditions sim-only verification never exercises. They MUST be verified beyond the
simulated scenarios (real historical/live, quiet/illiquid symbols, closed-market) and MUST NOT regress
J-01 – J-24.

- **J-25: A valid Watch never silently returns to (or stays on) the idle screen — in real modes and off-hours**
  - Steps:
    1. In **Historical** mode, enter a real symbol (e.g. `AAPL`) + a valid past window and click **Watch**
    2. In **Live** mode, enter a real symbol and click **Watch** — including **outside US market hours**
       and on a **thin / illiquid** symbol
    3. After the click, watch the screen through the first ~1s and until the watch resolves
  - Acceptance: in every case the idle screen leaves within ~1s (an explicit pending/"connecting" state
    labelled with the symbol) **and** the watch resolves to a **non-idle terminal state** — streaming
    data, an explicit connecting/waiting state (J-26), an explicit honest state (**market-closed** with
    next open / **provider unavailable** / **no data for window** / **stale** / **closed**), or an
    explicit error. The idle screen MUST NOT reappear or persist after a valid Watch, and the pending
    state MUST NOT be cleared without landing on one of those non-idle states. An off-hours Live watch
    shows the explicit **closed** state — never idle, never a fake-"live" empty cockpit. *(Real modes
    verified with credentials; the closed-market / unavailable paths are browser-verifiable without a
    feed.)*

- **J-26: A connected stream with no data yet explains itself (never a mute cockpit)**
  - Steps:
    1. Watch a stream that connects but has no immediate activity — a **Live** watch on a quiet/illiquid
       symbol, or the moment just after connect before the first trade, or a sparse **Historical**
       window — in both modes
    2. Observe the cockpit after the connecting state, while the tape is still empty
  - Acceptance: while connected but before any trade/quote has arrived, the cockpit shows an explicit,
    human-readable waiting/empty state labelled with the symbol and mode (e.g. "Connected to <SYMBOL> —
    waiting for the first trade…"), **not** a set of blank panels under a bare **live** indicator. The
    status MUST NOT read a confident **live** over an empty tape; an empty tape reads as
    connecting/waiting (then **stale** once the configured gap is exceeded). The user always knows the
    watch is alive and what it is waiting for. *(Browser-verifiable with a provider that yields no
    immediate first event.)*

- **J-27: No usable data — whether silent or failed — resolves to an explicit honest state within a bounded time**
  - Steps:
    1. Start a watch that is accepted (200) and connects but whose feed delivers **no first event**
       (live: a quiet/off-hours symbol whose socket stays silent; historical: an effectively empty replay)
    2. Separately, start a watch whose background **feeder task fails** after acceptance — the
       provider/stream raises, or the feeder exits unexpectedly — before or after the first frame
    3. Wait past the configured bound in each case
  - Acceptance: each case is **bounded** by config and resolves to an explicit, distinct outcome — a
    no-data/empty message, **stale**, **closed**, or an error — owned once by the engine's
    `stream_status` (never a fabricated **live** over an empty tape, never a stuck **connecting**). A
    feeder exception/early-exit is **logged server-side and surfaced** to the UI (the existing failure
    panel / error banner / honest status dot), never swallowed, and never leaves the engine frozen at
    cold-start. *(Backend-provable by unit tests with a no-event provider and with a feeder that raises;
    UI-verifiable by the resulting state.)*

Journeys **J-28 – J-30** cover real-vendor responsiveness — honest, truly-enforced timeouts (J-28),
fast Historical loading of busy windows (J-29), and a fast symbol search (J-30). They assume vendor
credentials are configured and MUST NOT regress J-01 – J-27.

- **J-28: A vendor-call timeout is truly enforced and honestly reported (backend wins, message is actionable)**
  - Steps:
    1. Trigger a Historical/Live watch whose vendor fetch genuinely exceeds the budget — an oversized
       window, or a slow / CPU-bound large response
    2. Observe how and when the error appears, and what it says
  - Acceptance: the timeout is enforced at the **vendor-call boundary** (a real HTTP/SDK deadline), not
    only via an async wrapper that a blocking or CPU-bound (large-response) call can defeat; the
    **backend timeout is shorter than the frontend client timeout** so the user sees the backend's
    honest, distinct error rather than a client-side give-up; and the message is **actionable for the
    real cause** — a deterministically oversized window says so (e.g. "that window is very high-volume —
    try a shorter range") instead of a misleading "please try again" that will deterministically fail
    again. *(Backend bound proven by a test simulating a slow / large vendor response; the
    backend<frontend ordering and message mapping are verifiable.)*

- **J-29: A Historical watch of a real liquid symbol loads quickly and within bounds — never a routine timeout**
  - Steps:
    1. Select **Historical**, enter a **liquid** symbol (e.g. `TSLA`) and a busy regular-hours window
       that includes the **market-open minute** (09:30–09:31 ET, or its local equivalent such as
       14:30–14:31 BST), and click **Watch**
    2. Measure the time from click to the cockpit showing real values / a warm read; then re-watch the
       same symbol + window
  - Acceptance: the cockpit populates with the window's **real** trades + quotes within a bounded,
    configured time, and a legitimate busy window MUST NOT routinely time out. Loading is **optimized
    for speed, not merely given a longer timeout**: trades and quotes are fetched **concurrently**,
    needless pre-flight round-trips are removed, a fetched window may be **cached / reused** (re-watching
    the same symbol + window is near-instant), and the engine **warms promptly** (the warm-up events are
    delivered with minimal initial pacing / a bounded fast-forward, then normal replay pacing resumes).
    The fetch wait is filled with an explicit **progress** state (J-26), never a blank / idle screen.
    These speed-ups MUST NOT introduce a timeout or error, MUST NOT fabricate or drop trades/quotes, and
    a genuinely slow path still resolves to an honest bounded state (J-28). A **longer** window (multi-
    hour, up to full RTH) MUST be loaded by **chunked, bounded-concurrency** sub-window fetches stitched
    in order rather than refused (see **J-34**). *(Verified with credentials
    against a real liquid symbol + busy window; the fetch concurrency and warm-up timing are covered by
    tests.)*

- **J-30: Symbol search is fast and responsive**
  - Steps:
    1. Select **Live** or **Historical** and type a few characters (e.g. "TSL", then backspace and
       "AAP") into the symbol search, typing quickly
    2. Observe how fast suggestions appear — including the **very first search after a backend (re)start**
  - Acceptance: suggestions appear within a small bounded time after the debounce, and the **first
    search after startup is not a multi-second stall** — the tradable-symbol universe is **warmed /
    cached** (fetched once at startup or first availability, ideally persisted across restarts and
    refreshed in the background) rather than re-fetched per request; rapid typing **cancels stale
    in-flight requests** (no pile-up, no out-of-order overwrite) and repeated queries are served from a
    cache; a sensible **minimum query length** avoids over-broad single-character scans. Free-text watch
    entry always remains possible, and any vendor hiccup still yields an **empty list, never an error or
    a stuck spinner**. *(Browser-verifiable; the cache warm / refresh and request cancellation are
    covered by tests.)*

Journeys **J-31 – J-35** are the refinement pass: a **true-clock chart axis** (J-31), **live**
replay-speed changes (J-32), **real-data classification calibration** so a genuine move is not stuck
on `unclear` (J-33), **chunked loading of long historical windows** up to a full trading day (J-34),
and **dd-MM-yyyy dates everywhere** with a custom date input (J-35). J-31, J-32, and J-35 are
browser-verifiable without credentials; J-33's gating check is a deterministic fixture (its real-GME
confirmation needs credentials); J-34's gating checks are chunk-stitch unit tests (its full-window
load is verified with credentials). These additions MUST NOT regress **J-01 – J-30**.

- **J-31: The price chart shows TRUE clock time, not elapsed playback seconds**
  - Steps:
    1. Visit `/`, select **Historical**, watch a real symbol over a known past intraday window (e.g. a
       recent trading day, 09:30–09:40 ET — 14:30–14:40 BST in London) and let it replay
    2. Read the chart's **time axis**, hover the **crosshair**, and inspect a **tape-state marker**
    3. Switch the bar size 10 / 30 / 60 s; then watch a `SIM-*` ticker and read its chart axis
  - Acceptance: on **historical** replay the candles, crosshair, and markers are stamped at the
    window's **real market clock time** (e.g. ~14:30–14:40 of the chosen day, formatted `dd-MM-yyyy
    HH:mm:ss` in the user's local zone with an explicit zone label — see J-35), **never** an elapsed
    0…600 s playback counter; switching bar size keeps the real-time axis. On **simulated** data the
    axis shows a **synthetic session clock** anchored to the watch-start instant (a real clock face,
    not elapsed seconds). The engine still bins on its **deterministic logical timeline** and the
    chart recomputes no price/state/side — true time comes from an **additive canonical epoch anchor**
    exposed by the engine/serializer and read verbatim (single source of truth + determinism
    preserved; **J-17 / J-18** still pass). *(Historical verified with credentials; the sim axis and
    the axis date formatting are browser-verifiable.)*

- **J-32: Replay-speed changes take effect immediately (no re-Watch)**
  - Steps:
    1. Visit `/`, select **Historical**, watch a real symbol at **1×** and let the replay run
    2. While it is running, change the **replay-speed** control to **10×** (and back) **without
       clicking Watch again**
    3. Observe the replay cadence (new candles / new trades arriving) and the watched session
  - Acceptance: the new speed applies to the **in-progress** replay within ~1 s — the cockpit and
    chart **continue from their current position** at the new cadence, with **no** re-fetch of the
    window, **no** engine restart, and **no** teardown of the watch. Speed is a **delivery-pacing
    change only**, so the resulting features/state/confidence for the window are unchanged
    (determinism preserved). A change made while **paused** applies on resume. An out-of-set speed is
    rejected (HTTP 422); setting speed on a not-watched ticker is a 404. *(Historical replay verified
    with credentials; the control + immediate-apply wiring are browser-verifiable, and the backend
    speed endpoint is covered by a unit test.)*

- **J-33: A genuine directional move on real data classifies as control, not perpetual `unclear`**
  - ⚠️ **Superseded by J-36** — the iter-13 pass was synthetic-fixture-only and is **INVALID**; replayed
    on real data the GME window reads 100% `unclear` (IEX quoted spread ~2,700 bps vs the ≤30 bps gate,
    though sell-ratio 0.77 / impact −4.79 / speed 1.5 all pass). The real fix is tracked by **J-36**.
  - Steps:
    1. Replay a real symbol over a window with a **strong, fast directional move** — the reference
       case is **GME on 14-05-2024, 14:30–14:40 London time** (13:30–13:40 UTC), which fell >10% in
       minutes near the open
    2. Read the **tape-state** panel + confidence as the drop plays, and the chart **markers**
  - Acceptance: the drop resolves to **seller_control** (and the mirror: a comparable rally →
    **buyer_control**) with confidence ≥ the configured reasonable threshold, and seller markers
    appear at the transition — it does **not** sit on `unclear` through an obvious >10% move. The fix
    is that the directional/absorption gates judge **spread and price-impact relative to the
    instrument's price level / recent volatility** (config-owned — **no magic numbers**), **not** a
    single absolute dollar constant tuned for the simulator; so a real ~$30–50 name with a
    proportionate spread is no longer forced to `unclear`, while a genuinely **wide relative** spread,
    or high aggression with no proportionate price progress, still reads `unclear` / absorption (the
    *Honest uncertainty* and *Price impact over raw aggression* anti-goals hold). All five simulated
    scenarios **J-01 – J-09** and the existing classifier unit tests MUST stay green after re-tuning.
    *(Gated by a **deterministic regression fixture** reproducing the failing conditions — warmed,
    high sell ratio, strong negative impact, spread wide in absolute $ but normal relative to price —
    asserting `seller_control`; the real-GME confirmation is verified with credentials.)*

- **J-34: A long historical window loads via chunking instead of "very high-volume"**
  - ⚠️ **Superseded by J-37** — chunking only parallelized within the 8s cap; it never decoupled
    first-data from full-load, so long/dense real windows still time out into "very high-volume". The
    real fix (progressive streamed loading) is tracked by **J-37**.
  - Steps:
    1. Visit `/`, select **Historical**, choose a **liquid** symbol and a **long** window — click the
       **Full RTH 9:30–16:00** quick-pick (or any multi-hour window) — and Watch
    2. Wait for the fetch and watch the cockpit + chart populate; then re-watch the same symbol +
       window
  - Acceptance: the long window loads its **real** trades + quotes and the cockpit/chart populate
    within a bounded, configured time **without** the "that window is very high-volume — try a shorter
    range" error; the advertised **Full RTH** quick-pick MUST work for a liquid symbol. The fetch is
    **split into bounded sub-windows fetched with bounded concurrency** and **stitched in epoch
    order** into one real window — it MUST NOT fabricate, drop, reorder, or de-duplicate real prints,
    and a re-watch is near-instant from the window cache (the SAME real window). This is **fast by
    design** (parallelizing the vendor SDK's sequential pagination), not "a longer timeout": any
    timeout raise stays modest and the **backend bound MUST remain shorter than the frontend client
    timeout** (J-28). A window genuinely too large to load within budget still resolves to the honest,
    actionable "shorter range" message (J-28) — that message is now only a **true backstop**, not the
    routine outcome for a normal long session. *(Gated by unit tests on chunk splitting + in-order
    stitching with no fabricated/dropped/reordered prints; the full-window load is verified with
    credentials against a liquid symbol.)*

- **J-35: Dates are dd-MM-yyyy everywhere, entered via a custom date input**
  - Steps:
    1. Inspect every place the UI shows a date — the **chart time axis / crosshair** (J-31), the
       **market-status** times (live), the **watched-source** descriptor ("historical <SYM>
       <window>"), recent-trade / event timestamps on real data, and the historical picker
    2. In **Historical** mode, enter a date in the **date field**, pick a window, and Watch
  - Acceptance: every rendered date reads **`dd-MM-yyyy`** (and date-times **`dd-MM-yyyy HH:mm[:ss]`**,
    24h) from a **single shared formatter** — no `MM/DD/YYYY`, ISO `YYYY-MM-DD`, or "Jun 8"-style date
    remains visible anywhere in the UI. The native `<input type="date">` is **replaced by a custom
    `dd-MM-yyyy` text input** (validated), so both entry and display are `dd-MM-yyyy`. Timezone
    correctness is **unchanged**: the field still carries the explicit **local zone label** and
    resolves to the exact tz-aware instant the user selected with **no silent UTC shift**, and the
    fetched window still matches the selected local window (**J-20** and the *Timezone-correct
    windows* anti-goal hold). *(Browser-verifiable.)*

Journeys **J-36 – J-37** REOPEN the two real-data defects the user verified still fail after iter-13.
The iter-13 "pass" for J-33/J-34 was validated only against **hand-built synthetic fixtures** with the
real-data legs marked "operator-gated" — the real Alpaca data was never replayed, so two real-data
defects shipped. These two journeys are therefore gated by **committed real captured market data**, not
synthetic fixtures; an "operator-gated" manual note is explicitly **insufficient** (see the *Real-data
journeys are proven with real data* anti-goal). They MUST NOT regress **J-01 – J-35**.

- **J-36: A real directional move classifies as control on real data — proven by a committed real-data fixture**
  - Steps:
    1. In **Historical** mode replay the reference window — **GME on 14-05-2024, 14:30–14:40 London
       time (13:30–13:40 UTC)**, which fell ~12% in minutes into an LULD trading halt
    2. Read the **tape-state** panel + confidence as the drop plays, and the chart **markers**
  - Acceptance: the drop resolves to **seller_control** with confidence ≥ the configured reasonable
    threshold (and the mirror: a comparable rally → **buyer_control**), with seller markers at the
    transition — it does **not** sit on `unclear` through the obvious >10% move. *(Measured today the
    engine reads 100% `unclear`: on the default IEX feed the quoted spread is ~2,700 bps versus the
    ≤30 bps gate, even though aggressive-sell-ratio 0.77, sell-price-impact −4.79, and trade-speed 1.5
    all clearly pass — the spread gate alone vetoes the call.)* The fix is twofold and **config-owned
    (no magic numbers)**: **(a)** historical replays fetch the **SIP consolidated feed** so the quoted
    spread is realistic (the account has SIP historical, free for data >15 min old; on a calm name the
    SIP spread is sub-bps where the single-venue IEX spread is hundreds of bps) — the feed per mode is
    explicit and config-owned, and **live** streaming may remain the free IEX feed; **(b)** the
    classifier is **robust to quoting artifacts** — a clearly directional move (strong one-sided
    aggressive ratio AND real price impact AND elevated speed) MUST resolve to control even when the
    quoted spread is momentarily wide or quotes are **absent/crossed** (e.g. around a halt), with spread
    acting as a **graded confidence factor, not an absolute veto**. Genuinely mixed/illiquid tape (weak
    ratio or no real price impact) still reads `unclear` / absorption (the *Honest uncertainty* and
    *Price impact over raw aggression* anti-goals hold). All five simulated scenarios **J-01 – J-09**
    and the existing classifier unit tests MUST stay green after the change. *(Gated by a **committed
    real-data fixture** captured from the GME window above driving an automated test that asserts
    `seller_control` at the drop, runnable in CI **without** live credentials; a synthetic fixture and
    an "operator-gated" note are NOT sufficient. The live SIP confirmation is re-run as a manual check.)*

- **J-37: A long/dense window loads progressively — first chunk replays immediately, the rest streams in — proven by a committed real-data fixture**
  - Steps:
    1. In **Historical** mode choose a **liquid** symbol and a **long** window — the **Full RTH
       9:30–16:00** quick-pick (or any multi-hour window) — and Watch
    2. Observe the cockpit + chart **begin within the frontend timeout**; keep watching as later data
       arrives; then re-watch the same symbol + window
  - Acceptance: **time-to-first-data is decoupled from total-window load** — the replay begins as soon
    as the **first chunk** is fetched (within the bounded budget, backend bound < frontend timeout) and
    subsequent chunks are fetched **in the background** and appended **in epoch order** as the replay
    advances; the system MUST **never** fetch the entire window before responding. The advertised **Full
    RTH** quick-pick MUST work for a liquid symbol **without** the "that window is very high-volume — try
    a shorter range" error; that message becomes a **true last-resort backstop** (e.g. the first chunk
    itself genuinely cannot load), never the routine outcome for a normal long/dense session. Correctness
    is preserved: streamed chunks MUST NOT fabricate, drop, reorder (beyond the canonical epoch order),
    or de-duplicate real prints, and a re-watch is near-instant from the window cache. The engine MUST
    process real consolidated-tape density without stalling *(today a ~50k-event window does not finish
    processing within budget)* — it MAY bound/aggregate the displayed series, but tape state and each
    feature stay **single-source and deterministic**. *(Gated by a **committed real-data fixture** for a
    long/dense real window driving an automated test that asserts (a) first-data/replay begins within
    budget, (b) no "high-volume" error, and (c) no fabricated/dropped/reordered prints across the
    streamed chunks, runnable in CI **without** live credentials; chunk-stitch unit tests alone and an
    "operator-gated" note are NOT sufficient. The live Full-RTH confirmation is re-run as a manual check.)*

Journeys **J-38 – J-68** are the **research evolution**: declared theses and tape confirmation
(J-38 – J-48), risk and lifecycle honesty (J-49 – J-51), the user's own actions and holding-period
support (J-52 – J-54), review and grading (J-55 – J-57), the **evidence layer** — excursions,
analytics, and replay studies (J-58 – J-62) — and, strictly **last**, the decision-support cues
(J-63 – J-67) plus the regression sentinel (J-68). Verdict-transition journeys are deterministic
on the seeded sims — including the two new scenarios **`SIM-SHIFT`** and **`SIM-REVERSAL`**
(capability 21) — so they are browser-verifiable without credentials; persistence journeys span a
backend restart; study journeys are gated by **committed real-data fixtures** per the established
J-36/J-37 standard. **Build order is binding: the cue journeys (J-63 – J-67) MUST NOT be
implemented before the evidence journeys (J-58 – J-62) pass** (the *Evidence before cues*
anti-goal). These additions MUST NOT regress **J-01 – J-37**.

- **J-38: Declare a thesis on the watched ticker**
  - Steps:
    1. Visit `/`, watch `SIM-BIDABS` (Simulated) and let the cockpit populate
    2. In the thesis strip, declare: setup **absorption_reversal**, direction **long**, an
       invalidation price below the current last; submit
    3. Read the thesis strip; in a new tab open `GET /research/thesis/active?ticker=SIM-BIDABS`
  - Acceptance: the strip shows an ACTIVE thesis — setup, direction, and invalidation (mono) —
    with the frozen **expected-behaviour statements** each rendering a live status (met /
    not-yet / violated); the verdict starts honestly at **pending** (dwell restarts at creation —
    no instant confirmation); the REST projection equals the WS frame's `thesis` key **verbatim**
    (single source of truth); declaration requires no page reload. *(No credentials;
    browser-verifiable.)*

- **J-39: Thesis creation is validated honestly (no silent coercion)**
  - Steps:
    1. With no ticker watched, attempt `POST /research/thesis` for an unwatched ticker
    2. Watch `SIM-BUYER`; in the form, declare **long** with an invalidation **above** the
       current last (wrong side) and submit
    3. Declare **level_break** without a level; then declare **absorption_reversal** with a level
    4. Declare a valid thesis; then attempt to declare a second on the same ticker
  - Acceptance: unwatched ticker → explicit 404; wrong-side invalidation → inline validation
    message + 422 and nothing created; missing level for a level setup → 422; a level supplied to
    a non-level setup → 422; a second active thesis → 409 with an explicit message. Input is
    never silently coerced, auto-corrected, or partially saved. *(No credentials;
    browser-verifiable.)*

- **J-40: Absorption-reversal confirms on the REVERSAL, not the absorption**
  - Steps:
    1. Watch `SIM-REVERSAL`; during its **bid-absorption phase**, declare **absorption_reversal /
       long** with an invalidation below the absorbed price
    2. Read the verdict and the statement statuses through the phase shift into buyer control
  - Acceptance: during sustained bid_absorption the verdict stays **pending** — the premise
    statements (e.g. "sellers absorbed, bid holding") read **met** while the trigger statement
    ("buyers take control with real upward impact") reads **not-yet**; sustained absorption alone
    MUST NOT read `confirming` (the classic trap — entering long while sellers still hammer the
    bid — is structurally excluded). When the scenario flips to buyer_control with real upward
    impact, the verdict publishes **confirming** (after its post-declaration dwell) with evidence
    citing the flip; the timeline records the transition with both `rule_first_true` and
    published timestamps. *(No credentials; browser-verifiable.)*

- **J-41: A thesis against the tape reads REJECTING, with evidence**
  - Steps:
    1. Watch `SIM-SELLER`; declare **trend_continuation / long** with an invalidation **far**
       below the current last (so the rejection publishes before any invalidation)
    2. Read the verdict, its evidence, and the timeline
  - Acceptance: after the dwell the verdict publishes **rejecting**, citing seller control / real
    downward impact in plain language — never a naked verdict; the thesis stays active (rejecting
    is a judgement, not a resolution); the expected-behaviour statements read violated/not-met
    honestly. *(No credentials; browser-verifiable.)*

- **J-42: Trend continuation confirms while control holds**
  - Steps:
    1. Watch `SIM-BUYER`; declare **trend_continuation / long**, invalidation below
    2. Read the verdict as the scenario streams
  - Acceptance: after the post-declaration dwell the verdict publishes **confirming** with
    evidence citing buyer control and positive impact; it remains confirming while the scenario's
    control persists (no flapping); statements read met. *(No credentials; browser-verifiable.)*

- **J-43: WEAKENING after confirmation on a shifting tape**
  - Steps:
    1. Watch `SIM-SHIFT`; during its buyer-control phase declare **trend_continuation / long**
       with an invalidation far below the chop band
    2. Let the scenario shift into its unclear/chop phase; read the verdict and timeline
  - Acceptance: the verdict publishes **confirming** during control, then — only after the
    configured logical-time dwell — **weakening** when the tape goes neutral after having
    confirmed (the confirmed→neutral rule; never a silent return to `pending`), with distinct
    plain-language evidence ("supporting evidence faded" register); the timeline holds both
    transitions at their logical timestamps; the published verdict never flaps per tick.
    *(No credentials; browser-verifiable; dwell asserted in logical time.)*

- **J-44: Invalidation is a hard, robust trigger**
  - Steps:
    1. Watch `SIM-SELLER`; declare any **long** thesis with an invalidation just below the
       current last
    2. Let the scenario print through the invalidation; read the strip, timeline, and journal
  - Acceptance: the qualifying print(s) flip the verdict to **invalidated** immediately —
    dwell-exempt — and the thesis **auto-resolves** `invalidated`; the strip shows the terminal
    treatment and the final timeline entry records the offending print price + logical timestamp
    as evidence. Robustness is config-owned: a single print must exceed the level by ≥ the
    configured spread-multiple ε, or k consecutive prints beyond it (a lone bad print inside the
    guard does NOT invalidate) — *the guard behaviour is proven by a unit test with a synthetic
    outlier print; the browser leg uses the deterministic sim fall.* *(No credentials;
    browser-verifiable.)*

- **J-45: Level break-and-go confirms only after the level is crossed**
  - Steps:
    1. Watch `SIM-BUYER`; declare **level_break / long** with a level **above** the current last
       (inside the scenario's deterministic rise) and an invalidation below
    2. Read the verdict before and after price crosses the level
  - Acceptance: pre-cross the verdict is **pending** with the cross statement not-yet (the latch
    is unset — no confirmation however strong the control); once last ≥ level (latched) and buyer
    control holds, the verdict publishes **confirming** citing the cross + control; the level
    line is visible on the chart at the declared price (J-48). *(No credentials;
    browser-verifiable.)*

- **J-46: Failed-move fade confirms on absorption of the break**
  - Steps:
    1. Watch `SIM-REVERSAL`; during its absorption phase declare **failed_move_fade / long** with
       the level just above the absorbed price (the broken level being faded) and an invalidation
       below
    2. Read the verdict through the absorption and the reclaim
  - Acceptance: during the absorption phase the verdict reads **confirming** ("the downside break
    is being absorbed") — for THIS setup the absorption *is* the expected behaviour, the
    deliberate asymmetry with J-40 made explicit by the statements; when buyers take control and
    price reclaims the level, the verdict remains confirming citing the reclaim; `rejecting`
    would require real downside follow-through (seller_control), which never occurs in this
    scenario. *(No credentials; browser-verifiable.)*

- **J-47: A thesis is bound to its source, and survives interruption only with a position**
  - Steps:
    1. Watch `SIM-BUYER`; declare **trend_continuation / long** (invalidation far below) and
       **mark an entry** (J-52)
    2. Stop the watch; read the strip/journal; then re-watch `SIM-BUYER`
    3. Separately: declare a thesis WITHOUT an entry mark and stop the watch
  - Acceptance: the entry-marked thesis survives the stop as **active-but-not-evaluated**, shown
    honestly ("not currently evaluated — re-watch this source to resume"), with NO verdicts
    appended while unwatched; re-watching the **matching source** re-attaches it and the timeline
    records an explicit **`watch_restarted` gap event** (never interpolated history). The
    unmarked thesis instead auto-resolves **`expired(watch_stopped)`**. A watch of a
    **different** source for the same symbol MUST NOT be evaluated against the thesis (explicit
    bound-source notice) — *the cross-source leg (e.g. a live thesis vs a historical replay of
    the same symbol) is enforced by the source-identity check and proven by a unit test; with
    credentials it is also operator-verifiable.* *(Sim legs: no credentials;
    browser-verifiable.)*

- **J-48: Thesis geometry is drawn on the price chart**
  - Steps:
    1. Watch `SIM-BUYER`; declare **level_break / long** with a level and an invalidation; later
       mark an entry
    2. Read the chart through confirmation
  - Acceptance: the chart shows a labeled **invalidation price-line** and **level price-line** at
    the declared prices; published verdict transitions appear as markers visually distinct from
    tape-state markers; the entry mark and first-confirmation mark appear at their times; all
    geometry is served by the backend projection and drawn verbatim (the chart computes nothing).
    The same component renders in historical and **live** modes — *the live chart render
    (display-only epoch anchor) is verified with credentials during market hours; sim/historical
    are browser-verifiable.* *(No credentials for the sim leg.)*

- **J-49: Entry risk flags are computed at declaration and recorded**
  - Steps:
    1. Watch `SIM-BUYER` and let it run well past warm-up (an extended move); declare
       **trend_continuation / long**
    2. On a fresh watch, declare with an invalidation extremely close to the last
    3. Watch `SIM-CHOP`; declare any thesis
  - Acceptance: (1) fires **`chasing_entry`** — the recent directional impact already exceeds the
    config return threshold — shown as an amber chip with its measured margin in plain language;
    (2) fires **`invalidation_too_tight`** (distance < the config spread-multiple); (3) fires the
    liquidity flags (**`wide_spread_illiquid`** / **`low_trade_speed`**, reusing the classifier's
    own stability gates). Flags are **advisory** — creation always succeeds — and are frozen on
    the thesis, visible later in the journal and review. Declaring before warm-up fires
    **`before_warmup`**. *(No credentials; browser-verifiable.)*

- **J-50: Resolving a thesis is honest (played out / abandoned / expired)**
  - Steps:
    1. On a confirming `SIM-BUYER` thesis, click **Played out**
    2. Declare again; click **Abandon**
    3. Declare again (no entry mark) and let the bounded sim stream end
  - Acceptance: (1) resolves `played_out` and (2) `abandoned`, each recorded with logical + wall
    timestamps, the journal row appearing immediately and the strip returning to the declare
    affordance; (3) auto-resolves **`expired(stream_closed)`** with the final verdict frozen —
    never deleted, never upgraded to a user resolution. The UI offers ONLY played-out/abandon
    (the system owns `invalidated`/`expired`; requesting them via the API is a 422), and an
    entry-marked thesis offers no Abandon at all (J-52). *(No credentials; browser-verifiable.)*

- **J-51: The journal survives a backend restart; interrupted theses are handled honestly**
  - Steps:
    1. Create and resolve a thesis on `SIM-BUYER` (with a few verdict transitions)
    2. Declare a second thesis and leave it active without an entry mark
    3. Restart the backend; reload the UI and open `/journal`
  - Acceptance: the resolved thesis's row and full verdict timeline are **byte-identical** after
    the restart (append-only store, nothing recomputed at read); the previously-active unmarked
    thesis reads **`expired`** with an explicit interruption reason — never deleted, never still
    "active" over a fabricated gap, never backfilled; an entry-marked active thesis instead
    survives as active-but-not-evaluated per J-47. *(No credentials; browser-verifiable with an
    operator/harness-performed restart.)*

- **J-52: Mark your actual entry and exit (journaling, not execution)**
  - Steps:
    1. On a confirming `SIM-BUYER` **trend_continuation / long**, click **Mark entry** — the
       price field is prefilled with the current last; accept or edit; submit
    2. Later click **Mark exit** the same way; then resolve **Played out**
  - Acceptance: both marks are recorded **verbatim** (price + logical & wall time — never
    inferred, never a simulated fill) and appear on the strip, the chart (J-48), and the journal
    detail; once entry-marked the thesis no longer offers **Abandon** (resolve only); the
    realized move displays in **R units** (R = |entry − invalidation|) labeled as a journaled
    measurement with the spread-at-mark shown — never as currency P&L. With no marks, no realized
    metric is shown. *(No credentials; browser-verifiable.)*

- **J-53: Management stance while holding a position**
  - Steps:
    1. Watch `SIM-SHIFT`; during the control phase declare **trend_continuation / long** with the
       invalidation just below the late-control price (inside the coming chop band); **mark an
       entry** while confirming
    2. Watch the strip through the phase shift until the band prints through the invalidation
  - Acceptance: after the entry mark the strip switches to the **management stance**:
    **`thesis_intact`** while confirming → **`thesis_weakening`** with evidence as the verdict
    decays → **`thesis_invalidated`** when the invalidation prints (auto-resolve per J-44); live
    **distance-to-invalidation** ($ and R) and **open R** read in mono throughout; the copy
    states facts ("invalidation level traded") and never instructions ("exit now"). *(No
    credentials; browser-verifiable.)*

- **J-54: Objective execution checks suggest mistake tags**
  - Steps:
    1. Watch `SIM-REVERSAL`; declare **absorption_reversal / long** during the absorption phase
       and deliberately **mark an entry while the verdict is still `pending`**
    2. Let it confirm; mark an exit; resolve; open the review detail
  - Acceptance: the review shows machine-derived **execution checks** with evidence —
    `entered_before_confirmation` reads failed (entry timestamp < first confirming publish) and
    is **auto-suggested** as a mistake tag, pre-selected but editable (the user confirms; the
    system never tags on its own); the checks for chased-beyond-trigger (vs the `rule_first_true`
    price + threshold), exited-beyond-invalidation, and cut-confirming-early are likewise
    evaluated from recorded marks + the timeline only. *(No credentials; browser-verifiable.)*

- **J-55: Review compares expected vs actual behaviour**
  - Steps:
    1. Open a resolved thesis with transitions (e.g. J-40's) at `/journal/[id]`
  - Acceptance: the frozen expected-behaviour statements are listed with their final statuses
    beside the verdict timeline rendered at **true clock time** (epoch anchor), each transition
    carrying its evidence; entry risk flags, action marks, and execution checks are visible; the
    page renders **recorded values verbatim** — nothing is recomputed at read time, and the REST
    detail equals what was shown live. *(No credentials; browser-verifiable.)*

- **J-56: Outcome and process are graded on separate axes**
  - Steps:
    1. Produce a **clean-process invalidated** thesis: on `SIM-SHIFT`, declare
       **trend_continuation / long** early in the warm control phase (no flags), invalidation
       under the chop band — it invalidates in phase 2
    2. Produce a **flagged-process played-out** thesis: declare long on a long-extended
       `SIM-BUYER` (chase flag), let it confirm, resolve **Played out**
    3. Read both in the journal
  - Acceptance: (1) renders outcome **`thesis_failed`** × process **`clean`** — the "disciplined
    thesis, adverse tape" quadrant; (2) renders **`thesis_held`** × **`flagged`** — the "got away
    with it" quadrant. Both grades are enum labels derived from named, evidence-backed checks —
    never a numeric score; being invalidated is never itself a process failure. *(No
    credentials; browser-verifiable.)*

- **J-57: Mistake tags come from the backend taxonomy**
  - Steps:
    1. On any resolved thesis's review, open the tag picker; select tags (including `other`) and
       write a note; save
  - Acceptance: the picker lists exactly the backend taxonomy (`GET /research/taxonomy`) with its
    display copy — the frontend hardcodes no labels; `other` requires the note; saving persists
    tags + note and flips the thesis to **reviewed**; tags render identically everywhere they
    appear. *(No credentials; browser-verifiable.)*

- **J-58: Excursion outcomes are measured and honest**
  - Steps:
    1. Run J-42's confirming `SIM-BUYER` thesis (with an entry mark) to the scenario's end
    2. Open the journal detail and read the excursion section
  - Acceptance: for each configured horizon after the **first confirmation** — and separately
    after the **entry mark** (two populations, never pooled) — the max favorable and adverse
    excursions read in **R units** with the ternary outcome `+1R_first | −1R_first |
    neither_within_horizon`; **spread-at-mark** is recorded alongside; horizons cut short by the
    stream end are flagged **truncated**, never extrapolated; re-running the same seeded scenario
    reproduces identical numbers. *(No credentials; browser-verifiable; determinism asserted by a
    unit test.)*

- **J-59: Analytics aggregate honestly, segregated by feed and config**
  - Steps:
    1. Create a handful of resolved theses across setups and sims, including at least one
       abandoned
    2. Open the analytics view on `/journal`
  - Acceptance: per setup × direction the view shows **n with the abandonment bucket always
    visible**, the ternary excursion distribution, median time-to-confirm, tag frequencies, and
    the acted-trade R distribution **kept apart** from confirmation-anchored stats; **median
    spread / R** reads beside every +1R figure; groups under the config minimum sample read
    "insufficient sample" (n still shown) instead of bare percentages; rows are partitioned by
    `data_feed` and `config_fingerprint` — never pooled across either; no equity curve and no
    currency P&L appear anywhere. *(No credentials; browser-verifiable.)*

- **J-60: A replay study runs the setup grammar over a window — against a null baseline**
  - Steps:
    1. Open `/studies`; create a study: a symbol + past window (the committed reference window
       works), setup **absorption_reversal** (or trend_continuation), direction; run it
    2. Watch the job status; open the results when done; run the identical study again
  - Acceptance: the runner replays the window **unpaced** through a fresh engine, **auto-arms**
    occurrences per the state-native arming rule, and records per-occurrence verdict summaries +
    excursions; results show occurrence rows and aggregates **side-by-side with the seeded
    random-arm-time null baseline** (same window, direction, R definition, horizons — e.g.
    "setup: 8/13 `+1R_first`; random-time baseline: 41/100"); outcomes are ternary; the study is
    stamped with feed + config fingerprint; the identical re-run reproduces **identical**
    results. The page presents measurements with n and caveats — never an edge claim. *(The
    fixture-window leg runs in CI without credentials; an arbitrary-window study is verified with
    credentials.)*

- **J-61: Studies are honest about their limits**
  - Steps:
    1. Run a **level_break** study supplying a manual level on a single window
    2. Run a study whose window end truncates the horizons
    3. Start a long study and cancel it; separately observe a failing study (e.g. no data)
  - Acceptance: manual-level results carry a visible **`hindsight_level`** label ("level chosen
    with hindsight — illustrative") and are excluded from cross-study aggregates; truncated
    occurrences are flagged and counted separately — never silently dropped or extrapolated; the
    job shows queued/running progress, a cancelled study resolves to an explicit **cancelled**
    status (partial results clearly marked partial, never presented as complete), and a failed
    study surfaces an explicit error — never an empty "success". *(Browser-verifiable with the
    committed fixtures; cancellation covered by a test.)*

- **J-62: The reference study reproduces pinned results in CI (and the engine keeps up)**
  - Steps:
    1. (Automated; operator can re-run) Execute the committed reference study over the committed
       **moderate-density real SIP fixture** (≈10 minutes of real tape, sized for the configured
       horizons) and over the seeded sims
  - Acceptance: a committed test runs the study **unpaced in CI without credentials** and asserts
    the exact pinned occurrence rows + aggregates (byte-stable); the run completes within the
    **CI-gated time budget** — the engine-performance gate (capability 34): truly incremental
    feature maintenance, no per-event full-window rescans, with feature values byte-identical to
    before (or the change justified and re-pinned as its own iteration). The 7-second GME fixture
    remains the classification gate (J-36) and is NOT used for minute-horizon excursion claims.
    *(CI-gated by committed real data, per the J-36/J-37 standard.)*

- **J-63: The entry checklist renders live margins, not a naked signal**
  - Steps:
    1. Watch `SIM-REVERSAL`; declare **absorption_reversal / long** during the absorption phase
    2. Read the checklist before, at, and after the confirmation
  - Acceptance: each named check — verdict confirming; warm; `feed_live`; `tape_lag_ok`; spread
    within the stability domain; trade speed ≥ floor; invalidation distance ≥ spread multiple;
    not chasing (anchored at the **`rule_first_true`** price + config threshold) — renders its
    **live measured margin in its own units**, never a bare boolean; the stance reads
    **`conditions_not_met`** with the blocker list while pending, flips **`conditions_met`** only
    when every check passes after confirmation, and **`tape_against`** if the verdict turns
    rejecting; a **nearest-counterevidence** line names the closest condition that would flip the
    read; the stance publishes through its own dwell (no per-tick flapping); the copy is factual
    ("6/6 checks pass") — never imperative. *(No credentials; browser-verifiable.)*

- **J-64: Stance freshness — never a frozen green over a dead tape**
  - Steps:
    1. With a `conditions_met` checklist showing on a watched sim, click **Pause**
    2. Let a bounded sim stream end (**closed**)
    3. (Live leg) observe a live lull that crosses the stale gap
  - Acceptance: paused, closed, stale, and failed each force the stance to an explicit
    **`no_fresh_tape`** (the named `feed_live` / `tape_lag_ok` checks failing) — a previous green
    `conditions_met` never persists over non-live data; resume restores honest evaluation; the
    `delivery_lag_seconds` readout is visible and its bound is config-owned. *(Pause/closed legs:
    no credentials, browser-verifiable; the stale leg follows J-15's gated pattern.)*

- **J-65: Setup-forming hints are descriptive, gated, and logged**
  - Steps:
    1. Watch `SIM-BIDABS` with **no thesis**; wait past the configured sustain dwell and read the
       hint dock
    2. Click the hint's declare affordance
    3. Watch `SIM-CHOP` for at least the same duration
  - Acceptance: the hint card is **state-descriptive** ("bid absorption sustained 45 s — sellers
    being absorbed at the bid"), names the matching setup type as context, and contains **no
    imperative and no direction command**; it cites the user's own study baseline for that
    setup/feed when one exists, else exactly **"no studied baseline — unvalidated pattern"**; the
    declare affordance **prefills** the form (ticker, setup, direction) but the invalidation must
    still be typed — one click never creates a thesis; `SIM-CHOP`'s flapping produces **no hint**
    (sustain dwell + cooldown); every shown hint is **logged** (ticker, time, pattern, evidence,
    whether declared-from) and visible in the journal's hint log. *(No credentials;
    browser-verifiable.)*

- **J-66: Cue-discipline sweep — no imperative, no prediction, sound off by default**
  - Steps:
    1. Walk every research surface: the thesis strip across all verdicts and stances, hint cards,
       chart geometry labels, journal rows + detail, analytics, studies, and the taxonomy copy
  - Acceptance: no surface uses imperative trade language (buy / sell / enter / exit / "should" /
    targets) or prediction/certainty claims; verdict, stance, and hint copy is present-tense,
    descriptive, and thesis-attributed; the "Descriptive only — not trading advice" register
    appears on the research surfaces; the optional sound cue defaults **OFF**, fires only on
    stance/verdict transitions with a cooldown when enabled, and its toggle is explicit. *(No
    credentials; browser-verifiable; backed by a copy-lint test over UI strings.)*

- **J-67: The live-feed basis is always labeled (SIP research vs IEX live)**
  - Steps:
    1. Open **Live** mode and read the cockpit; declare a live thesis (with credentials) or
       inspect a stored live-bound thesis row
    2. Open the analytics view and read the partitioning
  - Acceptance: the live cockpit carries a visible feed badge ("live verdicts read the
    single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ");
    every thesis/hint/action/study row stores and displays its `data_feed`; no aggregate pools
    SIP with IEX rows; upgrading live to SIP remains a single config value (no relabeling code).
    *(Badge + stamps + partitioning: browser-verifiable without a feed; the live-declared row is
    verified with credentials.)*

- **J-68: The existing cockpit is unchanged (regression sentinel)**
  - Steps:
    1. With the research layer deployed but **no thesis declared**, run the J-01 – J-09 sim flows
       and spot-check J-17 (chart) and J-19 (pause/resume)
  - Acceptance: every pre-existing panel and flow behaves identically — the thesis strip idles as
    a single declare affordance and nothing else moves; an automated **equivalence test** replays
    a fixed event stream through the engine with research observers attached vs absent and
    asserts **byte-identical** snapshots (state, confidence, features, history); J-01 – J-37 all
    remain green in the session's journey history. *(No credentials; browser-verifiable +
    automated.)*

## Anti-goals

- **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and
  MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the
  tape. *(critical)*
- **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no
  fundamental analysis, no chart-pattern or indicator charting, no portfolio/position
  management — these belong to separate projects and MUST NOT be built here. The one allowed chart
  is the focused price candlestick + tape-state-marker overlay (simulated/historical), which adds
  **no** indicators, studies, or drawing tools. *(critical)*
- **Price impact over raw aggression.** The classifier MUST distinguish absorption from
  control: a tape with high one-sided aggression but no corresponding price progress MUST
  resolve to the matching absorption state (bid_absorption / ask_absorption), never to
  seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical)*
- **Honest uncertainty.** When evidence is weak or mixed, the spread is wide **relative to the
  instrument's price / typical spread**, or there is no clean price impact, the state MUST be
  `unclear` with low confidence. The system MUST NOT manufacture a directional call to look decisive.
  The "wide spread" and "clean price impact" tests MUST be judged **relative to the instrument's
  price level / recent volatility** (e.g. spread in basis points, impact as a return), never via a
  single absolute dollar constant calibrated for the simulator — so a genuine strong directional move
  on a real symbol with a proportionate spread reads as control, while a genuinely wide *relative*
  spread (or high aggression with no proportionate price progress) still reads `unclear` / absorption.
  The spread/impact tests MUST also account for the **selected feed** and for **trading halts**: a wide
  or **absent** *quoted* spread (a single-venue IEX quote, or suppressed/crossed quotes during an LULD
  halt) MUST NOT by itself veto a move that is otherwise clearly directional (strong one-sided ratio +
  real price impact + elevated speed) — there the spread acts as a **graded confidence factor, not an
  absolute veto**. Honest uncertainty applies to genuinely illiquid/mixed tape, never to a single-venue
  quoting artifact.
  *(critical)*
- **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state
  to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state
  and never a cockpit: a provider gap/feed lull → `stale`; an unknown/untradable symbol → an
  explicit error; an empty historical window → explicit no-data; a live watch while the market is
  closed → explicit closed (with the next open); missing credentials → explicit "unavailable".
  Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*
- **Single source of truth.** Tape state, confidence, and each feature MUST be computed
  exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and
  frontend MUST NOT recompute them. The same ticker MUST NOT show different values across
  views. *(critical)*
- **No magic numbers.** Every window length, threshold, large-print size, impact/absorption
  cutoff, and confidence boundary MUST come from config — no such literal in
  engine/classifier code.
- **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface
  (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed — live or
  historical — MUST NOT require engine or API changes. A concrete vendor SDK MUST appear in only
  one adapter module behind a vendor-neutral seam, so a second vendor is one new adapter; vendor
  specifics MUST NOT leak into the engine, providers, or API.
- **No secrets in source.** Real-vendor API keys/tokens MUST come only from environment/config and
  MUST NOT be committed; with no keys the app runs simulator-only and real modes report an explicit
  "unavailable" rather than failing opaquely or fabricating data.
- **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine
  MUST produce identical features, state, and confidence; classification MUST NOT depend on
  wall-clock time or randomness. Each simulated scenario MUST have an automated test asserting
  the expected state is reached with reasonable confidence.
- **No ML in v1.** The MVP classifier MUST be transparent rule/threshold logic over named
  features — no trained model in the first version.
- **No trade/profit claims.** The product MUST NOT claim profitability or present output as
  trading advice; tape state is descriptive, not prescriptive.
- **Honest side inference, not fabrication.** The aggressor side is a documented classification
  (quote rule, then a Lee-Ready **tick test** against the prior trade). This inference is legitimate
  and MUST be applied, but the engine MUST NOT force a guess when there is no quote **and** no prior
  trade — such a print stays `unknown`. Inferred side MUST NOT invent quotes or trades. *(critical)*
- **One focused chart, computed once.** OHLC bars and tape-state markers MUST be computed once in
  the engine history buffer and read identically by `…/history` and the chart; the UI MUST NOT
  recompute side, state, or price from raw data. An empty window MUST yield an **empty** chart, not
  invented candles. The chart is analysis-only — it MUST NOT add any order/execution affordance. The
  chart's **time axis shows true clock time** (real market time for historical; a synthetic session
  clock for simulated) via an **additive canonical epoch anchor** — the chart still recomputes no
  side/state/price, and the engine still bins on its deterministic logical timeline.
  *(critical)*
- **Honest pause.** Pause MUST freeze the displayed state without tearing the session down or
  fabricating data; while paused the UI MUST read as **paused**, never as live. On resume, **live**
  MUST rejoin current real data — the engine MUST NOT synthesize trades to "catch up" the gap.
  *(critical)*
- **Timezone-correct windows.** A historical window MUST be fetched for the exact instant the user
  selected in their local time — no silent UTC reinterpretation that shifts the window by the local
  offset; all market/session times shown to the user MUST carry an explicit zone label. *(critical)*
- **No silent dead-clicks.** Pressing Watch MUST always produce a visible UI change within ~1 second —
  a pending/"connecting" state, streaming data, an empty-state, an explicit error, or an inline
  validation message. The UI MUST NOT silently remain on the idle/previous screen, MUST NOT leave
  "Connecting…" running with no resolution, and MUST NOT swallow a failure (no empty `catch`, no
  unawaited promise that drops an error, no unbounded external wait). A reproducible silent no-op, an
  infinite connecting spinner, or a swallowed Watch error is a veto on GOAL_ACHIEVED. *(critical)*
- **No mute cockpit, no silent return to idle.** A valid Watch MUST resolve to a non-idle terminal
  state and MUST NOT silently return to or remain on the idle/previous screen. A watched cockpit MUST
  NOT present a confident **live** status over an empty tape, nor render blank panels indefinitely with
  no explanation. Connected-but-no-data MUST read as an explicit connecting/waiting or honest
  empty-state and MUST resolve, within a bounded configured time, to streaming data or an explicit
  honest state (**stale** / **closed** / no-data / market-closed / unavailable / error) — owned once by
  the engine's `stream_status`. A cold-start/empty snapshot MUST NOT be treated as a settled connection
  that disables the failure/empty-resolution path; a feeder failure MUST be logged and surfaced, never
  swallowed. A reproducible Watch that returns to idle, or an indefinitely-empty cockpit, in any mode
  (including off-hours), is a veto on GOAL_ACHIEVED. *(critical)*
- **Bounded, honest, performant vendor calls.** Every vendor-gated Watch MUST be bounded by a **real
  call-level deadline** (an HTTP/SDK timeout), not only an async wrapper a blocking/large-response call
  can defeat, and the backend's bound MUST be **shorter than the frontend client timeout** so the user
  always sees the backend's honest error, never a client-side give-up. Interactive vendor paths MUST be
  **fast by design, not by lengthening timeouts**: a legitimate high-volume window MUST load within
  budget via an optimized fetch (concurrent trades/quotes, **chunked sub-window fetch with bounded
  concurrency for long windows up to a full trading day**, no needless pre-flight, cached/reused
  windows, prompt warm-up), and **symbol search MUST NOT re-fetch the whole asset universe per
  keystroke** (a warmed/cached universe, cancelled stale requests, a sensible min-query). Any
  timeout/oversize error MUST be **actionable for the real cause** (e.g. "shorten the window"), never a
  misleading "try again"; and every performance optimization MUST preserve correctness — **no fabricated
  or dropped trades/quotes, no recomputation outside the engine** (single source of truth holds).
  For a long window, "fast by design" MUST mean **time-to-first-data is decoupled from total-window
  load** — the first chunk begins the replay within budget while later chunks stream in the background —
  not merely parallelizing a fetch that still completes entirely before responding; the "shorter range"
  message is a true last-resort backstop only.
  *(critical)*
- **Real-data journeys are proven with real data.** A journey whose outcome depends on real market data
  (classification of a real move, real-window loading) is NOT done until an **automated test over
  committed, real captured market data** asserts the outcome and runs in CI **without** live credentials.
  A synthetic/hand-tuned fixture and an "operator-gated" manual check are necessary-but-**insufficient** —
  they MUST NOT be the sole evidence for GOAL_ACHIEVED. This rule exists because the iter-13 J-33/J-34
  "pass" was synthetic-only and shipped two real-data defects. *(critical)*

The research evolution adds the following anti-goals (the existing ones above all still hold):

- **No unsolicited or unconditional trade commands.** Every actionable cue MUST be gated on a
  user-declared thesis with an invalidation, rendered as named checks with margins and evidence,
  in present-tense descriptive language. No imperative buy/sell/enter/exit wording, no price
  targets, no certainty language — anywhere. A hint is a logged description of a forming pattern,
  never a command and never a thesis by itself. *(critical)*
- **Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built
  before the journal, excursion outcomes, and replay studies exist and their journeys
  (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state
  exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is
  a defect. *(critical)*
- **No profitability or edge claims.** No currency P&L, equity curves, compounding, or
  win-rate-as-edge presentation anywhere. R statistics are journaled measurements and MUST always
  appear with their n, the abandonment bucket, the null baseline (where one applies), and the
  spread/R cost figure. *(critical)*
- **No prediction language.** A verdict or stance describes what the tape is doing **now**
  relative to the declared thesis — never a forecast of what price will do. *(critical)*
- **No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and
  grade MUST carry plain-language evidence derived from canonical engine values. A verdict
  without evidence is a defect. *(critical)*
- **Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated,
  or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart,
  stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated
  outcome; action marks are recorded exactly as the user stated them — never inferred fills.
  Abandoned theses remain visible in every denominator (no survivorship pruning), and an
  entry-marked thesis can never be abandoned. *(critical)*
- **The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or
  feature state or outputs: the same event stream yields **byte-identical** tape
  state/confidence/features/history with or without an active thesis or attached observers
  (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed.
  *(critical)*
- **Source, feed, and config honesty.** Every research record MUST be stamped with its bound
  source, its `data_feed`, and a `config_fingerprint` over the entire frozen config; a thesis
  MUST never be evaluated against a different source than it was declared on; analytics and
  studies MUST NOT pool across feeds or fingerprints; and SIP-derived research MUST NOT be
  presented as validating IEX-live behaviour without the explicit basis label. *(critical)*
- **No scanning, no execution — still.** Theses and hints exist only on the one watched ticker;
  studies run only over explicitly chosen windows; there is no background or multi-symbol setup
  detection, and (re-affirming the first anti-goal) no order placement, routing, simulation of
  fills, or broker integration.
- **No new indicators, no auto-tuning.** Confirmation rules, stances, hints, and studies MUST be
  composed from the EXISTING engine features and states only; research thresholds are config-owned
  research defaults calibrated against the sims/fixtures; no parameter optimizer, grid search, or
  automatic threshold fitting of any kind. *(critical)*
- **Persistence stays scoped to research records.** SQLite holds theses, verdict events, hints,
  actions, reviews, and study results only — no trades, quotes, candles, or feature series are
  persisted (committed test fixtures excepted).
