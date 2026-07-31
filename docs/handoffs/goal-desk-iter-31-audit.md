# goal-desk-iter-31 Audit Report

**Date:** 2026-07-31
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration did exactly what it said and nothing else: the `failed_member` fabrication is gone
(verified first-hand — TC-1 fails `assert 'AAA' is None` against the old expression and passes
against the new one), the reused-run detail block no longer shows the false-failure amber note or
the zeroed counts (verified by reading the QA screenshot myself, not by trusting the row), and both
build files are byte-identical to their pre-iteration-30 content with zero scratchpad paths
anywhere. The working diff is 5 files / 1 changed backend line / 2 changed JSX lines / 68 added
test lines — no scope creep. Two GAP-level limitations survive, both inherent to the *shape the
spec ordered* rather than to the implementation: `attempted == 0` also swallows the case where the
FIRST member is the one that crashed, and the counts-line suppression also hides genuine counts on
the `ScreenAlreadyRecorded` reuse race. Neither is a defect against the spec, neither loses or
corrupts recorded data, and neither should become a future iteration's goal.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): `attempted == 0` conflates "crashed before the walk" with "crashed on the FIRST
member"**
`apps/backend/app/research/desk_screen_compute.py:277` now records `failed_member = None` whenever
`attempted == 0`. But `compute_screen` calls `progress({"symbol": symbol})` at the END of each
member's processing (`apps/backend/app/research/desk_screen.py:513-514`), so `attempted` is the
count of *completed* members — a raise while processing member index 0 also leaves `attempted == 0`.
Before this iteration that case recorded `members[0]`, which was the genuinely failing symbol; it
now records `null`. This is information loss, not fabrication (the UI renders
`"(member not recorded)"` — `apps/frontend/app/desk/page.tsx:1346` — and the verbatim exception is
still stored in `error`), and it is precisely the rule the spec ordered (`docs/phases/goal-desk-iter-31.md:101-104`,
TC-1 at :217-219). Distinguishing the two would need a new "current member" signal threaded through
`compute_screen` — a new contract, out of this iteration's blast radius. Not fixed; documented.
Note the implementation summary's phrasing ("fails before it has even started looking at the first
company … never got that far", `reports/phase-goal-desk-iter-31-implementation-summary.md:29-33`)
overstates this: it is accurate for a pre-loop crash, not for a first-member crash.

**B2 — OBSERVATION (observation): `failed_member` has no other consumer that can break on `null`**
Verified rather than assumed: the only readers are the store's own passthrough
(`desk_screen_log.py:182,216,242,266` — typed `str | None`, no state/field coupling, no validation
that a `"failed"` record must name a member), the route's heavy-key strip
(`desk_routes.py:494` — the field never appears on list rows, only on `latest`), and the two
frontend sites (`lib/types.ts:1131`, `page.tsx:1346`, both `| null`-aware). No report, MCP tool, or
golden script reads it. The `null` is a first-class value end-to-end.

### Frontend Findings

**F1 — GAP (gap): the counts line is also suppressed on the `ScreenAlreadyRecorded` reuse path,
where a full walk really happened**
`apps/frontend/app/desk/page.tsx:1337` gates the counts line on `run.state === "done" && !run.reused`.
There are two distinct producers of `done && reused`: the pre-check short-circuit
(`desk_screen_compute.py:212-218` — `members_attempted: 0`, zeroed counts, nothing to show, the case
this iteration targets) and the record-time race backstop (`desk_screen_compute.py:260-272` — the
walk DID run, `members_attempted == members_total`, and `ranked_count`/`skipped_by_reason` carry
genuine values). The new guard hides real counts in the second case. Reachable in practice: an
operator CLI run (`python -m app.research.desk_screen_compute`) recording the same pins while a UI
walk is in flight — the module's own comment calls this "the structural backstop for the race"
(`desk_screen_compute.py:264-265`). Nothing is lost or wrong on disk; `GET /research/desk/screen/runs`
still serves both fields, and `desk-screen-run-latest-attempted` still renders "N of N members
attempted" beside it. The spec ordered the coarse `done && reused` condition verbatim
(`docs/phases/goal-desk-iter-31.md:113-117`), so tightening it here would be a deviation from spec,
not a fix. Not fixed; documented.

**F2 — OBSERVATION (observation, pre-existing): `screenRunOutcomeText` claims "no walk was
performed" for every `done && reused` run**
`apps/frontend/app/desk/page.tsx:1252-1255` returns `reused <id> — no walk was performed` on state
alone. On the F1 race path a full 101-member walk *was* performed, so that sentence is false there.
Shipped at iter-29, untouched by this iteration, and this iteration's own rationale leans on it
("the run's own `screenRunOutcomeText` already discloses this honestly"). The rendered
"N of N members attempted" line contradicts it on-screen, so the DOM is not silent — but the prose
is wrong on that path. Pre-existing; not introduced or worsened in kind by this iteration.

### Test Findings

**T1 — OBSERVATION (observation): TC-3's completeness assertion is self-referential**
`apps/backend/tests/test_desk_screen_compute.py:762` asserts
`run["members_attempted"] == run["members_total"]` without pinning the member count. Both sides come
from the same universe snapshot, so the assertion would hold vacuously (`0 == 0`) if the fixture
ever degenerated. Non-vacuous today — I read the fixture directly:
`tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json` carries `member_count: 103`. Tight
enough for its purpose (one record, right state, right `screen_id`); the missing `> 0` pin is worth
a line, not a fix.

**T2 — OBSERVATION (observation, pre-existing): the full suite prints no pass/fail summary line**
Reproduced twice in my own runs (and visible in the pipeline's own
`$TMPDIR/full_pytest.log`): a whole-directory run ends after the warnings block with no
`"N passed, M skipped in X.XXs"` line, so every downstream "1502 passed" claim in this iteration
rests on counting progress characters. Exit code 0 still proves zero failures, and I settled the
count authoritatively with `--junitxml` (below), so this is an evidence-quality wrinkle, not a
correctness risk. Pre-existing and out of this iteration's blast radius.

**T3 — OBSERVATION (observation): `journey-scripts/J-18.json`'s note 4 is now stale**
The note asserts, in the present tense, that `LatestScreenRunDetail` "still renders both
`data-testid="desk-screen-run-latest-unreached"` … and `desk-screen-run-latest-counts` …
unconditionally for the latest reused run" and that "the frontend code was NOT changed this
iteration". That was true when written at iter-30 and is false after this iteration. The field is
inert metadata (only `steps` drives replay) and the spec put re-pinning J-18.json out of scope, so I
did not touch the golden script — but a future reader taking that note at face value would be
misled, and this session's own iter-30 lesson is precisely about stale past/present-tense claims.

---

## 3. Domain Assessment

The two fixes are correct in the direction that matters for this project's honesty contract: a run
record must never assert something the run did not do. B1's remaining coarseness is a *silence*, not
a claim, which is the right way to fail on this axis — `null` renders as "(member not recorded)"
rather than pointing at an innocent symbol. F1's suppression is the same trade in the UI: the reused
short-circuit's zeroed counts were a false failure signal and are now gone; the price is that a rare
race path's genuine counts are also hidden from the detail block (still served by the canonical
endpoint, so single-source-of-truth is intact — no value is recomputed or re-derived anywhere).

Architecture rules hold. No new module, endpoint, `Config` field, MCP tool, or Data-Contract row;
`Config().config_fingerprint()` = `08e471b10130e1e2` and `len(app.mcp.TOOL_NAMES)` = `17`, both
executed by me directly, not read from a handoff. The append-only/pinned discipline is untouched —
`ScreenRunStore.record` still writes a fresh checksummed file per call
(`desk_screen_log.py:192-220`) and this iteration adds no rewrite path. Hermeticity holds: TC-3's
CLI run resolves its log dir through `resolve_desk_screen_log_dir` off the monkeypatched
`TAPEOLOGY_DESK_UNIVERSE_DIR`, i.e. `tmp_path/screen_runs`, never the operator's `.data`
(`desk_screen_log.py:80-83`, `tests/test_desk_screen_compute.py:678-684`). No test reaches the
network. Repo hygiene: both build files diff clean against `git show 48c5fc2^` and contain zero
`scratchpad`/absolute paths — this iteration's browser-QA and demo runs used the ambient
`:3301`/`:8301` pair, so no scoped rig existed to re-pollute them.

Evidence I produced first-hand rather than inherited:

| Claim | My own evidence |
|---|---|
| Fix genuinely fixes the bug (before AND after) | Temporarily restored the old expression → `FAILED … test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null`, `AssertionError: assert 'AAA' is None`; restored from backup, md5 match, diff back to the single line |
| Full suite green | `pytest tests/ -q --junitxml` → `tests=1510, failures=0, errors=0, skipped=8` ⇒ **1502 passed**, exit 0 (two independent runs) |
| Fingerprint / MCP contract | `Config().config_fingerprint()` → `08e471b10130e1e2`; `len(app.mcp.TOOL_NAMES)` → `17` |
| Build files pristine | `git show 48c5fc2^:… \| diff -` → zero diff on both; `grep scratchpad` → 0 hits |
| Reused-run suppression on screen | Read `reports/qa/goal-desk-iter-31-evidence/UT-02-result.png` directly: "Latest run" shows `state: done · 0 of 101 members attempted · 0s elapsed · reused screen-2026-07-31-c169546856c7 — no walk was performed` and **no** amber note, **no** counts row |
| Golden replay reality | Read `J-18-verify.png` — real `/desk` render with live provenance (fingerprint `08e471b10130e1e2` on screen), not an error page |
| Walkthrough frames distinct | `md5sum reports/demo/goal-desk-iter-31/step-0*.png` → 3 distinct hashes (the iter-29 duplicate-frame gap did NOT recur) |

**DEFINITION OF DONE — verification state**

1. *J-18 via browser-qa (replay green + live reused-run check)* — **verified**, and I did not take
   this one on citation alone: the golden replay row is `reports/phase-goal-desk-iter-31-regression-replay-results.md`
   (J-18 4/4 steps) and the live check is `reports/phase-goal-desk-iter-31-ui-test-results.md` UT-02,
   whose screenshot I opened and confirmed myself. The absence of both testids is only possible
   against the NEW build (the old code would render the amber note for this exact run:
   `unreached = 101 - 0 > 0`), so the served bundle demonstrably carries the fix.
2. *10 required-still-passing journeys green* — accepted on citation: reviewer `issues: []` /
   `spec_alignment.definition_of_done: complete` (`reports/reviews/goal-desk-iter-31-review.md`)
   plus the executed replay table (10/10 PASS, one screenshot per journey,
   `reports/phase-goal-desk-iter-31-regression-replay-results.md`). Mechanical, executed against the
   running system, two independent verifications — no third re-trace.
3. *No anti-goal violation left open* — **verified by me**, with one honest correction to the QA
   report (see D1 below).
4. *Suite ≥1,500 pass / 8 skip, fingerprint, 17 MCP tools* — **re-executed by me** (junit counts
   above); matches dev and QA exactly.
5. *Dev handoff written* — present, and its own disclosures (the missing summary line, "no browser
   QA run by this agent") are accurate, not spin.

**D1 — OBSERVATION (observation): DoD item 3's literal check cannot pass before the commit, and QA's
wording glosses it.** `docs/phases/goal-desk-iter-31.md:199` requires
`git status --porcelain -- apps/frontend/next-env.d.ts apps/frontend/tsconfig.json` to be *empty*.
It is not — it reports ` M` for both, because HEAD (`48c5fc2`/`639b11b`) is what carries the
polluted content, so the revert necessarily shows as a working-tree diff until this iteration is
committed. The QA report's line 147 ("`git status --porcelain …` shows clean revert") reads as if
the command returned nothing; it did not. The substance the item exists for — TC-9's "the rig did
not re-pollute", TC-6's "no `/scratchpad/` and the reference path reads `./.next/types/routes.d.ts`"
— is fully satisfied and I verified it against the pristine blob directly. Spec wording flaw, not an
implementation flaw.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT finding survived verification; every finding above is a GAP or
OBSERVATION, and the rules forbid fixing those (it would be scope creep — and for B1/F1 it would
also mean deviating from the condition the spec ordered verbatim). The only file I touched was a
deliberate, restored-in-the-same-command temporary revert of
`apps/backend/app/research/desk_screen_compute.py` to prove TC-1 discriminates; md5 before/after
match and `git diff --stat` shows the working tree back to this iteration's intended 5-file diff.

---

## 5. Recommended Next Step

Proceed. This iteration closed all five follow-ups the iteration-30 evaluator named, the ESCALATE
condition is discharged, and nothing here blocks J-18 or a GOAL_ACHIEVED re-confirmation.

Explicitly **do not** spin B1, F1, F2, T1, T2, or T3 into a follow-up iteration. They are
documentation-grade limitations of a spec-ordered shape (B1, F1), pre-existing prose/test-infra
wrinkles (F2, T1, T2), or an inert stale comment (T3) — promoting any of them would be manufacturing
low-value work in a session that is already past its goal. If a future iteration touches
`LatestScreenRunDetail` or the screen-run failure path for an independent reason, F1's tighter
condition (`!(run.reused && run.members_attempted === 0)`) and T3's note refresh are cheap
ride-alongs at that time. The `[NEW]` walkthrough passenger converged this run — three distinct
frames — so the iter-30 evaluator's "last time I ask" bound is satisfied rather than expired.
