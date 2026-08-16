# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

This was the honest opening count for the new "Rapid Microscope" era. No code was written, and
none was expected. The team checked all ten journeys against the running product and the
codebase: none of the new microscope features exist yet, and everything the project already
shipped still works. The two starting numbers this era must protect were re-checked by me and
are correct: the backend test suite passes 2,691 tests with 8 skipped, and the settings
fingerprint still reads `08e471b10130e1e2`.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | (none — first iteration) | partial | `reports/qa/goal-rapid-microscope-iter-0-evidence/J-01-desk-readiness-absent.png`; `reports/phase-goal-rapid-microscope-iter-0-ui-test-results.md` UT-J-01 |
| J-02 The micro observer | (none) | failing | `reports/phase-goal-rapid-microscope-iter-0-ui-test-results.md` UT-J-02; `apps/backend/app/research/datasets.py:376` has no `observer=` kwarg (evaluator re-checked) |
| J-03 Structure x flow join | (none) | failing | UT-J-03; `micro_join.py` absent (evaluator `find` re-check) |
| J-04 The Scout and the ledger | (none) | failing | UT-J-04; `scout.py`/`scout_ledger.py` absent (evaluator re-check) |
| J-05 The walk-forward engine | (none) | failing | UT-J-05; `micro_accessor.py`/`walkforward.py` absent (evaluator re-check) |
| J-06 The recorder and the Vault | (none) | failing | UT-J-06; `tick_recorder.py`/`vault.py` absent; `providers/adapters/base.py:64-82` has no preservation fields |
| J-07 Graduation | (none) | failing | UT-J-07; `micro_graduation.py` absent (evaluator re-check) |
| J-08 The surface and MCP v6 | (none) | failing | `reports/qa/goal-rapid-microscope-iter-0-evidence/J-08-desk-sections-absent.png`; `EXPECTED_TOOLS` is a 22-tuple (evaluator parsed `tests/test_mcp_server.py`) |
| J-09 The pilot studies | (none) | failing | UT-J-09; no ledgered study specs (no scout ledger exists) |
| J-10 The kept product stands | (none) | partial | `.../J-10-cockpit.png`, `.../J-10-structure.png`, `.../J-10-desk.png`; suite 2691 pass / 8 skip; fingerprint + 6/6 referee SHA-256 re-run by the evaluator |

Notes on the two `partial` rows:
- **J-01** — steps 1-2 verified true (all era-transition documents present; era-open baseline
  recorded). Steps 3-4 verified absent (`GET /research/desk/micro/readiness` → 404; no
  Microscope Readiness section in the `/desk` screenshot).
- **J-10** — the sentinel half is verified (suite, fingerprint, referee hashes, three kept
  pages screenshot-verified as shipped). The TR-1…TR-22 trap suite and the
  deterministic-rerun check do not exist yet, so full acceptance is not met.

Capture-scope gap recorded for later (not a product defect): the cockpit screenshot shows the
idle "No ticker watched" state, so the live-tape chart named in J-10 step 3 was not exercised,
and the four collapsed `/desk` panels (Playbook Evidence, Referee Registry, Referee
Adjudications, Referee Runs) were captured as headers only. A later J-10 sentinel pass should
expand them.

## Anti-goal Check

Product diff this iteration = three documentation files only (`docs/goal.md`,
`docs/rapid-validation-spec.md`, `docs/research-directions.md`, commit `bbfcfd0`, authored by
the human operator at 23:25 before the developer step began at 23:34). Zero files under
`apps/backend/` or `apps/frontend/` changed (`git status --short` re-run by the evaluator).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials committed | OK | `iter-0/scan-report.md` CLEAN; no config/env file in the 3-file diff |
| Paid/external SaaS dependency | OK | no manifest (`package.json`, `requirements*`, `pyproject.toml`) in the diff |
| License changes | OK | no LICENSE or license-field file in the diff |
| Fabricated/substituted data | OK | no code ingests anything; the era-open numbers were reproduced independently three ways (dev dot-count, reviewer fresh pytest run, evaluator re-ran fingerprint + all 6 referee hashes) |
| 1. No execution path | OK | zero source change; `test_no_execution_path.py` present and unmodified |
| 2. No profit claims / no advice | OK | no copy changed; `/structure` capture still carries "simulated — assumed fees/slippage — not indicative of live results" |
| 3. Frozen foundations | OK | fingerprint `08e471b10130e1e2` re-printed by the evaluator; 6/6 `referee_*.py` SHA-256 match the recorded listing; zero `apps/` diff |
| 4. Hold-out-only promotion | OK | champion pointer untouched (`/structure` Registry still v1/default); no promotion path exercised |
| 5. No lookahead | OK | no computation code added |
| 6. Single source of truth | OK | no new served value this iteration; note `coherence.md` was not produced (see below) |
| 7. Deterministic and seeded | OK | no random draw added |
| 8. Read-only MCP | OK | tool list still the 22-tuple, no write tool (evaluator parsed `EXPECTED_TOOLS`) |
| 9. Immutable data | OK | store-scope guard CLEAN — 11,275 protected files unchanged in size and mtime |
| 10. Persistence stays scoped | OK | every probe was a read-only GET; no POST/PUT/DELETE run |
| Rapid-Microscope rails (sealed shards, class mixing, denominators, accessor door, units, vault secret) | OK / not applicable | none of the guarded machinery exists yet; nothing was built to violate |
| Enhancement loop stays in its box | OK | `docs/goal.md` was edited by the human operator's preflight commit `bbfcfd0`, not by the goal-proposer; the `AUTO:journeys` block is still empty |
| Host-guard caps | OK | no heavy compute beyond the test suite; no cap widening or bypass in the diff |

No anti-goal violation, critical or minor, was found.

**Coherence:** `runs/goal-session-rapid-microscope/iter-0/coherence.md` was not produced this
iteration. It is not a `COHERENCE-FAIL`, so it does not force a consolidation pass, but a
missing coherence audit still blocks any GOAL_ACHIEVED verdict. The audit should run once the
first new served value lands (iteration 1).

## Next-Step Recommendation

Build **J-01 "The era transition stands"** on its own next, and nothing else. That means: a new
backend module that reads the tick corpus from disk and reports the truth about it (how many
symbol-days, how many session-equivalents, per-file counts and coverage, each file marked
`exploratory` with a hand-assigned split), a new read-only endpoint that serves it, and one new
"Microscope Readiness" panel at the bottom of the Desk page that shows exactly those served
numbers. Every other journey in this era needs that corpus-truth surface to exist first.

Two things to carry into the next run. First, run the backend tests as `pytest tests/`
without adding `-q` on the command line — the project config already adds it, and doubling it
hides the final "N passed" summary line. Second, the coherence audit did not produce a file
this iteration; make sure it runs once the new panel exists, because that is the first new
value this era serves.

Depth `lean` is right for iteration 1: it is a single journey, and this era's own notes warn
that long iterations timed out repeatedly in the previous era. Move to `full` depth for the
first iteration that lands the leakage rails (J-02 "The micro observer"), where an audit pass
earns its cost.

In one sentence for approval: next iteration should add the "Microscope Readiness" panel to the
Desk page, backed by one new endpoint that honestly reports what tick data is on disk.
