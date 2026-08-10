# Iteration 2 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The desk can now say what price did after each signal it finds. J-02 "Every signal measured" is
genuinely done: every detected opening-range break carries a forward measurement made with the
desk's existing measuring rules, plus an honest note about whether price later traded through the
book's own invalidation level. I checked this myself rather than trusting the write-ups — I re-ran
the whole backend test suite (2025 pass, 8 skipped, nothing failed), read the new code to confirm
the measuring maths is borrowed from the existing rail instead of copied, and confirmed by git that
none of the protected files and none of the website files changed. The kept-product check that was
skipped last time was run this time and passed, and I opened its screenshot to confirm it.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The signal contract | passing | passing (re-verified) | zero production diff to the detection files; evaluator re-ran 99 playbook tests + full suite 2025 pass / 8 skip; `reports/phase-goal-playbook-iter-2-ui-test-results.md` row UT-J-01 (SKIP — journey has no browser step) |
| J-02 Every signal measured | failing | **passing** | `apps/backend/tests/test_desk_playbook.py::test_measure_signal_and_measure_from_produce_byte_identical_leaves` (+98 sibling playbook tests, all green when the evaluator ran them); full suite exit 0, 2025 pass / 8 skip; `reports/reviews/goal-playbook-iter-2-review.md` PASS |
| J-03 The Playbook lands on /desk | failing | failing (not targeted) | `reports/qa/goal-playbook-iter-2-evidence/J-01-J-02-desk-no-ui-change.png` — /desk still shows only the shipped sections |
| J-04 The continuation family | failing | failing (not targeted) | carried from `reports/qa/goal-playbook-iter-0-evidence/J-03-desk-no-playbook.png` |
| J-05 The climax family | failing | failing (not targeted) | carried from iter-0 evidence |
| J-06 The range family | failing | failing (not targeted) | carried from iter-0 evidence |
| J-07 The back-scan | failing | failing (not targeted) | carried from `reports/qa/goal-playbook-iter-0-evidence/J-07-route-404.png` |
| J-08 The evidence view | failing | failing (not targeted) | carried from `reports/qa/goal-playbook-iter-0-evidence/J-08-route-404.png` |
| J-09 MCP contract v4 | failing | failing (not targeted) | evaluator counted the live tool list: 12 static paths = 18 tools, not 20; zero diff to `app/mcp/__init__.py` |
| J-10 The kept product stands | partial | partial (replay gap CLOSED) | `reports/phase-goal-playbook-iter-2-regression-replay-results.md` PASS 1/1 + `reports/qa/goal-playbook-iter-2-evidence/J-10-verify.png` (same run — both files carry mtime 19:10:03) |

Note on J-10: it stays "partly done" for the same reason as the last two iterations — its own
wording asks for 20 Claude tools and there are 18 until J-09 ships. Nothing about the kept product
is broken; the missing browser replay that iteration 1 left open was run this time and passed.

Note on J-01 and J-02: both are marked "(Keyless; automated.)" in `docs/goal.md`, so neither has a
browser step to photograph. The browser lane recorded them as SKIP with a written reason, and the
lane itself was healthy (it loaded /desk and took a screenshot) — this is not a missing-evidence
skip.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-2/scan-report.md` = CLEAN; the changed-file list holds only 4 Python modules, 4 test modules and one spec document — no config or env file |
| Paid / external SaaS | OK | no dependency manifest in the diff (`git diff ecf6ab5 --stat` shows 5 tracked + 4 untracked files, none of them a manifest); scan-report has zero dependency findings |
| License changes | OK | no LICENSE file or license field in the diff; scan-report clean |
| Fabricated / substituted data | OK — checked closely | this was iteration 1's critical failure class. The new risk is the 5m→1m anchor mapping. A trigger window with no 1m bars degrades that one signal to the 5m basis and discloses it (`test_gapped_1m_window_at_the_trigger_bar_degrades_honestly_to_5m_basis`), rather than borrowing a bar from the neighbouring window; the "first bar of the window" fallback is the pre-registered rule from the spec's own §0 (`docs/playbook-detector-spec.md:58`) |
| No execution path | OK | `test_no_execution_path.py` green in the full suite; `test_no_served_signal_field_is_ever_named_stop_loss` green; the field is `invalidation_price` |
| No profit claims / advice | OK | evaluator read the served register text in `desk_playbook.py`: descriptive only, states no fills, no costs, no probability/expectancy/edge/significance; `test_playbook_register_passes_copy_discipline` green |
| Frozen foundations | OK | evaluator ran `git diff` per file: 0 changes to `desk_forward.py`, `desk_forward_compute.py`, `desk_screen.py`, `setups.py`, `bars.py`, `levels.py`, `config.py`, `mcp/__init__.py` and all of `apps/frontend` |
| No lookahead | OK | detection code carries a zero production diff, so the lookahead property tests still bind unchanged; measurement legitimately reads later bars — that is what a forward measurement is |
| Single source of truth | OK | `iter-2/coherence.md` = COHERENCE-PASS; the rail helpers are imported at `desk_playbook.py:52-62`, not re-written |
| Deterministic and seeded | OK | the baseline draw builds `random.Random("<seed>:playbook-<date>:<symbol>:<setup>")` and calls the rail's own `_draw_anchor_indices` — no global randomness, no `random.sample`; repeat-run equality asserted by test |
| Read-only MCP | OK | zero diff to `app/mcp/__init__.py`; live count still 18 tools |
| Immutable data / no rewrite | OK | store has no update or delete method (test); duplicate key raises; a re-key writes a new file and the earlier file's SHA-256 is asserted unchanged |
| Persistence stays scoped | OK | computing is an explicit act via POST or the CLI; the read endpoints only read |
| No threshold outside the spec, no sweep | OK — with a recorded judgement call | the new cross-symbol pooling cap re-uses the measuring rail's own existing number (`DESK_FORWARD_MAX_TOUCHES_PER_ROW`), echoed into the parameters blob so a future change re-keys records. The spec's §0 already says the seeded random-anchor baseline is "the rail's, unchanged", so this is inside the spec's delegation rather than a newly invented threshold. No code loops over candidate values. Logged in `assumptions.md` |
| Enhancement loop stays in its box | OK | `docs/goal.md` has zero diff this iteration |
| Host-guard caps | OK | no heavy path ran; every test in this iteration is fixture-scoped and keyless |

Iteration 1's one open minor violation (a detector rule written in code but not in the spec) is now
**resolved**: the spec document states the rule, and a test proves the code line did not move.

## Next-Step Recommendation

Build **J-03 "The Playbook lands on /desk"** next, at full depth. This is the first time the
playbook becomes visible to the person using the product: a session-date box, a Run Playbook button
with live progress and a cancel, the signals table with its forward numbers, and honest wording when
nothing has been computed yet. It needs a real browser pass with screenshots, and it touches the
protective tests that guard the desk page, so the fuller review-and-audit pass is worth it.

Ask that iteration to also carry four small items rather than making them their own iteration:
1. Show the exact sentence `"measurement not recorded in this record"` for records made before
   measurement existed — today the backend leaves the measurement block out, which is honest, but
   the sentence the goal names has never been written anywhere.
2. Remove the unused import flagged in the review (`desk_routes.py:126`).
3. Use the rail's own `_side_sign` helper instead of repeating the two-line long/short mapping twice
   (`desk_playbook.py:170` and `:281`), as the coherence audit advises.
4. Before adding more setup families, fix the baseline-anchor draw so it works when one symbol fires
   more than one signal of the same setup in a session; today it hard-codes one anchor per symbol
   (`desk_playbook.py:557`) and re-seeds with the same string each time, which is correct only
   because opening-range breaks can fire at most once per symbol per day.

In one sentence: next, put the playbook on the Desk page where the operator can actually see and run
it, and fold the four small clean-ups above into that same piece of work.
