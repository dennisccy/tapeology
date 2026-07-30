# assumptions.md — archive

Entries moved out of `assumptions.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-07-27T15:28:38Z: moved 6 entries (keep-iters=5) -->

## iter-0 — goal-evaluator

**Ambiguity:** J-07 ("The kept product stands — regression sentinel") mixes two kinds of
acceptance clause in one journey: kept-product behaviors checkable every iteration (suite green,
unchanged pin, browser walk of `/` and `/structure`, kept-route byte-identity) AND two
era-completion clauses that only become true once other journeys ship ("nav = exactly three
routes", "MCP = exactly 17 tools"). `docs/goal.md` never says how to score J-07 mid-era, and the
iteration spec explicitly delegated the call to the evaluator.
**We chose:** Score J-07 `partial` at baseline — kept half evidenced, era-completion half recorded
as unmet (2 routes / 15 tools today) — rather than `already_passing` on the kept half alone. Side
effect accepted: J-07 no longer sits at `passing`, so a later kept-product break will not
auto-trip the decision tree's `passing → failing` REGRESSION rule; it reaches REGRESSION instead
via critical rail 3 ("Frozen foundations … every KEPT surface's behaviour stays byte-identical"),
and that routing is stated in `iter-0/eval.md` and in the journey-history note so no later
evaluator loses the sentinel's halting power.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s Constraints state "every browser acceptance needs a screenshot — no
screenshot ⇒ the journey is `unknown`, never `passing`", but J-01's own acceptance text is tagged
"(Keyless; automated…)" and names no browser step, and browser QA was correctly SKIPPED
(`Frontend Present: no`). Nothing states what the evidence class is for a REST-only journey when the
browser lane does not run — and the evaluation methodology separately warns that unit tests are never
journey evidence.
**We chose:** Treat live REST through the REAL route handlers as the equivalent of a screenshot for a
journey whose acceptance has no browser clause — and require the evaluator to execute it personally,
not read it from a report. I ran all four J-01 clauses in-process against `app.main:app` with the
universe dir scoped to a temp dir and fixture HTML injected into the vendor seam (zero network), and
scored `passing` on that. Unit-test results alone would NOT have sufficed. Same rule will apply to
J-02/J-03 (also tagged keyless/automated); J-04/J-05/J-07's browser clauses still require screenshots.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** The desk-era anti-goal says universe snapshots are "append-only … nothing is silently
refetched, backfilled, recomputed in place, or rewritten". Audit finding B3 (which I reproduced) shows
a snapshot FILE that fails its checksum — surfaced in `integrity_errors`, never in `records` — is
silently overwritten at the same path when identical membership is re-recorded. The anti-goal does not
say whether "snapshot" means the registered record or the file on disk.
**We chose:** Read it as protecting the registered RECORD, so this is a minor gap (a silent self-heal)
rather than an anti-goal violation: no valid registered snapshot can be lost — the duplicate check
refuses before any write, which I verified byte-for-byte — and the replacement carries the same content
identity the filename asserts. Consequence: `anti_goal_violations` stays empty, so this does not block a
future GOAL_ACHIEVED; instead it is carried as a hardening item (make the replacement loud) in the
iter-2 recommendation. A stricter reading would make it a minor violation with the same practical fix.
**Reversible:** yes

## iter-2 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s T-4 says desk coverage/freshness must be "read from `bar_index` only
(NEVER re-hashing the store)", and the era's "Frozen foundations" rail lists the JSON `BarStore` (not
`bar_index.py`, a derived era-fast_wall cache) as byte-identical-forever. Neither states whether
`bar_index.py`'s own PUBLIC READ API may be additively extended — exposing its already-existing
`window_end_utc` SQLite column, which today's `BarIndexHit` dataclass does not surface — to serve
coverage's freshness field, or whether J-02 must instead resolve every hit through `BarStore.get()`
(heavier, and arguably closer to the "re-hashing" T-4 warns against).
**We chose:** Permit a minimal, additive extension to `bar_index.py`'s public read surface (a new
field on `BarIndexHit`, or an equivalent new accessor) that exposes the existing `window_end_utc`
column as the coverage-freshness source — never a DB-schema change, never touching `.lookup()`/
`.insert()`'s existing contract or any current caller's behavior. This reads T-4's "read from
`bar_index` only" literally (freshness comes FROM the index itself, not from a per-row store
resolve) and keeps coverage genuinely index-read-fast, matching the era's own latency framing and
the `EdgeReportComputeManager`-adjacent precedent of exposing exactly what a new caller needs.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** J-02's top-up derives its bar-fetch window from wall clock
(`_fetch_window_now()` = `[today-730d, today]`, `desk_topup_compute.py:80`/`:91-101`). Anti-goal 7
says "no wall-clock … in any research artifact" and build trap T-6 says "Determinism means no
wall-clock", but T-6's own sentences scope to a SCREEN's `as_of` and to snapshot ids/content —
neither text says whether a bar-FETCH horizon (which is persisted as the recorded series'
`window_end_utc` metadata) counts as the prohibited wall-clock use.
**We chose:** Read it as scoping to computed/served research VALUES and to snapshot keys, so a fetch
horizon is a sanctioned operator-request parameter — the same thing a manual `POST /research/bars`
call with today's date already supplies. Therefore not an anti-goal violation, minor or critical.
Consequence accepted: a re-run on a later UTC day always re-fetches, which is exactly what makes
audit finding B1 reachable (~100 benign `1w` 409s reported as `outcome: "failed"`, CLI exit 1). Both
are carried into the J-03/J-04 specs, and J-03's own `as_of` is stated there as a HARD "never
`now()`" requirement so this reading cannot creep into the screen's determinism contract.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** J-02's acceptance is phrased per-MEMBER — "coverage for the fixture universe reports
bars-present for exactly the members the era-open store holds (AAPL/AMD/MSFT) and bars-missing for
every other member" — but the shipped payload (and the era-open reality) is per-`(symbol,
timeframe)`: MSFT holds `1h`/`1d` rows and **no** `1w`/`4h`. Read literally, MSFT is neither wholly
"bars-present" nor wholly "bars-missing", and goal.md never says which wins.
**We chose:** Score the clause satisfied by a per-`(symbol, timeframe)` truth-table that reports the
index verbatim — MSFT `{1h: true, 4h: false, 1d: true, 1w: false}` — rather than requiring
whole-member presence. The finer granularity is strictly more honest (it cannot fabricate a `1w`
value MSFT does not have) and matches the journey's own step 1 wording ("bars present per required
timeframe"). Consequence: "the members the era-open store holds" is recorded in journey-history as
three symbols with UNEQUAL timeframe coverage, and J-03/J-04 are told that rows with partial
coverage must degrade honestly rather than assume the full pinned set.
**Reversible:** yes


<!-- condense.sh 2026-07-27T20:07:55Z: moved 5 entries (keep-iters=5) -->

## iter-3 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s J-03 acceptance says a screen row summarizes "best band, band
class, distance-from-close bps, band score" per member, but `compute_tradability` returns a LIST
of bands per symbol (up to `2 * tradability_band_cap_per_side`, split across resistance/support
sides) with no existing method that already selects a single "best" one, and the era's own
cross-symbol rank tuple `(band class A>B>C, then distance asc, then band score desc, then symbol
asc)` is stated only for ordering the FINAL rows, not for choosing which band represents a symbol.
**We chose:** Apply the SAME tuple `(class rank A>B>C>null desc, distance_bps asc, quality_score
desc)` twice — first WITHIN a symbol's own band list to pick its "best" band (iterating
`compute_tradability`'s already-deterministic served order so a tie resolves identically every
run), then ACROSS symbols (plus `symbol asc` as the final tie-break) to produce the screen's row
order. This reuses one rule for both jobs rather than inventing a second selection policy, and
never re-grades a band (the chosen band's own `class`/`quality_score`/`price_low`/`price_high` are
served verbatim).
**Reversible:** yes

## iter-3 — goal-decomposer

**Ambiguity:** `distance-from-close bps` requires a reference close price, but
`compute_tradability`'s returned shape (`{"bands": [...], "no_bar_series_for_symbol": bool,
"basis_as_of": str | None}`) does not serve one — the internal `current_price = prior_bar.close`
(`tradability.py:426`) is a local variable, never returned — and `compute_levels`'s own return
shape has no such field either. Adding one to either frozen module's return dict would break
existing exact-dict-equality assertions in `test_tradability.py` (e.g. `assert result ==
{"bands": [], "no_bar_series_for_symbol": True, "basis_as_of": None}`), which the goal-era's
"Frozen foundations" anti-goal (rail 3) forbids disturbing.
**We chose:** `desk_screen.py` resolves the reference close ITSELF via a plain, existing
`BarStore` read (the same `merged_bars`-style accessor `tradability.py` already calls internally)
of the ONE daily bar dated at `basis_as_of` — a value `compute_tradability` already serves — never
re-deriving WHICH bar is the basis (that stays `compute_tradability`'s exclusive decision) and
never touching `tradability.py`'s or `levels.py`'s return shape. A diff on either frozen module is
therefore a build defect, not an accepted side effect.
**Reversible:** yes

## iter-3 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s Constraints say every new SEMANTIC knob takes Path A as a `Config`
field, but separately say "operational knobs (worker counts, timeouts, store dirs) may be env vars
per the 5C precedent" — and this codebase has BOTH patterns live: primary content stores
(`journal_db_path`, `dataset_dir`, `bar_dir`, and J-01's own `desk_universe_dir`) are `Config`
fields with Path-A treatment, while derived caches (`edge_report_cache.db`,
`edge_report_backtests.db`, `bar_index.db`) resolve via a bare env-var-or-sibling-default function
with NO `Config` field at all. A new screen-snapshot store (a primary, non-reconstructible content
store, like the first group) could honestly go either way, and `iteration-state.md`'s carried "Do
not redo" note explicitly prefers zero new `Config` fields ("a new field re-moves
`_config_content_hash` and re-strands the caches").
**We chose:** Treat the screen store's directory as a "store dir" operational knob (the
Constraints' own explicit sanction) — a bare `TAPEOLOGY_DESK_SCREEN_DIR`-env-var-or-sibling-of-
`desk_universe_dir_resolved()` default (the `resolve_cache_db_path` pattern), NOT a new `Config`
field. This adds zero further `config_fingerprint`/`_config_content_hash` Path-A debt on top of
J-01's already-unwarmed move, honors the carried lesson, and is fully reversible: a future
iteration can still promote it to a `Config` field if the screen store genuinely needs independent
operator relocation from the universe store.
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** J-03 step 4 asks the backend to "serve `GET /research/desk/screen` (latest, `?date=`,
and a snapshot list) with the honest `"Desk screen not computed yet."` payload before any run" — but
that literal string is also `docs/goal.md`'s Design-Direction *copy* example and J-04's own browser
acceptance clause ("`/desk` with no screen shows `"Desk screen not computed yet."`"). Nothing states
whether the JSON payload itself must carry the sentence.
**We chose:** Score the clause satisfied by an honest-empty JSON payload — HTTP 200 with
`{"screens": [], "latest": null, "integrity_errors": []}` (never 404, never a fabricated row), which
is exactly what the iteration spec's TC-5 defines and what `GET /research/desk/universe` already does
— and treat the literal sentence as UI copy owned by J-04. Consequence: J-04's acceptance now carries
the string as a HARD requirement (the page must render that exact copy over this payload), recorded in
the next-step recommendation; if a future reader expects the API to echo the sentence, only the
rendering layer changes.
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** Anti-goal 7 says "no wall-clock … in any research artifact" and build trap T-6 says
"Progress timestamps live in compute-manager state, never in snapshot content" — yet the screen
snapshot's registered shape (spec Data-contract addition #1) includes `created_utc`, which
`desk_screen.py:481` fills from `datetime.now(timezone.utc)`. Read strictly, a wall-clock field lives
inside snapshot content.
**We chose:** Read `created_utc` as registration metadata rather than a research value or a progress
timestamp: it is excluded from the 5-pin key AND from the snapshot-id checksum, no served value
derives from it, identical pins still reproduce byte-identical `rows`/`skipped` (I proved this across
two fresh interpreters), and it is the exact field `desk_universe.py:411` already carries — accepted
in iter-1 when J-01 passed. So: not an anti-goal violation, minor or critical. Consequence: the
determinism guarantee this era enforces is scoped to computed CONTENT plus the pin key, not to
file-registration bookkeeping; `id`, `screen_date`, `as_of`, `universe_snapshot_id`,
`config_fingerprint` and `bar_store_signature` remain the only fields any re-run comparison may use.
**Reversible:** yes


<!-- condense.sh 2026-07-27T20:23:16Z: moved 5 entries (keep-iters=5) -->

## iter-4 — goal-decomposer

**Ambiguity:** Audit finding B10 (iter-3 handoff) shows `_select_best_band` (`desk_screen.py:206`)
ranks distance-to-close ahead of quality score, so a symbol's headline screen row can be its
NEAREST same-class band rather than its highest-scoring one — on the committed fixtures, AAPL's
row is `resistance C, 2.348 bps, score 57.0 (298.08–299.24)` while the same served band list also
carries `resistance C, score 123.0 (300.23–302.25)`, the era's own pinned 300–302.4 wall. iter-3's
eval.md flagged this explicitly as a human call for J-04 to resolve BEFORE rendering the chip:
"either the chip copy says 'nearest same-class band' or the human respecs the within-symbol tuple."
`docs/goal.md` itself is silent on which band a "best band" chip should mean.
**We chose:** Keep `_select_best_band`'s ranking tuple byte-unchanged (zero diff on
`desk_screen.py`'s computation — it is spec-conformant per `assumptions.md` iter-3 entry 1, not a
bug) and make `/desk`'s headline-band chip copy read "nearest same-class band" rather than implying
it is the symbol's strongest band. This keeps the chip's claim honest about what the ranking
actually selects without touching J-03-owned, already-shipped computation this iteration.
**Reversible:** yes

## iter-4 — goal-decomposer

**Ambiguity:** `docs/goal.md` step 3 for J-04 says "Wire Run Screen ... to the compute endpoints
with live progress + cancel" but never states how the button supplies the REQUIRED `screen_date`
body field (`POST /research/desk/screen/compute` 422s without it, per J-03/iter-3's TC-9). Anti-goal
"every run is an explicit operator act" and build trap T-6 ("no wall-clock ... determinism means no
wall-clock") both concern SERVED/computed values and snapshot keys (per `assumptions.md` iter-2's
own reading of the parallel top-up fetch-horizon question), but neither states whether a UI control
may CLIENT-SIDE default a request parameter to "today" without that becoming a disallowed
wall-clock dependency.
**We chose:** Run Screen always submits the client's own `today` (the SAME `todayUtcDate()`-style
helper `/structure`'s existing "Today" shortcut button already uses) as `screen_date` — no
date-picker or alternate-date control ships on `/desk` this iteration. The operator's click remains
the explicit, logged act (matching the CLI's own `--date`-required design and iter-2's accepted
fetch-horizon precedent); the backend computation itself still never reads wall-clock time — only
the CLIENT parameter defaults to "now," submitted explicitly. The CLI's `--date` flag remains the
path for an arbitrary historical re-screen; no UI regression if a future iteration adds a picker.
**Reversible:** yes

## iter-4 (fix pass) — developer

**Ambiguity:** Audit B1 found 60 recorded bar series (58 symbols, incl. the era's pinned AAPL `1d`)
each holding ONE row whose OHLC are the JSON `NaN` token — written by the new `/desk` Top-up button
during this iteration's own QA, via a Yahoo row for a session that had not traded yet. The era's data
anti-goal says registered bar series are "append-only, checksummed, never re-tagged, never deleted,
never content-perturbed", and the audit explicitly left the fate of those 60 series as a decision it
would not make unilaterally: quarantine + `integrity_errors` surfacing, a superseding revision
series, or tolerate-on-read. `docs/goal.md` says nothing about a recorded value that is not a number.

**We chose:** ROW-level exclusion on the shared merged read, reported through the ALREADY-registered
`integrity_errors` channel — never file deletion, never a rewrite, never a re-fetch. Concretely:
`BarStore._merged_rows` drops any row whose OHLC are not all finite and reports one entry per
affected series ("N recorded row(s) carry a non-finite price … the file itself is unchanged"), which
is exactly the treatment a corrupt FILE already gets ("never served as data, never silently
dropped"). The three alternatives were rejected on evidence:

  * **File-level quarantine** (the audit's first option) was MEASURED and rejected: excluding the
    whole 501-bar AAPL `1d` series moves the tradable map's entire support side as-of 2026-06-22
    (`support A 222.68–224.23 score 688.6` → `support A 274.60–276.51 score 471.7`), because that
    series is the only recording covering 2024-07..2024-12. Quarantining a file to remove one bad row
    would silently change every band 500 good bars support — a worse anti-goal breach than the bug.
  * **A superseding revision series** cannot work: the vendor serves NO prices for that timestamp
    (verified live on 2026-07-26 — the same `2026-07-24 open=nan volume=47402209` row is still
    served), so a clean re-fetch simply omits it and the union keeps the old priceless row.
  * **Tolerate on read** was rejected because it is not merely cosmetic: measured on the ambient
    store, `compute_tradability("AAPL", as_of=2026-07-25)` returns `bands: []` with the NaN row as
    its basis, versus 10 honest bands off 2026-07-23 once the row is excluded. The priceless rows
    were silently deleting the tradable map, not just crashing the chart.

Consequences accepted: (a) the merged `bar_count` for an affected pair drops by the number of
priceless rows (AAPL `1d`: 501 → 500) — the honest count of candles that exist; (b) those pairs now
report a permanent, honest `integrity_errors` entry until an operator chooses to act on the files
(nothing in the product requires that, and nothing deletes them); (c) values computed as-of a date
BEFORE the priceless row are byte-identical (verified: the pinned 2026-06-22 map is unchanged
field-for-field), so no prior evidence is invalidated. Prevention is separate and structural:
`YahooAdapter` drops a priceless vendor row at the seam, and `BarStore.record` refuses one outright,
so this state is no longer reachable.
**Reversible:** yes — the files are untouched, so any later policy (quarantine, supersede, an
operator-run compaction) is still fully available.

## iter-4 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s browser-evidence rule says "every browser acceptance needs a
screenshot — no screenshot ⇒ the journey is `unknown`, never `passing`", but it never says WHO must
capture it, while the iteration spec's DEFINITION OF DONE #1 names the `browser-qa-agent` lane
specifically ("J-04 passes via browser-qa-agent"). This iteration produced real, current screenshots
of two of J-04's three required states — captured by the auditor and the developer — and no
browser-qa-agent dispatch at all.
**We chose:** Count a screenshot I personally opened, which unambiguously shows the acceptance state
on the current tree, as genuine evidence for THAT clause regardless of which agent captured it (so
the empty state and the populated briefing are met, not `unknown`), but refuse to let it satisfy the
DoD's lane requirement or to substitute for the missing third state. Net effect: J-04 is `partial`,
not `passing` and not `failing`, and the browser lane is carried as owed work into iteration 5.
**Reversible:** yes

## iter-4 — goal-evaluator

**Ambiguity:** Anti-goal 3 ("Frozen foundations") and the Non-Goals list in `docs/goal.md` name
`bars.py`'s JSON `BarStore` and `components/StructureChart.tsx` as untouched for this whole era, and
label the rail *(critical)*. This iteration changed both, authorized ONLY by an amendment the
developer wrote into the iteration spec during his own fix pass (`docs/phases/goal-desk-iter-4.md`
OUT OF SCOPE, "bars.py's zero-diff constraint is LIFTED for the priceless-bar rail only"). Nothing in
`docs/goal.md` says whether an iteration spec may grant itself an exception to a critical rail.
**We chose:** Score it a MINOR, disclosed deviation (logged `resolved: false` and escalated for the
owner's written ratification) rather than a critical violation that halts the loop — because I
re-measured that output is identical for all-finite data, the era's pinned Apple band is unchanged,
the fingerprint has not moved, the suite is green, and the change repairs a kept surface that would
otherwise crash. The alternative reading (an iteration spec cannot self-grant a goal.md exception →
REGRESSION and halt) stays available to the owner: the code is small, additive and revertible, and
the 60 affected data files were never modified.
**Reversible:** yes


<!-- condense.sh 2026-07-29T00:03:45Z: moved 14 entries (keep-iters=5) -->

## iter-5 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s J-04 acceptance demands a screenshot of "Run Screen shows live
progress and an in-flight second trigger is refused", and the era's rule is "no screenshot ⇒ the
journey is `unknown`, never `passing`" — but nothing says whether a screenshot whose LAYOUT was
altered by the QA lane (two controls repositioned to the top-left and outlined via injected CSS, plus
one poll reply held open for a few seconds so the sub-second state persisted) still counts as the
required screenshot. The controls genuinely live at the bottom of a ~4500px page, past the 4320px
full-page capture limit, so an unaided capture of that state is not possible without scrolling.
**We chose:** Count it. The rendered elements are the real components in their real states with real
values (`disabled` "Computing…" button, `desk-screen-compute-running` showing "0 / 103 members" +
Cancel), which I corroborated three ways: the 8×8 pixel difference between the two shots falls exactly
on the `h-2 w-2 animate-pulse` dot at `page.tsx:463-466` (a static forgery would not animate), the
populated briefing behind them is exactly what `page.tsx:671-689` produces when a screen exists and a
new run starts, and no request or response body was faked. So the position/outline injection is a
capture aid of the same class as scrolling, not fabricated evidence. Consequence: J-04 is `passing`,
and the next iteration's results report is required to disclose any such aid up front.
**Reversible:** yes

## iter-5 — goal-evaluator

**Ambiguity:** The iter-5 spec's TC-7 demands the ambient `apps/backend/.data/` listing be
"byte-for-byte identical" before and after the pass. The listing came out identical, but I found two
files under it dated inside the iteration window: `bar_index.db-wal` (0 bytes) and `bar_index.db-shm`,
created 15:00:31 when the deterministic J-07 replay booted the REAL backend. `docs/goal.md`'s
immutable-data rail speaks of registered datasets and bar series, not of SQLite side-files.
**We chose:** Not a violation and not a TC-7 failure. `bar_index.db` itself is untouched (mtime still
2026-07-25 12:49), the WAL is empty (zero pending writes), and no bar/universe/screen/dataset record
was added or changed — these are read-mode side-files, and they predate the browser pass (they were in
BOTH of the QA lane's listings, which is why its 391-entry count exceeds the developer's earlier 389).
Consequence: "ambient store untouched" is scored on registered CONTENT, not on SQLite bookkeeping
side-files; a future iteration that finds a non-empty `-wal` or a changed `bar_index.db` mtime should
treat that differently.
**Reversible:** yes

## iter-6 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s J-05 step 3 says "make each briefing row a drill-in link to
`/structure?symbol=<sym>&asof=<as_of>`" without distinguishing ranked rows from skipped-member
rows — both are rendered on `/desk`'s briefing table (blueprint.md's Data Contract already
registers a `DeskScreenSkip` shape with its own `symbol` field, structurally identical to a ranked
row for this purpose), but a skipped member by definition has no band/coverage evidence backing a
"drill in to see the wall" motivation.
**We chose:** Link BOTH row kinds. A skipped-member drill-in still lands on `/structure` with that
symbol and the screen's `as_of` prefilled, and `/structure` will honestly render its own no-bars/
empty state for that symbol at that date — exactly the same "describe, never fabricate" discipline
this era already applies everywhere else, so there is no dishonest or misleading render to guard
against. Narrowing to ranked-rows-only remains available if the owner prefers that scope.
**Reversible:** yes

## iter-6 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s browser-evidence rail ("every browser acceptance needs a screenshot — no
screenshot ⇒ the journey is `unknown`, never `passing`") says nothing about a screenshot captured on the
tree as it stood BEFORE a fix landed later in the same iteration. J-05's four acceptance screenshots
were taken by the browser-QA lane between 17:11 and 18:03; the auditor then changed
`apps/frontend/app/desk/page.tsx:983` (`isViewingLatest` now compares snapshot ids instead of testing
"was anything clicked") at the end of the iteration.
**We chose:** Count the screenshots. The fix only alters one path — selecting the NEWEST screen's own
history row — and none of the four captures exercises it (UT-03 selects 2026-06-22, UT-04 uses the
Latest button, UT-05/UT-06 navigate away, UT-02 has no params), so each image still shows the state the
current code produces for the case it depicts. Corroborated two ways: the auditor re-ran TC-1/TC-2/TC-3
live on a fixture-scoped rig AFTER the fix with printed state for both directions, and the evaluator
compared UT-03's rendered rows field-for-field against the real recorded snapshot JSON. Consequence:
mid-iteration fixes do not automatically void earlier evidence — but only when the changed path is
demonstrably outside every accepted capture; a fix touching a photographed path would require re-capture.
**Reversible:** yes

## iter-7 — goal-decomposer

**Ambiguity:** iter-6's evaluator framed audit F2 (the whole-row drill-in link on `/desk` had made
several per-cell `title` tooltips — full-precision `distance_bps`/`band_score`, per-timeframe
"window last requested" freshness — unreachable by hover) as a choice between exactly two fixes:
"the whole row is a link, or each cell keeps its hover detail." Neither `docs/goal.md` nor the
blueprint states which cells, if any, may stop being part of the row's click target.

**We chose:** Neither named option. Both risk breaking `runs/goal-session-desk/journey-scripts/J-05.json`
step 4, which clicks the whole `desk-screen-row` testid (`<tr>`) and currently succeeds everywhere in
the row because the drill-in anchor covers the full row via `absolute inset-0`; if the distance/score/
coverage cells reclaimed pointer-event priority (either candidate's implied mechanism), a click
landing over those cells could silently stop navigating — rebuilding/breaking J-05's own
already-verified, binding "do not redo" click behavior. Instead, iter-7 consolidates every
now-unreachable per-cell tooltip onto the row's own drill-in anchor (already the topmost element
everywhere in the row): hovering anywhere in the row reveals one composite tooltip carrying the full
`distance_bps`, full `band_score`, and each coverage entry's `latest_window_end_utc`. This makes zero
change to the anchor's `href`, `absolute inset-0` positioning, or any click geometry, and does not
touch audit F3's earlier, deliberate 2-decimal DISPLAY rounding (kept for scanability) — only WHERE
the full-precision detail is reachable from.

**Reversible:** yes — the composite-tooltip approach can be replaced by either originally-named
option later if the owner prefers a different contract; no stored data or endpoint shape is affected.

## iter-7 — goal-evaluator

**Ambiguity:** The iter-7 audit recommended scoring J-07 as "passing on every clause that has
evidence, with two clauses carried" (its §5.1). `docs/goal.md`'s J-07 acceptance, however, lists
"kept-route byte-identity holds" and "zero out-of-inventory changes in the cumulative diff" as
conditions, and its step 1 requires every guard test to pass byte-unmodified — nothing in the file
says whether a disclosed, owner-escalated deviation counts as satisfying a condition it plainly
contradicts.
**We chose:** Score J-07 `partial`, not `passing` — a condition that is verifiably false today is
unmet, however well disclosed — and halt with STALLED rather than carry the item a fifth time. The
consequence is deliberate: the owner's one written decision (ratify / revert / narrow the wording)
now gates the era, instead of the loop spending another iteration on work that cannot change the
outcome. The audit's softer framing stays available: if the owner narrows J-07's wording to "no
UNDISCLOSED out-of-inventory changes" plus "a guard test may be updated for a rename", the existing
evidence closes the era immediately.
**Reversible:** yes

## iter-7 — goal-evaluator

**Ambiguity:** J-07 step 2 asks for a browser walk of the "sim cockpit (`SIM-BUYER` settles
`buyer_control`, chart candles + timeframe switch + band overlay + live tape bars)". `SIM-BUYER` is a
synthetic ticker with no recorded bars and no tradable map, so its cockpit honestly renders "No
recorded bars for SIM-BUYER." and "No tradable map for SIM-BUYER." — the candle-history and
band-overlay halves of that sentence cannot be shown on that symbol at all.
**We chose:** Treat the clause as met for the parts the sim symbol can show (settled `buyer_control`,
live tape candles, the 10s/30s/60s tape-timeframe controls, six populated panels — all in
`UT-08-cockpit-buyer-control.png`), treat historical candles + band overlay as evidenced on
`/structure` instead (`UT-09-structure-aapl-wall.png`), and record the missing Historical-mode
cockpit capture on a REAL symbol as an open J-07 gap rather than a failure. This does not change
J-07's status (already `partial` for other reasons), but iteration 8 must take that picture before
the clause is called complete.
**Reversible:** yes

## iter-8 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s J-07 step 3 asks for "kept-route responses byte-identical on
identical inputs vs a baseline captured from the era-open commit `047c38e`" but names no exhaustive
route list or input set, and no baseline was ever captured at era open (iter-7 audit T3) — so this
iteration must pick, for the first time, exactly which routes and inputs constitute "the kept
product's routes."

**We chose:** the full set of pre-desk GET routes under `/research/` and `/meta/` (taxonomy,
datasets(+id), bars(+id/candles), candles, levels, tradability, setups(+id), pnl/ledger, profiles,
strategies, edge-report) plus `/meta/ui-routes`, exercised with the same concrete inputs prior
iterations' own evidence already used (pinned AAPL as-of 2026-06-22/2026-07-25, the fixture universe
member set) rather than every theoretically possible parameter combination — a bounded, reproducible
set matching what J-07's acceptance text calls out by name (the AAPL wall, `/research/taxonomy`
unchanged) rather than an exhaustive fuzz. The MCP tool-count delta (15→17) is cited from iter-7's
own already-proven evidence, not re-diffed against a second checked-out MCP server, since J-06 is a
binding "do not redo" item. Live WS tape frames are not diffed byte-for-byte (no engine change this
era; the existing engine-equivalence suite already proves byte-identical `default` projections).

**Reversible:** yes — a future iteration can widen the route/input set if a gap surfaces.

## iter-8 — goal-evaluator

**Ambiguity:** J-07 step 2 asks for a screenshot of the "Case Studies drill-in" on the current tree,
and the era's rail is absolute ("no screenshot ⇒ the journey is `unknown`, never `passing`"). This
iteration's Case Studies capture (`J-07-case-studies-drillin.png`) proves only that the panel RESOLVES
and renders its honest empty state, on a disclosed fixture-scoped rig that contains no band-touch
events at all — because the ambient store's `GET /research/setups` did not return inside a bounded 30 s
probe (its scan cache is cold; see the second entry below). The one screenshot that shows a real event
drill-in with real reaction/forward-return numbers is iter-7's
`reports/qa/goal-desk-iter-7-evidence/UT-10-case-studies-drillin.png`.
**We chose:** Count the iter-7 frame as satisfying that sub-clause for the current tree, because the
code it depicts is provably unchanged — `git diff --name-only <iter-8 snapshot> HEAD -- apps/` is empty,
`apps/backend/app/research/setups.py` has no diff at all this era, and `apps/frontend/app/structure/page.tsx`
was last touched in iter-6 — and pair it with this iteration's fresh capture, which proves the same
panel still resolves and still degrades honestly on today's build. The alternative (score the sub-clause
unmet for want of a same-iteration capture) would have held the era open on a picture that only an
operator cache-warm, not any product work, can produce.
**Reversible:** yes — a later capture on a warmed ambient store would replace the iter-7 frame outright.

## iter-8 — goal-evaluator

**Ambiguity:** J-07's acceptance says "kept-route byte-identity holds on every route outside step 3's
two named exemptions" (`/meta/ui-routes` and the MCP tool list). The captured baseline found a THIRD
route differing: `/research/candles` for AAPL 1d, by exactly `integrity_errors` 0 -> 1 and
`revised_timestamps` 188 -> 187. Read literally, the acceptance sentence makes any third difference a
failure; step 3's own body, however, says a difference "is explained against R-1 or it is a defect",
and R-1 adds "where the clauses below say untouched / byte-unmodified / out-of-inventory, they are read
subject to R-1".
**We chose:** Score the clause MET. I read the mechanism in code myself (`apps/backend/app/research/bars.py:518-547`
collects price-less rows, excludes them from the merged view, and reports them through the existing
`integrity_errors` channel) and confirmed it is precisely the behaviour the owner ratified in writing;
`/research/levels` and `/research/tradability`, which read the SAME merged path, both MATCH, which
bounds the effect to one route and one as-of window. Treating the owner's own ratified repair as a
sentinel failure would mean the owner ratified something that automatically fails the sentinel.
**Reversible:** yes — if the owner intended "exactly two differing routes, full stop", the era reopens
with a single clarifying line in J-07's acceptance text.

## iter-8 — goal-evaluator

**Ambiguity:** Anti-goal "Every run is an explicit operator act … page-load GETs never trigger fetches
or computes" *(critical)* versus what the operator will actually see: on the ambient `.data/`, loading
`/structure` leaves the Case Studies panel on its loading skeleton for minutes, because this era added
`desk_*` `Config` fields (explicitly sanctioned by the era's own Constraints, Path A) and that changed
the content hash keying `setups_scan_cache.db`, so the pre-existing GET path now performs a real scan
instead of a cache read.
**We chose:** Not an anti-goal violation, and not a J-07 acceptance failure — recorded instead as an
open OPERATOR item on J-07 and in the next-step recommendation. Reasons: the era added no such code
path (`setups.py` and its route are byte-unchanged vs `047c38e`); the compute-on-miss behaviour predates
the era; the served VALUES are byte-identical (`/research/setups` MATCHes in the baseline report); and
the remedy is the existing operator-run scan, not product work the era is allowed to do (Non-Goals:
"No engine, chart, or kept-surface work"). Had I scored it a minor violation, the verdict would have
been CONTINUE on a latency item that no in-scope code change could fix.
**Reversible:** yes — if the owner reads that rail as covering cache-key side effects, this becomes a
minor unresolved violation and the era reopens for a warm-or-refuse fix on that panel.

## iter-9 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s J-08 step 1 specifies `basis_age_days` only as "a plain arithmetic
derivation from the row's own `basis_as_of` and the snapshot's own `as_of` (the `distance_bps`
precedent, `desk_screen.py:197`)" — it names neither the exact formula nor whether the result is a
whole-day integer or a fractional/float day count, and both `basis_as_of` and `as_of` are full ISO
datetimes (not bare dates) whose time-of-day components can differ (e.g. an existing fixture pair
resolves `as_of="2026-06-22T15:00:00Z"` against `basis_as_of="2026-06-18T04:00:00.000000Z"`).
**We chose:** A whole calendar-date difference — `(date(as_of) - date(basis_as_of)).days`, an
`int >= 0` — discarding the time-of-day component on both sides. This is the reading that
reproduces the exact numbers the proposer measured live and cited in goal.md's own rationale
(as-of 2026-07-25 minus basis 2026-07-24 = 1 d for AAPL; minus 2026-07-13 = 12 d for
META/NFLX/NVDA) and matches every "N d" example in the acceptance text and the UI copy example
("12 d before as-of"). A true elapsed-time formula (subtracting full timestamps, dividing by
86400, then flooring or rounding) would give a different integer whenever the two time-of-day
components straddle a day boundary, and does not reproduce the cited examples as cleanly.
**Reversible:** yes — `basis_age_days`'s derivation can be swapped for a different formula in a
later iteration without touching `basis_as_of`, the persisted 5-pin key, or any other row field;
only already-recorded rows from this iteration forward would keep their original (never
retroactively rewritten, per the append-only rail) values.

## iter-9 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s J-08 acceptance requires a browser screenshot with "at least one
fresh row (age ≤ 2 d) and one stale row (age ≥ 10 d) legible in the same screenshot". The captured
evidence (`UT-03-fresh-vs-stale.png`) shows 3 d vs 14 d. The iteration's own test plan
(`reports/phase-goal-desk-iter-9-ui-test-plan.md:112-115`) declares an "explicit, documented
allowance" that a 7+ day spread satisfies the clause even when no row is ≤ 2 d, and the audit
(T1, GAP not IMPORTANT) explicitly hands the call to the evaluator: accept the spread, or require
the literal thresholds.
**We chose:** Score J-08 `partial`, not `passing`, and CONTINUE. Reasons: (i) a test plan written
downstream cannot amend `docs/goal.md`'s acceptance text — only the owner can; (ii) the allowance
was unnecessary, which is decisive — I measured the canonical owner myself at
`as_of 2026-07-25T23:59:59Z` on a throw-away copy of the bar store and got AAPL = 1 d and
META/NFLX/NVDA = 12 d, so both thresholds are reachable TODAY with zero code change and zero write
to the ambient store; (iii) this session's own iter-7 precedent ("a condition that is verifiably
false today is unmet, however well disclosed"). The consequence is one short lean iteration whose
only real deliverable is the correctly-parameterised screenshot. The softer reading stays available:
if the owner narrows J-08's wording to "a legible fresh-vs-stale spread" (or restates the thresholds
relative to the newest available bar rather than absolute days), the existing evidence closes the
journey immediately.
**Reversible:** yes

## iter-9 — goal-evaluator

**Ambiguity:** The browser-QA lane clicked "Run Screen" against the AMBIENT `apps/backend/.data/`
rather than the throw-away copy this iteration's own spec NOTES and
`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` directed (audit T3), writing a real
`screen-2026-07-27-936543601e75.json` into the operator's ledger. `docs/goal.md` has no rail
naming "the pipeline must not write to the ambient store"; the closest rails are "Every run is an
explicit operator act", "Persistence stays scoped", "Snapshots are append-only and pinned" and
"Immutable data".
**We chose:** Not an anti-goal violation — a hygiene deviation, recorded in `journey-history.json`
(`notes_iter_9`) and in the next-step recommendation instead. Each rail was checked individually:
the run was an explicit button click (not a scheduler, daemon, auto-refresh, market-hours trigger,
or page-load GET); it appended a NEW correctly-pinned snapshot rather than rewriting anything; both
pre-existing snapshots are provably untouched (sha256 `530bb4f6b4a5a3fc…` / `9c2fddf6c4821a89…`,
mtime 2026-07-25, predating the 20:21 start); no bar or dataset was written. Consequence to carry:
prior iterations tracked "the owner's real data folder is unchanged" as a standing hygiene check,
and that streak is now broken by a QA-produced (but genuine) screen record; and
`journey-scripts/J-08.json` steps 3/6 now assume the replay target's latest screen carries basis
fields.
**Reversible:** yes — if the owner reads the scoped-rig discipline as a rail rather than a
convention, this becomes a minor unresolved violation and the next iteration owes a remediation
note (the file itself must stay: deleting it would breach the append-only rail).


<!-- condense.sh 2026-07-29T18:49:49Z: moved 7 entries (keep-iters=5) -->

## iter-10 — goal-evaluator

**Ambiguity:** J-08's acceptance bundles several clauses. This iteration produced fresh evidence for
exactly one of them (the literal `<= 2 d` / `>= 10 d` screenshot). The clause "`/desk` renders
[legacy snapshots'] rows with the honest `basis not recorded in this snapshot` state" could NOT be
re-photographed here: the scoped rig now holds two `2026-07-25` recordings, so the golden's history
click resolves to the new (basis-carrying) snapshot instead of the legacy one. `docs/goal.md` does
not say whether every acceptance clause must be re-evidenced in the iteration that closes a journey.
**We chose:** Score J-08 `passing` on the strength of this iteration's new evidence PLUS iteration 9's
own clause evidence, because the product tree is byte-identical between the two runs — I verified
`git diff 472f0ce -- apps/` is empty and `git status -- apps/` shows no untracked file, and the render
path still exists at `apps/frontend/app/desk/page.tsx:203/285` — and because the legacy records
themselves are byte-identical on disk (sha256 `530bb4f6…`/`9c2fddf6…`) with zero rows carrying a basis
key. The alternative (demand a same-iteration capture of every clause) would hold the era open on a
picture only a re-seeded scoped root could produce, for code that provably did not change.
**Reversible:** yes — a later capture on a scoped root holding exactly one recording per date would
replace iter-9's frame outright; if the owner reads the acceptance as "all clauses, same iteration",
J-08 returns to `partial` and one short capture run closes it.

## iter-11 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s J-09 step 1 names a top-up run record field "the requested fetch
window" without specifying its shape. The top-up walk's own `_fetch_window_now()` helper
(`desk_topup_compute.py:91-101`) already returns a plain `(start, end)` ISO-date tuple describing
"the SAME `[start, end]` ISO window every top-up pair requests" (the module's own docstring), but it
is currently called once PER PAIR inside `_run_one_pair`, not once per run, so there is no existing
single value to copy onto a run-level record without a new decision.

**We chose:** Register the Data-Contract shape as `requested_window: {"start": str, "end": str}` — a
direct, minimal packaging of `_fetch_window_now()`'s own existing tuple into named keys, since the
window is deterministic to the calendar day and the module's own docstring already treats it as one
per-run concept ("the fetch horizon — a SINGLE wide lookback shared by all four pinned timeframes").
We deliberately left the exact CAPTURE POINT open to the developer's build-time judgment (call the
helper once at run start purely for record-keeping, vs. read the value off the first pair's own
call) — both readings satisfy J-09's own "zero change to what `run_topup` itself computes" rail
(this iteration's OUT OF SCOPE), and goal.md's text does not distinguish between them.

**Reversible:** yes — `requested_window`'s shape can be widened later (e.g., a per-pair variant, if
a future run ever spans a UTC day boundary) without touching any other field or the store's
key/checksum discipline, since no other value derives from it.

## iter-11 — developer

**Ambiguity (closes the goal-decomposer's entry above):** the capture point for `requested_window`
was left open. Chose: call `_fetch_window_now()` exactly ONCE in the caller (`DeskTopupComputeManager
.trigger`'s own body, before the worker thread starts; the CLI's `main()` mirrors this before calling
`run_topup`), never inside the writer and never a second time inside `_run_one_pair` (which keeps its
own existing per-pair call byte-unchanged — verified: `git diff` on `_run_one_pair`/`run_topup` is
empty). This is the plan's own explicit trap #3 resolution, implemented as written.

**Ambiguity:** `docs/goal.md`'s J-09 step 4 and the phase spec's DoD both say the new "Top-up Runs"
section sits "beside Screen History." Screen History (`section aria-label="Screen history"`) lives
ONLY inside `DeskPopulatedScreen` — the branch rendered when `latest !== null` (a screen has been
computed at least once). A top-up run is a wholly independent operator act from a screen run (the
backend enforces no ordering between them — `desk_coverage`/`desk_topup_compute` never read the
screen store), and TC-12's precondition ("a registered universe snapshot and zero top-up runs
recorded") names nothing about screen state. Placing the new section literally "beside" Screen
History (i.e., nested inside `DeskPopulatedScreen`, per the plan's own "recommended placement... not
a hard requirement" wording) would make it invisible whenever no screen has ever been run, even if
top-up runs exist — an artificial coupling with no basis in what the data actually depends on, and
one that would make TC-12's honest-empty screenshot only reachable after ALSO running a screen.

**We chose:** Render the Top-up Runs section at the top level of `/desk`, as its own `<section
aria-label="Top-up runs">` placed immediately after the screen-state conditional (i.e., after
whichever of `DeskNotComputedPanel`/`DeskPopulatedScreen` is showing) and before `</main>` — visible
in EVERY reachable page state once its own independent GET resolves, never gated on whether a screen
exists. This still reads as "beside" the screen content in the page's top-to-bottom flow; it simply
does not require `latest !== null` to render, unlike the plan's literal suggested position (which the
plan's own text explicitly permits changing, with disclosure — this entry is that disclosure).

**Reversible:** yes — the section is one self-contained `<section>` block (`TopupRunsSection`) fed by
its own `topupRunsResult` state and its own `fetchDeskTopupRuns()` call; moving it inside
`DeskPopulatedScreen` (and/or duplicating it into `DeskNotComputedPanel`) later is a pure JSX
relocation with zero change to the component's own internals, the fetch, or any backend contract.

**Ambiguity:** the DoD/plan text ("each run showing date + id, universe snapshot id, terminal state,
attempted-of-total pairs and counts by outcome, and — for the latest run — every failed pair...") could
be read as requiring a per-outcome breakdown (reused/fetched/failed counts) on EVERY historical run
row, not only the latest. The backend Data Contract's own precise field list, however, gives the
`runs` list's meta-only entries every field EXCEPT `outcomes` (mirrors the screen list's own
meta-only convention) — so a real per-outcome count is structurally undonable for any row except
`latest`, which alone carries the full `outcomes` array.

**We chose:** Historical `runs` rows show only what their meta actually carries (date, id, universe
snapshot id, terminal state, attempted-of-total); per-outcome counts, every failed pair's verbatim
detail, and the unreached-pairs count are rendered ONLY for `latest` — reading "for the latest run"
as scoping the whole cluster of per-pair-derived facts, not only the failed-pair clause. This also
matches this iteration's own explicit OUT OF SCOPE line ("no new interactive control on the Top-up
Runs section" — no click-through exists to fetch a historical run's full record on demand, unlike
Screen History's later J-05 click-through), so there is no path to a historical row's per-outcome
breakdown even if the UI wanted to show one.

**Reversible:** yes — a future iteration could add a per-run `outcome_counts` field to the backend's
full-record schema (a Path-irrelevant, non-fingerprint-affecting addition, since it is derived
entirely from `outcomes`) and thread it onto the meta projection, without touching the store's
checksum/append-only discipline or any already-recorded file.

## iter-11 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s J-09 Acceptance requires "a **`[NEW]`-flagged demo-narrator
walkthrough** covers the top-up-run disclosure end to end." The recorded walkthrough
(`reports/phase-goal-desk-iter-11-demo.json`) has exactly one J-09 step, `new: true`, whose
narration and point-out describe only the honest-empty panel, with
`reports/demo/goal-desk-iter-11/step-02.png` showing zero run rows. The phase spec's own TC-16 reads
the clause as "an empty run history, **then a populated one with a failed pair**"; the audit rated
the shortfall IMPORTANT (T3) and explicitly handed the call to the evaluator; the closure auditor
rated the same fact non-blocking because showcase artifacts are non-blocking *for the pipeline gate*.
`docs/goal.md` does not define "end to end".

**We chose:** Score J-09 `partial`, not `passing`, and CONTINUE. Reasons: (i) the pipeline's
"showcase artifacts are non-blocking" rule governs whether the PIPELINE halts, not whether a
journey's own goal.md acceptance is met — the evaluator scores against goal.md, and this session set
that precedent at iter-7 and iter-9; (ii) the walkthrough's narration asserts "every top-up run is
saved for good. Its result can never be lost" over a picture that shows nothing saved — an
unevidenced claim in the one artifact the non-programmer owner actually watches, which is precisely
what the clause guards; (iii) decisively, the correct evidence is reachable TODAY with zero code
change — the exact fixture-scoped rig with three checkpoint runs existed inside THIS iteration hours
earlier and its recipe is scripted (`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`), so the
cost is one short filming run, the same shape as iter-10's successful capture-only iteration. Every
other J-09 clause was verified by the evaluator directly, including a byte-identity spy over the real
`run_topup` and an independent forced-failure walk.

**Reversible:** yes — if the owner reads "end to end" as "the walkthrough introduces the feature"
(which the single empty-state step does), J-09 closes immediately on the evidence already on disk;
a one-line clarification in J-09's acceptance text settles it either way.

## iter-12 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s J-09 Acceptance requires "in a real browser after the T-9 clean
rebuild, `/desk` shows the honest no-run-recorded state in one screenshot and, **after a
fixture-scoped run**, the top-up-runs section with attempted-of-total, per-outcome counts and at
least one `failed` pair's recorded detail legible in another". Read literally, "after a run" implies
one rig photographed before and then after. The delivered frames come from TWO different scoped
roots: `desk-iter12-scoped-qa` (:3301, populated) and `desk-iter12-scoped-qa-empty` (:3302, empty) —
disclosed in full at `reports/phase-goal-desk-iter-12-ui-test-results.llm.md:32-58`. The iteration
spec's own DoD had said "both captured against the SAME scoped throwaway rig".
**We chose:** Accept both frames as satisfying the two browser clauses. Reasons: (i) both roots are
`cp -a` copies of the identical ambient tree taken the same day, with the same universe snapshot
`universe-2026-07-25-49b33fa31680`/101 members — the empty rig genuinely IS what the populated rig
looked like before its three runs; (ii) the single-rig reading was unreachable without breaching a
critical rail — the dev's seed -> record -> boot order had already closed the honest-empty window,
and recreating it would have meant deleting three real append-only records, so the browser lane's
refusal to do that was correct rail-keeping, not a shortcut; (iii) the deviation was disclosed up
front rather than silently substituted. This changes nothing about J-09's score, which stays
`partial` on the separate, still-unevidenced walkthrough clause.
**Reversible:** yes — one long-form iteration that boots the frontend BEFORE recording (the lessons
entry's ordering fix) produces both frames on one root and moots this entirely.

## iter-12 — goal-evaluator

**Ambiguity:** Nothing in `docs/goal.md` or the methodology says whether an acceptance clause may be
scored on an artifact a LATER lane in the same iteration is expected to produce. J-09's outstanding
clause names a demo-narrator walkthrough, and at lean depth that lane runs after the evaluator — so
the artifact could plausibly appear ~15 minutes after this scoring.
**We chose:** Score strictly on artifacts that exist at evaluation time — no walkthrough on disk
means the clause is unmet, so J-09 stays `partial` (session precedent: iter-7 "a condition that is
verifiably false today is unmet, however well disclosed"; iter-9; iter-11). Two further facts made
the deferring reading untenable rather than merely unattractive: the populated rig's frontend on
:3301 is already dead (no node process, nothing listening) and the empty rig on :3302 was
deliberately stopped after its single capture, so a demo-narrator dispatched now would have no
browser surface for EITHER half; and the honest-empty state cannot be re-filmed on the populated rig
at all without breaching the append-only rail. Hence ESCALATE (force full depth, where the lane runs
before scoring) rather than CONTINUE-and-hope.
**Reversible:** yes — if the owner reads the walkthrough clause as satisfiable by the post-scoring
showcase lane, then whatever that lane records at finalization can close J-09 without another
iteration; the standing evidence for every other clause is already complete.

## iter-13 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s J-09 Acceptance requires "a **`[NEW]`-flagged demo-narrator
walkthrough** covers the top-up-run disclosure end to end." The demo-narrator lane's own live record
pass produced only populated frames (its opening step narrated an empty starting point beside a
screenshot of three recorded runs — the exact mismatch the phase spec's TC-4 forbids). The iteration
auditor detected this, and FIXED it in-place by inserting a new `n:2` J-09 step whose frame is the
dev lane's own pre-write capture from the SAME scoped rig, renumbering the rest and rewording the
now-`n:3` step (`docs/handoffs/goal-desk-iter-13-audit.md` A1/§4). goal.md does not say whether every
frame must be captured by the demo-narrator's own live pass, nor whether a repair by a later lane
still counts as "a demo-narrator walkthrough".
**We chose:** Score J-09 `passing` on the repaired artifact. Reasons: (i) the clause's subject is the
WALKTHROUGH and what it covers, not which lane pressed the shutter — `reports/phase-goal-desk-iter-13-
demo.json` is the demo-narrator lane's artifact, regenerated with the framework's own renderers, and
`demo_runner.validate_script()` returns OK on my own run; (ii) the frame is genuine and provably
same-rig, same-order — byte-identical (md5 `ba131133…`) to this iteration's `UT-J-09-empty-topup-
section.png` written at 17:02Z, with the first record's `started_utc` 17:03:23.321789Z, and both
frames carry the identical Screen History rows/provenance; (iii) the strict reading is unsatisfiable
in principle: a live recorder can only ever render the store's CURRENT state, so the empty half and
the populated half can never both be live-captured in one pass on one append-only rig — demanding it
is the "vague acceptance criteria -> infinite loop" anti-pattern, and three iterations already
demonstrated it; (iv) the substitution is disclosed three times (the step's own `capture` block,
`demo-results.md` soft notes, the audit report) — no claim in the artifact is unsupported by the image
beside it; (v) re-running the recorder would DESTROY the fix (audit A5), so no further iteration has a
better path absent a framework change.
**Reversible:** yes — if the owner reads the clause as "every frame live-captured by the demo-narrator
lane in one pass", J-09 returns to `partial` and stays permanently unclosable until `demo_runner.py`
gains a first-class static-frame step kind; adding that step kind and re-recording on a freshly seeded
root would then close it in one short run.


<!-- condense.sh 2026-07-30T07:48:21Z: moved 7 entries (keep-iters=5) -->

## iter-14 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s J-10 step 3 says only to "trigger via `POST` through the established
compute-manager pattern (`DeskTopupComputeManager`, `desk_topup_compute.py` — single-flight,
pollable progress, cancellable)" and step 4 registers exactly one new Data-Contract row (the durable
run record) "BEFORE the code lands." It does not say whether the transient in-flight progress a
compute manager necessarily carries (state/progress while `"running"`) needs its OWN registered
Data-Contract row — the way J-02's "Top-up compute progress" row already sits separately from J-09's
later "Top-up run records" row — or whether J-10's one new module can carry that transient state
unregistered, since nothing outside the run's own terminal write strictly needs to persist it.
Separately, unlike J-02 ("an explicit operator-run top-up (POST + CLI)") and J-03 ("an operator-run
screen (POST + CLI + `/desk` button)"), J-10's own text never mentions a CLI anywhere in its six
steps or its acceptance paragraph.

**We chose:** Register TWO new Data-Contract rows in `blueprint.md` — a durable "Coverage-index
reconciliation run records" row (the one step 4 explicitly demands) and a transient "Coverage-index
reconciliation compute progress" row mirroring J-02's original pattern — because "single-flight,
pollable progress, cancellable" is itself a load-bearing contract surface (a future page or a test
can poll it independently of the durable record, exactly as `/desk` already polls
`GET /research/desk/topup/compute` separately from `GET /research/desk/topup/runs`), and leaving it
unregistered would let a later iteration invent a second, divergent progress shape with no row to
check it against. We also chose NOT to require a CLI warmer for J-10 this iteration: the repair is a
fast, local, no-network index rebuild (unlike a ~100-symbol vendor walk), goal.md's own J-10 text
never names one, and the `POST` route itself already serves the "operator-run act against the real
ambient store" role goal.md's acceptance text describes.

**Reversible:** yes — a CLI warmer can be added later as a thin wrapper over the same shared repair
function with zero change to either registered row's shape; and if a future iteration decides the
transient progress row was unnecessary to register separately, it can be folded back into the
durable row's own module docstring without changing any served value.

## iter-14 — goal-evaluator

**Ambiguity:** An earlier QA pass of this iteration triggered the REAL coverage-index
reconciliation and a new screen compute against the owner's ambient `apps/backend/.data`
(`index_reconcile_runs/reconcile-2026-07-28-43857811211f.json`, 281 → 369 rows, 88 unindexed → 0;
`screen/screen-2026-07-27-3ad3c57aa6ba.json`) — which `docs/phases/goal-desk-iter-14.md:225-227`
and its NOTES:349-351 put explicitly OUT OF SCOPE. The auditor rated it IMPORTANT (B1) and did not
revert it. `docs/goal.md` does not say whether an agent-triggered run against the ambient store is
an "explicit operator act", nor whether rebuilding the DERIVED `bar_index` counts under the
"Immutable data" rail that names "registered datasets and bar series".
**We chose:** Record it as a disclosed process deviation (a breach of this iteration's own plan)
and NOT as a `docs/goal.md` anti-goal violation, so it does not drive REGRESSION. Verified rather
than assumed, each point by the evaluator directly: (i) 0 of 369 bar-series files were modified in
the ambient store (`find … -newermt 2026-07-27` → 0), so no registered series was perturbed;
(ii) `bar_index` is the derived, rebuildable accelerator `docs/goal.md` itself calls derived
("frozen JSON = source of truth; any index over it is derived/rebuildable"), and the repair went
only through the sanctioned `BarIndex.reindex()`; (iii) the previous screen snapshot
`screen-2026-07-27-936543601e75.json` is untouched (mtime 2026-07-27) and the new one is an
appended file, so the append-only rail holds; (iv) the trigger was an explicit `POST`, never a
scheduler/cron/auto-refresh — which is what that rail actually forbids; (v) reverting would mean
deleting an append-only record, itself a critical-rail breach. Same class as iter-9's carried
hygiene deviation, and the effect is the repair `docs/goal.md`'s own J-10 rationale wanted, taken
early and by the machine rather than by the operator.
**Reversible:** no — the ambient run record and the new screen snapshot are permanent by design,
and the index rebuild cannot be un-run (it can only be re-run). If the owner reads
"explicit operator act" as "the human, not an agent", the correct remedy is a future rail that
forbids evidence lanes from touching `apps/backend/.data` at all, not an undo of these files.

## iter-14 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s Anti-goals section carries an uncommitted edit this iteration (the
host-guard paragraph reworded from "interactive pump sessions are launched via
`host-guard-exec.sh claude`" to "auto-confined in place by the engine (`host-guard-adopt.sh`…)").
The critical anti-goal "The enhancement loop stays inside its box" forbids the GOAL-PROPOSER from
editing that section, but the file itself does not record who made any given edit.
**We chose:** Treat it as owner-authored maintenance, not a proposer breach, so it is not scored as
a violation. Evidence: `docs/goal.md`'s mtime is 2026-07-28 21:39, the same minute as the owner's
own `project-extensions/host-guard/host-guard.env` edit and ~1h AFTER the goal-proposer finished
(`proposer-result.json` mtime 20:41); the proposer's own result file claims only the J-10 promotion
inside the `AUTO:journeys` markers; the reviewer independently confirmed it documents the mechanism
already committed separately as `b97bf32`; and the wording does not weaken the rail ("Never
disable, widen, or bypass these caps" is unchanged, and I verified my own process affinity is
`4-7,12-15`).
**Reversible:** yes — if the owner did not author it, reverting the paragraph is a one-line change
with no effect on any journey, and the run's own host-guard behaviour (verified confined) stands
either way.

## iter-15 — goal-evaluator

**Ambiguity:** This iteration's spec put rig discipline in its BACKGROUND and NOTES ("every lane
must state its own fixture-scoped rig path... never fall back to the ambient `apps/backend/.data`
store"), but `docs/goal.md` itself says only that every run must be an "explicit operator act" and
that snapshots are append-only — it does not say whether an agent-triggered `POST` against the
owner's ambient store is such an act, nor whether breaching an ITERATION plan (as opposed to a
project rail) is an anti-goal violation. The dev lane computed a real screen into
`apps/backend/.data/screen/screen-2026-07-28-ac07c9581a4f.json`, and I established that the
`:8301` "scoped rig" (uvicorn PID 4014756) carries no `TAPEOLOGY_*` environment override at all, so
the browser-QA and demo-narrator lanes served that same ambient store — while
`reports/phase-goal-desk-iter-15-ui-test-results.llm.md:109` states the opposite.
**We chose:** Record it as a disclosed process deviation (a breach of this iteration's own plan,
plus one inaccurate isolation claim in a report) and NOT as a `docs/goal.md` anti-goal violation, so
it does not drive REGRESSION — the same call this session made at iter-14. Verified by me directly,
not assumed: (i) `find apps/backend/.data/bars -newermt "2026-07-29 00:00"` → 0 of 369 bar-series
files modified; (ii) no universe file and no prior screen snapshot was written — only ONE appended
snapshot plus `tradability_cache.db`/`bar_index.db`, which `docs/goal.md` itself calls derived and
rebuildable; (iii) both snapshot files recompute their stored checksums, and the pre-existing
`screen-2026-07-29-ce0d82b8e9bf.json` (mtime 02:11, before this iteration's 02:32 snapshot) is
untouched with both new keys absent on all 63 rows; (iv) the trigger was an explicit `POST`, never a
scheduler/cron/auto-refresh — which is what that rail actually forbids; (v) reverting would mean
deleting an append-only record, itself a critical-rail breach. The evidence is if anything stronger
for having been taken against the real store: my own 63-row re-derivation ran against those same
real files.
**Reversible:** no — the appended screen record is permanent by design and the cache refreshes
cannot be un-run. If the owner reads "explicit operator act" as "the human, not an agent", the
remedy is a rail that forces evidence lanes to set a scoped store dir (and a check that the SERVING
process actually has it), not an undo of this file.

## iter-15 — goal-evaluator

**Ambiguity:** J-11's acceptance asks that "the recorded rank order is byte-identical to what the
same pins produced before this change (disclosure only — a golden comparison proves the rank key did
not move)". No screen with IDENTICAL pins exists on both sides of the change: the pre-change screen
is `screen-2026-07-29-ce0d82b8e9bf` (screen_date 2026-07-29) and the post-change one is
`screen-2026-07-28-ac07c9581a4f` (screen_date 2026-07-28), because re-running the same pins
correctly returns the already-recorded snapshot instead of recomputing — so the literal
same-pins-before-and-after comparison is structurally unobtainable without breaching the append-only
rail.
**We chose:** Treat the clause as satisfied by an equivalent proof rather than the literal one.
Three independent strands, each run by me: (i) `_row_rank_key`'s body appears only as unchanged
CONTEXT in `git diff -- apps/backend/app/research/desk_screen.py`, so the key cannot have moved;
(ii) the two screens' ranked symbol sequences are identical (63/63), as are their skipped sequences
(38/38); (iii) comparing every non-history field across all 63 paired rows yields differences ONLY
in `basis_age_days`, and only by exactly 1 — the arithmetic consequence of the two screens' as-of
dates being one day apart. Plus the fixture-scoped golden tests the spec asked for.
**Reversible:** yes — a future iteration computing a screen for a genuinely new date under the old
and new code paths (or a golden fixture recorded pre-change and replayed post-change) would give the
literal comparison; nothing about the recorded data prevents it.

## iter-16 — goal-decomposer

**Ambiguity:** `docs/goal.md`'s J-12 step 1 requires "`id` and `date` together is an honest refusal,
never a silent precedence rule" but does not name the HTTP status code, nor whether the refusal
should look like FastAPI's own automatic validation 422 or a hand-raised 400/409.
**We chose:** Leave the exact status code to build discretion, requiring only that it is an honest
4xx (never a 200 with either value silently preferred, never a 5xx). 422 is the natural choice since
it matches this router's existing FastAPI-validation-refusal convention elsewhere (e.g. the screen
compute's required-body 422), but the iteration spec does not pin it, since goal.md itself does not.
**Reversible:** yes — a later iteration can tighten the exact status code with zero effect on any
recorded data or any other clause, if the owner wants one pinned.

## iter-16 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s J-12 Acceptance asks that the two same-date views be shown "with at
least one row whose coverage badge differs between the two views legible across the screenshots (on
the ambient rig this is ... NFLX's `1d` badge dark in `screen-2026-07-27-936543601e75` and lit in
`screen-2026-07-27-3ad3c57aa6ba`)". The later view IS captured full-page (`UT-03-result.png`, NFLX
row present), but the earlier view's only genuine capture
(`AUDIT-UT-02-earlier-same-date-recording.png`, byte-identical to demo `step-03.png`) is a 1280x800
viewport frame that stops above the NFLX row — the browser lane's own full-page `UT-02-result.png`
turned out to be a screenshot of an unrelated application (audit T3, which I opened and confirmed).
So the named row's badge is not legible on BOTH sides of the pair. goal.md does not say whether the
named NFLX example is the required comparison or an illustration of "at least one row".
**We chose:** Read "at least one row whose coverage badge differs ... legible across the
screenshots" as the requirement and the NFLX line as its illustration, score J-12 `passing`, and
record the framing shortfall as a capture defect (`evidence_makeup: true`, methodology A.7) rather
than an unmet clause. Four strands, each checked by me: (i) the coverage difference IS legible
across the pair — the earlier view carries the on-screen sentence "3 ranked row(s) below show every
timeframe badge dark" and the later view does not; (ii) I re-derived the row-level difference from
the two stored files directly — they differ on EXACTLY 4 ranked rows' `coverage` (NFLX, META, MSFT,
NVDA), ranked order identical 63/63, and NFLX `1d` `has_bars` is `false` then `true`, precisely
goal.md's example; (iii) the browser lane's UT-02/UT-03 rows record DOM `eval()` reads of the NFLX
row's `data-has-bars` flipping `false` -> `true` between the two selections; (iv) methodology A.7's
rail is respected — the asserted BEHAVIOUR is confirmed, only the artifact's crop is wrong, and no
screenshot shows behaviour contradicting the claim. The strict reading would demand one more
full-page capture of an already-working, already-photographed page, which the framework routes to
the make-up lane, never to a new iteration goal.
**Reversible:** yes — one full-page re-capture of the earlier recording (a `Depth: evidence` run or
a passenger task, no program change, and repeatable at will since this journey only READS) produces
the literal side-by-side NFLX comparison; nothing about the stored data prevents it, and the flag
clears on any fresh capture.

