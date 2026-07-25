# Goal Iteration 3 — The screen: pinned inputs, append-only snapshot, deterministic rank (J-03)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-02, J-07
- **Anti-goal reminders:**
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Membership is never a signal.** Universe membership (and any constituents metadata) selects WHAT to screen; it never enters a computation, rank formula beyond selection, feature, or report as an input value. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **No new statistics, gates, or strategies.** No probability/expectancy/edge claims on any desk surface; champion, `v1`, `default`, gates, and minimum-n floors untouched (the Referee is a future era). *(critical)*
  - **The ledger never holds orders.** No sizes, tickets, entries/exits, or account concepts in any desk record — rail 1 in desk terms. *(critical)*
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged by the sentinel every iteration. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no advice, imperative, prediction, or ranking language implying action ("buy", "watch this", "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*

## GOAL

An operator (or the CLI) can trigger a deterministic, append-only "screen" — one pass over the
latest registered universe snapshot, as-of a given screen date, that summarizes each member's
canonical tradable-map structure into a ranked row (or an honest skip) — and read it back byte-
identical on every re-run, with zero new `Config` fields and zero diff on any frozen research
module.

## BACKGROUND

J-03 is iter-2's own explicit next-step recommendation and `docs/goal.md`'s next journey in stated
dependency order (J-01 → J-02 → J-03 → J-04 → J-05 → J-06): it unblocks J-04 (the `/desk` page needs
a screen to render), J-05 (drill-in needs a screen row to click), and J-06 (the `desk_screen` MCP
tool needs the endpoint proven in both empty and populated states — build anchors: "J-06 becomes
buildable only after J-03"). Depth is **full** under trigger 2 (a brand-new persisted, append-only
data kind — the screen-snapshot store — mirroring J-01's `desk_universe.py` precedent) and trigger 1
(a second compute manager plus a byte-for-byte cross-module contract spanning `tradability.py`,
`bar_index.py`, `desk_coverage.py`, and `datasets.py` — failure modes cross more than three modules'
interactions, none covered by one journey's existing tests).

This spec carries forward iter-2's evaluator recommendation verbatim (T-6 as-of-never-`now()`, the
bar-store-signature-via-index-only rule, per-`(symbol,timeframe)` coverage truth) and applies two
lessons directly: `lessons.md` iter-1 (a new `Config` field re-strands `edge_report_cache.
_config_content_hash`, re-arming the real-data cache-cold trap) and `lessons.md` iter-2 (a synthetic
`AAA…EEE` fixture can silently hide what goal.md's LITERAL real-symbol acceptance actually requires
— this spec's TCs below run against the real committed universe fixture + real AAPL/AMD/MSFT bars,
never a synthetic stand-in). Stays backend/CLI-only (`Frontend Present: no`), matching J-01/J-02's
own cadence — `/desk` is J-04's job, a separate future iteration.

## IN SCOPE

### Backend

- [ ] New `apps/backend/app/research/desk_screen.py`: the append-only screen-snapshot store
  (mirrors `desk_universe.UniverseStore`'s discipline exactly — checksum-verified load on every
  read, `record()` is the only mutation and refuses/returns-the-existing-snapshot on an identical
  5-pin key, structurally immutable — no update/delete function anywhere) plus the row-computation
  function that walks the LATEST universe snapshot's members through `compute_tradability`
  (`tradability.py:381`, canonical, byte-for-byte reuse — zero diff), `desk_coverage.
  get_desk_coverage` (reused verbatim for each row's coverage badge — zero re-derivation), and
  `DatasetStore.list()` (tick-evidence badge — 11 recorded symbols at era open).
- [ ] A desk-screen compute manager (new module, e.g. `desk_screen_compute.py`, or folded into
  `desk_screen.py` — developer's call) mirroring `EdgeReportComputeManager`/
  `DeskTopupComputeManager`'s single-flight/progress/cancel shape, triggered per an explicit,
  REQUIRED `screen_date`; an identical-pin trigger over an ALREADY-recorded snapshot returns it
  without recomputing or rewriting (T-6/append-only — see NOTES for the exact rank/pin design).
- [ ] Extend `apps/backend/app/research/desk_routes.py` (the existing J-01/J-02 router) with
  `GET /research/desk/screen` (latest + `?date=` + a lightweight snapshot list),
  `POST /research/desk/screen/compute` (trigger), `GET /research/desk/screen/compute` (poll),
  `POST /research/desk/screen/compute/cancel` (cancel) — mirrors `/research/desk/topup/compute*`
  exactly.
- [ ] A CLI warmer (`main()`, mirroring `desk_topup_compute.py`/`edge_report_compute.py`'s exact
  precedent) taking a REQUIRED `--date` argument — never defaulting to today's wall-clock date.
- [ ] Zero new `Config` field: resolve the screen store's directory via a bare env-var-or-sibling-
  of-`desk_universe_dir_resolved()` default (the `resolve_cache_db_path` pattern) — explicitly NOT
  a `desk_screen_dir` Config field (see NOTES + `assumptions.md` iter-3 for the full reasoning).
- [ ] Unit/integration tests: the store (append-only refusal, checksum verification, corrupt-file
  honesty), the row computation (rank order, both skip reasons, byte-for-byte cross-check vs
  `GET /research/tradability` on the real fixture), the compute manager (single-flight, cancel,
  GET-never-computes, identical-pin no-rewrite), the routes (honest-empty, `?date=`, 422 on a
  missing `screen_date`), and the CLI (`--date` required).

### Frontend

None this iteration (`Frontend Present: no`). No `/desk` page, no `/structure` change — J-04/J-05
ship those in later iterations.

### New user-facing capability

None this iteration. The operator can trigger a screen via `POST` or the CLI and read it back via
`GET`, but there is no UI page yet.

### New information displayed

None (backend/CLI-only; no UI surface ships this iteration).

### New user actions

None (no UI surface ships this iteration; the CLI/POST/GET triggers below are operator/API actions,
not UI controls).

### UI surface changes

None.

### Product surface delta

None visible to an end user this iteration — the product's UI is unchanged. The desk gains a new,
API/CLI-reachable capability (the screen) that J-04 will surface on `/desk` in a later iteration.

### Blueprint conformance

No new page ships this iteration. The new Data-Contract rows below are registered under the
EXISTING `blueprint.md` Information-Architecture "Desk" section's already-present J-03 row
("backend POST/CLI compute; served to `/desk`") — no nav-skeleton change, no reapproval file
needed.

### Data-contract additions

Both rows below finalize placeholders `blueprint.md` already carried since iter-0/iter-2 (this spec
also writes them into `blueprint.md` directly, per the goal-decomposer's standing instruction to
keep the blueprint current):

1. **Screen snapshots, rank rows, skip rows** — computed by `app/research/desk_screen.py`; served by
   `GET /research/desk/screen`. Snapshot shape: `{id: str, screen_date: str (YYYY-MM-DD),
   as_of: str (ISO), universe_snapshot_id: str, config_fingerprint: str, bar_store_signature: str,
   created_utc: str, rows: [...], skipped: [...]}`. Ranked row: `{symbol: str,
   side: "support"|"resistance", band_class: "A"|"B"|"C"|null, distance_bps: float >= 0,
   band_score: float, price_low: float, price_high: float, coverage: {<tf>: {has_bars: bool,
   latest_window_end_utc: str|null}}, tick_evidence: bool}`. Skip row: `{symbol: str,
   skipped: true, reason: "no_bars"|"no_basis", coverage: {...same shape...},
   tick_evidence: bool}`. `GET /research/desk/screen` (no params) →
   `{"screens": [...lightweight meta only — id/screen_date/as_of/universe_snapshot_id/
   config_fingerprint/bar_store_signature/created_utc/counts, NEVER the full rows/skipped arrays...],
   "latest": <full snapshot>|null}` (honest-empty, HTTP 200, never 404). `?date=YYYY-MM-DD` →
   `{"screen": <full snapshot for the latest recording on that date>|null}`.
2. **Screen compute progress** — computed by the new desk-screen compute manager (mirrors
   `EdgeReportComputeManager`/`DeskTopupComputeManager`); served by `POST /research/desk/
   screen/compute` (trigger, body `{"screen_date": "YYYY-MM-DD"}` REQUIRED — 422 if absent),
   `GET /research/desk/screen/compute` (poll), `POST /research/desk/screen/compute/cancel`
   (cancel). Snapshot shape: `{id: str, state: "running"|"done"|"cancelled"|"failed",
   screen_date: str, started_utc: str, finished_utc: str|null, error: str|null,
   progress: {members_total: int, members_done: int, current: str|null}}`. Process-scoped
   bookkeeping only — never a research value.

## OUT OF SCOPE

- J-04 (`/desk` page), J-05 (screen-history + `/structure` drill-in prefill), J-06 (MCP v3, 17
  tools) — separate future iterations; J-06 is unbuildable until this iteration ships.
- A `desk_screen_dir` `Config` field — explicitly rejected this iteration (see NOTES); use the bare
  env-var/sibling-default resolver instead.
- Any change to `tradability.py`, `levels.py`, `bars.py`'s existing methods, `bar_index.py`'s
  existing methods, `desk_universe.py`, `desk_coverage.py`, `routes.py`, `config.py`, `main.py`,
  `meta.py`, `mcp/__init__.py` — all reused verbatim; zero diff expected on every one of these
  files.
- A real ~100-symbol screen over real bar data — an explicit operator-run act (goal.md's own
  framing: "a real screen over real bars is an operator-run act"); this iteration ships the
  capability, verified keyless against the committed fixture.
- The optional `UniverseStore.latest()` DRY cleanup the iter-2 coherence audit flagged (collapsing
  four independent `records[-1]` call sites into one accessor) — genuinely optional, not required
  this iteration; a 5th `records[-1]` call site here is acceptable (advisory-only finding).
- Repaying `desk_topup_compute.py`'s carried-forward test-net debt (3 CLI `main()` tests, 1
  populated route-level coverage assertion, the composite cancel/resume test) — carried forward
  again; J-03 is already full-depth and heavy, and none of these three files are touched by design
  (desk_screen.py has no import reason to touch desk_topup_compute.py).
- Warming the `_config_content_hash`-stranded caches and re-pointing `journey-scripts/J-07.json`
  step 8 off the async `300.11` text — both still deferred to whichever iteration runs J-04's
  browser pass. This iteration adds no new `Config` field, so the stranding does not worsen.

## DEFINITION OF DONE

- [ ] Target journey J-03 passes via the evaluator's own executed acceptance clauses (byte-for-byte
  cross-check against `GET /research/tradability`, deterministic re-run, append-only refusal,
  honest skip rows) — TC-1 through TC-19 below.
- [ ] Required-still-passing journeys J-01, J-02, J-07 remain green (suite + pin + kept-route
  byte-identity; no browser pass this iteration, `Frontend Present: no`).
- [ ] No anti-goal violation introduced — the 12 reminders above, especially: membership never a
  signal, snapshots append-only and never rewritten, every run an explicit operator act, the
  ledger never holds orders, the fingerprint pin unchanged.
- [ ] Unit tests pass; suite count >= iter-2's floor (1240 passed / 8 skipped / 0 failed); zero diff
  on every frozen owner named in OUT OF SCOPE.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-3-dev.md`.

## TESTING REQUIREMENTS

- Browser: none this iteration (`Frontend Present: no`).
- Unit/integration: TC-1 through TC-19 below, executed against the REAL committed universe fixture
  (`tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json`, 103 members) and the real
  AAPL/AMD/MSFT bar fixtures already used by `test_tradability.py`/`test_mcp_server.py` — never a
  synthetic `AAA…EEE` stand-in for the clauses that name real symbols (lessons.md iter-2).
- Error cases: missing `screen_date` on the compute trigger (422), an idle cancel (409), a
  corrupted/tampered snapshot file (an honest, explicit integrity error — never silence, never a
  fabricated snapshot — mirrors `UniverseIntegrityError`), a partially-covered symbol (MSFT-shaped:
  some but not all pinned timeframes) never silently mis-skipped.

Test-first contract — TC- scenarios (every DEFINITION OF DONE checkbox and Data-contract addition
above maps to at least one line below):

- TC-1: given the committed fixture universe + the real AAPL fixture bars (the SAME ones
  `test_tradability.py`'s pinned 2026-06-22 scenario uses), when a screen is triggered for
  `screen_date` matching that same pinned session, then the persisted snapshot's AAPL row's
  `band_class`/`distance_bps`/`band_score`/`price_low`/`price_high` are byte-identical to what
  `GET /research/tradability?symbol=AAPL&as_of=<the as_of desk_screen.py derived>` returns for the
  band `desk_screen.py` selected as AAPL's "best" (see NOTES for the selection rule).
- TC-2: given the same fixture universe, when the screen computes MSFT's row (bars on `1h`/`1d`
  only, per iter-2's real-store finding — NOT `1w`/`4h`), then MSFT still resolves a ranked row
  (never mis-skipped merely for partial pinned-timeframe coverage), and its `coverage` field
  reports `1h`/`1d` `has_bars: true` and `4h`/`1w` `has_bars: false`.
- TC-3: given the fixture universe's ~100 members with zero recorded bars on any timeframe, when
  the screen completes, then every one of them appears in `skipped` with `reason: "no_bars"` and
  none appears in `rows`.
- TC-4: given a screen already persisted for `screen_date=D` under a fixed universe/bar-store
  state, when the identical `screen_date` is triggered again with that state unchanged, then the
  manager/store returns the EXISTING snapshot (same `id`) rather than writing a second file, and a
  direct re-computation of the row content (if triggered) is byte-identical to the first run's.
- TC-5: given no screen has ever been computed, when `GET /research/desk/screen` is called, then it
  returns HTTP 200 with `{"screens": [], "latest": null}` — never 404, never a fabricated row.
- TC-6: given a persisted screen for `screen_date=D`, when `GET /research/desk/screen?date=D` is
  called, then it returns that exact snapshot's `rows`/`skipped` verbatim (byte-equal to what was
  persisted at compute time) — never recomputed on the GET.
- TC-7: given an in-flight screen-compute job (`state: "running"`), when a second
  `POST /research/desk/screen/compute` is triggered concurrently, then the response reports
  `started: false` and returns the SAME job unchanged (single-flight — mirrors J-02's proven topup
  contract).
- TC-8: given an in-flight job, when `POST /research/desk/screen/compute/cancel` is called, then
  the polled state transitions to `"cancelled"` with `finished_utc` set and fewer than
  `members_total` processed; given no job has ever run (or the last one is already terminal), a
  cancel call returns HTTP 409.
- TC-9: given `POST /research/desk/screen/compute` is called with an empty body (no `screen_date`),
  then it is rejected with HTTP 422 — the endpoint never defaults to the current wall-clock date.
- TC-10: given the same `screen_date` and an unchanged universe/bar-store state, when the row
  computation runs twice in two separate fresh test processes, then the two results' `rows`/
  `skipped` content is byte-identical (no wall-clock, no unseeded randomness anywhere in the path).
- TC-11: given a symbol with a daily bar series but for which `compute_tradability` cannot resolve
  a prior session (`no_bar_series_for_symbol: false`, `basis_as_of: null`), when the screen
  computes that symbol's row, then it appears in `skipped` with `reason: "no_basis"` (distinct from
  `"no_bars"`), and its `coverage` field still honestly reflects whichever pinned timeframes DO
  have bars (never all-false when bars genuinely exist).
- TC-12: given the fixture universe + populated bar store, when the screen completes, then every
  row's (ranked or skipped) `coverage` field is byte-identical to the corresponding member's
  `per_timeframe` block returned by `desk_coverage.get_desk_coverage` for the SAME universe
  snapshot (proving reuse, not re-derivation).
- TC-13: given the 11 recorded dataset symbols (AAPL, AMD, AMZN, GOOGL, META, MSFT, NFLX, NVDA, PG,
  SPY, TSLA — goal.md's own build-anchors list) registered in the dataset store, when the screen
  computes rows/skips touching those symbols, then their `tick_evidence` is `true`; every other
  member's `tick_evidence` is `false`.
- TC-14: given a completed screen with at least two distinct resolved band classes among its
  ranked rows, when `rows` is inspected, then it is sorted by exactly `(band_class rank
  A>B>C>null desc, distance_bps ascending, band_score descending, symbol ascending)`.
- TC-15: given a screen computation in progress, when `bar_store_signature` is derived, then it is
  instrumented at exactly 0 `BarStore.list`/`BarStore.get` calls during derivation (sourced
  entirely from `bar_index`/`desk_coverage` reads) — never a re-hash of the JSON bar files (T-4).
- TC-16: given `Config().config_fingerprint()` printed before and after this iteration's full diff,
  then the value is unchanged (`08e471b10130e1e2`) — zero new `Config` fields are added.
- TC-17: given the full backend suite, when it runs after this iteration's changes, then it passes
  with a count >= iter-2's `1240 passed / 8 skipped / 0 failed` floor, and every guard test
  (`test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, the 13 fingerprint pin
  assertions) passes byte-unmodified.
- TC-18: given the CLI warmer invoked with no `--date` argument, then it exits non-zero with an
  explicit usage error (never silently using today's date); given `--date 2026-06-22` (or the
  fixture's pinned date) against a scoped test/fixture dir, then it runs to completion and prints a
  ranked/skipped summary count.
- TC-19: given the resolved "best" band for a real fixture row (e.g. AAPL), when `distance_bps` is
  computed, then its reference close price is read via a plain, existing `BarStore` lookup of the
  ONE daily bar dated at `basis_as_of` (a value `compute_tradability` already returns) — verified
  against that fixture bar's own recorded close value — and `git diff` on `tradability.py` and
  `levels.py` is empty (adding a field to either frozen module's return shape is a FAIL; see NOTES).

## NOTES

**as_of translation (T-6).** `as_of` must be a deterministic function of the operator-given
`screen_date` alone, never `datetime.now()`. Reuse `/structure`'s OWN existing plain-date
convention (`apps/frontend/app/structure/page.tsx` ~:260, `{date}T23:59:59Z`) rather than inventing
a new one: `compute_tradability`'s as-of resolution is a CALENDAR-DATE comparison ("the last
completed daily bar strictly before the requested session's own UTC calendar date"), so an as_of
dated anywhere inside `screen_date`'s own calendar day resolves the SAME prior-session basis
`/structure`'s Load form already proves for that date (confirmed live: `test_tradability.py`'s own
pinned golden — `as_of="2026-06-22T15:00:00Z"` resolves `basis_as_of="2026-06-18T04:00:00.000000Z"`
— the SAME "AAPL 2026-06-22" scenario goal.md's J-05/J-07 acceptance text already names). This is
what makes J-05's future drill-in ("clicking AAPL... still renders the SAME 300–302.4 walls") hold
by construction, and gives this iteration a zero-new-fixture-risk golden input (TC-1). Do NOT copy
the top-up's wall-clock fetch-window pattern (`_TOPUP_LOOKBACK_DAYS`) — that governs a DIFFERENT
concept (a fetch horizon) and does not apply here.

**"Best band" selection + `distance_bps` (logged: `assumptions.md` iter-3, entry 1).** Per symbol,
select the band minimizing `(class rank A=3/B=2/C=1/null=0 — as a DESCENDING preference, distance_bps
ascending, quality_score descending)`, iterating `compute_tradability`'s own already-deterministic
served band order so a tie resolves identically every run. Use that SAME tuple (plus `symbol asc`)
to order the final `rows`. `distance_bps` for a candidate band = `abs(edge_price - close) / close *
10000`, where `edge_price = band["price_low"]` for a `"resistance"` band, `band["price_high"]` for
`"support"` (the near edge to price — correct by construction, since `compute_tradability`'s own
side split guarantees `price_low`/`price_high` are already the closest member on the relevant side).

**Reference close price (logged: `assumptions.md` iter-3, entry 2).** `compute_tradability`/
`compute_levels` do NOT serve a `current_price`/close field, and adding one would break existing
exact-dict-equality assertions in `test_tradability.py` — a "Frozen foundations" violation. Resolve
it via a plain `BarStore` read (the same `merged_bars`-style accessor `tradability.py` already uses
internally) of the ONE daily bar dated at the already-returned `basis_as_of` — never re-deriving
WHICH bar is the basis, never touching `tradability.py`'s or `levels.py`'s return shape (TC-19).

**Bar-store signature (T-4).** Derive it entirely from `desk_coverage.get_desk_coverage`'s own
per-member × per-timeframe read (already `bar_index`-backed, already proven index-fast in J-02) —
e.g. a checksum over the sorted `(symbol, timeframe, latest_window_end_utc)` tuples for the
universe's members × `DESK_TOPUP_TIMEFRAMES`. Never a `BarStore`/JSON-file re-hash (the 5C 31.4s
mistake T-4 exists to prevent) — TC-15 enforces this by instrumentation, mirroring J-02's own proof
technique.

**No new `Config` field (logged: `assumptions.md` iter-3, entry 3).** The screen store's directory
is a bare `TAPEOLOGY_DESK_SCREEN_DIR`-env-var-or-sibling-of-`desk_universe_dir_resolved()` default
(the `resolve_cache_db_path`/`resolve_backtest_cache_db_path` pattern — `edge_report_cache.py:188`)
— never a `desk_screen_dir` Config field. This keeps `config_fingerprint()` AND
`edge_report_cache._config_content_hash` both untouched this iteration (the latter is already
stranded from iter-1's move and still un-warmed; this choice does not deepen that debt).

**Skip reasons.** Exactly two, never conflated: `"no_bars"` = `compute_tradability`'s own
`no_bar_series_for_symbol: true`; `"no_basis"` = a daily series exists but no session resolves
(`basis_as_of: null`, `bands: []`). Both are honest, distinct absences — never guessed, never
silently merged into one vague "skipped" bucket.

**Compute-manager placement.** Unlike `DeskTopupComputeManager` (forced off `ResearchRegistry` to
avoid a circular import through `record_bar_series`), `desk_screen.py` has no such constraint — it
never needs anything from `routes.py`. Prefer the `EdgeReportComputeManager`-on-`ResearchRegistry`
placement (goal.md's own named model), but either placement is acceptable as long as single-flight/
progress/cancel semantics hold; developer's call.

**Screen list stays lightweight, deliberately UNLIKE `GET /research/desk/universe`'s list (which
returns full records for every snapshot).** A universe snapshot is KB-scale (iter-1's own
docstring); a screen snapshot carries ~100 rows each with a nested `coverage` object and is
materially larger — returning full content for every historical snapshot in one list call risks
repeating the 5C latency mistake at a smaller scale. `GET /research/desk/screen`'s list entries are
meta-only; only `latest` and the `?date=` lookup carry full `rows`/`skipped`.

**Applies from lessons.md:** iter-1's Config-field/`_config_content_hash` trap (directly resolved
by the zero-new-field decision above); iter-2's synthetic-fixture gap (this spec's TCs run against
the real committed fixture + real AAPL/AMD/MSFT bars, never a synthetic stand-in); iter-0's
async-golden-text trap (not this iteration's concern — no browser pass — but do not touch
`journey-scripts/J-07.json`, it is still pending for J-04).
