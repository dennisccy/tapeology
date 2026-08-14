# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

This was the opening check of Era 6 "The Referee". No code was written, on purpose. The
pipeline tried all ten journeys against the product as it stands today and wrote down what it
found. Nine journeys (J-01 "Era transition made testable" through J-09 "Referee on the Desk
page") fail, because none of the Referee machinery exists yet — the four new web addresses all
answer "not found", none of the new backend files exist, and the Desk page screenshot shows no
Referee section anywhere. The tenth journey, J-10 "The kept product stands", is the sentinel:
the old product was walked in a real browser and works — the live tape page, the Structure page
loading Apple's real price walls, and the Desk page with its shipped sections. J-10 is recorded
as partly met, not fully met, because its own wording also asks for the three Referee sections
and a 22-tool Claude connector, and today there are zero sections and 20 tools. Nothing was
broken and nothing was faked: the guard that watches the owner's saved data reports all 11,274
files untouched.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Era transition / evidence readiness | (none — first iteration) | failing | `reports/phase-goal-referee-iter-0-ui-test-results.md` UT-J-01 (`GET /research/desk/referee/evidence` → 404; `referee_evidence.py` and `test_referee_guards.py` absent) |
| J-02 Evidence contract, two families | (none) | failing | same results file, UT-J-02 (`referee_evidence.py` absent — no adapters, no goldens) |
| J-03 Statistics core + oracles | (none) | failing | same results file, UT-J-03 (`referee_stats.py`, `tests/test_referee_oracles.py` absent) |
| J-04 Matched nulls | (none) | failing | same results file, UT-J-04 (`GET /research/desk/referee/nulls` → 404) |
| J-05 Registry with immutable boundary | (none) | failing | same results file, UT-J-05 (`GET .../registry` → 404; `POST .../registry/hypotheses` → 404) |
| J-06 Estimands + adjudication | (none) | failing | same results file, UT-J-06 (`GET .../adjudications` → 404) |
| J-07 Starter family shortlist + registration | (none) | failing | `reports/qa/goal-referee-iter-0-evidence/J-07-fail.png` — /desk renders only shipped sections; zero shortlist/registration UI; zero "referee" text |
| J-08 Strategy family + promotion interlock | (none) | failing | same results file, UT-J-08 (`authorize_promotion` absent under `app/research/`; `pnl_scan._promote` runs the pre-Era-6 gate only; `pytest -k promot` → 7 passed) |
| J-09 Referee sections + 22 MCP tools | (none) | failing | `reports/qa/goal-referee-iter-0-evidence/J-09-fail.png`; `EXPECTED_TOOLS` = 20 entries, live MCP manifest = same 20 |
| J-10 Kept product stands (sentinel) | (none) | partial | `reports/qa/goal-referee-iter-0-evidence/J-10-result.png` (cockpit: Buyer Control 0.914, quote/features/trades/observations populated), `J-10-structure.png` (AAPL as-of 2026-06-22, map basis 2026-06-18, resistance 300.11–302.2 Class A "round number"), `J-07-fail.png` (desk shell + shipped sections), suite 2,418 pass / 8 skip, fingerprint `08e471b10130e1e2`, nav = 3 routes |

**J-10 gap (why `partial`, not `passing`):** its acceptance also requires the three Referee
`/desk` sections to render and "MCP = exactly 22 tools". The same browser pass proves zero
sections and 20 tools. Those clauses can only close when J-09 lands; the kept-product
regression half is fully verified and must not be re-done.

**Evidence-lane notes (not defects):** (a) the browser lane deliberately skipped the T-9 clean
`.next` rebuild, disclosed in the results file — zero frontend files changed this iteration, so
there was no stale-build risk; T-9 becomes mandatory again the first time frontend code
changes. (b) The QA rig is the fixture-scoped backend (`project-extensions/store-scope/`), so
`/desk` honestly shows "Desk screen not computed yet." and near-empty Playbook Evidence cells —
that is the rig's own seeded data, not the operator's 385-record store, and not a regression.
(c) `coherence.md` was not produced for this iteration; with a zero-line product diff there was
nothing structural to audit, but its absence is recorded because a missing coherence verdict can
never support GOAL_ACHIEVED later.

## Anti-goal Check

Source: `runs/goal-session-referee/iter-0/scan-report.md` (CLEAN), `iter-0/iter-diff.md`
(5 files, all Markdown docs from the era-opening commit `e875972`), `git diff --stat HEAD~1..HEAD`
(zero files under `apps/`), and `reports/qa/goal-referee-iter-0-store-scope-guard.md`.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | scan-report CLEAN on added lines; diff contains only `docs/*.md`; no env/config file touched |
| Paid or external SaaS | OK | no manifest in the diff (`requirements.txt`, `package.json` untouched); no new dependency; scipy still absent |
| License changes | OK | no LICENSE file or license field in the diff |
| Fabricated / substituted data | OK | no code changed; every journey verdict is backed by a 404, a file-absence check, or a screenshot; the failing verdicts were recorded as failures, not papered over |
| 1. No execution path | OK | zero `apps/` diff; `test_no_execution_path.py` green inside the 2,418-pass suite |
| 2. No profit claims / advice | OK | zero copy change; `test_copy_discipline.py` green in the same suite |
| 3. Frozen foundations | OK | zero diff to `app/engine/`, `levels.py`, `tradability.py`, `setups.py`, `desk_playbook*.py`, `desk_forward.py`; fingerprint `08e471b10130e1e2` printed live; suite count equals the era-open floor exactly (2,418/8) |
| 4. Hold-out-only promotion | OK | `pnl_scan.py` untouched; champion pointer not moved (no promotion path ran; `-k promot` was a read-only fixture re-run) |
| 5. No lookahead | OK | no computation changed this iteration |
| 6. Single source of truth | OK | no new value or owner shipped; the 7 planned Era-6 rows are pre-registered in `runs/goal-session-referee/state/blueprint.md` verbatim from goal.md § Product Shape. Caveat: no `coherence.md` was produced this iteration |
| 7. Deterministic and seeded | OK | no random draw added |
| 8. Read-only MCP | OK | 20 tools, all GET proxies; the one live proxy call errored honestly rather than serving cached data (dev handoff, J-09) |
| 9. Immutable data | OK | store-scope guard CLEAN — 11,274 protected files identical in size and mtime before/after; `apps/backend/.data/playbook` last written 2026-08-13 |
| 10. Persistence stays scoped | OK | the only records written were the fixture rig's own seeded ones (14:58:20Z, other signatures, visible in `J-07-fail.png`); the operator's store took no write |
| Era-B/B2 carried rails | OK | fingerprint pin unmoved; no recorded playbook file rewritten (guard); suite keyless — the 8 skips are the standard `TAPEOLOGY_LIVE_INTEGRATION` opt-in gates, not credential failures |
| Referee-era rails (gauntlet, exploratory-forever, CI-inversion, BH denominator, no gate loosening, no feedback, certificate-locked promotion, attestation, no annualized) | OK | vacuously — no referee code, no verdict, no p-value, no certificate exists yet; recorded so iteration 1 inherits an explicit baseline |
| Enhancement loop stays in its box | OK | the goal-proposer did not run; the `AUTO:journeys` block in `docs/goal.md` is empty |
| Host-guard caps are law | OK | `project-extensions/host-guard/host-guard.env` present; no cap was widened or disabled; the only heavy path was the pre-existing hermetic test suite |

No violation found, critical or minor.

## Next-Step Recommendation

Build J-01 "Era transition made testable" next, on its own, at lean depth. In plain terms:
add the first small piece of backend work that answers the address
`GET /research/desk/referee/evidence` with an honest count of what evidence the system already
holds — how many Playbook records and sessions exist per setup and side, and how many strategy
datasets and trades exist — plus the written statement that the old tick-data gate is still
unmet, and the two guard tests that pin the documentation to the code. Nothing else in this era
can be built before that count exists, and it needs no browser work, no credentials, and no new
dependency. Do not re-do the baseline checks: the kept product, the test count, and the
fingerprint are already verified for this iteration. Please approve starting iteration 1 on
J-01 alone.
