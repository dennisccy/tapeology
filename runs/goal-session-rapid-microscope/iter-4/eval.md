# Iteration 4 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The Scout and its trial ledger were built and they work. I ran them myself, end to end, on a
throwaway copy of the test data: every candidate that was tried got one permanent line in the
record, with an honest reason for its death, and the count of "how many things we tried" behaves
correctly. The independent checker found four real integrity faults that the code review and the
test pass both missed, fixed all four, and I re-proved each fix against the running code. One
thing did not happen: the browser check was skipped completely, so nobody looked at the four
already-working parts of the product this iteration was told to re-check — including the
13-step whole-product safety walk. Nothing in this iteration's changes can reach the screen, so
I did not mark anything down for it, but the next run must actually do that check.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (re-verified by me; photo make-up still owed) | I called `build_readiness` on the real store: 12 symbol-days, 18 shards all `exploratory`/`hand_assigned`, 3.0089 session-equivalents, all 3 floors `floor_unmet`. Panel photo carried: `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-02-result.png` |
| J-02 The micro observer | passing | passing (re-verified by me) | `micro_observer.py`/`micro_features.py`/`micro_snapshots.py` byte-unchanged (empty `git diff`); I re-counted the 18 snapshot files off disk = exactly 3,815,933 rows |
| J-03 Structure x flow | passing | passing (re-verified by me) | I called `joinable_corpus_counts` on the real stores: `playbook_signal_count` 2, `by_setup_id {"range_trade": 2}` unchanged; both iteration-3 honesty fixes now present in the served body; 142 tests passed in my own run |
| J-04 The Scout and the ledger | failing | **passing** (newly passing) | I ran `python -m app.research.scout` on a scoped fixture copy: 6 trials, one permanent row each, all decisions in the closed vocabulary; served screen carries `historical_exposed_diagnostic`, the best-of-N line and the cost-proxy sentence verbatim. Independent check: `docs/handoffs/goal-rapid-microscope-iter-4-audit.md` |
| J-05 The walk-forward engine | failing | failing | `micro_accessor.py` and `walkforward.py` both absent from disk |
| J-06 The recorder and the Vault | failing | failing | `tick_recorder.py` and `vault.py` both absent from disk |
| J-07 Graduation | failing | failing | `micro_graduation.py` absent from disk |
| J-08 The surface and MCP v6 | failing | failing | Tool list still 22 names (`desk_scout` absent); `/desk` page has none of the three new section headings |
| J-09 The pilot studies | failing | failing | No study family predeclared or ledgered; only a generic fixture grid ran |
| J-10 The kept product stands | partial | partial | Trap suite 4/22 -> 8/22; fingerprint `08e471b10130e1e2` and all 6 referee file hashes re-checked identical to iteration 0 by me; I re-ran the whole backend suite myself: **2949 passed, 8 skipped, 0 failed** (baseline 2,866). Safety walk NOT re-run this iteration — carried from `reports/qa/goal-rapid-microscope-iter-3-evidence/UT-J-10-result.png` |

**Evidence gap (recorded, not scored down):** `reports/phase-goal-rapid-microscope-iter-4-ui-test-results.md`
reads `Browser QA Verdict: SKIPPED` in four lines. The iteration spec (TC-20) asked for the
opposite split — re-check J-01/J-02/J-03 and run `journey-scripts/J-10.json` unmodified, with an
honest skip for J-04 only. No screenshots exist for this iteration at all. I verified myself that
no field this iteration changed can reach any screen (`git diff` over `apps/frontend` is empty; a
search of the app source for `band_touch_count`, `joinable_corpus` and `playbook_integrity_errors`
finds nothing), so the four journeys keep their status under the evidence-durability rule.

This overrules the independent checker's own recommendation ("do not score this iteration until
browser QA actually runs"). I overruled it deliberately and recorded why in the assumption ledger:
holding the whole iteration hostage to a re-photograph of unchanged screens would make evidence
capture the next iteration's goal, which this project forbids. Instead the gap becomes binding
next-iteration work and is the main reason this verdict is ESCALATE rather than CONTINUE.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-4/scan-report.md`: CLEAN, no findings on added lines; no config or env file in the 9-file change list |
| Paid / external SaaS, new dependency | OK | `pyproject.toml`, `package.json` untouched (empty diff); `scout.py` imports stdlib + numpy only |
| License changes | OK | No LICENSE file in the diff; scan-report reports no license findings |
| Fabricated / substituted data | OK — improved | The fixture grid's all-`killed_insufficient_n` outcome is honest. Two honesty fixes landed: a corrupt playbook record is now reported (`playbook_integrity_errors`) instead of silently dropped, and the wall-touch count is now a typed "not enumerated" state instead of a bare zero. Both confirmed by me in the real-store payload |
| Frozen foundations (critical) | OK | Verified by me: fingerprint `08e471b10130e1e2`; all 6 `referee_*.py` hashes byte-identical to the iteration-0 listing; empty diff over `app/engine/`, `desk_playbook.py`, `desk_playbook_context.py` |
| No lookahead (critical) | OPEN — minor, human-owned | The one-quote-early timing stamp in `micro_observer.py` is still unresolved. This iteration correctly refused to invent a reading and instead excluded every candidate that depends on it — I confirmed `quote_depletion` is absent from the feature table entirely |
| Single source of truth (critical) | OK | `iter-4/coherence.md`: COHERENCE-PASS; one owner module, one endpoint, no second implementation |
| Deterministic and seeded (critical) | OK | The command-line and endpoint paths call one shared function; re-running the same grid reproduced identical candidate ids and decisions in my own runs |
| Read-only MCP (critical) | OK | No MCP file in the diff; tool list still 22 |
| Immutable / append-only records (critical) | OK — fixed in-run | Three identical re-runs grew the ledger 6 -> 12 -> 18 rows with nothing deleted or suppressed |
| The denominator never shrinks (critical) | VIOLATED then FIXED in-run | Two faults the independent checker found: a chopped-off ledger tail was undetectable, and the "how many tried" count counted rows instead of distinct candidates. I re-proved both fixes on live code (`tail_truncated` now reported; count holds at 2 across three re-runs) |
| Screening null must not be anti-conservative (critical) | VIOLATED then FIXED in-run | Two horizon families were screened against a null block far shorter than their own label span. Now refused outright with a typed error rather than guessed at |
| Evidence classes never mix (critical) | OK | Every screen carries `historical_exposed_diagnostic`; `live_confirmatory` is defined but emitted nowhere |
| No profit claims / no advice (critical) | OK | The economic column is served beside — never merged into — the statistical result, with the cost-proxy sentence present word for word |
| Host-guard caps (critical) | OK | No change to host-guard configuration; heavy work ran under the engine's own confinement |

## Next-Step Recommendation

Build J-05 "The walk-forward engine" next, and run it as a full iteration so the independent
checker is in the loop again. This is the part of the era that decides which results are allowed to
count, so a hidden mistake there would be the most expensive one in the whole project — and in this
session the independent checker is the only step that has ever caught that kind of mistake (twice
in iteration 2, four more times here, all missed by review and testing).

Carry five small passenger items, none of which should become an iteration of its own:

1. **Actually run the browser check this time.** Re-check J-01, J-02, J-03 and run the 13-step
   whole-product safety walk `journey-scripts/J-10.json` unmodified, with screenshots saved, and an
   honest skip recorded only for the journeys that have no screen. Nobody ran it this time: the
   test pass said it belonged to the browser step, and the browser step skipped everything.
2. **Two owner rulings are now due together, before J-06 adds more recorded data.** (a) The
   one-quote-early timing stamp, still unresolved since iteration 2. (b) Whether the "how many
   variants tried" bucket should be counted per data-set as well as per feature family — the
   written specification says it should, the code does not, and changing it later would rewrite
   rows that are already permanently on the record.
3. **Re-take the corpus-readiness photograph** whenever the browser rig can show real tick data.
   The current picture is honest but shows the small test corpus, not the real 12 symbol-days.
4. **Before any of this is put on screen (J-08):** one kill message currently reads "approximately
   None bps", which is truthful but unreadable, and the new numbers still need to be added to the
   two guard lists that protect the page's wording and arithmetic.
5. **Watch the running time.** The full grid already takes minutes on today's 18 files; the era's
   later steps grow that corpus a lot. Weigh a speed-focused pass before J-06 lands.

One sentence for the owner: approve building the walk-forward engine next as a full-depth run, and
please answer the two questions in item 2 — a timing question and a counting question — because
both get harder to change once more data is recorded.

## Halt Justification (if halting)

Not halting. ESCALATE keeps the loop running; it only forces the next iteration to use the full
pipeline instead of the quick one. The reason is that the evidence step failed to do its job this
time (the browser check produced nothing at all, with no agent owning the gap), and the next
journey is the one where a silent mistake would be worst. In this session a plain depth
*recommendation* has already been overruled once for time reasons — in iteration 3 — and the
independent checker that got skipped then was exactly the step that caught four real faults when it
finally ran here. ESCALATE is the only signal that reliably survives that budget decision.
