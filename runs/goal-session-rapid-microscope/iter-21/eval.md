# Iteration 21 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round built the first of the three pilot studies and it genuinely works. On screen the Scout
Ledger now shows a real study row that is tied to a wall on the price map, and the readiness panel
now prints a real "band touches" number instead of the old "not counted yet" placeholder. J-09
"The pilot studies" moves from failing to partial: one study of three has been run and its answer
recorded honestly ("not enough data"). Two studies are still only written down in the code, never
run. One promised piece — the second ledger line that records the walk-forward eligibility answer —
was genuinely missing when the browser lane looked, and only the independent checker found and
fixed it; nobody has yet re-opened the page to see the fixed version.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (re-verified) | reports/qa/goal-rapid-microscope-iter-21-evidence/J-01-verify.png |
| J-02 The micro observer | passing | passing (re-verified) | reports/qa/goal-rapid-microscope-iter-21-evidence/J-02-verify.png |
| J-03 Structure x flow | passing | passing (re-verified) | reports/qa/goal-rapid-microscope-iter-21-evidence/J-03-verify.png |
| J-04 The Scout and the ledger | passing | passing (re-verified; screenshot opened) | reports/qa/goal-rapid-microscope-iter-21-evidence/J-04-verify.png |
| J-05 The walk-forward engine | passing | passing (re-verified) | reports/qa/goal-rapid-microscope-iter-21-evidence/J-05-verify.png |
| J-06 The recorder and the Vault | partial | partial (unchanged; step 4 is a forbidden operator act) | reports/qa/goal-rapid-microscope-iter-21-evidence/J-06-verify.png |
| J-07 Graduation | passing | passing — **NOT tested** (`DEFERRED-BUDGET` row); keeps its iter-20 stamp | reports/qa/goal-rapid-microscope-iter-20-evidence/J-07-graduation.png (durable: `micro_graduation.py` unchanged this round) |
| J-08 The surface and MCP v6 | passing | passing (re-verified) | reports/qa/goal-rapid-microscope-iter-21-evidence/J-08-verify.png |
| **J-09 The pilot studies** | **failing** | **partial** | reports/qa/goal-rapid-microscope-iter-21-evidence/UT-03-result.png (band_touch study row on screen); UT-02/UT-05/UT-06/UT-07/UT-09 PASS; **UT-04 FAIL** (reports/qa/goal-rapid-microscope-iter-21-evidence/UT-04-fail.png) |
| J-10 The kept product stands | passing | passing (re-verified; screenshot opened) | reports/qa/goal-rapid-microscope-iter-21-evidence/J-10-verify.png + UT-08 full 17-step hand replay |

**J-09 gap detail (why partial, not passing).** Its acceptance asks for three ledgered study
families, each with a served screen and a recorded decision. Only ONE study (delta divergence at
level tests) was run: `divergence_at_level_bearish__band_touch__trades_20`, candidate
`cand-a5f1eff2380a1674`, decision `killed_insufficient_n` — I read that row off the screenshot
myself. Studies 1 and 3 are written in the code but never run (UT-05 confirmed no row for either).
The walk-forward eligibility line was absent (UT-04) and is now code-fixed but not seen on screen.
The iteration spec itself set the bar at "at least partial".

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-21/scan-report.md`: CLEAN, no findings on added lines. No new config/env file in the 12-file diff. |
| Paid / external SaaS | OK | No manifest touched — `package.json`, `requirements.txt`, `pyproject.toml` are all absent from `iter-diff.md`'s file list. |
| License change | OK | No LICENSE file or license field in the diff; scan-report CLEAN. |
| Fabricated / substituted data | OK | The one screen ran on a committed hermetic fixture; the enumerator returns an honest empty list when no band map resolves; the decision recorded is a real kill. Auditor re-ran the screen independently (`killed_null`, effect −0.012 bps, p 0.218). |
| Frozen foundations (fingerprint, referee modules, engine) | OK | I checked by hand: `Config().config_fingerprint()` prints `08e471b10130e1e2`; `git status` shows no `referee_*.py` modified (six SHAs listed in my log); no engine file in the diff. |
| Single source of truth | OK (advisory) | `iter-21/coherence.md` = **COHERENCE-WARN**, no blocking violation. One advisory: the walk-forward floor-check row is served through the Scout endpoint, while the spec's text names the walk-forward endpoint — a documentation correction, one serving path only. |
| Deterministic and seeded | OK | No new randomness in the diff; the auditor re-ran the screen and reproduced the same numbers; my own full suite reproduced the auditor's count exactly. |
| Read-only MCP | OK | `EXPECTED_TOOLS` still 26 (I counted it); no MCP file in the diff. |
| Immutable data / append-only ledgers | OK | Rows are appended, never edited; the only ledger written this round is the throwaway QA rig's. |
| No exploratory read of a sealed shard | OK | The new counter sums over the already withheld-excluded record list; TC-9's sealed case asserts count 0 **and** `withheld_excluded` 1. |
| Evidence classes never mix | OK | The screen is labelled `historical_exposed_diagnostic`; the eligibility check refuses because there are zero out-of-sample sessions. |
| No new threshold chosen from outcomes | OK | Zero new constants; auditor confirmed and the fingerprint is unchanged. |
| The denominator never shrinks | OK | Every trial is a ledger row with a closed-vocabulary decision; nothing deleted. |
| The accessor is the only data door | OK | The new counter reads through the existing sanctioned store reader; TR-3 green in my own full-suite run. |
| No claim beyond what L1 supports | OK | The fallback / unknown disclosures are carried on the new row (visible in the UT-03 notes column). |
| 12 legacy symbol-days permanently exploratory | OK | Untouched; the readiness gate line still reads "unmet ... 147 short of the gate" (J-10 screenshot). |
| Host-guard caps | OK | Not touched. |
| **Shipped-surface behaviour (latency)** | **MINOR, open** | The readiness page-load call now costs a measured **22.3 s** of uncached parsing against the real store (auditor B2, measured twice). Values are correct; only speed is hurt, and only on the owner's own machine. Deliberately left unfixed because a careless cache would serve a stale wrong number. |
| **A promised flow that only a test can reach** | **MINOR, open** | The walk-forward eligibility line had zero real callers (UT-04 FAIL + auditor B1). Fixed in-round; I broke the fix myself and watched the test go red, then restored the file byte-identically. Still owed: one browser pass showing the fixed line on screen. |
| **A lane certifying what it did not check** | **MINOR, open** | The quality report ticked the eligibility item using the wrong row, said 1 of 18 datasets where 5 was measured, and returned PASS while the browser verdict for the same round was FAIL — and the closing gate still passed the round, because it never reads the browser verdict. |
| **Shared test rig changed mid-round** | **MINOR, open** | My own finding: this round's own browser tests wrote 7 rows into the throwaway rig's ledger, and the demo lane, which runs last, then failed its "nothing recorded yet" step and recorded it anyway. No damage across rounds — each run gets a fresh rig. |

No critical violation was introduced or is open.

## Next-Step Recommendation

Do the next round as a FULL round with the independent checker, and keep it SMALL. In order:

1. **Finish J-09 "The pilot studies."** Run the two remaining studies — range-wall failed
   aggression and capitulation exhaustion — on the same committed practice data the first one used,
   through to a recorded answer each. "Not enough evidence" is a perfectly good answer. This is the
   only thing standing between the project and nine of ten journeys green.
2. **Re-open the page and photograph the walk-forward eligibility line.** The independent checker
   built it this round and is the only lane that has checked its own work. No screenshot means no
   pass.
3. **Re-check J-07 "Graduation."** The clock cut it this round, so nobody tested it. Nothing it
   depends on changed, so its earlier proof still stands — but the finish line stays blocked until
   somebody looks at it again.
4. **Fix the 22-second wait on the Desk readiness panel** by remembering each dataset's wall-touch
   count on disk, keyed to that dataset's own checksum and its wall map, and only remembering an
   answer when a map really resolved — never remembering "none". If the clock bites, drop THIS item,
   not items 2 and 3.

Named as deliberately NOT this round's work, so nobody quietly does it: making the divergence
search fast enough for the real tape (it is far too slow today, so a real-tape run still cannot
finish); turning an unknown grid name into a polite error instead of a server crash; and the
one-line blueprint note correcting which address serves the eligibility row.

Two things still wait only on you, unchanged: whether to authorise recording real market tape for
J-06 "The recorder and the Vault", and where a candidate's pre-registered money floor and evidence
label should come from. Nothing in items 1-4 needs your answer.

In one sentence: approve one more careful round with the independent checker to finish the two
remaining pilot studies and take the two photographs that are still owed.

## Halt Justification (if halting)

Not halting.
