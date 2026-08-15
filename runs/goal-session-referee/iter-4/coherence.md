# Iteration 4 — Coherence Audit

**Iteration:** goal-referee-iter-4
**Date:** 2026-08-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

Backend-only iteration (statistics-core bugfix + one additive disclosure field). Zero frontend
files touched, zero route files touched, zero new `Config` fields, zero new endpoints. The one
diff that touches the Data Contract (`stale_basis_dates` on the already-registered "Referee
evidence coverage + per-family readiness" row) is additive, was registered into
`state/blueprint.md` in this SAME diff (the iter-4 note), and its implementation is a
duplication-*reduction* (one new shared predicate replaces two previously-independent copies of
the identical staleness check) — the opposite of a coherence violation.

Diff scope verified via `git diff 921d31badaf260619299513c0e455e9c7bdab993`, `--stat` of the
noise-excluded paths, and `git status`: only 5 files changed —
`apps/backend/app/research/referee_stats.py`, `apps/backend/app/research/referee_evidence.py`,
`apps/backend/tests/test_referee_stats.py`, `apps/backend/tests/test_referee_oracles.py`,
`apps/backend/tests/test_referee_evidence.py` — plus the sanctioned `state/blueprint.md` additive
note. Confirmed no route file, `apps/frontend/`, or `app/config.py` appears anywhere in the diff
(`git diff --name-only -- apps/backend/app/ | grep -iv research/referee` returned empty;
`git diff --name-only -- apps/frontend/` returned empty). This matches the iteration spec's own
IN SCOPE/OUT OF SCOPE declarations verbatim (backend-only, "zero diff to ... any route file",
"Frontend: none").

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Referee evidence coverage + per-family readiness (`playbook_occurrence.stale_basis_dates`, `GET /research/desk/referee/evidence`) | OK | `apps/backend/app/research/referee_evidence.py:235-249` (`_is_stale_basis` — one new shared predicate), `:270-303` (`playbook_occurrence_readiness` calls it, appends to `stale_basis_dates`, all other fields' computation unchanged); registered same-diff in `runs/goal-session-referee/state/blueprint.md:73-81` |
| Same field on `playbook_observations()` (J-02 adapter, unconsumed by any route) | OK | `apps/backend/app/research/referee_evidence.py:733-750` — same shared `_is_stale_basis` helper, not a second independent check |
| `referee_stats.py` internals (`STATS_CORE_VERSION`, `_ATTESTATION_EXPECTED`, exact-enumeration `permutation_test` fix) | N/A — not a Data Contract row | Blueprint IA explicitly lists "J-02 evidence contract, J-03 stats core (library modules, no page of their own) \| n/a — consumed by J-04–J-09 \| —"; module remains imported by nothing outside its own test suite (confirmed by `reports/phase-goal-referee-iter-4-ui-surface-map.md`'s File Classification table) |

No duplicate computation: the only production-code Data Contract touch (`stale_basis_dates`)
*removes* a pre-existing duplication rather than adding one — `playbook_occurrence_readiness()`
and `playbook_observations()` each used to inline the identical
`record_basis != live_basis or fingerprint != config_fingerprint` check; both now call the one
new `_is_stale_basis` helper.

No non-canonical source: zero new UI surfaces exist to check. `reports/phase-goal-referee-iter-4-ui-surface-map.md`
independently confirms via `grep -rn "referee" apps/frontend/app apps/frontend/components
apps/frontend/lib` → zero matches.

No unregistered new value: `stale_basis_dates` is registered in `state/blueprint.md`'s iter-4 note
in this same commit's diff, word-for-word matching the iteration spec's "Data-contract additions"
section (`docs/phases/goal-referee-iter-4.md:255-271`). Not a synonym/re-derivation of any existing
registered value — it is a new disclosure field on an already-registered row, exactly the additive
case the blueprint's own header sanctions without re-approval ("Additive edits (new value rows,
new pages under an existing nav section) need no re-approval").

The `_prefix_bug_enumeration_p` helper added to `apps/backend/tests/test_referee_oracles.py`
(TC-4's anti-conservative mutant) is a deliberate test-only reproduction of the pre-fix buggy
computation, used to prove the oracle suite detects it — not a second production computation path
of any registered value. This is explicitly the iteration spec's own design (IN SCOPE: "Extend the
existing mutation-fixture test with a SECOND, paired mutant that reproduces the PRE-FIX
subtraction-based computation").

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK | `git diff --name-only` shows no route file, no `apps/frontend/` file, no `app/main.py`; `app/meta.py` `UI_ROUTES` (the nav skeleton per blueprint IA) untouched |

The blueprint's existing IA rows already cover every module this iteration touches ("J-01 per-family
readiness fold ... \| `GET /research/desk/referee/evidence` \| Desk" and "J-02 evidence contract,
J-03 stats core (library modules, no page of their own) \| n/a"). No nav change was needed or made.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `stale_basis_dates` is served but rendered nowhere yet (by design — J-09 is its first UI
  consumer, several iterations away per the blueprint IA row for J-09). Not a violation: an
  unregistered-and-new value would be a WARN, but this value IS registered this same iteration: no
  WARN needed.
- The `permutation_test` fix in `referee_stats.py` went slightly beyond the iteration spec's
  literal bullet (it also changed the per-session `acc +=` accumulation to `math.fsum(terms)`,
  justified inline by an empirical finding that the g2_sum fix alone left ~7% of 3-to-5-session
  cases still able to violate the floor). This is a correctness/spec-fidelity question for the
  reviewer/auditor, not a coherence one — it stays inside the same function, in the same
  already-registered owner module, touches no endpoint, and introduces no new value or duplicate
  source. Flagged here only for visibility, not as a coherence finding.
