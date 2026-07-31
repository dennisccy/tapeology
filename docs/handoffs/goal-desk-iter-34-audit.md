# goal-desk-iter-34 Audit Report

**Date:** 2026-07-31
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The product fix is real and correct: I re-derived the day-precision grouping myself, in Python, over
the 404 stored outcomes of the ambient run and reproduced the post-fix split (`2026-07-30` newest /
303 pairs, 101 genuinely earlier, all `2026-07-27`) *and* the pre-fix inversion (101/303 with 202 of
the "earlier" rows printing the newest day) — so the contradiction J-19 has carried since iter-32 is
provably gone, not merely reported gone. Two audit findings were fixed: the iteration's demo lane had
produced **no walkthrough at all** (the demo JSON contained a JavaScript regex literal, so the runner
recorded `SKIPPED` with zero steps while the blueprint's `RESOLVED at iter-34` note asserted the
walkthrough was recorded), and the QA report cited a screenshot that does not contain the element it
claimed to confirm. Both are repaired with cited evidence; the remaining gaps are evidence-hygiene
and guard-depth limitations, none of which compromise the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no change needed): zero backend production diff, as specified.**
`git diff --stat HEAD` shows only `apps/backend/tests/test_desk_topup_library_reach_guard.py`
(+135), `apps/frontend/app/desk/page.tsx` (+65/−24), `runs/goal-session-desk/journey-scripts/J-19.json`
and `runs/goal-session-desk/state/blueprint.md`. `desk_topup_compute.py`, `desk_topup_log.py`,
`bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py` and
`routes.py` are byte-unchanged, matching the spec's "Backend: none". `Config().config_fingerprint()`
re-run by me: `08e471b10130e1e2` (unchanged). `tests/test_mcp_server.py` re-run by me: 39 passed,
with `len(TOOL_NAMES) == 17` asserted at `tests/test_mcp_server.py:1084`.

### Frontend Findings

**F1 — GAP (documented, not fixed): the 20 shown rows are the payload's first 20, not the 20
furthest behind.**
`apps/frontend/app/desk/page.tsx:929` — `earlierAll.slice(0, EARLIER_PAIRS_DISPLAY_CAP)` takes
outcome order (symbol, then timeframe), so when a future run's earlier pairs span several days the
visible sample is arbitrary and could omit the oldest reach dates entirely. It is not *dishonest* —
the heading carries the true total (101) and the new sentence says `showing 20 of 101` — and the
implementation summary states "shows only the first 20" plainly. The spec required a cap and a
disclosure, not an ordering, so sorting `earlierAll` by day ascending before slicing would be scope
creep this iteration. Worth recording as the obvious next refinement if the earlier list ever spans
multiple days.
*(For the current ambient run this is invisible: all 101 earlier pairs share `2026-07-27` — verified
directly against `apps/backend/.data/topup_runs/topup-2026-07-31-8fb5c9a1f737.json`.)*

**F2 — OBSERVATION (no change needed): `newestDate` is no longer the maximum timestamp.**
`page.tsx:918/927` returns `dayKeyed.find((d) => d.day === newestDay)!.outcome.store_frozen_through_after`
— i.e. *some* timestamp on the newest calendar day, not the largest one. Output is identical because
the only consumer truncates it (`page.tsx:1024`, `.slice(0, 10)`), and the code says so in a comment
at `:915-917`. Flagged only because the field name now over-promises for any future consumer that
reads it at full precision.

**F3 — OBSERVATION (no change needed): legacy `null` (not `undefined`) reach values are listed as
"recorded earlier".**
`page.tsx:919-925` — an outcome whose `store_frozen_through_after` is `null` has a `null` day key, so
it falls into `earlier` and renders as `SYMBOL tf — no bars recorded`. This is unchanged iter-32
behavior (the old code did the same via `!== newestDate`), not a regression introduced here, and the
row text is honest about having no bars.

### Test Findings

**T1 — GAP (documented, not fixed): the day-truncation guard is a source-substring check, not a
behavioral one.**
`apps/backend/tests/test_desk_topup_library_reach_guard.py:142-151` — `_day_truncation_check` proves
only that (a) some `store_frozen_through_after…​.slice(0, 10)` exists inside the function body and
(b) the two exact iter-32/33 bug strings (`store_frozen_through_after === newestDate` /
`!== newestDate`) are absent. A regression that reintroduced raw-precision grouping under a different
variable name would pass this guard. There is no JS test runner in this repo to do better
(`apps/frontend/package.json` has no `test` script and no jest/vitest dependency), and the spec
explicitly sanctioned "a source-introspection **or** logic-level test", so this is a repo-level
limitation rather than a spec breach. I closed the behavioral hole for this iteration by
re-implementing the grouping independently in Python over the real stored payload (see §3).

**T2 — OBSERVATION (not fixed): one seeded-violation counterpart is a tautology.**
`test_the_cap_disclosure_guard_can_fail_on_a_seeded_violation`
(`test_desk_topup_library_reach_guard.py:98-105`) asserts that a one-line string literal does not
contain a different string literal, instead of feeding a seeded body through the same predicate the
real check uses. It therefore proves nothing about the guard. The guard it accompanies is
nonetheless genuinely fallible (it asserts `"Pairs recorded earlier ({libraryReach.earlierTotal})"
in source` against real file text), and the spec's two *required* new assertions — day-truncation
and cap — both carry real counterparts built on reusable predicates (`_day_truncation_check` at
`:142`, `_cap_check` at `:185`), which I confirmed by reading them. Test hygiene only.

**T3 — GAP (documented, not fixed): `J-19.json` cannot assert the bug is fixed, and step 5 re-adds
environment dependence.**
`runs/goal-session-desk/journey-scripts/J-19.json` now asserts only stable substrings (`"reach it"`,
`"Pairs recorded earlier"`) and testid existence — correct per spec, and the bug-enshrining
`"AAPL 4h — 2026-07-30"` row assertion is gone. But two consequences deserve recording:
1. No live assertion covers TC-1 itself (no earlier row's day equals the reach line's day). The
   replay tool has no cross-step computed comparison and no negative `expect`
   (`demo_runner.py:638-649`), which the spec anticipated and allowed. If the frontend grouping were
   reverted, J-19 replay would still pass — only the pytest guard would catch it.
2. Step 5 asserts the `desk-topup-run-latest-reach-earlier-cap` element exists. That element renders
   only while the ambient run's true earlier-total exceeds 20, so a future real top-up run can make
   J-19 fail for a purely environmental reason — the same fragility class that pinned this script to
   the bug in the first place. The script's own notes disclose this honestly (notes[3]) and cite the
   J-09/J-17/J-18 precedent, which is why this is a GAP and not a spec breach.

**T4 — IMPORTANT (fixed): the demo lane recorded nothing; the blueprint claimed it had.**
`reports/phase-goal-desk-iter-34-demo.json:56` contained `"name": /newest recorded reach/` — a
JavaScript regex literal, which is not valid JSON. `demo_runner.py` therefore parsed nothing and
wrote `**Demo Verdict:** SKIPPED` with an empty Captured Steps table and the soft note
`demo JSON parse error: Expecting value: line 56 column 19`; `reports/demo/goal-desk-iter-34/` and
`reports/phase-goal-desk-iter-34-demo-script.md` did not exist. This left the DoD item
"A `[NEW]`-flagged demo-narrator walkthrough records the fixed disclosure end to end" unmet while
`runs/goal-session-desk/state/blueprint.md` (the `RESOLVED at iter-34` note) stated the walkthrough
"is recorded ... narrated from the actually-rendered post-fix page" — the exact iter-30 failure mode
the spec cited. **Fixed** — see §4, fix 1.

**T5 — IMPORTANT (fixed): the QA report cited a screenshot that does not show the element it
claims to confirm.**
`reports/qa/goal-desk-iter-34-qa.md` cited `QA-desk-topup-reach-section.png` twice as proof that
`showing 20 of 101` renders ("screenshot ... confirms element present and styled correctly"). That
file is byte-identical to `browser-check-01-desk-load.png` (both md5 `1c251af7336153174e17e45d4bb4b8fd`)
and I opened it: it shows the top-of-page BRIEFING table, not the reach block. The claim was true but
the cited artifact does not support it — below the rubric's evidence floor for "UI journey passes"
(row + screenshot showing the acceptance state). **Fixed** — see §4, fix 2.

**T6 — GAP (documented, not fixed): the LLM browser-QA lane's per-test screenshots are blank.**
`UT-01/02/03/06/07-result.png` in `reports/qa/goal-desk-iter-34-evidence/` are five copies of the
same 5,853-byte solid-background image (md5 `00de3a48723423728c32515733aa1059`) with no page content;
I opened `UT-01-result.png` to confirm. Consequently
`reports/phase-goal-desk-iter-34-ui-test-results.llm.md:39`'s clause "verified both visually in the
screenshot and programmatically" is unsupported by its own artifact. The *verdicts* are sound — that
lane also extracted the DOM text and independently re-computed the day grouping from
`curl /research/desk/topup/runs`, and I reproduced both results independently (§3) — so this is
recorded as a GAP rather than an IMPORTANT finding. I did not regenerate another lane's evidence
files; correct captures of the same acceptance state now exist at
`reports/demo/goal-desk-iter-34/step-04.png` and
`reports/qa/goal-desk-iter-34-evidence/AUDIT-J-19-reach-block-verified.png`.

**T7 — OBSERVATION (not fixed): demo narration step 3 misdescribes the rendered line.**
`reports/phase-goal-desk-iter-34-demo-script.md` step 03 narrates "the date **all pairs** reach"
while the rendered line reads `newest recorded reach 2026-07-30 · 303 pairs reach it` (303 of 404).
Showcase copy on a non-gating lane; the point-out text and the four other J-19 steps are accurate.

---

## 3. Domain Assessment

The domain question is narrow and answerable: does `/desk`'s Top-up Runs panel now describe one run
consistently at one precision?

I did not take that on report. I read `topupLibraryReach` (`page.tsx:884-932`) and re-implemented its
grouping in Python directly over the run on disk
(`apps/backend/.data/topup_runs/topup-2026-07-31-8fb5c9a1f737.json`, 404 outcomes, 0 missing
`store_frozen_through_after`):

- **Post-fix (day-truncated key):** newest day `2026-07-30`, `newestCount` **303**; `earlierTotal`
  **101**, every one of them `2026-07-27`. Zero overlap between the reach line's printed day and any
  earlier row's printed day.
- **Pre-fix (raw microsecond key), reproduced from the same file:** newest raw timestamp
  `2026-07-30T19:30:00.000000Z`, count **101**, earlier **303** — and because the newest day carries
  3 distinct timestamps, 202 of those 303 "earlier" rows printed `2026-07-30`, the identical day the
  reach line named as newest. That is exactly the contradiction iter-33's confirm rejected, and it is
  now structurally impossible: the partition key and the rendered string are the same 10 characters.

That independent derivation matches the live page byte-for-byte: the developer's crop
(`UT-J-19-topup-reach-crop.png`) and my own audit-time capture both show
`newest recorded reach 2026-07-30 · 303 pairs reach it`, `Pairs recorded earlier (101)`,
`showing 20 of 101`, and 20 rows `AAPL 1w … C 1w` all dated `2026-07-27` — the same 20 symbols, in
the same order, my Python produced for `earlierAll[:20]`.

The cap is honest by construction rather than by convention: the heading reads `earlierTotal`
(`page.tsx:1030`), the disclosure reads `earlier.length` and `earlierTotal` (`:1034`), and the
disclosure is gated on `earlierTotal > EARLIER_PAIRS_DISPLAY_CAP` (`:1032`) so a run of ≤ 20 renders
nothing new. The `earlierTotal > 0` section gate (`:1027`) is behaviourally identical to the old
`earlier.length > 0` because a cap can never empty a non-empty list. The legacy path is untouched:
`undefined` anywhere still returns `null` (`:892`) and renders `LIBRARY_REACH_NOT_RECORDED`, and an
all-`null` run still returns the honest zero-extreme (`:908-912`).

Anti-goal check: no execution path, no advice language (the sentence is `showing 20 of 101` and
`test_copy_discipline.py` passes unmodified), no new endpoint/field/`Config` key, no second
computation of a contract value — `store_frozen_through_after` is still owned by
`desk_topup_compute.py` and read by exactly one frontend consumer
(`grep -rn store_frozen_through_after apps/frontend` returns only `lib/types.ts:962` and this one
function). No new top-up run was triggered by any audit step: `.data/topup_runs/` still holds the
same two files with unchanged mtimes.

Evidence honesty of the handoffs themselves holds up: the dev handoff's TC-by-TC live-vs-structural
disclosure is accurate — TC-5 (≤ 20 branch) and TC-6 (legacy run) genuinely have no live artifact,
and it says so rather than claiming one.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/phase-goal-desk-iter-34-demo.json` | Replaced the invalid JS regex literal `"name": /newest recorded reach/` (line 56) with the string `"name": "newest recorded reach"`, making the file valid JSON |
| 2 | Important | `reports/qa/goal-desk-iter-34-qa.md` | Corrected two evidence citations that pointed at a top-of-page capture not containing the disclosure; repointed them at the two artifacts that do show it, with an explicit correction note |
| 3 | Important | `reports/demo/goal-desk-iter-34/*`, `reports/phase-goal-desk-iter-34-demo-{results.md,script.md}` | Re-ran the deterministic demo recorder after fix 1, producing the missing `[NEW]`-flagged walkthrough |
| 4 | — | `reports/qa/goal-desk-iter-34-evidence/AUDIT-J-19-reach-block-verified.png` | Added the audit's own live capture of the reach block as citable evidence for fix 2 |

**Verification of fix 1 + 3.** Started the ambient pair myself
(`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 scripts/start-{backend,frontend}.sh`; `/health`
200, `/desk` 200), then:

```
python3 -c "import json,demo_runner as D; d=json.load(open('reports/phase-goal-desk-iter-34-demo.json')); print(D.validate_script(d))"
→ []   (valid JSON, 8 steps, zero schema errors)

python3 incredible_auto_dev/scripts/automation/lib/demo_runner.py \
  --json reports/phase-goal-desk-iter-34-demo.json --mode record --base-url http://localhost:3301 \
  --out-dir reports/demo/goal-desk-iter-34 --results reports/phase-goal-desk-iter-34-demo-results.md \
  --script-fallback reports/phase-goal-desk-iter-34-demo-script.md --phase-id goal-desk-iter-34
→ [demo_runner] recorded 6 step(s) (verdict: RECORDED)     # was: SKIPPED, 0 steps
```

`reports/phase-goal-desk-iter-34-demo-results.md` now lists steps 01-06 with steps 02-05 flagged
`[NEW]` for J-19, and I opened `reports/demo/goal-desk-iter-34/step-04.png`: it shows the reach line,
`Pairs recorded earlier (101)`, `showing 20 of 101`, and exactly 20 rows all dated `2026-07-27` — the
walkthrough is narrated over the actually-rendered post-fix page, satisfying the DoD item and the
iter-33 lesson. I ran only the runner, not `demo-phase.sh`, so the SPEED-21 golden-auto-derive step
did not fire and no golden script was installed by the audit. `git diff --stat` over `apps/` and
`runs/goal-session-desk/journey-scripts/` after my fixes is unchanged from the developer's: no
product code, test, golden script or blueprint line was touched by this audit. The two services I
started were stopped afterwards (`:3301`/`:8301` verified free), and `.data/topup_runs/` still holds
the same two run files with unchanged mtimes — no ambient top-up was triggered, per the spec's
explicit prohibition.

**Independent re-verification of the DoD (not accepted on report).**

| DoD item | How I verified it |
|---|---|
| Day-precision grouping; no same-day pair in "earlier" | Full trace of `page.tsx:884-932` + independent Python re-derivation over the 404 stored outcomes (§3) + live capture |
| ≤ 20 rows, `showing 20 of <true>` only when > 20 | Full trace of `page.tsx:929-1036` + live `showing 20 of 101` with exactly 20 rows in `step-04.png` |
| New guard assertions + seeded counterparts pass | Re-ran `pytest tests/test_desk_topup_library_reach_guard.py tests/test_copy_discipline.py tests/test_desk_ui_guards.py tests/test_desk_hover_tooltip_guard.py tests/test_desk_topup_compute.py tests/test_desk_topup_log.py -q` → **114 passed**; read all four new checks (T1/T2 above) |
| `J-19.json` drops drifting/bug assertions | Read the repointed file end to end (T3 above) |
| J-19 + J-04/J-07/J-09/J-16/J-17 green | Re-ran `demo_runner.py --mode verify` myself against my own `:3301`/`:8301` pair → **6/6 PASS, 0 skipped** (evidence written to the audit scratchpad, not over the pipeline's) |
| Fingerprint / MCP / zero `Config` fields | `Config().config_fingerprint()` → `08e471b10130e1e2`; `pytest tests/test_mcp_server.py` → 39 passed with the `== 17` tool assertion |
| Full backend suite green | Re-ran it myself rather than accept the handoff's figure (QA had cited it "from handoff", not from its own run): `cd apps/backend && .venv/bin/python -m pytest tests/ -q -p no:warnings --tb=short` → **`PYTEST_RC=0`**, progress stream `1520 '.' + 8 's'` = **1528 tests, 0 F/E, 8 skipped**, matching the dev handoff exactly. (No summary line prints because `apps/backend/pyproject.toml:9` already sets `addopts = "-q"`, so the extra `-q` makes it `-qq` — the exit code and the dot count are the evidence.) |
| `[NEW]` demo walkthrough | Was missing (T4); recorded during this audit (fix 3) |
| Blueprint `RESOLVED at iter-34` note | Read the diff; lands in the same working tree as the code, past tense, with the concrete post-fix numbers |

---

## 5. Recommended Next Step

Proceed. The phase goal — a `/desk` Top-up Runs panel that names one calendar day as newest and never
contradicts itself in the list beneath, with an honest disclosure when that list is shortened — is
achieved and independently proven at three levels (stored payload re-derivation, structural guards,
live browser). The remaining gaps need no iteration of their own:

- **F1** (arbitrary 20 of 101) and **T3** (J-19 step 5's environment dependence) are the two worth
  carrying forward as notes, not work items — F1 becomes visible only if a future run's earlier pairs
  span several days, and T3 will announce itself as a J-19 replay failure whose cause is a data
  change, not a regression. Neither justifies a new iteration under the "do not redo" rule.
- **T6** (blank browser-QA screenshots) is a lane-level evidence-hygiene issue rather than a product
  one; if it recurs it belongs in `lessons.md` as "a screenshot the agent never opened is not
  evidence", alongside T4's sharper lesson: **the demo lane silently degrades to `SKIPPED` on a
  malformed script, so a `RESOLVED`/`is recorded` claim must be written after reading
  `demo-results.md`'s verdict line, never before.**
