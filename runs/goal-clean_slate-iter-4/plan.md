# goal-clean_slate-iter-4 Execution Plan

Session `clean_slate`, iteration 4, depth **full**, Mode **next**. Target journey **J-04** ("The
fingerprint epoch bump — §0.4 Path B") — the fourth of five Must-have journeys in "The Clean Slate"
demolition interlude (`docs/goal.md`), and the era's single most delicate operation (it moves the ONE
Data-Contract value every kept route embeds). Required-still-passing this iteration: **J-01, J-02, J-03,
J-05**, all scoped to backend/keyless checks (the I-9 kept-route re-capture + full suite + guard tests;
no browser walk — matches goal.md's own `(Keyless; automated.)` tag on J-04 and iter-1's precedent).
Full acceptance detail, the I-4/I-9 inventory rows, Weak-model traps T-1..T-14, and the TC-1..TC-17
test-first contract live in `docs/phases/goal-clean_slate-iter-4.md` — the developer must read it in
full, including its NOTES section (two load-bearing corrections + a re-seed mechanism discovery, all
already logged to `runs/goal-session-clean_slate/state/assumptions.md`). This plan distills execution
order; it is a guide, not a restatement.

**Alignment check:** J-04 is goal.md's own next journey in the J-01→J-02→J-03→J-04→J-05 order, and
iter-3's evaluator explicitly recommended it next at full depth (`reports/phase-goal-clean_slate-iter-3-
iteration-summary.md`). I independently re-verified this iteration's most load-bearing numeric claims
directly against the live repo (not just trusting the spec's own text) and found **zero drift**:
- All 23 fields on the corrected DELETE list exist in `apps/backend/app/config.py` today.
- All 5 fields the spec says must NOT be deleted (`study_arm_sustain_seconds`,
  `study_arm_cooldown_seconds`, `study_occurrence_r_spread_multiple`, `study_occurrence_r_floor`,
  `analytics_min_sample_size`) exist and are distinct from the delete list.
- The fingerprint literal `4d665603569b9dbf` appears in **exactly 13 assertion lines across exactly 8
  test files** — matching the spec's I-9 map exactly, byte-for-byte, including line numbers.
- All 8 names slated for exclusion-set pruning are present in `config_fingerprint()`'s `excluded` set at
  the claimed lines.
- `pnl_founding_enhancement_id`/`pnl_founding_enhancement_title`'s current literal values match the
  spec's description (`"founding-baseline-strategy-v1-default"` / `"founding baseline — strategy v1 on
  default"`), confirming the re-seed collision the spec's Correction 2 describes is real and the fix is
  necessary.
- Spot-checked `len(store.list_pnl_ledger()) == 1`-style assertions across `test_pnl_ledger.py`,
  `test_pnl_scan.py`, `test_pnl_history.py`: all operate on isolated `tmp_path`/fresh-store fixtures, not
  the real production ledger — so the real ledger going from 1 row to 2 rows this iteration cannot
  contradict them. No hidden landmine there.

No scope creep found: the phase spec's OUT OF SCOPE section matches goal.md's Non-Goals verbatim (no new
Config fields beyond the id/title VALUE bump, no engine/chart/MCP/frontend touch, no schema surgery); zero
`apps/frontend/` files are in scope, matching the spec's own `Frontend Present: no` metadata.

## What to Build

**Critical ordering constraint (T-3 — read before starting):** all of `config.py`'s edits (the 23-field
deletion, the 8-entry exclusion-set prune, and the enhancement-id/title value bump) must land together in
one state, and the new fingerprint must be computed **exactly once** from that final state, before any of
the 13 pin sites are touched. Computing/pinning twice is itself a T-3 violation. Sequence strictly:

1. **`apps/backend/app/config.py` — delete 23 fields**, verifying each via `grep -rln <field> app/ tests/`
   returns only `config.py` immediately before deleting it (T-12):
   - The 14 corrected-confirmed fields: `verdict_dwell_seconds`, `invalidation_epsilon_spread_multiple`,
     `verdict_timeline_cap`, `management_stance_dwell_seconds`, `checklist_stance_dwell_seconds`,
     `delivery_lag_ok_bound_seconds`, `excursion_horizons_seconds`, `excursion_target_r`,
     `study_null_arm_count`, `study_null_baseline_seed`, `study_list_max`, `hint_sustain_dwell_seconds`,
     `hint_cooldown_seconds`, `hint_log_max`.
   - The 9 additional closure-rule finds: `invalidation_k_consecutive`, `journal_list_default_limit`,
     `journal_list_max_limit`, `chase_return_threshold`, `invalidation_too_tight_spread_multiple`,
     `process_outcome_grade_map`, `process_violated_min_failed_checks`, `process_flagged_min_risk_flags`,
     `sound_cue_cooldown_seconds`.
   - **Do NOT delete** (verified live readers outside `config.py`): `study_arm_sustain_seconds`,
     `study_arm_cooldown_seconds`, `study_occurrence_r_spread_multiple`, `study_occurrence_r_floor`
     (read by `Config.strategy_definition()` + `backtests.py:225`), `analytics_min_sample_size` (read by
     `pnl_ledger.py`).
2. **Same file, same commit — prune `config_fingerprint()`'s `excluded` set** of exactly these 8 now-
   orphaned entries (string + its comment, nothing else): `checklist_stance_dwell_seconds`,
   `delivery_lag_ok_bound_seconds`, `hint_log_max`, `journal_list_default_limit`,
   `journal_list_max_limit`, `management_stance_dwell_seconds`, `sound_cue_cooldown_seconds`,
   `study_list_max`. The other ~40 entries are untouched (unrelated live era-3/4/5B/5C fields).
3. **Same file, same commit — bump** `pnl_founding_enhancement_id` and `pnl_founding_enhancement_title`'s
   literal defaults to a new, distinct, self-documenting pair (e.g.
   `"founding-baseline-strategy-v1-default-clean-slate"` /
   `"founding baseline — strategy v1 on default (post-clean-slate epoch)"` — exact bytes not
   load-bearing). This is a VALUE edit of 2 existing fields, not a new field.
4. **Compute the new pin once**: `python -c "from app.config import Config;
   print(Config().config_fingerprint())"`. Record the printed value — it is needed for the dev handoff
   and for step 5.
5. **Update all 13 assertion sites to the new pin** (locate each by the
   `CONFIG.config_fingerprint()`/`Config().config_fingerprint()` assertion symbol, not by line number —
   lines may have drifted since planning):
   - `test_timeframe_history_api.py` (1), `test_levels.py` (1), `test_tradability.py` (1),
     `test_backtests.py` (2), `test_profile_equivalence.py` (1), `test_pnl_scan.py` (4),
     `test_edge_report.py` (1), `test_setups.py` (2). Touch only these 13 lines — nothing else in any of
     these 8 files.
6. **Add one new test** (new small file, e.g. `tests/test_fingerprint_epoch_retirement.py`, or any kept
   module) asserting `4d665603569b9dbf` appears in zero files under `apps/` (code + tests) —
   `reports/**`/`runs/**`/`docs/goal-archive/**` exempt (T-11).
7. **Run `python -m app.research.pnl_baseline`** for real (keyless, deterministic, against the operator's
   real dev-mode journal DB — same launch convention iter-1/2/3 used, cwd=`apps/backend`). Expect stdout
   `founding baseline row appended: '<new-id>' ...` (created=True) — never `already present`. Confirm via
   the `DatasetAlreadyRegistered` REUSE path that neither founding dataset is re-recorded (TC-8, rail 9).
8. **Regenerate `reports/pnl/pnl-history.md`**: `python -m app.research.pnl_history` (no
   `--append-report`). Confirm section 1 (old id, old fingerprint, unchanged numbers) stays byte-identical
   and a new section renders the new-epoch row, train/holdout never pooled across the two.
9. **Idempotency check (TC-11):** re-run `python -m app.research.pnl_baseline` a second time — must print
   "already present" / exit 0, nothing appended, proving the guarantee holds for the NEW id too.
10. **Re-run the I-9 kept-route byte-comparison capture** against
    `runs/goal-session-clean_slate/iter-3/kept-route-after.txt`; write
    `runs/goal-session-clean_slate/iter-4/kept-route-after.txt`. Every fingerprint-embedding route
    (bars/levels/tradability/setups/backtests/pnl-ledger/edge-report/taxonomy) must differ **only** in the
    stamp substring — zero other byte.
11. **Run the full backend suite** — 0 failed, 0 errors — plus explicitly re-confirm byte-unmodified: the
    3 chart guard suites (`test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`,
    `test_price_chart_confluence.py`), `test_no_execution_path.py`, `test_no_credential_in_artifacts.py`,
    and the content-hash-cache-busting suites (`test_edge_report_cache.py`,
    `test_edge_report_backtest_cache.py`, `test_tradability_cache.py`, `test_setups.py`).
12. Dev handoff at `docs/handoffs/goal-clean_slate-iter-4-dev.md`, **explicitly recording the new
    fingerprint pin value and the new enhancement-id/title chosen** (iteration 5's planner needs both
    without re-deriving).

## Out of Scope (carried from the phase spec — do not relitigate)

- J-05's full sentinel closure (browser walk of both charts + `/structure` Load + Case Studies drill-in +
  cumulative diff-vs-inventory cross-check) — reserved for iteration 5. This iteration only advances J-05's
  backend/keyless sub-clauses.
- Any `Config` field not on the corrected 23-field list — every `sr_*`/`tradability_*`/`setups_*`/
  edge-report/engine/classifier field, every I-4 KEEP-DANGER field, and the 5 explicitly-excluded
  study_*/analytics fields — all untouched.
- `pnl_ledger.py`'s writer and `store.py`'s `enhancement_id` PRIMARY KEY / `DuplicateEnhancementError`
  discipline — untouched; the fix is scoped to 2 `config.py` literal values plus running the existing CLI.
- Any store schema change (`_migrate`, `_create_schema`, no v9, no table drop) — J-01's domain, not this
  one.
- `app/mcp/`, `app/main.py`, `app/research/routes.py`, any `apps/frontend/` file — zero touch.
- Restoring `SHOW_CASE_STUDIES` on `/structure` (`apps/frontend/app/structure/page.tsx:335`) — unrelated
  pre-existing flag, still pending for whoever plans J-05.
- Re-tagging, re-recording, or content-perturbing the founding reference datasets — reuse via
  `DatasetAlreadyRegistered` only (rail 9).
- Any edit to `app/engine/` or any `sr_*`/`tradability_*`/`setups_*`/edge-report computation module.

## Agents Required

- backend-data: yes -- all 12 steps above: `config.py` field/exclusion-set/id-title edits, the 13-pin-site
  update, the new retired-literal test, running `pnl_baseline`/`pnl_history`, the I-9 recapture, full
  suite verification.
- frontend-ux: no -- zero `apps/frontend/` files in scope this iteration (matches goal.md's own
  `(Keyless; automated.)` tag on J-04).

(This project's agent roster has one implementation agent, `developer`, covering both areas — see
`.claude/agents/`. There are no separate backend-data/frontend-ux agents to dispatch; one `developer` run
implements the full ordered list above.)

Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/config.py` -- delete 23 fields; prune 8 exclusion-set entries; bump
  `pnl_founding_enhancement_id`/`pnl_founding_enhancement_title` literal defaults (all in one commit,
  before the pin is computed).
- `apps/backend/tests/test_timeframe_history_api.py` -- update 1 fingerprint assertion line.
- `apps/backend/tests/test_levels.py` -- update 1 fingerprint assertion line.
- `apps/backend/tests/test_tradability.py` -- update 1 fingerprint assertion line.
- `apps/backend/tests/test_backtests.py` -- update 2 fingerprint assertion lines only (leave the
  study_*-field assertions at ~194/195/197/198/360/1074 untouched — TC-2 proof the 4-field correction was
  respected).
- `apps/backend/tests/test_profile_equivalence.py` -- update 1 fingerprint assertion line.
- `apps/backend/tests/test_pnl_scan.py` -- update 4 fingerprint assertion lines.
- `apps/backend/tests/test_edge_report.py` -- update 1 fingerprint assertion line.
- `apps/backend/tests/test_setups.py` -- update 2 fingerprint assertion lines.
- `apps/backend/tests/test_fingerprint_epoch_retirement.py` (new, name flexible) -- asserts the old literal
  is absent under `apps/`.
- `reports/pnl/pnl-history.md` -- regenerated via `python -m app.research.pnl_history` (both epochs
  render; old section byte-unchanged).
- `runs/goal-session-clean_slate/iter-4/kept-route-after.txt` -- new I-9 byte-comparison capture.
- `docs/handoffs/goal-clean_slate-iter-4-dev.md` -- new, required; records the new pin + new id/title.
- **Zero diff expected:** `apps/backend/app/mcp/__init__.py`, `apps/backend/app/main.py`,
  `apps/backend/app/research/routes.py`, `apps/backend/tests/test_mcp_server.py`,
  `apps/backend/tests/test_pnl_ledger.py`, `apps/backend/tests/test_pnl_ledger_api.py` (both read the id
  dynamically via `CONFIG.pnl_founding_enhancement_id` per TC-10 — no hardcoded string to update), the 3
  chart guard suites, `test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, every
  `apps/frontend/` file, `app/engine/`, `docs/goal-archive/`, `journal.db`'s existing rows,
  `reports/pnl/pnl-history.md`'s existing §1 content.

## Key Test Scenarios

(Full TC-1..TC-17 wording with exact commands in the phase spec; condensed here.)

- `dataclasses.fields(Config)` output contains none of the 23 deleted names, and does contain
  `study_arm_sustain_seconds`, `study_arm_cooldown_seconds`, `study_occurrence_r_spread_multiple`,
  `study_occurrence_r_floor`, `analytics_min_sample_size` (TC-1).
- `pytest tests/test_backtests.py -q` — 0 failed after the field deletions, with the study_*-field
  assertions against `CONFIG.study_arm_*`/`CONFIG.study_occurrence_r_*` still passing unmodified (TC-2).
- `config_fingerprint()`'s `excluded` set contains exactly 40 entries after the 8-entry prune, every
  remaining name still a live `Config` field (TC-3).
- `Config().config_fingerprint()` prints exactly ONE new value (≠ `4d665603569b9dbf`), computed only after
  all of config.py's edits land together (TC-4).
- `grep -rn "4d665603569b9dbf" apps/backend/tests/*.py` returns zero hits after all 13 sites move together
  (TC-5).
- The new retired-literal test passes: the old pin appears in zero files under `apps/` (TC-6).
- `python -m app.research.pnl_baseline` prints `founding baseline row appended: '<new-id>'`
  (created=True, not "already present"); `GET /research/pnl/ledger` then lists 2 rows — old (byte-
  unchanged) + new (TC-7).
- The founding datasets hit `DatasetAlreadyRegistered` REUSE for both splits — registered-dataset count
  does not increase (TC-8).
- `reports/pnl/pnl-history.md` after regen: §1 byte-unchanged, new section renders the new-epoch row,
  train/holdout never pooled across sections (TC-9).
- `pytest tests/test_pnl_ledger.py tests/test_pnl_ledger_api.py -q` — 0 failed (dynamic id references
  hold) (TC-10).
- Second `pnl_baseline` run — "already present," exit 0, nothing appended (TC-11).
- I-9 recapture vs `iter-3/kept-route-after.txt`: every fingerprint-embedding route differs only in the
  stamp substring; any non-embedding route stays fully byte-identical (TC-12).
- `pytest tests/test_edge_report_cache.py tests/test_edge_report_backtest_cache.py
  tests/test_tradability_cache.py tests/test_setups.py -q` — 0 failed (cache-busting mechanism holds under
  the new pin) (TC-13).
- The 3 chart guard suites — 0 failed, byte-unmodified (TC-14).
- `test_no_execution_path.py` + `test_no_credential_in_artifacts.py` — 0 failed (TC-15).
- Full suite (`pytest tests/ -v`) — 0 failed, 0 errors, literally (TC-16).
- `grep -rn "read_text\|\.open(" apps/backend/tests/*.py | grep -i config` stays zero hits; no NEW failure
  beyond the 13 intentionally-updated pin assertions anywhere in the full-suite run (TC-17).
