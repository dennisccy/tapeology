# Iteration 4 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The Playbook now finds three more of the book's setups, and I saw all three on screen myself:
a Jump-Base Explosion (long), a Drop-Base Implosion (short), and a Cup and Handle (long), each
with its own measurements printed beside it. Nothing that already worked broke: I re-ran the whole
backend test suite (2061 passed, 8 skipped), checked the pin, the three menu items and the 18
Claude tools, and confirmed the owner's older records were left untouched while a new one was
written beside them. One new small problem is open: the summary sentence the product prints
beside every record still says it only finds opening-range breaks, which is now less than the truth.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The signal contract | passing | passing | `reports/qa/goal-playbook-iter-4-evidence/UT-07-result.png` (row UT-J-01/UT-07); evaluator's own suite run 2061 pass / 8 skip |
| J-02 Every signal measured | passing | passing | `reports/qa/goal-playbook-iter-4-evidence/UT-07-result.png` (row UT-J-02) — full forward table, dual MDD, invalidation and baseline lines |
| J-03 The Playbook lands on /desk | passing | passing | `reports/qa/goal-playbook-iter-4-evidence/J-03-verify.png` (row UT-J-03, stored golden replay) |
| J-04 The continuation family | failing | **passing** | `reports/qa/goal-playbook-iter-4-evidence/UT-02-result.png` (JBE), `UT-03-result.png` (DBI), `UT-04-result.png` (Cup and Handle), `UT-11-result.png` (two-firing ladder, "ladder step ratio 0.68") |
| J-05 The climax family | failing | failing | not targeted; served setups tuple has no capitulation/euphoria entry |
| J-06 The range family | failing | failing | not targeted; no range/double-top entry in the served setups tuple |
| J-07 The back-scan | failing | failing | not targeted; no backscan route exists |
| J-08 The evidence view | failing | failing | not targeted; `desk_playbook_evidence.py` still absent (now forward-guarded by `tests/test_desk_playbook_guards.py`) |
| J-09 MCP contract v4 | failing | failing | evaluator imported `app.mcp._STATIC_PATHS` live: 12 static entries = 18 tools; `tests/test_mcp_server.py` still asserts 18 |
| J-10 The kept product stands | partial | partial | `reports/qa/goal-playbook-iter-4-evidence/UT-08-lower-sections.png` + `UT-J-10-result.png` (rows UT-08, UT-J-10); suite 2061/8, pin `08e471b10130e1e2`, three nav routes — still short of its own "20 tools" clause until J-09 |

Deferred / infra rows this iteration: none. Every required-still-passing journey (J-01, J-02,
J-03, J-10) carries a fresh row in `reports/phase-goal-playbook-iter-4-ui-test-results.md`.

The deterministic replay lane reported a FAIL for J-10 step 5 ("300.11" did not appear). The merged
results file overturns it, and I checked the overturn myself: `UT-J-10-result.png` shows
`/structure` with AAPL as-of 2026-06-22 and the 300.11–302.2 Class A band both drawn on the chart
and listed in the table. A dated reconciliation footer is on
`reports/phase-goal-playbook-iter-4-regression-replay-results.md`.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-4/scan-report.md`: CLEAN, no findings on added lines (tracked + 1 untracked file) |
| Paid / external SaaS, new dependency | OK | scan-report CLEAN; the 9 changed product files contain no manifest (`package.json`, `requirements*.txt`, `pyproject.toml` all untouched) |
| License changes | OK | scan-report CLEAN; no LICENSE file in the diff |
| Fabricated / substituted data | OK, with one fixed defect | The three new detectors read stored bars only. The auditor found a **misleading label** — a short `dbi` row printed "ascending base" while the code measured non-increasing highs — and fixed it inside this iteration (`page.tsx:4610-4611`, guarded by a source-scan test + seeded counter-test). No number or served field changed. Recorded as a minor violation, resolved. |
| No execution path, ever | OK | `test_no_execution_path.py` unmodified and green inside the 2061-test run; no order/broker concept in the new geometry fields |
| No profit claims / no advice; a signal is an observation | **VIOLATION (minor, OPEN)** | `PLAYBOOK_REGISTER` (`apps/backend/app/research/desk_playbook.py:159-160`) and the `/desk` blurb (`apps/frontend/app/desk/page.tsx:5079`) still say "opening-range-break signals". That register is embedded verbatim into every new record — including `apps/backend/.data/playbook/playbook-2026-06-22-b698c3871e62.json`, whose 5 signals are ALL `jbe`/`dbi` (read by the evaluator). Nothing is fabricated; the sentence simply under-describes. No advice/probability/expectancy wording was introduced. |
| Frozen foundations / kept surfaces byte-identical | OK | `git diff` empty against `desk_forward.py`, `desk_screen*.py`, `setups.py`, `bars.py`, `levels.py`, `config.py`, `mcp/__init__.py`, `desk_playbook_features.py`, `meta.py` — verified by the evaluator, not taken from the handoff. Pin `08e471b10130e1e2` printed live. |
| No lookahead | OK | Truncate-after-trigger + mutate-post-trigger property tests extended to all three new detectors (TC-7) and green in the 2061-test run; the auditor re-derived the cup's trigger boundary (`max(handle_start+1, right.confirmed_at+1)`) independently |
| Single source of truth | OK | `iter-4/coherence.md` = **COHERENCE-PASS**: new fields land inside the one already-registered "Playbook records" row, same owner, same endpoint; `ladder_step_ratio` computed once server-side and read verbatim |
| Deterministic and seeded | OK | Two-firing JBE ladder draws two independent anchors (TC-8, and visible as "ladder step ratio 0.68" in `UT-11-result.png`); re-compute byte-identical |
| Read-only MCP (18 tools this era until J-09) | OK | `app/mcp/__init__.py` zero diff; live count 18 |
| Immutable data / no record rewritten, backfilled, pruned | OK | Evaluator listed the real store: `playbook-2026-06-22-c204913154c5.json` (old 2-setup signature `5b70ba860b5efd47`) sits untouched beside the new `playbook-2026-06-22-b698c3871e62.json` (new 5-setup signature `898af0960779e897`) — re-key, not rewrite. Duplicate-key raise (TC-14) untouched. |
| No threshold outside the spec; no sweep | OK | Two new named constants (`PLAYBOOK_BASE_FLATLINE_MAX_MBR = 1.0`, `PLAYBOOK_HANDLE_DESIRABLE_DURATION_FRAC = 0.25`) promote values that ALREADY existed in the pre-iteration spec prose (verified with `git show ac6e9ad:docs/playbook-detector-spec.md`, lines 242 and 148) and are now tabulated in §1. New source-scan guard (TC-12) finds zero threshold sweeps. See `assumptions.md`. |
| No second implementation of the measurement rail | OK | `desk_forward.py` zero diff; import-graph verified by the coherence auditor; `desk_playbook_features.py` zero diff (shared primitives called, not reforked) |
| The evidence pools one signature | n/a | J-08 not built; a forward guard now bans `desk_playbook_detect.py` from importing any `*evidence*` module (TC-13) |
| Host-guard caps | OK | no change to host-guard config; no unconfined heavy path added (real computes are operator acts) |
| Iteration-3's open minor violation (stray fixture record) | **RESOLVED** | `playbook-2026-08-04-e0f249f57785.json` is gone (evaluator listed the store); no `LADDER`/`DBI1`/`CUP1` record exists anywhere in it; the fixture rig ran against a scratch dir via `TAPEOLOGY_DESK_PLAYBOOK_DIR` and friends. `UT-09-result.png` shows that date now serving the honest "Playbook not computed for this session." panel. |

## Next-Step Recommendation

Build J-05 "The climax family" (capitulation entry plus the euphoria marker) next, and run it as a
deep iteration with the auditor again. The auditor was the only reader who caught two real problems
this time — a short signal labelled with the opposite of what was measured, and two "must not fire"
tests that were passing for the wrong reason — so new detection maths should keep getting that
extra pair of eyes.

Carry three small items inside the same cycle:

1. Rewrite the summary sentence printed beside every record (`desk_playbook.py:159`) and the
   heading paragraph on the Desk page (`page.tsx:5079`) so they name every setup family the
   product now records. This changes no number and does not re-key any record — but the existing
   "the sentence must not change" test has to be updated deliberately in the same edit, the way
   the refresh-chain count guard is.
2. Re-take one picture of the Drop-Base Implosion row: the wording fix landed after the pictures
   were taken, so the stored picture shows the old wording.
3. Put back the clean rebuild before the browser checks (it was skipped this time), and remember
   that the "the evidence module does not exist" test must be flipped when J-08 is built.

Two questions for the owner, cheap to answer now and expensive after the back-scan reads real
sessions: whether the book's "jump must be 1.5x the base" rule is meant to be unreachable under the
current numbers (with a base capped at 2.0 and a jump floor of 3.0, the floor always rejects first),
and whether the cup's rim test should use the rim constant the spec names instead of the near-high
one the code uses (both are 1.0 today, so nothing behaves differently yet).

In one sentence: approve building the capitulation and euphoria setups next, as a deep run, with the
product's own summary sentence corrected in the same pass.
