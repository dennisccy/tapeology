# Iteration 3 — Coherence Audit

**Iteration:** goal-observation-contract-iter-3
**Date:** 2026-09-04
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

This iteration is backend-only and additive per the blueprint and iter spec: it completes the
in-process half ("source/session descriptor") of the already-registered "Provenance / source /
lifecycle metadata" Data Contract row, and fixes a `_settle` identity bug. No new endpoint, page,
nav entry, or displayed value is introduced; `GET /tape/{ticker}/observation` remains unbuilt
(confirmed absent — see evidence below). Reviewed against the bounded diff
(`runs/goal-session-observation-contract/iter-3/iter-diff.md`), the full new test file
(`apps/backend/tests/test_tape_observation_lifecycle_feed.py`, read directly since the bounded
diff truncated it), `git status --short` (confirms no uncommitted app-level changes beyond the
diff), and the excluded-path `--stat` (confirms only `runs/`/`reports/` harness bookkeeping, no
dependency-lockfile changes). The touched files are exactly: `apps/backend/app/main.py`,
`apps/backend/app/watch_manager.py`, `apps/backend/tests/test_tape_observation_lifecycle_feed.py`
(new), `apps/backend/tests/test_tape_observation_time.py` (mechanical 3-tuple→4-tuple unpack
updates only). All other diff hunks are in the vendored `incredible_auto_dev/` framework tree —
dev-tooling/process files, not Tapeology product surface, so out of scope for IA/Data-Contract
review.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `source.source_mode` | OK | `apps/backend/app/watch_manager.py:139-166` (`_record_source`), single writer; literal parameter at each of the 4 `watch*` constructors (`watch_manager.py:175,260,375` region), never re-parsed from the scenario string |
| `source.data_feed` | OK | `apps/backend/app/watch_manager.py:158` calls the one existing `data_feed_for_scenario` (`apps/backend/app/research/feed_basis.py`); no second scenario-prefix parser — confirmed by the new AST guard `test_no_second_scenario_prefix_parser_outside_feed_basis` (`test_tape_observation_lifecycle_feed.py:614-619`) scanning both touched modules, and independently by my own re-read of the `main.py`/`watch_manager.py` diffs (no `.startswith(` on a scenario string anywhere in either) |
| `source.window_start_utc` / `window_end_utc` | OK | Parsed once in `apps/backend/app/main.py`'s existing `_parse_window_dt`, formatted once by the new `main._iso_utc` (`main.py:266-27`), threaded verbatim into `manager.watch_with_provider`/`watch_with_progressive_historical` (`main.py:401-427` region) and stored verbatim by `_record_source` — no re-derivation at the manager layer |
| `source.dataset_id` / `dataset_checksum` | OK | Always `None` for every `WatchManager`-managed watch (`watch_manager.py:161-162`), matching the blueprint's note that `dataset_replay` is a distinct out-of-manager path; unchanged this iteration |
| `lifecycle.session_id` / `session_started_at_utc` | OK | Minted once per `_record_source` call (`uuid.uuid4().hex` / `_iso_utc(time.time())`, `watch_manager.py:163-164`); read verbatim by `get_observation_source` (no re-fetch); AST guard `test_no_engine_module_references_session_identity` (`test_tape_observation_lifecycle_feed.py:636-644`) proves `app/engine/*.py` never references either name |
| `source.profile_id` | OK | `PROFILE_DEFAULT` imported from `apps/backend/app/config.py` (`watch_manager.py:79`), not redefined; stored as a constant descriptor field per the logged assumption in `state/assumptions.md` |
| `timing.settled_at_utc` (existing row, touched by the `_settle` fix) | OK | Still the ONE `_settle` writer (`watch_manager.py:422-...`); this iteration only adds an identity guard (`if self._engines.get(ticker) is not engine: return`) — no second write path, no second settle helper |
| Generic ISO-8601 formatting helper `_iso_utc` (not itself a Data Contract entry — a shared string-formatting utility used by several registered fields) | ADVISORY (see notes) — not a FAIL: it is not a second computation of any registered value, and the established repo-wide pattern is deliberate and (for the two pre-existing copies) actively cross-tested | `apps/backend/app/main.py:266-27` (new, this iteration) vs. `apps/backend/app/watch_manager.py:70-84` and `apps/backend/app/observation_contract.py:265-271` (pre-existing, cross-checked against each other by `apps/backend/tests/test_tape_observation_time.py:540`) |

No new displayed value/entity was introduced this iteration (all `SourceDescriptor` fields were
already named in the blueprint's Data Contract row before this iteration ran), so Part A.4/A.5
("unregistered value") does not apply.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /tape/{ticker}/observation` | OK (still correctly absent) | `apps/backend/app/main.py` — grepped `@app\.(get|post)("/tape` and confirmed only `/state`, `/features`, `/events`, `/summary`, `/history` are registered (`main.py:564,569,574,579,584`); no `/observation` route exists, matching the iter spec's explicit out-of-scope item and DoD ("`/tape/SIM-BIDABS/observation` still 404s") |
| Cockpit `/`, `/structure`, `/desk` | OK (unchanged) | `git status --short` / diff file list confirms zero `apps/frontend/*` files touched this iteration |

No new page, route, or nav entry was introduced, so no navigation-path, reachability,
duplicate-home, or parallel-shell check has anything to evaluate against — the IA is byte-identical
to iter-2's, exactly as the blueprint and iter spec require.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `apps/backend/app/main.py`'s new `_iso_utc(dt)` (added this iteration, `main.py:266-27`) is a
  third independent implementation of the repository's pinned ISO-instant format, alongside the
  pre-existing `watch_manager._iso_utc` and `observation_contract._iso_utc`. This continues an
  established, deliberate repo-wide convention (roughly 40 modules already define their own
  `_iso_utc`/`_iso_utc_now`), and today all three produce byte-identical output for equivalent
  inputs (verified by reading all three definitions). However, unlike the watch_manager/
  observation_contract pair — which `test_tape_observation_time.py:540`
  (`assert watch_manager._iso_utc(epoch) == observation_contract._iso_utc(epoch)`) actively
  cross-checks — the new `main._iso_utc` has no equivalent cross-check test in this iteration's
  diff, despite its own docstring asserting it matches the other two "byte-for-byte." This is not
  a Data Contract violation (no registered field is computed twice — `main.py` formats the window
  bounds once and the manager stores them verbatim, never re-deriving), so it does not FAIL. Decomposer
  should consider having the next iteration that touches `main.py`'s time formatting add a
  three-way cross-check assertion (or extend `test_tape_observation_time.py`'s existing pairwise
  check to include `main_module._iso_utc`) so the claim in the docstring is actually enforced, not
  just asserted in a comment.
