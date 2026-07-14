# goal-tradable_wall-iter-2 Execution Plan

Era 5B "The Tradable Wall", iteration 2: build **J-02 alone** (the wide scan — touch-event scanner
+ case-study registry), continuing the dependency order iter-1 unblocked (J-01, the tradable map,
is `passing`). Backend + MCP only; no UI this iteration (the case-browser UI is J-05). Depth: full —
new canonical value + owner (`setups.py`) across the backend+MCP boundary, plus tests well beyond
browser smoke (no-lookahead consecutive-session, determinism, REST==MCP, reaction classification
under intraday density).

Verified against the current codebase before writing this plan: `apps/backend/app/research/setups.py`
does not exist yet; J-01 (`tradability.py`) and J-07 (regression sentinel) are both `passing` per
`runs/goal-session-tradable_wall/state/journey-history.json`. The live bar store
(`apps/backend/.data/bars/`) currently holds **AAPL only** (1d/1h/1w/4h/5m, several overlapping
windows) plus **one MSFT `4h` series** — MSFT's `1d`/`1h`/`5m` and all of NVDA/TSLA/AMZN/GOOGL/META/
AMD/NFLX/SPY/QQQ/JPM are entirely unrecorded. This confirms the phase spec's own NOTES prerequisite
by direct inspection, not just by citation.

## What to Build

- **`apps/backend/app/research/setups.py`** (new module, sole owner of the touch-event/case-registry
  value). For each of the 12 panel symbols and each session present in its stored 5m series: derive
  that session's morning map by calling **`compute_tradability(store, symbol, as_of_epoch, config)`**
  (from `.tradability`, era-5B J-01) — **never `compute_levels` directly, never a second map/levels
  computation** — then scan that session's own 5m bars for the first touch per band (config-owned
  re-arm rule), classify the reaction (`rejected`/`broke`/`chopped`, config-owned pre-registered
  definitions), and record forward returns at config-owned horizons measured strictly after the
  touch.
  - **Central risk (why this is depth=full):** `as_of_epoch` must be threaded PER SESSION, chosen so
    it falls inside that session (so `compute_tradability`'s own `_resolve_basis` finds the correct
    prior session). A single shared/fixed `as_of` across the whole walk — or one derived from the
    scan's overall end date — would silently hand EVERY session the SAME (latest) map: a critical
    no-lookahead violation one level up from the exact `_PriorSessionBarView` hazard J-01's dev
    handoff already found and fixed inside `compute_tradability`/`compute_levels`.
    `compute_tradability` already owns its own lookahead safety internally (reuse it verbatim);
    `setups.py`'s own no-lookahead obligation is narrower but still real: correct per-session
    `as_of`, plus a scan-window walk whose already-emitted events never change when the walk is
    extended forward (the DoD's "shifting `as_of` earlier never changes an already-emitted event" —
    a consecutive-session test mirroring `test_tradability.py`'s
    `test_no_lookahead_bars_after_the_basis_never_affect_the_result`).
  - `compute_tradability` returns an honest empty map (`bands: []`) whenever no daily series exists
    or no prior session resolves — a session with no derivable morning map contributes NO events for
    that session (never a fabricated event); a symbol with no 5m series at all contributes none.
- **Config additions** (`apps/backend/app/config.py`), namespaced distinctly from both the existing
  `sr_*`/`tradability_*` families AND `studies.py`'s own **unrelated** `study_*` tape-arming-
  occurrence vocabulary (which also uses the word "setup" — `level_break`, `absorption_reversal`,
  etc.: a different concept, live tape-arming occurrences, not band-touch events). Document this
  distinction explicitly in `setups.py`'s module docstring so a reviewer never conflates the two
  "setup" vocabularies. New constants: the **12-symbol panel** (`AAPL MSFT NVDA TSLA AMZN GOOGL META
  AMD NFLX SPY QQQ JPM` — confirmed not yet defined anywhere in `config.py`; grepped, zero hits —
  this iteration introduces it), reaction definitions/thresholds, forward-return horizons, the
  first-touch re-arm rule, and the 5m retention window. Add every new field to the
  `config_fingerprint` exclusion set (the `tradability_*` precedent iter-1 set, exclusion block
  starting `config.py:1494`) with a fingerprint-stability test + real-threshold counter-test (the
  established paired-test pattern). Exact thresholds/horizons are the developer's config-owned
  design freedom (spec's explicit "pre-registered... never post-hoc tuned" framing) — but the pinned
  AAPL 06-22 `rejected`/negative-forward result must fall out of the chosen definitions applied to
  real bars, never reverse-engineered from the desired answer.
- **`GET /research/setups`** (filterable by `symbol`/`reaction`/`class`, optional independently
  combinable query params — mirror `list_bar_series`'s optional-param pattern, `routes.py:1705-1706`,
  with 422 on a malformed filter value) and **`GET /research/setups/{id}`** (404 on unknown id —
  mirror `get_backtest`'s `routes.py:1905` / `get_dataset`'s `routes.py:1519` detail-string pattern).
  Both serve `setups.py`'s output VERBATIM. The drill-in includes a `tape_timeline` field that is
  present-but-empty until J-03 records (never omitted, never fabricated).
- **Read-only MCP `setups` proxy** — simpler than J-01's `tradability` tool: `GET /research/setups`
  takes no REQUIRED params for the base list, so this is a plain `_STATIC_PATHS` entry (the
  `datasets`/`bars` precedent, `mcp/__init__.py:84-95`), not a new two-param branch. Update
  `TOOL_NAMES`/`TOOLS` (mirror the `datasets` tool block, `mcp/__init__.py:178-186`), the module's
  own result-contract docstring, and `test_mcp_server.py`'s `EXPECTED_TOOLS` + the "every tool errors
  when backend is down" args map.
- **Test fixtures — a real gap found by inspection, read carefully:** the spec asks for "ONE small
  multi-session, multi-symbol 5m scan fixture." The only committed 5m AAPL fixture today
  (`tests/fixtures/yahoo/AAPL_5m_20260601_20260618.json`) stops at **2026-06-18T19:55Z** (verified by
  reading its last bar) — it does NOT contain the 2026-06-22 session (the pinned touch) or anything
  after, so it cannot by itself prove the pinned acceptance. The committed daily fixture
  (`AAPL_1d_20260101_20260626.json`) DOES already extend through 2026-06-26 (past the 06-22 touch,
  06-23, and the 06-25 collapse), so it needs no extension. A new/extended real, frozen-from-live-data
  5m AAPL slice reaching through at least 06-22 plus the chosen forward-return horizon (the
  `test_tradability.py`/iter-1 "freeze from this environment's own live `.data/bars`, never
  fabricate" precedent) is required for the pinned end-to-end proof. For the keyless no-lookahead /
  determinism / reaction-classification UNIT tests and the "multi-symbol" requirement, a synthetic
  engineered fixture (the `test_tradability.py` `_SYN_TRADABILITY` pattern — full control over exact
  expected values, plus a second synthetic symbol for symbol-isolation coverage) is the lower-risk
  path already proven in this codebase; reserve the real AAPL slice for the one pinned end-to-end
  case.
- **Execution prerequisite — populate the live store (per spec NOTES, confirmed necessary above):**
  the ≥15-events/≥8-symbols headline needs the 12-symbol panel's `1d` (long window), `1h`, `5m`
  (retention window) bars actually recorded. This is a **live-network, keyless (Yahoo, no Alpaca
  creds needed)** operational act through the EXISTING `POST /research/bars` store-first route
  (`routes.py`, era-5 J-01/J-03; no new production code) — run it as an explicit executor step (a
  small script/loop over the 12 symbols × 3 timeframes) under `TAPEOLOGY_LIVE_INTEGRATION=1` (the
  existing `integration` pytest marker / `test_yahoo_live_integration.py` convention), NOT part of
  the hermetic default suite. The scan LOGIC must pass on the committed fixture regardless of network
  availability; if the panel fetch cannot complete, report that honestly (per NOTES) — the ≥15/≥8
  headline stays unverified rather than simulated; it does not block the rest of the DoD.
- **Tests**: `tests/test_setups.py` (pure/module-level: scan-over-fixture exact values, no-lookahead
  consecutive-session, reaction-classification-under-intraday-density regression, determinism,
  fingerprint-stability + counter-test) + `tests/test_setups_api.py` (route-integration: list
  filters, drill-in, 404, 422s, honest-empty states) + additions to `tests/test_mcp_server.py`
  (REST==MCP byte-identity, `EXPECTED_TOOLS`). Re-run frozen-foundation guards (`levels.py` /
  `tradability.py` byte-identity, engine equivalence 22/22) as part of the J-07 sentinel.
- **Dev handoff** at `docs/handoffs/goal-tradable_wall-iter-2-dev.md`.

No `blueprint.md` edit needed — the Data Contract row and `/structure` → Case Studies home are
already drafted there (`runs/goal-session-tradable_wall/state/blueprint.md`); nav stays frozen.

## Agents Required

- backend-data: yes -- implement `setups.py`, the `config.py` additions (+ fingerprint exclusion +
  counter-test), the two `/research/setups*` routes, the MCP `setups` proxy, the fixture(s), the
  full unit/integration/MCP test suite, AND run the live 12-symbol panel population prerequisite (or
  honestly report why it could not complete) before claiming the ≥15/≥8 headline.
- frontend-ux: no -- backend + API + MCP only this iteration (Frontend Present: no, per the phase
  spec's own Goal Mode Metadata).

## Frontend Present

Frontend Present: no

(UI pipeline stages — ui-impact-analyst, ui-test-designer, browser-qa-agent, ux-regression-reviewer
— are N/A-stubbed. QA + the goal-evaluator verify J-02 via live REST + MCP probes, mirroring how
backend-only J-01 was verified in iter-1.)

## Files to Create/Modify

- `apps/backend/app/research/setups.py` -- NEW. Sole owner of the touch-event/case-registry
  computation; consumes `compute_tradability` verbatim per session.
- `apps/backend/app/config.py` -- ADD the panel/reaction/horizon/re-arm/retention constants near the
  `tradability_*` block (~line 1150-1230); ADD each to the `config_fingerprint` exclusion set
  (~line 1494+ block).
- `apps/backend/app/research/routes.py` -- ADD `GET /research/setups` (mirror `list_bar_series`,
  line 1705) + `GET /research/setups/{id}` (mirror `get_backtest`/`get_dataset`); import from
  `.setups`.
- `apps/backend/app/mcp/__init__.py` -- ADD `"setups": "/research/setups"` to `_STATIC_PATHS`
  (line ~84-95) + a `setups` `types.Tool` entry (mirrors the `datasets` tool, line ~178-186).
- `apps/backend/tests/fixtures/yahoo/` -- EXTEND the 5m AAPL fixture (or add a new committed slice)
  through at least 2026-06-22 + the chosen forward-return horizon; the 1d fixture already covers
  this range.
- `apps/backend/tests/test_setups.py` -- NEW. Pure/module-level unit tests (mirrors
  `test_tradability.py`'s synthetic + real-fixture structure).
- `apps/backend/tests/test_setups_api.py` -- NEW. Route-integration tests (mirrors
  `test_tradability_api.py`).
- `apps/backend/tests/test_mcp_server.py` -- MODIFY. Add `setups` tool tests (byte-identity,
  `EXPECTED_TOOLS`, backend-down args map).
- `docs/handoffs/goal-tradable_wall-iter-2-dev.md` -- NEW. Dev handoff.

## Explicitly Out of Scope (per phase spec — do not build)

No `structure_tape_map` strategy registration or `backtests.py`/`edge_report.py` change (J-04); no
credentialed Alpaca recording or `DatasetStore` writes (J-03) — the drill-in's `tape_timeline` field
stays present-but-empty; no `/structure` or cockpit UI of any kind (J-05/J-06 — Frontend Present:
no); no mutation of `tradability.py`, `levels.py`, the tape engine, `backtests.py`, or
`config_fingerprint` (`setups.py` only READS the map/levels); no champion/promotion/sweep/nav
changes; no bulk/ambient recording of anything — the panel bar fetch is BARS only, via the existing
keyless Yahoo path, never tick/trade/quote recording (which stays J-03's credentialed act).

## Key Test Scenarios

- `GET /research/setups` returns **≥15 band-touch events across ≥8 of the 12 panel symbols** (after
  the panel-population prerequisite runs against the live store).
- The pinned **AAPL 2026-06-22** event on the ~300–302 resistance band appears with reaction
  **`rejected`** and **negative** forward-return field(s).
- **No-lookahead consecutive-session**: shifting a scan's `as_of` earlier never changes an
  already-emitted event; each session's map derives only from bars completed strictly before that
  session (the per-session `as_of` risk called out above).
- **Reaction-classification regression under intraday density**: a realistic multi-timeframe/5m
  slice (never daily-only) with a guard that bites — e.g. a shallow high-volume intraday touch must
  not be misclassified as the pinned daily rejection (the iter-1 lesson, applied here).
- **Determinism**: repeat scans are byte-identical. **REST == MCP**: byte-identical bodies for
  `setups`.
- `config_fingerprint` stays `4d665603569b9dbf` (fingerprint-stability test + real-threshold
  counter-test).
- `GET /research/setups/{id}` returns band + reaction + forward returns; unknown id -> 404; malformed
  filter (bad reaction/class/symbol) -> 422.
- Error cases: symbol with no bar series -> honest empty (no events, no crash); a session with a
  zero-band morning map -> no events for that session (never fabricated).
- **Frozen foundations**: `levels.py`/`tradability.py`/`backtests.py`/tape engine/`BarStore`/Alpaca
  paths absent from the diff; engine equivalence 22/22 green.
- **J-01, J-07 stay green** (required-still-passing per the phase spec's Goal Mode Metadata): the
  full backend suite passes with zero deletions/weakenings (iter-1 baseline: 1240 collected / 1234
  passed / 6 skipped).
