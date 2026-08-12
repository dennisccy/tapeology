# Tapeology — Project Goal (Era B2: The Playbook — the book's intraday setups, detected on the desk's own bars and measured forward)

> Eras 1–5D and Era B are the **foundation** of this goal. Eras 1–2 (tape reading + the research
> evolution, GOAL_ACHIEVED) are archived at
> [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md); the structure-UI
> interlude at [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md);
> **Era 5 "The Library"** at [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md);
> the **"Fast Wall" interlude** at [`docs/goal-archive/goal-2026-07-17.md`](goal-archive/goal-2026-07-17.md);
> the **"Clean Slate" demolition** at [`docs/goal-archive/goal-2026-07-25.md`](goal-archive/goal-2026-07-25.md);
> and **Era B "The Desk" (GOAL_ACHIEVED 2026-07-31, session `desk`, journeys J-01–J-21)** at
> [`docs/goal-archive/goal-2026-08-10.md`](goal-archive/goal-2026-08-10.md). Eras 3, 4, 5B, and 5C
> are frozen foundation; their records live in git history and `reports/goal-session-*-delivered.md`.
>
> **This chapter is Era B2 of the operator's pivot (A Demolition → B Desk → B2 Playbook → C
> Annotator).** The product today is exactly **Cockpit (`/`) + Structure (`/structure`) + Desk
> (`/desk`)**, the fingerprint epoch is `08e471b10130e1e2`, the MCP surface is **18 read-only
> tools**, and the honesty machinery (stores, gates, registry, PnL promotion ledger) is fully
> intact. B2 is a BUILDING era on the desk's ground: it teaches the desk the intraday setups of
> the book the project is named for — Graifer & Schumacher, *Techniques of Tape Reading* (2004) —
> detected on the desk's own recorded 5m/1m bars and measured with the desk's own forward-return
> + max-drawdown conventions. It is an operator-directed product era OUTSIDE the research catalog
> ([`docs/research-directions.md`](research-directions.md) has no Playbook card; per its §5.6 this
> file wins for the running era). The statistics program (era-6 "The Referee") and the annotation
> corpus (Era C) remain SEPARATE future chapters — nothing of them lands here.
>
> **Unlike Era B, this era DOES add new research math** — a family of pre-registered bar-pattern
> detectors and their trigger-anchored measurements — under two hard disciplines: (1) every
> detector rule and threshold is fixed in advance in
> [`docs/playbook-detector-spec.md`](playbook-detector-spec.md) (the canonical spec; developers
> implement from it, never re-derive or re-tune — a threshold change is a named revision that
> re-keys future records, never a sweep); (2) every measurement reuses the desk forward rail's
> own conventions verbatim. It adds **zero statistics gates** and **zero annotation surfaces**.

## Vision

Era B gave the operator a desk: universe in, wall-screen briefing out, every record append-only
and evaluable. But the desk still reads only structure — it knows where the walls are, not what
the tape is DOING. The book this project is named for describes exactly that missing layer: an
intraday grammar of price/volume behavior (six principles, a handful of named setups) that has
never been encoded, let alone measured. Era B2 builds it as evidence, not advice:

1. **A pre-registered playbook of the book's intraday setups.** For any recorded session, a
   detector family — open-high/open-low-break, jump-base-explosion (JBE) / drop-base-implosion
   (DBI), capitulation (+ euphoria marker), cup-and-handle, range trades, double top/bottom —
   walks each member's RTH 5m bars (1m bars for the opening range) and emits signals:
   `{symbol, setup_id, side, trigger price/time, invalidation_price, geometry, volume character,
   market context, principles}`. Formation logic is lookahead-clean at bar granularity; every
   threshold is a named constant from the canonical spec, tagged BOOK or ADAPTATION.
2. **Every signal measured the desk's own way.** Each signal carries a trigger-anchored
   measurement produced by the SAME conventions as the desk forward rail: horizons +1m/+5m/+1h/
   +4h/to-close as trading-bar counts on the session's finest series, side-signed returns, dual
   max drawdown clamped ≤ 0, truncation honesty, and a seeded random-anchor baseline of the same
   session — plus an `invalidation_breached` disclosure (did price trade through the book's
   structural level; returns are never stop-adjusted).
3. **A back-scan that turns the book into a ledger.** One resumable operator act walks EVERY
   recorded session with 5m coverage (~45 sessions × ~101 members at authoring; the store is
   append-only so this grows daily), recording one append-only playbook record per
   (session date, input signature) — reusing recorded work on re-run, chunked by session,
   host-guard-confined.
4. **An evidence view that says what happened, with n.** Per setup × side × horizon: the pooled
   forward-return and MDD distributions of every recorded signal beside the pooled baseline
   anchors — median/quartiles/mean, `n`, `n_truncated`, `n_baseline`, low-n tags below a named
   disclosure floor. Descriptive distribution language only; no probability, expectancy, edge,
   or significance claims — those gates are era-6's.

The deliverable: the desk learns to read the tape the way the book teaches, writes down every
signal it would have seen, measures what price then did against chance anchors, and shows the
distributions honestly — every number owned once, every run explicit, every record append-only.

## Target Users

- The project owner (a discretionary intraday trader) who opens `/desk`, runs the playbook for a
  session, reads the signals beside the wall briefing, and reads the evidence table to learn
  which of the book's setups his own data supports.
- The same owner operating through **Claude + MCP**: `desk_playbook` / `desk_playbook_evidence`
  (plus the existing 18 tools) make the playbook readable from a conversation end to end.
- AI dev-chain agents (the goal-mode chain) building and browser-verifying the era.

## Foundation invariants (still law — eras 1–5D and B)

The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md))
remains binding on all KEPT code — price-impact-over-aggression; honest uncertainty; **no
fabricated data**; single source of truth; no magic numbers; provider-agnostic engine;
deterministic & reproducible; no secrets in source; research read-only over the engine; record
integrity; source/feed/`config_fingerprint` honesty. The surface inventory is the post-Era-B
one: `/`, `/structure`, and `/desk` (this era adds sections to `/desk`, no new route).

1. The **tape engine** (`app/engine/`) emits byte-identical output under `default` on identical
   inputs. `config_fingerprint` stays **`08e471b10130e1e2`** for this WHOLE era. This era needs
   **zero new `Config` fields** (the `desk_forward` precedent: playbook thresholds are module
   constants hashed into the record's own input signature); if the build genuinely needs one, it
   takes §0.4 **Path A** (exclusion + stability test + counter-test) — a pin movement is a
   defect, full stop.
2. The **research computations** — `levels.py`, `tradability.py` (+cache), `setups.py` (+scan
   cache), `edge_report*.py`, `backtests.py`, the strategy registry, `profiles.py` (`default`),
   the champion pointer — stay behaviorally byte-identical. The playbook READS bars; it never
   touches, re-implements, or re-tunes any of them.
3. The **stores** — `BarStore` + `DatasetStore` formats, checksums, append-only immutability,
   split freezing, the durable accelerator DBs, the Era-B universe/screen/forward stores and
   their run ledgers — are untouched in format and discipline. The era ADDS a playbook store
   (and its run ledgers + a derived evidence projection cache) under the same discipline.
4. The **PnL promotion ledger** stays append-only and intact; the champion pointer does not move.
5. The **kept surfaces as shipped**: the cockpit, `/structure`, and every shipped `/desk`
   section (screen history calendar, forward returns, refresh chain + compute controls, ranked
   briefing, skipped members, runs/pins/compare/provenance sections) keep working exactly as
   shipped. The playbook lands as NEW sections below the shipped ones; no shipped `/desk`
   section, column, or behavior changes.
6. The **read-only MCP server** keeps its byte-identical GET-proxy contract; this era adds two
   GET-proxy tools (**18 → 20**) and never adds writes.

### OWNER RATIFICATION — carried and new

**R-1 (2026-07-27, price-less-bar repair)** — ratified in Era B (see the archived goal's R-1
block for the eight-file inventory); it remains ratified history and its terms carry forward
unchanged.

**R-2 (2026-08-10, the post-Era-B forward-test interlude) — ratified and IN INVENTORY for this
era.** Between Era B's GOAL_ACHIEVED (iteration 36, commit `94eb1b0`) and this era's opening,
the operator's interactive sessions landed a body of desk work no Era-B journey describes. It is
ratified as foundation, comprising the `goal/desk` commits after `94eb1b0` through the era-open
tip (including the operator's pre-era commit of the 2026-08-07/09 working tree — 14 modified
files + `desk_meta_cache.py`/`test_desk_meta_cache.py`; iteration 0 records the era-open SHA):

- `app/research/desk_forward.py` + `desk_forward_compute.py` + `desk_forward_log.py` +
  `desk_forward_pins.py` — the touch-anchored forward-return v2 rail (horizons/dual-MDD/seeded
  baseline/2-pin append-only `ForwardStore`) and its manager, ledger, and pins;
- `app/research/desk_sessions.py` — recorded-session honesty (screen only real sessions);
- `app/research/desk_screen_decision.py` + `desk_screen_cleanup.py` — one-snapshot-per-date
  reuse/record/replace semantics and the operator cleanup path;
- `app/research/desk_deep_backfill.py` — the chunked, resumable fine-bar (1m/5m) deep-backfill
  quartet and its Alpaca vendor seam;
- `app/research/desk_meta_cache.py` — the derived, rebuildable screen/forward meta-projection
  cache (stat-keyed, owns nothing);
- the desk refresh/screen/forward performance work, the ET time convention on desk surfaces, and
  the fine-timeframe top-up walk (`DESK_TOPUP_FINE_TIMEFRAMES`).

Where clauses below say "untouched", "byte-unmodified", or "out-of-inventory", they are read
subject to **R-1** and **R-2**.

**R-3 (2026-08-11, the playbook spec rulings) — ratified.** Iterations 6–9 surfaced two open
"The spec is canonical" items and halted the session STALLED awaiting them. Both are ruled here.
This block is the ruling; the spec edits it directs are iteration-10 developer work (the same
shape as iteration 6's §3.5 doc-only closure), not a licence to change detector behavior beyond
what is named below.

**R-3.1 — the `range_trade` "degenerate trigger reference" clause is RATIFIED as written.**
The dated clarification in `docs/playbook-detector-spec.md` §3.7 Edge cases, and the matching
fail-closed void in `_range_trade_side` (`T ≤ SL` long / `T ≥ SH` short emits nothing and the walk
continues), stand as canonical. It is ratified on its merits: narrowing-only, no new constant,
`playbook_input_signature` unmoved, pinned by long- and short-side tests whose controls differ in
exactly one number, and it prevents a real defect — a long recorded with its own invalidation
ABOVE its entry. Two corrections to the record it was justified on: the "no recorded record
contains a `range_trade` signal" premise is now stale (87 real `range_trade` signals sit in four
append-only records under signature `16a2734d10c91ea7`, all written after the void was in force,
so none is born-invalidated), and dropping the setup would therefore also move the signature and
orphan them. `range_trade` stays in `PLAYBOOK_SETUPS`; J-06 ships unchanged.
The Constraints clause below is NOT relaxed: a developer who finds the spec ambiguous still drops
and surfaces rather than improvising. This ruling is a decision on one instance, not a standing
permission — the next such clause needs its own ratification.

**R-3.2 — the shipped narrower-than-spec readings are ACCEPTED as canonical, with one
completion.** Each was disclosed by an audit, each is deterministic, and iteration 10 writes each
into the spec so code and rulebook agree. Where the spec and the shipped code differ, the spec
is edited to match the code — no detector logic changes — EXCEPT R-3.2(b), which adds a
disclosure:

- **(a) `double_top`/`double_bottom` pair selection.** §3.8's Caps line ("the first valid valley
  break") is rewritten to the shipped reading: the first pivot pair, in chronological
  `(p1, p2)` order, whose full formation validates AND triggers; mirrored in §3.9. This is a
  choice among valid formations, not a wrong one, and 155 recorded signals ride it. Recorded
  under this reading, they remain canonical. If the back-scan's forward distributions later give
  cause to prefer the earliest valley break, that is a NAMED revision — it adds a discipline key
  to `playbook_parameters()` so the signature re-keys and old records are kept beside the new,
  never a silent logic swap under the same key.
- **(b) `crossed_midrange` — accepted AND completed.** The shipped boolean answers only §3.7's
  first half (did price cross the range midpoint on the approach). §3.7 is split so that half is
  named exactly, and the missing half — whether the prior swing TURNED at midrange (the BOOK
  midrange rule) — ships as a SECOND served disclosure field on `range_trade` geometry, with its
  `/desk` chip. Binding constraints: spec-first (the mechanical definition is written into §3.7
  before any code); disclosure-only (it may never gate, suppress, or create a signal); and it
  MUST reuse an already pre-registered constant for any tolerance it needs — minting a new
  constant would move `playbook_input_signature` for a disclosure, which this ruling does not
  authorize. The field is optional in the served payload and in `types.ts`, so the 87 already
  recorded `range_trade` signals stay honest by lacking it rather than being backfilled. If the
  second half genuinely cannot be defined without a new constant, DROP it and surface that —
  do not mint one.
- **(c) the BOOK 1.5× jump-to-base ratio is inert, and the spec must say so.** Both §3.3 gates
  are implemented verbatim, but `PLAYBOOK_JUMP_MIN_MULT · PLAYBOOK_BASE_MAX_RANGE_MBR`
  (1.5 × 2.0) equals `PLAYBOOK_JUMP_MIN_MOVE_MBR` (3.0), so the ADAPTATION floor always binds
  first and the BOOK ratio can never reject a formation on its own (min observed ratio across the
  32 recorded `jbe`/`dbi` signals: 1.735). No number moves — moving one to "activate" the gate
  would be threshold fitting, which stays barred. §3.3 and the `PLAYBOOK_JUMP_MIN_MULT` row of
  the constants table record the inertness plainly so the back-scan never credits a gate that has
  never bound.
- **(d) the cup rim constant.** §3.6 names `PLAYBOOK_RIM_MATCH_MBR` for the left rim's
  "within X of session-high-so-far" test, while the code reads `PLAYBOOK_NEAR_EXTREME_MBR` there
  (the rim-to-rim test correctly uses `RIM_MATCH_MBR`). Both are 1.0, so there is no behavioral
  difference on any input and `cup_handle` has never fired. §3.6 is edited to name
  `PLAYBOOK_NEAR_EXTREME_MBR` for the session-high test; the detector is NOT touched. This closes
  the latent trap where a future revision of `RIM_MATCH_MBR` would silently miss that gate.
- **(e) the `range_trade` trigger anchor — folded in here because it was never tracked.** The
  iteration-6 audit's finding B4 (§3.7 anchors the bounce scan on "a bar `b` touches the low
  zone", while `_range_trade_side` anchors only on the arming-completing touch) is the same
  species as (a)–(d) but never reached the owner-rulings list. It is ruled with them: §3.7's
  Trigger clause is narrowed to the arming-completing touch, matching the shipped code. It is
  fail-closed (fewer signals, never invented ones). It is named here so it cannot resurface after
  these items close.

**R-3.3 — iteration 10 is the era-closing pass.** Its scope is R-3.2's spec catch-up edits, the
R-3.2(b) disclosure field, and the iteration-9 evaluator's carried clean-up items: rewrite
`J-10.json`'s step 6 to assert a stable piece of shipped page furniture instead of a signature
hash that changes whenever the fixture rig is rebuilt; re-take one `/structure` capture on data
that actually has price bars; and run the pass at FULL depth with the auditor, which four
iteration specs asked for and the depth arbiter demoted each time. The operator restored `:8301`
to the real store before this resume. `Config().config_fingerprint()` stays `08e471b10130e1e2`
and `playbook_input_signature` does not move.

## Success Criteria

In priority order — kept-value integrity outranks new-surface completeness outranks convenience:

1. **Nothing kept regresses.** Full backend suite green (1926 pass / 8 skip at authoring —
   iteration 0 records the era-open count; grows, never shrinks); engine equivalence proves
   byte-identical `default` outputs; `Config().config_fingerprint()` prints `08e471b10130e1e2`
   every iteration; every kept `/`, `/structure`, and `/desk` behavior browser-verified as
   shipped; every guard test passes extended-not-edited (subject to R-1/R-2).
2. **Detection is pre-registered and lookahead-clean.** Every signal is a pure function of bars
   at or before its trigger bar plus prior-session baselines, under the named constant set of
   [`docs/playbook-detector-spec.md`](playbook-detector-spec.md); the truncation property test
   proves it per detector; no code path anywhere iterates thresholds against outcomes.
3. **Measurement is the desk's own.** Convention identity with the forward rail is proven by
   test (same horizons, sign discipline, dual-MDD semantics, truncation, seed recipe); the
   playbook embeds the rail's shape constants in its own parameters so a rail change re-keys
   playbook records instead of silently reinterpreting them.
4. **The ledger is append-only and evaluable.** One record per (session date, input signature);
   identical pins reproduce byte-identical content or reuse honestly; nothing is backfilled,
   rewritten, or recomputed in place; absences (no bars, thin baseline, no SPY) are disclosed
   rows, never guesses.
5. **The playbook is a real `/desk` surface.** Signals, back-scan, and evidence sections render
   with honest empty states, live progress, and full provenance — all browser-verified with
   screenshots (DOM-content reveals only; no journey requires native-tooltip photography).
6. **The playbook is Claude-operable.** `desk_playbook` and `desk_playbook_evidence` are
   byte-identical GET proxies; the MCP suite proves the 20-tool contract.

## Key Capabilities

1. **Detector family + primitives (new research math, pre-registered).** A lean primitives
   module (RTH session slice, opening range with `1m→5m` honest degradation, prior-20-session
   MBR + per-slot volume medians, strict swing pivots, consolidation-range finder, vertical-move
   detector, zone touches, market context) and the nine detectors + euphoria marker of the
   canonical spec — all thresholds from the spec's single constants table, every vagueness in
   the book resolved as ONE named, cited adaptation.
2. **Trigger-anchored measurement on the desk's rail.** Signals measured by the forward rail's
   own `_measure_from` at the trigger bar on the session's finest series; per-signal
   `invalidation_breached` computed in the same pass OUTSIDE the rail helper; per (symbol,
   setup) seeded baseline anchors with the rail's seed discipline; caps + beyond-cap disclosure.
3. **One compute, one store.** `compute_playbook(session_date)` detects + measures in one walk
   and records ONE frozen, checksummed, append-only record keyed
   `(session_date, playbook_input_signature)` — the signature hashes the fine-series tuples of
   members ∪ {SPY}, the `config_fingerprint`, and the FULL parameters blob (thresholds, setup
   list, measurement shape), so a logic change mints new versions and can never silently reuse
   or rewrite old ones. Compute manager trio + CLI + durable run ledger per the desk pattern;
   `refuse_if_not_a_session` guards every compute path.
4. **The back-scan.** `GET .../backscan/plan` (pure, metadata-only: recorded session dates ×
   recorded-at-current-signature) and a resumable compute trio walking planned dates through the
   ONE shared `run_playbook_and_record` entry point — per-date outcomes
   `reused/recorded/refused_non_session/failed`, cancel on a date boundary, durable back-scan
   ledger, host-guard-confined.
5. **The evidence view.** `GET /research/desk/playbook/evidence` folds the newest record per
   date AT ONE SIGNATURE into per-(setup, side) × measure distribution cells (median/p25/p75/
   mean, `n`, `n_truncated`, `n_baseline`, `below_min_n` tags, `invalidation_breached` counts)
   beside the pooled baseline — computed on read via a stat-keyed derived projection cache
   (the meta-cache contract), never a snapshot store; other signatures listed, never pooled.
6. **`/desk` playbook sections + MCP contract v4 (20 tools).** Playbook Signals (per-session
   signal table + Run Playbook + provenance), Backscan (plan preview + trigger + progress +
   runs), Playbook Evidence (the distribution table) — rendered BELOW the shipped sections;
   `desk_playbook` + `desk_playbook_evidence` in `_STATIC_PATHS`; `get_endpoint`'s `/research/`
   allowlist already reaches the parameterized reads.

## Non-Goals

- **No trading, no advice, no sizing.** A signal is a recorded observation. `invalidation_price`
  is the book's structural level as a geometry disclosure — never a stop order, size, R-multiple,
  or account concept; measured returns are never stop-adjusted (stated in the served register).
- **No statistics program.** No CIs, p-values, nulls beyond the shipped seeded baseline, no
  multiple-testing control, no gates, no edge/probability/expectancy language — era-6 "The
  Referee". The min-n floor DISCLOSES (tags cells); it never filters or suppresses.
- **No threshold fitting.** No sweep, grid, or outcome-driven iteration over detector constants
  anywhere, ever (`docs/research-directions.md` DO-NOT #5). A mis-scaled constant is fixed by a
  named revision in the spec + code (new signature, old records kept), never tuned.
- **No annotation layer** (Era C). The playbook records machine output only; zero manual-input
  write paths.
- **No tick-data dependence.** Detection and measurement read stored 5m/1m bars only;
  `datasets`, the engine, and the backtest/edge-report rail are untouched.
- **No new vendor, no new symbols beyond SPY freshness.** SPY 5m/1m bars are already frozen in
  the store; the only fetch-path change is keeping SPY fresh through the existing top-up walk.
  `^OEX` is not fetched; no options/sentiment/news data; no paid services.
- **No wall-screen or kept-surface work.** `desk_screen*` computation, the ranked briefing, the
  forward rail's own behavior, cockpit, `/structure` — all as shipped. The playbook IMPORTS the
  rail's helpers; it takes a ZERO diff to `desk_forward.py` itself.
- **No scheduling.** Every compute is an explicit operator act; page-load GETs never compute.
- **No fingerprint epoch bump.** Zero new Config fields expected; Path A if one is unavoidable;
  the pin `08e471b10130e1e2` does not move.

## Constraints

- **Stack (carried over):** Next.js 15 + TypeScript + Tailwind v3, dark-only;
  Python 3.12 + FastAPI; backend `:8000`, frontend `:3000` (browser-QA rig `:8301`/`:3301`);
  no new runtime dependency (detectors are plain Python over `merged_bars`).
- **The spec is canonical.** Formation/trigger/invalidation logic and every constant come from
  [`docs/playbook-detector-spec.md`](playbook-detector-spec.md). A developer who finds the spec
  ambiguous or unimplementable for a detector DROPS that detector from the iteration, records
  the drop, and surfaces it for an owner ruling — never improvises a rule (the spec's
  range_trade is already marked PROVISIONAL for exactly this reason).
- **Parameters discipline (the `desk_forward` pattern, applied at birth):**
  `playbook_parameters()` reads every constant at call time and embeds the rail's horizon/
  measure/seed constants; `compute_playbook_input_signature` hashes sorted
  `(symbol, timeframe, series_id, checksum)` tuples for (members ∪ {SPY}) × `("1m","5m")` +
  `config_fingerprint` + the canonical parameters blob (`sha256[:16]`, metadata-only via
  `list(include_bars=False)`). The parameters blob is embedded verbatim in every payload
  (provenance duty). A monkeypatched constant must move the parameters AND the signature
  (counter-tested).
- **Store discipline:** frozen, checksummed, append-only JSON records; record id = pure
  function of the 2-pin key; duplicate key raises; a corrupt file at a key's path is surfaced,
  never overwritten; NO supersede/prune path exists in v1 (versions kept and counted;
  `newest_for_date` + `versions` served). Storage dirs are env-var-or-sibling defaults
  (`TAPEOLOGY_DESK_PLAYBOOK_DIR`, `_LOG_DIR`, `_BACKSCAN_LOG_DIR` — deliberately NOT Config
  fields). The evidence projection cache follows the `desk_meta_cache` contract: derived,
  stat-keyed, rebuildable, owns nothing, unopenable = missing optimisation never a failed read.
- **Lookahead law (bar granularity):** formation conditions read bars strictly before the
  trigger bar (pivots wait out their confirmation window; fail-closed); the trigger predicate
  uses only the price-crossing fact; trigger-bar volume/close are disclosures, never gates;
  baselines are prior-sessions-only; market context reads SPY strictly before the trigger
  epoch. The generic truncation property test (truncate the series after the trigger; mutate
  post-trigger bars) covers every detector and every fixture.
- **Session honesty:** every compute path calls `desk_sessions.refuse_if_not_a_session`
  (`app/research/desk_sessions.py:180`); the back-scan planner draws only from
  `recorded_session_dates` (:129); a session with no 5m bars, MBR = 0, or a thin baseline is a
  disclosed absence, never a guess and never a crash.
- **Measurement convention identity:** the playbook imports the rail's helpers
  (`_session_slice` :295, `_measure_from` :451, `_draw_anchor_indices` :428, the averaging
  helpers) rather than copying them; a convention-identity test proves a synthetic anchor
  measures byte-identically through both paths; `invalidation_breached` is computed OUTSIDE
  `_measure_from` so the rail's served shape never changes and no recorded forward record
  re-keys.
- **Copy discipline:** all playbook copy is descriptive measurement; the served
  `PLAYBOOK_REGISTER` and `EVIDENCE_REGISTER` sentences state what was measured and what was
  NOT (no fills, no costs, returns not stop-adjusted, baseline = seeded random anchors);
  `tests/test_copy_discipline.py` covers the new page copy and registers unmodified.
- **Guard tests are extended, never edited:** `tests/test_desk_ui_guards.py`'s
  `_PRICE_ARITHMETIC_FIELDS` (:152) gains every new served numeric the UI renders (+ seeded
  counter-test additions); `tests/test_desk_refresh_chain_guard.py`'s
  `_EXPECTED_EFFECT_COUNT = 15` (:104) is re-derived deliberately with the mandatory rationale
  paragraph and `_TRIGGER_CALLS` additions; `test_no_execution_path.py`,
  `test_no_credential_in_artifacts.py`, the chart guards, and the 13 pin assertions pass
  byte-unmodified.
- **Hermetic tests:** keyless on committed fixtures (synthetic bar sessions per detector:
  one canonical firing fixture + one near-miss that must NOT fire); no test fetches the
  network; the real back-scan is an operator-run act reported run-or-not-run, never a CI gate.
- **Browser evidence:** `rm -rf apps/frontend/.next` + rebuild before any browser pass (T-9);
  every browser acceptance needs a screenshot — none ⇒ `unknown`, never `passing` (T-10); all
  playbook UI acceptance uses DOM-content reveals only — no native `title` tooltips required
  by any journey (the T-10a rig stays available but unneeded).
- **Compute-manager reuse:** the playbook compute and back-scan follow the shipped desk
  manager pattern (single-flight, snapshot-pollable progress, cancel, CLI-runnable, one shared
  `run_*_and_record` writer, terminal-state-only ledger writes); page-load GETs never trigger
  computes.

## Design Direction

Unchanged house style: dark-only, dense, professional, terminal-grade; honest empty/degraded
states are first-class copy (`"Playbook not computed for this session."`,
`"no signals: baseline too thin"`); the signals table reads like a session log, not a
recommendation feed; setup names are the book's own; no marketing chrome.

## Product Shape

Nav unchanged: **Cockpit `/` · Structure `/structure` · Desk `/desk`** (`app/meta.py`
`UI_ROUTES` untouched). The playbook adds three sections to `/desk`, rendered BELOW the shipped
sections.

**Data Contract — new rows (each value computed once, one owner):**

| Value | Owner (module) | Serving endpoint |
|---|---|---|
| Playbook records (signals + measurements + baseline + summary) | new `app/research/desk_playbook.py` | `GET /research/desk/playbook` (`?date=`, `?id=`) |
| Playbook compute progress | new playbook compute manager | `POST/GET/POST-cancel /research/desk/playbook/compute` |
| Playbook run ledger | new `app/research/desk_playbook_log.py` | `GET /research/desk/playbook/runs` |
| Back-scan plan | new `app/research/desk_playbook_backscan.py` | `GET /research/desk/playbook/backscan/plan` |
| Back-scan progress + ledger | same back-scan module | `POST/GET/POST-cancel .../backscan/compute`, `GET .../backscan/runs` |
| Evidence aggregates | new `app/research/desk_playbook_evidence.py` | `GET /research/desk/playbook/evidence` |

**Unchanged owners (the playbook reads them verbatim):** bars/candles → `bars.py`
(`merged_bars` :883) + `bar_index`; session honesty → `desk_sessions.py`; measurement helpers →
`desk_forward.py` (imported, zero diff); universe membership → `desk_universe.py`; everything
else exactly as the archived Era-B contract lists.

## Build anchors & weak-model traps (era B2)

Anchors verified against the `goal/desk` working tree at authoring (2026-08-10) — **re-locate by
symbol name (grep), never by line arithmetic**:

- Measurement rail: `app/research/desk_forward.py` — `DESK_FORWARD_HORIZONS_MINUTES` :112,
  `DESK_FORWARD_TOUCH_TIMEFRAMES` :121, `DESK_FORWARD_MAX_TOUCHES_PER_ROW` :134,
  `DESK_FORWARD_BASELINE_SEED = 1729` :138, `DESK_FORWARD_MEASURE_KEYS` :146,
  `forward_parameters()` :225 (the parameters-liveness pattern), `_session_slice` :295,
  `compute_forward_input_signature` :362 (the signature recipe), `_draw_anchor_indices` :428,
  `_measure_from` :451.
- Session honesty: `app/research/desk_sessions.py` — `recorded_session_dates` :129,
  `refuse_if_not_a_session` :180.
- Bars: `BarStore.merged_bars` (`app/research/bars.py:883`) — the ONLY analytic accessor;
  `bar_index.db` for coverage; fine coverage at authoring: 5m for all members + SPY + QQQ back
  to ~2026-06-05, 1m to ~2026-07-05.
- Pivot rule: `levels._swing_pivots` (`app/research/levels.py:325`) — the strict-extreme,
  ties-are-not-pivots discipline the playbook's pivot primitive mirrors.
- Batch precedents: `desk_deep_backfill.py` — `run_deep_backfill` :284,
  `DeskDeepBackfillComputeManager` :476 (the plan/walker/ledger/manager quartet the back-scan
  mirrors, re-chunked to one-session-date); `desk_topup_compute.py` — `run_topup` :397,
  `DESK_TOPUP_FINE_TIMEFRAMES` :168 (SPY freshness rides here).
- MCP: `_STATIC_PATHS` (`app/mcp/__init__.py:86`, 12 static entries; 18 tools total with the
  six parameterized); contract suite `tests/test_mcp_server.py`.
- Config: `config_fingerprint()` (`app/config.py:1351`); pin literal `08e471b10130e1e2`.
- Frontend guards: `tests/test_desk_ui_guards.py` `_PRICE_ARITHMETIC_FIELDS` :152;
  `tests/test_desk_refresh_chain_guard.py` `_EXPECTED_EFFECT_COUNT = 15` :104; copy lint
  `tests/test_copy_discipline.py`.
- The canonical spec: [`docs/playbook-detector-spec.md`](playbook-detector-spec.md) — §0 shared
  conventions, §1 the complete constants table, §3 the nine detectors.

Traps (learned in prior eras or foreseen for this one — read before EVERY iteration):

- **T-1 · The spec is law, vagueness is a drop.** Implement detectors from the spec verbatim.
  If a rule cannot be implemented deterministically as written, drop the detector from the
  iteration and surface it — never invent or adjust a threshold in code. A constant changed
  without a spec revision is a defect even if tests pass.
- **T-2 · The third setup vocabulary.** `setups.py` (tick touch scanner) and
  `backtests.py` (tape-arming occurrences) already use "setup" for OTHER things. The playbook
  module docstring carries the never-conflate disclaimer; playbook code never imports from
  `setups.py`; the field is `invalidation_price`, never "stop_loss" (copy lint).
- **T-3 · Lookahead hides in convenience.** The tempting bugs: gating on the trigger bar's own
  volume, using an unconfirmed pivot, computing MBR/RVOL from a window that includes the
  current session, reading SPY's in-progress bar. The generic truncation test exists to catch
  every one — extend it with each detector, never special-case it.
- **T-4 · Re-key, never rewrite.** A changed threshold/shape means new signatures and NEW
  record versions; old files stay byte-identical forever (SHA-256 listings in acceptance). If
  a re-run "should" overwrite something, the design is wrong.
- **T-5 · Fail closed, disclose the absence.** Thin baseline, missing 1m opening range
  (degrade to 5m basis, disclosed), no SPY bars (null market block + reason), non-session date
  (honest refusal) — every absence is a served row/reason, never a silent skip and never a
  fabricated value.
- **T-6 · Determinism means no wall-clock.** `as_of` derives from the session date; record ids
  from content/keys; baseline anchors from the recorded seed recipe (per-row streams — never
  `random.sample`, never a global RNG); repeat computation is byte-identical,
  division-independent, cancel-independent.
- **T-7 · GETs never compute.** The plan GET is metadata-only (one `list(include_bars=False)`
  pass + file stats); the evidence GET folds cached projections; a page load triggers nothing
  (the effect-count guard is re-derived deliberately, with rationale, exactly once).
- **T-8 · The rail is imported, not forked.** Measurement helpers come from `desk_forward.py`
  with a ZERO diff to that file; the playbook embeds the rail's constants in its own
  parameters so a rail change re-keys playbook records. Copying `_measure_from` "to be safe"
  creates the second-owner drift the whole codebase is built to prevent.
- **T-9 · Clean rebuild before browser evidence** (`rm -rf apps/frontend/.next`, rebuild,
  restart) — the stale-build trap.
- **T-10 · Evidence honesty.** No screenshot ⇒ `unknown`, never `passing`; backend-only proof
  never satisfies a browser acceptance line; the real back-scan is operator-run, reported
  run-or-not-run. **T-10a** (native tooltips need the headed rig) is carried but MOOT by
  design: every playbook acceptance uses DOM-content reveals only.
- **T-11 · Replay-script collisions.** The 20 stored golden replay scripts match
  first-visible text — new sections render BELOW shipped ones, reuse no shipped `data-testid`
  or heading string, and are statically swept against the stored scripts (the era-5 J-06
  lesson: target statically-rendered shell strings, never async list text).
- **T-12 · Host-guard caps are law** for the back-scan exactly as for every heavy path (see
  Anti-goals; the host has a hard-reset history under unconfined load).

## Must-have user journeys

Journeys **J-01 – J-10** form the era. **Frontend is present** (J-03 onward are
browser-verifiable). The default suite stays keyless on committed fixtures. Natural dependency
order: J-01 → J-02 → J-03, then the detector families J-04/J-05/J-06 (each lands visibly on the
J-03 section), then J-07 → J-08 → J-09, with J-10 guarding continuously.

- **J-01: The signal contract — opening-range breaks end to end, lookahead-clean and
  pre-registered**
  - Steps:
    1. Build `desk_playbook_features.py` (the spec §2 primitives: RTH slice, opening range with
       `1m→5m` honest degradation, `baselines` = MBR + per-slot volume medians, strict pivots,
       consolidation range, vertical move, zone touches, market context) and
       `desk_playbook_detect.py` with the two opening-range detectors (spec §3.1–3.2) + the
       signal shape `{symbol, setup_id, side, trigger_ts, trigger_price, entry, entry_kind,
       price_low, price_high, invalidation_price, geometry, volume, market, principles,
       disclosures}`.
    2. Build `desk_playbook.py`: the module doctrine docstring (third-vocabulary disclaimer),
       the spec §1 constants, `PLAYBOOK_REGISTER`, `playbook_parameters()` (call-time reads +
       embedded rail constants), `compute_playbook_input_signature` (metadata-only),
       `PlaybookStore` (2-pin append-only, id = pure key function, versions counted),
       `compute_playbook(session_date)` walking members for detection only (measurement is
       J-02), and `GET /research/desk/playbook` (honest empty; `?date=`/`?id=` verbatim reads).
    3. Wire `refuse_if_not_a_session` on the compute path; per-symbol absences (no 5m bars,
       thin baseline, no opening range) recorded as disclosed absence rows.
    4. Build the generic lookahead property test: for every detector × fixture × signal,
       `detect(bars[:trigger_index+1])` emits the identical signal, and mutating any bar after
       the trigger changes nothing — parametrized so J-04/J-05/J-06 extend it by adding
       fixtures only.
    5. Fixtures: one canonical 5m session firing exactly one `open_high_break` (hand-computed
       trigger/invalidation/geometry), one near-miss (wide OR — must NOT fire), one 5m-basis
       degradation session, one ambiguous outside bar (no signal + diagnostic).
  - Acceptance: with no record, `GET /research/desk/playbook` serves the honest empty payload;
    on the fixture rig a run records the golden signals byte-identically on re-run under
    identical pins, and a same-pins re-run returns the honest already-recorded response; the
    parameters blob is embedded verbatim in the payload and a monkeypatched constant moves both
    the blob and the signature (counter-test); the lookahead property test passes; a non-session
    date is refused with the module's honest sentence; suite green,
    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, zero
    diff to `desk_forward.py`/`desk_screen*.py`/`setups.py`/`bars.py`. *(Keyless; automated.)*

- **J-02: Every signal measured — the rail's own conventions, anchored at the trigger bar**
  - Steps:
    1. Extend `compute_playbook` to measure each signal in the same walk: finest-series anchor
       mapping (5m trigger → first containing 1m bar, fallback window-first), entry per the
       spec's stop-through convention, `_measure_from` imported from `desk_forward.py` with
       explicit `sign = ±1`, per-signal `forward` block (rail horizons + `to_close` +
       session-end dual MDD + truncation disclosures).
    2. Compute `invalidation_breached` (per-horizon boolean + `first_breach_minutes`) in the
       same pass, OUTSIDE `_measure_from`; declare it in `PLAYBOOK_SIGNAL_MEASURES` inside the
       parameters blob.
    3. Baseline anchors per (symbol, setup_id): the rail's seed discipline with per-row streams
       (`f"{seed}:playbook-{session_date}:{symbol}:{setup_id}"`), `k = min(capped signals,
       session bars)`, entry = anchor close, drawn by the imported `_draw_anchor_indices`;
       signal caps + beyond-cap disclosure; per-(setup, side) record `summary` via the imported
       averaging helpers.
    4. Build `desk_playbook_compute.py` (single-flight manager trio + CLI through ONE shared
       `run_playbook_and_record`) and `desk_playbook_log.py` (terminal-state-only run ledger,
       served by `GET /research/desk/playbook/runs`).
    5. Convention-identity test: a synthetic anchor measured through the playbook path and
       directly through `desk_forward._measure_from` produces byte-identical leaves; a
       rail-constant monkeypatch moves the playbook signature (the embedded-constants guard).
  - Acceptance: fixture goldens assert exact horizon returns/MDD per signal including one
    truncated horizon and one gap_open entry; `invalidation_breached` fixtures cover breach at
    a horizon boundary, breach on the anchor bar, and never-breached; baseline anchors are
    byte-reproducible from the recorded parameters and unchanged when an unrelated symbol is
    added; J-01-era records (no measurement) serve verbatim with the honest
    `"measurement not recorded in this record"` absence — never backfilled; prior record files
    byte-identical on disk (SHA-256 listing); the run ledger records exactly one row per
    terminal run (interrupted run records NOTHING); suite green, pin unchanged, zero diff to
    `desk_forward.py`. *(Keyless; automated.)*

- **J-03: The Playbook lands on `/desk`**
  - Steps:
    1. Build the **Playbook Signals** section (below every shipped section): a session-date
       text input using the desk's existing validated day-input convention (the
       `validateScreenDayRange` pattern — `yyyy-MM-dd`, blank = the most recent recorded
       session), a Run Playbook button wired to the compute trio (live progress + cancel; page-load GETs trigger nothing), the signals table
       (setup chip, side, trigger time ET / price, invalidation price, geometry + volume +
       market disclosures, per-horizon forward cells + invalidation-breached marks, baseline
       summary), per-symbol absence rows, and the provenance line (record id, signature,
       parameters hash, fingerprint) — rows served pre-sorted (trigger ts, symbol), never
       client-reordered.
    2. Honest states: `"Playbook not computed for this session."` + enabled Run Playbook;
       non-session refusal copy verbatim; `"measurement not recorded in this record"` for
       legacy records.
    3. Extend the guards deliberately: every new served numeric into
       `_PRICE_ARITHMETIC_FIELDS` (+ seeded counter-tests); `_EXPECTED_EFFECT_COUNT`
       re-derived once with the rationale paragraph; `_TRIGGER_CALLS` additions; new
       `data-testid`s only; static sweep against the stored replay scripts (T-11).
    4. `apps/frontend/lib/api.ts` gains the playbook fetch/trigger/poll/cancel functions in
       the established style; copy lint green unmodified.
  - Acceptance: in a real browser after the T-9 clean rebuild — the empty state + enabled Run
    Playbook (screenshot); after a fixture-scoped run, the signals table renders with chips,
    disclosures, forward cells, and provenance (screenshot); an in-flight second trigger is
    refused (single-flight, screenshot); a non-session date shows the refusal copy
    (screenshot); every shipped `/desk` section renders exactly as shipped in the same pass;
    all extended guard tests green; suite green, pin unchanged. *(Browser-verifiable; keyless
    via the fixture-scoped backend; DOM reveals only.)*

- **J-04: The continuation family — JBE, DBI, cup-and-handle**
  - Steps:
    1. Implement spec §3.3–3.4 (JBE/DBI over the shared consolidation-range + jump gates,
       ladder caps + `ladder_step_ratio`) and §3.6 (cup-and-handle over confirmed pivots +
       the two dry-up gates), long-only cup per spec.
    2. Constants join the parameters blob (signature moves — expected and visible; previously
       recorded files stay byte-identical).
    3. Fixtures per detector: one canonical firing session (hand-computed geometry) + one
       near-miss (e.g. jump < 1.5× base; handle deeper than 50%) + lookahead-test extension.
    4. A structural guard: no playbook module iterates over candidate threshold values
       (source-scan test), and `desk_playbook_evidence` is import-banned from the detect
       module.
  - Acceptance: fixture goldens for JBE, DBI, and cup-and-handle (trigger, invalidation,
    geometry disclosures exact); near-misses provably silent; the lookahead property test
    covers the new detectors; a back-dated fixture re-run shows new-signature versioning with
    old records untouched (SHA-256); in the browser, at least one signal of each new setup
    legible in the J-03 section on the fixture rig (screenshot); suite green, pin unchanged.
    *(Keyless core; browser-verifiable.)*

- **J-05: The climax family — capitulation entry, euphoria marker**
  - Steps:
    1. Implement spec §3.5: the vertical-move formation with climax re-anchoring, the
       reversal-bar trigger, the leg-low invalidation; euphoria as the exact mirror MARKER —
       no side, no band, never measured — decorating subsequent signals
       (`euphoria_recent`/`capitulation_recent`) within the decay window.
    2. Fixtures: one clean capitulation → bounce firing; one high-volume decline that never
       reverses in the window (expires silently); one euphoria marker decorating a later
       fixture signal.
  - Acceptance: fixture goldens exact; the marker never appears as a measurable signal row
    anywhere (structural test: no euphoria entry in any `summary`/evidence pool); lookahead
    test extended; browser: a capitulation signal + a marker-decorated signal legible on the
    fixture rig (screenshot); suite green, pin unchanged. *(Keyless core; browser-verifiable.)*

- **J-06: The range family — range trades, double top/bottom**
  - Steps:
    1. Implement spec §3.7 (range arming via tested-twice-and-held zones, the shared
       reversal-bar trigger grammar, midrange + absorption-bar P6 disclosures; PROVISIONAL
       tier stated in the module) and §3.8–3.9 (double top/bottom over confirmed pivots,
       valley-break trigger — never the second top, full-height `nominal_risk_mbr`).
    2. Guard: the playbook walk performs zero `compute_tradability`/`compute_levels` calls
       (call-count test) — the book's intraday ranges and the desk's walls are different
       owners.
    3. Fixtures: a triple-touch armed range firing off the low zone; a range dissolved by a
       strict break; a clean double top firing at the valley; a failed double top (p2 exceeds
       p1 beyond tolerance — silent).
  - Acceptance: fixture goldens exact; the zero-structure-calls guard green; lookahead test
    extended; browser: one range signal and one double-top signal legible on the fixture rig
    (screenshot); suite green, pin unchanged. *(Keyless core; browser-verifiable.)*

- **J-07: The back-scan — every recorded session, resumable and append-only**
  - Steps:
    1. Build `desk_playbook_backscan.py`: `plan_backscan` (pure, metadata-only — recorded
       session dates in range × recorded-at-current-signature state, one signature resolution
       per call), the compute trio + `run_backscan` walking planned dates through the ONE
       shared `run_playbook_and_record`, per-date outcomes
       `reused/recorded/refused_non_session/failed`, cooperative cancel on a date boundary,
       and the terminal-state-only back-scan ledger.
    2. Serve `GET .../backscan/plan`, the trio, and `GET .../backscan/runs`; build the
       `/desk` **Backscan** panel (plan preview for a From/To range, trigger + live progress +
       cancel, runs table) — page-load GETs trigger nothing.
    3. The REAL back-scan over the store's recorded sessions is an operator-run act,
       host-guard-confined, reported run-or-not-run with its ledger row.
  - Acceptance: fixture-scoped — a run over N planted sessions records N; cancel mid-scan then
    re-run resumes with recorded dates reported `reused` at zero detector calls (call-count
    asserted); a threshold monkeypatch flips every planned date to
    `missing_at_current_signature`; an interrupted run leaves the ledger honestly empty; every
    previously recorded file byte-identical (SHA-256); plan GET performs no bar reads
    (stub-store-that-raises test); browser: plan preview + a completed fixture scan's run row
    with per-outcome counts (screenshot); suite green, pin unchanged. *(Keyless core;
    browser-verifiable; the real scan operator-run.)*

- **J-08: The evidence view — distributions beside the null, min-n honest**
  - Steps:
    1. Build `desk_playbook_evidence.py`: per-file evidence projections (pooled per-(setup,
       side) value lists) in a stat-keyed derived cache (`desk_meta_cache` contract), folded
       on read into `GET /research/desk/playbook/evidence` — newest record per date at ONE
       signature (default: the current parameters' signature; others listed as
       `{signature, dates, created span}`, never pooled).
    2. Cells: `{n, n_truncated, n_baseline, median_pct, p25_pct, p75_pct, mean_pct}` for
       signals and baseline side-by-side, `invalidation_breached` counts by horizon,
       `below_min_n` tag under `PLAYBOOK_MIN_N_DISCLOSURE` (a disclosure — nothing hidden),
       truncated values excluded from pools with the exclusion disclosed; `EVIDENCE_REGISTER`
       served on the payload.
    3. Build the `/desk` **Playbook Evidence** section rendering the table as served (no
       client arithmetic — guard fields registered).
  - Acceptance: the GET is a pure function of the recorded record set (identical set →
    byte-identical body; asserted with the cache cold AND warm); a hand-computed fixture
    aggregate reproduces exactly; a low-n cell carries the tag while still serving its
    numbers; deleting the cache DB changes nothing but latency (rebuild test); no
    probability/expectancy/significance words anywhere (copy lint + register lint); browser:
    one well-populated cell and one tagged low-n cell legible (screenshot); suite green, pin
    unchanged. *(Keyless core; browser-verifiable.)*

- **J-09: MCP contract v4 — 20 read-only tools**
  - Steps:
    1. Add `desk_playbook` → `/research/desk/playbook` and `desk_playbook_evidence` →
       `/research/desk/playbook/evidence` to `_STATIC_PATHS` (`app/mcp/__init__.py:86`);
       `get_endpoint`'s `/research/` allowlist already reaches the parameterized reads.
    2. Update `tests/test_mcp_server.py` to the 20-tool contract (baseline is the post-Era-B
       **18** — the archived goal's "17" predates `desk_forward`), keeping byte-identity and
       honest-error clauses for every tool including the two new ones against honest-empty
       AND populated fixture states.
  - Acceptance: exactly 20 tools advertised; both new tools byte-identical to their curl
    equivalents in empty and populated states; `get_endpoint` on
    `/research/desk/playbook?date=...` proxies verbatim; MCP suite green. *(Keyless;
    automated.)*

- **J-10: The kept product stands — regression sentinel**
  - Steps:
    1. Full backend suite + engine equivalence; every guard test green with the playbook
       extensions and NO other modification; `Config().config_fingerprint()` prints
       `08e471b10130e1e2`; suite count ≥ the era-open count recorded at iteration 0.
    2. In a real browser (after T-9): walk the kept product — cockpit sim tape + chart,
       `/structure` pinned-AAPL Load, and EVERY shipped `/desk` section (screen history,
       forward returns, refresh chain, briefing, skipped, runs/pins/compare/provenance) —
       screenshots for each.
    3. Kept-route byte-identity vs a baseline captured from the era-open commit, with exactly
       two expected exemptions: the MCP tool list (18 → 20) and any route this goal's own
       Data Contract adds; any other difference is explained against R-1/R-2 or it is a
       defect.
    4. The era's cumulative diff stays inside this goal's inventory (the new
       `desk_playbook*` modules/routes/sections/tools + the named guard-test extensions +
       SPY freshness in the top-up walk) — anything else is surfaced BEFORE it lands.
  - Acceptance: full suite green under the unchanged pin; every browser step evidenced by
    screenshot; kept-route byte-identity outside the two named exemptions; nav = exactly
    three routes; MCP = exactly 20 tools; zero out-of-inventory changes, reading "inventory"
    as including R-1 and R-2. *(Keyless core; browser-verifiable.)*

<!-- AUTO:journeys -->

- **J-11: Every evidence cell states the basis of its own n**
  - Steps:
    1. Extend the fold in `app/research/desk_playbook_evidence.py` — the ALREADY-registered
       "Evidence aggregates" Data Contract row, same owner, same serving endpoint
       `GET /research/desk/playbook/evidence`, no new row and no new endpoint — so every served
       cell carries the exclusions it already computes and then discards: `signal.n_unmeasured`
       (pooled events whose horizon leaf carries `return_pct: null`, which
       `desk_forward._collect_measures` skips with no counter — today 234 of the real corpus's
       300 recorded signals carry exactly that at `1m` under the recorded reason "the 1m horizon
       is finer than the 5m touch series", so `double_top:short` at `1m` serves `n: 31`,
       `n_truncated: 0` while 59 of its 90 signals were never measurable there);
       `baseline.n_truncated` + `baseline.n_unmeasured` (the baseline pool's own exclusion counts,
       computed today as `_baseline_truncated` and thrown away — `capitulation:long` at `4h`
       serves `n_baseline: 8` beside a signal cell that honestly says `n: 25, n_truncated: 4`);
       and `signal.n_sessions` / `baseline.n_sessions`, the number of distinct recorded session
       dates that contributed to the pool.
    2. Add a payload-level `basis` block for the POOLED signature — `{dates, n_records,
       created_span}` — built by the SAME helper that already builds each `other_signatures`
       entry (extract it once and call it twice; never a second implementation), so the pooled
       signature discloses exactly what every non-pooled signature already does. Today the table
       pools 4 session dates (2026-06-22, 2026-06-23, 2026-06-24, 2026-08-07) and says so nowhere.
    3. Every new value folds from the per-file projections `PlaybookEvidenceCache` ALREADY stores
       (each carries `session_date`, `recorded_at`, and the full `forward` leaves): no cache
       schema change and no cache migration, no bar read, no re-measurement, and no call into
       `desk_forward._measure_from` — the counts read absences that were recorded at compute time.
    4. Update `EVIDENCE_REGISTER` so its "the exclusion counted, never silently dropped" sentence
       covers the unmeasurable class and the baseline column too, and names the basis; the copy
       stays descriptive with no probability, expectancy, edge, or significance word, and states
       nothing about the excluded observations beyond their count and the recorded reason.
    5. Render them on the `/desk` Playbook Evidence section as served: the basis line beside the
       existing "Built from signature:" line, and the new counts in the cells table — no client
       arithmetic; extend `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` with each
       new served numeric plus a seeded counter-test; `lib/types.ts` + `lib/api.ts` in the
       established style; new `data-testid`s only, statically swept against the stored replay
       scripts (T-11).
  - Acceptance: `GET /research/desk/playbook/evidence` remains the single owner and single
    serving endpoint of every value here (the blueprint's already-registered "Evidence
    aggregates" row — no new row, no new owner, no second computation path), and its
    `basis.dates` / `basis.created_span` are byte-identical to what the shipped
    `?signature=<that same signature>` inspect branch serves for the same signature, asserted by
    test — one implementation, two views. The GET stays a pure function of the recorded record
    set: identical files in, byte-identical body out, asserted with the projection cache cold AND
    warm and again after deleting the cache DB, with no cache-schema migration anywhere. A
    hand-computed fixture over at least two recorded session dates — one of them a 5m-basis
    session whose `1m` leaves carry the recorded null reason — reproduces `n`, `n_truncated`,
    `n_unmeasured`, `n_sessions`, `n_baseline`, and `basis` exactly, and every already-served
    number (`n`, `median_pct`, `p25_pct`, `p75_pct`, `mean_pct`, `below_min_n`, the breach
    counts) is unchanged for the identical record set. No playbook record file is written,
    rewritten, backfilled, or re-keyed: the new fields are served-only, never parameters, so
    `playbook_parameters()` and `playbook_input_signature` do not move and every previously
    recorded file stays byte-identical on disk (SHA-256 listing). The `default` profile, `v1`,
    and the engine's equivalence output stay byte-identical, `Config().config_fingerprint()`
    still prints `08e471b10130e1e2`, and zero new `Config` fields are added. MCP stays exactly 20
    tools with `desk_playbook_evidence` still a byte-identical proxy of the enriched body. In a
    real browser after the T-9 clean rebuild, on the scoped fixture rig, the Playbook Evidence
    section shows the basis line and at least one cell whose `n_unmeasured` is greater than zero
    beside its own `n` (screenshot; DOM-content reveals only — no screenshot ⇒ `unknown`), and
    every shipped `/desk` section still renders as shipped in the same pass; the extended guard
    tests (including the seeded counter-test on each new served numeric), the copy lint, and the
    full backend suite are green under the unchanged pin. A `[NEW]`-flagged demo-narrator
    walkthrough step walks the enriched Playbook Evidence section and is recorded against a state
    that actually renders those fields — no step may claim `new`/`verified` for anything not
    built. No PnL-ledger row is written and no R, $, or return figure is produced anywhere: the
    playbook measures no PnL (a signal is a recorded observation, never a trade, and this era's
    anti-goals keep the promotion ledger and the champion pointer untouched), so the
    operator-visible before/after of this enhancement is the evidence table's own n shown with
    its basis, not a promotion record. *(Keyless core; browser-verifiable.)*

- **J-12: Every other signature says which of its own inputs made it other**
  - Steps:
    1. Extend `_fold_other_signatures` in `app/research/desk_playbook_evidence.py` — the
       ALREADY-registered "Evidence aggregates" Data Contract row, same owner, same serving
       endpoint `GET /research/desk/playbook/evidence`, no new row, no new endpoint, no new MCP
       tool — so every signature it lists also states WHICH hashed input made it differ from the
       pooled one. `compute_playbook_input_signature` (`desk_playbook.py:322`) hashes exactly
       three things — the sorted `(symbol, timeframe, series_id, checksum)` tuples of
       members ∪ {SPY} at `1m`/`5m`, the `config_fingerprint`, and the canonical
       `playbook_parameters()` blob — and every recorded file already carries TWO of the three
       verbatim (`parameters`, `config_fingerprint`), so each listed entry gains
       `parameters_match`, `changed_parameter_keys` (sorted key NAMES only, never their values),
       `config_fingerprint_match`, and `differs_in`: the list of hashed inputs proven to differ.
       Today's real store makes the distinction concrete — its two non-pooled signatures differ
       from the pooled one in `setups` alone (plus two constants that did not exist yet), i.e. the
       detector rules changed; a bar top-up would instead leave both recorded pins identical.
    2. Keep `bar_inputs` HONEST, because it is the one input no record stores: it may appear in
       `differs_in` ONLY when both recorded pins match the current ones, where it is a proof by
       elimination (nothing else is hashed). When a recorded pin differs, the bar listing's own
       state is not recorded anywhere, so it is neither claimed nor denied — the served shape says
       what is proven and stays silent on what is not (a missing claim, never a guessed one).
    3. Bound the cost and change no cache: every record at ONE signature necessarily carries the
       identical `parameters` and `config_fingerprint` (both are hashed INTO that signature), so
       the fold resolves each other signature's pins from ONE representative file per distinct
       signature through `PlaybookStore.get` — the `inspect_signature` non-hot-path precedent —
       never once per file, never a bar read, never a call into `_measure_from`. If instead the
       pins are carried in the per-file projection, the cached projection must carry its own
       version marker so an already-cached old-shape row is an honest MISS rather than a wrong or
       crashing read; either way there is no cache-schema migration and no re-measurement.
    4. Update `EVIDENCE_REGISTER` so its "listed, never pooled" sentence also names what a listing
       now discloses AND its boundary: another signature's own thresholds, distributions, and
       cells are never served beside these — a signature is identified, never compared, and no
       parameter value is ever shown next to an outcome number (the era's no-threshold-fitting
       rail, restated where a reader could otherwise expect a comparison). Copy stays descriptive:
       no probability, expectancy, edge, or significance word; `tests/test_copy_discipline.py`
       green unmodified.
    5. Render it verbatim on the `/desk` Playbook Evidence section's existing "Other signatures
       (listed, never pooled)" list — one served phrase per entry, no client-side classification —
       and read the ALREADY-served `n_records` for each entry's record count instead of the
       `entry.dates.length` the section derives client-side today (the count is the server's;
       `PlaybookEvidenceOtherSignatures`, `page.tsx:3908`). Extend
       `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` with `entry.n_records` plus a
       seeded counter-test; `lib/types.ts` + `lib/api.ts` in the established style; new
       `data-testid`s only, statically swept against the stored replay scripts (T-11).
  - Acceptance: `GET /research/desk/playbook/evidence` remains the single owner and single serving
    endpoint of every value here — no new Data Contract row, no new owner, no second computation
    path, and no client-side derivation of any of it (the `/desk` section renders the served
    fields verbatim, including the record count it derives itself today). The evidence still pools
    exactly ONE signature: `cells`, `invalidation_breached`, and `basis` are byte-identical to
    what they serve today for the identical record set, no non-pooled signature's signals,
    distributions, thresholds, or cells appear anywhere in the payload or on the page, and the
    attribution is proven by three keyless fixture states asserted separately — a monkeypatched
    detector constant (`parameters`, with `changed_parameter_keys` naming exactly the moved keys),
    a different `config_fingerprint` argument passed to `fold_evidence` (`config_fingerprint`; the
    real pin is never touched and no `Config` field is added), and an added bar series with both
    recorded pins unchanged (`bar_inputs`, the elimination case) — plus a fourth asserting that
    when a recorded pin differs, `bar_inputs` is absent from `differs_in` rather than guessed. The
    GET stays a pure function of the recorded record set: identical files in, byte-identical body
    out, asserted with the projection cache cold AND warm and again after deleting the cache DB,
    with no cache-schema migration; the fold performs at most one additional record read per
    DISTINCT other signature (asserted by call count, so a store with many files at few signatures
    cannot become O(files)), and reads no bars at all (stub-store-that-raises test). No playbook
    record file is written, rewritten, backfilled, or re-keyed: the new fields are served-only and
    never parameters, so `playbook_parameters()` and `playbook_input_signature` do not move and
    every previously recorded file stays byte-identical on disk (SHA-256 listing). The `default`
    profile, `v1`, and the engine's equivalence output stay byte-identical,
    `Config().config_fingerprint()` still prints `08e471b10130e1e2`, zero new `Config` fields, and
    MCP stays exactly 20 tools with `desk_playbook_evidence` still a byte-identical proxy of the
    enriched body. In a real browser after the T-9 clean rebuild, on the scoped fixture rig, ONE
    screenshot shows a state where the pooled signature holds zero records — the shipped empty
    cells state — and, in the same frame, at least one other signature carrying its own record
    count and its served attribution phrase (DOM-content reveals only; no screenshot ⇒ `unknown`,
    never `passing`), and every shipped `/desk` section still renders as shipped in the same pass;
    the extended guard test with its seeded counter-test, the copy lint, and the full backend
    suite are green under the unchanged pin. A `[NEW]`-flagged demo-narrator walkthrough step
    walks the Other signatures list in the state it was actually captured in: a step may mark
    `new`/`verified` only for what this iteration actually built AND photographed, and no step may
    click an affordance `/desk` does not have. No PnL-ledger row is written and no R, $, or return
    figure is produced anywhere — the playbook measures no PnL (a signal is a recorded
    observation, never a trade, and this era's anti-goals keep the promotion ledger and the
    champion pointer untouched) — so the operator-visible before/after of this enhancement is an
    evidence table that, when its own pool is empty or thin, names which of its three hashed
    inputs moved instead of leaving the operator to guess. *(Keyless core; browser-verifiable.)*

<!-- /AUTO:journeys -->

## Anti-goals

**Immutable rails — the identity of the project (from
[`docs/research-directions.md`](research-directions.md) §0.3; enforced by existing tests and
audits; only ever grow more specific, never weaker):**

1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
   trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
   tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
   fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
   imperative trading cues. *(critical)*
3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
   states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
   surface's behaviour stay byte-identical. New work is additive and versioned beside them,
   never a mutation of them. *(critical)*
4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
   through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins
   are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
   feeds/fingerprints to manufacture a survivor. *(critical)*
5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
   *(critical)*
6. **Single source of truth** — each shared value is computed once, owned by one canonical
   endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
   violations. *(critical)*
7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
   requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
   research artifact.
8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
   MCP surface can change state. *(critical)*
9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never
   re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
   *(critical)*
10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is
    an explicit, logged act. *(critical)*

**Era-B desk anti-goals that remain binding:** membership is never a signal; snapshots are
append-only and pinned; every run is an explicit operator act; the briefing describes, never
advises; no new statistics, gates, or strategies; the demolition stays demolished; the ledger
never holds orders; the suite stays keyless and hermetic; the fingerprint pin does not move.
*(all critical)*

**Playbook-era anti-goals (added, not weakening any rail above):**

- **No threshold exists outside the spec, and no code path sweeps one.** Every detector rule
  and threshold exists in [`docs/playbook-detector-spec.md`](playbook-detector-spec.md) BEFORE
  the code that uses it; no code path iterates thresholds against outcomes (source-scan
  guard-tested); a threshold change is a spec revision + new signature, never an edit of
  recorded signals and never a sweep. *(critical)*
- **A signal is an observation, not a call.** No signal, chip, or evidence cell uses advice,
  imperative, prediction, probability, expectancy, edge, or significance language; the served
  registers state what was NOT measured (no fills, no costs, returns not stop-adjusted);
  `invalidation_price` is geometry, never an order concept. *(critical)*
- **The evidence pools one signature.** Distributions never mix parameter regimes; other
  signatures are listed, not merged; the min-n floor tags, it never filters; truncated values
  never enter a pool undisclosed. *(critical)*
- **No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1.**
  New signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never
  overwritten; the store exposes no update or delete method (source-scan guard-tested).
  *(critical)*
- **No second implementation of the measurement rail.** Measurement helpers are imported from
  `desk_forward.py` with a zero diff to that file; no playbook module re-implements horizons,
  MDD, truncation, or the seed discipline (import-graph guard-tested). *(critical)*
- **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY
  inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys,
  this Anti-goals section, or any other part of this file; proposed journeys MUST carry a
  single-source-of-truth acceptance criterion, keep the `default` profile and `v1`
  byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey
  just to keep the loop alive is a failure. *(critical)*

**Host protection (carried verbatim — a physical constraint of the host, not product scope):**

- **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
  2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
  with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
  beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
  (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
  bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
  interactive pump sessions are auto-confined in place by the engine (`host-guard-adopt.sh`;
  `scripts/automation/host-guard-exec.sh claude` is the optional from-birth wrapper) — the
  engine pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established.
  Never disable, widen, or bypass these caps to make a run faster or a pause go away; widening
  the mask follows the verification ladder in
  `trendora/project-extensions/host-guard/README.md`. *(critical)*
