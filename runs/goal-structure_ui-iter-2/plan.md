# goal-structure_ui-iter-2 Execution Plan

Scope check against `docs/goal.md`: **aligned, no drift.** This iteration is squarely inside the
"Structure, made visible" interlude (Key Capability 3: "Strategy registry & champion view") and
inside J-02's own acceptance criteria verbatim. J-03 (backtest comparison) and any backend/champion
mutation are correctly excluded by the phase spec's own OUT OF SCOPE section — no scope-creep to flag.
Depth **full** is justified (closing J-01 needs the phase-closure + ux-regression steps that only the
full pipeline runs; J-02 touches the frozen champion pointer, which needs the coherence lane).

## What to Build

- **Registry section on `/structure`** (below the existing Levels & Zones section, page.tsx): two
  cards, `v1` and `structure_tape`, each showing its entry rule and exit fields (`r_stop`,
  `reward_target` where the strategy defines one, `state_flip`, `horizon_seconds`) plus
  `structure_tape`'s class-scaled `stop_bps_by_class` / `r_multiple_by_class` / `size_multiple_by_class`
  — every field printed verbatim (`String(value)`, the page's established precedent).
- **Champion badge**, read from `champion.strategy_id` / `champion.profile`, cross-checked against
  `GET /research/profiles`'s `champion` (both must agree — they share one store source).
- **Registry-unavailable honest state**: endpoint non-200/unreachable → explicit distinct panel, no
  fabricated strategy or champion.
- **Registry section renders on page load**, independent of the existing Load button (which only
  gates the Levels & Zones fetch) — the spec's own "New user actions: None... renders on page load" is
  explicit, and the registry/champion are populated even keyless, so there is no reason to gate this
  section behind the symbol/as-of form.
- **J-01 independent re-verification only** — see "Files to Create/Modify" below: no code change is
  expected here. Confirmed by direct inspection that the iter-1 audit's fix is already committed
  (`StructureChart.tsx:98-100` carries `z-10` on the `!hasBars` overlay and the corrected copy "No
  candles to draw at this as-of time."). This iteration's job is a **fresh, independent** browser-QA
  pass against the current tree (per lessons.md iter-1(b): an auditor's in-tree fix is not "done" until
  browser-QA re-runs independently and the records reconcile into a CLOSURE-PASS) — not a re-implementation.
- **J-04 regression sentinel stays green**: full backend suite, `config_fingerprint`
  `4d665603569b9dbf` unchanged, engine equivalence, and the four prior surfaces + 5-link nav intact.

## Agents Required

- developer: yes -- implement the frontend-only Registry section (`types.ts`, `api.ts`, `page.tsx`);
  confirm (not re-fix) that the StructureChart.tsx J-01 fix is intact and touch it ONLY if browser-QA
  surfaces a residual occlusion; run the backend suite + frontend build; write the dev handoff.
- backend-data: no -- `GET /research/strategies` (`apps/backend/app/research/strategies.py` →
  `strategies_projection`) and `GET /research/profiles` already exist, are unchanged, and both read the
  SAME `store.get_champion_pointer()` source. Confirmed live in `routes.py:1785-1809` and
  `meta.py:24-31` (the `/structure` nav entry already shipped in iter-1). Zero backend edits this
  iteration — any backend diff is a defect.
- frontend-ux: yes -- new Registry section (two strategy cards + champion badge + honest unavailable
  state) appended to the existing `/structure` page. No new route, no nav change (already shipped).

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

- `apps/frontend/lib/types.ts` -- add `Strategy` and `StrategiesPayload` interfaces mirroring the
  served `GET /research/strategies` shape (`strategies: Strategy[]`, each with `strategy_id`,
  `entries` (rule + params), `exits` (`r_stop`, optional `reward_target`, `horizon_seconds`,
  `state_flip`, `dataset_end`), `fees`, `slippage`, `dollars_per_r`, and — for `structure_tape` only —
  `size_multiple_by_class`). Keep `type` fields loose (`string`/`Record<string, unknown>` where the
  exact shape varies by strategy) rather than a rigid union, matching `SrLevel.type`'s existing
  precedent of tolerating an unrecognized-but-real value. **Reuse `ProfilesPayload["champion"]`'s type
  for `StrategiesPayload.champion`** (e.g. `champion: ProfilesPayload["champion"]`) — do not declare a
  second champion shape; the backend serves both from the identical store call.
- `apps/frontend/lib/api.ts` -- add `fetchStrategies()`, mirroring `fetchProfiles()` byte-for-byte in
  structure (`{ ok, strategies: StrategiesPayload | null, error? }`; `fetch(`${API_BASE}/research/strategies`)`;
  on non-200 or a thrown error, `strategies: null` with an explicit message — never a fabricated
  registry).
- `apps/frontend/app/structure/page.tsx` -- add a `useEffect(() => { ... }, [])` on mount (mirroring
  `/performance/page.tsx`'s own `fetchPnlLedger`/`fetchProfiles` effect) that calls both
  `fetchStrategies()` and `fetchProfiles()` (new import — `fetchProfiles` is not currently imported
  here) independent of the existing `handleLoad`/Load-button flow. Render a new `<section>` below the
  "Confluence zones" `Panel`: two strategy cards (reuse the `Panel`/`article` card visual language
  already in this file and in `/performance/page.tsx`'s `LedgerRowPanel`) plus a champion badge (reuse
  `/performance/page.tsx`'s `champion-summary`/`champion-strategy`/`champion-profile` dl pattern) plus
  the existing local `LoadingPanel`/`UnavailablePanel` components for the loading/unavailable states
  (already defined in this file — reuse them, do not redefine).
- `apps/frontend/components/StructureChart.tsx` -- **no change expected.** Confirmed via direct
  read: line 99 already has `z-10` on the `!hasBars` overlay and the caption already reads "No candles
  to draw at this as-of time." Touch this file ONLY if the independent browser-QA re-verification of
  the levels-but-no-zones state finds a residual occlusion — if so, the fix is the same explicit-z-index
  remedy already applied here (nothing new to invent).
- **No backend files.** `apps/backend/app/meta.py` (`/structure` entry), `research/strategies.py`,
  `research/profiles.py`, `research/routes.py` (`GET /strategies`, `GET /profiles`), and `config.py`
  (`strategy_registry()`, `strategy_definition()`) all already serve exactly what this iteration needs.
  A diff touching any of these is out of scope and a defect against the critical "no new backend
  computation or endpoint" anti-goal.
- `docs/handoffs/goal-structure_ui-iter-2-dev.md` -- dev handoff (required by the DoD).

### Assumption flagged for the developer (documented, not a blocking question)

The phase spec (and `docs/goal.md`) both describe the "exit precedence" as the fixed phrase
`r_stop → reward_target → state_flip → horizon`. This is **prose framing describing the runner's
general exit-check order**, not a literal field to read out of the JSON — `v1`'s `exits` object has no
`reward_target` key at all (only `structure_tape` does), and neither strategy's raw dict key order
matches that phrase exactly (`horizon_seconds` sits before `state_flip` in both payloads, and
`dataset_end` is also present but not named in the phrase). Recommended approach: render each exit
field's own actual value **verbatim** from the payload (present fields only — `v1`'s card naturally
omits `reward_target` since the field is genuinely absent, an honest omission, not a gap), in a fixed
display order chosen by the developer (e.g. r_stop, reward_target if present, state_flip,
horizon_seconds, dataset_end), and use the spec's phrase as a static caption describing that order —
never derive the ordering from `Object.keys()` (fragile) and never fabricate a `reward_target` value
for `v1`.

### Stack/test-command source note (matches iter-0/iter-1 precedent — not this iteration's scope to fix)

`.claude/project-template.md` is still the generic, unfilled template (both prior dev handoffs in this
session already documented this). Use `README.md`'s verified "How to run"/"Run tests" section instead
(cross-checked against `apps/backend/pyproject.toml` / `apps/frontend/package.json`): backend tests via
`cd apps/backend && .venv/bin/python -m pytest tests/ -v` (1147 collected baseline per iter-1's
handoff); frontend has no unit-test runner, so `cd apps/frontend && npm run build` is the full extent
of automated frontend verification (type-check + compile), matching every prior `/performance`,
`/studies` precedent.

## UI Evolution

- **New user-facing capability:** on `/structure`, a person can read both registered strategies
  (`v1`, `structure_tape`) with their config-owned parameters and see the current champion — inside
  the app, not only via `curl`/MCP.
- **New information displayed:** each strategy's entry rule, exit rules (`r_stop`, `reward_target`
  where defined, `state_flip`, `horizon_seconds`), and `structure_tape`'s class-scaled
  `stop_bps_by_class` / `r_multiple_by_class` / `size_multiple_by_class` maps; the champion pointer
  (`champion.strategy_id` / `champion.profile`, founding `v1`/`default`).
- **New user actions:** none — the Registry section is read-only, no form/button/input; it fetches and
  renders on page load.
- **UI surface changes:** one new "Registry" section appended to the existing `/structure` page, below
  the Levels & Zones section. J-01's section is functionally unchanged (already-applied z-index fix is
  only re-verified, not re-built).
- **Navigation changes:** none — the `/structure` nav entry already shipped in iter-1
  (`meta.py` `UI_ROUTES`, `nav: true`).

## Visual Requirements

- **Component patterns:** reuse the existing local `Panel` wrapper (already imported in `page.tsx`)
  for the Registry section container; strategy cards follow `/performance/page.tsx`'s
  `LedgerRowPanel`/`article` card shape (`rounded-lg border border-slate-800 bg-slate-900/60 p-4`,
  `data-testid` + a stable data attribute like `data-strategy-id`); the champion badge follows
  `/performance/page.tsx`'s `champion-summary` `dl` block (`champion-strategy` / `champion-profile`
  testids) — do not invent a new visual language for either.
- **Layout:** single column, appended below the existing sections, `max-w-7xl` (matches the rest of
  this page and every other page) — no sidebar, no new grid.
- **Key visual effects:** none new. Font-mono numerics via the page's existing `NUMERIC_CELL`/
  `LABEL_CELL` constants; the A/B/C zone badge's neutral slate treatment is precedent for the
  strategy-card class-map tables (no invented traffic-light semantics); amber
  `border-amber-800/60 bg-amber-900/20 text-amber-300` for the registry-unavailable state, via the
  already-defined local `UnavailablePanel`.
- **States to handle:** loading (reuse local `LoadingPanel`), registry-unavailable (reuse local
  `UnavailablePanel` with its own distinct message and `data-testid`, e.g.
  `structure-registry-unavailable`), populated (two strategy cards + champion badge, both cross-read
  against `/research/profiles`).

## Key Test Scenarios

- **J-02 populated:** Registry section renders `v1` and `structure_tape` cards whose entry rule, exit
  fields, and (for `structure_tape`) `stop_bps_by_class`/`r_multiple_by_class`/`size_multiple_by_class`
  match `GET /research/strategies` byte-for-byte; screenshot in
  `reports/qa/goal-structure_ui-iter-2-evidence/`.
- **J-02 champion:** badge shows `v1`/`default`, equal to both `/research/strategies` and
  `/research/profiles` byte-for-byte; screenshot captured.
- **J-02 honest state:** registry endpoint unreachable/non-200 → explicit distinct "registry
  unavailable" panel, no fabricated strategy/champion; screenshot captured.
- **J-01 re-verify (levels-but-no-zones):** a **fresh, independent** browser-qa-agent pass (not a
  citation of iter-1's evidence) against the current `StructureChart.tsx` shows "No candles to draw at
  this as-of time.", not a blank box; screenshot captured.
- **J-01 re-verify (populated levels/zones):** chart + zones table still render byte-for-byte as before
  — confirms the new Registry section introduces no regression to the existing section.
- **J-01 closure:** iteration-2's `ui-test-results` / `ux-regression` / `status.json` reconcile
  internally (no contradiction like iter-1's CLOSURE-FAIL); phase-closure verdict is CLOSURE-PASS.
- **J-04 regression sentinel:** backend suite green (1147 collected baseline, zero regressions),
  `config_fingerprint` still `4d665603569b9dbf`, SIM-BUYER/SIM-SELLER cockpit flows settle correctly,
  `/journal` `/studies` `/performance` unchanged, 5-link nav intact.
- **`fetchStrategies()` unavailable path:** non-200/unreachable → `strategies: null`, mirroring
  `fetchProfiles()`'s established behavior (verified functionally/live — no frontend unit-test runner
  exists in this project).
- **Coherence / single-source-of-truth:** diff is frontend-only (`types.ts`/`api.ts`/`page.tsx`
  additive; `StructureChart.tsx` untouched unless a residual J-01 occlusion is found); no second
  champion shape defined; no `set_champion_pointer` call added; no new backend endpoint or
  computation.
