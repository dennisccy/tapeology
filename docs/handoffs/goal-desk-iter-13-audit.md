# goal-desk-iter-13 Audit Report

**Date:** 2026-07-28
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's two structural fixes both genuinely landed and are independently re-verified: depth
was `full` (demo-narrator ran at 19:21–19:23, before this audit and before the evaluator), and the
capture order was corrected on ONE never-swapped rig (empty frame written 17:02Z → first checkpoint
run written 17:03:23Z → populated frame 17:06Z, all against
`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/desk-iter13-scoped-qa`). Every
deterministic gate holds under my own re-run: fingerprint `08e471b10130e1e2`, suite 1369 passed / 8
skipped / 0 failed, 17-tool MCP contract, 7/7 replay, and the ambient `apps/backend/.data/` tree
byte-identical (400 files) at iteration start, at dev-lane end, AND now after every downstream lane
— a stronger proof than the handoff claimed.

**But the one artifact this iteration exists to produce shipped incomplete.** The `[NEW]`-flagged
walkthrough contained only the populated Top-up Runs state; its opening J-09 step *narrated* an empty
starting point next to a screenshot of three recorded runs — the precise mismatch TC-4 forbids. I
confirmed this by opening the rendered frames, not by reading the reports. I fixed it during this
audit (finding A1), so the artifact now carries both states in sequence from the same scoped root,
with the empty frame's static provenance disclosed inside the artifact itself. Scoring J-09 remains
the evaluator's call, and it should weigh that the closing frame was spliced by the audit rather than
produced by the demo-narrator lane.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified-by-audit): zero product diff is real, not asserted.**
`git diff --stat -- apps/backend/app apps/frontend/app apps/frontend/lib apps/frontend/components
runs/goal-session-desk/journey-scripts` → empty. All 16 named out-of-scope files plus the 8 golden
scripts are untouched (TC-10). `apps/backend/.venv/bin/python -c "from app.config import Config;
print(Config().config_fingerprint())"` → `08e471b10130e1e2` (TC-9), re-run by me, not quoted.

**B2 — OBSERVATION (verified-by-audit): the three checkpoint records match every UI claim.**
QA skipped TC-02, so I read the records directly from
`.../desk-iter13-scoped-qa/.data/topup_runs/`:
`topup-2026-07-28-bad54d19fb21` `state=done 404/404 {fetched: 404}`;
`topup-2026-07-28-a45eb8397844` `state=cancelled 3/404`;
`topup-2026-07-28-c4de94d71e04` `state=done 404/404 {fetched: 403, failed: 1}` with
`{'symbol': 'AAPL', 'timeframe': '1h', 'outcome': 'failed', 'detail': 'no data for that window'}`.
All three carry `config_fingerprint: 08e471b10130e1e2`. The rendered UI text in every populated frame
matches these records exactly — nothing in the screenshots is unbacked by a record on disk.

**B3 — OBSERVATION (verified-by-audit): ambient store untouched, including after QA and demo.**
The dev lane's TC-6 proof stopped at 18:14, but the QA harness started a non-scoped backend on
`:8301` at 18:31 (`fanout-backend-8301.log:1-4`, no scoped-root banner) — a window the handoff's
proof does not cover. I re-checksummed the whole tree at audit time and diffed it against the
iteration-start baseline (`iter13-evidence/ambient-before-data.sha256`): **identical**, 400 files,
`tapeology_journal.db` sha256 `3db3ee7e…` unchanged, no `topup_runs/` directory anywhere in the
ambient tree. The zero-write claim survives the extra scrutiny the handoff did not apply.

### Frontend Findings

**F1 — OBSERVATION: no frontend change to audit.** `/desk`'s Top-up Runs section shipped in
iteration 11 and is byte-unmodified; browser-QA re-verified both states live on the scoped rig via
DOM queries (`reports/phase-goal-desk-iter-13-ui-test-results.md:62-66`), and I independently
confirmed the two states from the rendered images.

### Evidence / Showcase Findings

**A1 — CRITICAL (fixed): the `[NEW]`-flagged walkthrough omitted the honest-empty state, and its
opening step's narration contradicted its own screenshot.**
Pre-fix `reports/phase-goal-desk-iter-13-demo.json:21-64` carried exactly three `journey: "J-09"`
steps (`n:2,3,4`), every one a live click against the already-populated rig. All three rendered
frames were byte-identical (`md5 ac0e34b28ff60fda1c8509586c5201db` for
`reports/demo/goal-desk-iter-13/step-0{2,3,4}.png`) and all three show the populated table. Neither
`UT-J-09-empty-fullpage.png` nor `UT-J-09-empty-topup-section.png` was referenced anywhere in the
demo JSON, script, or results. Sharper than the omission: pre-fix `demo.json:23` narrated *"A
brand-new Desk starts with no runs recorded — an honest, empty starting point"* beside a screenshot
of three recorded runs — a claim unsupported by the image next to it, which TC-4 names explicitly as
the failure mode to avoid. This defeats DEFINITION OF DONE bullet 1, TC-4, and `docs/goal.md:616`'s
"covers the top-up-run disclosure end to end" — the sole reason this iteration was dispatched. The
ux-regression reviewer reached the same conclusion independently
(`reports/phase-goal-desk-iter-13-ux-regression.md:99-145`); nothing upstream of it caught this,
because review, QA, and ui-impact all ran before the demo-narrator lane existed.

*Fix applied (see §4):* inserted a new `n:2` J-09 step showing the honest-empty state, paired with
the developer lane's own same-rig pre-write capture; renumbered the remaining steps 3–15 and shifted
the recorded gallery frames to match (every live frame preserved byte-identically under its new
number — md5s verified before and after); reworded the now-`n:3` step so its narration and point-out
describe what its own frame shows (three recorded runs, one cancelled after 3 of 404 — the pre-fix
point-out called all three "completed", which the `cancelled` row contradicts). The static frame's
provenance is disclosed inside the artifact in three places: a `capture` block on the step itself, a
soft note in `demo-results.md`, and this report.

*Why a splice and not a re-record:* the honest-empty state is a one-way door on an append-only store.
It existed on this rig for 81 seconds (frame captured 17:02Z, first record written 17:03:23Z per
`topup-2026-07-28-bad54d19fb21.json`'s `started_utc`). Re-driving it live would require deleting a
recorded run (forbidden by the append-only rail and by this spec's OUT OF SCOPE) or a second rig
(iteration 12's exact failure, which TC-4's "both drawn from the SAME scoped root" forbids). The
spliced frame satisfies the DoD's own wording literally — "captured on a live, already-booted `/desk`
page BEFORE any run was recorded into the rig."

**A2 — IMPORTANT (fixed): the demo/showcase report did not state the scoped-root path.**
DEFINITION OF DONE bullet 5 and TC-5 require the demo/showcase report AND the browser-QA/evidence
report each to state the absolute scoped-root path in plain text. The browser-QA report does
(`…-ui-test-results.md:180-181`); the QA report does (`goal-desk-iter-13-qa.md:193`); the
smoke-replay report does (`…-smoke-replay-results.md:43`). Pre-fix,
`grep -c "desk-iter13-scoped-qa"` returned **0** for `…-demo-results.md`, `…-demo-script.md`, and
`…-demo.json` alike. Fixed as part of the A1 regeneration: `demo-results.md` now carries a "Scoped
data root (TC-5 disclosure requirement)" section naming the absolute path and the three run ids the
populated frames show, and the path also appears in the new step's `capture.scoped_root`.

**A3 — GAP: the walkthrough's three populated J-09 steps share one frame.**
Post-fix `step-03/04/05.png` remain byte-identical (`md5 ac0e34b2…`) because the runner's clicks
target non-navigating elements at the same scroll depth. Each step's narration is nonetheless
supported by that frame (the run table, the `0 reused · 403 fetched · 1 failed` line, and the failed
pair all appear in it), so TC-4 holds — but the walkthrough shows one view three times rather than
three progressive views. Not fixed: changing what the runner captured would mean fabricating frames.

**A4 — GAP: the Next.js dev-mode indicator overlaps the failed pair's symbol in the live frames.**
In `reports/demo/goal-desk-iter-13/step-0{3,4,5}.png` the bottom-left dev badge covers the first
characters of `AAPL`, leaving `…PL  1h — no data for that window` readable. The detail string —
what steps 4 and 5 actually assert — is fully legible, and the dev lane's own evidence capture
`reports/qa/goal-desk-iter-13-evidence/UT-J-09-populated-topup-section.png` shows the whole line
(`AAPL 1h — no data for that window`) unobstructed, which is what DoD (b) and TC-3 are measured
against. Cosmetic; not fixed.

**A5 — GAP: re-running the demo recorder against this script would silently destroy the fix.**
`demo_runner.py --mode record` writes `out_dir/step-NN.png` for every highlights step, so a re-record
against the (now permanently populated) rig would overwrite `step-02.png` with a populated frame and
re-break A1 without any error. Recorded as a soft note inside `demo-results.md` so the next lane sees
it; a durable framework accommodation (a `static`/`skip_capture` step kind) is out of this
iteration's scope and belongs in `lessons.md`, not here.

### Test Findings

**T1 — IMPORTANT (verified-by-audit): QA passed the phase while skipping the two test cases that
carry J-09's core claims, on a cause the logs only partly support.**
`reports/qa/goal-desk-iter-13-qa.md:63-64` marks TC-02 and TC-03 `SKIPPED`, attributing it
(`:84`) to the QA harness replacing the scoped backend with the ambient one. That did happen at QA
time (`fanout-backend-8301.log` shows a backend on `:8301` with no scoped-root banner, serving three
`/research/desk/topup/runs` GETs before shutting down), but it was not the durable state the report
implies: the browser-QA lane then rebooted the SCOPED rig on the same port
(`browser-qa-backend-8301.log:1-7` shows the
`[desk-iter9-scoped-backend] root=…/desk-iter13-scoped-qa` banner and `TAPEOLOGY_*` env lines), and
both browser-QA (18:52–19:03) and the demo recorder (19:22) ran against the scoped rig with all three
runs present. A QA verdict of PASS resting on "evidence exists on disk" for the journey's two
load-bearing assertions is thinner than the evidence floor for "journey passes". I closed the gap
myself rather than leaving it open: TC-02 is verified in B2 above from the on-disk records, and TC-03
from the rendered images (both states opened and read). Also inaccurate but harmless:
`goal-desk-iter-13-qa.md:197-199` describes the scoped root as containing a top-level `topup_runs/`
directory — it is `.data/topup_runs/`.

**T2 — OBSERVATION: the regression evidence images are deduplicated by construction.**
`J-01/02/03/04/08-verify.png` are one byte-identical image (`md5 c558e49d…`, also identical to
iteration 12's) because those journeys all end on the same `/desk` view. That is the replay lane's
normal behavior, not a copied artifact: the replay's PASS/FAIL comes from the golden steps'
`expect`s, and `reports/phase-goal-desk-iter-13-smoke-replay-results.md:19-25` reports 7/7 with the
J-07 warm-up flake disclosed rather than silently retried (`:61-82`). No finding.

**T3 — OBSERVATION: suite floor and MCP contract hold.** `iter13-evidence/pytest-full.log` ends
`1369 passed, 8 skipped, 2 warnings in 135.84s`; `test_mcp_server.py` 35/35 with `EXPECTED_TOOLS` at
exactly 17 (TC-8, closing J-06 without a browser). I re-ran the fingerprint check myself; I did not
re-run the full suite, since zero source lines changed this iteration and my own fix touches only
`reports/`.

**T4 — OBSERVATION (carried from review): `README.md` carries an uncommitted iteration-12
readme-maintainer edit** that sits in this iteration's working tree and contradicts TC-10's closed
artifact list. Already reported at `reports/reviews/goal-desk-iter-13-review.md:22-35`; content is
accurate and unrelated to product code. Should be committed separately, attributed to its iter-12
origin. Not fixed (not this iteration's work).

---

## 3. Domain Assessment

The domain logic under test — the append-only per-run top-up ledger — was built and proved in
iteration 11 and is byte-unmodified here, so this audit's domain work was to check that the evidence
actually exercises the real code path rather than a synthetic write. It does. The three checkpoint
runs were produced through `DeskTopupComputeManager.trigger()` in-process with only the vendor
adapter doubled (`_NthCallFailsAdapter`-style, copied from `test_desk_topup_compute.py`'s own
fixture), so the ledger, the state machine, and the outcome accounting all ran for real: `cancelled`
is recorded with `pairs_attempted (3) < pairs_total (404)`, the failed pair's `detail` is stored
verbatim rather than normalized to a generic message, and each record independently pins
`config_fingerprint: 08e471b10130e1e2` and `universe_snapshot_id:
universe-2026-07-25-49b33fa31680`. The `/desk` panel's rendered text matches those records field for
field, which is the single-source-of-truth rail holding in practice, not just in a test.

Two honesty properties are worth recording because they are what the walkthrough is supposed to
show, and they survive inspection: the empty state is a genuine absence (`{"runs": [], "latest":
null}` on a rig where `.data/topup_runs/` did not exist), and the failure is a genuine failure
(`"no data for that window"` produced by the adapter double and passed through unaltered). Nothing
in the evidence chain is a placeholder or a mock presented as live — the one substitution anywhere in
this iteration is the vendor adapter, which the spec mandates ("never a live vendor call").

The dev lane's disclosed side effect — checkpoint 3's real walk writing 403 synthetic bar series into
the scoped copy — is confined to the throwaway root and does not perturb what the regression set
reads (`1h/4h/1d/1w` vs the `1m` microscope timeframe the pinned AAPL 2026-06-22 wall uses); the
handoff's live re-check of `resistance 300.11–302.2 class A quality_score 171.0` is consistent with
`docs/goal.md`'s own pinned value, and the replay set passed on that same rig afterward.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `reports/phase-goal-desk-iter-13-demo.json` | Inserted `n:2` J-09 step showing the honest-empty state (`expect: "No top-up runs recorded yet."`, `new: true`) with a `capture` block recording its static provenance, scoped root, and capture time; renumbered the remaining steps to 3–15 |
| 2 | Critical | `reports/phase-goal-desk-iter-13-demo.json` (step now `n:3`) | Reworded the narration that asserted "a brand-new Desk starts with no runs recorded" beside a populated screenshot, and corrected its point-out's "three completed runs" (one is `cancelled`) so both match the frame |
| 3 | Critical | `reports/demo/goal-desk-iter-13/step-*.png` | Shifted the recorded frames to their new numbers (`02→03, 03→04, 04→05, 05→06, 06→07, 10→11, 14→15`; every md5 preserved) and placed the developer lane's same-rig empty capture at `step-02.png` |
| 4 | Important | `reports/phase-goal-desk-iter-13-demo-results.md` | Regenerated via `demo_runner.render_results_md`; verdict now `RECORDED_WITH_NOTES` with two soft notes (static-frame provenance; re-record would clobber it), plus a "Scoped data root (TC-5 disclosure requirement)" section naming the absolute path and the three run ids (closes A2) |
| 5 | Important | `reports/phase-goal-desk-iter-13-demo-script.md` | Regenerated via `demo_runner.render_script_md` from the corrected JSON, so all 15 steps and the four `[NEW]` J-09 tags stay in sync with it |

Nothing outside `reports/` was touched. Originals are preserved at
`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/audit-backup-pre-fix/` (JSON, both `.md`
files, and the pre-fix gallery), and the transformation script at `…/audit_fix_demo.py`.

**Post-fix verification (commands and results):**

- `apps/backend/.venv/bin/python incredible_auto_dev/scripts/automation/lib/demo_runner.py
  --self-test` → `16 passed, 0 failed` (the renderers I regenerated with are healthy).
- `demo_runner.validate_script(json.load(demo.json))` → `OK` (no schema errors after the insert and
  renumber).
- `render_iteration_summary._parse_demo_results(demo-results.md)` → verdict
  `RECORDED_WITH_NOTES`, 9 captured steps parsed with correct numbers/journeys/`is_new` flags, 2 soft
  notes; `_parse_demo_script_narrations(demo-script.md)` → all 15 steps parsed. The downstream HTML
  summary renderer consumes the fixed artifacts without change.
- Frame-mapping proof: md5 of every post-fix gallery file compared against the pre-fix backup — each
  live frame identical under its new number; `step-02.png` md5 `ba131133b8850f90e40315ba69956be1` ==
  `reports/qa/goal-desk-iter-13-evidence/UT-J-09-empty-topup-section.png`.
- I opened both frames rather than trusting filenames: `step-02.png` shows `TOP-UP RUNS` with the ∅
  glyph and "No top-up runs recorded yet.", zero rows; `step-03.png` shows the 3-row table
  (`done 404/404`, `cancelled 3/404`, `done 404/404`), `state: done 404 of 404 pairs attempted
  0 reused · 403 fetched · 1 failed`, and `Failed pairs (1)`. Both carry the identical Screen History
  rows (2026-06-22 / 2026-07-25 / 2026-07-27 with the same provenance strings) — same data root,
  confirming the two frames are the same rig before and after.
- Scope re-check (`git status --porcelain`, `git diff --stat`): my changes touch only the three
  `reports/phase-goal-desk-iter-13-demo*` artifacts and the `reports/demo/goal-desk-iter-13/`
  gallery. Zero product diff still holds; the ambient `.data/` tree re-checksummed after my work is
  still byte-identical to the iteration-start baseline.

No dev-handoff claim was invalidated by these fixes — its "Known Issues" statement that the
demo-narrator lane still had to produce the artifact was accurate when written; that lane then ran,
and this audit repaired its output.

---

## 5. Recommended Next Step

**Proceed to the evaluator with the fixed artifact, and let it score J-09 on the full picture** —
including that the empty half of the walkthrough was spliced by this audit, not produced by the
demo-narrator lane. Every behavioral clause of J-09 was already proved in iteration 11 and re-proved
live here; the remaining question was purely whether the walkthrough shows the disclosure end to end,
and it now does, from one scoped root, in sequence, with each step's narration matching its own
frame.

Three things to carry forward, none of them blocking:

1. **Do not re-run `demo_runner.py --mode record` against
   `reports/phase-goal-desk-iter-13-demo.json`** — it would overwrite `step-02.png` with a populated
   frame and silently re-open finding A1 (A5).
2. **The durable fix belongs in the framework, not in another iteration of this journey:** the
   demo-narrator lane needs a way to declare a step whose frame is a pre-captured static image
   (a one-way-door state an append-only store can never re-render live). Worth a `lessons.md` entry
   for the era's retro; three iterations were spent on a clause that no live-only recorder could
   ever satisfy in a single pass.
3. **Commit the `README.md` iteration-12 leftover separately** (T4) so this iteration's own diff
   matches TC-10's closed list exactly.

The scoped rig is currently **down** (nothing listening on `:8301`/`:3301`; the dev handoff's PIDs
1419904/1421592 are gone). All its data is intact on disk at
`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/desk-iter13-scoped-qa`; any lane that
wants the live page back should use the restart recipe in the dev handoff — and must not click
"Top-up" or "Run Screen" on it, which would append a fourth run and displace the induced-failure run
the walkthrough's populated frames depend on.
