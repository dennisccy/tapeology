# goal-clean_slate-iter-4 Dev Handoff

**Phase:** goal-clean_slate-iter-4
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete

## What Was Built

J-04 (The fingerprint epoch bump — §0.4 Path B), per goal.md's I-4/I-9 and the iter spec's
corrected 23-field delete list. Backend/config/reports only; zero `apps/frontend/` files touched
(matches the spec's own `Frontend Present: no`).

- **Deleted 23 orphaned journal-era `Config` fields** from `apps/backend/app/config.py`: the 14
  corrected-confirmed fields (`verdict_dwell_seconds`, `invalidation_epsilon_spread_multiple`,
  `verdict_timeline_cap`, `management_stance_dwell_seconds`, `checklist_stance_dwell_seconds`,
  `delivery_lag_ok_bound_seconds`, `excursion_horizons_seconds`, `excursion_target_r`,
  `study_null_arm_count`, `study_null_baseline_seed`, `study_list_max`,
  `hint_sustain_dwell_seconds`, `hint_cooldown_seconds`, `hint_log_max`) plus the 9 closure-rule
  finds (`invalidation_k_consecutive`, `journal_list_default_limit`, `journal_list_max_limit`,
  `chase_return_threshold`, `invalidation_too_tight_spread_multiple`, `process_outcome_grade_map`,
  `process_violated_min_failed_checks`, `process_flagged_min_risk_flags`,
  `sound_cue_cooldown_seconds`). Verified via grep before deleting (T-12) that each has zero
  readers outside `config.py` (two fields — `study_null_baseline_seed`, `study_list_max` — had
  prose-only mentions in `backtests.py`/`test_backtests.py` docstrings/comments, not live reads;
  left untouched, see Known Issues). Explicitly did NOT delete `study_arm_sustain_seconds`,
  `study_arm_cooldown_seconds`, `study_occurrence_r_spread_multiple`, `study_occurrence_r_floor`
  (read live by `Config.strategy_definition()` + `backtests.py:225`), or
  `analytics_min_sample_size` (read by `pnl_ledger.py`) — all five still present.
- **Pruned exactly 8 now-orphaned entries** (string + own comment block) from
  `config_fingerprint()`'s `excluded` set: `journal_list_default_limit`, `journal_list_max_limit`,
  `study_list_max`, `management_stance_dwell_seconds`, `checklist_stance_dwell_seconds`,
  `delivery_lag_ok_bound_seconds`, `hint_log_max`, `sound_cue_cooldown_seconds`. Also trimmed the
  THREE sentences in `config_fingerprint()`'s own top-level docstring that named
  `journal_list_default_limit`/`journal_list_max_limit`/`management_stance_dwell_seconds` as
  "EXCLUDED" (those fields no longer exist at all, so the claim would otherwise be actively false
  in the method's own primary documentation) — no other prose elsewhere was touched (see Known
  Issues for the ones deliberately left alone).
- **Bumped `pnl_founding_enhancement_id`/`pnl_founding_enhancement_title`** literal defaults (a
  VALUE edit of two existing era-3 fields, not a new field) to
  `"founding-baseline-strategy-v1-default-clean-slate"` /
  `"founding baseline — strategy v1 on default (post-clean-slate epoch)"`, landed in the SAME
  commit/state as the deletions above, before the pin was computed (T-3 ordering).
- **Computed the new pin ONCE**: `Config().config_fingerprint()` → **`08e471b10130e1e2`**
  (≠ `4d665603569b9dbf`). Reproducible across repeated calls.
- **Updated the 13 verified I-9 pin-assertion sites** to the new pin, touching only those 13 lines
  across `test_timeframe_history_api.py`, `test_levels.py`, `test_tradability.py`,
  `test_backtests.py` (×2), `test_profile_equivalence.py`, `test_pnl_scan.py` (×4),
  `test_edge_report.py`, `test_setups.py` (×2) — confirmed via `git diff --stat` that each of
  these 8 files shows exactly the expected number of 1-line changes and nothing else.
- **Found and fixed a 14th pinned fingerprint literal goal.md's I-9 inventory did not enumerate**
  (see Known Issues / T-14 inventory correction): `test_profile_equivalence.py`'s
  `test_candidate_resolved_fingerprint_is_distinct_from_default` separately pins the
  CANDIDATE-PROFILE-RESOLVED config's fingerprint (a DIFFERENT literal from the base config's,
  since `resolved_for_profile` overlays `warmup_min_events`) — updated `"8c2c0fbf978228e3"` →
  `"16d7c98e4fdca755"` (computed directly, verified distinct from the new base pin).
- **Added `tests/test_fingerprint_epoch_retirement.py`** (new file): asserts the retired literal
  `4d665603569b9dbf` appears in zero files under `apps/` (mirrors the `test_no_execution_path.py`
  `REPO_APPS`/`_SKIP_DIRS`/`_SOURCE_SUFFIXES` scan convention — naturally satisfies the T-11
  exemption since `reports/**`/`runs/**`/`docs/goal-archive/**` live outside `apps/`), plus a
  non-vacuousness check and a live-fingerprint-moved sanity check.
- **Ran `python -m app.research.pnl_baseline` for real** against the operator's real dev-mode
  journal DB (cwd=`apps/backend`). Result: `founding baseline row appended:
  'founding-baseline-strategy-v1-default-clean-slate'` (created=True, NOT "already present").
  Directly verified via the store: the OLD row is byte-identical (same id, fingerprint
  `4d665603569b9dbf`, net_r/net_usd/n, dataset ids/checksums) and the NEW row carries the new
  fingerprint with net_r/net_usd/n IDENTICAL to the old row's values — the VALUES never moved,
  only the stamp. Both founding datasets hit the `DatasetAlreadyRegistered` REUSE path (dataset
  store stayed at 18 registered files throughout — confirmed via file-mtime inspection, no new
  file created, rail 9 intact).
- **Regenerated `reports/pnl/pnl-history.md`** via `python -m app.research.pnl_history` (no
  `--append-report`): section 1 (old id, old fingerprint, unchanged numbers) is byte-identical to
  the pre-iteration file (diffed directly); a new section 2 renders the new-epoch row; train/
  holdout are never pooled across the two sections.
- **Idempotency re-verified**: running `pnl_baseline` a second time printed "already present ...
  nothing was appended" and exited 0 — ledger row count stayed at 2, dataset count stayed at 18.
- **Re-captured the I-9 kept-route byte comparison** against
  `runs/goal-session-clean_slate/iter-3/kept-route-after.txt`, written to
  `runs/goal-session-clean_slate/iter-4/kept-route-after.txt` (28 routes). Result: 26 of 28 rows
  byte-identical; the 2 that differ (`research.pnl_ledger`, `research.backtests.list`) are both
  fully explained and attributed to this journey's OWN required actions, not a code regression —
  full explanation in the capture file's header comment and in Known Issues below.

## Files Changed

- `apps/backend/app/config.py` — deleted 23 fields; pruned 8 exclusion-set entries + 3 stale
  docstring sentences naming them; bumped `pnl_founding_enhancement_id`/`_title` literal defaults.
- `apps/backend/tests/test_timeframe_history_api.py` — 1 fingerprint-pin line updated.
- `apps/backend/tests/test_levels.py` — 1 fingerprint-pin line updated.
- `apps/backend/tests/test_tradability.py` — 1 fingerprint-pin line updated.
- `apps/backend/tests/test_backtests.py` — 2 fingerprint-pin lines updated.
- `apps/backend/tests/test_profile_equivalence.py` — 1 base-fingerprint-pin line updated PLUS the
  1 additional candidate-resolved-fingerprint-pin line (the discovered 14th site).
- `apps/backend/tests/test_pnl_scan.py` — 4 fingerprint-pin lines updated.
- `apps/backend/tests/test_edge_report.py` — 1 fingerprint-pin line updated.
- `apps/backend/tests/test_setups.py` — 2 fingerprint-pin lines updated.
- `apps/backend/tests/test_fingerprint_epoch_retirement.py` — new file (3 tests).
- `reports/pnl/pnl-history.md` — regenerated (old section byte-unchanged; new section 2 added).
- `runs/goal-session-clean_slate/iter-4/kept-route-after.txt` — new I-9 byte-comparison capture.
- `runs/goal-clean_slate-iter-4/status.json` — `current_step: dev_complete`.
- The real dev-mode `apps/backend/tapeology_journal.db` gained one new PnL-ledger row and 2 new
  backtest reports (the `pnl_baseline` run's own required, expected mutation — not a code file,
  not committed).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **1167 passed, 7 skipped, 0 failed, 0 errors** (was 1164 passed / 7 skipped pre-iteration;
+3 net from the new retirement-test file).

Sequence followed:
1. Deleted the 23 fields + pruned the exclusion set + bumped the id/title (all landed together
   before computing the pin — T-3).
2. Computed the new pin once: `08e471b10130e1e2`.
3. Updated the 13 known I-9 sites — re-ran the full suite — found ONE more failure
   (`test_profile_equivalence.py::test_candidate_resolved_fingerprint_is_distinct_from_default`,
   pinning a candidate-resolved fingerprint under a literal the base-fingerprint grep never would
   have surfaced). Fixed it (see Known Issues). Re-ran — green.
4. Added the retirement test — green (3/3).
5. Ran `pnl_baseline` for real, regenerated `pnl-history.md`, ran the idempotency check.
6. Re-captured the I-9 kept-route comparison against a freshly-started backend
   (`bash scripts/start-backend.sh`, cwd=`apps/backend`, port 8301).
7. Ran the full suite one final time after the complete diff — 1167 passed, 7 skipped, 0 failed.
8. Explicitly re-ran the named guard/cache-busting suites together as a final spot-check:
   `test_cockpit_chart_upgrade.py test_structure_chart_viewport.py
   test_price_chart_confluence.py test_no_execution_path.py test_no_credential_in_artifacts.py
   test_edge_report_cache.py test_edge_report_backtest_cache.py test_tradability_cache.py
   test_setups.py` → **145 passed, 0 failed**. `git status` confirms none of the 3 chart guard
   files, `test_no_execution_path.py`, or `test_no_credential_in_artifacts.py` appear in the diff
   — byte-unmodified, as required.
9. `python -m pytest tests/test_pnl_ledger.py tests/test_pnl_ledger_api.py tests/test_pnl_scan.py
   tests/test_pnl_history.py` → 63 passed (TC-10: the id/title bump doesn't break either file —
   both read `CONFIG.pnl_founding_enhancement_id` dynamically, never a hardcoded string).

## Known Issues

**T-14 inventory correction — a 14th fingerprint pin site goal.md's I-9 did not enumerate.**
`test_profile_equivalence.py::test_candidate_resolved_fingerprint_is_distinct_from_default`
(line 136) hardcodes the CANDIDATE-PROFILE-RESOLVED config's fingerprint as a literal
(`"8c2c0fbf978228e3"` before this iteration) — a value DERIVED FROM but DISTINCT FROM the base
`Config().config_fingerprint()` value, since `resolved_for_profile(PROFILE_CANDIDATE_FASTER_WARMUP)`
overlays `warmup_min_events` before hashing. Because this is a different literal than
`4d665603569b9dbf`, grepping for the retired base pin (TC-5's own check, and I-9's "13 verified
sites" enumeration) would never have surfaced it — it only showed up as a genuine, unavoidable
test failure once the base config's other fields changed (the resolved-candidate hash is a pure
function of the base config plus the one overlay, so it necessarily moves whenever the base
config's hashed payload changes). I verified this is not a bug: computed
`CONFIG.resolved_for_profile(PROFILE_CANDIDATE_FASTER_WARMUP).config_fingerprint()` directly,
confirmed it prints `16d7c98e4fdca755` (distinct from the new base pin `08e471b10130e1e2`,
matching the test's own adjacent assertion that the two must differ), and updated the literal to
that computed value. This is the exact "inventory contradiction, documented correction, never a
silent improvisation" discipline T-14 calls for — flagging prominently here since it changes the
"13 verified pin sites" count to 14 for any future re-audit of this file.

**Exclusion-set arithmetic in the phase spec (cosmetic, non-blocking).** TC-3 states the pruned
exclusion set should contain "exactly 40 entries (48 today minus these 8)". Direct AST-based
counting of the CURRENT (pre-iteration) `excluded = {...}` set literal found **49** entries, not
48 — so post-prune the set correctly contains **41**, not 40. This looks like a simple off-by-one
in the spec's arithmetic (49 − 8 = 41), not a sign of a missed/extra entry: I verified
independently that exactly the 8 named entries were removed and every one of the 41 remaining
entries names a field still present on `Config` (checked programmatically). No code change
resulted from this — it's a documentation-accuracy note for whoever next edits the phase spec or
goal.md's I-9/TC-3 text.

**Two intentionally-left-alone stale prose references (not fixed, out of scope).** (1)
`config.py`'s `backtest_list_max` exclusion-entry comment still says "Same iter-12 page-size
precedent (``journal_list_*`` / ``study_list_max`` / ``hint_log_max`` above)" — all three cited
precedent names are now-deleted fields. (2) `backtests.py`'s docstring and
`test_backtests.py`'s comment each still name `study_null_baseline_seed` (deleted) as a design
precedent, and `config.py`'s `strategy_exit_horizon_seconds` comment still names
`excursion_horizons_seconds` (deleted, in J-01) as a calibration reference. All four are pure
prose in comments/docstrings for KEPT code (backtest_list_max, strategy_exit_horizon_seconds,
backtest_null_baseline_seed) — no functional impact, and this matches the codebase's own
pre-existing precedent of leaving such references (e.g. a KEPT field's docstring at
`study_occurrence_r_spread_multiple` already named the J-01-deleted `excursions.py` module by
name, unfixed through iterations 2 and 3). Left untouched per the plan's explicit "touch only
these 13 lines / these 8 entries, nothing else" scoping and the "do not refactor unrelated code"
rule; flagging for whoever eventually does a prose-cleanup pass.

**I-9 recapture operational note.** The first live-capture attempt (against a backend that had
been up for a while, having already served earlier requests during this iteration's own manual
verification) stalled indefinitely on one of the large computed routes (most likely
`/research/setups/...` recomputing under the invalidated durable setups-scan cache — the fresh
fingerprint busts that content-hash cache exactly as designed, but the resulting real-corpus
recompute on this dev machine's full registered panel took long enough to hang a normal request).
Killing that backend and starting a **fresh** one (`bash scripts/start-backend.sh`) immediately
resolved it — the full 28-route capture then completed cleanly with a 25s per-route client
timeout and zero timeouts triggered. This reads as a stuck/lingering server-side computation from
the earlier session, not a defect in this iteration's code: the exact same routes captured
byte-identically to iter-3 once the server was restarted clean, and the existing content-hash-
cache-busting unit tests (`test_setups.py`, `test_tradability_cache.py`,
`test_edge_report_cache.py`, `test_edge_report_backtest_cache.py`) all pass unmodified,
independently proving the busting mechanism itself is sound.

**The 2 sanctioned I-9 kept-route diffs.** `research.pnl_ledger` and `research.backtests.list`
differ from iter-3's capture — both fully explained (with direct evidentiary verification, not
just an assertion) in `runs/goal-session-clean_slate/iter-4/kept-route-after.txt`'s header
comment: the ledger gained the one required new-epoch row (old row byte-identical incl. its old
stamp; new row's VALUES identical to the old row's, only the stamp differs); the backtests list
(capped at the pre-existing, unrelated `backtest_list_max`=100, most-recent-first) rolled its 2
oldest entries off the page as the 2 new founding-row backtests were added — the 2 rolled-off
reports still exist in the store untouched, simply outside the served "100 most recent" window.
Every other kept route (26 of 28) is byte-for-byte identical to iter-3's capture.

**Carried forward, unrelated to J-04 (unchanged from prior iterations):**
`SHOW_CASE_STUDIES = false` (`apps/frontend/app/structure/page.tsx:335`) — still unresolved, still
J-05's concern, not touched this iteration.
