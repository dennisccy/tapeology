# Iteration 22 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

The round did everything it set out to do, and I checked it myself rather than reading the
reports. All three of the pilot studies now have a real, recorded answer on the Desk page, and
they can be run by an operator from the command line or the web address — not only from a test.
The graduation page was photographed fresh, which closes the gap the clock created last round.
That makes nine of the ten journeys green. The tenth, J-06 "The recorder and the Vault", cannot
move at all without you: its only remaining step is the recording of real market tape, which the
goal itself calls an operator act and which you have told the machine not to do. Every way out of
that is a decision only you can make, so I am halting the run rather than spending another round
that cannot reach the finish line.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (replay re-verified) | reports/qa/goal-rapid-microscope-iter-22-evidence/J-01-verify.png |
| J-02 The micro observer | passing | passing (replay re-verified) | reports/qa/goal-rapid-microscope-iter-22-evidence/J-02-verify.png |
| J-03 Structure x flow | passing | passing (replay re-verified) | reports/qa/goal-rapid-microscope-iter-22-evidence/J-03-verify.png |
| J-04 The Scout and the ledger | passing | passing (replay re-verified; evaluator spot-check) | reports/qa/goal-rapid-microscope-iter-22-evidence/J-04-verify.png |
| J-05 The walk-forward engine | passing | passing (replay re-verified) | reports/qa/goal-rapid-microscope-iter-22-evidence/J-05-verify.png |
| J-06 The recorder and the Vault | partial | partial (not tested; carried over) | reports/qa/goal-rapid-microscope-iter-21-evidence/J-06-verify.png (iter-21; operator step still owed) |
| J-07 Graduation | passing (stamp iter-20) | passing (fresh iter-22 capture) | reports/qa/goal-rapid-microscope-iter-22-evidence/UT-08-result.png |
| J-08 The surface and MCP v6 | passing | passing (replay re-verified; evaluator spot-check) | reports/qa/goal-rapid-microscope-iter-22-evidence/J-08-verify.png |
| **J-09 The pilot studies** | **partial** | **PASSING** | reports/qa/goal-rapid-microscope-iter-22-evidence/UT-07-result.png (+ UT-02, UT-03, UT-10-ledger.jsonl) |
| J-10 The kept product stands | passing | passing (replay re-verified) | reports/qa/goal-rapid-microscope-iter-22-evidence/J-10-verify.png |

Evidence I opened myself for the two journeys whose status or stamp changed:

- **J-09.** UT-02 shows Study 1's family `failed_aggression_score__band_touch__trades_20` with a
  screen row and a `— / —` floor-check row, both `killed_insufficient_n`. UT-03 shows Study 3's
  family `failed_aggression_score__playbook_signal__trades_20` in the same shape with Study 1
  still present. UT-07 (1668x3918) shows all three pilot families plus the three default-grid
  families, and I cropped it to read Study 2's floor-check row registered `2026-08-20 18:47 ET`
  — this iteration, which is the photograph round 21 said was still owed. I then read the
  command line's own ledger (`UT-10-ledger.jsonl`) by hand: two rows under one candidate id, the
  first carrying the evidence class, the denominators, the concentration, fallback and
  best-of-N disclosures and the money column with its "research cost proxy" sentence, the second
  carrying `stage: walkforward_floor_check`, `status: insufficient_n`.
- **J-07.** UT-08 is a full graduation answer — one family, one sealed reading with verdict
  `pass` over 30 observations, both breadth floors recorded as "not applicable to one day"
  exactly as your round-17 ruling requires, and the chain check `ok`. It is a different file from
  round 20's capture (md5 `5cc50f17…` vs `abe0c70c…`), so it is a genuinely fresh look.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | `iter-22/scan-report.md` = CLEAN on added lines; the three changed files are `micro_routes.py`, `scout.py`, `test_scout.py` — no config or env file in the diff. Vault-secret rail untouched (no `vault.py` diff). |
| Paid / external SaaS dependency | OK | No manifest changed (`pyproject.toml`/`requirements*` absent from the diff); scan-report reports no dependency findings. |
| License change | OK | No LICENSE or license-field diff; scan-report clean. |
| Fabricated or substituted data | OK | Runs used committed hermetic fixtures in the scoped QA rig; every ledger row carries its `corpus_manifest` with dataset checksums and `evidence_class: historical_exposed_diagnostic`. The store-scope guard (`reports/qa/goal-rapid-microscope-iter-22-store-scope-guard.md`) reports the real store at 11,275 files before and after, byte-size and mtime unchanged. |
| No execution path, ever | OK | No broker/order code; `test_no_execution_path.py` green in my own full-suite run. |
| No profit claims and no advice | OK | No new prose; the money column keeps its "quoted spread is a research cost proxy, not a full execution or tradability model" sentence verbatim in every screen row I read. |
| Frozen foundations | OK | I ran the fingerprint myself: `08e471b10130e1e2`. `git status` shows no `referee_*` and no `config.py` change. The default grid path is unchanged — the new `grid_selector is not None` test is only reached after an unknown selector already raised, which I confirmed in the diff, and the rig's six default rows carry no floor-check stage. |
| Hold-out-only promotion | OK (1 older minor open) | No champion move. The round-18 item about the sealed judge's money floor stays open, awaiting your ruling. |
| No lookahead | OK | Anchor extraction and join code unchanged this round. |
| Single source of truth | **MINOR — new, open** | `micro_routes.py:284-287` hand-writes a second copy of the selector-to-kind classification that `scout.py:1684-1689` already owns. Raised by all three lanes; the two agree today. Minor, not critical, because a future mismatch raises a loud `ValueError` (HTTP 500) rather than serving a wrong number. Coherence verdict for the round is COHERENCE-PASS. |
| Deterministic and seeded | OK (1 older minor open) | The rule the round-21 evaluator wrote — re-run the replay set before any lane that writes into the shared practice rig — was honoured: the replay ran 22:41:33Z–22:42:06Z, the first writing request landed 22:44:01Z. I re-read those timestamps. The underlying order-dependence stays open as the round-21 item. |
| Read-only MCP | OK | No `app/mcp/` change; the 26-tool contract is asserted in `tests/test_mcp_server.py` and green. |
| Immutable data | OK | Store-scope guard CLEAN; no dataset written outside the scratch rig. |
| Persistence stays scoped | OK | Every run was an explicit request or command; the command-line run was pointed at scratch directories, never `.data/`. |
| Evidence classes never mix | OK | Screens emit `historical_exposed_diagnostic`; the floor check only reads the `historical_oos` count in order to refuse. The source-level guard test is green. |
| No threshold chosen from outcomes | OK | `pilot_study_candidate_grid`'s body is unchanged (comments only); Study 1's frozen request `failed_aggression_score >= 0.5` is pinned by its own test. |
| The denominator never shrinks | OK | Each pilot family still reports one variant tried; the second stage row does not inflate it (checked on screen in UT-07). |
| Screenshot or `unknown`, never `passing` (T-10) | **MINOR — opened and repaired in-round** | The quality report cited two blank screenshots (one file, used twice) and one screenshot copied from another lane. The independent checker found it and appended a signed retraction; I read the retraction and re-confirmed every md5 in it. The claims themselves are true from other evidence. This is the second round running that this lane certified something it had not checked. |
| Hermetic tests carry known truth | **MINOR — new, open** | Study 3's new test cannot fail on an empty screen. I proved it: I moved the planted signal outside the data window so nothing could match, and the test still passed. Study 1's sibling test has the missing one-line check. Files restored byte-identical afterwards. |
| Tranche stays one opaque pool / no sealed read / Referee byte-frozen / no sub-second horizon / no cross-unit arithmetic | OK | None of the implicated modules appear in the three-file diff. |

## Next-Step Recommendation

Nothing the machine can do on its own will finish this era. J-06 "The recorder and the Vault"
needs you. Please pick one of the three options in the halt note below and then restart the run.
If you would rather keep the machine busy while you decide, three small jobs need nobody's
permission and are written into the next planner's digest: make the Desk readiness panel stop
taking twenty-two seconds, collapse the duplicated study-selector list into the single list that
already owns it, and add the one missing line to Study 3's test so it can fail. None of those
moves a journey; they are polish, and I have deliberately not dressed them up as progress.

## Halt Justification

Nine of the ten journeys are green and proved. The tenth, J-06 "The recorder and the Vault", is
stuck on a step the goal itself calls an operator act: screening and freezing the Tier-B list of
symbols, then recording real market tape from the paid data feed to the era's own minimum size,
sealing it at birth. Everything before that step is built — the recorder and the vault both exist
on disk, and I confirmed that. The step itself needs three things only you control: the paid feed
subscription, your attendance during the run, and your sanction for an act that cannot be undone
(sealing is one-way and permanent by design). You have told the machine not to do it in each of
the last six rounds, and it has correctly obeyed.

Your options, plainly:

1. **Authorise the recording and attend it.** The machine then re-checks J-06 and the era can
   finish.
2. **Change what the goal asks of J-06** in `docs/goal.md` — for example, accept the recorder and
   vault machinery as proved on practice data, without a real tranche. Then the era can finish
   without any recording.
3. **Resume anyway and accept an unfinished era**, letting the machine spend its time on the
   three polish jobs above. This will not turn J-06 green.

Two honest limits you should know before you choose, neither of which changes the verdict:

- Every one of J-09's three answers is "not enough data". The studies ran against practice
  fixtures, so the questions have been asked properly but never of your real recorded tape.
  Asking them for real is also gated on you: it writes permanent rows into the live record, it
  would break J-10's stored check that the live record is empty, and the search is currently far
  too slow to finish against real data. I scored J-09 as passing because its own written pass
  bar names "not enough data" as an acceptable answer and because rounds 20 and 21 both promised
  in writing that three recorded answers would be enough — moving that bar after the work was
  done to order would be dishonest. The limitation is recorded in full in the journey record and
  the assumption ledger.
- The walkthrough recording's last step shows a "404 page not found". That is the recording tool
  pointing a research address at the website's port, which has no route for it — the same
  mechanism round 19 recorded. The real check for that page passed and I opened its picture. I
  did not ask for a re-recording because it would produce the identical 404.
