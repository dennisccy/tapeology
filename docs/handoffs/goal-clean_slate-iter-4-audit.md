# goal-clean_slate-iter-4 Audit Report

**Date:** 2026-07-24
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

The §0.4 Path B fingerprint epoch bump (J-04) is fully and correctly achieved. Independently
verified against the live code and the production data store — not the handoff — every DEFINITION
OF DONE item holds: exactly the 23 orphaned Config fields are deleted (5 protected fields kept),
the exclusion set is pruned by exactly the 8 named entries (0 others, 0 additions), the new pin
`08e471b10130e1e2` is applied at all 13 enumerated sites plus 1 honestly-discovered candidate-
resolved site, the new-epoch PnL row is appended with byte-identical VALUES beside the untouched
old row, the old literal is retired from source, and the full suite is 1167 passed / 7 skipped /
0 failed / 0 errors. No anti-goal is violated; no CRITICAL or IMPORTANT finding exists. No fixes
were required.

---

## 2. Findings

No CRITICAL or IMPORTANT findings. All findings below are OBSERVATION- or spec-documentation-GAP
level; per the auditor rubric they are documented, not fixed (fixing would be scope creep against
this iteration's "touch only these lines / these 8 entries, nothing else" discipline).

### Backend Findings

**B1 — OBSERVATION (observation): stale prose references to deleted fields in KEPT-code comments.**
`apps/backend/app/research/backtests.py:76` still names the now-deleted `study_null_baseline_seed`
as a design "precedent" in a docstring of the KEPT `backtest_null_baseline_seed` path; similarly
`config.py`'s `backtest_list_max` exclusion comment still cites `journal_list_*`/`study_list_max`/
`hint_log_max` (all deleted) and its `strategy_exit_horizon_seconds` comment still names the
J-01-deleted `excursion_horizons_seconds`. These are pure prose in comments/docstrings for kept
code — zero functional impact (grep-confirmed: no live attribute read of any of the 23 deleted
fields anywhere in `app/`; the only match is this comment). The dev flagged all four in the
handoff's Known Issues, and the codebase already carries precedent for leaving such references
across prior iterations. No fix — surgical scope forbids it and there is no behavioral consequence.

**B2 — OBSERVATION (observation): the retired literal legitimately survives in two exempt places.**
`4d665603569b9dbf` still exists (a) in the policing test that searches for it
(`test_fingerprint_epoch_retirement.py`, self-exempted — the standard `test_no_execution_path.py`
convention) and (b) as immutable historical data inside the uncommitted dev-mode
`apps/backend/tapeology_journal.db` (the preserved old PnL founding row and the 203 pre-existing
backtest reports each keep the stamp they were computed under). Both are correct and required —
the "never touch a historical record" rail mandates the old row keep its old stamp — and neither
is a source straggler. The DoD's "appears nowhere under `apps/`" is satisfied in intent: the
retirement test scopes to source suffixes (`.py/.ts/.tsx/.js`) and confirmed (verified this audit)
that no non-test source file under `apps/` carries the literal.

### Frontend Findings

None. Zero `apps/frontend/` files in scope; `git diff --name-only` confirms no frontend file
changed. `Frontend Present: no` is accurate.

### Test Findings

**T1 — GAP (spec-doc, not code): TC-3's exclusion-set arithmetic is off by one.** The spec/TC-3
states the set goes "48 → 40 (minus 8)". AST-diff of the actual literal at HEAD vs the working tree
shows the real counts are **49 → 41**. The implementation is correct — exactly the 8 spec-named
entries were removed, nothing else, no additions, and every one of the 41 remaining entries names
a live `Config` field (verified programmatically this audit). The dev and QA both caught this and
recorded 41. This is a documentation error in the phase spec's TC-3 arithmetic to correct for
future re-audits, not a defect in the code. No code change.

**T2 — GAP (spec-doc, not code): the spec's I-9 route list over-predicted which routes embed the
stamp.** The spec expected `bars/levels/tradability/setups/taxonomy/edge-report` to each show a
stamp diff. Grepping the serialization code shows `config_fingerprint` enters served bodies only
via `pnl_ledger.py:278` (ledger rows) and `backtests.py:620/1264` (backtest reports); it is used
by levels/tradability/setups/edge-report only as a **cache key**, never emitted in their payload
(`routes.py:236`'s `self._fingerprint` is stored but never serialized). Consequently those routes
being byte-identical to iter-3 after their content-hash caches were busted and recomputed is the
**correct** "no research-value change" outcome — a stronger guarantee than the spec anticipated,
not a stale-cache artifact. The cache-busting suites pass unmodified under the new pin (284-test
targeted run below), independently proving the bust-and-recompute mechanism is live. The dev's
capture header documents this honestly. No code change.

---

## 3. Domain Assessment

The core operation — moving the single most-embedded Data-Contract value (`config_fingerprint`)
across an epoch boundary while every kept research VALUE stays byte-identical — was executed
surgically and honestly. Evidence gathered directly (not from summaries):

- **Field deletions (verified via `dataclasses.fields`):** all 23 deleted names absent; all 5
  protected names (`study_arm_sustain_seconds`, `study_arm_cooldown_seconds`,
  `study_occurrence_r_spread_multiple`, `study_occurrence_r_floor`, `analytics_min_sample_size`)
  present. No live reader of any deleted field remains in `app/` (only the one B1 comment).
- **Exclusion set (verified via AST diff HEAD→working):** 49 → 41; removed set == exactly the 8
  spec-named orphans; added set == ∅; all 41 remaining are live fields. This closes the subtle
  escape-hatch risk of a dropped exclusion silently folding a live field into the fingerprint —
  it did not happen.
- **Pin (verified by live computation):** `Config().config_fingerprint()` → `08e471b10130e1e2`
  (≠ old), reproducible; candidate-resolved → `16d7c98e4fdca755`. Exactly 13 base-pin assertion
  sites + 1 candidate-resolved site carry the new values; every test-file hunk is strictly one
  pin literal flipped, no collateral edits.
- **New epoch row (verified by reading the real `journal.db` store):** exactly 2 ledger rows.
  Old row keeps id `founding-baseline-strategy-v1-default` and stamp `4d665603569b9dbf`; new row
  carries `…-clean-slate` and `08e471b10130e1e2`. Both rows' `net_r`/`net_usd`/`n` are
  byte-identical (`-0.16000000000001136`/1 train, `0.3334000000001356`/1 holdout) and both reuse
  the identical train/holdout dataset ids + checksums (rail-9 REUSE) — only the stamp and the
  freshly-computed backtest ids differ. `pnl-history.md` renders both epochs with §1 byte-
  unchanged and no cross-epoch pooling.
- **Kept-route byte-identity (verified by joining iter-3 vs iter-4 captures):** exactly 2 of 28
  rows differ — `research.pnl_ledger` (new row) and `research.backtests.list` (page-window roll as
  2 new founding backtests entered the cap-100 view); the other 26 are byte-for-byte identical.

The T-14 discovery of a 14th (candidate-resolved) pin site the spec's inventory missed is an honest
inventory correction that strengthened coverage — I recomputed the value live and confirmed it is
the genuine resolved-config hash, not a value contrived to make a red test green.

Frozen-foundations and historical-record rails are intact: `git diff --name-only` shows the only
`app/` file touched is `config.py`; no engine, `sr_*`/`tradability_*`/`setups_*`/edge-report
compute module, MCP, `main.py`, `routes.py`, or frontend file changed; the id/title bump is a VALUE
edit of two pre-existing era-3 fields (net field count fell by 23 — no new field). The guard suites
(`test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, the three chart guards, and the
`test_edge_report_cache`/`test_edge_report_backtest_cache`/`test_tradability_cache` cache guards)
are all byte-identical to HEAD and pass.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found; every DEFINITION OF DONE item verified correct on
first inspection. The minor findings (B1, B2, T1, T2) are OBSERVATION- or spec-documentation-level
and fixing them would be scope creep.

Independent verification runs cited (all this audit, TMPDIR-isolated):

| Check | Command | Result |
|-------|---------|--------|
| Full suite (DoD) | `pytest tests/ -p no:cacheprovider` | 1167 passed, 7 skipped, **0 failed, 0 errors**, exit 0 |
| Retirement + cache-bust + guards + pins | `pytest test_fingerprint_epoch_retirement … test_setups.py` (15 suites) | **284 passed, 0 failed**, exit 0 |
| Base pin | `Config().config_fingerprint()` | `08e471b10130e1e2` (≠ old, stable) |
| Candidate-resolved pin | `resolved_for_profile(...).config_fingerprint()` | `16d7c98e4fdca755` |
| Exclusion-set AST diff | HEAD vs working `excluded` set | 49→41; removed==the 8; added==∅; all live |
| Real ledger read | `JournalStore(...).list_pnl_ledger()` | 2 rows, values byte-identical, old stamp preserved |
| Route capture diff | join iter-3 vs iter-4 by sha | exactly 2 rows differ (both sanctioned) |

---

## 5. Recommended Next Step

Proceed. J-04 is complete and clean — the era's most delicate operation landed with zero collateral
change to any kept value. The next iteration is J-05 (the full sentinel closure: browser walk of
both charts + `/structure` Load + the Case-Studies drill-in decision + the cumulative diff-vs-
inventory cross-check), which requires the real browser pass this backend/keyless iteration
correctly deferred. Two items to carry into J-05 planning (already flagged by the dev, not defects
here): the unresolved `SHOW_CASE_STUDIES = false` flag at `apps/frontend/app/structure/page.tsx:335`
(restore-vs-rescope decision for J-05's Case-Study acceptance clause), and — for spec hygiene only —
correct TC-3's "48→40" to "49→41" and note that the I-9 route list over-enumerated stamp-embedding
routes (only `pnl_ledger` + backtest reports embed it in-body). New pin `08e471b10130e1e2` and new
id/title `founding-baseline-strategy-v1-default-clean-slate` are recorded for iteration 5's planner.
