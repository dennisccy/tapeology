# Iteration 13 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-13
**Date:** 2026-08-19
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

Backend-only iteration. Diff touches exactly four product/test files (`apps/backend/app/research/vault.py`,
`apps/backend/app/research/micro_routes.py`, `apps/backend/tests/test_vault.py`,
`apps/backend/tests/test_tick_recorder.py`) plus doc/state bookkeeping (`docs/goal.md`,
`docs/rapid-validation-spec.md`, `runs/goal-session-rapid-microscope/state/{blueprint,assumptions}.md`).
Zero files under `apps/frontend/`, zero new routes, zero new MCP tools, zero nav change — confirmed by
`git diff 766799d1ea82e4e1db2d345fa5f96868bc2f2752 --stat` and independently by
`reports/phase-goal-rapid-microscope-iter-13-ui-surface-map.md` ("Affected UI Surfaces: None"). Part B
(Information Architecture) is therefore trivially satisfied — there is no new page/route/feature to place.
Part A (Data Contract) reduces to one question: was the `exposure_unknown` retraction (r8 owner ruling)
executed cleanly, with the blueprint left accurate and no orphaned second source of that value anywhere?
Verified yes, by direct grep and by reading the full `vault.py` diff, independent of the dev/reviewer/
auditor's own claims.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `exposure_state` legal-value set (Vault shards/universes/exposure ledger row) — `exposure_unknown` retracted by r8 | OK | `runs/goal-session-rapid-microscope/state/blueprint.md:102-111` (retraction note, accurate) vs. `apps/backend/app/research/vault.py`: `STATE_EXPOSURE_UNKNOWN` constant + its `__all__` entry fully deleted (diff hunks at old `__all__` list and the state-constants block); `_serialize_shard` (vault.py, reveal-test hunk) flipped to a positive whitelist `state not in (STATE_ASSIGNED, STATE_EXPOSED): return opaque` — cannot leak on any unrecognised/deleted state. Repo-wide grep (`grep -rn "exposure_unknown\|EXPOSURE_UNKNOWN" apps/backend/app/`) returns only historical-context prose inside `vault.py`'s own docstrings; zero live code references. `apps/backend/tests/test_vault.py` references the string only inside comments/docstrings narrating the deleted bug, never in a live assertion. Single writer (was `vault.py`'s deleted branch), single owner, single endpoint (`GET /research/desk/micro/vault`) — no second implementation anywhere. |
| `recover_shard_ledger` return shape (`{"ok","resumed"}`) + `recovery_ledger`'s `recovery_halted` incident row | OK — no Data Contract row needed (unchanged precedent) | `apps/backend/app/research/vault.py:1495` (`def recover_shard_ledger`) has zero production call sites — `grep -rn "recover_shard_ledger" apps/backend/app/` finds only the function's own definition/self-references and two comments (`main.py:241`, `micro_chain_ledger.py:96`); `grep -rln "recovery_ledger\|recovery_halted\|\"resumed\""` outside `vault.py`/tests returns nothing. Matches the iter-12 coherence-audit precedent already recorded in blueprint.md:176-185 ("no Data Contract row needed yet ... register it if/when a route or CLI ever surfaces it"). Since nothing serves it, there is no second source to diverge from — not a violation, and not yet a WARN-worthy "new displayed value" either, since it is not displayed. |
| `get_tick_recorder_compute` docstring (`trades_total_bucket`/`quotes_total_bucket`) | OK — documentation-only, re-format-equivalent | `apps/backend/app/research/micro_routes.py:488-497` diff corrects stale prose; the served JSON (`tick_recorder._progress_view`) is byte-unchanged, confirmed by the new `test_tc8_...` assertion in `apps/backend/tests/test_tick_recorder.py`. No shape/value/endpoint change — already-registered row, already-registered endpoint. |
| `seal_shard`/`assign_shard`/`expose_shard` corruption-gating scope | OK — documentation-only, zero behavior change | `apps/backend/app/research/vault.py` docstring additions on each of the three functions; TC-7 pins the behavior is unchanged. No served value affected. |

No new UI surface fetches any registered value from a non-canonical source (there is no new UI surface).
No new value is displayed that isn't already in the contract. No duplicate computation was introduced —
the one function this iteration substantially rewrites (`recover_shard_ledger`) reuses the pre-existing
`_rehash_suffix`/`_row_content` chain-walk helpers rather than reimplementing chain verification, and
remains the sole computation path for shard exposure state.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK / N/A | `reports/phase-goal-rapid-microscope-iter-13-ui-surface-map.md` §"Affected UI Surfaces: None"; `git diff 766799d1ea82e4e1db2d345fa5f96868bc2f2752 --stat` shows no `apps/frontend/*` paths; phase spec `docs/phases/goal-rapid-microscope-iter-13.md` §"Blueprint conformance" states "No new pages, routes, or nav entries," confirmed against the actual diff rather than taken on faith. `app/meta.py`'s `UI_ROUTES` (the nav skeleton blueprint.md cites) is untouched — not in the changed-file list. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The blueprint's iter-13 retraction note (`blueprint.md:102-111`) is a clean, accurate piece of
  contract bookkeeping: it records what was removed, why (r8 owner ruling), and confirms no
  shape/endpoint/ownership change — exactly the discipline this gate exists to encourage. No action
  needed.
- The independent post-dev auditor (`docs/handoffs/goal-rapid-microscope-iter-13-audit.md`, verdict
  PASS_WITH_GAPS) found and fixed a real integrity bug (a lagging tail-anchor letting a byte-genuine
  recovery truncate a sealed shard away) and flagged several residuals (B2 delete-both-files gap, B3
  a stale `exposure_unknown` mention left in `docs/rapid-validation-spec.md:901`'s TR-25 prose, B4 an
  overstated "zero on-disk format change" claim re: the internal `recovery_ledger` row schema, T1-T3
  test/reporting nits). Checked each against this gate's scope: none touches `blueprint.md`, none
  introduces a second source for a registered value, and none adds an unreachable or duplicate-home
  UI surface (there is no UI surface here at all). B3 in particular is a staleness issue inside
  `docs/rapid-validation-spec.md` — a spec/requirements document, not the blueprint and not a served
  value — so it sits outside this gate's Data Contract check by definition; it does not affect this
  verdict.
- Watch item for whenever `recover_shard_ledger` first gets a route/CLI caller (not this iteration):
  at that point its `{"ok","resumed"}` shape and the `recovery_ledger` incident-row schema (renamed
  `kind: "recovery_halted"`, dropped `exposure_unknown_dataset_ids`, added forensic fields per the
  auditor's B4) will need their first real Data Contract row — flagging now only so the future
  decomposer isn't surprised, not a defect today.
