# Phase goal-playbook-iter-4 — UI Surface Map

**Phase:** goal-playbook-iter-4
**Date:** 2026-08-11
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Playbook Signals table row, setup chip (`data-testid="desk-playbook-signal-setup"`, `playbookSetupLabel()` in `page.tsx`) | Changed behavior (chip now takes 3 additional values) | `PLAYBOOK_SETUPS` extended to a 5-tuple; `playbookSetupLabel` gains `"jbe"` → "Jump-Base Explosion", `"dbi"` → "Drop-Base Implosion", `"cup_handle"` → "Cup and Handle" | Run Playbook for a session whose recorded bars fire a `jbe` signal; verify the row's setup cell renders the chip text "Jump-Base Explosion" exactly (not the raw string `jbe`). Repeat for a `dbi` row (expect "Drop-Base Implosion") and a `cup_handle` row (expect "Cup and Handle") |
| `/desk` | Playbook signal detail panel, jbe/dbi geometry line (`data-testid="desk-playbook-signal-continuation-geometry"`, inside `PlaybookSignalDetail`) | New content (new conditional render branch) | J-04 adds the `jbe`/`dbi` detector pair with its own geometry shape, distinct from the opening-range shape | Click a `jbe` or `dbi` row in the Playbook Signals table to select it; verify a `<p>` with `data-testid="desk-playbook-signal-continuation-geometry"` appears directly below the trigger/invalidation line, reading "base `<N>` MBR wide (`<N>` bars) · jump `<N>` MBR · broke at slot `<N>`"; if `base_flatline` is true, verify "· flatline base" is appended; if `base_lows_ascending` is true, verify "· ascending base" is appended; on the SECOND firing of a jbe ladder, verify "· ladder step ratio `<N>`" is appended and on the FIRST firing it is absent |
| `/desk` | Playbook signal detail panel, cup-and-handle geometry line (`data-testid="desk-playbook-signal-cup-handle-geometry"`, inside `PlaybookSignalDetail`) | New content (new conditional render branch) | J-04 adds the `cup_handle` detector with its own geometry shape | Click a `cup_handle` row to select it; verify a `<p>` with `data-testid="desk-playbook-signal-cup-handle-geometry"` appears reading "cup `<N>` bars · depth `<N>` MBR · handle retrace `<N>` · handle duration `<N>` of cup · broke at slot `<N>`" followed by "· RVOL cup mid `<N>` / cup outer `<N>` / handle `<N>`"; if `cup_optimal` is true, verify "· optimal cup length" is appended; if `handle_duration_desirable` is true, verify "· desirable handle length" is appended |
| `/desk` | Playbook signal detail panel, opening-range geometry line (existing `<p>` inside `PlaybookSignalDetail`, now conditionally rendered) | Changed behavior (render gate added; content for OR signals unchanged) | The same `signal.geometry` object now varies its fields by `setup_id`; the OR line is now gated on `signal.setup_id === "open_high_break" || signal.setup_id === "open_low_break"` instead of always rendering | Run Playbook for a session with an `open_high_break` or `open_low_break` signal (already-shipped J-03 behavior); click that row; verify the line still reads "opening range `<low>`–`<high>` (`<basis>` basis, `<N>` bars) · width `<N>` MBR · broke at slot `<N>`" with the optional "· open vs prior close `<N>`%" suffix, identical wording to before this iteration; verify NEITHER of the two new geometry `<p>` elements above is present on this row |
| `/desk` | `DeskPlaybookGeometry` type (`apps/frontend/lib/types.ts`) — no visual element of its own | Config/type change (fields made optional; 9 new optional fields added) | Backing shape for the three rows above; the opening-range fields and the new jbe/dbi/cup_handle fields are now all optional on the same interface since the served shape genuinely differs by `setup_id` | No standalone visual test — covered indirectly by the three render-branch tests above. Confirm `cd apps/frontend && npx tsc --noEmit` exits clean (already verified by the developer; re-verify only if the type file is touched again) |
| `/desk` | Playbook Signals section — the `2026-08-04` session-date query specifically | Removed data (hygiene deletion, not a code change) | The stray, git-ignored fixture record `playbook-2026-08-04-e0f249f57785.json` was deleted from the operator's real `.data/playbook/` store as a carried housekeeping item | Enter `2026-08-04` in the "Session date (yyyy-MM-dd)" input (`data-testid="desk-playbook-date-input"`) and click "Run Playbook" (or load the section if a record already resolves for that date); if no other legitimate record exists for `2026-08-04`, verify the section shows the amber "Playbook not computed for this session." panel (`data-testid="desk-playbook-not-computed"`) rather than a populated signals table |
| `/desk` | Every other shipped Desk section (screen history calendar, forward returns, refresh chain, ranked briefing, skipped members, runs/pins/compare/provenance) | No code change — regression risk only | J-04 touches only the Playbook Signals sub-tree (`playbookSetupLabel`, `PlaybookSignalDetail`); TC-11/TC-17 require every other shipped section to render exactly as before | Load `http://localhost:3301/desk` with `apps/frontend/.next` freshly rebuilt; scroll through every shipped section heading (Screen History, Forward Returns, Refresh Chain, Briefing, Skipped, Runs, Pins, Compare, Provenance, Playbook Signals) using the sibling-`display:none`-collapse technique for the lower sections; verify each heading text and layout is unchanged from before this iteration and no new console error appears |

<!-- Change Type options used above: Changed behavior | New content | Removed data | Config/type change -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/desk_playbook_detect.py` — `detect_jbe`, `detect_dbi`,
  `detect_cup_handle`, `_base_lows_ascending` — the detection math itself. No UI impact directly;
  its OUTPUT reaches the UI only through the already-registered `GET /research/desk/playbook`
  endpoint, captured in the surface-map rows above.
- `apps/backend/app/research/desk_playbook.py` — `PLAYBOOK_SETUPS` extended to 5 entries, two new
  named constants joined to `playbook_parameters()`, the compute-walk loop generalized to iterate
  every detected signal instead of at most one. Same as above — reaches the UI only through the
  existing endpoint's payload, already covered.
- `apps/backend/tests/test_desk_playbook_detect.py`, `test_desk_playbook.py`,
  `test_desk_playbook_guards.py` (new), `test_desk_ui_guards.py` — test files. No UI surface.
- `docs/playbook-detector-spec.md` — §0 provenance-line paragraph, two new §1 constant table rows.
  Documentation only; not served by any app route.
- `apps/backend/.data/playbook/playbook-2026-08-04-e0f249f57785.json` (deleted) — a stray
  git-ignored fixture record. Its removal has a narrow, testable UI effect (see the surface-map row
  above for the `2026-08-04` date query) but the deletion itself is a filesystem/hygiene action, not
  a code change to any UI-serving surface.

---

## Summary

- **Frontend surfaces changed:** 2 files (`apps/frontend/lib/types.ts`, `apps/frontend/app/desk/page.tsx`), all within the single already-shipped Playbook Signals sub-tree on `/desk`.
- **New pages/routes:** 0
- **Modified components:** 2 (`playbookSetupLabel`, `PlaybookSignalDetail`) — plus the `DeskPlaybookGeometry` type they depend on.
- **Navigation changes:** no
- **Backend-only changes:** 5 (2 detection/compute modules feeding the existing endpoint, 4 test files, 1 doc file, 1 deleted stray data file) — see list above.
