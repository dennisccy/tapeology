# Goal Session desk — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-25T03:25:01+01:00

**Verdict:** CONTINUE
**Lesson:** The new J-07 golden (`runs/goal-session-desk/journey-scripts/J-07.json`) step 8 asserts
the text `300.11` — a post-Load, cache-warmth-dependent async value — on the 15 s default timeout,
which is the exact shape of assertion that cost a full iteration in the `yahoo_fetch` era (headless
matcher misses async-rendered list text). Re-point it at a statically-rendered `/structure` shell
string (or widen its timeout) BEFORE the replay lane guards J-07; if replay FAILs step 8 while the
LLM lane passes, the merged results file wins and it is a golden false negative, not a regression.
**Applies to:** any iteration where J-07 rides the deterministic replay lane, and every new golden
script written this era.

## iter-0 — 2026-07-25T03:25:01+01:00

**Verdict:** CONTINUE
**Lesson:** On a freshly-started scoped browser-QA backend, the first
`GET /research/setups?symbol=AAPL` took ~9–11 min at ~96% CPU (warm re-call: 0.84 s) — the
`/structure` Case Studies skeleton is honest, not hung, but any browser pass that clicks a Case
Study needs the cache warmed first or a wait budget far past the usual per-command timeout.
**Applies to:** every browser-QA dispatch against `.data/scoped_browser_qa`; and read it as live
precedent when building J-02's "coverage GET is index-read fast, never re-hashes the store"
requirement (T-4).

## iter-1 — 2026-07-25T06:05:00+01:00

**Verdict:** CONTINUE
**Lesson:** The era's Path-A protocol only protects `config_fingerprint()` — there is a SECOND,
unnamed whole-config hash, `edge_report_cache._config_content_hash` (`apps/backend/app/research/edge_report_cache.py:165-169`),
which hashes `dataclasses.asdict(config)` with NO exclusion set and keys four durable caches
(`setups_scan_cache`, `tradability_cache`, `edge_report_cache`, `edge_report_backtest_cache`). Adding
the four `desk_universe_*` fields moved it to `dc0271c15a26…` (I confirmed the change myself), so
every pre-diff cache row is unreachable: the real-data `GET /research/setups` is cold again (~9–11 min
first call) and `/structure` Load is back to ~21.6 s. Served values are unaffected (no desk field is
read outside `config.py` + the two desk modules), so this is pure latency — but it re-arms exactly the
false-negative trap that has burned prior browser passes.
**Applies to:** every era-B iteration that adds ANY `Config` field (i.e. most of them), and
unconditionally to whichever iteration next dispatches browser QA (expected J-04): warm
`/research/setups` and `/structure` Load on the real data dir first, and budget for the cold call.

## iter-2 — 2026-07-25T08:24:13+01:00

**Verdict:** CONTINUE
**Lesson:** J-02's delivered truth-table test used synthetic `AAA…EEE` symbols, so goal.md's LITERAL
clause ("bars-present for exactly the members the era-open store holds (AAPL/AMD/MSFT)" over the
fixture universe) was asserted by no test — and when I ran it directly against
`tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json` + the real `bar_index`, it passed but
revealed the goal text's own hidden assumption is wrong: MSFT holds `1h`/`1d` rows but **no** `1w`/`4h`,
so era-open coverage is per-`(symbol, timeframe)`, not per-member. Any consumer that treats "this
symbol has bars" as "the whole pinned timeframe set is present" will silently mis-serve MSFT.
**Applies to:** J-03's screen rows and J-04's coverage badges (any code consuming
`GET /research/desk/coverage`); and generally — when a spec's acceptance names concrete real symbols,
execute it against those symbols rather than accepting a synthetic-fixture stand-in as equivalent.

## iter-3 — 2026-07-25T11:05:00+01:00

**Verdict:** CONTINUE
**Lesson:** Two sibling append-only stores in this era now disagree on the SAME failure mode: the
audit made `ScreenStore.record` refuse (`ScreenIntegrityError`) when the 5-pin key's own
deterministic path already holds a checksum-failed file (`desk_screen.py:467-473`, verified live),
while `UniverseStore.record` still `write_text()`s straight over it (`desk_universe.py:418`, iter-1's
audit B3 gap). The general trap: when a store's file path is a pure function of its dedup key, the
"look up by key → not found → write" sequence silently overwrites any file the loader withheld for
failing verification — so every content-addressed store in this codebase needs an explicit
`path.exists()` guard, not just a key lookup.
**Applies to:** any iteration touching `desk_universe.py`, `desk_screen.py`, or adding a new
checksum-verified append-only store (a `record()` whose filename derives from its dedup key)

## iter-3 — 2026-07-25T11:05:00+01:00

**Verdict:** CONTINUE
**Lesson:** A QA report's numbers can silently come from a DIFFERENT data basis than the acceptance
clause names: `reports/qa/goal-desk-iter-3-qa.md` TC-01 records AAPL as `class A, distance_bps 0.335,
band_score 97.0` "verified against the committed fixture universe", but that run was against the real
ambient 101-member `.data/` store — the committed fixture universe + fixture bars actually yield
`class C, 2.348 bps, score 57.0` (my run, and the auditor's independent probe). The same report also
carried a fabricated single-flight "queue" mechanism the auditor had to correct in place. Never carry
a QA numeric into a golden or a spec without re-deriving it against the named data basis.
**Applies to:** any iteration whose spec quotes measured values from a QA/dev report, and any golden
or fixture assertion authored from one

## iter-4 — 2026-07-26T14:20:00+01:00

**Verdict:** CONTINUE
**Lesson:** A `full`-depth iteration reached the evaluator with its designated browser-QA step never
dispatched at all, while the reviewer's own YAML said `definition_of_done: complete` — the only gate
that caught it was the phase-closure-auditor's mechanical "does
`reports/phase-<iter>-ui-test-results.md` exist?" check (the file was absent; iters 0-3 all had
proper N/A stubs). Screenshots taken by the developer/auditor filled the gap and were partly broken
(`TC-01-empty-state.png` shows a POPULATED page; `TC-12-topup-progress.png` and
`TC-12-topup-cancelled.png` are the same blank 6,490-byte image), so a prose "21/21 passed" QA report
existed for states nobody had really observed.
**Applies to:** every iteration with `Frontend Present: yes` — check the existence of
`ui-test-results.md` and the trace's `browser-qa-agent` entry BEFORE reading any verdict prose, and
never let another agent's ad-hoc screenshot stand in for the named lane.

## iter-4 — 2026-07-26T14:22:00+01:00

**Verdict:** CONTINUE
**Lesson:** The first-ever UI click of the `/desk` Top-up button ran against the AMBIENT
`apps/backend/.data` store (the iter-4 spec's own NOTES had required a fixture-scoped one) and
permanently recorded 60 bar series holding a NaN-priced Yahoo row for a session that had not traded;
JSON round-trips that to `null`, which made `lightweight-charts` throw and unmount `/structure`
~0.1 s AFTER the J-07 golden's step-8 string had already matched — i.e. the replay reported PASS on a
page that had just crashed. Fixed three ways (adapter drops the row at the seam, `BarStore.record`
refuses it, `_merged_rows` excludes + reports it) and the golden gained post-match liveness
assertions (steps 9-11).
**Applies to:** any iteration whose browser/QA pass can trigger a WRITE path (fetch, top-up,
record) — scope the stores to a temp dir first; and any golden script — assert the page is still
alive AFTER the first matching string, never only at the match.

## iter-5 — 2026-07-26T15:38:33+01:00

**Verdict:** CONTINUE
**Lesson:** A recorded golden replay script can be a WRITE path. `runs/goal-session-desk/journey-scripts/J-04.json`
step 5 clicks "Run Screen", so every future replay against the ambient backend records a real screen
snapshot into `apps/backend/.data/screen` (once per new day, since same-pin re-runs reuse) — the same
class of ambient-store pollution as iter-4's unscoped Top-up, just arriving through the regression
lane instead of a QA click. Scope the replay lane's data dirs or assert only read-only content.
**Applies to:** any iteration that records or edits a `journey-scripts/*.json` golden whose steps
click a compute/fetch/Run button, and any iteration that runs the deterministic replay lane.

## iter-5 — 2026-07-26T15:38:33+01:00

**Verdict:** CONTINUE
**Lesson:** A sub-second UI state on a long page is capturable, but only with help, and the help must
be disclosed. The Desk controls sit at the BOTTOM of a ~4500px page while the full-page capture tops
out at 4320px, and the "Computing…" window lasts one 700ms poll tick — so the QA lane held one poll
reply open AND visually pinned the two controls to the top-left with an outline. That produced a real
state in an unnatural layout; the report disclosed the held reply but not the pinning, which cost an
evaluator a pixel-diff and a code read to distinguish "capture aid" from "fabricated element" (the
8×8 `animate-pulse` dot differing between the two shots is what proved they were real).
**Applies to:** any browser-QA pass photographing an in-flight compute state, and any page whose
controls render below a full-page capture's height limit.

## iter-6 — 2026-07-26T19:50:00+01:00

**Verdict:** CONTINUE
**Lesson:** The "stretched link" row pattern (`<Link className="absolute inset-0">` inside a
`position: relative` `<tr>`, `apps/frontend/app/desk/page.tsx:198-213` / `:288-300`) silently hid every
per-cell `title` tooltip on both desk tables — including iter-4's own audit fix that kept the rounded
`0.34 bps` honest by exposing the full `0.33523150389608725` on hover. No source lint, no DOM-text
assertion, no screenshot and no golden could see it: the values are still in the DOM, they are just
unreachable by pointer. Only `document.elementFromPoint` hit-testing at each element's centre found it.
Making a whole row clickable therefore costs every hover affordance inside that row unless the contract
is chosen deliberately.
**Applies to:** any iteration that makes a table row clickable/navigable, or that relies on a `title`
tooltip to keep a rounded display honest — pair the change with a hit-test assertion naming the
element expected to be topmost at each interactive cell's centre.

## iter-7 — 2026-07-27T16:45:00+01:00

**Verdict:** STALLED
**Lesson:** A sentinel journey that asserts "kept responses are byte-identical to an era-open
baseline" is unfalsifiable unless iteration 0 actually CAPTURES that baseline — this era never did,
so the clause sat unchecked for seven iterations and then blocked closure at the gate. Worse, the
same era-close audit surfaced that a mid-era emergency repair to protected files (iter-4's
price-less-bar fix in `bars.py` / `StructureChart.tsx` / a chart guard test) silently made THREE of
that sentinel's clauses literally false; because each iteration had other productive work, the
loop kept CONTINUE-ing past the one question only the owner could answer, four times.
**Applies to:** any era whose goal.md contains a "byte-identical vs baseline" or "zero
out-of-inventory diff" sentinel clause (capture the baseline artifact in iter-0 and store it under
`runs/goal-session-<sid>/state/`), and any iteration that touches a file goal.md declares frozen —
route the ratification to the human IMMEDIATELY (STALLED), not as a recommendation carried by later
iterations.
