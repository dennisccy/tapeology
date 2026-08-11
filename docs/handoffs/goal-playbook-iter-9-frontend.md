# goal-playbook-iter-9 Frontend Handoff

**Phase:** goal-playbook-iter-9
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

One new text line inside the existing Playbook Evidence section on `/desk` — no new pages, panels,
cards, nav entries, buttons, or forms. `PlaybookEvidenceSection` (`apps/frontend/app/desk/page.tsx`)
now renders the already-served `data.signature` field as a visible disclosure line ("Built from
signature: `<value>`", `data-testid="desk-evidence-signature"`) directly above the section's existing
`data.register` paragraph — the same treatment `desk-evidence-other-signature-row` already gives
OTHER signatures the section discusses, so every signature the section names is now visible on
screen (closes the iter-8 audit's F1 gap).

No new API call: `DeskPlaybookEvidence.signature` was already returned by
`GET /research/desk/playbook/evidence` (`apps/backend/app/research/desk_playbook_evidence.py:407`)
and already typed in `apps/frontend/lib/types.ts:1789`; this iteration only renders a field that was
already being fetched and stored in component state.

## Files Changed

- `apps/frontend/app/desk/page.tsx` -- `PlaybookEvidenceSection`: one new `<p>` rendering
  `data.signature`

## Design System Compliance

Matches the existing section's own established style verbatim (no new tokens introduced):
`text-xs text-slate-400` for the new line (one shade lighter than the `text-slate-500` register
paragraph directly below it, to read as a label-value pair), `font-mono text-slate-300` on the value
span — the exact classes `desk-evidence-other-signature-row` already uses for a signature value.
Dark-only, no new spacing scale, no new effect.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit`
Result: 0 errors.

Backend guard tests re-run to confirm the new rendered field needs no guard extension:
`cd apps/backend && .venv/bin/python -m pytest tests/test_desk_ui_guards.py
tests/test_desk_refresh_chain_guard.py tests/test_copy_discipline.py -q` → all pass unchanged
(96 tests). `signature` is an opaque hex string (no arithmetic possible, so it does not belong in
`_PRICE_ARITHMETIC_FIELDS`); the fetch is unchanged (the evidence GET was already joined into the
page's existing mount-time effect at iter-8, so `_EXPECTED_EFFECT_COUNT` needed no re-derivation);
the copy lint already globs `app/**/*.tsx`, so "Built from signature: ..." is covered structurally
with no edit needed.

Live browser verification (scoped fixture rig, `:3301`, Chrome CDP `:9222`):
- Screenshot: `reports/qa/goal-playbook-iter-9-evidence/desk-evidence-signature-crop.png` — shows
  "Built from signature: `9803f6881e8f86b3`" rendering above the register paragraph, with the cells
  table beneath showing both a well-populated row set (`5m`/`to_close`/`mdd_*`, n=13) and
  `below_min_n`-tagged rows (`1h`/`4h`) legible in the same view.
- Golden replay script `runs/goal-session-playbook/journey-scripts/J-08.json` (new this iteration)
  exercises the section end-to-end and passes `demo_runner.py --mode verify`.

## Known Issues

None specific to this frontend change — it is a single additive `<p>` element with zero new state,
zero new fetch, and zero new interaction surface.
