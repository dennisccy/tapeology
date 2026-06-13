# goal-i_will_be_super_rich_with_my_loved_ones-iter-25 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-25
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built

The optional **sound cue** (capability 33's final item, J-66) — a new `SoundCue` control in the
`/` cockpit cue area (the thesis strip, the pre-registered cue-layer home). Plus the copy fixes the
J-66 walk surfaced (none required — every frontend-owned string already passes the copy-lint).

## Files Changed

- `apps/frontend/components/SoundCue.tsx` -- NEW. The toggle + fired-indicator.
- `apps/frontend/components/ThesisStrip.tsx` -- renders `<SoundCue>` at the bottom of the
  active-thesis strip; adds `cueKeyFor(thesis)` which reads the served verdict + active stance value
  VERBATIM (management stance when entry-marked, else the entry-checklist stance) — the UI derives no
  stance/verdict of its own.
- `apps/frontend/lib/types.ts` -- `SoundCueTaxonomy` interface + optional `sound_cue` on
  `ResearchTaxonomy`.
- `apps/frontend/app/globals.css` -- `@keyframes sound-cue-pulse` + `.sound-cue-pulse` for the
  fired-indicator flash.

## Behaviour (matches the iter spec)

- **Default OFF on every fresh load.** `enabled` starts `false` and is NEVER persisted (no
  localStorage) — a fresh page load is always silent, even on the first transition.
- **Transition-only.** Fires only when the served `cueKey` (verdict + active stance) CHANGES to a
  different value while enabled — never on the first value seen, never on an unchanged re-render.
- **Cooldown-gated.** No second fire within the served `sound_cue_cooldown_seconds` (config-owned,
  read verbatim from `taxonomy.sound_cue.cooldown_seconds` — no UI magic number).
- **Visible fired-indicator.** A brief slate pulse (`data-testid="sound-cue-fired"`,
  `data-fire-count`) shown on each fire — so transition-only + cooldown is verifiable without audio
  hardware. The sound itself is a short Web Audio beep (no asset, no new dependency); if audio is
  blocked the indicator still fires.
- **Copy from taxonomy.** Toggle label, description (states off-by-default + transition-only),
  fired-indicator label, and the reused "Descriptive only — not trading advice" register line all come
  from `GET /research/taxonomy` → `sound_cue.copy` — the frontend hardcodes none.
- **Color:** neutral slate (a UI affordance, not a side/impact signal — it does not borrow the
  green/red/amber palette). Hover/focus/active states on the toggle switch.

## Test Hooks (for browser QA, J-66)

- `data-testid="sound-cue"` (with `data-enabled`), `data-testid="sound-cue-toggle"`
  (`role="switch"`, `aria-checked`), `data-testid="sound-cue-fired"` (`data-fire-count`).
- OFF leg: fresh load ⇒ `data-enabled="false"`, switch `aria-checked="false"`, and
  `sound-cue-fired` ABSENT across transitions.
- ON leg: toggle ON ⇒ `sound-cue-fired` appears exactly at a real verdict/stance transition
  (reuse SIM-REVERSAL / SIM-SHIFT frames), with no second fire within `cooldown_seconds`.

## Type-check

`cd apps/frontend && node_modules/.bin/tsc --noEmit` → exit 0. (`npm run build` intentionally NOT
run against the harness's shared `.next` — iter-2/iter-18 lesson.)
