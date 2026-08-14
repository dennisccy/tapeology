# Iteration 3 — Coherence Audit

**Iteration:** goal-referee-iter-3
**Date:** 2026-08-14
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

Backend-only, unconsumed library iteration (per the iter spec's own "New user-facing capability:
None yet" / "UI surface changes: None" / "Data-contract additions: None"). Confirmed independently
against the diff, not just the spec's say-so:

- `apps/frontend/` — zero diff (`git diff <snapshot-sha> --stat -- apps/frontend/` empty).
- `apps/backend/app/meta.py` (`UI_ROUTES`, the nav skeleton) — zero diff.
- Every route file / `apps/backend/app/main.py` / MCP server — zero diff.
- `apps/backend/app/config.py` — zero diff (no new `Config` field).
- The "Unchanged owners" list from the blueprint (`desk_playbook.py`, `desk_forward.py`,
  `levels.py`, `tradability.py`, `desk_playbook_detect.py`, `desk_playbook_context.py`,
  `pnl_scan.py`, `store.py`, `datasets.py`, and `referee_evidence.py`'s own source) — zero diff,
  confirmed via `git diff --stat` against each named file individually.
- `apps/backend/app/research/referee_stats.py` (new, 711 lines) imports only stdlib
  (`itertools`, `math`, `random`, `statistics`) — no route, no store, no `Config`, no other
  research module.

Net: this iteration ships a new pure-computation library with no caller, no route, no MCP tool,
and no UI surface. There is nothing for Part B (Information Architecture) to check — no new
page/route/feature was introduced — and Part A (Data Contract) reduces to "does the new module
duplicate an already-registered value's computation," since it registers no new displayed value of
its own (the blueprint's IA table already carries J-03 as "library modules, no page of their own").

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Referee evidence coverage + per-family readiness (`referee_evidence.py`) | OK — source untouched | `git diff --stat` shows only `apps/backend/tests/test_referee_evidence.py` changed; `referee_evidence.py` itself has zero diff |
| Matched-null records, Registry, Evaluation records, Adjudications, Promotion verdict (J-04–J-08 rows) | OK — not touched | none of `referee_null.py` / `referee_registry.py` / `referee_adjudicate.py` / `pnl_scan.py` exist or changed this iteration |
| Playbook records / measurement rail / band maps / session honesty / strategy trades / config fingerprint (unchanged owners) | OK — zero diff | see file list above |
| `referee_stats.py`'s own new functions (`permutation_test`, `bootstrap_ci_*`, `benjamini_hochberg`, `run_oracle_attestation`, …) | OK — genuinely new, not yet a displayed value | serves no endpoint, consumed by no caller this iteration (`apps/backend/app/research/referee_stats.py:1-13` module docstring; confirmed no importer exists in the diff) — matches the blueprint IA row "J-03 stats core (library module, no page of their own) \| n/a — consumed by J-04–J-09 \| —", so this is not an unregistered-value WARN either |

**One traced-through, non-violating observation.** `referee_stats.py`'s
`_draw_indices_without_replacement` (`apps/backend/app/research/referee_stats.py:164-174`)
re-implements the same hand-coded partial Fisher-Yates idiom that
`desk_forward._draw_anchor_indices` (`apps/backend/app/research/desk_forward.py:428`) also
implements, rather than importing it — and the blueprint's "Unchanged owners" line names
`_draw_anchor_indices` under "never re-implements." I traced this to both places (the blueprint
row and the offending `file:line`) to check whether it clears the Part A bar, and concluded it
does not, for three concrete reasons: (1) `_draw_anchor_indices` is an internal RNG-shuffle
primitive, not itself a row in the Data Contract table — the Contract registers *displayed
values* (evidence coverage, null records, registry, …), and a shuffle algorithm computing no
displayed value cannot "not match" another displayed value; (2) the two implementations feed
disjoint domains that never both render the same number — `desk_forward`'s copy samples anchor
indices for forward-return measurement, `referee_stats.py`'s copy samples indices for
bootstrap/permutation draws over caller-supplied arrays passed in from an as-yet-nonexistent
caller — so there is no code path where the same logical value could diverge; (3) the
re-implementation is a disclosed, spec-mandated architectural decision, not drift: the iter spec's
IN SCOPE section states verbatim that `referee_stats.py` must match (never import) the idiom
specifically because it is barred from importing `desk_forward` at all (the import-ban guard,
`apps/backend/tests/test_referee_guards.py`'s new `test_referee_stats_module_imports_none_of_the_banned_rail_detector_context_modules`),
which exists to enforce the anti-goal "The Referee never feeds back" (no referee module may depend
on rail/detector/context modules). Recommending the import here would directly break a
guard-tested anti-goal this same iteration built — so this is not something for the next iteration
to "tidy." Flagging it in this PASS's notes only so the reasoning is on record and a future
reader doesn't misread the blueprint's "never re-implements" phrasing as broken.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — zero new pages/routes this iteration) | OK | `app/meta.py` (`UI_ROUTES`) has zero diff; `apps/frontend/` has zero diff |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The Fisher-Yates re-implementation discussed above is recorded for context, not as a to-do —
  it is correct as shipped and must NOT be "fixed" into an import of `desk_forward` (that would
  violate the import-ban anti-goal this iteration itself guard-tested).
- `referee_stats.py` is unconsumed by any caller this iteration (by design — J-04/J-05/J-06 wire it
  up later). Nothing to check on the serving side yet; the next iteration(s) that add a caller are
  where Part A's "non-canonical source" check will start to bite for real, once `referee_stats.py`'s
  outputs (p-values, CIs, BH results) start reaching a route or UI surface.
