# Iteration 2 — Coherence Audit

**Iteration:** goal-observation-contract-iter-2
**Date:** 2026-09-03
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration touches exactly one product file — `apps/backend/app/watch_manager.py` (124
insertions, confirmed via `git diff 052828c548e30b4a60d8735d4e123254a998cb43 --stat`) — plus one new
test module (`apps/backend/tests/test_tape_observation_time.py`). Per the iter spec's "Data-contract
additions": None (no new endpoint, no new served/displayed value). Verified against the diff.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Provenance/source/lifecycle metadata — `settled_at_utc`, `end_reason` (the atomic-settled-pair half) | OK | `apps/backend/app/watch_manager.py:293-345` (`get_observation_source`, `_settle`) — this IS the blueprint's registered future computing module for this row (`WatchManager.get_observation_source`), being built in place, not a rival path. Not yet served by any endpoint (route lands iter-5, confirmed absent — `/tape/{ticker}/observation` still 404s per DoD). |
| `observed_at_utc`, `availability_basis`, `available_at_utc` (time-law arithmetic) | OK — unchanged | `apps/backend/app/observation_contract.py` not touched this iteration (`git diff --stat` shows zero changes to it); the iter-1-built `_observed_at_utc`/`_availability` logic is exercised, not reimplemented, by the new test file. |
| ISO-timestamp formatting (`_iso_utc`) | OK — cross-checked duplicate, not a divergent computation | `apps/backend/app/watch_manager.py:66-80` duplicates the pinned ISO formatter already owned by `apps/backend/app/observation_contract.py`. This is a pure, stateless epoch→string formatter (not a domain value with its own semantics), follows an established repo-wide convention (per its own docstring: ~2 dozen other modules already do this rather than importing a private cross-module name), and is guarded by an explicit byte-for-byte cross-check test — `test_watch_manager_iso_helper_matches_observation_contract_byte_for_byte` (`apps/backend/tests/test_tape_observation_time.py:535-541`) — that fails the moment the two implementations diverge. This is the "re-format is fine" / cross-checked-duplicate case the skill exempts, not the "the numbers don't match" failure the Data Contract gate targets. |

No new displayed value is introduced (nothing is served anywhere this iteration — `get_observation_source`
is an in-process manager method only, per the spec's "New information displayed: None"). No duplicate
computation of any registered value was found. No new UI surface fetches anything from a non-canonical
source (zero frontend files touched — confirmed via `git diff --stat` against the snapshot SHA, no
`apps/frontend/*` entries).

## Information Architecture check

No new page, route, panel, link, or nav change this iteration (blueprint conformance section and DoD
both state this explicitly; confirmed by the diff — only `watch_manager.py` and a new test module
changed). `apps/backend/app/main.py` is untouched (`/tape/{ticker}/observation` route still does not
exist; confirmed absent from the diff and explicitly re-verified in the iter spec's TC-14/DoD as
"still 404s"). Nothing to check for reachability or duplicate homes.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new surface this iteration) | OK | N/A |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The duplicated `_iso_utc` helper in `watch_manager.py` (noted above) is architecturally sound given
  its cross-check test, but is worth folding into a single shared formatter (e.g. imported from
  `observation_contract.py` or a small shared `time_format.py`) once the guard-forbidden-import
  tension that motivates the per-module duplication convention is revisited — not urgent, purely a
  future de-duplication opportunity, not a coherence defect.
