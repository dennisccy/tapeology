# Goal Session desk — Assumption Ledger

Append-only. An entry is added whenever scoring or planning required *interpreting*
`docs/goal.md` rather than just reading evidence. The human reviews these to catch
silent interpretation calls early.

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
