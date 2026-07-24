# goal-clean_slate-iter-6 Audit Report

**Date:** 2026-07-24
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The interlude's closing demolition is genuinely complete and correct: the 5 orphaned Pydantic
request-body classes are gone (pure 67-line subtraction, nothing else touched), the new guard test
is a sound structural AST check that I independently proved would have caught the real residue, and
every deterministic gate (full suite 0-failed, fingerprint pin, 15 byte-identical guard/chart files,
orphan sweep, README, history-freeze) holds up under firsthand re-verification. The one gap: an
**undeclared change to the `J-05.json` golden replay script** (`default_timeout_ms` 20000→30000) that
appears in neither `changed_files`, the dev handoff, nor the crosscheck's "zero out-of-inventory
changes" accounting — a defensible test-infra tuning (it accommodates a documented 13–25 s
stop-watching settle; no assertion was weakened), but an out-of-scope, unaccounted-for edit worth
recording rather than silently committing.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): guard matches any function parameter, not strictly a route-handler parameter**
`test_routes_no_orphaned_request_models.py:50-65` (`_parameter_referenced_class_names`) walks *every*
`FunctionDef`/`AsyncFunctionDef` in the module and treats a `BaseModel` class as "referenced" if it is
annotated on *any* function parameter, not specifically a live route-handler parameter (the docstring
says "live route-handler parameter"). This is conservative and safe — it can only *under*-report
orphans (a class used solely by a dead helper's parameter would escape), never falsely flag a live
one — and all 4 kept classes are in fact real route bodies (`body:` at `routes.py:299/521/1069/1270`),
so today it is exactly correct. Related latent limitation: because the check keys on *parameter*
annotations only, a future response-model `BaseModel` used solely in a `-> X` return annotation would
be false-flagged as an orphan. Neither is a defect for this iteration (there are no such classes); no
fix applied (fixing would be scope creep on a passing, well-designed guard).

**B2 — GAP (observation, not fixed — pre-existing, out of scope): stop-watching 13–25 s settle**
The ux-regression report (`reports/phase-goal-clean_slate-iter-6-ux-regression.md:57-91`) documents
that the cockpit "Stop watching" reset reaches "No ticker watched" only after ~13–25 s on an isolated
retest. I confirmed this is **not** caused by this iteration: the `DELETE /watch/{ticker}` handler
lives in `apps/backend/app/main.py`, a different file from this iteration's only source edit
(`app/research/routes.py`), and `git diff HEAD -- app/main.py` is empty. Correctly out of scope for a
zero-frontend-diff cleanup iteration; carried forward for a future root-cause pass. Directly relevant
to finding T1 below (it is why the replay timeout was raised).

### Frontend Findings

**F1 — (no finding): zero frontend source changed, verified**
`git diff HEAD --stat` shows no `.tsx`/`.ts` file changed; `StructureChart.tsx` and `PriceChart.tsx`
are byte-identical (T-8 veto-class satisfied), corroborated by the 3 chart-guard suites showing 0
diff-lines and passing. Nav single-source (`app/meta.py` `UI_ROUTES`) unchanged. No frontend defect.

### Test Findings

**T1 — GAP (not fixed by design): `J-05.json` golden replay modified but undeclared**
`runs/goal-session-clean_slate/journey-scripts/J-05.json` was changed this iteration —
`default_timeout_ms` `20000`→`30000` (`git diff HEAD` confirms; the file is `M` in the working tree).
This edit is **absent from all three accounting artifacts**: `status.json` `changed_files` (lists only
`routes.py`, the new guard test, and the crosscheck), the dev handoff's "Files Changed" section, and
the iter-6 crosscheck — which explicitly claims *"this iteration's own diff is exactly ONE tracked-file
modification … plus ONE new untracked test file"* and enumerates `telemetry.jsonl`/`trace.jsonl` as the
only other writes while omitting `J-05.json`, so its "zero out-of-inventory changes" conclusion is
technically overstated.

Assessment (why this is a GAP, not IMPORTANT/CRITICAL):
- **Not an assertion weakening.** Every text expectation in the script is intact (`Buyer Control`,
  `Logical 30s bars built live from the tape.`, `No ticker watched`, `300.11`, `case-drillin`,
  `Structure`). Only the patience window widened. A broken flow that never reaches the target text
  would still fail at 30 s — increasing a timeout cannot make an incorrect flow pass, so it does not
  weaken the correctness gate (distinct from §4's "disabling/weakening a gate to go green").
- **It has a real reason.** Step 5 (Stop watching → "No ticker watched") uses the default timeout, and
  finding B2 documents that exact step taking 13–25 s to settle; at the old 20 s default the replay
  would intermittently false-fail. The bump tolerates a documented, pre-existing, out-of-scope UX
  slowness rather than masking a product regression from this iteration (deleting 5 inert Pydantic
  classes has zero runtime effect).
- **Not a veto-class "historical record" violation.** The goal.md anti-goal freezes destruction of
  *records* under `runs/goal-session-*` (delivered reports, past iter-N dirs, ledgers); its own
  operationalization, TC-17, protects `iter-0..iter-5`, `goal-archive/`, and `pnl-history.md` — not the
  live `journey-scripts/`, which are actively maintained working assets (the spec itself calls J-05.json
  "now-fuller … the fuller walk landed at iter-5", i.e. iter-5 modified it), and `telemetry.jsonl`/
  `trace.jsonl` under the same tree are pipeline-written every iteration. A timeout widening is not a
  delete/rewrite/truncate of a record.

**No fix applied, deliberately.** Reverting 30000→20000 to restore byte-identity would risk
reintroducing the intermittent replay false-fail that finding B2 explains, trading a documented GAP for
a flaky-test IMPORTANT issue (the post-fix rule forbids fixes that introduce a new finding); and the
"correct" fix — root-causing the slow stop — is explicitly out of this iteration's scope. Recommended
handling: when this iteration is committed, **declare** the `J-05.json` timeout change (add it to the
change record) rather than let it ride in silently, or intentionally revert it with a note if the team
prefers the golden frozen.

**T2 — (verification note, not a defect): deterministic J-05 golden replay deferred, but J-05 states are evidenced**
QA deferred the deterministic replay of `J-05.json` itself (TC-9) to the closure lane; the deterministic
runner logged only J-02 (`regression-replay-results.md`, 1/1). However J-05's acceptance is genuinely
evidenced via the browser-qa-agent's live walk: UT-03 covers steps 1–5 (Watch→"Buyer Control",
bar-size→caption, Stop→"No ticker watched") and UT-04 covers steps 6–10 (Load→"300.11", row-click→
`case-drillin`), all PASS with screenshots (`UT-03-*.png`, `UT-04-load-result.png`,
`UT-04-drillin-dom-text.txt`), 12/12 browser QA. Per rubric §5 this clears the "UI journey passes" floor
(results row + acceptance-state screenshot). J-05 is legitimately `passing`.

---

## 3. Domain Assessment

The core deliverable — a **durable structural guard against the "orphaned request-body class" defect
class** — is high quality and I verified its soundness firsthand rather than trusting the handoff:

- The production test parses `routes.py`'s own AST, collects every top-level `class X(BaseModel):`, and
  subtracts the set of class names annotated on any function parameter — it **never names a deletion
  target as a string**, correctly applying iter-2's carried lesson so it cannot go stale after a future
  deletion.
- I ran the guard's own `_orphaned_model_classes` against the **real pre-cleanup file**
  (`git show HEAD:…/routes.py`) and it returned exactly
  `['ActionRequest', 'ResolveRequest', 'ReviewRequest', 'StudyRequest', 'ThesisRequest']` — the strong
  form of TC-4 ("would have caught the actual residue"), stronger than the committed synthetic-module
  test alone.
- The deletion is a clean subtraction: `git diff HEAD -- routes.py` is 67 deletions / 0 insertions,
  removing precisely the 5 named classes and their docstrings, blank-line convention preserved, all 4
  kept classes and `get_study_market_adapter` (the genuine J-01 relocation, live consumer
  `record_dataset`) untouched.
- The expanded orphan sweep is honest: every one of the 4 residual symbol hits
  (`routes.py:160`, `edge_report.py:40`, `test_research_store.py:5`, `main.py:150`) is a docstring/comment
  narrating the historical removal — I read each in context; zero live references.

The `config_fingerprint()` stayed pinned at `08e471b10130e1e2`, and the 15 guard/chart/fingerprint-pin
files are byte-identical (0 diff-lines each) — the "frozen foundations" and "no research-value change"
rails hold. The previously-unresolved MINOR anti-goal breach ("Deletion is complete, never cosmetic")
is now genuinely closed and durably guarded.

### Independent verification ledger (firsthand this audit)

| TC | Claim | How I checked | Result |
|----|-------|---------------|--------|
| TC-1 | 5 classes grep-gone | `grep -c` on routes.py | `0` ✓ |
| TC-2 | 4 kept classes referenced | occurrence count + `body:` param lines 299/521/1069/1270 | 2 each ✓ |
| TC-3 | no live refs to deleted symbols | grep + read each hit in context | all docstring/comment ✓ |
| TC-4 | guard catches pre-cleanup orphans | ran guard logic vs `HEAD:routes.py` | exactly the 5 ✓ |
| TC-5 | full suite 0 failed | junit-xml parse + 3× exit-0 runs | 1176 tests, 0 failed/err, 7 skip, 1169 pass ✓ |
| TC-6 | fingerprint unchanged | live `Config().config_fingerprint()` | `08e471b10130e1e2` ✓ |
| TC-7/14 | 15 guard/chart/pin files byte-identical | `git diff HEAD` line count per file | 0 on all 15 ✓ |
| TC-8 | 11 deleted modules absent | import grep + file-existence probe | zero / all absent ✓ |
| TC-16 | README clean | `grep -c "pending an operator decision"` | `0` ✓ |
| TC-17 | history untouched | `git diff HEAD --stat` on protected paths | empty ✓ |
| Browser | J-05 states + Edge honest + nav=2 | screenshots + 12/12 QA row read | evidenced ✓ |

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found. The single GAP (T1, undeclared `J-05.json` timeout
edit) is deliberately **not** fixed — reverting risks reintroducing a documented replay false-fail
(finding B2), and per the audit rules GAP/OBSERVATION items are documented, not fixed. B1 and B2 are
observation/out-of-scope and likewise not touched.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied; all findings are GAP/OBSERVATION and documented above. |

---

## 5. Recommended Next Step

**Proceed** — the phase goal is fully achieved: all 5 Must-have journeys of the interlude are
`passing` (J-05 re-certified with browser evidence; J-01–J-04 mechanically re-verified), the demolition
is complete and durably guarded, and no deterministic gate regressed. This closes the last open item
(iter-5 audit finding B1). Whether this constitutes `GOAL_ACHIEVED` is the evaluator's call under the
two-key protocol; nothing in this audit blocks it.

One housekeeping item to hand to the commit/release step (not a blocker): **account for the `J-05.json`
`default_timeout_ms` 20000→30000 change** — either declare it in the change record when committing, or
intentionally revert it. It should not be committed silently, since the iter-6 crosscheck currently
asserts "zero out-of-inventory changes" without listing it. Two pre-existing, correctly-out-of-scope
follow-ups remain logged for a future iteration: root-cause the 13–25 s stop-watching settle
(`app/main.py`), and add a scroll-into-view affordance to the Case Studies drill-in (iter-5's open
recommendation).
