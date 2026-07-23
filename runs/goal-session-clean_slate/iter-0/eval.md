# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Verify-only baseline for "The Clean Slate" demolition interlude. Zero source changes (the iteration
diff is docs-only: `docs/goal.md` rewrite + the new `docs/goal-archive/goal-2026-07-17.md`; scan CLEAN;
`git diff HEAD~1..HEAD -- apps/` empty). The demolition has not started, so J-01–J-04 are recorded
`failing` exactly as the spec predicted, and J-05 is `partial` — the kept product is overwhelmingly
intact (sim cockpit + both charts, AAPL wall band, honest Edge-Report state, full suite green) but one
acceptance clause (Case Studies drill-in) is unmet and its full literal acceptance ties to the post-J-04
end state. No anti-goal is violable this iteration.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | (none — first eval) | failing | `reports/phase-goal-clean_slate-iter-0-ui-test-results.md#UT-J-01` — curl: I-1 routes 200/422 not 404; grep: 11 modules still imported; `r_basis`/dataset-source symbols un-relocated; fingerprint `4d665603569b9dbf` (keyless/automated — no screenshot by design) |
| J-02 | (none — first eval) | failing | `reports/qa/goal-clean_slate-iter-0-evidence/J-02-journal-still-exists.png`, `J-02-studies-still-exists.png`, `J-02-performance-still-exists.png`, `J-02-cockpit-thesis-hint-sound-present.png` — nav shows 5 items; three pages render (not 404); thesis/hint/sound UI present. Corroborated by the 5-item nav visible in the J-05 cockpit screenshots I opened. |
| J-03 | (none — first eval) | failing | `reports/phase-goal-clean_slate-iter-0-ui-test-results.md#UT-J-03` — `app/mcp/__init__.py` still registers 18 tools incl. `journal`/`analytics`/`studies`; confirmed against the live session MCP roster (keyless/automated) |
| J-04 | (none — first eval) | failing | `reports/phase-goal-clean_slate-iter-0-ui-test-results.md#UT-J-04` — `config_fingerprint()` = `4d665603569b9dbf` (old pin); `verdict_dwell_seconds`/`hint_sustain_dwell_seconds` still in `config.py` (keyless/automated) |
| J-05 | (none — first eval) | partial | `reports/qa/goal-clean_slate-iter-0-evidence/J-05-cockpit-sim-buyer-control-30s.png` (opened: Buyer Control conf 0.921, 30s candles→107.27, state marker, timeframe switch), `J-05-structure-aapl-load.png` (opened: `resistance 300.11–302.2 Class A score 171 round` wall band on StructureChart), `J-05-structure-edge-report-honest-state.png`. Suite green 1665p/7s/0f under the OLD pin. GAP: Case Studies drill-in unreachable (`SHOW_CASE_STUDIES = false`). |

## Anti-goal Check

Iteration diff = 2 docs files only (`docs/goal.md`, `docs/goal-archive/goal-2026-07-17.md`); zero
`apps/` changes; scan-report CLEAN. Every category checked against the diff, not assumed:

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No execution path (rail 1) | OK | No code changed; `test_no_execution_path.py` present + green in the 1665-pass suite |
| No profit claims / advice (rail 2) | OK | No surface changed; `test_copy_discipline.py` present + green |
| Frozen foundations byte-identical (rail 3) | OK | Zero `apps/` diff; fingerprint still `4d665603569b9dbf` |
| Hold-out-only promotion (rail 4) | OK | Champion pointer unchanged (`v1`/`default`); no gate touched |
| No lookahead (rail 5) | OK | No compute code changed |
| Single source of truth (rail 6) | OK | No new/duplicated value; coherence.md absent (zero-diff baseline — nothing to audit; not a COHERENCE-FAIL) |
| Deterministic/seeded (rail 7) | OK | No code changed |
| Read-only MCP (rail 8) | OK | MCP source unchanged |
| Immutable data (rail 9) | OK | No dataset/bar touched; read-only GET probes only |
| Persistence scoped (rail 10) | OK | No recording/fetch performed |
| No research-value change beyond epoch bump | OK | No value moved (no code changed) |
| Deletion complete, never cosmetic | N/A | Demolition not started (baseline) |
| No new features | OK | Nothing added |
| Relocations are moves not rewrites | N/A | Relocations not started (baseline) |
| Never modify the charts beyond the one edit | OK | Charts untouched; 3 chart guard suites green |
| Never touch a historical record | OK | `goal-2026-07-17.md` is a NEW archive file (added, not edited); no `goal-archive`/`runs`/`delivered`/pnl-row edits in diff |
| No guard weakening | OK | 13 fingerprint pins + all guard tests unmodified (zero `apps/` diff) |
| Enhancement loop stays in its box | OK | goal.md rewrite is operator-authored (commit e7865b4); `AUTO:journeys` block empty |

## Next-Step Recommendation

**Iteration 1 → target J-01 alone, at `full` depth.** Per `docs/goal.md`'s dependency order (J-01 → … →
J-05) and the spec's own "Depth expectation" note: relocate first and prove the full suite green
(`r_basis` → `backtests.py`; the four dataset-source symbols → `datasets.py`; update importers +
`edge_report.py:72` comment) BEFORE any deletion; then the 14-route deletion (re-grep the 15-vs-14 count
at execution time per T-14 — reconciled to 14 this iteration), `routes.py`/`taxonomy.py` SLIM, the
eleven-module deletion (T-12 grep-before-delete each), `JournalStore` method deletion, and the ~24
test-file deletions + I-8 UPDATE edits. Leave the 13 fingerprint pins untouched until J-04 (T-3). This is
large, structural, and has a hard two-phase ordering constraint → `full`, not `lean`.

**Surface for the decomposer/human before J-05 can ever close (T-14 inventory-vs-reality contradiction):**
the Case Studies section is code-suppressed (`apps/frontend/app/structure/page.tsx:335`
`const SHOW_CASE_STUDIES = false`, from commit `e60f6a7`, 2026-07-20 — three days BEFORE this goal.md was
authored against `main @ fa76460`, which already contains that commit). J-05's literal acceptance requires
"a Case Study drill-in opens," which the shipped app cannot satisfy. This is NOT a regression (pre-existing;
zero-diff iteration) but it IS an unresolvable-as-written gap: whoever executes/closes J-05 must EITHER
restore `SHOW_CASE_STUDIES = true` (the commit message calls the suppression "reversible" — a one-line dev
change) OR the operator must rescope J-05's acceptance line (editing a human-authored journey is an
operator-only action). Flag this early so it is decided before the J-05 sentinel work, not discovered at
era close.

## Halt Justification (if halting)

Not halting — verdict is CONTINUE. Baseline recorded the honest not-yet-started state completely; the
failing journeys (J-01–J-04) are tractable, well-scoped dev work with no human-owned blocker, so neither
STALLED nor ESCALATE applies (review lane PASSED — no fail-open; no journey has failed twice; the
depth-for-next is conveyed via the Depth Recommendation line rather than forced via ESCALATE). GOAL_ACHIEVED
is excluded because J-01–J-04 are `failing` and J-05 is `partial`.
