# Iteration 16 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round did what it set out to do. Three more safety tests are built and armed, the total is
now 27 of the 29 the plan asks for, and the two that are missing are next round's job by design.
One of the three was a real repair, not just a test: a liquidity reading used to be date-stamped
one quote too early, and that has been wrong since round 2. It is now fixed and shut.

The important news is about how the safety tests were checked. This round every lane was told to
prove its own tests can actually fail. The coder proved it, the reviewer proved it by breaking the
real program himself, and then the independent checker broke the program twelve different ways and
found three ways that nobody's test noticed. One of those three was inside the new repair's own
promise: the practice data happened to use the same number twice, so a test that was supposed to
prove "the size measurement is untouched" would have passed even if the size had been corrupted.
I did not take that on trust — I broke the program the same way myself, and I watched the whole
file stay green except for the one new test the checker had added to close the hole. That test is
real and it works.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing | reports/qa/goal-rapid-microscope-iter-16-evidence/J-01-verify.png (opened: readiness loaded with real corpus totals + Sealed Tranche block); UT-02-result.png (unavailable state) |
| J-02 The micro observer | passing | passing | reports/qa/goal-rapid-microscope-iter-16-evidence/J-02-verify.png (thin replay row); evaluator's own full suite 3246/3238/8/0/0; evaluator's own M2 mutation of `micro_observer.py` |
| J-03 Structure x flow | passing | passing | reports/qa/goal-rapid-microscope-iter-16-evidence/J-03-verify.png; `micro_join.py` byte-unchanged (evaluator's own `git status`) |
| J-04 The Scout and the ledger | passing | passing | reports/qa/goal-rapid-microscope-iter-16-evidence/J-04-verify.png; UT-03-result.png (opened: Scout Ledger expanded, chain verification ok, honest empty states) |
| J-05 The walk-forward engine | passing | passing | reports/qa/goal-rapid-microscope-iter-16-evidence/UT-06-result.png (opened: fold specs / sequences / run history all honest-empty); evaluator's own A1 fence mutation caught by the new aggregate test |
| J-06 The recorder and the Vault | partial | partial (not re-verified) | Excluded from the required set by the phase spec; `git diff --stat` on `vault.py`/`tick_recorder.py`/`micro_readiness.py` is EMPTY (evaluator's own check). `last_verified_iter` and `spec_hash` carried forward from iteration 14, not restamped |
| J-07 Graduation | passing | passing | reports/qa/goal-rapid-microscope-iter-16-evidence/J-07-verify.png (opened: the graduation endpoint's real honest-empty body at HTTP 200). Merged table's `DEFERRED-BUDGET` row is the golden-replay lane, which has no J-07 script by design — see Notes |
| J-08 The surface and MCP v6 | passing | passing | reports/qa/goal-rapid-microscope-iter-16-evidence/J-08-verify.png (opened); UT-01/UT-05 (11 sections, clean console); evaluator's own MCP tool count = 26 |
| J-09 The pilot studies | failing | failing (out of scope) | No pilot-study module under `app/research/`; no scout-ledger store dir on disk; "No candidates ledgered." on screen (UT-03) — all confirmed by the evaluator himself |
| J-10 The kept product stands | partial | partial (planned) | Trap count 27/29 by the evaluator's own label sweep of `apps/backend/tests`; sentinel green for the 11th run (UT-01, UT-03, UT-05, UT-06, UT-07, UT-08, UT-09 all opened) |

Deferred / not-run rows this iteration: `UT-J-07` carries `DEFERRED-BUDGET` in the merged results
table. It is scored as verified anyway — see the assumption-ledger entry. No other journey was
budget-deferred. `UT-04` (malformed Scout row degrades gracefully) is an optional P3 test that was
SKIPPED; it is not part of J-04's goal.md acceptance and does not downgrade anything.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | `iter-16/scan-report.md`: CLEAN, no findings on added lines. No config/env file in the 6-file diff (checked the file list myself). Vault secret path unchanged and never in the repo |
| Paid / external SaaS dependency | OK | scan-report reports no dependency findings; no manifest (`package.json`, `requirements*.txt`, `pyproject.toml`) appears in the diff at all |
| License change | OK | scan-report CLEAN; no LICENSE file or license field in the diff |
| Fabricated / substituted data | OK | The one production edit is a timestamp correction inside the observer. Every screenshot I opened shows honest empty or honestly-small fixture states, labelled as such ("No candidates ledgered.", "Backend unreachable — ... Nothing cached and nothing fabricated is shown in its place.") |
| No lookahead *(critical)* | OK — and one old violation CLOSED | TR-26's fix stamps `run["observed_through"] = ts`, the current event's own timestamp on a non-decreasing stream, so it can only move LATER. I read the fix in source. This CLOSES the iteration-2 minor item, open since round 2 and the oldest in the session |
| No value is served before it exists (TR-17) *(critical)* | OK | Same fix; the auditor's M5 mutation (`available_at = observed_through + 1.0`) fails 9 tests, so the opposite direction is guarded too |
| The accessor is the only data door *(critical)* | OK, with a documentation defect | Import-ban tests unchanged and green; no new direct `open()`/`sqlite3` on snapshot or vault data. NEW MINOR ITEM: `micro_accessor.py:34-37` describes a walk-forward origin-fenced read path that does not exist — I confirmed by my own greps that zero production callers pass `origin=` |
| No exploratory read of a sealed shard *(critical)* | OK | No change to `vault.py` or readiness computation; production has zero sealed shards; UT-06 shows the Validation Vault section with ZERO buttons |
| One opaque research pool *(critical, spec r5)* | OK | No served surface changed shape. J-01-verify.png shows the "Sealed Tranche (Aggregate Only)" block with its opaque-pool sentence intact |
| Evidence classes never mix *(critical)* | OK — strengthened | TR-22 landed with a mutation-proof; the auditor confirmed `classify_evidence_class` is called at `walkforward.py:533`/`:596`, so unlike TR-3's fence this guards a LIVE path |
| Single source of truth *(critical)* | OK | `coherence.md` = COHERENCE-PASS; `quote_depletion` has one owner and is served by no endpoint or MCP tool |
| Deterministic and seeded *(critical)* | OK | No new randomness; every new test is fixture-based; my own suite run reproduced the same counts |
| Frozen foundations *(critical)* | OK | I checked all of it myself: fingerprint `08e471b10130e1e2` (live import), six `referee_*.py` + `micro_chain_ledger.py` SHA-256 identical to the iteration-0 baseline, `config.py` diff EMPTY, engine untouched |
| Read-only MCP *(critical)* | OK | `app/mcp/__init__.py` untouched; my own count = 26 tools |
| Immutable data *(critical)* | OK | No recorded dataset written. The suite legitimately rebuilds the DERIVED snapshot cache because the observer's source hash is part of the snapshot identity — designed behaviour, the append-only source files are never touched |
| No execution path / no profit claims / no advice *(critical)* | OK | No such code in the diff; the cockpit footer still reads "Descriptive only — not trading advice." (UT-08) |
| Host-guard caps *(critical)* | OK | No cap widened, no mask changed; nothing in the diff touches host-guard |
| Enhancement loop stays in its box *(critical)* | OK | `docs/goal.md` is not in `git status` — untouched. No `journeys-changed.md` was produced |
| Evidence honesty (T-10) | NEW MINOR ITEM | J-10's own golden replay script was rewritten, linted only, never executed, lost two data-bearing assertions, and is a 7th changed tracked file missing from `status.json` — so two lanes certified "exactly 6 files" wrongly. Verified by my own `git status` and `git diff` |

**Critical violations: none, introduced or open.** Open minor items: 5 (two closed this round, two
opened). Nothing waits on the owner.

Two mutations escaped every test and are recorded as GAPs, not violations. I checked both
directions myself in source. `is_exposed_before`'s `<` → `<=` is fail-safe (it classes MORE
evidence as diagnostic, and diagnostic evidence advances no gate, so it can never manufacture a
fake out-of-sample result). `finalize()`'s session-end stamp is correct in the shipped code; only
the test fixtures cannot tell it apart from the run's own stamp, because both fixtures end on a
quote. GAP is the right severity for both, and both ride round 17 as cheap single-fixture
additions.

## Next-Step Recommendation

Run round 17 as a FULL round with the independent checker, and build the last two safety tests:
TR-23 (nobody may claim a sealed result passed by simply saying so) and TR-24 (a killed sibling's
knowledge must not be laundered into a survivor's paperwork). That finishes the safety suite at 29
of 29 and is the whole of what remains in J-10 "The kept product stands" apart from the
repeat-run check.

Give that round one new rule, because it is this round's real lesson: it is not enough to show a
safety test can fail. The practice data itself must be able to tell the right answer apart from
the wrong one. This round's repair shipped with practice data that used the same number twice, so
the test would have passed even if the thing it promised to protect had been corrupted, and only
the independent checker found it. Every new test next round should use practice numbers that are
deliberately all different.

Carry four small jobs as passengers, never a round of their own:

1. Run J-10's stored replay script once — it was rewritten this round and never run, in the very
   round where J-10 is the subject. If it passes, put back the two checks that were deleted (they
   both passed one round ago and the text they look for is still on the page) and run it again. If
   they no longer pass, that is itself worth writing down, not dropping. Also make the harness list
   replay scripts among a round's changed files, so a script edit cannot again slip past a
   "we changed exactly six files" sign-off.
2. Fix the note at the top of `micro_accessor.py` that says the date-fence protects live reads. It
   does not — no part of the running program uses it yet. Either say so plainly or wire up the
   first real user of it.
3. Add the two cheap missing checks the independent checker named: one where a viewing is recorded
   at exactly the moment a question is registered, and one where the last thing in a session is a
   trade rather than a quote.
4. Do NOT record real tape, and do not start J-09 "The pilot studies" yet. Its one blocking safety
   test landed this round, so it is genuinely unblocked — round 18 is its natural home, once the
   safety suite is complete.

Nothing waits on your answer. One thing would help if you agree with it: this is the fifth round
running where I have had to write "escalate" rather than "continue" purely to stop the machine
cutting the independent checker for time. That checker has now caught something after both the
review and the quality check passed the same code eight separate times. If you tell the machine
that a request for the checker cannot be cut, I can go back to plain "continue" and the rounds
will be cheaper.

## Halt Justification (if halting)

Not halting. This verdict continues the loop; "escalate" only forces the next round to run the
full pipeline with the independent checker.

## Notes on two artifacts that disagree

**J-07 "Graduation".** The merged results table lists it as `DEFERRED-BUDGET`, which normally
means "not tested". That row comes from the automatic replay lane, which has no script for this
journey by design. The round's own plan assigns J-07 to the other lane, and that lane ran, passed,
and left a picture. I opened the picture myself: it is a real browser view of the graduation
address showing its honest empty answer. J-07 is verified. A later reader who only skims the
merged table would wrongly conclude it went unchecked. Recorded in the assumption ledger.

**Screenshots that are the same file.** J-02, J-03, J-04 and J-05's replay pictures are
byte-identical to one another, and UT-09's is identical to UT-10's. This is the known thin-replay
property first recorded in round 12: those replay scripts are one step long and land on the same
page. The pass comes from the script's own text assertions, not from the image. Not a new defect,
and not grounds to downgrade anything — but those images are not per-journey evidence and should
not be read as such.
