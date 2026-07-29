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

## iter-4 — 2026-07-26T14:20:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** every iteration with `Frontend Present: yes` — check the existence of
`ui-test-results.md` and the trace's `browser-qa-agent` entry BEFORE reading any verdict prose, and
never let another agent's ad-hoc screenshot stand in for the named lane.

## iter-4 — 2026-07-26T14:22:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose browser/QA pass can trigger a WRITE path (fetch, top-up,
record) — scope the stores to a temp dir first; and any golden script — assert the page is still
alive AFTER the first matching string, never only at the match.

## iter-5 — 2026-07-26T15:38:33+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that records or edits a `journey-scripts/*.json` golden whose steps
click a compute/fetch/Run button, and any iteration that runs the deterministic replay lane.

## iter-5 — 2026-07-26T15:38:33+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any browser-QA pass photographing an in-flight compute state, and any page whose
controls render below a full-page capture's height limit.

## iter-6 — 2026-07-26T19:50:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that makes a table row clickable/navigable, or that relies on a `title`
tooltip to keep a rounded display honest — pair the change with a hit-test assertion naming the
element expected to be topmost at each interactive cell's centre.

## iter-7 — 2026-07-27T16:45:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any era whose goal.md contains a "byte-identical vs baseline" or "zero
out-of-inventory diff" sentinel clause (capture the baseline artifact in iter-0 and store it under
`runs/goal-session-<sid>/state/`), and any iteration that touches a file goal.md declares frozen —
route the ratification to the human IMMEDIATELY (STALLED), not as a recommendation carried by later
iterations.

## iter-8 — 2026-07-27T20:15:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance text says "byte-identical vs baseline/era-open" — capture
the baseline in that same iteration, never defer it; and any era that adds `Config` fields, since that
silently re-keys every content-hash-keyed durable cache (here `setups_scan_cache.db`), turning a warm
kept-surface panel into a multi-minute cold scan on the operator's real data folder.

## iter-8 — 2026-07-27T20:15:02+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration where the deterministic replay lane FAILs and the merged file PASSes;
any dispatch that tells browser-qa-agent to "overwrite if present" a golden script.

## iter-9 — 2026-07-27T23:59:05+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance text carries a NUMBER measured live at authoring time
(ages, freshness, counts, spreads) — and any lane writing a test plan for such a journey: reproduce
the goal's own cited measurement conditions, and escalate to the owner rather than granting
yourself an allowance.

## iter-9 — 2026-07-27T23:59:05+01:00 (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose browser walk includes a WRITE-triggering button (Run Screen,
Top-up, Compute) — the scoped rig must be named in the browser-QA dispatch, not just the dev spec,
and the results report must state which data root was used.

## iter-10 — 2026-07-28T11:05:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that computes/records a snapshot into a store a golden script replays
against — check the target store for an existing record under the same key first, and if a collision
is unavoidable, disclose it in the script's `notes` and in the results report before the replay runs.

## iter-11 — 2026-07-28T15:40:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance names a demo-narrator walkthrough for a feature that
is invisible until data accumulates — name the scoped rig (and the records it must already hold) in
the SHOWCASE dispatch, not only the dev and browser-QA ones; and any DoD line of the form "X reaches
Y" — send a real request through the real path rather than reading an allowlist constant.

## iter-12 — 2026-07-28T17:20:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any decomposer/evaluator handling a journey whose remaining gap is a showcase
artifact (demo walkthrough, iteration summary, README/rendered showcase) — those clauses require
`full` depth; also any "capture-only" iteration whose deliverable is produced by a post-evaluation
lane.

## iter-12 — 2026-07-28T17:20:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration capturing before/after evidence for an append-only store (top-up run
log, screen ledger, universe snapshots, dataset/bar stores) — sequence the frontend boot before the
first write, and say so in the dev spec, not only in the QA spec.

## iter-13 — 2026-07-28T20:03:15+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance names a demo-narrator walkthrough over a state that
only exists before the first write (top-up run log, screen ledger, universe snapshots, any
append-only store) — and any lane tempted to re-run `--mode record` on a finished walkthrough.

## iter-13 — 2026-07-28T20:03:15+01:00 (second entry)  [condensed: body → lessons.md.archive.md]
**Applies to:** any evaluator weighing "this lane independently re-verified X" when the cited image
is byte-identical to an earlier lane's — treat the image as evidence of the STATE, not of the lane.

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
