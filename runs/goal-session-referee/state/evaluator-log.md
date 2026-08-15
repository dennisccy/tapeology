# Goal Session referee — Evaluator Log

Append-only chronological record. One entry per evaluated iteration.

## Iteration 0 — goal-referee-iter-0

**Date:** 2026-08-14T15:37:59Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly failing: J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09 (first recorded state — the Referee machinery is unbuilt by design)
- Partial: J-10 (kept-product half verified; the "three Referee sections + 22 MCP tools" clauses of its own acceptance are unmeetable until J-09 lands)
- Regressed: none
- Anti-goal violations: none

**Reasoning:** This was a verify-only baseline with zero code written, and the checks were
really run instead of assumed. The four Referee web addresses all answer "not found", every
`referee_*.py` file is missing, `authorize_promotion` does not exist, and the Claude connector
still offers 20 tools, not 22 — so nine journeys are honestly recorded as failing. The old
product was walked in a real browser and works: the live tape page shows a converged tape state
with a populated quote and feature panel, the Structure page loads Apple's real price walls
including the 300.11–302.2 band, and the Desk page renders every shipped section with honest
"not computed yet" copy. The full test suite is 2,418 pass / 8 skip, exactly the era-open floor,
and the fingerprint prints `08e471b10130e1e2`. The guard over the owner's saved data reports all
11,274 files unchanged, so nothing was written where it should not be.

**Next-step recommendation:** Iteration 1 should build J-01 "Era transition made testable"
alone, at lean depth: the first backend slice that reports how much evidence the system already
holds (Playbook records, sessions, signals per setup and side; strategy datasets, splits and
trades; the honest statement that the tick-data gate is unmet), plus the two guard tests that
pin the documentation to the code. Every other Referee journey waits on that count.

## Iteration 1 — goal-referee-iter-1

**Date:** 2026-08-14T18:05:00Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: J-01 "The era transition stands — the evidence readiness count"
- Newly failing: none
- Partial: J-10 "The kept product stands" (kept-product half re-checked green by replay; its
  era-end clauses — three Referee sections and 22 tools for the Claude connector — still wait on
  J-09)
- Regressed: none
- Anti-goal violations: none

**Reasoning:** The new page-less backend answer at `/research/desk/referee/evidence` really
works. The saved picture of it shows an honest reply: how many Playbook records and trading days
exist, the count per setup and side, and the strategy side reporting zero data with a plain
sentence saying the tick-data gate is 150 short and one caveat sentence naming the still-forming
bar problem. I did not take the builder's word for the rest: I ran the 15 new tests myself (all
pass, with counts written out by hand in the test file), re-ran 156 older protection tests
(nothing broke, the Claude connector still offers 20 tools), and printed the settings fingerprint
myself — still `08e471b10130e1e2`. Only one old file changed, by seven added lines. The old
product was replayed step by step in a browser and held: the live tape page reaches "Buyer
Control", the Structure page loads Apple as of 22 June, and the Desk page opens its Playbook
panel. The guard over the owner's saved data reports all 11,274 files unchanged.

**Next-step recommendation:** Build J-02 "The evidence contract" next, alone, at lean depth: turn
the counts into one typed record per single observation, for both families (Playbook occurrences
and strategy trades), with the small rebuildable cache the goal describes. While that file is
open, also write the two extra `integrity_errors` fields into the written-down response shape,
because they are served today but not documented — the reviewer and the coherence check both
raised this. Approve building J-02 next; nothing needs a human unblock.

## Iteration 2 — goal-referee-iter-2

**Date:** 2026-08-14T19:20:00Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: J-02 "The evidence contract — two families, one observation shape"
- Newly failing: none
- Partial: J-10 "The kept product stands" (kept-product half re-verified green by golden
  replay with a genuinely fresh screenshot; its era-end clauses — three Referee sections and
  22 MCP tools — still wait on J-09)
- Regressed: none
- Anti-goal violations: none. One out-of-scope host action recorded as a NOTE, not a
  violation: the developer's pattern-based `pkill` also stopped an unrelated project's
  backend (trendora, port 8255); it is still stopped and needs a person to restart it.

**Reasoning:** The new work really does what it says. Every recorded trading signal and every
recorded test trade can now be read as one shared kind of record with the same fields, so the
later Referee parts have one foundation instead of two. I did not trust the report: I ran the
28 new-and-existing tests for this area myself, then ran the whole suite myself (2,454
collected, 2,446 passed, 8 skipped, none failed), and I read the new test file line by line to
check that its expected numbers are typed by hand rather than taken from the code being tested
— they are, including a full record-by-record comparison, a check that unmeasurable readings
are dropped instead of filled in with a made-up value, and a before-and-after fingerprint of
every saved file proving nothing was written. I also printed the settings pin and the detector
name from the live code myself: both match the saved picture of the web answer exactly, so
that picture belongs to this version of the code. The old product replayed green with a fresh
screenshot, and the guard over the owner's saved data reports all 11,274 files unchanged. Only
three files changed, all additions.

**Next-step recommendation:** Build J-03 "The statistics core" next, alone, at full depth —
this is the part that decides whether a pattern is real or noise, and a wrong sum there would
pass its own tests while quietly spoiling every later verdict. Carry three small leftovers
along with it rather than making an iteration of them: add tests for the "was this trading day
complete" helper (currently untested and a rough estimate that cannot see gaps in the price
data), add a test for the written-but-never-called cache path helper, and get an owner ruling
on one spec wording — the spec says every record carries a detector name, but a strategy trade
has none, so the code leaves it empty. Separately, outside this project: please restart
trendora's backend on port 8255 using the command recorded in the dev handoff.

## Iteration 3 — goal-referee-iter-3

**Date:** 2026-08-14T22:05:00Z
**Verdict:** ESCALATE
**Depth dispatched:** lean (the spec asked for full; the engine demoted it — telemetry
`depth_demoted`, `reason: budget-breach`)
**Journey deltas:**
- Newly passing: none
- Newly failing: none
- Partial: J-03 "The statistics core" (moved failing -> partial: the engine and its proof suite
  are real and verified, but one of its two p-value routes is provably over-confident);
  J-10 "The kept product stands" (kept half re-verified green by replay with a fresh screenshot;
  its era-end clauses still wait on J-09)
- Not re-tested this run: J-01 "The era transition stands" and J-02 "The evidence contract" —
  both marked DEFERRED-BUDGET in the results file, so both keep their recorded passing status
- Regressed: none
- Anti-goal violations: none

**Reasoning:** I did not take the report's word for anything. I re-ran the new proof suite myself
(77 tests green in 81 seconds, inside its own 120-second limit), re-ran the whole test suite
myself (2,503 collected, 2,495 passed, 8 skipped, nothing failed), printed the settings pin
myself (`08e471b10130e1e2`), counted the Claude connector's tools myself (still 20), and executed
all four tamper cases against the stored proof record — every one correctly refused, including a
record whose own "passed" flag still claimed success. All of that is real and good. Then I found
a fault nobody else did. The engine has two ways to compute the "how surprising is this?" number.
In the exact way — used when the number of possible re-shufflings is small — it works out one
group's total by subtraction while the figure it compares against was built by direct addition.
Those disagree in the last decimal place, so the real observed result narrowly fails its own
extremeness test and is not counted, and the answer comes out at half the smallest value that
method can legitimately produce. I reproduced this on 60,000 fresh cases: 1.72% of small
two-versus-two cases, 0.86% of one-versus-four, always on the most extreme results. No proof case
ever exercises that exact route, and the single test that does uses round numbers a computer
stores perfectly, so it cannot fail this way. Nothing is served to any user yet — the engine is
imported by nothing — so no one is being misled today, but four later journeys plan to use it for
their real numbers.

**Next-step recommendation:** Iteration 4 should fix the exact-mode number and prove the fix, at
full depth, before building anything on top. Three parts: add the second group up directly so the
observed result always counts (guaranteeing the answer can never fall below its own floor); add a
proof case that actually runs the exact route with awkward decimal values, plus a deliberately
broken variant that errs in the over-confident direction, since today's broken-on-purpose test can
only catch the over-cautious kind; and re-pin the stored proof record while bumping the engine's
version label, which is free today because nothing has been recorded yet. Two small leftovers ride
along: the unused draw helper and the untested single-anchor shortcut the reviewer flagged, plus a
check of two leads in older unchanged code that I could not settle in this pass (a date whose
newest record sits at a different detector version can silently blank that date's evidence; a
dataset with no time anchor becomes a 1969 date and lumps unrelated trades into one group). For a
person: approve "fix and prove the p-value floor in the statistics engine, at full depth, then
continue to matched nulls". Still outstanding for a human, from iteration 2: the unrelated trendora
backend on port 8255 has not been restarted.

## Iteration 4 — goal-referee-iter-4

**Date:** 2026-08-15T07:05:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: J-03 "The statistics core" (moved partial -> passing)
- Newly failing: none
- Partial: J-10 "The kept product stands" (kept half re-verified green by golden replay with a
  fresh screenshot; its era-end clauses — three Referee sections and 22 MCP tools — still wait
  on J-09)
- Not re-tested this run: J-01 "The era transition stands" and J-02 "The evidence contract" —
  both marked DEFERRED-BUDGET again in the results file, so both keep their recorded passing
  status; their shared source file DID change this run, so I checked that change directly
  instead of leaning on old evidence
- Regressed: none
- Anti-goal violations: none

**Reasoning:** The fault I found last iteration is really fixed, and I proved it myself rather
than reading it in a report. The exact example that used to come out at 1/7 now comes out at 2/7,
the lowest value the method can honestly produce. I wrote my own fresh test of 2,500 small cases —
one to three trading days, five different group shapes, all three directions, and deliberately
including the hard cases where the two groups sit far apart — and found zero bad answers, with 448
of them landing exactly on that lowest allowed value, which proves my test was actually looking in
the right place. I also ran the whole test suite myself (2,513 collected, 2,505 passed, 8 skipped,
none failed), printed the settings pin myself (08e471b10130e1e2), counted the Claude connector's
tools myself (still 20), ran the proof record live (it passes, and it correctly refuses both an
out-of-date copy and a doctored one), and confirmed the guard over the owner's saved data reports
all 11,274 files unchanged. The one FAIL line in the results file is not a break: it is a new
supplementary check that expected two Desk panels which only appear once a desk screen has been
recorded, and the test machine has none — the same honest empty state we recorded at the very
first iteration, on a run that changed no page code at all. Three smaller weaknesses stay open and
are written into the next step; none of them affects any number shown to anyone today, because
nothing reads this code yet.

**Next-step recommendation:** Build J-04 "Matched nulls" next, alone, at full depth — the part
that compares each recorded signal against fair comparison moments from the same stock, at the
same time of day, with the same trading time left, measured through the identical rail. Full depth
because this iteration also creates permanent name-tags for those comparison rules that later
registered questions will point at forever. Three riders travel with it instead of becoming their
own iteration: settle what "the smallest possible surprise value" means (the maths core still
advertises a value half as small as its exact method can reach — an owner ruling, since the
written specification reads both ways, and it is free to settle while nothing consumes it);
refuse unusable readings such as "not a number" or "infinity" at the door instead of silently
producing a meaningless answer; and tighten the one-against-many shortcut test, which currently
accepts anything inside a wide band. Two items for a person, neither blocking: this run finished
blocked because its own paperwork (`what-to-click.md`) still holds a "fill in" placeholder, so its
five changed files are still uncommitted and should be committed; and from iteration 2, the
unrelated trendora backend on port 8255 has still not been restarted.
