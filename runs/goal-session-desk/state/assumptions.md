# Goal Session desk — Assumption Ledger

Append-only. An entry is added whenever scoring or planning required *interpreting*
`docs/goal.md` rather than just reading evidence. The human reviews these to catch
silent interpretation calls early.

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
