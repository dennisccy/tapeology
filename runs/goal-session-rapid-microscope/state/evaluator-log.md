# Goal Session rapid-microscope — Evaluator Log

Append-only chronological record. One entry per evaluated iteration.

## Iteration 0 — goal-rapid-microscope-iter-0

**Date:** 2026-08-16T23:11:10Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly failing: J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09 (first recorded state — the
  era's features are not built yet)
- Partial: J-01 (transition documents + era-open baseline verified; readiness endpoint and
  Desk panel absent), J-10 (kept product verified green; trap suite absent)
- Regressed: none
- Anti-goal violations: none

**Reasoning:** This was a verify-only baseline, so nothing was built and nothing could
regress. I did not take the reports on trust: I re-ran the settings fingerprint (reads
`08e471b10130e1e2`), re-computed all six referee module hashes (all match the recorded
listing), parsed the MCP tool list myself (22 names, not the target 26), and searched the
codebase for every new module the era needs (none exist). The three page screenshots show the
Cockpit, Structure and Desk pages loading their shipped content, and the Desk screenshot shows
no microscope panels — which is exactly the honest starting picture. The reviewer passed the
iteration and the store-scope guard shows the operator's real data store was not touched.

**Next-step recommendation:** Build J-01 "The era transition stands" alone: the corpus-truth
module, its read-only endpoint, and the "Microscope Readiness" panel at the bottom of the Desk
page. Everything else in this era depends on that surface existing. Keep the next iteration
lean; switch to full depth when the leakage rails of J-02 "The micro observer" land.

## Iteration 1 — goal-rapid-microscope-iter-1

**Date:** 2026-08-17T02:20:00Z
**Verdict:** ESCALATE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly failing: none
- Regressed: none
- Partial (unchanged status, changed content): J-01 (endpoint half now genuinely met on the real
  corpus; browser half blocked by an empty QA rig), J-10 (sentinel half re-verified green and
  deeper than iter-0; trap suite still absent)
- Anti-goal violations: none

**Reasoning:** I did not take the handoff on trust. I ran the readiness code myself against the
real tick files and read 12 symbol-days, 18 shards, 3.0089 session-equivalents, every shard
marked exploratory and hand-assigned, and all three studies below their floor — so the served
numbers are real. The browser evidence tells a different story only because the test rig the
project forces browser checks onto points at an empty data folder: the new panel on the Desk page
honestly showed zeros, and the eighteen-row table was never drawn even once. That is a hole in
the proof, not a broken feature, so J-01 stays half-done. I also re-ran the frozen-foundation
checks myself: the fingerprint still prints 08e471b10130e1e2, all six referee files are
byte-for-byte unchanged since era open, and 239 guard and golden-trace tests pass. The Cockpit,
Structure and Desk screenshots show every shipped surface still working, and the store guard
proves nothing was written into the owner's real data.

**Next-step recommendation:** Build the micro observer (J-02) next under the full pipeline — it
edits the two files this era promises to keep byte-identical and lands the first no-peeking
checks, so it deserves the auditor and closure steps. Alongside it, make the browser test rig
able to show tick data so the corpus panel can finally be photographed with real numbers, and
move the five misplaced checks in `apps/backend/tests/test_desk_ui_guards.py` back into their own
test.

## Iteration 2 — goal-rapid-microscope-iter-2

**Date:** 2026-08-17T07:20:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: J-02 "The micro observer" (built and verified), J-01 "The era transition stands"
  (its missing photograph finally taken; flagged `evidence_makeup` — see Reasoning)
- Newly failing: none
- Regressed: none
- Unchanged: J-03..J-09 failing (none of their modules landed — checked against this iteration's
  complete 12-file change list); J-10 partial
- Anti-goal violations: two critical ones were introduced AND fixed inside this run (a
  share-denominated liquidity number served without its unit gate; a half-finished measurement
  written down as finished across 36 rows of 18 files) — both proven fixed by whole-corpus sweeps;
  one minor open item (a timing stamp that is one quote too early, harmless today, needs an owner
  ruling before J-05)

**Reasoning:** I did not take the handoff on trust. I ran J-02's evidence myself: 117 tests across
the three new test files plus the frozen equivalence test, the 11 golden-trace tests with that file
byte-unmodified, all 18 snapshot files read straight off disk (3,815,933 rows, every one stamped
`unverified` units and the frozen fingerprint), and the listing function called against the real
store returning 18 identity-verified entries. For J-01 I opened the screenshot: the panel really
does render a real two-row tick corpus with matching checksums, coverage gaps, fallback fractions
and all three floors unmet — the empty table iteration 1 was stuck with is gone. What the picture
does NOT show is the real 12-symbol-day totals, because the mandated test rig can only be fed the
two small committed fixtures safely; those totals stay proven the way iteration 1 proved them,
against the owner's real store, with that code byte-unchanged since. That is a photograph problem,
not a product problem, so J-01 passes with a make-up capture owed. J-10 stays half-done: I re-ran
the frozen-foundation checks myself (fingerprint `08e471b10130e1e2`, all six referee file hashes
identical to iteration 0) and the cockpit and Referee panels photograph clean, but two sentinel
checks failed because the test rig lacks price bars for PG and has no computed playbook session —
both confirmed from the screenshots as honest empty states, with the same pages rendering real data
for AAPL in the same session. The trap suite is also only 4 of 22 built.

**Next-step recommendation:** Build the structure-and-flow join (J-03) next under the full pipeline
— it is unblocked now that the feature snapshots exist, and the audit step earned its keep this run
by catching two honesty defects the review and QA both missed. Carry four small passenger items:
get an owner ruling on the depletion timing question before J-05 publishes outcomes; fix the J-10
sentinel test plan so it stops failing for test-rig reasons (use AAPL on Structure, pick a session
with recorded signals, repair the replay script's volatile assertion); write down the two
undisclosed measurement gaps so J-05 does not inherit them silently; and re-photograph the
readiness panel whenever a later iteration seeds the rig with more tick data.

## Iteration 3 — goal-rapid-microscope-iter-3

**Date:** 2026-08-17T09:05:00Z
**Verdict:** ESCALATE
**Depth dispatched:** lean (the spec asked for full; the engine demoted it — telemetry reason
`budget-breach`, so the auditor step never ran)
**Journey deltas:**
- Newly passing: J-03 "Structure x flow — the join that never looks ahead"
- Newly failing: none
- Regressed: none
- Unchanged: J-01, J-02 passing (both re-verified, not carried); J-04..J-09 failing (none of their
  modules landed — checked against this iteration's complete 8-file change list); J-10 partial, but
  its browser sentinel is fully green for the first time
- Anti-goal violations: none critical; one NEW minor open item (the new corpus count silently drops
  a corrupt playbook record instead of failing closed) plus the still-open minor timing-stamp
  ruling carried from iteration 2

**Reasoning:** I did not take the handoff on trust. I ran J-03's evidence myself: 74 tests across
the join and feature files, and I read the no-lookahead tests to confirm they really probe the
stream (a sampled grid across the fixture plus a probe just before each later row) rather than
passing vacuously. I called the new corpus count against the owner's real tick data and got exactly
what the handoff claimed — 2 recorded chart signals fall inside recorded tick windows, both of one
setup type — and the same answer twice in a row, so it is real and repeatable, not a stored number.
I re-ran the whole backend suite (2,866 pass, 8 skip, 0 fail), re-computed the six referee file
hashes against the iteration-0 list, and confirmed the settings pin, the engine folder, and both
chart-pattern modules are byte-for-byte unchanged. For J-10 I opened the page photograph and read
it: the Desk page really does show four recorded signals for 2026-06-22 with real prices and times,
which is what iteration 2 could not get, and every kept panel renders. One evidence fault: this
iteration's Microscope Readiness photograph is a blank rectangle, so J-01 keeps its make-up flag and
still cites the older, good picture — the panel's own code was not touched, and the endpoint
photograph taken this run shows the same served values.

**Next-step recommendation:** Build J-04 "The Scout and the ledger" next under the full pipeline.
The engine downgraded this iteration to the quick pass for time reasons, so the independent auditor
— the only step in this session that has caught an honesty fault (two of them, in iteration 2) —
did not run, and the quick pass again left two small honesty gaps unfixed. J-04 is the journey that
must never lose the record of a failed trial, so it needs that auditor. Carry four passenger items:
report or refuse on a corrupt playbook record instead of silently skipping it; serve a "not counted
yet" state for wall touches instead of a bare zero; get the owner's ruling on the one-quote-early
timing stamp before any result is measured from it; and re-take the readiness photograph.

## Iteration 4 — goal-rapid-microscope-iter-4

**Date:** 2026-08-17T16:10:00Z
**Verdict:** ESCALATE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: J-04 "The Scout and the ledger — every trial on the record"
- Newly failing: none
- Regressed: none
- Unchanged: J-01, J-02, J-03 passing (all three RE-VERIFIED by me, not carried — every one of
  their modules or their served values changed or needed re-counting); J-05..J-09 failing (none of
  their modules exist on disk — checked file by file); J-10 partial, its trap half 4/22 → 8/22
- Anti-goal violations: two critical ones were introduced AND fixed inside this run (a ledger whose
  chopped-off tail was undetectable, so the count of trials could silently shrink; and a "how many
  variants tried" number that counted rows instead of distinct candidates, inflating it and jamming
  the operator button after 12 clicks) — both re-proved fixed by me on live code; a third critical
  fault (two horizon families screened against a null far too short, making results look better than
  they were) was also found and closed by refusing those horizons outright. One iteration-3 minor
  item is now CLOSED (a corrupt record is reported, and a bare zero became a typed "not enumerated");
  one minor item stays open — the one-quote-early timing stamp, which needs the owner, not a coder.

**Reasoning:** I did not take the handoffs on trust. I ran the Scout myself, from the command line,
against a throwaway copy of the test data: six trials, one permanent line each, every death reason
from the fixed list, and the served result carrying its evidence label, its best-of-many warning and
the cost-proxy sentence word for word. I then re-broke and re-checked each of the independent
checker's four fixes on the running code — a record edited on disk is now reported as tampered, a
chopped tail is caught at the exact missing row, and three identical re-runs grew the record from 6
to 18 lines while the "variants tried" count correctly stayed at 2. Against the owner's real data I
re-read the corpus truth (12 symbol-days, 18 shards, 3.0089 session-equivalents, all three floors
unmet) and the joinable count (2 signals, both of one setup), and I re-counted the 18 feature files
straight off disk at exactly 3,815,933 rows. The frozen parts are frozen: the settings fingerprint
prints `08e471b10130e1e2` and all six judge files hash identical to iteration 0. The one real
failure is not in the product: the browser check was skipped entirely, so the four already-working
journeys this iteration was told to re-check were never looked at, and the 13-step whole-product
safety walk did not run. Nothing this iteration changed can reach a screen — I checked the frontend
diff is empty and that none of the changed fields is read by the app — so I did not mark anything
down, but no one owned that gap and it must not repeat.

**Next-step recommendation:** Build J-05 "The walk-forward engine" next under the full pipeline —
it decides which results are allowed to count, so a hidden mistake there is the most expensive kind,
and the independent checker is the only step in this session that has ever caught that kind of
mistake. Carry five passenger items: actually run the browser check and the safety walk this time;
get two owner rulings together (the one-quote-early timing stamp, and whether the "variants tried"
bucket should also be counted per data set as the written spec says) before more data is recorded;
re-take the readiness photograph when the rig can show real tick data; clean up one unreadable kill
message and add the new numbers to the two page-guard lists before anything is put on screen; and
weigh a speed-focused pass, because the grid already takes minutes on today's 18 files.

## Iteration 5 — goal-rapid-microscope-iter-5

**Date:** 2026-08-17T20:30:00Z
**Verdict:** ESCALATE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: none
- Newly failing: none
- Regressed: none
- Changed: J-05 "The walk-forward engine" failing → partial (built and largely proven; two items
  the goal names word for word are not done)
- Unchanged: J-01, J-02, J-03, J-04 passing (all four RE-VERIFIED by me, not carried — two of
  their modules were edited this run); J-06..J-09 failing (their files are still not on disk —
  I checked each one); J-10 partial, its trap half 8/22 → 17/22
- Anti-goal violations: three critical ones were introduced AND fixed inside this run (a repeat
  run that counted the same evidence twice and turned an honest "not enough data" answer into a
  computed one; a "declare the question before you look at the answer" step that ran after the
  answer was read and was never written down; a guard for the "one door only" rule that could not
  see the two easiest ways around it) — all three re-proved fixed by me on live code. Two minor
  items are open: the register that protects the 12 old tick days is never filled in for them,
  and the honest "this data set is too small" refusal exists but nothing calls it.

**Reasoning:** I did not take the handoffs on trust. I re-ran the walk-forward job myself, from
the command line, against a throwaway copy of the real records: it reported 5 folds over 100
test sessions from 154 days of history, exactly what the goal asks for, and — proving the fix the
independent checker made — a second run re-used the existing 5 folds instead of writing them
again. I read the stored records myself: 3 of the 5 folds honestly say "not enough data" (17, 16
and 15 cases against a floor of 30), the overall answer honestly refuses at "2 < 3", every row is
stamped as exploratory evidence worth zero credit, and the tamper check is clean. I re-checked the
frozen parts: the settings fingerprint still prints 08e471b10130e1e2, all six judge files hash the
same as at era open, the price-engine and chart-pattern folders show an empty change list, and the
18 feature files still hold exactly 3,815,933 rows. I re-read the readiness page's numbers straight
from the server code after this run's rewiring and they are identical to before (12 symbol-days,
about 3.0 sessions, 18 shards, all three study floors unmet, 2 joinable signals). Two things are
genuinely not done: the register that must mark the 12 old tick days as "already seen" contains
only playbook days — I counted its 154 rows and every one is playbook — and the honest "this data
set is too small" refusal is written and tested but nothing in the running program ever calls it.
Both are named word for word in the goal, so J-05 is half-done, not done. The other real failure is
not in the product at all: the browser check was skipped for the second run in a row, so nothing
was photographed and the 13-step whole-product safety walk never ran. I found the cause: the script
that runs browser checks quits immediately whenever the plan says "Frontend Present: no", and the
safeguard meant to stop that is written but never read anywhere.

**Next-step recommendation:** Finish J-05 "The walk-forward engine" in one short pass, then move
on. Three things must happen. First, mark the next plan "Frontend Present: yes" so the browser
check actually runs — it names journeys that must still work on screen, and a plain instruction in
the test section has now failed twice. Second, fill the register with the 12 old tick days so they
can never be mistaken for fresh, unseen data; the written spec already says exactly this, so no
owner decision is needed. Third, make the running program actually use the honest "this data set
is too small" refusal instead of quietly returning an empty result. Keep the independent checker
in the loop — it is the only step in this session that has ever caught this class of mistake, and
it caught another one this run. Carry three passenger items: photograph the readiness panel at
last; write down whether a measurement is in percent or in basis points before any money-sized
floor is compared to it; and get the two owner decisions that are still waiting (the timing stamp
that is one quote too early, and how "variants tried" should be counted).

## Iteration 6 — goal-rapid-microscope-iter-6

**Date:** 2026-08-17T23:30:00Z
**Verdict:** ESCALATE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: none
- Newly failing: none
- Regressed: none
- Changed content (status unchanged): J-05 "The walk-forward engine" partial — both items iteration 5
  named are now closed and proven on the running program; one item the goal names word for word is
  still not reachable. J-10 "The kept product stands" partial — its whole-product safety walk is
  green for the first time this era; its trap half is still about 17 of 22. J-01 "The corpus truth on
  the record" keeps passing and its overdue-photograph flag is cleared.
- Unchanged: J-02, J-03, J-04 passing (their re-checks were cut for time — "deferred", not tested, so
  they keep their prior status; I spot-checked two of them against the real data myself); J-06..J-09
  failing (their files are still not on disk — this iteration's whole change list is two files)
- Anti-goal violations: no critical ones. Two minor items from iteration 5 are now CLOSED (the
  register that protects the 12 old tick days is filled in; the honest "this data set is too small"
  refusal is genuinely used by the running program). Two new minor items are OPEN, both about the
  same new register: a damaged recording would be left out of it silently and permanently, and once
  sealed recordings exist the register could mark one as already-seen forever. One older minor item
  is still open and still waiting on the owner (the timing stamp that is one quote too early).

**Reasoning:** I did not take the handoffs on trust. I ran the walk-forward job myself against a
throwaway copy of the real records: a too-small data set now stops with a clear refusal, exit code 1,
the words "0 < 105 -- refused (TR-15)" and no crash text at all; the register gained exactly 11 days
covering every one of the 12 old tick days with no hole, and a second run left it at 11. The real
job is unchanged at 5 folds over 100 test sessions. I re-read the readiness numbers straight from the
real data — 12 symbol-days, 18 recordings, about 3.0 sessions, all three study floors unmet, no
integrity errors — and I opened the new photograph: the panel really renders, legibly, with real
checksums, coverage gaps and fallback fractions. I re-ran the frozen checks myself (the settings
fingerprint prints 08e471b10130e1e2; all six judge files hash the same as at era open) and the guard
suite (203 tests). Two things are genuinely not done. The goal asks in plain words for a refusal
saying "11 < 105" when someone asks for folds on the tick data; I grepped the running program myself
and there is exactly one place folds are built, always over the playbook data, with no way to name a
different data set — so that sentence is only satisfied by a test over made-up dates. And the browser
check reported a real failure, which a broken piece of the pipeline's own tooling silently turned into
a "pass" that then flowed into the run record; the independent checker caught it and wrote the
correction into both files. That failure is not a product fault — the test's expected numbers can
never be produced by the small test rig the same test insists on using.

**Next-step recommendation:** Build the first step of J-06 "The recorder and the Vault" on its own,
under the full pipeline with the independent checker — the optional trade and quote detail fields
that must land before any new tape is recorded. It is the era's most dangerous change (every old
recording and fixture must still load exactly as before, and the price engine must still produce
byte-identical output), so that run must not be shortened for time. Carry five passengers: make a
tick-data fold request possible so the "11 < 105" refusal is real; report a damaged recording instead
of dropping it from the register; make the register mark days by a recorded identity before sealed
recordings exist; ask a framework-maintenance session to fix the tool that turns a browser "fail"
into a "pass"; and get the two owner answers still waiting (the one-quote-early timing stamp, and
whether the readiness photograph must show the real 12-day corpus when the test rig can only show a
two-day one).

## Iteration 7 — goal-rapid-microscope-iter-7

**Date:** 2026-08-18T01:30:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: J-05 "The walk-forward engine" (partial → passing; its last open clause is now met
  by a real command an operator can run)
- Newly failing: none
- Regressed: none
- Changed: J-06 "The recorder and the Vault" failing → partial (the first of its five steps landed,
  and that step is itself only half of what the goal names)
- Unchanged: J-01, J-02, J-03, J-04 passing — all four RE-CHECKED by me against the owner's real
  data, not carried; J-07, J-08, J-09 failing (their files are still not on disk — I looked for
  each one); J-10 partial, its whole-product safety walk green for the second run in a row
- Anti-goal violations: one critical fault was introduced AND fixed inside this run (the new
  storage fields quietly changed how a recording's identity is calculated, so the same tape could
  have been filed twice under two different labels — I broke it again myself and confirmed the fix
  holds). One NEW minor item is open (the new command writes a permanent shape record before it
  checks the size floor, which pins today's numbers forever). Three older minor items stay open,
  one of them still waiting on the owner.

**Reasoning:** I did not take any handoff on trust. I re-ran the new command myself against the
owner's real recordings and it printed exactly the sentence the goal asks for — "11 < 105" — and
stopped with an error code, while leaving the owner's real records untouched (I hashed the folder
before and after: identical). I then re-broke the dangerous fault the independent checker found:
saving the same tape a second time, now carrying the new extra details, under a different label is
correctly refused, and only one copy stays on file. All 18 real recordings still open with their
fingerprints matching, and none of them gained a single new field. The frozen parts are frozen: the
settings fingerprint prints 08e471b10130e1e2 and all six judge files hash exactly as they did at
the era's start. I ran the whole test suite myself: 3,045 pass, 8 skipped, 0 failures. On screen,
the browser check finally ran properly — eight real photographs, and I opened three of them: the
Cockpit shows a live moving chart and a real reading, the Structure page loads its full map, and the
Desk page shows every kept panel plus the corpus-truth panel with real numbers and honest
"floor not met" rows. One evidence fault, not a product fault: two of the reports name photographs
that are not on disk any more; the eight that matter do exist.

**Next-step recommendation:** Build the tape recorder (the second step of J-06 "The recorder and the
Vault") on its own, under the full pipeline with the independent checker — that checker is the only
step in this session that has ever caught this class of fault, and it caught another one this run.
Along with it, fix three small things that only start to hurt once new tape is recorded: the new
command should check the size floor before it writes its permanent shape record; a recording that
carries the new extra details must not break when the program tries to use it as a lookup key; and a
damaged recording must be reported instead of quietly skipped. Please also decide two things that
have been waiting for you: whether a timing stamp that is one quote too early should be corrected,
and whether the corpus-truth photograph must show your real 12-day corpus when the test rig can only
ever show a two-day one.

## Iteration 8 — goal-rapid-microscope-iter-8

**Date:** 2026-08-18T04:20:00Z
**Verdict:** ESCALATE
**Depth dispatched:** lean (the spec asked for full; the engine demoted it — telemetry reason
`budget-breach`, so the independent checker step never ran, exactly as in iteration 3)
**Journey deltas:**
- Newly passing: none
- Newly failing: none
- Regressed: none
- Changed content (status unchanged): J-06 "The recorder and the Vault" partial — its second of
  five steps landed and is proven; J-10 "The kept product stands" partial — one more trap armed
  (TR-19), sentinel green for the third run in a row
- Unchanged: J-01 passing (re-checked on screen and against your real data); J-02, J-03, J-04
  passing — their on-screen re-checks were CUT FOR TIME ("deferred", not tested, so they keep
  their status), but I re-read each one's served number against your real data myself; J-05
  passing — its code changed this round, so I re-ran its own acceptance command myself;
  J-07, J-08, J-09 failing (their files are still not on disk — I looked for each one)
- Anti-goal violations: no critical ones, introduced or open. Two older minor items are now
  CLOSED and I proved both on the running program (a below-floor request no longer freezes a
  permanent shape record; a damaged recording is reported instead of quietly dropped). One NEW
  minor item is open: the recorder does not write down the vendor rule text or the verification
  note beside the unit stamp the way the written spec asks — harmless today because no tape has
  been recorded, but permanent once it is. Two older minor items stay open, one waiting on you.

**Reasoning:** I did not take any report on trust. I ran the whole test suite myself: 3,092 pass,
8 skipped, 0 failures — the same number the reviewer got independently, and 47 more tests than
last round. I checked every number in the new recorder against the written spec line by line
(the 200-per-minute pace, the 900-second pieces, the 2025-11-03 vendor cutover, the published
split rule) — all verbatim, nothing invented. I re-ran the walk-forward command against your real
recordings with a throwaway record folder: it printed "11 < 105 -- refused (TR-15)", stopped with
an error code, left the throwaway folder completely empty (proving the fix), and your real folder
hashed identical before and after. I re-read your real store myself: 12 symbol-days, 18
recordings, 3.0089 sessions, no integrity errors, every shard still marked exploratory; 18
feature files still holding exactly 3,815,933 rows; the trial ledger's tamper check clean. The
frozen parts are frozen — the settings fingerprint prints 08e471b10130e1e2, all six judge files
hash exactly as at the era's start, the engine folder and every frozen guard test are untouched,
and an automatic guard confirms the run wrote nothing into your real data (11,275 files, unchanged
size and timestamp). On screen, two journeys replayed green and a full-page photograph shows every
kept panel plus the corpus-truth panel, with the three new sections correctly absent. The one real
failure is not in the product: the round was cut short twice for time — the independent checker
never ran, and four of the six journeys that had to be re-checked on screen were skipped. That
checker is the only step in this session that has ever caught a dishonesty fault, and this round's
change touched the very same kind of code where it caught one four rounds in a row.

**Next-step recommendation:** Build the sealed-evidence vault (step 3 of J-06 "The recorder and
the Vault") next, under the full pipeline with the independent checker. It is where a recording
gets sealed before anyone may look at it, and there is already a known hole waiting exactly there:
the register of what has been seen still marks everything as seen, with no filter for sealed
items — harmless today, serious the moment the vault exists. Carry four passengers: make the
recorder write down the vendor rule text and verification note beside the unit stamp before any
real tape is recorded; re-check the four journeys skipped this round and give each a replay script
so they stop being first to be cut; clear the two small test-hygiene notes the review raised; and
please answer the two decisions still waiting on you. One choice is yours about the machine
itself: rounds now run two to four times over their time budget and the machine responds by
cutting the checker and the on-screen re-checks — either raise the budget for the next round or
split the vault work into two smaller rounds, but do not let it run short-handed again.
