# Iteration diff (bounded)

Files changed: 5. Shown in full: 3.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `docs/goal-archive/goal-2026-08-14.md` (547 lines not shown)
- `docs/goal.md` (1269 lines not shown)

```diff
diff --git a/docs/goal-archive/goal-2026-08-14.md b/docs/goal-archive/goal-2026-08-14.md
new file mode 100644
index 0000000..f6af075
--- /dev/null
+++ b/docs/goal-archive/goal-2026-08-14.md
@@ -0,0 +1,941 @@
+# Tapeology — Project Goal (Era B2: The Playbook — the book's intraday setups, detected on the desk's own bars and measured forward)
+
+> Eras 1–5D and Era B are the **foundation** of this goal. Eras 1–2 (tape reading + the research
+> evolution, GOAL_ACHIEVED) are archived at
+> [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md); the structure-UI
+> interlude at [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md);
+> **Era 5 "The Library"** at [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md);
+> the **"Fast Wall" interlude** at [`docs/goal-archive/goal-2026-07-17.md`](goal-archive/goal-2026-07-17.md);
+> the **"Clean Slate" demolition** at [`docs/goal-archive/goal-2026-07-25.md`](goal-archive/goal-2026-07-25.md);
+> and **Era B "The Desk" (GOAL_ACHIEVED 2026-07-31, session `desk`, journeys J-01–J-21)** at
+> [`docs/goal-archive/goal-2026-08-10.md`](goal-archive/goal-2026-08-10.md). Eras 3, 4, 5B, and 5C
+> are frozen foundation; their records live in git history and `reports/goal-session-*-delivered.md`.
+>
+> **This chapter is Era B2 of the operator's pivot (A Demolition → B Desk → B2 Playbook → C
+> Annotator).** The product today is exactly **Cockpit (`/`) + Structure (`/structure`) + Desk
+> (`/desk`)**, the fingerprint epoch is `08e471b10130e1e2`, the MCP surface is **18 read-only
+> tools**, and the honesty machinery (stores, gates, registry, PnL promotion ledger) is fully
+> intact. B2 is a BUILDING era on the desk's ground: it teaches the desk the intraday setups of
+> the book the project is named for — Graifer & Schumacher, *Techniques of Tape Reading* (2004) —
+> detected on the desk's own recorded 5m/1m bars and measured with the desk's own forward-return
+> + max-drawdown conventions. It is an operator-directed product era OUTSIDE the research catalog
+> ([`docs/research-directions.md`](research-directions.md) has no Playbook card; per its §5.6 this
+> file wins for the running era). The statistics program (era-6 "The Referee") and the annotation
+> corpus (Era C) remain SEPARATE future chapters — nothing of them lands here.
+>
+> **Unlike Era B, this era DOES add new research math** — a family of pre-registered bar-pattern
+> detectors and their trigger-anchored measurements — under two hard disciplines: (1) every
+> detector rule and threshold is fixed in advance in
+> [`docs/playbook-detector-spec.md`](playbook-detector-spec.md) (the canonical spec; developers
+> implement from it, never re-derive or re-tune — a threshold change is a named revision that
+> re-keys future records, never a sweep); (2) every measurement reuses the desk forward rail's
+> own conventions verbatim. It adds **zero statistics gates** and **zero annotation surfaces**.
+
+## Vision
+
+Era B gave the operator a desk: universe in, wall-screen briefing out, every record append-only
+and evaluable. But the desk still reads only structure — it knows where the walls are, not what
+the tape is DOING. The book this project is named for describes exactly that missing layer: an
+intraday grammar of price/volume behavior (six principles, a handful of named setups) that has
+never been encoded, let alone measured. Era B2 builds it as evidence, not advice:
+
+1. **A pre-registered playbook of the book's intraday setups.** For any recorded session, a
+   detector family — open-high/open-low-break, jump-base-explosion (JBE) / drop-base-implosion
+   (DBI), capitulation (+ euphoria marker), cup-and-handle, range trades, double top/bottom —
+   walks each member's RTH 5m bars (1m bars for the opening range) and emits signals:
+   `{symbol, setup_id, side, trigger price/time, invalidation_price, geometry, volume character,
+   market context, principles}`. Formation logic is lookahead-clean at bar granularity; every
+   threshold is a named constant from the canonical spec, tagged BOOK or ADAPTATION.
+2. **Every signal measured the desk's own way.** Each signal carries a trigger-anchored
+   measurement produced by the SAME conventions as the desk forward rail: horizons +1m/+5m/+1h/
+   +4h/to-close as trading-bar counts on the session's finest series, side-signed returns, dual
+   max drawdown clamped ≤ 0, truncation honesty, and a seeded random-anchor baseline of the same
+   session — plus an `invalidation_breached` disclosure (did price trade through the book's
+   structural level; returns are never stop-adjusted).
+3. **A back-scan that turns the book into a ledger.** One resumable operator act walks EVERY
+   recorded session with 5m coverage (~45 sessions × ~101 members at authoring; the store is
+   append-only so this grows daily), recording one append-only playbook record per
+   (session date, input signature) — reusing recorded work on re-run, chunked by session,
+   host-guard-confined.
+4. **An evidence view that says what happened, with n.** Per setup × side × horizon: the pooled
+   forward-return and MDD distributions of every recorded signal beside the pooled baseline
+   anchors — median/quartiles/mean, `n`, `n_truncated`, `n_baseline`, low-n tags below a named
+   disclosure floor. Descriptive distribution language only; no probability, expectancy, edge,
+   or significance claims — those gates are era-6's.
+
+The deliverable: the desk learns to read the tape the way the book teaches, writes down every
+signal it would have seen, measures what price then did against chance anchors, and shows the
+distributions honestly — every number owned once, every run explicit, every record append-only.
+
+## Target Users
+
+- The project owner (a discretionary intraday trader) who opens `/desk`, runs the playbook for a
+  session, reads the signals beside the wall briefing, and reads the evidence table to learn
+  which of the book's setups his own data supports.
+- The same owner operating through **Claude + MCP**: `desk_playbook` / `desk_playbook_evidence`
+  (plus the existing 18 tools) make the playbook readable from a conversation end to end.
+- AI dev-chain agents (the goal-mode chain) building and browser-verifying the era.
+
+## Foundation invariants (still law — eras 1–5D and B)
+
+The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md))
+remains binding on all KEPT code — price-impact-over-aggression; honest uncertainty; **no
+fabricated data**; single source of truth; no magic numbers; provider-agnostic engine;
+deterministic & reproducible; no secrets in source; research read-only over the engine; record
+integrity; source/feed/`config_fingerprint` honesty. The surface inventory is the post-Era-B
+one: `/`, `/structure`, and `/desk` (this era adds sections to `/desk`, no new route).
+
+1. The **tape engine** (`app/engine/`) emits byte-identical output under `default` on identical
+   inputs. `config_fingerprint` stays **`08e471b10130e1e2`** for this WHOLE era. This era needs
+   **zero new `Config` fields** (the `desk_forward` precedent: playbook thresholds are module
+   constants hashed into the record's own input signature); if the build genuinely needs one, it
+   takes §0.4 **Path A** (exclusion + stability test + counter-test) — a pin movement is a
+   defect, full stop.
+2. The **research computations** — `levels.py`, `tradability.py` (+cache), `setups.py` (+scan
+   cache), `edge_report*.py`, `backtests.py`, the strategy registry, `profiles.py` (`default`),
+   the champion pointer — stay behaviorally byte-identical. The playbook READS bars; it never
+   touches, re-implements, or re-tunes any of them.
+3. The **stores** — `BarStore` + `DatasetStore` formats, checksums, append-only immutability,
+   split freezing, the durable accelerator DBs, the Era-B universe/screen/forward stores and
+   their run ledgers — are untouched in format and discipline. The era ADDS a playbook store
+   (and its run ledgers + a derived evidence projection cache) under the same discipline.
+4. The **PnL promotion ledger** stays append-only and intact; the champion pointer does not move.
+5. The **kept surfaces as shipped**: the cockpit, `/structure`, and every shipped `/desk`
+   section (screen history calendar, forward returns, refresh chain + compute controls, ranked
+   briefing, skipped members, runs/pins/compare/provenance sections) keep working exactly as
+   shipped. The playbook lands as NEW sections below the shipped ones; no shipped `/desk`
+   section, column, or behavior changes.
+6. The **read-only MCP server** keeps its byte-identical GET-proxy contract; this era adds two
+   GET-proxy tools (**18 → 20**) and never adds writes.
+
+### OWNER RATIFICATION — carried and new
+
+**R-1 (2026-07-27, price-less-bar repair)** — ratified in Era B (see the archived goal's R-1
+block for the eight-file inventory); it remains ratified history and its terms carry forward
+unchanged.
+
+**R-2 (2026-08-10, the post-Era-B forward-test interlude) — ratified and IN INVENTORY for this
+era.** Between Era B's GOAL_ACHIEVED (iteration 36, commit `94eb1b0`) and this era's opening,
+the operator's interactive sessions landed a body of desk work no Era-B journey describes. It is
+ratified as foundation, comprising the `goal/desk` commits after `94eb1b0` through the era-open
+tip (including the operator's pre-era commit of the 2026-08-07/09 working tree — 14 modified
+files + `desk_meta_cache.py`/`test_desk_meta_cache.py`; iteration 0 records the era-open SHA):
+
+- `app/research/desk_forward.py` + `desk_forward_compute.py` + `desk_forward_log.py` +
+  `desk_forward_pins.py` — the touch-anchored forward-return v2 rail (horizons/dual-MDD/seeded
+  baseline/2-pin append-only `ForwardStore`) and its manager, ledger, and pins;
+- `app/research/desk_sessions.py` — recorded-session honesty (screen only real sessions);
+- `app/research/desk_screen_decision.py` + `desk_screen_cleanup.py` — one-snapshot-per-date
+  reuse/record/replace semantics and the operator cleanup path;
+- `app/research/desk_deep_backfill.py` — the chunked, resumable fine-bar (1m/5m) deep-backfill
+  quartet and its Alpaca vendor seam;
+- `app/research/desk_meta_cache.py` — the derived, rebuildable screen/forward meta-projection
+  cache (stat-keyed, owns nothing);
+- the desk refresh/screen/forward performance work, the ET time convention on desk surfaces, and
+  the fine-timeframe top-up walk (`DESK_TOPUP_FINE_TIMEFRAMES`).
+
+Where clauses below say "untouched", "byte-unmodified", or "out-of-inventory", they are read
+subject to **R-1** and **R-2**.
+
+**R-3 (2026-08-11, the playbook spec rulings) — ratified.** Iterations 6–9 surfaced two open
+"The spec is canonical" items and halted the session STALLED awaiting them. Both are ruled here.
+This block is the ruling; the spec edits it directs are iteration-10 developer work (the same
+shape as iteration 6's §3.5 doc-only closure), not a licence to change detector behavior beyond
+what is named below.
+
+**R-3.1 — the `range_trade` "degenerate trigger reference" clause is RATIFIED as written.**
+The dated clarification in `docs/playbook-detector-spec.md` §3.7 Edge cases, and the matching
+fail-closed void in `_range_trade_side` (`T ≤ SL` long / `T ≥ SH` short emits nothing and the walk
+continues), stand as canonical. It is ratified on its merits: narrowing-only, no new constant,
+`playbook_input_signature` unmoved, pinned by long- and short-side tests whose controls differ in
+exactly one number, and it prevents a real defect — a long recorded with its own invalidation
+ABOVE its entry. Two corrections to the record it was justified on: the "no recorded record
+contains a `range_trade` signal" premise is now stale (87 real `range_trade` signals sit in four
+append-only records under signature `16a2734d10c91ea7`, all written after the void was in force,
+so none is born-invalidated), and dropping the setup would therefore also move the signature and
+orphan them. `range_trade` stays in `PLAYBOOK_SETUPS`; J-06 ships unchanged.
+The Constraints clause below is NOT relaxed: a developer who finds the spec ambiguous still drops
+and surfaces rather than improvising. This ruling is a decision on one instance, not a standing
+permission — the next such clause needs its own ratification.
+
+**R-3.2 — the shipped narrower-than-spec readings are ACCEPTED as canonical, with one
+completion.** Each was disclosed by an audit, each is deterministic, and iteration 10 writes each
+into the spec so code and rulebook agree. Where the spec and the shipped code differ, the spec
+is edited to match the code — no detector logic changes — EXCEPT R-3.2(b), which adds a
+disclosure:
+
+- **(a) `double_top`/`double_bottom` pair selection.** §3.8's Caps line ("the first valid valley
+  break") is rewritten to the shipped reading: the first pivot pair, in chronological
+  `(p1, p2)` order, whose full formation validates AND triggers; mirrored in §3.9. This is a
+  choice among valid formations, not a wrong one, and 155 recorded signals ride it. Recorded
+  under this reading, they remain canonical. If the back-scan's forward distributions later give
+  cause to prefer the earliest valley break, that is a NAMED revision — it adds a discipline key
+  to `playbook_parameters()` so the signature re-keys and old records are kept beside the new,
+  never a silent logic swap under the same key.
+- **(b) `crossed_midrange` — accepted AND completed.** The shipped boolean answers only §3.7's
+  first half (did price cross the range midpoint on the approach). §3.7 is split so that half is
+  named exactly, and the missing half — whether the prior swing TURNED at midrange (the BOOK
+  midrange rule) — ships as a SECOND served disclosure field on `range_trade` geometry, with its
+  `/desk` chip. Binding constraints: spec-first (the mechanical definition is written into §3.7
+  before any code); disclosure-only (it may never gate, suppress, or create a signal); and it
+  MUST reuse an already pre-registered constant for any tolerance it needs — minting a new
+  constant would move `playbook_input_signature` for a disclosure, which this ruling does not
+  authorize. The field is optional in the served payload and in `types.ts`, so the 87 already
+  recorded `range_trade` signals stay honest by lacking it rather than being backfilled. If the
+  second half genuinely cannot be defined without a new constant, DROP it and surface that —
+  do not mint one.
+- **(c) the BOOK 1.5× jump-to-base ratio is inert, and the spec must say so.** Both §3.3 gates
+  are implemented verbatim, but `PLAYBOOK_JUMP_MIN_MULT · PLAYBOOK_BASE_MAX_RANGE_MBR`
+  (1.5 × 2.0) equals `PLAYBOOK_JUMP_MIN_MOVE_MBR` (3.0), so the ADAPTATION floor always binds
+  first and the BOOK ratio can never reject a formation on its own (min observed ratio across the
+  32 recorded `jbe`/`dbi` signals: 1.735). No number moves — moving one to "activate" the gate
+  would be threshold fitting, which stays barred. §3.3 and the `PLAYBOOK_JUMP_MIN_MULT` row of
+  the constants table record the inertness plainly so the back-scan never credits a gate that has
+  never bound.
+- **(d) the cup rim constant.** §3.6 names `PLAYBOOK_RIM_MATCH_MBR` for the left rim's
+  "within X of session-high-so-far" test, while the code reads `PLAYBOOK_NEAR_EXTREME_MBR` there
+  (the rim-to-rim test correctly uses `RIM_MATCH_MBR`). Both are 1.0, so there is no behavioral
+  difference on any input and `cup_handle` has never fired. §3.6 is edited to name
+  `PLAYBOOK_NEAR_EXTREME_MBR` for the session-high test; the detector is NOT touched. This closes
+  the latent trap where a future revision of `RIM_MATCH_MBR` would silently miss that gate.
+- **(e) the `range_trade` trigger anchor — folded in here because it was never tracked.** The
+  iteration-6 audit's finding B4 (§3.7 anchors the bounce scan on "a bar `b` touches the low
+  zone", while `_range_trade_side` anchors only on the arming-completing touch) is the same
+  species as (a)–(d) but never reached the owner-rulings list. It is ruled with them: §3.7's
+  Trigger clause is narrowed to the arming-completing touch, matching the shipped code. It is
+  fail-closed (fewer signals, never invented ones). It is named here so it cannot resurface after
+  these items close.
+
+**R-3.3 — iteration 10 is the era-closing pass.** Its scope is R-3.2's spec catch-up edits, the
+R-3.2(b) disclosure field, and the iteration-9 evaluator's carried clean-up items: rewrite
+`J-10.json`'s step 6 to assert a stable piece of shipped page furniture instead of a signature
+hash that changes whenever the fixture rig is rebuilt; re-take one `/structure` capture on data
+that actually has price bars; and run the pass at FULL depth with the auditor, which four
+iteration specs asked for and the depth arbiter demoted each time. The operator restored `:8301`
+to the real store before this resume. `Config().config_fingerprint()` stays `08e471b10130e1e2`
+and `playbook_input_signature` does not move.
+
+## Success Criteria
+
+In priority order — kept-value integrity outranks new-surface completeness outranks convenience:
+
+1. **Nothing kept regresses.** Full backend suite green (1926 pass / 8 skip at authoring —
+   iteration 0 records the era-open count; grows, never shrinks); engine equivalence proves
+   byte-identical `default` outputs; `Config().config_fingerprint()` prints `08e471b10130e1e2`
+   every iteration; every kept `/`, `/structure`, and `/desk` behavior browser-verified as
+   shipped; every guard test passes extended-not-edited (subject to R-1/R-2).
+2. **Detection is pre-registered and lookahead-clean.** Every signal is a pure function of bars
+   at or before its trigger bar plus prior-session baselines, under the named constant set of
+   [`docs/playbook-detector-spec.md`](playbook-detector-spec.md); the truncation property test
+   proves it per detector; no code path anywhere iterates thresholds against outcomes.
+3. **Measurement is the desk's own.** Convention identity with the forward rail is proven by
+   test (same horizons, sign discipline, dual-MDD semantics, truncation, seed recipe); the
+   playbook embeds the rail's shape constants in its own parameters so a rail change re-keys
+   playbook records instead of silently reinterpreting them.
+4. **The ledger is append-only and evaluable.** One record per (session date, input signature);
+   identical pins reproduce byte-identical content or reuse honestly; nothing is backfilled,
+   rewritten, or recomputed in place; absences (no bars, thin baseline, no SPY) are disclosed
+   rows, never guesses.
+5. **The playbook is a real `/desk` surface.** Signals, back-scan, and evidence sections render
+   with honest empty states, live progress, and full provenance — all browser-verified with
+   screenshots (DOM-content reveals only; no journey requires native-tooltip photography).
+6. **The playbook is Claude-operable.** `desk_playbook` and `desk_playbook_evidence` are
+   byte-identical GET proxies; the MCP suite proves the 20-tool contract.
+
+## Key Capabilities
+
+1. **Detector family + primitives (new research math, pre-registered).** A lean primitives
+   module (RTH session slice, opening range with `1m→5m` honest degradation, prior-20-session
+   MBR + per-slot volume medians, strict swing pivots, consolidation-range finder, vertical-move
+   detector, zone touches, market context) and the nine detectors + euphoria marker of the
+   canonical spec — all thresholds from the spec's single constants table, every vagueness in
+   the book resolved as ONE named, cited adaptation.
+2. **Trigger-anchored measurement on the desk's rail.** Signals measured by the forward rail's
+   own `_measure_from` at the trigger bar on the session's finest series; per-signal
+   `invalidation_breached` computed in the same pass OUTSIDE the rail helper; per (symbol,
+   setup) seeded baseline anchors with the rail's seed discipline; caps + beyond-cap disclosure.
+3. **One compute, one store.** `compute_playbook(session_date)` detects + measures in one walk
+   and records ONE frozen, checksummed, append-only record keyed
+   `(session_date, playbook_input_signature)` — the signature hashes the fine-series tuples of
+   members ∪ {SPY}, the `config_fingerprint`, and the FULL parameters blob (thresholds, setup
+   list, measurement shape), so a logic change mints new versions and can never silently reuse
+   or rewrite old ones. Compute manager trio + CLI + durable run ledger per the desk pattern;
+   `refuse_if_not_a_session` guards every compute path.
+4. **The back-scan.** `GET .../backscan/plan` (pure, metadata-only: recorded session dates ×
+   recorded-at-current-signature) and a resumable compute trio walking planned dates through the
+   ONE shared `run_playbook_and_record` entry point — per-date outcomes
+   `reused/recorded/refused_non_session/failed`, cancel on a date boundary, durable back-scan
+   ledger, host-guard-confined.
+5. **The evidence view.** `GET /research/desk/playbook/evidence` folds the newest record per
+   date AT ONE SIGNATURE into per-(setup, side) × measure distribution cells (median/p25/p75/
+   mean, `n`, `n_truncated`, `n_baseline`, `below_min_n` tags, `invalidation_breached` counts)
+   beside the pooled baseline — computed on read via a stat-keyed derived projection cache
+   (the meta-cache contract), never a snapshot store; other signatures listed, never pooled.
+6. **`/desk` playbook sections + MCP contract v4 (20 tools).** Playbook Signals (per-session
+   signal table + Run Playbook + provenance), Backscan (plan preview + trigger + progress +
+   runs), Playbook Evidence (the distribution table) — rendered BELOW the shipped sections;
+   `desk_playbook` + `desk_playbook_evidence` in `_STATIC_PATHS`; `get_endpoint`'s `/research/`
+   allowlist already reaches the parameterized reads.
+
+## Non-Goals
+
+- **No trading, no advice, no sizing.** A signal is a recorded observation. `invalidation_price`
+  is the book's structural level as a geometry disclosure — never a stop order, size, R-multiple,
+  or account concept; measured returns are never stop-adjusted (stated in the served register).
+- **No statistics program.** No CIs, p-values, nulls beyond the shipped seeded baseline, no
+  multiple-testing control, no gates, no edge/probability/expectancy language — era-6 "The
+  Referee". The min-n floor DISCLOSES (tags cells); it never filters or suppresses.
+- **No threshold fitting.** No sweep, grid, or outcome-driven iteration over detector constants
+  anywhere, ever (`docs/research-directions.md` DO-NOT #5). A mis-scaled constant is fixed by a
+  named revision in the spec + code (new signature, old records kept), never tuned.
+- **No annotation layer** (Era C). The playbook records machine output only; zero manual-input
+  write paths.
+- **No tick-data dependence.** Detection and measurement read stored 5m/1m bars only;
+  `datasets`, the engine, and the backtest/edge-report rail are untouched.
+- **No new vendor, no new symbols beyond SPY freshness.** SPY 5m/1m bars are already frozen in
+  the store; the only fetch-path change is keeping SPY fresh through the existing top-up walk.
+  `^OEX` is not fetched; no options/sentiment/news data; no paid services.
+- **No wall-screen or kept-surface work.** `desk_screen*` computation, the ranked briefing, the
+  forward rail's own behavior, cockpit, `/structure` — all as shipped. The playbook IMPORTS the
+  rail's helpers; it takes a ZERO diff to `desk_forward.py` itself.
+- **No scheduling.** Every compute is an explicit operator act; page-load GETs never compute.
+- **No fingerprint epoch bump.** Zero new Config fields expected; Path A if one is unavoidable;
+  the pin `08e471b10130e1e2` does not move.
+
+## Constraints
+
+- **Stack (carried over):** Next.js 15 + TypeScript + Tailwind v3, dark-only;
+  Python 3.12 + FastAPI; backend `:8000`, frontend `:3000` (browser-QA rig `:8301`/`:3301`);
+  no new runtime dependency (detectors are plain Python over `merged_bars`).
+- **The spec is canonical.** Formation/trigger/invalidation logic and every constant come from
+  [`docs/playbook-detector-spec.md`](playbook-detector-spec.md). A developer who finds the spec
+  ambiguous or unimplementable for a detector DROPS that detector from the iteration, records
+  the drop, and surfaces it for an owner ruling — never improvises a rule (the spec's
+  range_trade is already marked PROVISIONAL for exactly this reason).
+- **Parameters discipline (the `desk_forward` pattern, applied at birth):**
+  `playbook_parameters()` reads every constant at call time and embeds the rail's horizon/
+  measure/seed constants; `compute_playbook_input_signature` hashes sorted
+  `(symbol, timeframe, series_id, checksum)` tuples for (members ∪ {SPY}) × `("1m","5m")` +
+  `config_fingerprint` + the canonical parameters blob (`sha256[:16]`, metadata-only via
+  `list(include_bars=False)`). The parameters blob is embedded verbatim in every payload
+  (provenance duty). A monkeypatched constant must move the parameters AND the signature
+  (counter-tested).
+- **Store discipline:** frozen, checksummed, append-only JSON records; record id = pure
+  function of the 2-pin key; duplicate key raises; a corrupt file at a key's path is surfaced,
+  never overwritten; NO supersede/prune path exists in v1 (versions kept and counted;
+  `newest_for_date` + `versions` served). Storage dirs are env-var-or-sibling defaults
+  (`TAPEOLOGY_DESK_PLAYBOOK_DIR`, `_LOG_DIR`, `_BACKSCAN_LOG_DIR` — deliberately NOT Config
+  fields). The evidence projection cache follows the `desk_meta_cache` contract: derived,
+  stat-keyed, rebuildable, owns nothing, unopenable = missing optimisation never a failed read.
+- **Lookahead law (bar granularity):** formation conditions read bars strictly before the
+  trigger bar (pivots wait out their confirmation window; fail-closed); the trigger predicate
+  uses only the price-crossing fact; trigger-bar volume/close are disclosures, never gates;
+  baselines are prior-sessions-only; market context reads SPY strictly before the trigger
+  epoch. The generic truncation property test (truncate the series after the trigger; mutate
+  post-trigger bars) covers every detector and every fixture.
+- **Session honesty:** every compute path calls `desk_sessions.refuse_if_not_a_session`
+  (`app/research/desk_sessions.py:180`); the back-scan planner draws only from
+  `recorded_session_dates` (:129); a session with no 5m bars, MBR = 0, or a thin baseline is a
+  disclosed absence, never a guess and never a crash.
+- **Measurement convention identity:** the playbook imports the rail's helpers
+  (`_session_slice` :295, `_measure_from` :451, `_draw_anchor_indices` :428, the averaging
+  helpers) rather than copying them; a convention-identity test proves a synthetic anchor
+  measures byte-identically through both paths; `invalidation_breached` is computed OUTSIDE
+  `_measure_from` so the rail's served shape never changes and no recorded forward record
+  re-keys.
+- **Copy discipline:** all playbook copy is descriptive measurement; the served
+  `PLAYBOOK_REGISTER` and `EVIDENCE_REGISTER` sentences state what was measured and what was
+  NOT (no fills, no costs, returns not stop-adjusted, baseline = seeded random anchors);
+  `tests/test_copy_discipline.py` covers the new page copy and registers unmodified.
+- **Guard tests are extended, never edited:** `tests/test_desk_ui_guards.py`'s
+  `_PRICE_ARITHMETIC_FIELDS` (:152) gains every new served numeric the UI renders (+ seeded
+  counter-test additions); `tests/test_desk_refresh_chain_guard.py`'s
+  `_EXPECTED_EFFECT_COUNT = 15` (:104) is re-derived deliberately with the mandatory rationale
+  paragraph and `_TRIGGER_CALLS` additions; `test_no_execution_path.py`,
+  `test_no_credential_in_artifacts.py`, the chart guards, and the 13 pin assertions pass
+  byte-unmodified.
+- **Hermetic tests:** keyless on committed fixtures (synthetic bar sessions per detector:
+  one canonical firing fixture + one near-miss that must NOT fire); no test fetches the
+  network; the real back-scan is an operator-run act reported run-or-not-run, never a CI gate.
+- **Browser evidence:** `rm -rf apps/frontend/.next` + rebuild before any browser pass (T-9);
+  every browser acceptance needs a screenshot — none ⇒ `unknown`, never `passing` (T-10); all
+  playbook UI acceptance uses DOM-content reveals only — no native `title` tooltips required
+  by any journey (the T-10a rig stays available but unneeded).
+- **Compute-manager reuse:** the playbook compute and back-scan follow the shipped desk
+  manager pattern (single-flight, snapshot-pollable progress, cancel, CLI-runnable, one shared
+  `run_*_and_record` writer, terminal-state-only ledger writes); page-load GETs never trigger
+  computes.
+
+## Design Direction
+
+Unchanged house style: dark-only, dense, professional, terminal-grade; honest empty/degraded
+states are first-class copy (`"Playbook not computed for this session."`,
+`"no signals: baseline too thin"`); the signals table reads like a session log, not a
+recommendation feed; setup names are the book's own; no marketing chrome.
+
+## Product Shape
+
+Nav unchanged: **Cockpit `/` · Structure `/structure` · Desk `/desk`** (`app/meta.py`
+`UI_ROUTES` untouched). The playbook adds three sections to `/desk`, rendered BELOW the shipped
+sections.
+
+**Data Contract — new rows (each value computed once, one owner):**
+
+| Value | Owner (module) | Serving endpoint |
+|---|---|---|
+| Playbook records (signals + measurements + baseline + summary) | new `app/research/desk_playbook.py` | `GET /research/desk/playbook` (`?date=`, `?id=`) |
+| Playbook compute progress | new playbook compute manager | `POST/GET/POST-cancel /research/desk/playbook/compute` |
+| Playbook run ledger | new `app/research/desk_playbook_log.py` | `GET /research/desk/playbook/runs` |
+| Back-scan plan | new `app/research/desk_playbook_backscan.py` | `GET /research/desk/playbook/backscan/plan` |
+| Back-scan progress + ledger | same back-scan module | `POST/GET/POST-cancel .../backscan/compute`, `GET .../backscan/runs` |
+| Evidence aggregates | new `app/research/desk_playbook_evidence.py` | `GET /research/desk/playbook/evidence` |
+
+**Unchanged owners (the playbook reads them verbatim):** bars/candles → `bars.py`
+(`merged_bars` :883) + `bar_index`; session honesty → `desk_sessions.py`; measurement helpers →
... [diff_bound] docs/goal-archive/goal-2026-08-14.md: 547 more diff lines omitted — Read the file for full detail
diff --git a/docs/goal.md b/docs/goal.md
index f6af075..cea64cf 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1,858 +1,740 @@
-# Tapeology — Project Goal (Era B2: The Playbook — the book's intraday setups, detected on the desk's own bars and measured forward)
+# Tapeology — Project Goal (Era 6: The Referee — the statistics that try to disprove our own evidence)
 
-> Eras 1–5D and Era B are the **foundation** of this goal. Eras 1–2 (tape reading + the research
-> evolution, GOAL_ACHIEVED) are archived at
+> Eras 1–5D, B, and B2 are the **foundation** of this goal. Eras 1–2 are archived at
 > [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md); the structure-UI
 > interlude at [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md);
 > **Era 5 "The Library"** at [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md);
 > the **"Fast Wall" interlude** at [`docs/goal-archive/goal-2026-07-17.md`](goal-archive/goal-2026-07-17.md);
 > the **"Clean Slate" demolition** at [`docs/goal-archive/goal-2026-07-25.md`](goal-archive/goal-2026-07-25.md);
-> and **Era B "The Desk" (GOAL_ACHIEVED 2026-07-31, session `desk`, journeys J-01–J-21)** at
-> [`docs/goal-archive/goal-2026-08-10.md`](goal-archive/goal-2026-08-10.md). Eras 3, 4, 5B, and 5C
-> are frozen foundation; their records live in git history and `reports/goal-session-*-delivered.md`.
+> **Era B "The Desk"** at [`docs/goal-archive/goal-2026-08-10.md`](goal-archive/goal-2026-08-10.md);
+> and **Era B2 "The Playbook" (GOAL_ACHIEVED 2026-08-11, session `playbook`, J-01–J-12)** at
+> [`docs/goal-archive/goal-2026-08-14.md`](goal-archive/goal-2026-08-14.md). Eras 3, 4, 5B, and
+> 5C are frozen foundation; their records live in git history and `reports/`.
 >
-> **This chapter is Era B2 of the operator's pivot (A Demolition → B Desk → B2 Playbook → C
-> Annotator).** The product today is exactly **Cockpit (`/`) + Structure (`/structure`) + Desk
-> (`/desk`)**, the fingerprint epoch is `08e471b10130e1e2`, the MCP surface is **18 read-only
-> tools**, and the honesty machinery (stores, gates, registry, PnL promotion ledger) is fully
-> intact. B2 is a BUILDING era on the desk's ground: it teaches the desk the intraday setups of
-> the book the project is named for — Graifer & Schumacher, *Techniques of Tape Reading* (2004) —
-> detected on the desk's own recorded 5m/1m bars and measured with the desk's own forward-return
-> + max-drawdown conventions. It is an operator-directed product era OUTSIDE the research catalog
-> ([`docs/research-directions.md`](research-directions.md) has no Playbook card; per its §5.6 this
-> file wins for the running era). The statistics program (era-6 "The Referee") and the annotation
-> corpus (Era C) remain SEPARATE future chapters — nothing of them lands here.
+> **This chapter is Era 6 of the research catalog — "The Referee"
+> ([`docs/research-directions.md`](research-directions.md) §504), opened under §5.6 (goal.md
+> wins for the running era) with the catalog reconciled in this era's opening commit.** The
+> product today is exactly **Cockpit (`/`) + Structure (`/structure`) + Desk (`/desk`)**, the
+> fingerprint epoch is `08e471b10130e1e2`, the MCP surface is **20 read-only tools**, and the
+> honesty machinery (stores, gates, registry, PnL promotion ledger) is fully intact. Era 6 is a
+> BUILDING era on top of two frozen evidence families: it adds Tapeology's first **inferential
+> statistics program** — an adjudication layer that tries to DISPROVE the evidence the desk has
+> recorded, and that can say "no edge" confidently instead of manufacturing one from noise.
 >
-> **Unlike Era B, this era DOES add new research math** — a family of pre-registered bar-pattern
-> detectors and their trigger-anchored measurements — under two hard disciplines: (1) every
-> detector rule and threshold is fixed in advance in
-> [`docs/playbook-detector-spec.md`](playbook-detector-spec.md) (the canonical spec; developers
-> implement from it, never re-derive or re-tune — a threshold change is a named revision that
-> re-keys future records, never a sweep); (2) every measurement reuses the desk forward rail's
-> own conventions verbatim. It adds **zero statistics gates** and **zero annotation surfaces**.
+> **This era adds exactly one new research discipline — calibrated statistics — under two hard
+> rails:** (1) every statistical constant, null definition, test procedure, estimand, and
+> verdict rule is fixed in advance in
+> [`docs/referee-statistical-spec.md`](referee-statistical-spec.md) (the canonical spec;
+> developers implement from it, never re-derive or re-tune — a change is a named revision that
+> re-keys future results, never a sweep); (2) the Referee is READ-SIDE over the recorded
+> corpus: it never writes to, re-keys, or reinterprets any existing record, and it never feeds
+> back into detectors, context, or thresholds. The Playbook detector family and the
+> `playbook-band-context-v3` context revision are FROZEN research vocabulary for this whole
+> era (genuine bug fixes excepted, each its own named revision).
 
 ## Vision
 
-Era B gave the operator a desk: universe in, wall-screen briefing out, every record append-only
-and evaluable. But the desk still reads only structure — it knows where the walls are, not what
-the tape is DOING. The book this project is named for describes exactly that missing layer: an
-intraday grammar of price/volume behavior (six principles, a handful of named setups) that has
-never been encoded, let alone measured. Era B2 builds it as evidence, not advice:
-
-1. **A pre-registered playbook of the book's intraday setups.** For any recorded session, a
-   detector family — open-high/open-low-break, jump-base-explosion (JBE) / drop-base-implosion
-   (DBI), capitulation (+ euphoria marker), cup-and-handle, range trades, double top/bottom —
-   walks each member's RTH 5m bars (1m bars for the opening range) and emits signals:
-   `{symbol, setup_id, side, trigger price/time, invalidation_price, geometry, volume character,
-   market context, principles}`. Formation logic is lookahead-clean at bar granularity; every
-   threshold is a named constant from the canonical spec, tagged BOOK or ADAPTATION.
-2. **Every signal measured the desk's own way.** Each signal carries a trigger-anchored
-   measurement produced by the SAME conventions as the desk forward rail: horizons +1m/+5m/+1h/
-   +4h/to-close as trading-bar counts on the session's finest series, side-signed returns, dual
-   max drawdown clamped ≤ 0, truncation honesty, and a seeded random-anchor baseline of the same
-   session — plus an `invalidation_breached` disclosure (did price trade through the book's
-   structural level; returns are never stop-adjusted).
-3. **A back-scan that turns the book into a ledger.** One resumable operator act walks EVERY
-   recorded session with 5m coverage (~45 sessions × ~101 members at authoring; the store is
-   append-only so this grows daily), recording one append-only playbook record per
-   (session date, input signature) — reusing recorded work on re-run, chunked by session,
-   host-guard-confined.
-4. **An evidence view that says what happened, with n.** Per setup × side × horizon: the pooled
-   forward-return and MDD distributions of every recorded signal beside the pooled baseline
-   anchors — median/quartiles/mean, `n`, `n_truncated`, `n_baseline`, low-n tags below a named
-   disclosure floor. Descriptive distribution language only; no probability, expectancy, edge,
-   or significance claims — those gates are era-6's.
-
-The deliverable: the desk learns to read the tape the way the book teaches, writes down every
-signal it would have seen, measures what price then did against chance anchors, and shows the
-distributions honestly — every number owned once, every run explicit, every record append-only.
+Era B2 taught the desk to read the tape the way the book teaches and to write every signal
+down with honest descriptive distributions. The operator has looked at those tables — 270
+evidence cells, 1,080 band-context cells, the cohort views — and seen patterns worth taking
+seriously: range trades at a wall, capitulation snapbacks. But a pattern in an inspected table
+is a hypothesis, not a finding, and today Tapeology has NO machinery that can tell the two
+apart: no confidence interval, no calibrated p-value, no multiple-testing control, no
+dependence-aware uncertainty, no pre-registration, and no vocabulary for "we looked, and there
+is nothing here". Era 6 builds that machinery — the Referee:
+
+1. **One evidence contract, two families.** A typed read-side observation contract that carries
+   Playbook occurrences (bar-measured forward returns, session-clustered) and strategy/backtest
+   trades (net-R, dataset-clustered) into ONE shared statistical layer through per-family
+   adapters — preserving each family's semantics and provenance, forcing neither to pretend to
+   be the other.
+2. **Statistics that are calibrated, or refuse to speak.** Seeded bootstrap confidence
+   intervals (occurrence-level AND session-clustered, always side by side); formal p-values
+   from within-session randomization tests whose null distribution is constructed under H0 by
+   design; Benjamini–Hochberg over pre-registered families with the planned count as the
+   denominator; every procedure proven by seeded oracles with known answers — and a fail-closed
+   attestation: statistics whose oracle cannot be reproduced never emit a confirmatory verdict.
+3. **Nulls that are matched, not convenient.** The shipped seeded same-session anchors stay as
+   the descriptive baseline; the Referee adds time-of-day-matched nulls (and context-matched
+   nulls for combined claims) measured through the identical forward rail with
+   remaining-time-matched eligibility — so "beats chance" means "beats chance at comparable
+   times under identical measurement", not "beats a strawman".
+4. **Pre-registration with an immutable boundary.** An append-only registry of hypothesis
+   families where every candidate is written down BEFORE its confirmation data exists; the
+   historical atlas is exploratory forever; confirmation counts only sessions strictly after
+   the registration boundary; one confirmatory checkpoint per hypothesis, recorded as an
+   append-only snapshot no later evaluation can change.
+5. **A verdict vocabulary where "corroborated" is earned.** Registered → pending →
+   insufficient_sample / fragile / no_evidence / corroborated / killed — each a pure function
+   of recorded facts; a positive mean, a beaten baseline, or an ordinary bootstrap CI excluding
+   zero is NEVER enough. And the champion promotion gate gains a fail-closed interlock: no
+   strategy candidate can ever be promoted again without a valid, candidate-specific Referee
+   certificate.
+
+The deliverable: Tapeology moves from a system that can generate plausible tape-reading
+evidence to a system that can rigorously try to disprove it — and whose "no edge" is as
+trustworthy as any "edge" it will ever claim.
 
 ## Target Users
 
-- The project owner (a discretionary intraday trader) who opens `/desk`, runs the playbook for a
-  session, reads the signals beside the wall briefing, and reads the evidence table to learn
-  which of the book's setups his own data supports.
-- The same owner operating through **Claude + MCP**: `desk_playbook` / `desk_playbook_evidence`
-  (plus the existing 18 tools) make the playbook readable from a conversation end to end.
+- The project owner (a discretionary intraday trader) who reads the shortlist, approves 2–3
+  starter hypotheses through the real registration act, runs evaluations as sessions accrue,
+  and reads verdicts on `/desk` — knowing every verdict survived the full gauntlet or says
+  honestly why it cannot yet speak.
+- The same owner operating through **Claude + MCP**: `desk_referee` /
+  `desk_referee_registry` (plus the existing 20 tools) make the registry and adjudications
+  readable from a conversation end to end.
 - AI dev-chain agents (the goal-mode chain) building and browser-verifying the era.
 
-## Foundation invariants (still law — eras 1–5D and B)
+## Foundation invariants (still law — eras 1–5D, B, B2, and the R-4 interlude)
 
 The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md))
 remains binding on all KEPT code — price-impact-over-aggression; honest uncertainty; **no
 fabricated data**; single source of truth; no magic numbers; provider-agnostic engine;
 deterministic & reproducible; no secrets in source; research read-only over the engine; record
-integrity; source/feed/`config_fingerprint` honesty. The surface inventory is the post-Era-B
-one: `/`, `/structure`, and `/desk` (this era adds sections to `/desk`, no new route).
+integrity; source/feed/`config_fingerprint` honesty. The surface inventory is the post-B2 one:
+`/`, `/structure`, and `/desk` (this era adds sections to `/desk`, no new route).
 
 1. The **tape engine** (`app/engine/`) emits byte-identical output under `default` on identical
    inputs. `config_fingerprint` stays **`08e471b10130e1e2`** for this WHOLE era. This era needs
-   **zero new `Config` fields** (the `desk_forward` precedent: playbook thresholds are module
-   constants hashed into the record's own input signature); if the build genuinely needs one, it
-   takes §0.4 **Path A** (exclusion + stability test + counter-test) — a pin movement is a
-   defect, full stop.
-2. The **research computations** — `levels.py`, `tradability.py` (+cache), `setups.py` (+scan
-   cache), `edge_report*.py`, `backtests.py`, the strategy registry, `profiles.py` (`default`),
-   the champion pointer — stay behaviorally byte-identical. The playbook READS bars; it never
-   touches, re-implements, or re-tunes any of them.
+   **zero new `Config` fields** (the `desk_forward`/playbook precedent: every referee constant
+   is a module constant embedded in `referee_parameters()` and hashed into referee result
+   identities); if the build genuinely needs one, it takes §0.4 **Path A** (exclusion +
+   stability test + counter-test) — a pin movement is a defect, full stop.
+2. The **frozen research vocabulary**: the nine Playbook detectors, all 42+6 spec constants,
+   `playbook_input_signature`, the band-context revision `playbook-band-context-v3`, the cohort
+   vocabulary `playbook-cohort-v1`, `levels.py`/`tradability.py`/`setups.py`/`edge_report*.py`/
+   `backtests.py`/the strategy registry/`profiles.py`/the champion pointer — all behaviorally
+   byte-identical. The Referee READS them; it never touches, re-implements, re-tunes, or feeds
+   back into any of them. **The one deliberate exception, in inventory:** `pnl_scan.py` gains
+   the J-08 promotion interlock (authorization before any write; everything else
+   byte-compatible).
 3. The **stores** — `BarStore` + `DatasetStore` formats, checksums, append-only immutability,
-   split freezing, the durable accelerator DBs, the Era-B universe/screen/forward stores and
-   their run ledgers — are untouched in format and discipline. The era ADDS a playbook store
-   (and its run ledgers + a derived evidence projection cache) under the same discipline.
-4. The **PnL promotion ledger** stays append-only and intact; the champion pointer does not move.
+   frozen splits, the accelerator DBs, the desk universe/screen/forward stores, the playbook
+   store and its ledgers — are untouched in format and discipline. The era ADDS the referee
+   store family (registry, nulls, evaluations, adjudication snapshots, run ledgers + one
+   derived observation cache) under the same discipline.
+4. The **PnL promotion ledger** stays append-only and intact; the champion pointer does not
+   move this era — and after J-08 it CANNOT move without a valid Referee certificate.
 5. The **kept surfaces as shipped**: the cockpit, `/structure`, and every shipped `/desk`
-   section (screen history calendar, forward returns, refresh chain + compute controls, ranked
-   briefing, skipped members, runs/pins/compare/provenance sections) keep working exactly as
-   shipped. The playbook lands as NEW sections below the shipped ones; no shipped `/desk`
-   section, column, or behavior changes.
+   section (including all Playbook sections, the band-context columns, filters, and cohort
+   views) keep working exactly as shipped. Referee sections land as NEW sections below the
+   shipped ones; no shipped section, column, or behavior changes.
 6. The **read-only MCP server** keeps its byte-identical GET-proxy contract; this era adds two
-   GET-proxy tools (**18 → 20**) and never adds writes.
+   GET-proxy tools (**20 → 22**) and never adds writes.
 
 ### OWNER RATIFICATION — carried and new
 
-**R-1 (2026-07-27, price-less-bar repair)** — ratified in Era B (see the archived goal's R-1
-block for the eight-file inventory); it remains ratified history and its terms carry forward
-unchanged.
-
-**R-2 (2026-08-10, the post-Era-B forward-test interlude) — ratified and IN INVENTORY for this
-era.** Between Era B's GOAL_ACHIEVED (iteration 36, commit `94eb1b0`) and this era's opening,
-the operator's interactive sessions landed a body of desk work no Era-B journey describes. It is
-ratified as foundation, comprising the `goal/desk` commits after `94eb1b0` through the era-open
-tip (including the operator's pre-era commit of the 2026-08-07/09 working tree — 14 modified
-files + `desk_meta_cache.py`/`test_desk_meta_cache.py`; iteration 0 records the era-open SHA):
-
-- `app/research/desk_forward.py` + `desk_forward_compute.py` + `desk_forward_log.py` +
-  `desk_forward_pins.py` — the touch-anchored forward-return v2 rail (horizons/dual-MDD/seeded
-  baseline/2-pin append-only `ForwardStore`) and its manager, ledger, and pins;
-- `app/research/desk_sessions.py` — recorded-session honesty (screen only real sessions);
-- `app/research/desk_screen_decision.py` + `desk_screen_cleanup.py` — one-snapshot-per-date
-  reuse/record/replace semantics and the operator cleanup path;
-- `app/research/desk_deep_backfill.py` — the chunked, resumable fine-bar (1m/5m) deep-backfill
-  quartet and its Alpaca vendor seam;
-- `app/research/desk_meta_cache.py` — the derived, rebuildable screen/forward meta-projection
-  cache (stat-keyed, owns nothing);
-- the desk refresh/screen/forward performance work, the ET time convention on desk surfaces, and
-  the fine-timeframe top-up walk (`DESK_TOPUP_FINE_TIMEFRAMES`).
-
-Where clauses below say "untouched", "byte-unmodified", or "out-of-inventory", they are read
-subject to **R-1** and **R-2**.
-
-**R-3 (2026-08-11, the playbook spec rulings) — ratified.** Iterations 6–9 surfaced two open
-"The spec is canonical" items and halted the session STALLED awaiting them. Both are ruled here.
-This block is the ruling; the spec edits it directs are iteration-10 developer work (the same
-shape as iteration 6's §3.5 doc-only closure), not a licence to change detector behavior beyond
-what is named below.
-
-**R-3.1 — the `range_trade` "degenerate trigger reference" clause is RATIFIED as written.**
-The dated clarification in `docs/playbook-detector-spec.md` §3.7 Edge cases, and the matching
-fail-closed void in `_range_trade_side` (`T ≤ SL` long / `T ≥ SH` short emits nothing and the walk
-continues), stand as canonical. It is ratified on its merits: narrowing-only, no new constant,
-`playbook_input_signature` unmoved, pinned by long- and short-side tests whose controls differ in
-exactly one number, and it prevents a real defect — a long recorded with its own invalidation
-ABOVE its entry. Two corrections to the record it was justified on: the "no recorded record
-contains a `range_trade` signal" premise is now stale (87 real `range_trade` signals sit in four
-append-only records under signature `16a2734d10c91ea7`, all written after the void was in force,
-so none is born-invalidated), and dropping the setup would therefore also move the signature and
-orphan them. `range_trade` stays in `PLAYBOOK_SETUPS`; J-06 ships unchanged.
-The Constraints clause below is NOT relaxed: a developer who finds the spec ambiguous still drops
-and surfaces rather than improvising. This ruling is a decision on one instance, not a standing
-permission — the next such clause needs its own ratification.
-
-**R-3.2 — the shipped narrower-than-spec readings are ACCEPTED as canonical, with one
-completion.** Each was disclosed by an audit, each is deterministic, and iteration 10 writes each
-into the spec so code and rulebook agree. Where the spec and the shipped code differ, the spec
-is edited to match the code — no detector logic changes — EXCEPT R-3.2(b), which adds a
-disclosure:
-
-- **(a) `double_top`/`double_bottom` pair selection.** §3.8's Caps line ("the first valid valley
-  break") is rewritten to the shipped reading: the first pivot pair, in chronological
-  `(p1, p2)` order, whose full formation validates AND triggers; mirrored in §3.9. This is a
-  choice among valid formations, not a wrong one, and 155 recorded signals ride it. Recorded
-  under this reading, they remain canonical. If the back-scan's forward distributions later give
-  cause to prefer the earliest valley break, that is a NAMED revision — it adds a discipline key
-  to `playbook_parameters()` so the signature re-keys and old records are kept beside the new,
-  never a silent logic swap under the same key.
-- **(b) `crossed_midrange` — accepted AND completed.** The shipped boolean answers only §3.7's
-  first half (did price cross the range midpoint on the approach). §3.7 is split so that half is
-  named exactly, and the missing half — whether the prior swing TURNED at midrange (the BOOK
-  midrange rule) — ships as a SECOND served disclosure field on `range_trade` geometry, with its
-  `/desk` chip. Binding constraints: spec-first (the mechanical definition is written into §3.7
-  before any code); disclosure-only (it may never gate, suppress, or create a signal); and it
-  MUST reuse an already pre-registered constant for any tolerance it needs — minting a new
-  constant would move `playbook_input_signature` for a disclosure, which this ruling does not
-  authorize. The field is optional in the served payload and in `types.ts`, so the 87 already
-  recorded `range_trade` signals stay honest by lacking it rather than being backfilled. If the
-  second half genuinely cannot be defined without a new constant, DROP it and surface that —
-  do not mint one.
-- **(c) the BOOK 1.5× jump-to-base ratio is inert, and the spec must say so.** Both §3.3 gates
-  are implemented verbatim, but `PLAYBOOK_JUMP_MIN_MULT · PLAYBOOK_BASE_MAX_RANGE_MBR`
-  (1.5 × 2.0) equals `PLAYBOOK_JUMP_MIN_MOVE_MBR` (3.0), so the ADAPTATION floor always binds
-  first and the BOOK ratio can never reject a formation on its own (min observed ratio across the
-  32 recorded `jbe`/`dbi` signals: 1.735). No number moves — moving one to "activate" the gate
-  would be threshold fitting, which stays barred. §3.3 and the `PLAYBOOK_JUMP_MIN_MULT` row of
-  the constants table record the inertness plainly so the back-scan never credits a gate that has
-  never bound.
-- **(d) the cup rim constant.** §3.6 names `PLAYBOOK_RIM_MATCH_MBR` for the left rim's
-  "within X of session-high-so-far" test, while the code reads `PLAYBOOK_NEAR_EXTREME_MBR` there
-  (the rim-to-rim test correctly uses `RIM_MATCH_MBR`). Both are 1.0, so there is no behavioral
-  difference on any input and `cup_handle` has never fired. §3.6 is edited to name
-  `PLAYBOOK_NEAR_EXTREME_MBR` for the session-high test; the detector is NOT touched. This closes
-  the latent trap where a future revision of `RIM_MATCH_MBR` would silently miss that gate.
-- **(e) the `range_trade` trigger anchor — folded in here because it was never tracked.** The
-  iteration-6 audit's finding B4 (§3.7 anchors the bounce scan on "a bar `b` touches the low
-  zone", while `_range_trade_side` anchors only on the arming-completing touch) is the same
-  species as (a)–(d) but never reached the owner-rulings list. It is ruled with them: §3.7's
-  Trigger clause is narrowed to the arming-completing touch, matching the shipped code. It is
-  fail-closed (fewer signals, never invented ones). It is named here so it cannot resurface after
-  these items close.
-
-**R-3.3 — iteration 10 is the era-closing pass.** Its scope is R-3.2's spec catch-up edits, the
-R-3.2(b) disclosure field, and the iteration-9 evaluator's carried clean-up items: rewrite
-`J-10.json`'s step 6 to assert a stable piece of shipped page furniture instead of a signature
-hash that changes whenever the fixture rig is rebuilt; re-take one `/structure` capture on data
-that actually has price bars; and run the pass at FULL depth with the auditor, which four
-iteration specs asked for and the depth arbiter demoted each time. The operator restored `:8301`
-to the real store before this resume. `Config().config_fingerprint()` stays `08e471b10130e1e2`
-and `playbook_input_signature` does not move.
+**R-1 (2026-07-27, price-less-bar repair)**, **R-2 (2026-08-10, the post-Era-B interlude)**,
+and **R-3 (2026-08-11, the playbook spec rulings R-3.1–R-3.3)** remain ratified history; their
+terms carry forward unchanged (see the archived B2 goal for their full text).
+
+**R-4 (2026-08-14, the post-B2 band-context interlude) — ratified and IN INVENTORY for this
+era.** Between B2's GOAL_ACHIEVED (iteration 12, `0ab5a11`) and this era's opening, the
+operator's interactive sessions landed a body of Playbook work no B2 journey describes. It is
+ratified as foundation, comprising the eleven `main` commits `9e65bb0` → `83c24a8`:
+
+- `app/research/desk_playbook_context.py` — the band-context read-side lens (v1 → v2 bracket
+  frame → v3 basis-bounded cache key; `PLAYBOOK_CONTEXT_ALGORITHM_VERSION =
+  "playbook-band-context-v3"`), its cache, warmer CLI, and
+  `GET /research/desk/playbook/context`;
+- `app/research/desk_playbook_cohort.py` — the 9-key cohort vocabulary
+  (`playbook-cohort-v1`) and the `?cohorts=true` read;
+- the refresh-chain steps 6–7 (playbook detection + back-scan inside the desk refresh);
+- the occurrence expansion + `geometry.anchors` persistence + chart shape drill-ins (a named
+  signature re-key, old records kept);
+- the `/desk` surfacing: context columns (trade-relative BEHIND/AHEAD), near-band and
+  inside/not-inside filters, sort/collapse primitives, screen-history → playbook date link;
+- `docs/playbook-detector-spec.md` §6 (band context) and §7 (cohorts).
+
+Where clauses below say "untouched", "as shipped", or "out-of-inventory", they are read
+subject to **R-1, R-2, R-3, and R-4**.
 
 ## Success Criteria
 
-In priority order — kept-value integrity outranks new-surface completeness outranks convenience:
+In priority order — kept-value integrity outranks machinery completeness outranks surface
+convenience:
 
-1. **Nothing kept regresses.** Full backend suite green (1926 pass / 8 skip at authoring —
+1. **Nothing kept regresses.** Full backend suite green (2,418 pass / 8 skip at authoring —
    iteration 0 records the era-open count; grows, never shrinks); engine equivalence proves
    byte-identical `default` outputs; `Config().config_fingerprint()` prints `08e471b10130e1e2`
    every iteration; every kept `/`, `/structure`, and `/desk` behavior browser-verified as
-   shipped; every guard test passes extended-not-edited (subject to R-1/R-2).
-2. **Detection is pre-registered and lookahead-clean.** Every signal is a pure function of bars
-   at or before its trigger bar plus prior-session baselines, under the named constant set of
-   [`docs/playbook-detector-spec.md`](playbook-detector-spec.md); the truncation property test
-   proves it per detector; no code path anywhere iterates thresholds against outcomes.
-3. **Measurement is the desk's own.** Convention identity with the forward rail is proven by
-   test (same horizons, sign discipline, dual-MDD semantics, truncation, seed recipe); the
-   playbook embeds the rail's shape constants in its own parameters so a rail change re-keys
-   playbook records instead of silently reinterpreting them.
-4. **The ledger is append-only and evaluable.** One record per (session date, input signature);
-   identical pins reproduce byte-identical content or reuse honestly; nothing is backfilled,
-   rewritten, or recomputed in place; absences (no bars, thin baseline, no SPY) are disclosed
-   rows, never guesses.
-5. **The playbook is a real `/desk` surface.** Signals, back-scan, and evidence sections render
-   with honest empty states, live progress, and full provenance — all browser-verified with
-   screenshots (DOM-content reveals only; no journey requires native-tooltip photography).
-6. **The playbook is Claude-operable.** `desk_playbook` and `desk_playbook_evidence` are
-   byte-identical GET proxies; the MCP suite proves the 20-tool contract.
+   shipped; every guard test passes extended-not-edited (subject to R-1/R-2/R-4 and the J-08
+   enumerated pnl_scan amendments); every previously recorded store file byte-identical
+   (SHA-256 listings).
+2. **The statistics are proven, or silent.** Every statistical procedure passes its seeded
+   oracle suite (null calibration on iid-skewed, heavy-tailed, AND session-clustered
+   generators; the demonstrated failure cases; power; BH sweep; CI coverage) within its
+   pre-registered runtime budget; evaluation records carry a pass attestation; adjudication
+   refuses confirmatory output without a matching attestation (fail closed, honestly served).
+3. **Exploratory and confirmatory never mix.** The historical atlas is served as exploratory
+   forever; confirmation pools contain only completed-session records with `session_date`
+   strictly after the hypothesis's registered boundary (deep-backfilled older dates can never
+   enter — counter-tested); the BH denominator is the registered planned count; one
+   confirmatory checkpoint per hypothesis, recorded append-only, immutable under later
+   evaluations.
+4. **Every number is reproducible from append-only records.** Registry, null, evaluation, and
+   adjudication-snapshot records are frozen, checksummed, append-only; `evaluation_basis`
+   content-hashes the exact evaluated inputs (record ids + coverage, null records, spec ids,
+   seeds, stats-core version); identical stores fold to byte-identical served bodies.
+5. **The starter family is real and clean.** The shortlist is served with live readiness; 2–3
+   hypotheses are registered through the real registration act with explicit operator
+   approval, `origin: "historical-exploration"` labels, one semantically-chosen primary
+   (measure, horizon) each, and estimand coverage per the shortlist constraints; their
+   confirmation state contains zero-or-only genuinely post-boundary sessions at era end — an
+   era ending with every real verdict `registered`/`pending_forward_confirmation` and ZERO
+   `corroborated` is the system working, not a failure.
+6. **Promotion is interlocked.** `pnl_scan` promotion requires a valid candidate-specific
+   Referee certificate and refuses closed on absent/stale/mismatched/malformed/failed-gates —
+   with no bypass of any kind — while sweep computation, survivor labelling, and reports keep
... [diff_bound] docs/goal.md: 1269 more diff lines omitted — Read the file for full detail
diff --git a/docs/playbook-detector-spec.md b/docs/playbook-detector-spec.md
index 5ddc41c..52f5ce0 100644
--- a/docs/playbook-detector-spec.md
+++ b/docs/playbook-detector-spec.md
@@ -432,14 +432,21 @@ back-scan — validation may DEMOTE a detector in a named revision, never tune c
 
 ---
 
-## 6. Band context (v2 — the bracket frame; read-side lens, never part of a record or its signature)
-
-> **Supersession.** §6 v2 (`playbook-band-context-v2`) replaces the v1 nearest-band lens shipped
-> 2026-08-12, which reported the nearest band in ANY direction plus an `aligned`/`opposed` label.
-> That frame could call a trade with no structure within 300 bps "aligned" with a wall it had no
-> relationship to, and never named which band it meant. v1's full text remains in git history; the
-> algorithm-version constant is the version pointer. No recorded byte, no `playbook_input_signature`,
-> and no detector changed in either direction.
+## 6. Band context (v3 — the bracket frame; read-side lens, never part of a record or its signature)
+
+> **Supersession.** §6's frame (the bracket) is v2's; the shipped constant is
+> `playbook-band-context-v3`. v2 (`playbook-band-context-v2`) replaced the v1 nearest-band lens
+> shipped 2026-08-12, which reported the nearest band in ANY direction plus an `aligned`/`opposed`
+> label — a frame that could call a trade with no structure within 300 bps "aligned" with a wall it
+> had no relationship to, and never named which band it meant. **v3 (commit `62db2ad`) changed ONLY
+> the cache keying** — basis-bounded invalidation (see "Cache invalidation is basis-bounded (v3)"
+> below) — so a daily top-up no longer invalidates the whole corpus; every distance, bucket, and
+> caption rule in this section is unchanged from v2. Full prior texts remain in git history; the
+> algorithm-version constant is the version pointer. No recorded byte, no
+> `playbook_input_signature`, and no detector changed in any of these revisions. *(Version string
+> reconciled to the shipped code at the era-6 opening, 2026-08-14 — doc catch-up only; the guard
+> test in `tests/test_referee_guards.py` pins this heading and the constant line to
+> `PLAYBOOK_CONTEXT_ALGORITHM_VERSION`.)*
 
 Frames every ALREADY-RECORDED signal (and every baseline anchor drawn beside one) against the desk's
 own tradable band map (`tradability.compute_tradability`, frozen) at that event's own session basis,
@@ -475,7 +482,7 @@ narrowed, and a context hit never consults the map at all.
 | `PLAYBOOK_CONTEXT_NEAR_BAND_BPS` | 70.0 | **ADAPTATION** | One band-width — the tolerance the desk already uses to CLUSTER levels into one wall (`tradability_band_width_bps`), read outward as "the trade is at the wall behind it". Echoed as a module constant, never read from `Config`. |
 | `PLAYBOOK_CONTEXT_ROOM_R_EDGES` | (1.0, 2.0) | **ADAPTATION** | The book's own reward-to-risk vocabulary, in multiples of the trade's OWN recorded invalidation distance — not values fitted to any outcome. |
 
-Structural (shape, not thresholds): `PLAYBOOK_CONTEXT_ALGORITHM_VERSION = "playbook-band-context-v2"`,
+Structural (shape, not thresholds): `PLAYBOOK_CONTEXT_ALGORITHM_VERSION = "playbook-band-context-v3"`,
 `PLAYBOOK_CONTEXT_DISTANCE_FROM = "entry"`, `PLAYBOOK_CONTEXT_STATUSES`,
 `PLAYBOOK_CONTEXT_BACKING_BUCKETS`, `PLAYBOOK_CONTEXT_ROOM_BUCKETS`.
 
diff --git a/docs/referee-statistical-spec.md b/docs/referee-statistical-spec.md
new file mode 100644
index 0000000..05d4a97
--- /dev/null
+++ b/docs/referee-statistical-spec.md
@@ -0,0 +1,371 @@
+# The Referee — canonical statistical specification (Era 6)
+
+> **This document is the rulebook.** Every constant, eligibility rule, null definition, test
+> procedure, weight, verdict rule, and oracle design for Era 6 is fixed HERE, before the code
+> that implements it. Developers implement from this spec verbatim; a developer who finds a
+> rule ambiguous or unimplementable DROPS the procedure from the iteration and surfaces it for
+> an owner ruling — never improvises. A change to anything in this document is a **named
+> revision** that re-keys future referee results beside old ones (new spec ids / parameter
+> hashes), never an edit of recorded meaning. Nothing here is ever tuned from outcomes.
+>
+> Authored 2026-08-14 at the opening of Era 6, from the approved era plan (statistical design
+> red-team-reviewed; the three blocker fixes — the single confirmatory checkpoint, the
+> within-session label permutation as primary, and remaining-time-matched eligibility — are
+> incorporated as law). Companion constitution: [`docs/goal.md`](goal.md).
+
+---
+
+## 0. Shared conventions
+
+- **Units.** Directional measures are the rail's `return_pct` values: side-signed percent
+  returns (long = raw, short = negated by `sign`), exactly as `desk_forward._measure_from`
+  serves them. MDD measures are unsigned, direction-named, clamped ≤ 0, never sign-multiplied;
+  the side→MDD binding is `long → mdd_long_*`, `short → mdd_short_*` (the rail's documented
+  convention). These statements live ONCE in the observation contract
+  (`referee_evidence.py`); adapters may not restate or vary them.
+- **Sessions.** A Playbook cluster is a trading `session_date` (the record's own
+  `"YYYY-MM-DD"` field). A strategy cluster is a registered dataset id. Clusters are never
+  cross-applied between families.
+- **Time of day.** ToD buckets are Card 6.5's, converted epoch → America/New_York with DST
+  (trap T1): `open` 09:30–10:30, `mid` 10:30–15:00, `close` 15:00–16:00. Bucket membership is
+  decided by the occurrence's trigger epoch (signals) or anchor bar epoch (nulls).
+- **Determinism.** Every random draw uses `random.Random(stream)` with the pinned stream
+  recipe (§1) and the hand-coded partial Fisher–Yates draw discipline (`_draw_anchor_indices`
+  import or its exact idiom) — never `random.sample`, never a global RNG, never wall-clock.
+  Persisted aggregate numbers use `math.fsum`-class stdlib accumulation, not
+  platform/version-sensitive vectorized reductions. Identical inputs ⇒ byte-identical
+  outputs, forever.
+- **Read-side law.** Nothing in this spec writes to, re-keys, backfills, or reinterprets any
+  existing record. All referee outputs are new append-only records or pure read-side folds.
+
+## 1. Pre-registered constants (module constants in `referee_*.py`; NEVER `Config` fields)
+
+| Constant | Value | Meaning |
+|---|---|---|
+| `REFEREE_SEED` | `271828` | Root seed for every referee stream (distinct from the rail's 1729; namespaced streams make collision impossible, distinctness is hygiene) |
+| `REFEREE_STREAM_RECIPE` | `f"{REFEREE_SEED}:{hypothesis_id}:{purpose}[:{session_date}[:{i}]]"` | The only stream constructor; `purpose` ∈ `{"null-draw","perm","flip","boot-occ","boot-cluster"}` |
+| `REFEREE_B` | `10_000` | Randomization/bootstrap draw count (confirmatory) |
+| `REFEREE_ENUMERATION_THRESHOLD` | `8_192` | Full enumeration when the randomization space is ≤ this; else `REFEREE_B` seeded draws |
+| `REFEREE_CI_LEVEL` | `0.95` | Percentile bootstrap CI level (both clustering levels) |
+| `REFEREE_DEFAULT_Q` | `0.10` | Default BH q; each family fixes its own q at registration and never after |
+| `REFEREE_MIN_SESSIONS` | `12` | Minimum INFORMATIVE post-boundary sessions for a confirmatory evaluation |
+| `REFEREE_MIN_OCCURRENCES` | `12` | Minimum eligible post-boundary occurrences (candidate group) |
+| `REFEREE_MIN_CLUSTERS_FOR_CI` | `8` | Below this cluster count the clustered CI serves `insufficient_sample`, never a fabricated interval |
+| `REFEREE_NULL_ANCHORS_PER_OCCURRENCE` | `4` | K seeded null anchors per eligible occurrence |
+| `REFEREE_TOD_BUCKETS` | `(("open","09:30","10:30"),("mid","10:30","15:00"),("close","15:00","16:00"))` ET | Card 6.5's buckets, verbatim |
+| `REFEREE_SESSION_COMPLETE_ET` | `"15:55"` | A record is a completed-session record for a symbol iff that symbol's finest measurement series reaches a bar whose epoch ≥ this ET time on the session date |
+| `REFEREE_ORACLE_B` | `2_000` | Draw count inside oracle simulations (size/power estimation) |
+| `REFEREE_ORACLE_REPLICATIONS` | `400` | Simulated datasets per oracle case |
+| `REFEREE_ORACLE_BUDGET_SECONDS` | `120` | Hard runtime budget for the oracle suite (the `dense_replay_time_budget_seconds` precedent); a slower suite is a defect |
+| `REFEREE_ORACLE_SIZE_TOLERANCE` | `0.5·α` … `1.5·α` empirical-rejection band at α = 0.05 | The calibration acceptance band (binomial noise at 400 replications is accounted for in the oracle tests' own math) |
+| `REFEREE_GATE_VERSION` | `"referee-gate-v1"` | The gate basis pinned into certificates and adjudication snapshots |
+| Null-spec ids | `"referee-null-tod-v1"`, `"referee-null-context-v1"` | §4; each id's signature hashes its full parameter blob |
+| Test-spec id | `"referee-test-perm-v1"` | §3; hashes the test's full parameter blob (weights, sidedness handling, enumeration rule, p convention) |
+
+Every constant above is read at call time by `referee_parameters()`, embedded verbatim in
+every referee record, and hashed into that record's identity. A monkeypatched constant must
+move the parameters AND the identity (counter-tested). Floors reuse philosophy: these are new
+KINDS of floors (sessions/clusters), minted once here; the existing `pnl_min_sample_size`-class
+floors keep their own owners.
+
+## 2. The observation contract (implemented once, in `referee_evidence.py`)
+
+```
+{
+  evidence_family: "playbook_occurrence" | "strategy_trade",
+  observation_id:  str,          # pure function of (source_record_id, signal index / trade index)
+  symbol:          str,
+  session_date:    "YYYY-MM-DD", # playbook: the record's field; strategy: ET date of entry instant
+  anchor_ts:       str,          # ISO-8601 UTC: trigger ts (playbook) / entry instant (strategy)
+  side:            "long"|"short",
+  measure_key:     str,          # one of the rail's 15 keys (playbook) / "net_r" (strategy)
+  value:           float,        # units per §0
+  cluster_key:     str,          # session_date (playbook) / dataset id (strategy)
+  provenance: {
+    detector_basis:            str,   # sha256(canonical(record.parameters))[:16]  (playbook)
+    config_fingerprint:        str,
+    context_algorithm_version: str|None,  # "playbook-band-context-v3" when a context predicate is involved
+    source_record_id:          str,
+    basis_caveats:             [str], # e.g. the Card-6.4 forming-bar caveat (strategy family)
+  },
+}
+```
+
+**Playbook pooling/dedup (the identity that survives daily top-ups):** observations pool at
+`(detector_basis, config_fingerprint)`; for each `session_date`, exactly ONE record
+contributes — the newest by `(recorded_at, id)` among records matching the pooled basis. A
+genuine detector revision moves `detector_basis` and honestly splits the pool. Coverage
+honesty: each pooled record carries its per-symbol coverage; when a newest record covers
+fewer symbols than a superseded one for the same date, a served disclosure names it.
+
+**Completed-session rule:** a record is confirmatory-eligible for a symbol only if that
+symbol's finest measurement series reaches `REFEREE_SESSION_COMPLETE_ET` (partial mid-day
+records are exploratory-only; the session guard fails open by design, so this predicate is
+the completeness gate).
+
+**Exclusions are counts, never values:** a truncated primary-horizon leaf, an unmeasurable
+leaf (`reason` non-null), or a zero-eligible-null occurrence is excluded from the pool and
+counted in served exclusion fields. There is no fallback measure substitution, ever.
+
+## 3. Estimands and tests
+
+Three Playbook estimands; one strategy-family analog. Each hypothesis registers exactly ONE
+primary `(measure_key, horizon)` chosen from the setup's economic semantics, and its
+sidedness; every other measure/horizon is secondary/descriptive and carries no confirmatory
+weight.
+
+### 3.1 Estimand A — setup effect
+"Do occurrences of setup S (side d) carry information beyond comparable times of the same
+sessions?" Comparison: each eligible occurrence vs its ToD-matched null anchors
+(`referee-null-tod-v1`, §4.1), paired within session.
+
+Per informative session s (≥1 eligible occurrence with ≥1 eligible anchor):
+`Δ_s = mean(occurrence values in s) − mean(anchor values in s)`.
+
+### 3.2 Estimand B — context-associated difference within setup
+Named honestly: this is ASSOCIATION, not a randomized increment (context labels are not
+assigned at random; symbol-mix and time-of-day composition can confound; the hypothesis
+record carries this statement). "Among occurrences of setup S (side d), do occurrences in
+context cell C differ from same-setup occurrences outside C?"
+
+Informative sessions = sessions containing BOTH groups (cell and complement, same setup+side,
+eligible occurrences). Per informative session:
+`Δ_s = mean(cell values in s) − mean(complement values in s)`.
+One-group sessions contribute nothing and are counted out loud. Per-cell symbol composition
+is served beside the result. Full (session × symbol) stratification is too sparse at this
+corpus and is deliberately NOT claimed.
+
+### 3.3 Estimand C — combined effect
+"Are occurrences of setup S (side d) in context cell C better than chance at comparable times
+AND comparable structure?" As estimand A, but against the context-matched null
+(`referee-null-context-v1`, §4.2). Registration as C is REFUSED when the context predicate is
+not evaluable at anchor bars from recorded data — register as A or B instead, never
+approximate silently.
+
+### 3.4 The primary test — within-session group-label permutation (`referee-test-perm-v1`)
+Combined statistic over informative sessions:
+`T = Σ_s w_s · Δ_s / Σ_s w_s`
+with pre-registered precision weights:
+- A/C: `w_s = n_s · K_s / (n_s + K_s)` where `n_s` = eligible occurrences, `K_s` = eligible
+  anchors in session s (the harmonic form; equals `n_s·K/(K+1)`-proportional when anchors are
+  full-K);
+- B: `w_s = n1_s · n2_s / (n1_s + n2_s)`.
+
+Null distribution: independently within each informative session, permute the group labels
+among that session's pooled eligible observations, PRESERVING group sizes (seeded stream
+`purpose="perm"`, per-session sub-streams); recompute `T*`. Draws: full enumeration when the
+total space ≤ `REFEREE_ENUMERATION_THRESHOLD`, else `REFEREE_B` seeded draws.
+`p = (1 + #{T* ≥ T}) / (B + 1)` for registered sidedness "greater" (mirrored for "less";
+two-sided uses `|T*| ≥ |T|`). The `+1` convention keeps p super-uniform under H0
+(Phipson–Smyth); the minimum attainable p (granularity) is served beside every p.
+
+Validity: exact (conditional on the realized observations) under within-session
+exchangeability of labels — which is precisely the H0 the constructed null encodes (A/C) or
+the no-context-information H0 (B) — for ANY group-size ratio and ANY skew. This is the reason
+it is primary and the session-level sign-flip is not (§6 case iii demonstrates the sign-flip's
+finite-sample mis-sizing for unequal groups under skew).
+
+### 3.5 Robustness disclosures (never the decision)
+Computed and served beside every confirmatory result; feeding only the `fragile` verdict:
+1. session-level sign-flip on `{Δ_s}` (the cluster-coarse view; `purpose="flip"`),
+2. the equal-session-weight variant of T (`w_s = 1` — the fat-session defense reading),
+3. the entry-basis sensitivity (§4.3),
+4. occurrence-level AND session-clustered percentile bootstrap CIs (§3.6).
+
+### 3.6 Uncertainty
+Percentile bootstrap at `REFEREE_CI_LEVEL`, seeded:
+- occurrence-level (`purpose="boot-occ"`): resample eligible occurrences' paired per-
+  occurrence differences (A/C: occurrence value − mean of its own anchors; B: not defined at
+  occurrence level — occurrence-level CI is over the cell-vs-complement pooled difference)
+  with replacement;
+- session-clustered (`purpose="boot-cluster"`): resample informative sessions with
+  replacement; a drawn session carries ALL its observations; the statistic is T.
+Below `REFEREE_MIN_CLUSTERS_FOR_CI` informative sessions the clustered CI serves
+`insufficient_sample`. CIs are descriptive companions; no CI is ever a p-value (the era's
+anti-goal), and MDE ≈ `z_{1−α} · sd*(T) / 1` from the clustered resamples is served as the
+power disclosure.
+
+### 3.7 Strategy-family analog
+Cluster = dataset. Per dataset d with ≥1 candidate trade:
+`Δ_d = mean(candidate net_r in d) − mean(recorded random_null net_r in d)`; the same
+permutation frame within dataset; the same floors read over datasets. At today's corpus the
+expected honest outcome is `insufficient_sample`; the adapter serves the Card-6.4
+`basis_caveats` and the null-design disclosure (the recorded null is 100 uniform-random
+entries, not count/ToD-matched — stated, not hidden).
+
+## 4. Matched nulls
+
+### 4.1 `referee-null-tod-v1` — the time-of-day-matched null
+For each eligible occurrence (primary-horizon leaf complete):
+- Anchor population: bars of the SAME symbol's SAME measurement series (`measure_bars`, same
+  `tf_minutes`) in the SAME session, whose ET time falls in the occurrence's ToD bucket,
+  EXCLUDING the trigger/anchor bar of the occurrence itself.
+- **Remaining-time matching:** for fixed horizons (1m/5m/1h/4h), an anchor bar is eligible
+  only if ≥ horizon minutes of session remain at it (mirroring the occurrence's own
+  completeness). For `to_close` primaries, eligibility is the ToD bucket alone and the mean
+  |exposure difference| (minutes-to-close) is a served disclosure.
+- Draw: `min(K, eligible)` anchors WITHOUT replacement, seeded stream
+  (`purpose="null-draw"`, per-occurrence sub-stream); shortfall disclosed; zero eligible ⇒
+  the occurrence is excluded and counted.
+- Measurement: the imported `desk_forward._measure_from` at the anchor bar, `entry = anchor
+  bar close`, `entry_kind = "close"`, the SIGNAL's side sign — identical conventions,
+  identical series, identical truncation semantics.
+- Overlap disclosure: mean fraction of each anchor's primary-horizon window overlapping its
+  paired occurrence's window (the same-session power-cost made visible). No exclusion radius
+  beyond the trigger bar itself (decided; the disclosure replaces it).
+
+### 4.2 `referee-null-context-v1` — the context/time-matched null
+As 4.1, plus: the anchor bar's price must satisfy the SAME backing-bucket predicate the
+hypothesis registers (e.g. `at_wall`: distance from the anchor bar's close to the wall behind,
+side-relative, ≤ 70 bps inclusive — evaluated through the existing `BandMapResolver` over the
+RECORDED band map for `(symbol, basis_day)`, the context layer's own machinery); `room_r` at
+the anchor borrows the paired occurrence's risk distance (the shipped
+`risk_source="paired_signal"` convention). Per-cell anchor eligibility rates are served; a
+cell whose anchors cannot be found is an exclusion disclosure, never a substitution.
+
+### 4.3 The entry-basis sensitivity (pre-registered, mechanical)
+Occurrences enter at detector-decided `entry`/`entry_kind`; anchors enter at bar close. The
+registered estimand wording is therefore "differs from a ToD-matched close-anchored
+baseline". The sensitivity: re-measure each occurrence close-anchored at its trigger bar
+through the same rail (read-side, at evaluation time; detectors untouched) and recompute T.
+A sign flip of T under this sensitivity triggers `fragile` mechanically.
+
+### 4.4 Persistence
+Null sets are recorded append-only (`TAPEOLOGY_DESK_REFEREE_NULL_DIR`), keyed
+`(playbook record id, null-spec signature)`, embedding the null parameters verbatim, with a
+run ledger and compute manager/CLI. GETs serve recorded nulls or honest absence; they never
+compute.
+
+## 5. Registry, boundary, checkpoint, and BH
+
+- **Family record** (immutable): `family_id`, `q`, the COMPLETE planned candidate list
+  (hypothesis ids), `registered_at`. The BH denominator m = the planned count, forever.
+- **Hypothesis record** (immutable): identity + estimand + setup/side + context predicate +
+  primary `(measure, horizon)` + sidedness + null-spec id + test-spec id + `detector_basis` +
+  `context_algorithm_version` (when contextual) + `confirmation_start_boundary` +
+  `target_sessions` + floors + `origin: "historical-exploration"` + `family_id`.
+- **Boundary:** `confirmation_start_boundary` = the ET calendar date of `registered_at`
+  (UTC → America/New_York); confirmation admits only observations with `session_date`
+  STRICTLY after it. The boundary is on `session_date`, never `recorded_at` — a
+  deep-backfilled record for an older session date recorded after registration can NEVER
+  enter confirmation (counter-tested).
+- **Withdrawal:** permitted only while no post-boundary evaluation of the hypothesis exists;
+  afterwards the hypothesis remains in m and folds as p = 1 if never evaluated.
+- **The single confirmatory checkpoint:** the FIRST evaluation of a hypothesis at which
+  post-boundary informative sessions ≥ `target_sessions` (on completed-session records) is
+  its confirmatory evaluation. Its family-level BH adjudication is recorded as an append-only
+  ADJUDICATION SNAPSHOT — the citable verdict. Earlier evaluations serve
+  `pending_forward_confirmation` (accrual math, NO confirmatory p). Later evaluations are
+  labeled `monitoring` and can never change the snapshot. A replication is a NEW registered
+  hypothesis. This closes optional stopping; there is no interim-look schedule in v1.
+- **BH within a family** (at its registered q, over the family's checkpoint p-values, m =
+  planned): sort ascending, `k* = max{k : p_(k) ≤ (k/m)·q}`, corroboration for ranks ≤ k*.
+  Benjamini–Yekutieli adjusted values are served beside BH as a dependence-robustness
+  disclosure; BH is the registered decision rule. The `REFEREE_REGISTER` states that
+  family-wise q does not compound across families — running many families over time erodes
+  global FDR, and only the registry's full history makes that auditable.
+- **Verdicts** (each a pure function of recorded facts):
+  `exploratory` (basis not registered) · `registered` (boundary set, zero post-boundary
+  informative sessions) · `pending_forward_confirmation` (0 < accrued < target) ·
+  `insufficient_sample` (floors unmet at checkpoint, or `REFEREE_MIN_CLUSTERS_FOR_CI` unmet)
+  · `fragile` (BH pass BUT: BY fail, OR any §3.5/§4.3 sensitivity flips T's sign, OR the
+  clustered CI includes 0) · `no_evidence` (checkpoint ran; null not rejected under BH) ·
+  `corroborated` (BH pass + no fragility trigger + floors met) · `killed` (a registered kill
+  condition met) · `basis_retired` (disclosure: the pinned `detector_basis` is no longer
+  produced by the live corpus). "Survivor" is never used — that word belongs to `pnl_scan`'s
+  holdout measurement concept.
+
+## 6. Oracles and the fail-closed attestation
+
+The oracle suite (seeded; `REFEREE_ORACLE_REPLICATIONS` datasets/case; `REFEREE_ORACLE_B`
+draws inside each; total ≤ `REFEREE_ORACLE_BUDGET_SECONDS`) is the acceptance for the
+statistics core. Cases:
+
+1. **Size, iid skewed:** lognormal-shifted-to-zero-mean occurrence values, n_s=1, K=4 —
+   empirical rejection at α=0.05 within the tolerance band.
+2. **Size, heavy-tailed:** Student-t(3)-generated values — same band.
+3. **The two demonstrated failures (must fail, by design):**
+   (a) an UNCLUSTERED pooled-label permutation foil on a session-clustered null (shared
+   per-session regime shifts) over-rejects (> the band's ceiling);
+   (b) the session-level SIGN-FLIP variant on the skewed n_s=1/K=3 one-sided case mis-sizes
+   while the within-session label permutation holds size. These two cases are the recorded
+   evidence for why the primary test is what it is.
+4. **Power:** a +0.5·sd location shift at S = 40 informative sessions — rejection rate
+   reported and pinned as a golden (a stated power, not a gate).
+5. **BH sweep:** 20 known-null + 1 known-positive candidates, m = 21 — across seeds, BH at
+   q=0.10 admits ≈ the positive only (the false-admission rate stays within its binomial
+   band).
+6. **CI coverage:** clustered percentile CI covers the true session-mean effect at ≈ 95%
+   within tolerance at S = 40; the S = 6 case correctly serves `insufficient_sample` instead
+   of an interval.
+
+**Attestation:** `run_oracle_attestation()` executes a pinned known-answer subset (fixed
+seeds, fixed tiny datasets, exact expected p/CI digests with stated tolerances) and returns
+`{passed, expected, actual, tolerance, stats_core_version}`. Every evaluation record embeds
+its attestation. The adjudication fold VERIFIES the attestation (presence + match + version)
+and refuses confirmatory output with honest served copy when it fails — fail closed, but
+never Monte Carlo at GET time.
+
+## 7. The starter family (PROPOSED shortlist — the operator approves 2–3 at the J-07 act)
+
+Constraints (operator ruling 2026-08-14): 2–3 hypotheses, operator-approved through the REAL
+registration act, never auto-baked or special-cased; `origin: "historical-exploration"` on
+every one (the atlas was inspected before these questions were written down); prefer covering
+all three estimands; exactly one semantically-chosen primary per hypothesis (never
+performance-picked, never blanket-`1h`); confirmation strictly post-boundary; zero
+`corroborated` at era end is the expected honest state.
+
+| # | Estimand | Candidate | Corpus at authoring (n / sessions, current basis) | Proposed primary + semantic rationale |
+|---|---|---|---|---|
+| S-1 | A | `capitulation:long` vs ToD-matched null | 473 / 71 | `5m` return — the book's capitulation claim is the immediate reflexive snapback off climax exhaustion; minutes-scale, not session-scale |
+| S-2 | A | `jbe:long` vs ToD-matched null | 164 / 44 | `1h` return — jump-base-explosion claims continuation of an established leg; the follow-through hour after the base resolves |
+| S-3 | A | `double_top:short` vs ToD-matched null | 771 / 105 | `to_close` return — a completed reversal structure claims the session's trend has turned; always measurable by construction |
+| S-4 | B | `range_trade` (registered per side) `at_wall` vs other same-setup contexts | subset of 469+459 / ~80 (live cell counts served at registration) | `1h` return — a range bounce plays out over the traverse toward the opposite boundary; `to_close` would contaminate with post-breakout regimes |
+| S-5 | C | `range_trade:long` + `at_wall` vs context/ToD-matched null | subset served at registration | `1h` return — the combined claim: a wall-backed bounce is better than chance at that time and place |
+
+Deliberately not proposed: `open_high_break`/`open_low_break` (26 and 18 occurrences — below
+any honest floor), `cup_handle` (n = 1), a fourth A on `dbi:short` (kept for a future
+family). The registration surface serves LIVE readiness (n, informative sessions, accrual
+rate, projected days to `target_sessions`) beside each candidate; the operator picks with the
+sample reality in view.
+
+## 8. The promotion certificate and interlock
+
+- **Certificate record** (append-only, in the registry): pins `{candidate (strategy_id,
+  profile), champion identity at scan time, train dataset (id, checksum, split), holdout
+  dataset (id, checksum, split), config_fingerprint, REFEREE_GATE_VERSION + referee
+  parameters hash, family_id + hypothesis_id, gate results (calibrated p, BH pass at the
+  family q, CI, floors)}`. Mintable only through the real evaluation rail — never by hand,
+  never by fixture paths in production code.
+- **`authorize_promotion`** runs inside `pnl_scan._promote` BEFORE any write (the
+  ledger-row-first / champion-pointer-second order is unchanged after authorization). Fail
+  closed, with distinct honest refusals: no certificate · stale (ANY pin differs from the
+  live scan's own report values) · wrong candidate · mismatched datasets/fingerprint ·
+  failed gates · malformed/unverifiable (store integrity failure). No `--force`, no skip
+  flag, no env override, no default-allow mode (source-scan guard-tested). A Playbook
+  hypothesis certificate can never satisfy a strategy promotion (the candidate pins make
+  this structural).
+- Survivor labelling and every report stay as shipped measurement concepts:
+  `survivor: true` with `promotion_eligible: false` (+ the refusal reason) is an honest,
+  expected state for the rest of this era.
+
+## 9. Stated assumptions and limits (served, not hidden)
+
+1. **Same-session matching is conservative under H1:** anchors share the session's realized
+   drift, which under a true effect partially contains the effect itself — a power cost, paid
+   for exchangeability. The overlap disclosure (§4.1) quantifies it.
+2. **Estimand B is observational:** context labels are not randomized; symbol-mix and ToD
+   composition can confound; B verdicts are association statements, worded so.
+3. **Exchangeability is within-session:** the permutation conditions on each session's
+   realized values; cross-session dependence enters only through the session-level statistic
+   and the clustered CI — the reason both are mandatory.
+4. **The corpus is coverage-heterogeneous** (median 4 symbols/date at authoring, 38
+   full-universe dates): precision weights lean on fat sessions; the equal-weight sensitivity
+   discloses when that matters.
+5. **Discrete p-values** make BH conservative at small S; the granularity floor is served.
+6. **The strategy family's recorded null is unmatched** (uniform-random, fixed 100); its
+   adjudications say so, and Card 6.6's matched nulls remain future work gated on the tick
+   library.
+7. **The forming-bar caveat (Card 6.4)** applies to structure/strategy-family measurement
+   bases and is stamped as `basis_caveats`; it does not touch Playbook context (recorded
+   band maps) or these tests' validity.
diff --git a/docs/research-directions.md b/docs/research-directions.md
index ec654b9..3895704 100644
--- a/docs/research-directions.md
+++ b/docs/research-directions.md
@@ -125,7 +125,10 @@ extends it to per-regime cells under a documented rail amendment), and the intra
 `Config.config_fingerprint()` hashes the entire config minus an explicit exclusion set
 (`apps/backend/app/config.py`), and the founding fingerprint `4d665603569b9dbf` is pinned by a
 literal assertion (`apps/backend/tests/test_profile_equivalence.py`) and stamped on the founding
-PnL-ledger row. **Almost every era below adds Config fields.** There are exactly two lawful moves;
+PnL-ledger row. *(Epoch note 2026-08-14: the founding pin was retired by the era-5D "Clean
+Slate" Path B bump — the CURRENT pinned epoch is `08e471b10130e1e2`, and
+`tests/test_fingerprint_epoch_retirement.py` guards the retired literal out of `apps/`. The
+protocol below is unchanged.)* **Almost every era below adds Config fields.** There are exactly two lawful moves;
 a weak model that improvises a third will corrupt the honesty machinery:
 
 - **Path A — exclusion (the default)**: when a new field is read ONLY by new code paths (a new
@@ -510,6 +513,24 @@ candidates; it will not survive twenty. Build the referee BEFORE the signal fact
 **Why now**: eras 7–14 generate dozens of pre-registered candidates. Multiple-testing correction,
 CIs, cost sensitivity, and the atlas must exist first, or every later "survivor" is suspect.
 
+> **ERA-6 OPENING NOTE (2026-08-14, session `referee`, under §5.6 "goal.md wins").** The era
+> opens against a repository this chapter did not foresee: the Desk (Era B) and the Playbook
+> (Era B2, plus the R-4 band-context interlude) built a SECOND evidence family — bar-measured
+> Playbook occurrences (210 append-only records / 156 sessions; 3,222 signals at the current
+> detector basis) — while the tick library this era's gate names was never built (Card 5.2:
+> ~12 partial 2.5-hour windows on disk vs the "≥ ~150 symbol-days" gate). The gate is therefore
+> re-scoped PER EVIDENCE FAMILY, honestly: the Referee core (6.2-as-amended, 6.3-as-amended,
+> the 6.6 matched-null concept) opens NOW against the Playbook family + a strategy-family
+> adapter (expected honest verdict at today's tick corpus: `insufficient_sample`); the
+> tick-dependent lenses (6.7 costs, 6.9 atlas, 6.10 loser mining) and the strategy-sweep cards
+> (6.1 metrics, 6.4 Part 2 walk-forward, 6.5, 6.8, 6.11) stay gated on their own data and are
+> NOT smuggled in. **Card 6.4 Part 1 (the forming-bar as-of fix) is explicitly DEFERRED by
+> operator decision 2026-08-14**: the defect is real and still live (`levels._bars_as_of` keeps
+> `epoch ≤ as_of`), it is disclosed as a served `basis_caveats` entry on strategy-family
+> evidence, and the fix remains this card — the opening gate of the next structure-measurement
+> era. The era's constitution is [`docs/goal.md`](goal.md); its statistical rulebook is
+> [`docs/referee-statistical-spec.md`](referee-statistical-spec.md).
+
 **[SPLIT-POINT after 6.6]** — session A = gates (6.1–6.6), session B = lenses (6.7–6.11).
 
 ---
@@ -532,33 +553,65 @@ CIs, cost sensitivity, and the atlas must exist first, or every later "survivor"
   division everywhere; keys sorted for byte-identical renders.
 
 #### Card 6.2 — Seeded bootstrap CIs + promotion gate v2 `[stats] [F1→F2] [M]`
+
+> **AMENDED 2026-08-14 (era-6 opening; statistical correction — the original procedure below is
+> preserved for the record but is superseded where it conflicts).** Two corrections, canonical in
+> [`docs/referee-statistical-spec.md`](referee-statistical-spec.md):
+> 1. **The bootstrap p-value is retracted.** `p = (1 + #{resample_mean ≤ 0})/(B + 1)` over
+>    ordinary resamples is a CI-inversion probability centered at the OBSERVED mean — not the
+>    probability of the observed statistic under H0. Its size under a true null is uncontrolled
+>    for skewed, heavy-tailed, clustered data at modest n, and BH's FDR guarantee assumes valid
+>    (super-uniform) p-values. Bootstrap machinery is CI-ONLY; every p that feeds BH comes from a
+>    null-calibrated randomization test (within-cluster group-label permutation; spec §3), proven
+>    by seeded oracles. "Resample trades, not days" is likewise superseded for the Playbook
+>    family: cluster-level (session) resampling and cluster-aware testing are first-class, not a
+>    future variant.
+> 2. **The seed is not a Config field.** `bootstrap_seed` via Path A is superseded by the
+>    era-B2/desk pattern: a module-constant seed (`REFEREE_SEED`) embedded in the procedure's own
+>    parameters blob and hashed into its result identity — zero Config fields, fingerprint
+>    untouched by construction. Path A remains the fallback if a Config field ever becomes
+>    genuinely necessary.
+> Gate v2's SHAPE stands (survivor gate AND interval AND BH membership) and is implemented in
+> era 6 as the fail-closed promotion certificate interlock (spec §8): promotion requires a valid
+> candidate-specific Referee certificate; sweep computation and survivor labelling keep working
+> without one; no bypass exists.
+
 - **Hypothesis**: point-estimate positivity at small n is noise; interval-based gating changes
   which candidates survive.
-- **Procedure (exact)**: B = 10,000 resamples, seed = new config `bootstrap_seed` (Path A
-  exclusion + counter-test per 0.4). Each resample: draw n trades with replacement, record
-  `mean(net R)`. `CI95 = [P2.5, P97.5]` of the resample means;
-  one-sided `p = (1 + #{resample_mean ≤ 0}) / (B + 1)`. Report CI and p beside every aggregate.
+- **Procedure (original text, superseded per the amendment above)**: B = 10,000 resamples,
+  seed = new config `bootstrap_seed` (Path A exclusion + counter-test per 0.4). Each resample:
+  draw n trades with replacement, record `mean(net R)`. `CI95 = [P2.5, P97.5]` of the resample
+  means; one-sided `p = (1 + #{resample_mean ≤ 0}) / (B + 1)`. Report CI and p beside every
+  aggregate.
 - **Gate v2**: survivor requires (pooled 5.4 gate) AND `CI95_low > 0` AND the 6.3 BH pass.
   Expect a long no-promotion period — **that is the system working** (do not loosen; T2).
 - **Build**: one bootstrap module with one owner (e.g. `research/statistics.py`), consumed by
-  `pnl_scan.py`, `edge_report.py`, and the forward ledger job.
+  `pnl_scan.py`, `edge_report.py`, and the forward ledger job. *(Era 6 ships this as
+  `research/referee_stats.py`.)*
 - **Evaluate (oracle, trap T7)**: seeded synthetic populations with KNOWN answers — all-+1R
   (CI excludes 0), zero-mean (CI spans 0 ≈ 95% of seeds), known-mean-0.2R at n=100 (CI covers
-  0.2). The oracle test is the acceptance; fixture-only tests prove nothing at n<5.
+  0.2). The oracle test is the acceptance; fixture-only tests prove nothing at n<5. *(Era 6
+  extends the oracle set with null-calibration, clustered-failure, and mis-sizing
+  demonstrations; spec §6.)*
 - **Kill**: n/a (referee machinery; its kill is failing its own oracle — then it must not ship).
-- **Traps**: T7; resample trades, not days (document the choice; per-day block bootstrap is a
-  registered future variant, not a silent switch); seed from config, never wall-clock.
+- **Traps**: T7; seeds recorded and streamed per row, never wall-clock; CI-inversion is never a
+  p-value (the amendment's correction #1).
 
 #### Card 6.3 — Experiment registry (multiple-testing ledger) + edge dashboard `[stats+infra] [F1] [M]`
 - **Hypothesis**: without a trial ledger, the year's true candidate count is unknowable and
   every later "discovery" is statistically uninterpretable.
-- **Build**: new append-only table `experiments` (schema migration in
-  `apps/backend/app/research/store.py`, next version, following the `pnl_ledger` single-writer
-  pattern): row = `{sweep_id, registered_wall_ts, candidate_id, family, params_hash,
-  split_basis, status(planned|evaluated), result_summary(JSON), p_value}`. **Pre-registration
-  protocol (T6)**: a sweep writes ALL its planned candidate rows BEFORE the first backtest
-  runs; results update rows in place to `evaluated`; the BH denominator is the count of
-  planned rows of that sweep — "evaluated", never "reported".
+- **Build** *(AMENDED 2026-08-14, era-6 opening: the store design below is superseded — era 6
+  ships the registry as append-only sibling JSON stores on the desk store pattern
+  (`referee_registry.py`: immutable family + hypothesis + withdrawal + certificate records,
+  appended evaluation records, adjudication snapshots; status DERIVED by fold, never updated in
+  place — strictly more auditable than update-to-evaluated rows; spec §5). The pre-registration
+  protocol and denominator rule below stand verbatim.)*: new append-only table `experiments`
+  (schema migration in `apps/backend/app/research/store.py`, next version, following the
+  `pnl_ledger` single-writer pattern): row = `{sweep_id, registered_wall_ts, candidate_id,
+  family, params_hash, split_basis, status(planned|evaluated), result_summary(JSON), p_value}`.
+  **Pre-registration protocol (T6)**: a sweep writes ALL its planned candidate rows BEFORE the
+  first backtest runs; the BH denominator is the count of planned rows of that sweep —
+  "evaluated", never "reported".
 - **BH procedure (exact)**: sort the sweep's one-sided p-values ascending `p_(1)…p_(m)`;
   `k* = max{k : p_(k) ≤ (k/m)·q}` with `q = 0.10` (config, fixed BEFORE the sweep);
   BH-survivors = candidates 1…k*. Promotion additionally requires membership here.
@@ -572,6 +625,11 @@ CIs, cost sensitivity, and the atlas must exist first, or every later "survivor"
   (append/update-to-evaluated only, no deletes).
 
 #### Card 6.4 — Walk-forward robustness + the forming-bar as-of fix `[stats+fix] [F2] [M]`
+
+> *(Status note 2026-08-14: Part 1 verified still live on `main` and DEFERRED out of era 6 by
+> operator decision — see the era-6 opening note. Until the fix lands, strategy-family referee
+> evidence carries the forming-bar `basis_caveats` disclosure.)*
+
 - **Part 1 — the fix (do this FIRST; everything in eras 7–12 stacks on it)**:
   `_bars_as_of` in `apps/backend/app/research/levels.py` keeps every bar with
   `epoch ≤ as_of` — for INTRADAY timeframes this admits the still-forming bar, whose stored
@@ -614,6 +672,13 @@ CIs, cost sensitivity, and the atlas must exist first, or every later "survivor"
   silently become an entry filter — that is a NEW candidate for a pre-registered sweep (T6).
 
 #### Card 6.6 — Null-baseline upgrades `[stats] [F2] [M]`
+
+> *(Scope note 2026-08-14: era 6 ships this card's CONCEPT for the Playbook family — the
+> ToD-matched null `referee-null-tod-v1` and the context-matched null `referee-null-context-v1`,
+> spec §4, measured through the desk forward rail's own conventions. The strategy-side builds
+> below — the `_null_trades` time-matched and random-levels variants — remain future work gated
+> on the tick library and are unchanged here.)*
+
 - **Hypothesis**: the current uniform-random-entry null is too weak; matched nulls isolate
   WHAT the strategy adds.
 - **Build** (both beside `_null_trades()` in `apps/backend/app/research/backtests.py`, both
@@ -1749,10 +1814,17 @@ credibility is the sum of its honest negatives; the C4 whitepaper is assembled F
 
 ## 3.3 Determinism & seeds recap
 
-Config-owned seeds per procedure (`bootstrap_seed`, null seeds, shuffle seeds, k-means seed, noise
-seed); every new seed follows fingerprint Path A with counter-test; no wall-clock in any research
-payload; every served list explicitly sorted; EWMA/stateful features document their initial
-state. If a procedure cannot be made deterministic, it does not ship.
+*(AMENDED 2026-08-14, era-6 opening: the PRIMARY seed pattern is now the desk/playbook one —
+a module-constant seed embedded in the procedure's own `*_parameters()` blob and hashed into
+its result identity via per-row streams (`DESK_FORWARD_BASELINE_SEED`/`PLAYBOOK_BASELINE_SEED`
+= 1729 and `REFEREE_SEED` = 271828 are the worked examples): zero Config fields, the
+fingerprint untouched by construction, and the seed's provenance embedded verbatim in every
+payload it shaped. Config-owned seeds via fingerprint Path A remain the FALLBACK for a seed a
+frozen path must read.)* Config-owned seeds per procedure (`bootstrap_seed`, null seeds,
+shuffle seeds, k-means seed, noise seed); every new Config-field seed follows fingerprint
+Path A with counter-test; no wall-clock in any research payload; every served list explicitly
+sorted; EWMA/stateful features document their initial state. If a procedure cannot be made
+deterministic, it does not ship.
 
 ## 3.4 Escalation guidance for weaker models
 
@@ -1835,6 +1907,13 @@ Columns: `date · era/workstream · session id · verdict (done | killed | split
 |------|-----|---------|---------|-------------|-------------|
 | 2026-07-05 | 3 (tape_to_profit) | `tape_to_profit` | done | Honest measurement machine complete; `v1` loses money on real tape; edge report correctly finds "no positive-edge dataset". | none |
 | 2026-07-06 | 4 (structure-and-tape) | `tape_to_profit_support_resistence` | done | All 7 journeys shipped; `structure_tape` honestly unevaluable on committed data (n=1 < 5) — the founding question remains empirically open pending the library. | none |
+| 2026-07-12 | 5 (The Library) — REDEFINED in execution | `yahoo_fetch` | done | The era pivoted to a keyless Yahoo Finance BAR library (6 journeys; 4h honestly resampled from 1h; derived SQLite index); the Card-5.2 tick-recorder library (≥150 symbol-days of trade/quote windows) was NOT built — bars and tick datasets are different data families. | Era-6 gate re-scoped per evidence family (era-6 opening note, 2026-08-14). |
+| 2026-07-16 | interlude (outside catalog) — "Tradable Wall" | `tradable_wall` | done | Tradable ≤10-band map + 12-symbol scan registry + 3-way edge report; 11 durable feed=sip tick windows / 10 symbols recorded into the persistent dataset store — the REAL tick corpus to date (~12 partial 2.5h windows). | none |
+| 2026-07-17 | interlude (outside catalog) — "Fast Wall" | `fast_wall` | done | Store stat-caches + durable dataset index, operator-run edge-report compute (GETs never compute), resumable parallel sweep, setups scan cache. | none |
+| 2026-07-24 | interlude (outside catalog) — "Clean Slate" demolition | `clean_slate` | done | Journal era deleted (14 routes, 3 pages → two-page product); the one product move = fingerprint epoch bump `4d665603569b9dbf` → `08e471b10130e1e2` (§0.4 Path B). | §0.4 epoch note added (2026-08-14). |
+| 2026-07-31 | B (operator pivot, outside catalog) — "The Desk" | `desk` | done | `/desk`: fetched S&P100 universe, append-only screen ledger + ranked briefing, touch-anchored forward-return rail v2, deep fine-bar backfill; 21 journeys. | none |
+| 2026-08-11 | B2 (operator pivot, outside catalog) — "The Playbook" | `playbook` | done | Nine pre-registered Graifer/Schumacher intraday detectors on the desk's own 5m/1m bars; append-only playbook corpus + back-scan + descriptive evidence view with seeded same-session anchors; zero statistics gates (deliberately era-6's). | none |
+| 2026-08-13 | operator interlude (outside catalog) — band context | main `9e65bb0`…`83c24a8` | done | Read-side band-context lens v1→v2 (bracket frame)→v3 (basis-bounded cache) + the 9-key cohort vocabulary + refresh-chain steps 6–7 + `/desk` context columns/filters/drill-ins; ratified as R-4 in the era-6 goal. | `docs/playbook-detector-spec.md` §6 version string reconciled v2→v3 (2026-08-14). |
 | _(next session appends here)_ | | | | | |
 
 Protocol: the row is written by the human operator or the session's closing agent AT session
```
