# goal-i_will_be_super_rich_with_my_loved_ones-iter-2 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-2
**Date:** 2026-06-10
**Agent:** developer
**Status:** complete

## What Was Built

The cockpit's first research surface: a **thesis strip** on `/` between the price chart and the
panel grid. The cockpit evolves from a pure tape reader into the first decision-support surface —
the user's own idea is now a first-class, validated, journaled object judged against the live tape.

- **Idle state** — a single one-line declare affordance ("Declare a thesis on this ticker…" + a
  "Declare thesis" button). Nothing else on the cockpit moves when idle (J-68 strip-idle clause);
  the strip is a fixed-height bar above the panel grid.
- **Declare form** — opens in place; fully taxonomy-driven from `GET /research/taxonomy` (setup and
  direction `<select>`s, an invalidation price input, and a level price input that appears ONLY when
  the selected setup requires it). No setup/direction label is hardcoded. The form loads the
  taxonomy lazily (only when opened) and shows an explicit loading line, plus an explicit
  "couldn't load the catalog" state — never a fabricated form.
- **Inline validation** — a 422/409/404 from the backend is surfaced verbatim as a rose inline
  message; the form values are preserved so the user can correct and resubmit. Nothing is created
  on rejection (no client-side coercion). A client-side guard also blocks an empty/non-numeric
  invalidation before the request.
- **Active-thesis display** — reads the WS `thesis` projection VERBATIM (the frontend derives
  nothing): setup, direction (emerald long / rose short), invalidation in `font-mono`, optional
  level in mono, the frozen expected-behaviour statements each with a live status dot + label
  (`met` emerald / `not yet` slate / `violated` rose), the `pending` verdict badge as a slate pill,
  bound source + `data_feed` (SIM/SIP/IEX) stamp, and a `monitor_status: failed` notice when the
  monitor errors. Carries the "Descriptive only — not trading advice" disclaimer.

## Copy / Design Discipline (J-66)

- All strings are thesis-attributed, present-tense, descriptive ("watch the tape judged against it",
  "Aggression … is being absorbed") — no imperative buy/sell/enter/exit, no prediction, no certainty.
- Verdict semantics follow the design direction: `pending` = slate (green/amber/red reserved for the
  verdict-transition engine next iteration). Statement statuses reuse the existing side/impact palette
  (met = emerald, not-yet = slate, violated = rose) without repurposing.
- The strip reuses the existing panel styling (`rounded-lg border border-slate-800 bg-slate-900/60`),
  mono numerics for all prices, and every interactive element has hover / focus / active / disabled
  states.

## Files Changed

- `apps/frontend/components/ThesisStrip.tsx` -- NEW: idle affordance / taxonomy-driven form / active display
- `apps/frontend/app/page.tsx` -- mount the strip between PriceChart and Cockpit (only on a settled live snapshot)
- `apps/frontend/lib/api.ts` -- `fetchTaxonomy`, `declareThesis` (backend error detail passthrough), `fetchActiveThesis`
- `apps/frontend/lib/types.ts` -- `ThesisProjection`, `ThesisStatement`, `ResearchTaxonomy`, `DeclareResult` types; additive `thesis?` on `TapeSnapshot`

## How Values Flow (single source of truth)

- The active thesis is pushed live on the WS frame's `thesis` key (composed once server-side by the
  research monitor). `useTapeStream` parses each WS frame into `TapeSnapshot`, which now carries
  `thesis?`; the strip reads `snapshot.thesis` directly. After a successful declare the form simply
  closes — the next WS frame (within ~200 ms) carries the active thesis, so the strip never derives
  or caches a thesis client-side. The REST `GET /research/thesis/active` is the verbatim-equal
  counterpart used by `fetchActiveThesis` (available for probes; the live display uses the WS key).

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: Compiled successfully; type-check + lint clean; `/` route 12.2 kB / 115 kB first load.

## Known Issues

- The verdict badge always reads `pending` this iteration by design (transition engine is next).
- No `risk_flags` chips are rendered — the backend omits the field entirely (J-49 adds it); the strip
  has no placeholder for it (an empty placeholder would dishonestly imply "no risks found").
- Browser QA (Chrome MCP) was not run by the developer — that is the QA step. The strip's behavior
  was verified against the live backend's REST/WS responses (declare matrix + REST==WS thesis key).
