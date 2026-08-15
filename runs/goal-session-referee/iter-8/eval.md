# Iteration 8 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The Referee became something a person can use. On the Desk page there is now a "Referee Registry"
panel that lists the five candidate research questions, shows how much evidence each already has,
and lets the operator pick one and confirm it — which writes a permanent record whose start date the
server stamps itself. I opened the pictures and re-ran the checks myself rather than trusting the
reports: the registration really happened and survived a page reload, the whole test suite passes
(2,657 collected, 2,649 passed, 8 skipped, none failed), the settings pin is unchanged, and not one
of the owner's 11,274 saved files was touched. The deeper checking lane caught a real fault again —
a "days until ready" number that counted old evidence as progress and so read "0 days — ready now"
against the owner's real data — and it was fixed inside this same round.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (deferred, not re-tested) | `reports/phase-goal-referee-iter-8-ui-test-results.md:45` (DEFERRED-BUDGET); its source `referee_evidence.py` is absent from this iteration's 9-file diff |
| J-02 The evidence contract | passing | passing (deferred, not re-tested) | `reports/phase-goal-referee-iter-8-ui-test-results.md:46`; source unchanged |
| J-03 The statistics core | passing | passing (deferred, not re-tested) | `reports/phase-goal-referee-iter-8-ui-test-results.md:47`; `referee_stats.py` unchanged; its oracle suite green inside my own full-suite run |
| J-04 Matched nulls | passing | passing (deferred, not re-tested) | `reports/phase-goal-referee-iter-8-ui-test-results.md:48`; `referee_null.py` unchanged (imported from, never edited) |
| J-05 The registry | passing | passing (re-verified directly) | Its own source changed, so I checked it myself: `runs/goal-session-referee/iter-8/iter-diff.md` shows the write path/boundary derivation untouched; my isolated probe registered a hypothesis and the boundary was server-stamped `2026-08-15`; all J-05 tests green in my own run |
| J-06 Estimand engines + adjudication | passing | passing (re-verified directly) | `docs/handoffs/goal-referee-iter-8-audit.md` finding B1 + `apps/backend/tests/test_referee_adjudicate.py::test_iter8_rider1_*`, `::test_iter8_audit_b1_*`, `::test_iter8_rider2_*` — all five green in my own run |
| J-07 The starter family | failing | **passing** (capture-defect noted) | `reports/qa/goal-referee-iter-8-evidence/UT-02-result.png` (five candidates + rationale + readiness + honest empty state) and `UT-06-result.png` (real registration: row `S-1 / capitulation:long / 2026-08-15 / historical-exploration / active / 0 / 12 / 1 / 1 discovery (exploratory)`, S-1 button disabled "Registered"); persistence confirmed by results row UT-08 |
| J-08 Strategy family + promotion interlock | failing | failing | Not built this iteration (`docs/phases/goal-referee-iter-8.md` OUT OF SCOPE); `authorize_promotion` remains unwired |
| J-09 Referee on /desk + MCP v5 | failing | failing | Only the first of its three sections exists; I counted the connector's tools myself — still 20, not 22 |
| J-10 The kept product stands | partial | partial | `reports/qa/goal-referee-iter-8-evidence/J-10-verify.png` (fresh golden-replay pass) + results row UT-10 (every shipped Desk section still renders, new section strictly last); suite/pin/store-guard re-run by me. Era-end clauses still wait on J-09 |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `runs/goal-session-referee/iter-8/scan-report.md` CLEAN; the 9 changed files are existing source/test/page files — no new config or env file |
| Paid / external SaaS, new runtime dependency | OK | No manifest in the change set (`pyproject.toml`, `package.json` untouched); the new fold uses stdlib + already-imported project modules |
| License changes | OK | Scan-report CLEAN; no LICENSE or license-field diff |
| Fabricated / substituted data | OK | The operator's real referee store does not exist on disk (`apps/backend/.data` holds no `referee_*` directory) — no registration was faked; the store-scope guard reports all 11,274 protected files unchanged; every shortlist number is computed from the store at call time (verified in code and by my own probe) |
| No confirmatory claim outside the gauntlet | OK — strengthened | Rider 1 plus audit finding B1 now gate BOTH sites that can write a hypothesis's one permanent snapshot; each ships a can-fail companion test, all green in my own run. This closes the exact risk iteration 7's evaluator logged as possibly re-scorable |
| The historical atlas is exploratory forever | VIOLATED (minor) — fixed in-iteration | `docs/handoffs/goal-referee-iter-8-audit.md` B2: `projected_days_to_target` subtracted pre-boundary history from a post-boundary target, serving "0 days — ready now" for all three estimand-A candidates on the real corpus. Fixed inside this iteration; I reproduced old (517) and new (564) values myself on an isolated copy of the rig corpus. Scored minor: pure read-side, nothing persisted, never on the operator's screen. The `discovery` block itself is correctly labeled and never feeds `accrual` (my probe: discovery 3, accrual 0) |
| Never shrink the BH denominator | OK | The registration payload sends `family_candidate_hypothesis_ids` read live off the fetched shortlist (all five) — `apps/frontend/app/desk/page.tsx` `handleRegisterRefereeCandidate` |
| No gate loosens mid-era | OK | `target_sessions`/`min_occurrences` come from the unchanged `REFEREE_MIN_SESSIONS`/`REFEREE_MIN_OCCURRENCES` constants; neither is in the diff |
| The Referee never feeds back | OK | Zero diff to `desk_forward.py`, `desk_playbook*.py`, `levels.py`, `tradability.py`; the new code only reads them |
| Frozen foundations / no fingerprint movement | OK | I printed `Config().config_fingerprint()` myself: `08e471b10130e1e2`; `app/config.py` not in the diff; zero new Config fields |
| Read-only MCP | OK | I counted `EXPECTED_TOOLS` myself: 20, unchanged (J-09 owns the growth to 22) |
| Immutable data / no rewriting of history | OK | Store-scope guard CLEAN; the new folds write nothing at all |
| No profit claims / no advice / no annualized metrics | OK | New copy is descriptive ("Registering one writes a permanent, boundary-stamped hypothesis"); the copy-discipline and annualization guards are green in my own full-suite run |
| Single source of truth | WARN (minor) | `runs/goal-session-referee/iter-8/coherence.md` is COHERENCE-WARN, not FAIL. Two open items: the family error-rate `0.1` lives only as a browser literal (audit F1), and — my own finding — the `discovery` count ignores the wall condition the same candidate's shortlist row applies (probe: shortlist 0 vs discovery 3) and carries no "estimate" marker although its `accrual` neighbour does |
| Host-guard caps | OK | No change to host-guard configuration in the diff |
| Enhancement loop stays in its box | OK | `docs/goal.md` is not in the change set; all ten journey spec hashes match the recorded ones, so no goal text moved |

## Next-Step Recommendation

Build J-08 "The strategy family and the promotion interlock" next, on its own, at full depth. This
is the rule that stops any new trading strategy from being crowned unless a valid, strategy-specific
certificate from this era's judging machinery exists, and it must refuse with no way around it. Full
depth is not a preference here: the round rewrites existing tests that today allow promotion, and
the deeper checking lane has now found a real fault in all three of the rounds it actually ran. The
time trimmer cut rounds 6 and 7 back to the short pipeline; it must not do that again here.

Four small items should ride inside that round rather than becoming their own: (1) make the
"discovery" count on a registered row use the same wall condition its shortlist row uses, or mark it
plainly as an estimate, so the same page stops showing two different numbers for one thing; (2) get
an owner ruling on the missing short side of the wall-based candidate — the written specification
asks for it "per side" and only the long side was built, with no drop recorded; (3) move the
family's error-rate setting (0.1) out of the browser file into the back end beside the other
statistical constants; (4) extend the on-screen number guard to the two accrual figures now shown.

Two things for a person. First, this round finished blocked on a paperwork check that misread the
words "backend-only" inside a sentence describing the new visible screen, so its nine changed files
are still uncommitted — please commit them and loosen that check's wording rule. Second, still open
since round 2 and outside this project: the unrelated trendora backend on port 8255 has not been
restarted. Approve building J-08 next at full depth; nothing needs a human unblock to start.
