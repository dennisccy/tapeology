# goal-i_will_be_super_rich_with_my_loved_ones-iter-11 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-11
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

Amber entry risk-flag chips on the thesis strip (capability 26, J-49). When the active-thesis
projection carries a non-empty `risk_flags` array, the strip renders one amber advisory chip per flag,
each showing the taxonomy-owned label and its plain-language measured margin — both read VERBATIM off
the projection. The strip derives nothing.

- `RiskFlagChips` component in `ThesisStrip.tsx`: renders nothing when `risk_flags` is absent (never
  assessed — a pre-v4 thesis) OR an empty array (assessed, nothing fired). Deliberately NO "all clear"
  badge (no naked reassurance). A non-empty array renders a labeled "Entry risk flags" group of amber
  chips.
- Each chip: an amber-bordered (`border-amber-700/60`, `bg-amber-900/30`) row with the label
  (`text-amber-300`, prefixed `⚠`) and the measured evidence sentence in `font-mono` (`text-amber-200/90`),
  matching the cockpit's numeric discipline. Amber = the design system's absorption/unclear semantics
  (these are advisories, not buy/sell side reads).
- Rendered on BOTH strip variants:
  - `ActiveThesis` — after the source/feed footer, before the action-marks block.
  - `NotEvaluatedThesis` (surviving/not-evaluated, J-47) — the frozen flags persist there too (they are
    a record of the entry moment, unchanged by the watch having stopped).
- Frozen for the thesis lifetime — the chips never change as the tape moves (the projection's
  `risk_flags` is frozen server-side; the strip just renders the live frame's value verbatim).

## Files Changed

- `apps/frontend/lib/types.ts` — `RiskFlag` interface (`flag`, `label`, `evidence`, `measured`);
  `risk_flags?: RiskFlag[]` on `ThesisProjection`; `risk_flags?: TaxonomyEnum[]` on `ResearchTaxonomy`.
- `apps/frontend/components/ThesisStrip.tsx` — imported `RiskFlag`; added the `RiskFlagChips` component;
  rendered it in `ActiveThesis` and `NotEvaluatedThesis`.

## Design-system compliance

- Color: amber-300/400/200 + amber-700/900 backgrounds only (absorption/unclear tokens). No arbitrary
  colors. Green/red side semantics untouched.
- Typography: the measured-margin numerics ride in `font-mono` (the cockpit's price/size discipline).
- No new effects, no new icons (a text `⚠` glyph only — consistent with the icon-library-none rule).
- States handled: absent `risk_flags` (no chips), empty list (no chips, no badge), non-empty (chips).
  The chips render verbatim — no loading/error state of their own (they ride the live WS frame the strip
  already manages).
- The "Descriptive only — not trading advice." footer stays on the strip; chip copy is present-tense,
  descriptive, measured (e.g. "recent buy impact +0.44% exceeds the 0.40% chase threshold") — never
  imperative/predictive.

## data-testids (for browser QA)

- `risk-flags` — the chip group container (present only when flags fired).
- `risk-flag-chip` — each individual chip; carries `data-flag="<flag-id>"` for targeting a specific flag.

## Tests Run

`cd apps/frontend && NEXT_DIST_DIR=.next-qa npm run build` → Compiled successfully, types valid. The
`.next-qa` dist was removed after the build; the dev server's shared `.next` was never touched.

## Known Issues

- None. The chips are purely presentational, driven entirely by the backend-computed frozen
  `risk_flags`. See the backend handoff for which sim scenarios trip which flags (for the browser legs).
