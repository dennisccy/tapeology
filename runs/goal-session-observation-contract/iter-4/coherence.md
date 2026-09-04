# Iteration 4 — Coherence Audit

**Iteration:** goal-observation-contract-iter-4
**Date:** 2026-09-04
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration (confirmed by diff inspection)

`git status --porcelain -- apps/ docs/ scripts/` and `git diff 2f32618a...` (both the noise-excluded
full diff and the bounded `iter-diff.md`) show exactly three code files touched, all test-only:

- `apps/backend/tests/test_tape_observation_lifecycle_feed.py` (modified) — removes the vacuous
  `test_seven_lifecycle_statuses_plus_watch_stopped_are_pairwise_distinguishable`.
- `apps/backend/tests/test_tape_observation_time.py` (modified) — extends the ISO-helper cross-check
  from two-way to three-way (adds `app.main._iso_utc`).
- `apps/backend/tests/test_tape_observation_path_equivalence.py` (new, 407 lines) — the J-04
  ingestion-path-equivalence proof.

Zero files under `apps/backend/app/` and zero frontend files are touched — verified directly, not
merely asserted from the spec. This matches the iter spec's IN SCOPE/OUT OF SCOPE and the blueprint's
IA note ("this era adds NO nav entry, NO page, NO panel").

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Machine observation semantics (`schema_version`, `tape_state`, `confidence`, `market.*`, `timing.*`, `engine_identity.*`, …) | OK | `test_tape_observation_path_equivalence.py:237-258` (`_build_observation` calls the canonical `build_tape_observation` from `app.observation_contract`; no reimplementation) |
| Provenance/source/lifecycle metadata (`source.*`, session id/start, `available_at_utc`, `lifecycle.*`) | OK | `test_tape_observation_path_equivalence.py:307-308,325-326` (`manager.get_observation_source(ticker)` — the registered atomic-read method — supplies the real `SourceDescriptor` for both legs; no re-derivation) |
| Explanatory metadata (`observations[]`) | OK | untouched by this iteration's diff |
| Integrity (`observation_hash`, `artifact_hash`) | OK | `test_tape_observation_path_equivalence.py:437` (`observation_contract.compute_observation_hash` — the canonical hash law — is called, not reimplemented, in the TC-4 counterexample) |
| Field partition constants (`MACHINE_OBSERVATION_SEMANTIC_FIELDS` etc.) | OK | `test_tape_observation_path_equivalence.py:458-489` — `_FROZEN_*` tuples are a golden-reference literal asserted **equal to** the real `observation_contract.*` constants (TC-6); this is a regression check on the canonical source, not a second implementation of it |
| `_iso_utc` formatting helper (not a registered Data Contract row — a shared string-formatting utility feeding several timestamp fields) | OK (advisory carried forward, now closed) | `main.py:266`, `watch_manager.py:70`, `observation_contract.py:265` — three independent copies, pre-existing from iter-3, not touched this iteration. Iter-3's own coherence verdict (`iter-3/coherence.md:42`) already classified this as ADVISORY not FAIL ("not a second computation of any registered value... the established repo-wide pattern is deliberate") and named exactly this iteration's fixup as the remediation. `test_tape_observation_time.py:59-66` now delivers it: the byte-identical cross-check is extended to all three implementations, closing the gap rather than opening a new one. |

No new displayed value is introduced this iteration (it is an in-process pytest proof, nothing is
served or rendered), so Data Contract items 4/5 (duplicate-of-existing / unregistered-new-value) do
not apply.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| N/A — no new page/route/feature this iteration | OK | Zero frontend files in the diff; `apps/backend/app/main.py` untouched, so `/tape/{ticker}/observation` still does not exist (confirmed absent from the diff — route lands iter-5 per blueprint and iter spec OUT OF SCOPE). Blueprint's Information Architecture section is unchanged (no nav entry, no page, no panel to check reachability for). |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The three independent `_iso_utc` implementations (`main.py:266`, `watch_manager.py:70`,
  `observation_contract.py:265`) remain three separate functions rather than one shared helper. This
  was already flagged advisory (not FAIL) at iter-3 and is not new to this iteration; this iteration's
  own fixup (`test_tape_observation_time.py`) is the exact remediation the prior verdict named, and it
  is now in place — the three copies are proven byte-identical across representative epochs, with a
  counterexample proving the check is non-vacuous. True consolidation into one shared helper (rather
  than three cross-tested copies) would be cleaner long-term but is not required and does not block
  anything.
- No other coherence-relevant observations. This iteration is a pure test-and-proof addition over
  already-registered computing modules, exactly as the blueprint's Data Contract closing paragraph and
  the iter spec's "Blueprint conformance" field describe.
