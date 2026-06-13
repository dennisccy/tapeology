# goal-i_will_be_super_rich_with_my_loved_ones-iter-26 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-26
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built

J-66 placement-only fix (lean, frontend-only). The optional sound-cue toggle was previously
mounted **inside** the thesis-conditional `ActiveThesis` branch of `ThesisStrip.tsx`, so a fresh
`/` cockpit with no thesis declared rendered no toggle anywhere — failing J-66's "its toggle is
explicit" precondition. This iteration relocates the `SoundCue` mount into the **shared
`StripShell` wrapper** so the toggle renders on **every** `ThesisStrip` state (idle no-thesis,
declare form, taxonomy-loading, taxonomy-error, active-thesis, and not-evaluated surviving
thesis). No cue behaviour, copy, fire logic, cooldown, default-OFF semantics, or fired-indicator
changed — only the mount position.

- The single `<SoundCue>` is now rendered once by `StripShell`, after `{children}`, in all six
  strip render paths. The previous inline mount inside `ActiveThesis` was removed (no
  double-render in the active state).
- `StripShell` gained two optional props — `cueKey?: string | null` and
  `cueTaxonomy?: SoundCueTaxonomy | null` — passed by every caller. For thesis states the caller
  passes `cueKeyFor(thesis)` (the verbatim row-15 verdict + active-stance key, unchanged from
  iter-25); for no-thesis states it passes `cueKey={null}` so the toggle is **inert** (no live
  verdict ⇒ never fires) but **visible and OFF**.
- The taxonomy `useEffect` guard was changed from `if ((!open && !thesis) || taxonomy) return;`
  to `if (taxonomy) return;` so the always-rendered toggle has its taxonomy-owned `sound_cue`
  copy available on a fresh idle cockpit. The taxonomy is still fetched **at most once** and
  cached (the `taxonomy` guard), so the idle line still issues a single cached request — no copy
  is fabricated client-side: a pre-J-66 taxonomy omitting `sound_cue` ⇒ the toggle renders
  nothing (`SoundCue` returns `null` when `taxonomy` is absent).

## Files Changed

- `apps/frontend/components/ThesisStrip.tsx` -- relocated the `SoundCue` mount from the
  `ActiveThesis` branch into the shared `StripShell` wrapper (rendered in all strip states);
  added optional `cueKey` / `cueTaxonomy` props to `StripShell` and wired them at every call
  site; imported `SoundCueTaxonomy`; changed the taxonomy fetch to load once unconditionally so
  the idle no-thesis cockpit has the cue copy.

## Tests Run

Command (backend): `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **848 passed, 1 skipped, 0 failed, 0 errors** (exit 0, 477.64s / 7m57s). The 1 skip is
the pre-existing credentialed live-integration test. Byte-identical baseline with ZERO re-pins —
no `apps/backend/` file is in the diff (no `app/engine/` or `app/providers/` change).

Command (frontend type-check): `cd apps/frontend && npx tsc --noEmit`
Result: exit 0 — clean. (Used `tsc --noEmit` rather than `npm run build` to avoid touching the
QA-harness shared `.next`, per the memorialized QA frontend-build caution.)

No backend file is in the diff (`git status` shows zero `apps/backend/` changes), so the backend
suite must stay byte-identical with the same counts and zero re-pins.

## Known Issues

- Browser verification is the gate for J-66 and is run by the browser-qa-agent (this is a
  user-visible UI relocation): (a) a fresh no-thesis `/` cockpit must show the sound-cue toggle
  present and `aria-checked=false`; (b) once a thesis is declared (SIM-BUYER) and a real
  verdict/stance transition occurs, the toggle must still fire its indicator (transition-only)
  and respect the served cooldown. These cannot be fully proven from a dev-side unit/type check.
- The `taxonomyError` state remains reachable only when the form is open or a thesis is active in
  practice; on a fresh idle cockpit (`!open`, no thesis) the `if (!open)` branch returns the idle
  declare affordance first, so a taxonomy-load failure never replaces the idle line — it only
  means the cue toggle renders nothing (no fabricated copy). The idle declare affordance is
  unchanged (J-68 strip-idle clause preserved).
- No backend, nav, route, or data-contract change. Suite expected byte-identical (zero re-pins).
