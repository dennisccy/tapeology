## Iteration 0 — goal-observation-contract-iter-0

**Date:** 2026-09-02T23:20:00Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly failing: J-01, J-02, J-03, J-04, J-05 (first record — baseline)
- Newly partial: J-06 (first record — era-open documents and the three existing pages pass; the guard test file is absent)
- Regressed: none (no prior state — this is the first iteration of the session)
- Anti-goal violations: none (scan-report CLEAN; ledger totals 0/0/0/0)

**Reasoning:** This was a verify-only baseline and it did exactly that. I confirmed by hand that the
product folders have no changes, that the new machine-readable address `/tape/{ticker}/observation`
is not registered, that `apps/backend/app/observation_contract.py` is missing, and that no
`test_tape_observation_*.py` file exists. The screenshots show the plain "Not Found" body for the
five failing journeys, and the `/desk` page rendering unchanged for J-06. Backend test collection
re-run by me gives 3938 tests, matching the developer and reviewer figures, so the frozen foundation
is intact. Nothing regressed because nothing had passed before.

**Next-step recommendation:** Build the first block of the goal's binding order — the constants, the
builder, the two hash rules and `tests/test_tape_observation_projection.py` for J-01 "the artifact is
a pure projection with identity, provenance and integrity". Keep the web address for later, as the
goal's order requires. Next iteration should be lean, backend-only, with no visible change for users.

## Iteration 1 — goal-observation-contract-iter-1

**Date:** 2026-09-03T09:05:00Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly partial: J-01 (was failing — its test file now passes; its served web address is still missing)
- Newly failing: none
- Regressed: none
- Unchanged: J-02, J-03, J-04, J-05 failing (not worked on this round); J-06 partial (re-verified)
- Anti-goal violations: none (scan-report CLEAN; coherence COHERENCE-PASS with one advisory note; ledger totals 0/0/0/0)

**Reasoning:** I checked the work myself instead of trusting the reports. I re-ran the new test file
`apps/backend/tests/test_tape_observation_projection.py`: 38 checks, all pass, and the five
"counter-example" checks that prove the guards can really fail are all present. I also re-ran the
whole backend test set end to end: 3968 pass, 8 skipped, 0 fail, which is the old baseline plus
exactly the 38 new ones, and the configuration fingerprint still reads 08e471b10130e1e2. The
screenshots agree with the reports: the Cockpit really does show SIM-BIDABS live on the simulated
feed, and the address `/tape/SIM-BIDABS/observation` really does still answer "Not Found". That
missing address is half of what J-01 asks for, so J-01 moves to partial, not passing. The change set
is only three backend files and touches no page, no settings and no existing guard file.

**Next-step recommendation:** Build the time block next — J-02 "Market-event time, measured
availability and generation time are three distinct, honest instants, read atomically": the watch
manager's single atomic read of the settled pair, the three time fields, `availability_basis`, and
the new test file `apps/backend/tests/test_tape_observation_time.py`. Do not move the web address
earlier to make a journey look green; it is step 5 of the goal's required order. Next iteration
should be lean, backend only, with no visible change on screen.

## Iteration 2 — goal-observation-contract-iter-2

**Date:** 2026-09-03T11:05:00Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly partial: J-02 (was failing — its new test file passes; its served web address is still missing)
- Newly failing: none
- Regressed: none
- Unchanged: J-01 partial, J-06 partial (both re-checked this round); J-03, J-04, J-05 failing (not worked on)
- Anti-goal violations: none (scan-report CLEAN; coherence COHERENCE-PASS with one advisory note; ledger totals 0/0/0/0)

**Reasoning:** I checked the work myself rather than trusting the reports. My own run of the new file
`apps/backend/tests/test_tape_observation_time.py` gives 33 checks, all pass, with 9 "counter-example"
checks present that prove the rules can really fail. My own run of the whole backend test set gives
4001 pass, 8 skipped, 0 fail — the previous 3968 plus exactly the 33 new ones — and the settings
fingerprint still reads 08e471b10130e1e2. The screenshots agree with the report: the Cockpit shows
SIM-BIDABS live on the simulated feed, the page returns to the idle "No ticker watched" screen after
Stop, and the address `/tape/SIM-BIDABS/observation` still answers "Not Found". That missing address
is one half of what J-02 asks for, so J-02 moves to partial, not passing. The change set is one
backend file plus one new test file; no page, no settings, no guard file was touched.

**Next-step recommendation:** Build the next block — J-03 "Lifecycle, feed basis and session identity
stay honest": the real source and session description for each watch, honest lifecycle wording for all
seven statuses, and the new test file `apps/backend/tests/test_tape_observation_lifecycle_feed.py`.
While that work is open, also fix the one small problem the reviewer found: the settle helper stores
its record under the ticker name only, so an old, cancelled feed can briefly overwrite a freshly
restarted watch's record; it must be fixed before the web address is built at step 5. Do not move the
web address earlier. Next iteration should be lean, backend only, with no visible change on screen.

## Iteration 3 — goal-observation-contract-iter-3

**Date:** 2026-09-04T22:35:00Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly partial: J-03 "Lifecycle, feed basis and session identity stay honest" (was failing — its new
  test file passes; its served web address is still missing)
- Newly failing: none
- Regressed: none
- Unchanged: J-01, J-02, J-06 partial (all re-checked this round); J-04, J-05 failing (not worked on)
- Anti-goal violations: none (scan-report CLEAN; coherence COHERENCE-PASS with one advisory note;
  ledger totals 0 total / 0 resolved / 0 blocking / 0 non-blocking / 0 critical)

**Reasoning:** I checked the work myself instead of trusting the reports. My own run of the new file
`apps/backend/tests/test_tape_observation_lifecycle_feed.py` gives 30 checks, all pass, including the
five "counter-example" checks that prove the rules can really fail. My own run of the whole backend test
set finishes clean (4039 checks collected, 0 failures, 8 skipped) — the previous 4009 plus exactly the 30
new ones — the settings fingerprint still reads 08e471b10130e1e2, and the frontend type check reports 0
errors. I read the code myself: the address `/tape/{ticker}/observation` is still not registered, so the
"look at the served JSON" half of J-03 remains unmet and J-03 moves to partial, not passing. The
screenshot agrees with the report: the Cockpit shows SIM-BIDABS watched and live after the full
Watch → Pause → Resume → Stop → Watch cycle, with no new panel or control. The change set is two backend
files, one new test file, and one mechanical update to an older test file; no page, no settings, no
protected guard file was touched.

**Next-step recommendation:** Build the next block in the goal's required order — J-04 "Ingestion-path
equivalence under an identical valid event stream": feed one identical event stream through the replay
path and through the live path and prove both produce the same content identity while the source and
session details honestly differ. While that work is open, also fix two small things found this round:
one summary test only checks a hand-written list of seven words and never calls the real code, so it
proves nothing; and the new date-formatting helper in the web layer claims in a comment that it matches
the two older copies but nothing tests that claim. Do not build the web address early — it is step 5 of
the required order. Next iteration should be lean, backend only, with no visible change on screen.

## Iteration 4 — goal-observation-contract-iter-4

**Date:** 2026-09-04T22:58:00Z
**Verdict:** CONTINUE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: none
- Newly partial: J-04 "Ingestion-path equivalence under an identical valid event stream" (was
  failing — its new test file passes; its served web address is still missing)
- Newly failing: none
- Regressed: none
- Unchanged: J-01, J-02, J-03, J-06 partial (all re-checked this round); J-05 failing (not worked
  on — it is the next step of the required order)
- Anti-goal violations: none (scan-report CLEAN; coherence COHERENCE-PASS with the iter-3 ISO
  advisory now closed; ledger totals 0 total / 0 resolved / 0 blocking / 0 non-blocking / 0 critical)

**Reasoning:** I checked the work myself instead of trusting the reports. My own run of the new file
`apps/backend/tests/test_tape_observation_path_equivalence.py` gives 6 checks, all pass, and I read
the code to confirm the comparison reads real built records on both sides — not a hand-written pair
— and that the mutation check really makes it fail. My own run of the whole backend test set gives
4036 pass, 8 skipped, 0 fail (exit code 0), which is the previous 4039 collected plus 6 new minus the
1 empty check that was removed; the settings fingerprint still reads 08e471b10130e1e2 and my own
frontend type check reports 0 errors. I confirmed by hand that `apps/backend/app/observation_contract.py`
is byte-identical to its iteration-1 version, so the field grouping could not have been widened to
manufacture the match. The screenshot agrees with the report: the address
`/tape/SIM-BIDABS/observation` still answers "404". That missing address is one half of what J-04
asks for, so J-04 moves to partial, not passing. The change set is three test files; no page, no
settings, no production file, no protected guard file was touched.

**Next-step recommendation:** Build the web address — `GET /tape/{ticker}/observation` and
`tests/test_tape_observation_route.py` — which is J-05 "One read-only machine path" and step 5 of the
goal's required order. The address must read the watch manager's single atomic read and never touch
the engine directly. In the same round, rewrite the three saved replay scripts that still expect the
address to be missing (`journey-scripts/J-01.json` step 5, `J-03.json` step 11, `J-04.json` steps
8-9), or later automatic replays will report false failures. Also repair one empty check in the new
test file (`test_counterexample_field_partition_drift_is_detected` compares two hand-written lists
and never reads the real ones). Next iteration should run at full depth: it is the first round of
this era that changes a real served surface and makes five journeys checkable in the browser at once.

## Iteration 5 — goal-observation-contract-iter-5

**Date:** 2026-09-05T02:40:00Z
**Verdict:** ESCALATE
**Depth dispatched:** lean
**Journey deltas:**
- Newly passing: J-01 "The artifact is a pure projection", J-02 "Three honest instants",
  J-03 "Lifecycle, feed and session stay honest", J-05 "One read-only machine path"
- Newly failing: none
- Regressed: none
- Unchanged: J-04 "Same result from both ingestion paths" partial (its test half is green, but
  nobody opened the web address in a browser this round); J-06 "Guards and the sentinel" partial
  (carried over — its row says DEFERRED-BUDGET, so it was not tested at all this round)
- Anti-goal violations: none (scan-report CLEAN; coherence COHERENCE-PASS with no advisory notes;
  ledger totals 0 total / 0 resolved / 0 blocking / 0 non-blocking / 0 critical)

**Reasoning:** I checked the work myself instead of trusting the reports. My own run of the five
observation test files gives 114 checks, all pass, 0 failures — 8 new for the web address, plus the
38 + 33 + 29 + 6 already there. I read the new address's code myself: its only data call is the watch
manager's single atomic read, and the guard that proves this introspects the real engine class and
scans the real route text, with a counter-example that injects a real engine call and shows the scan
catches it. I ran the settings fingerprint myself: still 08e471b10130e1e2. I checked by hand that no
page file, no settings file and none of the nine protected guard files were touched. Most of all I
opened the pictures: three screenshots show the complete record served from the backend, and the
session name really does change after Stop and re-Watch, which is what J-03 asks for. Two things did
not get checked: nobody opened the address in a browser for J-04, and the whole-product re-check for
J-06 was cut for time. I also found that the automatic replay tool always opens web addresses on the
page server, which has no such address — proved by the fact that its three "failure" pictures are one
and the same error screen, byte for byte. That is a tooling fault, not a product fault, and the
pipeline was right to void those three failures.

**Next-step recommendation:** Build the last block — J-06 "Guards and the regression sentinel": the
missing guard test file and the whole-product re-check (all backend tests, the frontend compile check,
the fingerprint, and the three pages loading with nothing new on them). In the same round, have the
browser tester open the observation address itself for J-04 "Same result from both ingestion paths"
(watch, pause, reload twice, save a picture of each reload) and run J-02 "Three honest instants" as
its own steps. Also fix or write down the replay tool's wrong-address problem, because it will keep
reporting false failures. Next iteration must run at full depth: it is the final block and it carries
the whole-product re-check.

## Iteration 6 — goal-observation-contract-iter-6

**Date:** 2026-09-05T05:45:00Z
**Verdict:** CONTINUE
**Depth dispatched:** full
**Journey deltas:**
- Newly passing: J-04 "Same result from both ingestion paths", J-06 "Guards and the sentinel"
  (both were partial)
- Newly failing: none
- Regressed: none
- Re-verified and still passing: J-01 "The artifact is a pure projection", J-02 "Three honest
  instants" (this time through its own test row, which retires the iter-5 borrowed-evidence
  note), J-03 "Lifecycle, feed and session stay honest"
- Not tested this round: J-05 "One read-only machine path" — its row says DEFERRED-BUDGET, so it
  keeps its earlier passing status and its earlier verification date
- Anti-goal violations: none (scan-report CLEAN; coherence COHERENCE-PASS with two non-blocking
  advisory notes; ledger totals 0 total / 0 resolved / 0 blocking / 0 non-blocking / 0 critical)

**Reasoning:** I checked the work myself instead of trusting the reports. My own run of the new
guard file gives 23 checks, all pass, and I read the code: each of the five guards scans real
source, the real app folder, or a real served answer, and each failure-proof check spoils a copy
of the real file rather than a hand-written stand-in. My own run of the whole backend test set
finishes clean (4075 collected, exit code 0, 8 skipped), my own type check reports 0 errors, and
my own reading of the settings fingerprint is 08e471b10130e1e2. Most of all I opened the
pictures: two reloads of the paused machine address show the same content fingerprint with a
different generation time and a different evidence fingerprint, which is exactly what J-04 asks
for, and the three pages render with the same three-link menu and no new panel. One thing was
not done: J-05's own row was dropped because the round ran out of time. Its substance was
exercised under other row ids and I opened those pictures too, but the automatic safety check
refuses to sign off while any row says "deferred", so this cannot be the closing round.

**Next-step recommendation:** Run one short verification-only round that re-opens the machine
address in a browser for J-05 "One read-only machine path" — watch the simulated ticker, open
`/tape/SIM-BIDABS/observation`, save a picture, then open `/tape/ZZZZ/observation` and save the
"not being watched" picture. Nothing needs to be built. Re-run the other five rows as well if
time allows, so the results table has no skipped and no failed row. Use `evidence` depth so no
developer or reviewer runs and the round stays short.

## Iteration 7 — goal-observation-contract-iter-7

**Date:** 2026-09-05T07:05:00Z
**Verdict:** GOAL_ACHIEVED
**Depth dispatched:** evidence
**Journey deltas:**
- Newly passing: none — all six were already passing
- Newly failing: none
- Regressed: none
- Re-verified and still passing this round, each on its own row with fresh pictures:
  J-01 "The record is a plain copy with its own name and proof", J-02 "Three honest instants",
  J-03 "Lifecycle, feed and session stay honest", J-04 "Same result from both ingestion paths",
  J-05 "One read-only machine path" (this closes the round-6 skipped row),
  J-06 "Guards and the sentinel"
- Not tested this round: none — the results table has no skipped and no failed row
- Anti-goal violations: none (scan-report CLEAN; coherence COHERENCE-PASS; ledger 0 total /
  0 resolved / 0 blocking / 0 non-blocking / 0 critical)

**Reasoning:** I checked the work myself instead of trusting the reports. Nothing was built this
round, and I proved that: the change list for this round is empty, and the working folder holds no
edit to the program at all. I opened all nine pictures. The two new ones for J-05 "One read-only
machine path" show exactly what was owed: the machine address answers with the full record while the
simulated ticker is being watched, and the address for a ticker nobody watches answers "Ticker
'ZZZZ' is not being watched". I also re-read the other pictures and they hold: two reloads of the
paused record share one content fingerprint but carry different generation times and different
evidence fingerprints; the session name really does change after Stop and re-Watch; and the three
pages still show the same three-link menu with nothing new added. My own runs agree with the
reports: the six test files give 137 checks, all pass; the whole program's test set finishes clean
(4075 checks, exit code 0); the type check reports 0 errors; the settings fingerprint reads
08e471b10130e1e2. One row, J-01, was not driven in the browser by itself this round; the automatic
replay tool reported it failed, and I opened that picture too — it is the page server's own "page
not found" screen, which is the known tool fault, not a product fault. Every value J-01 asks for is
legible in the picture taken at the same address minutes earlier, and nothing in the program changed
between them. All four automatic safety checks now pass: journeys 6/6, results with no failed or
skipped row, coherence, and the anti-goal ledger.

**Next-step recommendation:** Halt — the goal is reached. Nothing more needs to be built or
verified for this chapter. The one loose end is not a product problem: the automatic replay tool
still opens machine addresses on the page server instead of the program server, so it will keep
reporting false failures for `/tape/*` until someone fixes the tool. Record that as a tool issue and
close the chapter.
