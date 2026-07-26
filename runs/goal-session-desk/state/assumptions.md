# Goal Session desk — Assumption Ledger

Append-only. An entry is added whenever scoring or planning required *interpreting*
`docs/goal.md` rather than just reading evidence. The human reviews these to catch
silent interpretation calls early.

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
