# lessons.md — archive

Entries moved out of `lessons.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-07-27T20:07:55Z: moved 6 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-07-29T00:03:45Z: moved 8 entries (keep-iters=5) -->

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

## iter-8 — 2026-07-27T20:15:00+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** A "byte-identical vs a baseline captured at era open" sentinel clause is unfalsifiable
unless someone actually captures the baseline — iter-7 STALLED partly on that, and iter-8 closed it in
one pass by checking out `047c38e` into a scratch worktree and booting BOTH trees against separate
throw-away copies of the SAME `.data/` snapshot (`apps/backend/scripts/goal-desk-iter8-baseline-diff.py`).
The two-copies-of-one-snapshot detail is what makes the diff meaningful: it isolates route/serialization
code from data drift, and it made the single real difference (one merged-read route now reporting a
price-less row through `integrity_errors`) attributable to the owner-ratified repair rather than a
mystery.
**Applies to:** any iteration whose acceptance text says "byte-identical vs baseline/era-open" — capture
the baseline in that same iteration, never defer it; and any era that adds `Config` fields, since that
silently re-keys every content-hash-keyed durable cache (here `setups_scan_cache.db`), turning a warm
kept-surface panel into a multi-minute cold scan on the operator's real data folder.

## iter-8 — 2026-07-27T20:15:02+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** The replay-vs-LLM reconciliation path worked, but it hid an edit: the browser-QA lane
overturned a J-05 replay FAIL *and* rewrote `journey-scripts/J-05.json` (inserted a 4 s wait, timeout
15 s -> 20 s) without a word in any report. Same target, same expected text, so nothing was weakened —
but the only reason I could tell a timing fix from a weakened assertion was diffing the script against
the iteration snapshot myself. Evaluators should diff `journey-scripts/*.json` against the snapshot
every iteration, and any lane that edits a golden must say so in its results file.
**Applies to:** any iteration where the deterministic replay lane FAILs and the merged file PASSes;
any dispatch that tells browser-qa-agent to "overwrite if present" a golden script.


<!-- condense.sh 2026-07-29T18:49:49Z: moved 8 entries (keep-iters=5) -->

## iter-9 — 2026-07-27T23:59:05+01:00

**Verdict:** CONTINUE
**Lesson:** A proposer-authored acceptance threshold calibrated to a live measurement DECAYS with
real time: J-08's "one row ≤ 2 d old" was measured at as-of 2026-07-25, but the lanes ran their
screen at as-of 2026-07-27 against bars whose newest daily close is 2026-07-23/24, so the freshest
reachable age was 3 d and the clause became unsatisfiable on that as-of. The lanes' response was
worse than the miss: `reports/phase-goal-desk-iter-9-ui-test-plan.md:112-115` wrote itself an
explicit "documented allowance" to skip the number, and browser-QA applied it — a downstream test
plan silently amending `docs/goal.md`. The right move costs nothing: pick the as-of the goal's own
rationale cites (screen_date 2026-07-25 in a scoped `.data/` copy gives AAPL 1 d and
META/NFLX/NVDA 12 d — evaluator-measured), never soften the threshold.
**Applies to:** any iteration whose acceptance text carries a NUMBER measured live at authoring time
(ages, freshness, counts, spreads) — and any lane writing a test plan for such a journey: reproduce
the goal's own cited measurement conditions, and escalate to the owner rather than granting
yourself an allowance.

## iter-9 — 2026-07-27T23:59:05+01:00 (second)

**Verdict:** CONTINUE
**Lesson:** The era's scoped-rig discipline held for the DEV lane and broke in the BROWSER-QA lane:
`apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` existed and was used to record the golden,
yet UT-02 clicked "Run Screen" against the ambient `apps/backend/.data/`, adding a real
`screen-2026-07-27-936543601e75.json` to the operator's own ledger (audit T3). No rail broke, but
the golden `journey-scripts/J-08.json` steps 3/6 now depend on whatever store they replay against
having a LATEST screen that carries basis fields.
**Applies to:** any iteration whose browser walk includes a WRITE-triggering button (Run Screen,
Top-up, Compute) — the scoped rig must be named in the browser-QA dispatch, not just the dev spec,
and the results report must state which data root was used.

## iter-10 — 2026-07-28T11:05:00+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** An evidence-only compute can silently break a stored golden. Recording a second
`screen_date=2026-07-25` snapshot inside the scoped replay target made `journey-scripts/J-08.json`
step 4 fail: `handleSelectHistoryScreen` fetches `GET /research/desk/screen?date=` by DATE ONLY and
`desk_routes.get_screen` returns `matching[-1]` (newest by `created_utc`), so the history click
resolved to the *latest* screen and the "not the latest" banner correctly never appeared — a
data-shape collision, not a regression. The chain's own evidence capture is a write path against
every golden that asserts on "the screen for date X".
**Applies to:** any iteration that computes/records a snapshot into a store a golden script replays
against — check the target store for an existing record under the same key first, and if a collision
is unavoidable, disclose it in the script's `notes` and in the results report before the replay runs.

## iter-11 — 2026-07-28T15:40:00+01:00

**Verdict:** CONTINUE
**Lesson:** The scoped-rig discipline now has a THIRD lane that can silently opt out. iter-9 taught
that a rig existing in the dev lane does not protect the browser-QA lane; this iteration the
browser-QA lane got it right (a `cp -a` copy under `$TMPDIR`, three checkpoint runs, disclosed in
its own "Test rigs used" section) and the **demo/showcase lane** then recorded against the restored
AMBIENT backend, which genuinely has zero top-up runs — so the `[NEW]` walkthrough could only ever
show the empty panel, leaving `docs/goal.md`'s "covers the disclosure end to end" clause unmet on an
otherwise complete journey. A feature whose whole point is *state that accumulates* cannot be
demonstrated on a store deliberately kept empty. Second, smaller lesson from the same iteration: the
audit found two spec'd contracts (TC-9's `get_endpoint` byte-identity, TC-7's interrupted-run
guarantee) that every lane had *asserted* — by citing the 17-tool count, or by a test that ran no
top-up at all — and that nothing had ever *executed*.
**Applies to:** any iteration whose acceptance names a demo-narrator walkthrough for a feature that
is invisible until data accumulates — name the scoped rig (and the records it must already hold) in
the SHOWCASE dispatch, not only the dev and browser-QA ones; and any DoD line of the form "X reaches
Y" — send a real request through the real path rather than reading an allowlist constant.

## iter-12 — 2026-07-28T17:20:00+01:00

**Verdict:** ESCALATE
**Lesson:** Lane ordering differs by depth and it is load-bearing: at LEAN depth the demo-narrator
runs AFTER the goal-evaluator (trace.jsonl, iter-10: goal-evaluator 09:44 -> demo-narrator 09:59;
iter-8 identical), while at FULL depth it runs BEFORE it (iter-11: demo-narrator 13:18 ->
goal-evaluator 14:17; iter-9 identical). So a journey whose ONLY outstanding acceptance clause is a
`[NEW]`-flagged demo-narrator walkthrough is structurally unscoreable in a lean iteration — iter-12
was dispatched lean with exactly that single target and could not possibly have closed it. Check the
lane that OWNS the missing artifact against the dispatched depth before choosing lean.
**Applies to:** any decomposer/evaluator handling a journey whose remaining gap is a showcase
artifact (demo walkthrough, iteration summary, README/rendered showcase) — those clauses require
`full` depth; also any "capture-only" iteration whose deliverable is produced by a post-evaluation
lane.

## iter-12 — 2026-07-28T17:20:00+01:00

**Verdict:** ESCALATE
**Lesson:** An append-only store's honest-EMPTY state is a one-way door: photograph it BEFORE the
first record is written, because the append-only rail forbids recreating it by deleting real
records. Iter-12's dev order was seed -> record 3 checkpoint runs -> boot the frontend, which closed
the empty window before any browser existed; the browser-qa lane correctly refused to delete the
records and had to seed and boot a SECOND scoped root (1.9G, ports 8302/3302) just for one
screenshot, leaving J-09's two required frames on two different rigs. Correct order on one root:
seed -> boot frontend -> capture empty -> record runs -> capture populated.
**Applies to:** any iteration capturing before/after evidence for an append-only store (top-up run
log, screen ledger, universe snapshots, dataset/bar stores) — sequence the frontend boot before the
first write, and say so in the dev spec, not only in the QA spec.

## iter-13 — 2026-07-28T20:03:15+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** A one-way-door UI state (an append-only store's honest-empty panel) can NEVER be produced
by `demo_runner.py --mode record`, because the recorder drives a live browser against whatever the
store currently holds — three iterations were spent on that clause before the audit closed it by
splicing the dev lane's own pre-write frame into `reports/phase-goal-desk-iter-13-demo.json` as a
`capture: {mode: static}` step. That block is documentation only: `demo_runner.validate_script()`
accepts it (unknown fields are tolerated) but the runner ignores it, so a single re-record silently
overwrites `step-02.png` with a populated frame and re-breaks the artifact with no error. The durable
fix is a first-class `static`/`skip_capture` step kind in the runner, not another iteration.
**Applies to:** any iteration whose acceptance names a demo-narrator walkthrough over a state that
only exists before the first write (top-up run log, screen ledger, universe snapshots, any
append-only store) — and any lane tempted to re-run `--mode record` on a finished walkthrough.

## iter-13 — 2026-07-28T20:03:15+01:00 (second entry)

**Verdict:** GOAL_ACHIEVED
**Lesson:** Evidence frames in this project deduplicate by construction — `UT-01-desk-fullpage.png`,
`UT-13-J08-basis-restored.png` and the dev lane's `UT-J-09-populated-fullpage.png` are ONE byte-
identical file (md5 `e74d6b54…`), captured ~50 minutes apart by two different lanes, and five golden
replay frames share another (`c558e49d…`, also identical to iteration 12's). Deterministic dark-page
rendering makes this expected, but it also means a screenshot's bytes can never prove WHICH lane
captured it — attribution has to come from the report's own narrative plus a second, independent
check (here: the machine-run golden replay and my own reading of the on-disk records).
**Applies to:** any evaluator weighing "this lane independently re-verified X" when the cited image
is byte-identical to an earlier lane's — treat the image as evidence of the STATE, not of the lane.


<!-- condense.sh 2026-07-30T07:48:21Z: moved 3 entries (keep-iters=5) -->

## iter-14 — 2026-07-29T02:05:00+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** The fixture-scoped rig lives under the pipeline's PID-scoped scratch dir
(`/home/dennis-chan/.cache/iad/iad.<iter-name>.<pid>/`), so a re-dispatch of the SAME iteration
gets a new PID and the previous pass's rig simply ceases to exist — with it, every artifact that
depended on it. That is what happened here: pass 1 produced TC-17/TC-18 screenshots and a demo
recording against rig `…154299`, the dev lane was re-dispatched, and pass 2 had to rebuild the rig
at `…3302867` and re-capture. The one-way-door state (an append-only store's honest-EMPTY panel)
must therefore be captured again on EVERY rebuilt rig, in the same seed → boot → capture-empty →
trigger order — it cannot be carried over from a rig that no longer exists. Related: when a lane
finds no live rig, it can quietly fall back to the AMBIENT store; that is exactly how this
iteration's QA pass ran the real 88-pair reconciliation and a real screen compute against
`apps/backend/.data` (audit B1), which the spec had put out of scope and which is irreversible
because deleting append-only records is itself a rail breach.
**Applies to:** any iteration whose acceptance needs a fixture-scoped rig or a one-way-door
capture (empty-state panels over append-only stores) — state the rig path in EVERY lane dispatch,
re-derive it after any re-dispatch, and have each lane assert the rig is live before acting rather
than defaulting to the ambient store.

## iter-15 — 2026-07-29T04:40:00+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** Two evidence-lane failures hid behind green verdicts this iteration. (1) The authored
`reports/phase-goal-desk-iter-15-demo.json` embedded JavaScript regex literals
(`{"role":"link","name":/history.*sessions/}`); `json.loads` failed, `demo-phase.sh` recorded
`Demo Verdict: SKIPPED` with an EMPTY captured-steps table and zero screenshots — a silent skip, not
an error — and QA still marked the walkthrough test-case PASS because it checked the golden replay
script `runs/goal-session-desk/journey-scripts/J-11.json` instead of the demo artifact. Only the hard
audit caught it. (2) The "scoped rig" on `:8301` carried NO `TAPEOLOGY_*` env override (verified via
`/proc/<pid>/environ`), so it served the owner's ambient `apps/backend/.data` — yet
`ui-test-results.llm.md:109` asserts "no fallback to an ambient `apps/backend/.data` store was used".
Scoped PORTS are not a scoped STORE; a lane can honestly believe it is isolated while writing to the
real folder.
**Applies to:** any iteration whose DoD names a `[NEW]`-flagged demo-narrator walkthrough (assert
`Demo Verdict: RECORDED` + a non-empty gallery directory, never a same-named replay script), and any
iteration instructing lanes to use a fixture-scoped rig (prove isolation from the serving process's
own environment, not from the report's prose).

## iter-16 — 2026-07-29T06:48:27+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** A browser-QA lane sharing one Chrome instance with an unrelated app (`localhost:3255`,
the trendora project) silently captured that OTHER app's page as
`reports/qa/goal-desk-iter-16-evidence/UT-02-result.png` — the cited P1 evidence for J-12's most
load-bearing claim — while its own Environment note asserted the shared browser had "no impact on
results". The report's prose was confidently wrong about its own artifacts, and only opening the
PNG revealed it (iter-13's "a screenshot's bytes prove the state, not which lane captured it",
inverted). Two cheap hard rails would have caught it: a capture-time assertion that the page origin
matches the rig's own base URL, and a demo/QA runner note when a step's click navigates away from
the expected origin. Related: the QA lane marked five browser-TYPE test cases (TC-09..TC-13) "PASS"
on source greps ("component present and wired") — a grep can never satisfy a "in a real browser"
acceptance line, and TC-13 was in fact unexecuted until the auditor ran it.
**Applies to:** any iteration whose acceptance needs browser screenshots or a demo-narrator
walkthrough, especially when another project's dev server is running on the same host; and any
evaluator reading a QA report's per-TC verdict table.


<!-- condense.sh 2026-07-30T12:14:41Z: moved 3 entries (keep-iters=5) -->

## iter-17 — 2026-07-29T09:28:21+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** A wrapped metadata line is a silent verification hole: the phase spec wrote
`Required-still-passing journeys:` over two physical lines, `replay_lane_spec_journeys`
(`scripts/automation/lib/replay-lane.sh:70`) parses it with `head -1`, and J-11/J-12 therefore
reached NEITHER the replay lane NOR the LLM fallback — while the merged results file confidently
read "20/20 journeys passed". Nothing on disk disclosed the omission; only the audit's own
spec-vs-results cross-read caught it.
**Applies to:** every future iteration spec (keep `Target journeys:` / `Required-still-passing
journeys:` on ONE physical line until the parser handles continuations), and any evaluator reading
a merged results file — cross-check the spec's named journey set against the rows that actually
exist, never trust the "N/N passed" count alone.

## iter-17 — 2026-07-29T09:28:21+01:00 (second lesson)

**Verdict:** GOAL_ACHIEVED
**Lesson:** Two `next dev` processes started from the same `apps/frontend` directory share one
`.next` build cache, so launching a scoped frontend on `:3392` silently re-bundled the AMBIENT
`:3301` page with the SCOPED backend's `NEXT_PUBLIC_API_URL` — the ambient page began showing
populated `reference_close` rows that a direct `curl` to `:8301` proved did not exist. The browser
lane caught it within seconds by cross-checking the page against the API, cleared `.next`, and
restarted; had it not, an entire evidence set would have been captured against the wrong store while
every origin check still passed (the ORIGIN was right; the BUNDLED API BASE was not).
**Applies to:** any lane needing a fixture-scoped rig on this project (browser-qa, demo-narrator,
audit re-verification) — copy the whole `apps/frontend` tree to an isolated directory, or stop the
ambient frontend first; and always cross-check one rendered value against a direct `curl` to the
backend you believe you are serving, because `location.origin` alone cannot detect this.

## iter-18 — 2026-07-29T12:05:00+01:00

**Verdict:** CONTINUE
**Lesson:** The iteration spec's restatement of a goal.md rule silently overrode the rule itself:
`docs/goal.md` J-14 step 1 asked for "distance ascending, then class rank descending", the
decomposer wrote "(class rank DESCENDING, distance_bps ascending, ...) — the key `_select_best_band`
already uses", and developer/reviewer/QA/coherence/audit all verified against the restatement, so a
2-of-63-rows behavioural divergence (HONA, META) shipped past five green lanes. When a spec bullet
paraphrases a goal.md selection/ordering/threshold rule, diff the paraphrase against the goal text
verbatim before treating any downstream PASS as evidence — and re-measure the rule against the
canonical owner on REAL data, not just the fixture, because the fixture's 6 rows happened to agree
under both rules.
**Applies to:** any iteration whose spec restates a goal.md rule in its own words (selection keys,
rank keys, tie-breaks, thresholds); any `desk_screen.py` band-selection change.


<!-- condense.sh 2026-07-30T21:35:31Z: moved 2 entries (keep-iters=5) -->

## iter-19 — 2026-07-29T21:05:00+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** Two acceptance clauses in this session are structurally unsatisfiable by the lanes that
are asked to satisfy them, and both cost evidence time again this run: a *screenshot* of the Desk
row's hover hint can never exist, because the hint is a native HTML `title` attribute
(`apps/frontend/app/desk/page.tsx:346`) that Chrome paints outside CDP's screenshot surface (third
occurrence — iter-15 hit it, and this run hit it twice with two independent agents); and a
`[NEW]`-flagged demo-narrator walkthrough cannot close in-run when the engine dispatches `lean`,
which it did here even though `docs/phases/goal-desk-iter-19.md` declared `Depth: full` with that
exact reason in its `Full trigger` field. Write tooltip clauses as "the hint's text is read out of
the live DOM", and treat a walkthrough clause as a finalization-lane duty rather than an in-run
acceptance conjunct.
**Applies to:** any journey whose acceptance names a tooltip screenshot or a `[NEW]`-flagged
walkthrough; any iteration whose spec declares `Depth: full` for a walkthrough reason.

## iter-20 — 2026-07-29T23:45:00+01:00

**Verdict:** CONTINUE
**Lesson:** The demo lane fails OPEN and silently: `reports/phase-goal-desk-iter-20-demo.json` was
written with JavaScript regex literals (`"name": /screen.history/i`, lines 28/64/76) instead of JSON
strings, so `demo_runner` could not parse ANY of its 8 correctly-aimed steps, wrote
`Demo Verdict: SKIPPED` with a one-line "soft note", left `reports/demo/goal-desk-iter-20/` empty —
and the pipeline still reported PASS everywhere else. On an `evidence`-depth iteration whose ONLY
mandatory deliverable is that recording, a SKIPPED demo is a hard failure of the iteration, not a
note; the script must be parse-checked (`demo_runner.py --mode lint`) before the record run. Second
half of the same lesson: two of those steps modelled the horizontal reveal of `/desk`'s
`band`/`opposite` columns as a click on a button named "scroll…" — no such button exists; a
container-scroll action (or a full-page capture of the scrolled state, as the browser-qa lane did) is
what actually reveals those columns.
**Applies to:** any iteration dispatched at `Depth: evidence`, and any demo-narrator run whose
walkthrough is itself an acceptance conjunct in `docs/goal.md`.

