# goal-i_will_be_rich-iter-3 Dev Handoff

**Phase:** goal-i_will_be_rich-iter-3
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete
**Depth:** lean (frontend config-only; no backend change)

## What Was Built

A single, isolated root-cause fix to the cockpit's color layer. **Backend untouched.**

- **`apps/frontend/tailwind.config.ts`** — added `./lib/**/*.{ts,tsx}` to the Tailwind
  `content` globs (with an explanatory comment). This is the spec's *preferred root-cause
  fix*: the 8 color classes the cockpit returns dynamically live as literal strings in
  `apps/frontend/lib/format.ts`, but `./lib` was never scanned, so Tailwind's content
  scanner never emitted them and the load-bearing color semantics rendered colorless.

That is the entire change. No `format.ts` refactor, no safelist, no new files, no
backend/engine/classifier/API/config edits, no new panels/routes/controls/values.

## Root cause (confirmed by measurement, not by eye — iter-2 lesson)

`lib/format.ts` is the **only** source of runtime-built color classes in the frontend
(verified by grep: no other file constructs color classes via template literals or returns
color strings). Its helpers `stateColor` / `stateBarColor` / `sideColor` / `impactColor`
can return exactly these 8 classes, all as plain string literals:

```
text-emerald-400  text-rose-400  text-amber-400  text-slate-400  text-slate-300
bg-emerald-500    bg-rose-500    bg-amber-500
```

Because `tailwind.config.ts` scanned only `./app` and `./components`, the base utilities
that appear *only* in `./lib/format.ts` were absent from the built bundle. Three were
genuinely missing; the other five happened to be present *incidentally* via static usage
in components (and the spec explicitly says do not rely on that).

## Evidence — red → green build measurement

I deliberately measured the served bundle before and after (the iter-2 false-PASS came from
a screenshot glance; the stylesheet-rule probe is the truth). Probe = base-utility selector
`.<class>{` in the compiled CSS, which **excludes** variant forms such as
`.hover\:bg-emerald-500:hover{`. I self-verified the probe: `bg-emerald-500` existed in the
old bundle **only** as the `hover:` variant — a naive `grep bg-emerald-500` would have given
the exact false PASS that fooled iter-2; the base-selector probe correctly reported MISSING.

**RED — `npm run build` with the unfixed config** (`.next` cleared first):

| class | base utility present? |
|-------|-----------------------|
| `text-emerald-400` | **MISSING** ← headline "Buyer Control" rendered slate |
| `bg-emerald-500`   | **MISSING** ← confidence-bar fill was transparent |
| `bg-amber-500`     | **MISSING** ← J-04/05/06 absorption bar latent-broken |
| `text-rose-400`, `text-amber-400`, `text-slate-400`, `text-slate-300`, `bg-rose-500` | present (incidental static use) |

**GREEN — `npm run build` with `./lib` scanned** (`.next` cleared first): **all 8 present**,
with exact Tailwind-v3 default values (`theme.extend` empty), confirming emerald — **not**
slate `rgb(226 232 240)`:

```
.text-emerald-400{...color:rgb(52 211 153/var(--tw-text-opacity,1))}   → getComputedStyle: rgb(52, 211, 153)
.bg-emerald-500  {...background-color:rgb(16 185 129/var(--tw-bg-opacity,1))} → rgb(16, 185, 129)
.bg-amber-500    {...background-color:rgb(245 158 11/...)}              → rgb(245, 158, 11)
.bg-rose-500     {...background-color:rgb(244 63 94/...)}              → rgb(244, 63, 94)
```

**GREEN — dev server** (`next dev`, `NEXT_PUBLIC_API_URL=http://localhost:8650`, clean
startup, `GET /` → HTTP 200 — *not* a 500-trap SKIP): fetched every CSS/JS asset the page
references and probed each → **all 8 base utilities present in the dev-served stylesheet**
too. (Dev server was started on an isolated port 3771 and killed afterward — no orphan
processes.)

## Files Changed

- `apps/frontend/tailwind.config.ts` — add `./lib/**/*.{ts,tsx}` to `content` so
  `lib/format.ts`'s dynamic color classes are emitted as base utilities (+10/−1, incl. comment).

## Tests Run

- **Frontend build:** `cd apps/frontend && npm run build` → **clean** (Compiled
  successfully; 4/4 static pages; no type errors). Served bundle contains all 8 base
  utilities (measured, above).
- **Backend regression:** `cd apps/backend && .venv/bin/python -m pytest tests/` →
  **24 passed in 4.13s** — unchanged from iter-2 (expected 24/24). No backend file was
  touched, so this is the empirical guard that the color fix changed no engine value (J-08).

## Known Issues

- None functional. The change touches only which CSS utilities Tailwind emits; it cannot
  alter any engine-computed value, so there is no regression path to J-08 (single source of
  truth holds — a colorless number and a green number are the same number).
- **`bg-amber-500` / `bg-rose-500` are now present even though `SIM-BUYER` never renders
  them.** This is intentional per the DoD/forward-value note: it pre-empts the identical
  latent breakage for J-03 (rose bar) and J-04/05/06 (amber absorption/unclear), which share
  the dynamic-only pattern. They are verified present in the bundle but are *not* exercised
  on screen this iteration.

## Notes for QA (browser-qa-agent — the real gate)

- **Precondition (iter-1 lesson, mandatory):** `rm -rf apps/frontend/.next`, then restart the
  managed dev server with `NEXT_PUBLIC_API_URL` set, and confirm `GET /` → HTTP 200 before
  driving the browser. An all-SKIPPED run is not verification. *(Note: a harness-managed dev
  server is already running on :3650/:8650; my build steps cleared `.next`, so a clean
  restart per this precondition is required regardless to avoid stale CSS.)*
- **Color verification = `getComputedStyle` + a `document.styleSheets` rule probe, NOT a
  screenshot glance.** On `SIM-BUYER`, assert each of these computes **emerald**, explicitly
  not slate `rgb(226, 232, 240)`:
  - (a) headline state label — `TapeStatePanel.tsx:16`, class via `stateColor` → `text-emerald-400` → `rgb(52, 211, 153)`
  - (b) confidence-bar fill — `TapeStatePanel.tsx:25`, class via `stateBarColor` → `bg-emerald-500` → `rgb(16, 185, 129)`
  - (c) a BUY trade-side cell — `RecentTradesPanel.tsx:24`, class via `sideColor("buy")` → `text-emerald-400`
  - (d) the positive `buy_price_impact` value — `FeaturesPanel.tsx:55`, class via `impactColor(>0)` → `text-emerald-400`
- **Latent-class guard:** also run the `styleSheets` rule probe over all 8 classes (including
  the amber/rose ones `SIM-BUYER` does not render) and assert each resolves to a non-null
  rule — so J-03/04/05/06 are not left latent-broken.
- **J-08 re-verify:** UI `tape_state` / `confidence` / features must still exactly match
  `GET /tape/SIM-BUYER/state` and `.../features` (the color fix changed no value).
- **Escalation (per spec):** stay lean unless browser re-verify surfaces a *second* defect
  (a missed class, or a dev-server/build interaction that regresses the served bundle).

## Anti-goal / scope check

- **Single source of truth:** no value recomputed or re-derived in the UI — config-only change. ✓
- **No fabricated data:** none. ✓
- **Price-impact guard intact:** no backend/classifier change; buyer_control still requires
  positive `buy_price_impact`. ✓
- **In scope only:** only `tailwind.config.ts`; J-03 not started; stream-status-dot
  consolidation left untouched (deferred, not worsened). ✓
