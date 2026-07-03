# Iteration 6 — Coherence Audit

**Iteration:** goal-tape_to_profit-iter-6
**Date:** 2026-07-03
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this audit

`docs/phases/goal-tape_to_profit-iter-6.md` metadata declares `Frontend Present: no`. The
invocation's snapshot SHA (`14a7ea463f4cc674e1721d253e897cd6178f2277`) is a WIP stash-style commit
that already captured the resumed J-06 implementation before this iteration's dispatch ran (per
the spec's "Resume posture — VERIFY-AND-COMPLETE" note), so `git diff <snapshot-sha>` shows only a
`telemetry.jsonl` update. To audit the actual iteration content I widened the diff to the last
audited baseline, `git diff 9173a7d` (the iter-5 commit, whose `iter-5/coherence.md` verdict was
COHERENCE-PASS). That diff touches exactly: `apps/backend/app/config.py`,
`apps/backend/app/research/{backtests,profiles,routes}.py`,
`apps/backend/tests/{test_backtests_api.py,test_profiles_api.py}`, and new
`apps/backend/tests/test_profile_equivalence.py`. `apps/frontend/`, `apps/backend/app/mcp/`, and
every other module are confirmed zero-diff (`git diff --stat 9173a7d -- apps/frontend` /
`-- apps/backend/app/mcp` both empty). No `reports/phase-goal-tape_to_profit-iter-6-ui-surface-map.md`
exists, consistent with the no-frontend-change declaration.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 33 — Indicator profiles + champion pointer | OK | Single owner `Config.profile_definition` (`apps/backend/app/config.py:984`) / `Config.profile_registry` (`apps/backend/app/config.py:1007`), built from the private `_PROFILE_IDS_IN_ORDER` tuple (`apps/backend/app/config.py:44`). Served ONLY by `GET /research/profiles` → `profiles_projection()` (`apps/backend/app/research/profiles.py:38`) → `CONFIG.profile_registry()`. `POST /research/backtests`'s validation reads the SAME registry — `registry.config.profile_definition(body.profile)` (`apps/backend/app/research/routes.py:1530`) — not a second allowlist. `apps/backend/tests/test_profiles_api.py` asserts `app/research/profiles.py` carries no literal id-string copy. Champion pointer constants (`STRATEGY_V1_ID`, `PROFILE_DEFAULT`) unmoved. |
| Row 31 — Backtest reports (`profile` id + `config_fingerprint` in provenance) | OK | Stamped via `run_config.config_fingerprint()` where `run_config = self._config.resolved_for_profile(params["profile"])` (`apps/backend/app/research/backtests.py:221` terminal report, `:550` queued-time stamp) — the ONE pre-existing `Config.config_fingerprint()` hasher (`apps/backend/app/config.py`, exclusion set updated at the same diff to add `profile_candidate_warmup_min_events` so the new registry-metadata field cannot move any fingerprint), applied to either the identical `default` `Config` object or a `dataclasses.replace()` overlay that never mutates the shared `CONFIG` singleton. `test_profile_equivalence.py:110-129` pins `default` at `4d665603569b9dbf` (unchanged from pre-J-06) and the candidate at a distinct `8c2c0fbf978228e3` — corroborated live in the dev handoff and QA evidence (`reports/phase-goal-tape_to_profit-iter-6-ui-test-results.md` UT-J-06 row). |
| Engine-path exclusivity (supports rows 31/33) | OK | `test_profile_equivalence.py:306-317` (`test_resolved_for_profile_is_called_only_by_the_backtest_runner`) source-scans every `app/**/*.py` file (excluding `config.py`'s own definition) and asserts the only caller is `research/backtests.py` — confirmed by direct grep: the sole non-definition, non-test call sites are `apps/backend/app/research/backtests.py:221,550`. No cockpit/live-tape path resolves a profile. |
| New payload sub-fields (`based_on`, `overrides`) on the row-33 profile descriptor | Not a new entity — OK | These are richer shape on the SAME registered row-33 entity (the profile registry), not a new displayed value; no Data-Contract addition needed, matching the iter spec's explicit "Data-contract additions: None." |

No new function/service/endpoint independently recomputes any registered value, and no new UI
surface fetches a registered value from a non-canonical source (the frontend is zero-diff; the
existing `/performance` registry panel — unchanged since J-05 — already reads
`GET /research/profiles` generically). `test_performance_page_offers_no_profile_selection_control`
(`test_profile_equivalence.py:320-327`) directly asserts the frontend source has no `<select>` and
no hardcoded candidate-id literal.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK | `git diff --stat 9173a7d -- apps/frontend` is empty; `apps/frontend/components/NavBar.tsx` untouched. `GET /research/profiles` and `POST /research/backtests` are pre-existing endpoints on their pre-declared blueprint machine home (IA table rows for J-06/J-03); the read-only display continues to ride the pre-existing `/performance` page with zero page changes, exactly as the iter spec's "Blueprint conformance" section states ("No new surfaces… No Information-Architecture or nav-skeleton change"). |

No new page, no parallel shell, no duplicate home — there is nothing new to reach via navigation
this iteration.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `PROFILE_DEFAULT` moved from `apps/backend/app/research/backtests.py` to
  `apps/backend/app/config.py` (single source now lives beside the new `profile_definition`/
  `profile_registry` methods); `backtests.py` re-exports it for existing importers
  (`apps/backend/app/config.py:32`, re-export confirmed in `apps/backend/app/research/backtests.py`
  diff). This is a consolidation, not a duplication — noted only for the record.
- Reviewer report (`reports/reviews/goal-tape_to_profit-iter-6-review.md`, verdict
  PASS_WITH_NOTES) independently corroborates the single-registry/single-hasher/zero-out-of-scope-
  diff findings above and flags one MINOR test-completeness nit (an assertion could be stronger in
  `test_unregistered_profile_is_422`) — a test-quality item, not a coherence violation.
