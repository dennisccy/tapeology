# Goal Iteration 34 — Fix the topup library-reach day-precision contradiction, honestly cap the earlier-pairs list, repoint J-19's golden script

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 34
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was `ESCALATE` (`iter-33/eval.md`); the depth-binding rule
  makes `full` mandatory with no exceptions, and it is also the engine's own binding recommendation
  for this iteration.
- **Frontend Present:** yes
- **Target journeys:** J-19
- **Required-still-passing journeys:** J-04, J-07, J-09, J-16, J-17
- **Anti-goal reminders:**
  - No execution path, ever. *(critical)*
  - No profit claims and no advice. *(critical)*
  - Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five states
    and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. *(critical)*
  - Hold-out-only promotion. *(critical)*
  - No lookahead. *(critical)*
  - Single source of truth — each shared value is computed once, owned by one canonical endpoint,
    and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations.
    *(critical)*
  - Deterministic and seeded.
  - Read-only MCP. *(critical)*
  - Immutable data. *(critical)*
  - Persistence stays scoped. *(critical)*
  - Membership is never a signal. *(critical)*
  - Snapshots are append-only and pinned. *(critical)*
  - Every run is an explicit operator act. *(critical)*
  - The briefing describes, never advises. *(critical)*
  - No new statistics, gates, or strategies. *(critical)*
  - The demolition stays demolished. *(critical)*
  - The ledger never holds orders. *(critical)*
  - The suite stays keyless and hermetic. *(critical)*
  - The fingerprint pin does not move. *(critical)*
  - The enhancement loop stays inside its box. *(critical)*
  - Host-guard caps are law. *(critical)*

## GOAL

Make `/desk`'s Top-up Runs "newest recorded reach" line and its "Pairs recorded earlier" list
agree with each other at the SAME (calendar-day) precision, cap that list to an honest, legible
size, and repoint J-19's stale golden script so it asserts the fix instead of the bug it was
recorded against.

## BACKGROUND

J-19 has been `partial` since iter-33: the record half (`store_frozen_through_after` on every
per-pair outcome) is proven and byte-unchanged since iter-32, but `topupLibraryReach`
(`apps/frontend/app/desk/page.tsx:878-904`) computes its "newest" extreme and its "earlier"
partition by comparing full microsecond-precision `store_frozen_through_after` strings, while the
render (`:996`, `:1014`) prints only the calendar day via `.slice(0, 10)`. The result, confirmed by
opening `reports/qa/goal-desk-iter-33-evidence/UT-J-19-fail.png` and reading the current source
directly this iteration: the "newest recorded reach 2026-07-30 · 101 pairs reach it" line sits
directly above rows in "Pairs recorded earlier (303)" that print that SAME day. iter-33's own spec
ordered exactly this fix (day-precision grouping + a cap at 20 rows with a "showing N of M"
disclosure only when the true total exceeds 20) but the engine dispatched it at `evidence` depth
twice running (a budget-breach demotion, then SPEED-9's evidence backstop firing because J-19 was
still recorded `passing` at the time) — no developer ran either time, so the fix was never written.
Verified directly this iteration: `apps/frontend/app/desk/page.tsx` still has no cap on the
`earlier` array and still compares full-precision strings; `test_desk_topup_library_reach_guard.py`
still has no day-truncation or cap assertion; `journey-scripts/J-19.json` step 4 still asserts
`"AAPL 4h — 2026-07-30"` as an earlier row — i.e. it enshrines the exact bug. The prior verdict was
`ESCALATE`, so this iteration's depth is `full`, mandatorily (rule: "ESCALATE from last eval ⇒
full, no exceptions") — this also finally puts a developer back in the loop per
`iteration-state.md`'s explicit note.

Per the priority rubric, J-19 is the only journey with open, non-human-blocked work: nothing is
regressed, the last `coherence.md` was COHERENCE-PASS (no consolidation owed), and every other
journey (J-01..J-18) is `passing` with the "do not redo" list binding against re-verifying them as
an iteration goal. This iteration targets J-19 alone (rule 6 — never bundle a second risky change
in).

**Lesson applied** (`lessons.md` iter-33): "any evidence-depth or zero-diff iteration that still
dispatches the demo lane... narration must be written from the rendered page." This iteration is
`full` depth with a real code change landing, so the demo-narrator step is legitimate this time —
but it MUST run strictly AFTER the fix is committed to the working tree and narrate only what the
rendered page shows post-fix. **Lesson applied** (`lessons.md` iter-32/iter-31): record the film
against the ambient `:3301`/`:8301` pair (no scoped rig — the ambient store already carries a real
top-up run with genuine reach variance, `topup-2026-07-31-8fb5c9a1f737`). **Lesson applied**
(`lessons.md` iter-30): do not write a blueprint "RESOLVED/NOTED" entry in the past tense before
the code lands — this spec's blueprint edit (below) is written to land in the SAME commit as the
code, and the evaluator will reconcile `iter-34/depth-dispatched` against this spec's `Depth: full`
before scoring.

## IN SCOPE

### Backend

- None. Zero diff to `desk_topup_compute.py`, `desk_topup_log.py`, `bars.py`, `bar_index.py`,
  `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `routes.py`'s
  `record_bar_series`. The stored `store_frozen_through_after` value and its precision are already
  correct (proven at iter-32); only the frontend's display-time grouping of that already-served
  value is wrong.

### Frontend

- [ ] `apps/frontend/app/desk/page.tsx` — fix `topupLibraryReach` (currently `:878-904`) to group
  and compare `store_frozen_through_after` at CALENDAR-DAY precision (the same precision already
  rendered via `.slice(0, 10)`), not full microsecond-timestamp precision. Concretely: derive a
  day-truncated key per outcome (`store_frozen_through_after?.slice(0, 10) ?? null`) once, use that
  truncated value to find the newest day, to count how many pairs reach it, and to partition
  "earlier" — never compare the untruncated timestamp for grouping purposes again. The returned
  `newestDate`/`earlier[].date` values may keep full precision for storage in the return shape (the
  render already truncates on display), but the GROUPING decision itself must use the truncated
  day, so a pair whose day matches the newest day is NEVER placed in "earlier" again, regardless of
  its sub-day precision.
- [ ] Same function: cap the returned `earlier` array at 20 entries (a literal, e.g.
  `EARLIER_PAIRS_DISPLAY_CAP = 20`), while preserving the TRUE total count so the heading can
  disclose it honestly. Do not silently truncate without disclosure.
- [ ] Render: when the true total of earlier-than-newest pairs exceeds 20, add one plain
  descriptive sentence beneath/beside the existing "Pairs recorded earlier (N)" heading reading
  exactly `showing 20 of <true total>` (wording at build discretion but must literally include
  "showing" and both the shown count and the true total) — no advice/urgency/judgement language
  (`test_copy_discipline.py` stays green unmodified). When the true total is ≤ 20, render the
  existing heading with no such sentence (unchanged behavior for small runs / most fixture-scoped
  or future smaller universes).
- [ ] No new section, no new control, no new ranked-table column, no new Top-up Runs
  summary-table column — J-16's measured width contract stays byte-unchanged. The fix is entirely
  inside the already-registered "library reach" block between `desk-topup-run-latest-window-basis`
  and `desk-topup-run-latest-failed`.
- [ ] `apps/backend/tests/test_desk_topup_library_reach_guard.py` — extend with:
  - a day-truncation assertion: a source-introspection or logic-level test proving the grouping key
    is a day-truncated slice, not the raw field (e.g. assert the function body truncates BEFORE
    comparing, per TC-2/TC-3 below);
  - a cap assertion: proves the earlier list is capped at 20 and the true total is preserved
    separately;
  - a seeded-violation counterpart for EACH new assertion (the file's own existing pattern,
    `test_the_fallback_text_guard_can_fail_on_a_seeded_violation`) — a guard that cannot fail
    proves nothing.

### Golden replay script maintenance

- [ ] `runs/goal-session-desk/journey-scripts/J-19.json` — repoint to stable substrings instead of
  today's exact pinned figures (the `J-18.json`/`J-09.json` hardening precedent already applied to
  `J-17.json` at iter-33): assert the presence of `"reach it"` on the reach line and
  `"Pairs recorded earlier"` on the earlier-list heading, and DO NOT assert any specific date or
  count that will drift on the next real ambient top-up run. Critically, remove the current step 4
  assertion of `"AAPL 4h — 2026-07-30"` as an earlier row (it currently enshrines the exact bug this
  iteration fixes) — replace it with a structural check that no earlier-row's own printed date
  equals the reach line's own printed newest date (or, if the replay tool cannot do a cross-step
  computed comparison, assert a stable non-date substring such as the row's own testid text pattern
  `SYMBOL TF — `).
- [ ] `runs/goal-session-desk/journey-scripts/J-17.json` — already refreshed at iter-33 (uncommitted
  at the time, now on HEAD via commit `efef1c1`); do NOT redo it.

### New user-facing capability

None beyond what J-19 already shipped at iter-32 (the reach line + earlier-pairs list already
exist) — this iteration makes that existing disclosure internally consistent and legible instead
of self-contradicting, and honestly discloses when the list is truncated.

### New information displayed

One new descriptive sentence, shown ONLY when the true earlier-pairs count exceeds 20: `showing 20
of <true total>`.

### New user actions

None.

### UI surface changes

`/desk` → Top-up Runs → latest-run detail → the existing "Pairs recorded earlier" block gains a
conditional one-line disclosure; no new section, control, or column.

### Product surface delta

The reach line and the earlier-pairs list can no longer name the same calendar day as both
"newest" and "earlier" for the same run; a run with more than 20 earlier pairs now says so
honestly instead of rendering an unbounded, fourteen-screen-tall list.

### Blueprint conformance

Lives under the existing Desk nav home's `/desk` Top-up Runs section (Information Architecture,
"Desk" row) — no nav-skeleton change. This is a correctness fix to the ALREADY-REGISTERED "Top-up
run records" Data Contract row's iter-32 addition (`store_frozen_through_after`), not a new row.

### Data-contract additions

None. No new field, endpoint, module, page, or `Config` field. The already-registered
`store_frozen_through_after` field (owner `desk_topup_log.py`, served by
`GET /research/desk/topup/runs`) is unchanged in shape and precision; only the frontend's
display-time GROUPING of that already-served value is corrected, and this iteration's blueprint
edit documents that correction under the existing row's notes (see below).

## OUT OF SCOPE

- Any change to `_pair_window`, `run_topup`, `desk_topup_log.py`, or the stored precision of
  `store_frozen_through`/`store_frozen_through_after` — those are already correct; do not touch
  them.
- Re-verifying J-01..J-18 as an iteration goal (all `passing`, "do not redo" list is binding).
- The four items explicitly marked owner-optional/never-a-new-iteration in `iteration-state.md`
  (B1/F1/T3/demo scroll-anchor; iter-32's two wording notes, subsumed by this fix).
- Any nav-skeleton, new page, new Config field, new MCP tool, or new ranked-table/Top-up-Runs
  summary-table column.
- A real ambient ~100-symbol top-up trigger. The ambient store already holds a real run
  (`topup-2026-07-31-8fb5c9a1f737`, 404/404 pairs, genuine reach-date variance across timeframes)
  sufficient to exercise both the fix and its browser/demo evidence — do not click "Top-up" again
  this iteration.
- Standing up any scoped/fixture rig for evidence capture (iter-27/28 lessons: teardown races and
  dead `base_url` overrides) — record all evidence against the ambient `:3301`/`:8301` pair after
  the mandatory `rm -rf apps/frontend/.next` + clean rebuild (T-9).

## DEFINITION OF DONE

- [ ] `topupLibraryReach` groups/compares `store_frozen_through_after` at calendar-day precision;
  no pair whose day matches the newest day's own printed date can appear in "earlier".
- [ ] The "earlier" list renders at most 20 rows; when the true total exceeds 20, one plain
  sentence discloses `showing 20 of <true total>`; when it does not, no such sentence renders.
- [ ] `test_desk_topup_library_reach_guard.py`'s new assertions (day-truncation + cap, each with a
  seeded-violation counterpart) pass.
- [ ] `journey-scripts/J-19.json` no longer asserts any specific date/count that will drift, and no
  longer asserts the bug (`"AAPL 4h — 2026-07-30"` as an earlier row) as correct.
- [ ] J-19 passes via browser-qa-agent: TC-1 through TC-6 below, all green, in a real browser after
  the T-9 clean rebuild.
- [ ] Required-still-passing journeys (J-04, J-07, J-09, J-16, J-17) remain green via deterministic
  golden-script replay.
- [ ] No anti-goal violation introduced; no ranked-table/Top-up-Runs-summary-table column added;
  `test_copy_discipline.py`, `test_desk_ui_guards.py`, `test_desk_hover_tooltip_guard.py` green
  unmodified.
- [ ] Full backend suite green (no regressions), `Config().config_fingerprint()` still
  `08e471b10130e1e2`, MCP surface still exactly 17 tools, zero new `Config` fields.
- [ ] A `[NEW]`-flagged demo-narrator walkthrough records the fixed disclosure end to end,
  narrated from the ACTUALLY-RENDERED post-fix page (not the spec's intent — the iter-33 lesson).
- [ ] `runs/goal-session-desk/state/blueprint.md` updated with a `RESOLVED at iter-34` note
  (written to land alongside the code, not claiming it shipped before it does).
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-34-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-19 (TC-1..TC-6 below), plus deterministic replay of J-04, J-07, J-09, J-16, J-17.
- Unit/integration: `test_desk_topup_library_reach_guard.py` extended per IN SCOPE; every existing
  test in `test_desk_topup_compute.py`, `test_desk_topup_log.py`, `test_desk_ui_guards.py`,
  `test_desk_hover_tooltip_guard.py`, `test_copy_discipline.py` passes unmodified.
- Error cases: a run where every outcome's `store_frozen_through_after` is `undefined` (legacy run)
  still renders `LIBRARY_REACH_NOT_RECORDED` and is unaffected by the day-truncation/cap logic; a
  run where every pair reaches the exact same day renders an empty "earlier" list (no section at
  all, since `earlier.length > 0` still gates it) rather than a spurious day-boundary false-earlier.

Test-first contract:

- TC-1: given the ambient `/desk` page after the T-9 clean rebuild, with the current latest
  top-up run (`topup-2026-07-31-8fb5c9a1f737`) on disk, when the page renders the Top-up Runs
  latest-run detail, then the "newest recorded reach" line's own printed calendar day never
  matches any row's own printed calendar day inside "Pairs recorded earlier".
- TC-2: given `topupLibraryReach` called with two outcomes whose `store_frozen_through_after`
  values are the same calendar day but different microsecond timestamps (e.g.
  `2026-07-30T09:00:00.000000Z` and `2026-07-30T23:00:00.000000Z`), when the function groups them,
  then both are treated as the SAME day and neither appears in the returned `earlier` array.
- TC-3: given `topupLibraryReach` called with 25 outcomes whose `store_frozen_through_after` values
  are all earlier (by day) than one outcome's newest day, when the function returns its result,
  then the returned `earlier` array has length 20 and a separate true-total value of 25.
  - TC-4: given a run whose true earlier-pairs total is 25, when `/desk` renders the latest-run
  detail, then the page shows the text `showing 20 of 25` (or equivalent wording carrying both
  numbers) beside the "Pairs recorded earlier" heading.
- TC-5: given a run whose true earlier-pairs total is ≤ 20 (or 0), when `/desk` renders the
  latest-run detail, then no "showing N of M" sentence is present anywhere in that block.
- TC-6: given a legacy run recorded before iter-32 (no `store_frozen_through_after` on any
  outcome), when `/desk` renders its latest-run detail, then the text
  `"library reach not recorded in this run"` is shown and neither the day-truncation nor the cap
  logic alters that fallback.
- TC-7: given `test_desk_topup_library_reach_guard.py`'s new day-truncation assertion, when a
  seeded violation (grouping by the raw untruncated field) is fed to the same check, then the check
  fails — proving the guard is not vacuous.
- TC-8: given `test_desk_topup_library_reach_guard.py`'s new cap assertion, when a seeded violation
  (an uncapped `earlier` array of length > 20) is fed to the same check, then the check fails.
- TC-9: given the repointed `journey-scripts/J-19.json`, when it replays against the ambient
  `/desk` page, then it passes without asserting any specific date, count, or the bug's own
  contradictory row text.
- TC-10: given the existing full backend suite, when it runs after this iteration's change, then it
  passes with zero failures and `Config().config_fingerprint()` still reads `08e471b10130e1e2`.

## NOTES

- Evidence route: no real top-up trigger needed this iteration — the ambient store already holds
  `topup-2026-07-31-8fb5c9a1f737` with genuine cross-timeframe reach-date variance (per
  `docs/goal.md`'s J-19 rationale paragraph: 88 members' `1h` through 07-28, several through
  07-24/07-21), which is exactly the fixture the fix needs to prove TC-1/TC-2 live. Do not click
  "Top-up" again (`lessons.md` iter-32's coupling-invalidation lesson: every real ambient run
  invalidates sibling golden scripts pinned to the "latest" panel — one trigger already did that
  once this era, do not compound it).
- If the true earlier-pairs total for the CURRENT ambient run happens to be ≤ 20 after the
  day-truncation fix (i.e., most of the 303 previously-miscounted-as-earlier pairs turn out to
  share the newest day once grouped correctly), TC-4's "showing N of M" clause may need to be
  verified with a synthetic/unit-level input (TC-3) rather than live on the ambient page — this is
  expected and acceptable; TC-1/TC-2/TC-9 remain the live acceptance bar. Disclose in the dev
  handoff which of TC-1..TC-9 were verified live vs. at the unit/fixture level, per T-10's evidence
  honesty rule (screenshots for the live ones; test output for the rest — never claim a live
  screenshot exists when it does not).
- Golden-script maintenance is scoped explicitly to J-19.json this iteration; J-17.json was already
  refreshed at iter-33 (now on HEAD) — do not touch it again.
