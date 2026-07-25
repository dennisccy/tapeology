# Goal Session desk — Assumption Ledger

Append-only. An entry is added whenever scoring or planning required *interpreting*
`docs/goal.md` rather than just reading evidence. The human reviews these to catch
silent interpretation calls early.

## iter-0 — goal-evaluator

**Ambiguity:** J-07 ("The kept product stands — regression sentinel") mixes two kinds of
acceptance clause in one journey: kept-product behaviors checkable every iteration (suite green,
unchanged pin, browser walk of `/` and `/structure`, kept-route byte-identity) AND two
era-completion clauses that only become true once other journeys ship ("nav = exactly three
routes", "MCP = exactly 17 tools"). `docs/goal.md` never says how to score J-07 mid-era, and the
iteration spec explicitly delegated the call to the evaluator.
**We chose:** Score J-07 `partial` at baseline — kept half evidenced, era-completion half recorded
as unmet (2 routes / 15 tools today) — rather than `already_passing` on the kept half alone. Side
effect accepted: J-07 no longer sits at `passing`, so a later kept-product break will not
auto-trip the decision tree's `passing → failing` REGRESSION rule; it reaches REGRESSION instead
via critical rail 3 ("Frozen foundations … every KEPT surface's behaviour stays byte-identical"),
and that routing is stated in `iter-0/eval.md` and in the journey-history note so no later
evaluator loses the sentinel's halting power.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s Constraints state "every browser acceptance needs a screenshot — no
screenshot ⇒ the journey is `unknown`, never `passing`", but J-01's own acceptance text is tagged
"(Keyless; automated…)" and names no browser step, and browser QA was correctly SKIPPED
(`Frontend Present: no`). Nothing states what the evidence class is for a REST-only journey when the
browser lane does not run — and the evaluation methodology separately warns that unit tests are never
journey evidence.
**We chose:** Treat live REST through the REAL route handlers as the equivalent of a screenshot for a
journey whose acceptance has no browser clause — and require the evaluator to execute it personally,
not read it from a report. I ran all four J-01 clauses in-process against `app.main:app` with the
universe dir scoped to a temp dir and fixture HTML injected into the vendor seam (zero network), and
scored `passing` on that. Unit-test results alone would NOT have sufficed. Same rule will apply to
J-02/J-03 (also tagged keyless/automated); J-04/J-05/J-07's browser clauses still require screenshots.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** The desk-era anti-goal says universe snapshots are "append-only … nothing is silently
refetched, backfilled, recomputed in place, or rewritten". Audit finding B3 (which I reproduced) shows
a snapshot FILE that fails its checksum — surfaced in `integrity_errors`, never in `records` — is
silently overwritten at the same path when identical membership is re-recorded. The anti-goal does not
say whether "snapshot" means the registered record or the file on disk.
**We chose:** Read it as protecting the registered RECORD, so this is a minor gap (a silent self-heal)
rather than an anti-goal violation: no valid registered snapshot can be lost — the duplicate check
refuses before any write, which I verified byte-for-byte — and the replacement carries the same content
identity the filename asserts. Consequence: `anti_goal_violations` stays empty, so this does not block a
future GOAL_ACHIEVED; instead it is carried as a hardening item (make the replacement loud) in the
iter-2 recommendation. A stricter reading would make it a minor violation with the same practical fix.
**Reversible:** yes
