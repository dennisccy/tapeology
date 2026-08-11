# Iteration 7 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The back-scan works. I opened the picture myself: the Desk page now has a Backscan panel, and after
typing a date range it says "3 dates planned · 3 missing at the current signature", then the run
table shows one finished run reading "0 reused · 3 recorded · 0 refused · 0 failed". So J-07 "The
back-scan" is genuinely done. I also checked the thing that went wrong last time: no test and no
browser check wrote anything into the owner's own records this run (I listed every file in his
store and nothing was touched). I am asking for a deep pass next, with the auditor, for three
reasons: this iteration was planned as a deep pass and ran as a fast one, so nobody with an
auditor's brief read the first piece of code that can write many records at once; the automatic
replay checks still run against the owner's real records instead of the test copy, and two of those
scripts press a compute button; and the next journey is the one that pools numbers into
distributions, which is exactly where honest-measurement mistakes hide.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The signal contract | passing | passing (replayed) | reports/qa/goal-playbook-iter-7-evidence/J-01-verify.png |
| J-02 Every signal measured | passing | passing (replayed) | reports/qa/goal-playbook-iter-7-evidence/J-02-verify.png |
| J-03 The Playbook lands on /desk | passing | passing (replayed; evaluator opened it) | reports/qa/goal-playbook-iter-7-evidence/J-03-verify.png |
| J-04 The continuation family | passing | passing (replayed) | reports/qa/goal-playbook-iter-7-evidence/J-04-verify.png |
| J-05 The climax family | passing | passing (replay FAIL overturned by the live lane; evaluator opened the live capture) | reports/qa/goal-playbook-iter-7-evidence/UT-J-05-result.png (replay row + reconciliation footer: reports/phase-goal-playbook-iter-7-regression-replay-results.md) |
| J-06 The range family | passing | passing — DEFERRED-BUDGET, not re-tested this iteration; keeps its prior status and its owed re-capture | reports/phase-goal-playbook-iter-7-ui-test-results.md (Deferred table) · prior: reports/qa/goal-playbook-iter-6-evidence/audit-J-06-postfix-double-top-geometry.png |
| **J-07 The back-scan** | **failing** | **passing** | reports/qa/goal-playbook-iter-7-evidence/UT-J-07-result.png (results row UT-J-07) |
| J-08 The evidence view | failing | failing (not targeted; evaluator confirmed no evidence module or route exists) | no `desk_playbook_evidence.py`; no `playbook/evidence` route in `apps/backend/app/research/desk_routes.py` |
| J-09 MCP contract v4 | failing | failing (not targeted; evaluator counted the tools) | `tests/test_mcp_server.py:1195` still asserts `len(TOOL_NAMES) == 18`; no `desk_playbook` entry in `apps/backend/app/mcp/__init__.py` |
| J-10 The kept product stands | partial | partial (browser walk replayed green; the "20 Claude tools" clause is still unmet at 18) | reports/qa/goal-playbook-iter-7-evidence/J-10-verify.png |

Evaluator's own re-verification (not taken from any write-up):

- Full backend suite run to completion: exit 0, 2138 tests collected, 8 skipped, zero failures —
  above the 2105 floor. `Config().config_fingerprint()` prints `08e471b10130e1e2`.
- Zero diff to every protected file: `desk_forward.py`, `desk_playbook.py`,
  `desk_playbook_detect.py`, `desk_playbook_features.py`, `desk_playbook_compute.py`, `config.py`,
  `levels.py`, `bars.py`, `setups.py`, `mcp/__init__.py` — none appears in `git status`.
- `apps/frontend/app/desk/page.tsx` is +399 / -0 lines (purely additive), so every shipped Desk
  section is byte-unchanged and prior evidence for J-01..J-06 stays valid (methodology A.6).
- The operator's own store was untouched:
  `find apps/backend/.data -newermt "2026-08-11 11:40" -type f` returns only sqlite WAL/SHM
  sidecars; the newest playbook record is still the iter-6 one from 10:59.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-7/scan-report.md`: CLEAN, no secret findings on added lines; no new config/env file in the 11-file diff. |
| Paid / external SaaS, new dependency | OK | No manifest in the diff (`package.json`, `requirements*.txt`, `pyproject.toml` all absent from the changed-file list); the new module imports only stdlib + existing app modules. |
| License changes | OK | No LICENSE or license-field file in the diff; scan-report reports no license findings. |
| Fabricated / substituted data | OK | The new synthetic member BSCAN and its two sessions are planted only under the scoped rig root by `scripts/seed_playbook_iter7_backscan_fixture.py`; evaluator confirmed nothing landed in `apps/backend/.data`. |
| No execution path, ever | OK | No broker, order, or trading concept in the new module or panel; `test_no_execution_path.py` green in the full run. |
| No profit claims / no advice; a signal is an observation | OK | New panel copy is descriptive ("Bulk-check and bulk-populate the playbook ledger…", "Backscan cancelled — dates already recorded before the cancel stay stored…"); `test_copy_discipline.py` green. |
| Frozen foundations / kept surfaces byte-identical | OK | page.tsx is additive-only (0 deleted lines); `desk_routes.py` is +119/-1 (the one deletion is the `fastapi` import line gaining `Query`); pin unchanged; J-10 walk green. |
| No lookahead | OK | No detector or measurement code changed; the back-scan only orchestrates the existing `run_playbook_and_record`. |
| Single source of truth | OK | `iter-7/coherence.md`: **COHERENCE-PASS**, no blocking violations, no advisory notes. |
| Deterministic and seeded | OK | No new randomness; run ids use uuid4 for file naming only, never for any recorded measurement. |
| Read-only MCP | OK | `mcp/__init__.py` unchanged; 12 static paths / 18 tools, evaluator-verified. |
| Immutable data / no record rewritten, pruned, superseded | OK | `BackscanRunStore.record` only ever writes a new file and re-rolls the id on collision; the store exposes no update or delete method; playbook records are written through the unchanged `PlaybookStore`. |
| Persistence stays scoped | **MINOR, OPEN (carried from iter-6, narrowed)** | Nothing was written to the real store this iteration (evaluator-verified). Remaining hole: the deterministic replay lane ran at 12:40 against the ambient, unscoped `:8301` backend, and `J-01.json` / `J-03.json` click the Run Playbook trigger (both on non-session dates, so the honest refusal fired). The live browser lane did detect and replace that unscoped backend before its own run. |
| No threshold outside the spec / no sweep | OK | Zero diff to `desk_playbook_detect.py`; the only detector-related change is the new short-side test (TC-12). No loop over thresholds anywhere in the new module. |
| The spec is canonical (owner rulings) | **MINOR, OPEN ×2 (carried, untouched by design)** | The §3.7 degenerate-trigger clarification still awaits owner ratification, and the three narrower-than-spec disclosures are still open. Both were explicitly out of scope this iteration. |
| Host-guard caps | OK | The walk runs on one background thread inside the already-confined server process; no new process or worker pool. |

No NEW anti-goal violation was introduced this iteration.

One real defect found by the evaluator that nobody else recorded (not an anti-goal violation, but it
should be fixed): the plan preview refetches on every keystroke, and a half-typed date makes the
backend raise instead of answering honestly —
`_planned_dates("2026-06-2", "2026-06-24")` raises `ValueError: Invalid isoformat string`, so the
plan endpoint returns a 500 while the operator is still typing. An inverted range is handled
correctly (empty plan, no error), so only malformed dates are affected.

## Next-Step Recommendation

Build J-08 "The evidence view" next, and run it as a deep iteration with the auditor. This is the
step that pools every recorded signal into distributions beside the random-chance rows, so honesty
mistakes there would be invisible in a screenshot — an auditor is the right reader for it.

Carry five cheap items inside the same cycle:

1. Make the automatic replay checks start from the same scoped test backend the live browser check
   uses, so no replay script can ever press a compute button against the owner's real records.
2. Record a stored replay script for J-06 "The range family". It has none today, which is why it
   was skipped this run for lack of time and will keep being skipped.
3. Re-take the one owed picture: the Range Trade row opened so its full geometry line is readable
   (owed since iteration 6; this run's captures show the row but not its opened detail).
4. Make the back-scan plan answer honestly instead of failing when the date box holds a half-typed
   date.
5. Fix the J-05 replay script so it checks a real signal row rather than a word that also appears in
   the section's own description paragraph.

Four questions still wait for the owner and get more expensive once distributions pool real numbers:
say yes or no to the one sentence a developer added to the rule book about range trades; and settle
the three places where the shipped code reads the book more narrowly than it is written.

## Escalation Justification

This is not a halt — the loop continues, but the next iteration must run the full pipeline.

- The iteration spec asked for a deep pass with the auditor and the engine ran it as a fast one, for
  the third time in this session. J-07 is the first code that can write many records into the
  owner's own store in one act, and it went out with no auditor reading it.
- The fast pass left a real hole I found by hand: the automatic replay checks still point at the
  owner's real records, and two of them press a compute button. Nothing was written this time, but
  that is luck of the calendar, not a rule.
- J-06 "The range family" was not tested at all this run (the time budget cut it) and it has no
  stored replay script, so it will keep being skipped until one is written.
- The next journey pools numbers into distributions, which is precisely the kind of work the
  auditor caught real problems in three times already this session.
