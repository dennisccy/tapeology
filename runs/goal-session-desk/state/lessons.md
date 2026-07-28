# Goal Session desk — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-25T03:25:01+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration where J-07 rides the deterministic replay lane, and every new golden
script written this era.

## iter-0 — 2026-07-25T03:25:01+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** every browser-QA dispatch against `.data/scoped_browser_qa`; and read it as live
precedent when building J-02's "coverage GET is index-read fast, never re-hashes the store"
requirement (T-4).

## iter-1 — 2026-07-25T06:05:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** every era-B iteration that adds ANY `Config` field (i.e. most of them), and
unconditionally to whichever iteration next dispatches browser QA (expected J-04): warm
`/research/setups` and `/structure` Load on the real data dir first, and budget for the cold call.

## iter-2 — 2026-07-25T08:24:13+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** J-03's screen rows and J-04's coverage badges (any code consuming
`GET /research/desk/coverage`); and generally — when a spec's acceptance names concrete real symbols,
execute it against those symbols rather than accepting a synthetic-fixture stand-in as equivalent.

## iter-3 — 2026-07-25T11:05:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration touching `desk_universe.py`, `desk_screen.py`, or adding a new
checksum-verified append-only store (a `record()` whose filename derives from its dedup key)

## iter-3 — 2026-07-25T11:05:00+01:00  [condensed: body → lessons.md.archive.md]
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
