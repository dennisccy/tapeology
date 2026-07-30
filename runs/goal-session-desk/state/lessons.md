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

## iter-14 — 2026-07-29T02:05:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance needs a fixture-scoped rig or a one-way-door
capture (empty-state panels over append-only stores) — state the rig path in EVERY lane dispatch,
re-derive it after any re-dispatch, and have each lane assert the rig is live before acting rather
than defaulting to the ambient store.

## iter-15 — 2026-07-29T04:40:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose DoD names a `[NEW]`-flagged demo-narrator walkthrough (assert
`Demo Verdict: RECORDED` + a non-empty gallery directory, never a same-named replay script), and any
iteration instructing lanes to use a fixture-scoped rig (prove isolation from the serving process's
own environment, not from the report's prose).

## iter-16 — 2026-07-29T06:48:27+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose acceptance needs browser screenshots or a demo-narrator
walkthrough, especially when another project's dev server is running on the same host; and any
evaluator reading a QA report's per-TC verdict table.

## iter-17 — 2026-07-29T09:28:21+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** every future iteration spec (keep `Target journeys:` / `Required-still-passing
journeys:` on ONE physical line until the parser handles continuations), and any evaluator reading
a merged results file — cross-check the spec's named journey set against the rows that actually
exist, never trust the "N/N passed" count alone.

## iter-17 — 2026-07-29T09:28:21+01:00 (second lesson)  [condensed: body → lessons.md.archive.md]
**Applies to:** any lane needing a fixture-scoped rig on this project (browser-qa, demo-narrator,
audit re-verification) — copy the whole `apps/frontend` tree to an isolated directory, or stop the
ambient frontend first; and always cross-check one rendered value against a direct `curl` to the
backend you believe you are serving, because `location.origin` alone cannot detect this.

## iter-18 — 2026-07-29T12:05:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose spec restates a goal.md rule in its own words (selection keys,
rank keys, tie-breaks, thresholds); any `desk_screen.py` band-selection change.

## iter-19 — 2026-07-29T21:05:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any journey whose acceptance names a tooltip screenshot or a `[NEW]`-flagged
walkthrough; any iteration whose spec declares `Depth: full` for a walkthrough reason.

## iter-20 — 2026-07-29T23:45:00+01:00  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration dispatched at `Depth: evidence`, and any demo-narrator run whose
walkthrough is itself an acceptance conjunct in `docs/goal.md`.

## iter-21 — 2026-07-30T00:35:00+01:00

**Verdict:** STALLED
**Lesson:** An acceptance clause can be permanently unsatisfiable by the pipeline while the product
behind it is fully correct, and the framework's own two rails then point in opposite directions:
`docs/goal.md`'s J-14 says "no screenshot ⇒ `unknown`, never `passing`" for a photograph of a native
HTML `title` tooltip (`apps/frontend/app/desk/page.tsx:346`) that CDP cannot capture at all, while the
evaluator contract says an evidence gap must never be scored as blocking or become an iteration's
goal. Iterations 19, 20 and 21 all burned on that contradiction (one REJECT by the second key, two
capture-only iterations). The resolution is neither another retry nor a silent `evidence_makeup`
carry: it is to stop the loop and put the one-line clause decision to the owner (reword to "read out
of the live DOM" · replace the `title` with an on-page panel · approve a desktop-capture rig · accept
as-is) — STALLED on a human-owned unblock path, not CONTINUE.
**Applies to:** any journey whose acceptance names a screenshot of browser-chrome-drawn UI (native
`title`/`alt` tooltips, `select` popups, print dialogs, file pickers, OS context menus), and any
`Depth: evidence` iteration that would be the third consecutive capture-only run.

## iter-21 (second) — 2026-07-30T00:35:00+01:00

**Verdict:** STALLED
**Lesson:** `Demo Verdict: RECORDED` with a non-empty gallery is NOT proof the film shows anything:
this run's three frames are one byte-identical image (md5 `3b02db86…`, the same PNG as
`J-04-verify.png`) because `demo_runner.py`'s action vocabulary has no scroll primitive, every
`/desk` ranked row is one stretched `next/link` (so any in-row click navigates away), and the two
right-hand columns the film narrates sit past the table's `overflow-x-auto` clientWidth. Narration
accuracy had to be proven a different way — by re-deriving every quoted number from the recorded
snapshot on disk. Check frame md5s and what is actually inside the viewport before crediting a
walkthrough conjunct.
**Applies to:** any demo-narrator run whose walkthrough is an acceptance conjunct, and any future
`demo_runner.py` enhancement (a `scroll` action driving `el.scrollLeft = el.scrollWidth` on the
container, never a click, is the recorded remedy).

## iter-22 — 2026-07-30T09:45:00+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** A capture the harness "structurally cannot take" is not always a permanent gap — a native
`title` tooltip that CDP can never photograph WAS photographed by moving the capture one layer down
(own `Xvfb` display + real headed Chrome + real X pointer via `xdotool` + an X-level `ImageGrab`, at
`project-extensions/qa-rig/`), and the tool's own two refusal paths (no new X window ⇒ exit 3, missing
`--require-title` substring ⇒ exit 4) make the artifact self-validating. The tell that the artifact is
genuine is visible in the frame itself: the tooltip is drawn PAST the browser window's edge onto the
bare desktop, which an in-page screenshot can never show.
**Applies to:** any journey whose acceptance names a screenshot of native browser UI (tooltips,
`select` popups, file dialogs, print preview, permission prompts) — route it to the headed rig instead
of declaring it uncapturable or rewording the clause; and any evaluator judging such an artifact
should check the out-of-window overlap as the forgery test.

## iter-22 (b) — 2026-07-30T09:45:00+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** The deterministic replay lane saves the SAME first-view frame for every journey it
verifies (this run: 5 replay frames + 4 demo frames collapsed to 3 distinct images; md5 `3b02db86…`
recurs across iterations 21 and 22, and `J-04-verify.png` == `J-13-verify.png`). Replay PASS therefore
rests on its `expect` assertions, never on its screenshot — an evaluator must not treat a replay frame
as the journey's acceptance picture, and each journey still needs one dedicated capture somewhere in
its history.
**Applies to:** any iteration whose required-still-passing set is verified only by golden replay, and
any future work on `demo_runner.py --mode verify` (capturing after the last assertion, not before the
first, would fix it).

## iter-23 — 2026-07-30T11:50:00+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** Two deterministic gates in the harness are word-matchers and both mis-fired this
iteration, in opposite directions. `closure_gate.py`'s backend-only guard greps the bare substring
`backend-only` over `reports/phase-<iter>-user-visible-changes.md`, so the ui-impact-analyst's honest
sentence "Nothing else is backend-only:" produced a blocking CLOSURE-FAIL on a report that documents
four real user-visible changes. Meanwhile `goal_gate.py results`' FAIL detector is
`re.compile(r"\|\s*FAIL\s*\|")`, which does NOT match a **bolded** verdict cell — the merged results
file's one genuine `| **FAIL** |` row (UT-07) passed the achievement gate silently. Never treat either
gate's answer as the judgment: read the artifact.
**Applies to:** any iteration whose closure verdict is CLOSURE-FAIL with "backend-only claim guard:
INCONSISTENT" as the only blocking issue; and any evaluator relying on the achievement gate's
results check instead of reading the results table row by row.

## iter-23 — 2026-07-30T11:52:00+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** The scoped-rig instruction has now been dropped for eight consecutive iterations, and the
root cause is finally located: it lives in the iteration spec's NOTES, which the DEVELOPER's `plan.md`
inherits but the browser-qa lane's own slice (`runs/<iter>/goal-slice-bqa.md`) does not. The slice
carries goal.md's acceptance phrase ("on the fixture-scoped rig") with no recipe, so the lane
reasonably used the standing `:3301`/`:8301` rig — and this time wrote a real 100-row screen snapshot
into the operator's append-only store, which can never be removed. A written instruction in a file the
lane never receives is not an instruction; the fix is either injecting the recipe into the bqa slice or
a hard rail that refuses the write when the serving process points at the ambient store.
**Applies to:** any iteration whose evidence lane must compute, record, or film against a data store —
check `goal-slice-bqa.md` itself contains the scoped-rig paragraph before dispatch.

## iter-24 — 2026-07-30T14:45:00+01:00

**Verdict:** CONTINUE
**Lesson:** Dropping an in-cell LABEL PREFIX is a silent golden-script breaker. `demo_runner.py`'s
`_check_expect` resolves a bare `{"text": ...}` through Playwright `page.get_by_text`, which matches
VISIBLE DOM TEXT only — the row's composite `title` attribute carrying the same word is invisible to
it. Iter-24's first pass dropped `basis `/`history `/`band `/`opposite `/` levels`; `J-13.json` and
`J-14.json` pin the literal strings `band 488.50–490.91 · close 490.91` and `opposite resistance A
490.97–494.39 · 1.22 bps`, so those two prefixes had to be restored byte-identical (the other three
were safe because their goldens pin mid-string substrings). The fix added
`test_desk_row_cells_keep_the_label_prefix_their_golden_script_asserts`, which reads BOTH the page
source and the golden JSON and fails if they drift apart.
**Applies to:** any iteration that edits rendered TEXT (not just layout) on a page covered by stored
golden replay scripts — grep the scripts' `expect.text` values before touching a cell's string.

## iter-24 — 2026-07-30T14:45:00+01:00

**Verdict:** CONTINUE
**Lesson:** Under `table-fixed` + `<colgroup>`, a `scrollWidth <= clientWidth` check CANNOT detect
overflow: fixed layout ignores content when sizing, so a too-narrow column just paints its text over
its neighbour while the table's own box stays exactly the sum of the colgroup widths. The dev only
found the "nearest same-class band" caption bleeding into the next column by comparing each cell's
content bounding box against its own `<td>` rect, per row. Also, `Depth: lean` records no
demo-narrator walkthrough — the depth arbiter's `full-cap` demotion (telemetry `depth_demoted`)
therefore made J-16's `[NEW]`-flagged-film acceptance conjunct structurally unreachable this run,
regardless of build quality.
**Applies to:** any width/layout journey measured by DOM geometry (require per-cell bleed checks, not
just table `scrollWidth`), and any journey whose goal.md acceptance names a `[NEW]`-flagged
walkthrough (needs `full` or `evidence` depth — never `lean`).

## iter-25 — 2026-07-30T15:20:00+01:00

**Verdict:** GOAL_ACHIEVED
**Lesson:** A demo/replay script can never `click` any cell inside a `/desk` ranked row: the row's
stretched drill-in anchor (`absolute inset-0`, `apps/frontend/app/desk/page.tsx:416`, whose own
comment at `:454` says the anchor makes cells "pointer-unreachable") intercepts every pointer event,
so Playwright retries until the 8000 ms actionability timeout and emits a soft note — and if the
click DID land it would navigate to `/structure` and destroy the very frame the step exists to
capture. Per-row scoping via `tr[data-symbol="<SYM>"]` fixes the multi-match problem iter-20/23 hit
but not this one; the right action for an in-row disclosure is `expect`-only text assertion over the
populated frame, which is also what actually produced iter-25's usable frames.
**Applies to:** any demo-narrator or golden-replay script step targeting a cell inside a `/desk`
ranked row or skipped row (both carry the stretched anchor); also any future page that adopts the
same stretched-link row pattern.

## iter-26 — 2026-07-31T00:40:00+01:00

**Verdict:** CONTINUE
**Lesson:** A "fixture-scoped rig" is only scoped on the BACKEND side. Standing up a second frontend
with a different `NEXT_PUBLIC_API_URL` still runs `next build` against the ONE shared
`apps/frontend/.next` directory, so the scoped build silently overwrites the ambient build's baked
API base. Verified directly after this run: `.next/static/chunks/app/{layout,desk/page}.js` now
contain `localhost:8000` and no longer contain `localhost:8301`, so the ambient `:3301` page points
at a scoped backend that was torn down — all 16 golden replay scripts (which target `:3301`) would
false-FAIL on the next run for a reason with nothing to do with the product. This run's own replays
were safe only because they ran BEFORE the scoped build (proven by opening `J-13-verify.png`, which
shows real ambient data). Also recurred verbatim from iter-24: the depth arbiter demoted a spec that
explicitly asked for `Depth: full`, so the `[NEW]`-flagged walkthrough conjunct was structurally
unreachable again.
**Applies to:** any iteration whose evidence plan stands up a second frontend instance (scoped rig,
alternate port, different API base) — build it into its OWN `distDir`/copy, or schedule
`rm -rf apps/frontend/.next` + clean rebuild + restart of the ambient pair as the FIRST step of the
next iteration; and any journey whose goal.md acceptance names a `[NEW]`-flagged walkthrough.
