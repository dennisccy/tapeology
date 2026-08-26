# Iteration 2 — Coherence Audit

**Iteration:** goal-hypothesis-foundry-iter-2
**Date:** 2026-08-26
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Iteration scope: five new hermetic backend modules (`foundry_interpreter.py`, `foundry_family.py`,
`foundry_freeze.py`, `foundry_ledger.py`, `foundry_runner.py`) implementing Data Contract rows 3–8's
already-registered "Computed by" modules (moving them from "(planned)" to real). Confirmed via
`grep -rln "foundry_interpreter\|foundry_family\|foundry_freeze\|foundry_ledger\|foundry_runner"
apps/backend/app --include="*.py"` that no file outside these five modules and their own test files
references them — in particular no route file (`micro_routes.py` was NOT touched by this diff)
wires any of them into an endpoint. This matches the iter spec's explicit "Frontend Present: no" /
"None — hermetic backend-only iteration... not yet served through `GET
/research/desk/micro/foundry` or `/desk`."

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Per-variant `CandidateSpec` / population resolution (row 3) | OK | `foundry_interpreter.py:604-657` (`resolve_population`) — new canonical impl of a row already assigned to this module; no other module resolves population |
| Scout decision / disclosures (row 7) | OK | `foundry_interpreter.py:711-735` (`interpret_candidate`) calls `scout.screen_candidate` directly — the existing single statistical rail, never re-implemented. No second decision function found anywhere in the diff. |
| Family/variant counts, denominator, cap (row 5) | OK | `foundry_family.py:1-99` imports `SCOUT_MAX_VARIANTS_PER_FAMILY` from `.scout` (`foundry_family.py:19`) rather than redefining the cap constant — single source of truth preserved |
| Epoch/manifest/freeze identity (row 4) | OK | `foundry_freeze.py` — new canonical impl of an already-registered row; no other module generates manifests |
| Runner checkpoint / ledger integrity (row 8) | OK | `foundry_ledger.py` (own hash-chained ledger, built on the shared `micro_chain_ledger.HashChainedLedger` primitive) — explicitly never imports/writes `scout_ledger` (`foundry_ledger.py:1663` test asserts `"scout_ledger" not in dir(fl)`), matching the blueprint's row-8 note "never registered into the Scout ledger." This is the canonical implementation of an already-registered row, not a duplicate of a different registered value. |
| QA-rig era-open baseline visibility (row 1, carried) | OK | `qa_playbook_iter7_fixture_scoped_backend.sh` copies the real, already-recorded `apps/backend/.data/foundry/era_open_baseline.json` (read-only source) into the scoped rig's own `$ROOT/foundry/` directory — same computing module (`foundry_source_registry.py`) and same endpoint read that same file via the existing `resolve_foundry_dir()` derivation; no new computation or serving path introduced |

No new displayed value/entity was introduced this iteration (spec's "New information displayed:
None" is accurate — none of the five new modules are reachable from any endpoint yet).

## Information Architecture check

Zero frontend files appear anywhere in the diff (`git diff --stat` and the bounded diff's 11-file
list are both backend-only + one QA shell script). `reports/phase-goal-hypothesis-foundry-iter-2-ui-surface-map.md`
does not exist, consistent with a no-UI iteration. No new route, nav entry, or page was added or
could have been — there is nothing to check reachability for.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no UI shipped this iteration) | OK | n/a — confirmed via diff file list; no `apps/frontend/**` path touched |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The reviewer (`reports/reviews/goal-hypothesis-foundry-iter-2-review.md`) already flagged a MINOR
  issue at `foundry_runner.py:89` (`run_one_candidate`'s already-terminal fast path returns the
  cached ledger row without re-verifying `manifest_hash`/`econ_floor` against the caller's current
  inputs, unlike the intent-without-terminal resume branch which does check `econ_floor`). This is
  not a coherence violation — it is a single canonical module (the one Foundry ledger) with an
  incomplete identity check, not a second computation path or a non-canonical source — but it is
  worth carrying forward as a data-integrity gap to close before any real epoch (J-06/J-07) relies
  on resumed reads, since a resumed candidate with drifted inputs could currently return a stale
  terminal row silently instead of a `ConflictingReplayRefused`/`FoundryResumeIdentityMismatch`.
  Already tracked in the review report; no action needed from this gate.
- `state/blueprint.md`'s "Iteration note (iter-2)" was pre-written by the goal-decomposer at spec
  authoring time (dev handoff confirms no further edit was needed); its content matches what this
  diff actually shipped, so the blueprint stays an accurate contract.
