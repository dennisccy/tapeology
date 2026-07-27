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

