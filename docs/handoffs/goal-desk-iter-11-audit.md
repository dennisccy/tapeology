# goal-desk-iter-11 Audit Report

**Date:** 2026-07-28
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-09's product capability is genuinely built and genuinely evidenced: a checksummed, append-only
`TopupRunStore` written **exactly once**, at terminal state, by a **single** shared writer that I
verified by grep is the only write path in the codebase; `GET /research/desk/topup/runs` serving the
honest-empty payload and a `latest` whose `outcomes` are proven byte-identical to `run_topup`'s own
return by a spy wrapping the **real** function; and a `/desk` panel whose populated state I read off
the evidence PNGs myself (`404/404 attempted · 0 reused · 403 fetched · 1 failed`, `AAPL 4h — no
data for that window`, `401 pairs not reached`). `run_topup`/`_run_one_pair` are byte-identical to
HEAD (AST-level check, not a diffstat glance), the fingerprint is still `08e471b10130e1e2`, and the
frozen-file diffs are empty. Two spec'd test contracts, however, had never actually been executed by
any lane — TC-9's `get_endpoint` byte-identity and TC-7's interrupted-run guarantee (whose test was
vacuous) — both now written and passing; and TC-16's `[NEW]` demo walkthrough ships only the empty
half of the "empty → populated with a failed pair" disclosure it was specified to cover, which is a
showcase-lane shortfall I could not close surgically.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): `GET /research/desk/topup/runs` silently discards the store's integrity errors**
`apps/backend/app/research/desk_routes.py:258` does `records, _errors = store.list()` and returns
only `{"runs": ..., "latest": ...}`. Both sibling desk routes surface theirs — universe at
`desk_routes.py:150-152` (`"integrity_errors": errors`) and screen at `desk_routes.py:304-311`. The
new store *does* produce them correctly (`desk_topup_log.py:157-158`, covered by
`test_desk_topup_log.py:194-231`); the route is where they die. Consequence: a run record file
corrupted by a partial `write_text` (`desk_topup_log.py:206`, the same non-atomic write both sibling
stores use — a power loss mid-write is the realistic trigger) disappears from the *only* surface
that discloses run history, and the operator gets no signal at all. In a codebase whose stated rule
is "a corrupt file is surfaced, never silently hidden" (`desk_topup_log.py:141-148`, this module's
own docstring), that is a real hole.
**NOT fixed, deliberately.** The phase spec pins the response body to exactly two keys
(`docs/phases/goal-desk-iter-11.md`, Data-contract additions) and TC-1 asserts that exact body
(`test_desk_topup_compute.py:698`, `assert r.json() == {"runs": [], "latest": None}`). Adding a
third key is spec drift, not spec implementation. Recommend the next `/desk`-touching iteration
adopt the sibling `integrity_errors` convention and update the contract row with it.
*(I was torn between GAP and IMPORTANT here. It lands at GAP because the code matches the
specification exactly — the limitation is in what the spec asked for, which is the definition of a
GAP, not a specified behavior failing.)*

**B2 — OBSERVATION (gap): the two entry points disagree about what a no-universe top-up is**
`DeskTopupComputeManager.trigger()` with no registered universe snapshot still creates a zero-pair
job that resolves `"done"` (`desk_topup_compute.py:254-257`, `:327-329`) and therefore writes a
record with `pairs_total: 0`, `pairs_attempted: 0`, `universe_snapshot_id: null` — a row that will
render on `/desk`. The CLI in the same situation refuses and exits 1 before any writer call
(`desk_topup_compute.py:408-415`, asserted by
`test_cli_with_no_universe_snapshot_persists_no_run_record`). Both behaviours are honest and both
are tested; the ledger's meaning just differs by entry point. Traceable to the pre-existing J-02
difference between the two callers, not to the new writer.

**B3 — OBSERVATION (gap): the runs list is read in full on every page load and is unbounded**
`TopupRunStore.list()` parses every record file and deep-copies every `outcomes` entry
(`desk_topup_log.py:153-156`) before `desk_routes.py:260` throws `outcomes` away for the meta-only
projection. A real run carries 404 outcomes; the log is append-only with no cap, and `/desk`
fetches it on every mount. Identical to `ScreenStore`'s established pattern and negligible at
today's 0–3 records, but it is the same page-load cost curve Era 5C ("The Fast Wall") had to flatten
for screens and datasets. Worth watching before the operator has run a few hundred top-ups.

**B4 — OBSERVATION (gap): one input under which the DoD's cancelled-run inequality does not hold**
`desk_topup_compute.py:327` reads `cancel_event.is_set()` *after* the walk returns, so a cancel
signalled between the final pair completing and that line records `state: "cancelled"` with
`pairs_attempted == pairs_total` — not `<`. This is pre-existing J-02 state semantics, byte-unchanged
this iteration, and it is honest (the run genuinely was cancelled and genuinely had reached every
pair). Noting it only because the DoD states the inequality unconditionally.

### Frontend Findings

**F1 — GAP (gap): the single-shot run-log refresh can lose a race with the backend's disk write**
`apps/frontend/app/desk/page.tsx:1116-1121` re-fetches `/topup/runs` exactly once, the first time a
poll tick observes a non-`running` compute state — and the effect then tears its own interval down.
On the backend, `_resolve` (in-memory terminal state) and `_record_run` (the disk write) are two
sequential calls (`desk_topup_compute.py:328-329`), so a poll landing between them refreshes an
un-updated list and never retries; the just-finished run stays invisible until a manual reload. The
reviewer flagged the same at `reports/reviews/goal-desk-iter-11-review.md`. Window is the few
milliseconds of `record()` against a 700 ms poll, it self-heals on reload, browser QA observed the
happy path (UT-07), and no DoD clause requires auto-refresh at all — so this is not fixed. A second
delayed re-fetch, or keeping one extra poll tick alive, closes it.

**F2 — OBSERVATION (gap): the panel is not literally beside Screen History**
The DoD says "beside the existing Screen History panel"; the built section renders as a top-level
`<section aria-label="Top-up runs">` after the whole screen-state conditional
(`page.tsx:1276-1280`), so the **Run Screen / Top-up controls** section sits between the Top-up
button and the panel that reports that button's result — visible in the evidence PNG
`UT-05-failed-pair-detail-legible.png` (order: Screen History → Run Screen/Top-up → Top-up Runs).
The deviation is disclosed three times (dev handoff interpretation call 2, frontend handoff,
`assumptions.md` iter-11, plus an in-file comment) and is explicitly sanctioned by the plan's "not a
hard requirement, log the final placement choice if changed". It buys a real property: the panel
renders in *every* page state, including before any screen exists — which TC-12's precondition needs.
Discoverability was independently re-tested (UT-09). Correct call, worth recording.

**F3 — OBSERVATION (gap): no cap or pagination on the run table**
`TopupRunsTable` (`page.tsx:550-573`) renders one row per historical run with no limit. Fine now,
the counterpart of B3 later.

### Test Findings

**T1 — IMPORTANT (fixed): TC-9's `get_endpoint` byte-identity clause had never been executed**
TC-9 requires that `get_endpoint(path="/research/desk/topup/runs")` return the identical JSON body a
direct GET returns, and the DoD carries "`get_endpoint` reaches the new path with zero
`_STATIC_PATHS` addition". Every lane cited only the **tool count**: QA's TC-09 row
(`reports/qa/goal-desk-iter-11-qa.md:49`) says "test_mcp_server.py passes unmodified (17 tools)";
browser QA's UT-J-06 says the same; the dev handoff asserts reachability from reading the allowlist
constant. `grep -n topup apps/backend/tests/test_mcp_server.py` returned **zero hits** — the new path
was never sent through the proxy by anything. Per the evidence floor in `.claude/judgment-rubrics.md`
§5, "API works" needs a real request/response, so this DoD line was `unknown`, not `done`.
**Fixed:** added `test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool`
(`apps/backend/tests/test_mcp_server.py:904-920`) — proxies the new path through the real
`call_tool("get_endpoint", ...)` against the module's real uvicorn backend and asserts the bytes
match `httpx.get(...)`, the payload is the honest-empty `{"runs": [], "latest": null}`, and
`len(TOOL_NAMES) == 17`. Verified: `pytest tests/test_mcp_server.py` → **35 passed** (was 34), and
by name: `PASSED tests/test_mcp_server.py::test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool`.

**T2 — IMPORTANT (fixed): the interrupted-run test was vacuous**
TC-7 and the DoD both turn on "a run interrupted before its terminal write leaves zero new record".
The test carrying that guarantee,
`test_desk_topup_log.py:177-188` (`test_a_run_that_never_reaches_the_writer_call_leaves_the_store_untouched`),
constructs a store, runs **no top-up at all**, and asserts the store is empty — it proves only that
an untouched store holds no files. It would still pass if a future change made the manager write a
speculative "pending" record at run start, which is precisely the failure mode the phase spec named
("a crash mid-walk fabricating a record for a run that never reached its terminal state"). The
underlying behaviour is in fact correct — I confirmed by grep that `desk_topup_log.py:206` is the
only `write_text`/write path in the module and it is reached only from `record()` — but the guard was
not guarding.
**Fixed:** added `test_a_walk_interrupted_before_the_terminal_write_leaves_zero_run_record`
(`apps/backend/tests/test_desk_topup_compute.py:289-329`). It triggers a real manager job whose
`_run_one_pair` raises `SystemExit` on the third pair; neither `_run_one_pair`'s `except Exception`
nor `_work`'s catches a `BaseException`, so `_resolve` and the writer never run and `threading`
retires the worker silently — a faithful stand-in for a killed process. It asserts the walk really
happened (3 calls, 2 outcomes published into the live snapshot), that the job never resolved
(`state == "running"`, proving the line *before* the writer never executed), and that the store
gained **zero** files and its directory was never even created. Verified:
`pytest tests/test_desk_topup_compute.py` → **24 passed** (was 23), and by name:
`PASSED tests/test_desk_topup_compute.py::test_a_walk_interrupted_before_the_terminal_write_leaves_zero_run_record`.

**T3 — IMPORTANT (gap, not fixed): the `[NEW]` demo walkthrough covers only half the specified disclosure**
TC-16 asks for "a walkthrough entry flagged `[NEW]` describing the top-up-run disclosure (an empty
run history, **then a populated one with a failed pair**)", and goal.md's own J-09 Acceptance says
the walkthrough "covers the top-up-run disclosure **end to end**". `reports/phase-goal-desk-iter-11-demo.json`
contains exactly one J-09 step (step 2, `new: true`, "See the new record of every top-up run"), and
its narration/point-out describe only the empty state ("It plainly says none have been saved yet").
There is no populated / failed-pair step. **Not fixed:** the demo lane records against the live
frontend, and the ambient backend genuinely has zero runs — producing the populated half requires
re-running demo-narrator + `demo_runner.py` against the fixture-scoped rig with the three checkpoint
runs loaded, which is a pipeline lane, not a surgical auditor edit, and showcase steps are
non-blocking by this framework's own definition. The populated state *is* evidenced to acceptance
grade elsewhere (UT-03/04/05/06 + PNGs, which I read directly). *(Unsure between IMPORTANT and GAP;
took the higher per the rubric, because the spec and goal.md both name the missing half explicitly.)*

**T4 — GAP (gap): the J-09 golden asserts only the state the feature is designed to leave behind**
`runs/goal-session-desk/journey-scripts/J-09.json` is three `goto /desk` steps asserting "Top-up
Runs", "No top-up runs recorded yet." and "Desk". It gives the new capability's *populated* surface —
the table, the counts, the failed-pair detail, the unreached note — zero deterministic regression
protection, and its middle assertion is guaranteed to break the first time a real operator top-up
lands a record on the ambient store. Both facts are honestly disclosed in the script's own `notes`
(the read-only choice is the correct application of the iter-4/iter-5 write-triggering-golden
lesson, and the post-match liveness step 3 the spec asked for is present). TC-15's verify run is
reported PASS (`reports/phase-goal-desk-iter-11-ui-test-results.llm.md:172`), though against the
restored **ambient** backend rather than a throw-away one — harmless here precisely because the
script issues no writes.

---

## 3. Domain Assessment

The core discipline of this journey is *not fabricating provenance*, and the implementation gets the
hard parts right for reasons I verified rather than took on trust:

- **One writer, structurally.** `grep record_topup_run` across `apps/backend/app` returns exactly two
  call sites — `desk_topup_compute.py:302` (both `_work` exit paths, via the `_record_run` closure)
  and `:436` (CLI) — plus the definition. `desk_topup_log.py` contains exactly one `write_text`. The
  free-function-over-method indirection buys real greppability, not ceremony.
- **The frozen surface is genuinely frozen.** I extracted `run_topup`, `_run_one_pair`,
  `_fetch_window_now` and `_iso_utc_now` from `HEAD` and from the working tree via AST and compared
  source segments: all four **byte-identical**. The record is a pure persistence lens over an
  unchanged computation, as the era's Frozen-foundations rail requires.
- **"Attempted and failed" vs "never reached" stay distinct.** `pairs_attempted` is derived at write
  time from `len(outcomes)` (`desk_topup_log.py:200`), never a parallel counter, and the UI shows
  `pairs_total − pairs_attempted` as its own amber note that is *omitted entirely* at zero rather than
  rendered as a false "0 not reached" (`page.tsx:601-605`) — UT-06 Part B confirmed structural
  absence from the DOM, not a hidden element. This is exactly the conflation the journey exists to
  prevent.
- **`requested_window` captured once per run** in each caller (`desk_topup_compute.py:281`, `:428`),
  never re-derived in the writer — the plan's trap #3, implemented as written and logged in
  `assumptions.md`.
- **Job snapshot untouched.** `self._snapshot` gained no key; `universe_snapshot_id`,
  `requested_window` and `collected` are closure locals, and the crash path deliberately writes from
  `collected` rather than the shared snapshot so a superseding job can't poison the record. That is
  the right instinct, and it is the trap the plan warned would draw a coherence hard-fail.
- **Anti-goal sweep.** No execution path, no new statistic or gate, no scheduler (the new GET is a
  pure read — TC-8 plus browser QA's uvicorn access-log diff across three reloads show zero POSTs),
  read-only MCP unchanged at 17 tools, no new `Config` field (`resolve_desk_topup_log_dir` mirrors
  `resolve_desk_screen_dir` verbatim), and the proposer's `docs/goal.md` edit is `+63/−0` entirely
  inside the `AUTO:journeys` block (lines 514–630) — the enhancement loop stayed in its box.

Where the domain reasoning is thinner: the *reused/fetched/failed* aggregate is now computed in two
places — `page.tsx:518-528` and the CLI's summary print (`desk_topup_compute.py:450-452`, pre-existing).
Neither is a Data-Contract value (the contract serves `outcomes`, not counts), and the frontend
derives it from the verbatim served array, so I do not read this as a single-source-of-truth breach;
flagging it so the coherence-auditor can rule independently rather than discover it.

Evidence I checked first-hand rather than relaying: the populated-panel and cancelled-run PNGs (I
cropped and upsampled `UT-06-partA` myself to confirm `3 of 404 pairs attempted · 3 reused · 0
fetched · 0 failed · 401 pairs not reached` — the counts sum to `pairs_attempted` and `404 − 3 = 401`
both check out), `Config().config_fingerprint()` → `08e471b10130e1e2`, empty `git diff --stat` for
every frozen file, `blueprint.md`'s new Data-Contract row matching the shipped shape field for field,
and the full suite.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_mcp_server.py` | Added `test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool` — executes TC-9's never-run clause: proxies `/research/desk/topup/runs` through `get_endpoint` against the real uvicorn backend and asserts byte-identity with the direct GET, the honest-empty payload, and `len(TOOL_NAMES) == 17`. Re-ran → 35 passed (was 34). |
| 2 | Important | `apps/backend/tests/test_desk_topup_compute.py` | Added `test_a_walk_interrupted_before_the_terminal_write_leaves_zero_run_record` — replaces vacuous TC-7 coverage with a manager job that really walks pairs and then dies (`SystemExit`) before the terminal write; asserts 2 outcomes published, job never resolved, and zero files/no directory in the store. Re-ran → 24 passed (was 23). |
| 3 | — | `docs/handoffs/goal-desk-iter-11-dev.md` | Appended an auditor addendum superseding the suite counts the two fixes above changed (1367→1369 passed), without rewriting the developer's own record. |

**No production code was changed by this audit.** `git diff --stat HEAD -- apps/` shows my edits
confined to the two test files; `desk_topup_log.py`, `desk_topup_compute.py`, `desk_routes.py`,
`page.tsx`, `api.ts` and `types.ts` carry the developer's diff only.

**Post-fix verification (full):**
`cd apps/backend && .venv/bin/python -m pytest tests/` → **1369 passed, 8 skipped, 0 failed in
128.62s** (floor 1346/8; developer's own run was 1367/8 — the delta is exactly my two tests, zero
regressions). `Config().config_fingerprint()` re-checked → `08e471b10130e1e2`. `git diff --stat` for
`tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`, `config.py`, `mcp/__init__.py` and
`test_copy_discipline.py` → empty.

---

## 5. Recommended Next Step

**Proceed.** J-09's capability is built, correct, and evidenced at journey level; nothing found here
compromises the phase goal, and the two clauses that were merely *asserted* rather than *executed*
are now executed and passing. The goal-evaluator should weigh one item deliberately: **T3** — the
`[NEW]` demo walkthrough ships only the empty half of the "empty → populated with a failed pair"
disclosure that both the phase spec (TC-16) and goal.md's own J-09 Acceptance name. If that clause is
read strictly, the honest status for it is `partial` and the fix is a demo-lane re-record against the
fixture-scoped rig (the same rig `reports/phase-goal-desk-iter-11-ui-test-results.llm.md` documents,
with its three checkpoint runs) — a small, well-specified follow-up, not a rebuild.

Carry forward, un-fixed by design: **B1** (adopt the sibling `integrity_errors` convention on
`/research/desk/topup/runs` and widen the contract row to match) and **F1** (a second delayed
re-fetch, or one extra poll tick, to close the auto-refresh race) — both are one-line-class changes
for whichever iteration next touches `/desk`, and neither is worth a spec deviation now. **T4**'s
golden-script limitation should be revisited the moment a real operator top-up run lands on the
ambient store: the script's empty-state assertion will break honestly at that point, and the fix is
to repoint it at the new latest run's own rendered stats, disclosed in the script's `notes` per the
iter-8 lesson.
