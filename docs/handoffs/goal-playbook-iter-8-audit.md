# goal-playbook-iter-8 Audit Report

**Date:** 2026-08-11
**Auditor:** Hard audit pass — skeptical, evidence-based (re-audit after the fix pass; the first
audit's report was removed before this dispatch, so every claim below was re-derived from code and
executed commands, not from that report)

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-08's pooling math is correct — I re-derived every served statistic with my own arithmetic against
a hand-built fixture (29 checks, including four edge cases the shipped tests do not cover) and it
agrees exactly. The fix pass's store-scope guard is a genuine mechanism, not a launcher: I proved
the gate refuses, prepares, re-asserts, and that a refusal stops **both** browser lanes, then ran
the eight required goldens myself on a freshly seeded rig — **8/8 PASS with the operator's protected
store byte-identical before and after (9,841 files)**. One honesty defect survived every prior lane
and is fixed here: the served register claimed the baseline column covered every signal, which is
false on the operator's own corpus (90 signals vs 32 baseline anchors in one cell).

---

## 2. Findings

> **Naming note.** The previous (deleted) audit's findings were numbered B1 (malformed-date write
> path) and B2 (unscoped replay lane); the dev handoff cites those numbers. Both are re-verified
> CLOSED below under "Carried findings". The numbering in this section is fresh.

### Backend Findings

**B1 — IMPORTANT (fixed): `EVIDENCE_REGISTER` claimed the baseline covers every signal; on the
operator's real corpus it covers a third of them**

`apps/backend/app/research/desk_playbook_evidence.py:98` served this sentence:

> "…beside the pooled baseline — the SAME seeded random anchors **every signal** was already
> measured against…"

That is not what the recorded data contains. In `desk_playbook.py:706-731`, every detected signal
gets a `forward` block and is appended to `record["signals"]`, but a baseline anchor is drawn
**only while that `(setup_id, side)` is still within `DESK_FORWARD_MAX_TOUCHES_PER_ROW` (= 8) for
the session** (`desk_forward.py:134`); the rest are counted in `signals_beyond_cap` and draw
nothing. The evidence fold reads the uncapped `signals` for the signal half
(`desk_playbook_evidence.py:188-192`) and the capped `baseline_anchors` for the baseline half
(`:207-210`), so the two columns are pooled over different sample sets whenever the cap bites.

Measured on the operator's own store (read-only fold, `cache=None`) at the current default
signature `16a2734d10c91ea7`:

| cell | `signal.n` | `baseline.n_baseline` |
|---|---|---|
| `double_top / short / to_close` | 90 | 32 |
| `double_bottom / long / to_close` | 65 | 32 |
| `range_trade / long / to_close` | 46 | 29 |
| `capitulation / long / to_close` | 29 | 23 |

Both counts are served, so the asymmetry is visible — but the register, which is the payload's own
disclosure vehicle and is rendered verbatim at the top of the `/desk` section
(`apps/frontend/app/desk/page.tsx:3926`), asserted the opposite. The iteration's own anti-goal
requires that "the served registers state what was NOT measured". I was unsure between IMPORTANT
and GAP and took the higher level: this is the disclosure surface failing on the actual production
corpus, not a hypothetical.

**Fix applied** (`desk_playbook_evidence.py:98-110`): the clause now reads "…the seeded random
anchors already drawn beside those signals at compute time, one anchor per signal up to each
session's own per-setup-and-side pooling cap, so a cell whose `n_baseline` is smaller than its `n`
is one where that cap was reached and the two columns do not cover the same set of signals."
No served numeric changed; no frontend change was needed (the section renders `data.register`).

Verification of the fix (all executed):
- `pytest tests/test_desk_playbook_evidence.py tests/test_copy_discipline.py` → **46 passed**.
- New regression test `test_b1_a_cell_whose_baseline_pool_is_capped_serves_both_counts_and_discloses_why`
  (`tests/test_desk_playbook_evidence.py:341`) reproduces the shape (5 signals / 2 anchors), pins
  both counts, and asserts the register names the cap. **Counter-proved it can fail**: the pre-fix
  wording scores `disclose the cap? False` while still passing the copy lint — so the old text
  would have failed this test.
- `find_violations(EVIDENCE_REGISTER) == []`, and none of TC-7's six banned words appear.
- Full suite: **2158 passed, 8 skipped, exit 0**; `Config().config_fingerprint()` →
  `08e471b10130e1e2` (unchanged).
- Live on the restored real backend: `GET /research/desk/playbook/evidence` → HTTP 200 in 0.20s
  cold / 0.065s warm, `register discloses cap: True`.

**B2 — GAP: `STORE_SCOPE_PREPARE_CMD` is project-wide but hardcoded to the playbook rig**

`project-extensions/store-scope/store-scope.env:33` declares `STORE_SCOPE_ENABLED=1` for the whole
repo with a prepare command that seeds the *playbook* fixture rig. Correct for this era. For the
next one, the gate will force-swap the QA backend to playbook fixtures and then **let the lane run**,
so an unrelated era's journeys could be verified against playbook fixture data rather than skipped.
The reviewer flagged this as an availability regression; I read the failure mode as the more
serious one (a lane that runs against the wrong fixtures reports PASS). Not fixed — the prepare
target is a per-session decision, not a defect in this iteration's deliverable.

**B3 — GAP: the gate covers the two goal-mode browser lanes; the phase QA agent's own browser pass
is ungated**

`store_scope_require` is called from `browser-qa-phase.sh:250` and `goal-iter-lean.sh:350`. The
`qa` agent's own browser check is not in either path — and in this very iteration it drove `/desk`
against the operator's **real** backend (`reports/qa/goal-playbook-iter-8-qa.md:226`). No harm
occurred: `find apps/backend/.data/{playbook,playbook_runs,playbook_backscan_runs,universe,…}
-type f -newermt "2026-08-11 15:00"` returns nothing, so that pass was read-only. But the page it
drove carries a "Run Backscan" button, which is exactly the click that caused the original breach.

**B4 — GAP (disclosed by dev): a store-scope breach discloses but does not abort.**
`browser-qa-phase.sh:486-503` appends the breach section and emits telemetry, then continues.
Deliberate and documented; recorded so a future decision to make it terminal is a conscious one.

**B5 — OBSERVATION: the source-scan guard the spec asked for was delivered behaviorally.**
IN SCOPE asked for "a source-scan guard test proving … the pooling code never merges two signatures
into one cell". Shipped instead: TC-5 (behavioral) plus a `hasattr`-based no-update/no-delete check
(`tests/test_desk_playbook_evidence.py:436-438`). The rationale is written into
`test_desk_playbook_guards.py`'s docstring and is reasonable; noting the wording deviation only.

**B6 — OBSERVATION: `invalidation_breached.total_count` counts vacuously-unbreached horizons.**
`desk_playbook._invalidation_breached` (`:420-427`) records a horizon this signal could not measure
as `False` ("vacuously False", its own words). The evidence fold sums that verbatim
(`desk_playbook_evidence.py:327-353`), so a horizon's denominator includes signals that never
observed it. Correct relative to the rail, and pre-existing; the evidence payload does not restate
the convention.

### Frontend Findings

**F1 — GAP: the Evidence section never displays the signature it is pooling.**
`PlaybookEvidenceSection` (`apps/frontend/app/desk/page.tsx:3906-3936`) renders the register, the
cells table, the breach table and "Other signatures (listed, never pooled)" — but not
`data.signature`. The page therefore names every signature *except* the one the table is built
from. The served payload carries it; only the render omits it. Not fixed: the spec's "New
information displayed" list does not include it, and adding UI is scope creep — but it is the
natural first item for J-09's iteration.

**F2 — GAP (disclosed by dev): all 270 cell rows + 90 breach rows always render.**
A literal reading of "renders the served cells as a table" and a genuine pass-through, but a tall
section on a real corpus. No filter/collapse was added because "new user actions: none".

### Test Findings

**T1 — OBSERVATION: no unit test covers the `invalidation_breached` fold.** Every shipped test
asserts on `cells`. I verified the fold by hand (3 breached of 8 signals at `1h`, 90 entries =
9 setups × 2 sides × 5 horizons) and it is correct.

**T2 — GAP: the QA report certifies work it did not execute.**
`reports/qa/goal-playbook-iter-8-qa.md` marks carry item 5 ("Replay lane scoped") and "J-08 passes
via browser-qa-agent" as ✓ while its own Browser Checks section shows it ran against the operator's
real backend and never invoked the replay lane; the citations are the dev handoff and the (then
non-existent) audit. Every one of those claims turns out to be **true** — I executed them below —
but the report asserted verification it had not performed, which is the same class of defect the
previous audit's B2 was.

### Carried findings from the previous audit — re-verified CLOSED

| Prior finding | Re-verification (executed this pass) |
|---|---|
| **B1** — plan-read tolerance also made `POST .../backscan/compute` start a phantom job on a malformed date | `GET .../backscan/plan?from=2026-06-2&to=2026-06-24` → **HTTP 200**, `{"dates":[],"total":0,"missing":0}`. `POST .../backscan/compute {"from_day":"2026-06-2"}` → **HTTP 422**, "No job was started and no run-ledger row was written"; ledger row count before = after = 0. Read/write split is in one shared parser (`desk_playbook_backscan._is_calendar_day`). |
| **B2** — the replay lane ran unscoped and wrote into the operator's real store | Closed by a mechanism, verified end to end (§3). |
| **T1** — the baseline half of the fold had no unit coverage | Two tests added (`test_t1_*`); I re-derived their arithmetic independently and both hold. |

---

## 3. Domain Assessment

**The pooling math is right, and I did not take the tests' word for it.** I wrote an independent
fixture harness (`audit_fold.py`, scratchpad) that computes every expectation with its own
median/mean/linear-interpolation-quantile implementation and compares against `fold_evidence`.
**29/29 checks agree**, including four cases the shipped suite does not cover:

- the `below_min_n` **boundary**: `n == 12` is served untagged (`< PLAYBOOK_MIN_N_DISCLOSURE`, not `<=`);
- a record whose signal predates the measurement pass (no `forward` block) is skipped, not crashed
  on, and does not perturb the pool;
- the `invalidation_breached` fold (3 breached / 8 total at `1h`; 90 entries);
- a **warm** cache that must notice a newly appended record file (it does — `n` moves 8 → 9 and the
  warm body equals the cold body byte for byte).

The anti-goals hold structurally, not just by intent:

- **One signature.** `PlaybookStore`'s 2-pin key is `(session_date, playbook_input_signature)`
  (`desk_playbook.py:939-947`), so "every default-signature file" *is* goal.md's "newest record per
  date at ONE signature" — there is no path by which two files for the same date and signature can
  both pool. A second signature planted in the fixture never reaches a cell, on either half.
- **Tag, never filter.** `below_min_n` is a flag; all four statistics stay populated on a tagged
  cell (verified at `n = 2` and `n = 3`).
- **Truncation.** `_collect_measures` is imported verbatim from the rail; the truncated value is
  excluded from the pool and counted (13 kept / 4 excluded, mean unaffected by an `exit_price` of
  999.0). The `to_close`/`mdd_*` trio pools every event with `n_truncated = 0` — the rail's own
  rule, correctly inherited rather than re-invented.
- **Immutable data / no second rail.** `PlaybookEvidenceCache` carries no `update`/`delete`; it is
  stat-keyed `(path, size, mtime_ns)`, and since records are append-only a stat can never drift
  under a cached row. The only new math is `_quartile_stats`; horizons, MDD, truncation and the
  seed discipline are all imported.

**The store-scope guard is a real gate, and I tested the refusal path rather than reading about it.**
- `store-scope.sh require` with nothing on `:8301` → `NOT SCOPED … Connection refused` → ran the
  prepare command → re-asserted → `SCOPED (source_url='fixture-rig-iter8-replay', member_count=20)`.
  The marker discriminates: the operator's real store holds exactly one universe snapshot and its
  `source_url` is the Wikipedia S&P-100 URL, so no fixture prefix can be forged there.
- A refusal genuinely stops **both** lanes: it sets `FRONTEND_AVAILABLE=no`
  (`browser-qa-phase.sh:252`) *before* `replay_lane_partition_and_verify` runs, and the replay is
  gated on `FRONTEND_AVAILABLE == "yes"` (`lib/replay-lane.sh:309`); the LLM dispatch is separately
  skipped via `_bqa_infra_blocked` (`:373-382`). I checked this because the comment claiming it was
  exactly the kind of claim that had already been wrong once.
- The launcher scopes every protected path: `bars`/`universe`/`playbook`/`playbook_runs`/
  `playbook_backscan_runs`/`screen`/`datasets` by explicit env var, and `forward`, `forward_runs`,
  `screen_runs`, `topup_runs`, `index_reconcile_runs` derive from the (scoped)
  `TAPEOLOGY_DESK_UNIVERSE_DIR` through their own `resolve_*` functions.
- `incredible_auto_dev/tests/automation/test-store-scope-guard.sh` → **25 passed, 0 failed**, and
  the whole framework eval suite (`run-evals.sh`) → **152 pass, 0 fail** — both re-run by me.

**The goldens discriminate.** I built fixture-mismatched copies of J-04/J-05/J-06 (wrong date) and
replayed them: **3 journeys, 3 failed**, each at step 2 on the row-scoped selector. The "Capitulation"
static-copy collision that made a false PASS possible is genuinely closed, and the same protection
now covers J-04 and J-06.

**Definition of Done** — every item verified; risk-class items (state/writes/store safety) fully
traced, mechanical items cited:

| # | DoD item | Verification |
|---|---|---|
| 1 | J-08 passes in the browser, one populated + one tagged cell legible | Reviewer PASS + QA row "Evidence Table Data Verification ✓ / TC-08 screenshot"; re-confirmed live on a fresh rig: `open_high_break long 5m n=13` untagged beside tagged low-n cells with numbers served |
| 2 | J-01..J-07 + J-10 still green | **Executed by me**: 8 journeys, 0 failed (verdict PASS) on the scoped rig |
| 3 | No anti-goal violation | Traced (§3); one register overclaim found and fixed (B1) |
| 4 | Suite exit 0, ≥ 2130 passed, 8 skipped, pin `08e471b10130e1e2` | **Executed twice**: 2157/8 pre-fix, **2158/8 post-fix**, exit 0; pin verified directly |
| 5 | Back-scan plan honest 200 on a malformed date | **Executed**: HTTP 200 empty plan; and the write path refuses 422 |
| 6 | `J-06.json` exists and replays green | **Executed**: PASS inside the 8/8 run; and FAILs on a mismatched fixture |
| 7 | Replay lane scoped — zero new files under the real `.data` | **Executed**: `store-scope verify` → **CLEAN**, 9,841 protected files before == after, sizes and mtimes unchanged |
| 8 | Range Trade re-capture delivered | `reports/qa/.../audit-TC-14-range-trade-geometry-preseed-rig.png` exists; reviewer's MINOR stands (taken on the pre-final rig, RTAAA bars unchanged across seed versions) |
| 9 | Dev handoff written | Present, and honest about what the fix pass did and did not do |

**Honesty of the record.** The four artifacts the pre-fix run wrote into the operator's store are
listed in `runs/goal-session-playbook/state/iteration-state.md` and match disk **exactly** (three
playbook records + one back-scan ledger row, all 2026-08-11 14:45). Nothing has been written since:
`find … -newermt "2026-08-11 15:00"` is empty, including across my own pass. The dev also declined
to overwrite the pipeline's FAIL 6/8 replay artifact — the right call.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/research/desk_playbook_evidence.py` | `EVIDENCE_REGISTER`: replaced the false "the SAME seeded random anchors **every signal** was already measured against" with an accurate disclosure of the per-`(setup, side)` pooling cap and what a smaller `n_baseline` means. No served numeric, no schema, no fingerprint change. |
| 2 | Important | `apps/backend/tests/test_desk_playbook_evidence.py` | New `test_b1_…_capped_serves_both_counts_and_discloses_why`: pins `n=5` vs `n_baseline=2` on a capped cell and asserts the register names the cap. Counter-proved it fails on the pre-fix wording. |

Post-fix verification: full suite **2158 passed / 8 skipped / exit 0**; targeted suites 46 passed;
`config_fingerprint()` = `08e471b10130e1e2`; live endpoint serves the corrected register.
Diff re-read — the two edits touch only the register string and the new test; nothing else.

Servers left healthy as found: `:8301` is the operator's **real** backend again
(`source_url = https://en.wikipedia.org/wiki/S%26P_100`, 101 members, `/health` 200), `:3301`
frontend returns 200 on `/desk`, Chrome CDP `:9222` untouched.

---

## 5. Recommended Next Step

**Proceed to J-09.** The phase goal is achieved: the evidence view is correct, honestly disclosed
after B1's fix, and the two ESCALATEs' carry items are closed by executed evidence rather than
prose. Carry into J-09's iteration, in this order:

1. **Scope `STORE_SCOPE_PREPARE_CMD` per goal-session** (B2) before another era inherits a gate that
   swaps in playbook fixtures for unrelated journeys.
2. **Render `data.signature` in the Evidence section** (F1) — one line, and it removes the odd state
   where the page lists every signature except the pooled one.
3. **Extend the gate to the QA agent's own browser pass** (B3), or state explicitly that the phase
   QA lane is allowed to drive the real backend read-only.
4. Optional: a unit test for the `invalidation_breached` fold (T1) and a `signals_beyond_cap`-aware
   count on the payload if the cap asymmetry ever needs to be machine-readable, not just disclosed.
