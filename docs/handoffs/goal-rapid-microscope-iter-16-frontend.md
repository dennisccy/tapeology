# goal-rapid-microscope-iter-16 Frontend Handoff

**Phase:** goal-rapid-microscope-iter-16
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

Two small, scoped-as-passengers fixes to `apps/frontend/app/desk/page.tsx` — no new surface, no
new served value, no navigation change. Both are resilience/coherence fixes to already-shipped
sections (Microscope Readiness from J-01, Scout Ledger from J-04).

- **`MicroReadinessSection` testid coherence (closes iteration 15's COHERENCE-WARN)** — the
  section's `loading` and `unavailable` early returns now wrap their content in
  `data-testid="micro-readiness-section"`, exactly mirroring `ValidationVaultSection`'s own
  already-fixed pattern (`page.tsx:6684-6699`). The `loaded` state already carried this testid; all
  three render states now carry it consistently, matching every sibling Rapid-Microscope section.
- **Scout Ledger table survives a malformed/tampered trial row** — the table's two previously
  undefended reads, `trial.feature.name`/`trial.feature.transform` and `trial.outcome.horizon_key`,
  now use optional chaining with a `"—"` fallback glyph
  (`trial.feature?.name ?? "—"` / `trial.outcome?.horizon_key ?? "—"`). Before this fix, a trial
  row missing either key (a genuinely reachable server shape — see below) would throw during
  render with no `ErrorBoundary` anywhere on the page (`grep -c "ErrorBoundary\|componentDidCatch\|
  getDerivedStateFromError"` on the whole 6,700+-line file returns `0`), blanking the entire
  `/desk` page for every section, not just the Scout Ledger. The fix is row-level and local: one bad
  cell now renders `"—"`, every other row and every other section is unaffected.

## Files Changed

- `apps/frontend/app/desk/page.tsx` — `MicroReadinessSection` (~line 5886): two early returns now
  wrapped in `data-testid="micro-readiness-section"`. Scout Ledger table (~lines 6315/6317): two
  reads changed to optional-chained with a fallback glyph.

No new component, no new prop, no new fetch, no `lib/types.ts` change (the `ScoutTrialRow` type's
`feature`/`outcome` fields stay typed as required — matching the SHOULD-always-be-true server
contract; the defensive read guards the ACTUAL runtime shape, which the type system cannot enforce
against a hand-tampered or partially-constructed ledger row).

## Why the malformed shape is real, not hypothetical

`apps/backend/app/research/scout_ledger.py`'s `ScoutLedger.append_row(fields: dict)` persists
`fields` with zero shape validation or defaulting (confirmed by direct reading of its
implementation) — whatever dict a caller passes is what gets written and later served. `scout.py`'s
`list_scout_families` (`GET /research/desk/micro/scout`'s whole body) serves `"trials": family_rows`
— every row VERBATIM, by its own docstring ("every row verbatim — decision, reason, notes,
screen_result"), with no reshaping. A manual, throwaway script (not a committed test — `scout.py`/
`scout_ledger.py` are frozen this round) confirmed this directly against the real, unmodified
functions: a row appended with the exact sparse field set
`test_desk_scout_tool_byte_identical_on_a_populated_state` (`test_mcp_server.py`) already uses for
its own fixture (`family_id`, `family_root_id`, `candidate_id`, `decision`, `reason` — no
`feature`/`outcome` key) comes back from `list_scout_families` with those keys genuinely absent:

```
trial keys: ['candidate_id', 'decision', 'family_id', 'family_root_id', 'prev_hash', 'reason', 'row_hash', 'row_index', 'variants_tried']
```

So the frontend fix defends a state the real backend contract can genuinely produce today (e.g. a
future caller that registers a candidate before a feature/outcome pairing is fully wired, or any
tampered/corrupted ledger row), not a made-up edge case.

## Tests Run

- `npx tsc --noEmit` (apps/frontend) — 0 errors.
- `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_ui_guards.py -q` — all pass,
  including the new seeded-violation counter-test for the two iteration-15
  `_PRICE_ARITHMETIC_FIELDS` clauses (a backend-side guard, unaffected by these two frontend
  fixes, re-run to confirm no accidental arithmetic was introduced by this iteration's edits —
  neither fix touches a guarded numeric field).
- Full backend suite (authoritative, read from `--junitxml`): **3245 collected / 3237 passed /
  8 skipped / 0 failed / 0 errors** in a clean run — baseline (iteration 15) 3237/3229/8/0, so
  +8 collected / +8 passed / 0 regressed. This is the whole round's number (backend + frontend
  work together), reported in full in `docs/handoffs/goal-rapid-microscope-iter-16-dev.md`.

## Known Issues

- **Live browser confirmation of both fixes was not performed by this dev pass.** Both changes are
  `tsc`-clean and traced by hand against the exact JSX (the testid wrap mirrors an already-shipped,
  already-verified sibling pattern byte-for-byte; the optional-chaining fix is a standard,
  low-risk JS idiom). Confirming the "unavailable" state's testid live and a real seeded malformed
  row degrading gracefully in an actual rendered DOM is the QA/browser-qa lane's job this round
  (the shared QA fixture rig has never been seeded with a Scout family — any test needing that
  shape of data must seed its own isolated fixture store, per this round's carried environment
  constraints).
- No other frontend surface changed. `/desk`'s navigation, layout, and every other section are
  unaffected — confirmed by `git diff --stat` showing only `page.tsx` touched, with a 20-line
  (10 insertion / 10 modification-adjacent) diff confined to the two named locations.
