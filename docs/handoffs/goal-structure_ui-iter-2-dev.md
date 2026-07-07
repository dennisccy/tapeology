# goal-structure_ui-iter-2 Dev Handoff

**Phase:** goal-structure_ui-iter-2
**Date:** 2026-07-07
**Agent:** developer
**Status:** complete

## What Was Built

- **Registry section (J-02)** — a new read-only section appended to the existing `/structure` page,
  below the Levels & Zones section. It fetches `GET /research/strategies` on mount (independent of
  the Levels & Zones Load button) and renders:
  - Two strategy cards, `v1` and `structure_tape`, each showing its entry rule and exit fields
    (`r_stop`, `reward_target` only where the strategy actually defines one, `state_flip`,
    `horizon_seconds`, `dataset_end`) — every value `String(...)`-rendered verbatim from the payload.
  - `structure_tape`'s three class-scaled maps (`stop_bps_by_class`, `r_multiple_by_class`,
    `size_multiple_by_class`) as small class → value tables, rendered ONLY where the payload itself
    carries them (never assumed by strategy id).
  - A champion badge (`champion.strategy_id` / `champion.profile`), reusing `/performance/page.tsx`'s
    exact `champion-summary` / `champion-strategy` / `champion-profile` testid pattern, plus a
    cross-check caption against `GET /research/profiles`'s own `champion` (both read the same store
    pointer — the caption narrates agreement/disagreement, it never picks a value).
  - An honest "registry unavailable" state (`structure-registry-unavailable`, reusing the file's
    local `UnavailablePanel`) when `GET /research/strategies` is unreachable/non-200 — no fabricated
    strategy, no hardcoded `v1`/`default` fallback.
- **`fetchStrategies()`** in `apps/frontend/lib/api.ts` — mirrors `fetchProfiles()` byte-for-byte in
  structure (`{ok, strategies: StrategiesPayload | null, error?}`; `strategies: null` on any
  non-200/unreachable failure).
- **`Strategy` / `StrategyExits` / `StrategyExitRule` / `StrategiesPayload` types** in
  `apps/frontend/lib/types.ts`. `StrategiesPayload.champion` reuses `ProfilesPayload["champion"]`
  verbatim — no second champion shape was declared anywhere.
- **J-01 re-verification (not a rebuild):** confirmed by direct read that
  `apps/frontend/components/StructureChart.tsx` already carries the iter-1 audit's fix (line 99's
  `z-10` on the `!hasBars` overlay, line 100's "No candles to draw at this as-of time." copy). This
  file was **not touched** — no residual occlusion was found. Independent browser verification of
  this fix is the browser-qa-agent's job (per lessons.md iter-1(b), an in-tree fix isn't "done"
  until browser-QA re-runs independently); as the developer I confirmed the code state only.
- **No backend changes.** `git diff --stat -- apps/backend/` is empty — confirmed below.

## Files Changed

- `apps/frontend/lib/types.ts` -- added `StrategyExitRule`, `StrategyExits`, `Strategy`,
  `StrategiesPayload` (51 lines added, nothing removed).
- `apps/frontend/lib/api.ts` -- added `fetchStrategies()` beside `fetchProfiles()`, plus the
  `StrategiesPayload` import (23 lines added).
- `apps/frontend/app/structure/page.tsx` -- added the Registry section: `ClassMapTable` and
  `StrategyCard` components, the `championsMatch` helper, the `strategiesResult`/`profilesResult`
  state + mount-time `useEffect`, the derived `registry`/`profiles`/`championCrossCheck` values, and
  the new `<section aria-label="Strategy registry">` JSX block. The file's header doc-comment was
  extended to describe the two new endpoints; the existing Levels & Zones section and its four
  honest states are byte-unchanged (299 lines added, 12 removed — the 12 removed lines are the old
  header comment text replaced by the extended version, not functional changes).

No other files were touched. `apps/frontend/components/StructureChart.tsx`,
`apps/backend/app/research/strategies.py`, `apps/backend/app/research/profiles.py`,
`apps/backend/app/research/routes.py`, `apps/backend/app/meta.py`, and `apps/backend/app/config.py`
are all byte-identical to the pre-iteration tree.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: 1146 passed, 1 skipped, 0 failed (1147 collected — the same baseline iter-1 reported).
Expected and unaffected, since this iteration made zero backend edits; run to positively confirm
the J-04 regression sentinel rather than assume it.

Command: `cd apps/frontend && npm run build`
Result: `✓ Compiled successfully` — type-check (via `tsc --noEmit` under `next build`, `strict: true`
in `tsconfig.json`) and production build both passed with no errors or warnings. `/structure`
compiles to 5.34 kB (up from the iter-1 baseline; still a static page).

Command (directly, not via a test suite — no frontend unit-test runner exists in this project, see
`README.md`'s verified "Run tests" section): `.venv/bin/python -c "from app.config import CONFIG;
print(CONFIG.config_fingerprint())"` → `4d665603569b9dbf`, matching the pinned J-04 value exactly.

## Live verification performed

Ran the actual app end to end via `scripts/dev.sh` (backend :8301, frontend :3301 — this machine's
deterministic port offset) and drove it with the Chrome DevTools Protocol browser tool:

1. **Populated Registry, fresh backend + real data.** Navigated to `/structure` with neither symbol
   nor as-of filled in (Load never clicked). The Registry section rendered anyway (confirms it is
   independent of the Load button, per the spec's "New user actions: none... renders on page load").
   Extracted the DOM text and diffed it field-by-field against a direct `curl
   http://localhost:8301/research/strategies` / `.../research/profiles` — every value matched
   exactly: `v1`'s card showed `entry rule=state_native_sustained_premise`,
   `r_stop=synthetic_invalidation_at_arm` (correctly no `reward_target` row — v1 genuinely has none),
   `state_flip=opposing_control_state`, `horizon (seconds)=120`,
   `dataset_end=forced_exit_at_last_recorded_price`; `structure_tape`'s card additionally showed
   `reward_target=class_r_multiple_bounded_by_next_opposing_level` and its three class maps
   (`stop_bps_by_class` A=1/B=5/C=10, `r_multiple_by_class` A=3/B=2/C=1, `size_multiple_by_class`
   A=2/B=1/C=0.5) — byte-for-byte identical to the live JSON. The champion badge showed
   `strategy=v1`, `profile=default`, with the cross-check caption reading "Confirmed identical to the
   champion served by GET /research/profiles — one store pointer, two read views." Screenshot saved
   (not committed — this developer's own sanity check, not the formal QA evidence capture).
   `data-testid` inventory extracted via `document.querySelectorAll('[data-testid]')` confirmed every
   planned testid is present exactly once per card (`strategy-card` ×2, `strategy-exit-reward-target`
   present only on the `structure_tape` card, the three class-map testids present only there too).
   No Next.js dev error overlay was present (checked the `nextjs-portal` shadow root for a
   `[data-nextjs-dialog]` — none found).
2. **Registry-unavailable honest state.** Killed only the backend process (frontend left running),
   reloaded `/structure`: the Registry section rendered `structure-registry-unavailable` with
   "Backend unreachable — is the API running?" / "Nothing cached and nothing fabricated is shown in
   its place." — no strategy cards, no champion badge, no hardcoded `v1`/`default` fallback.
   Screenshot saved.
3. **Restart resilience (pre-handoff checklist).** Re-ran `scripts/dev.sh` with the frontend still up
   from the previous run: it correctly killed the leftover frontend PIDs on port 3301 and started
   both services fresh with no port conflicts (`Application startup complete.` /
   `✓ Ready in 1193ms`). Reloaded `/structure` again — Registry repopulated correctly.
4. **No regression spot-check.** Loaded `/performance` — its own `champion-summary` block (a
   pre-existing, byte-unchanged component) rendered correctly, confirming the new `/structure`
   Registry section's reuse of the same testid strings on a **different route** causes no collision
   or interference.
5. **Server cleanup.** Killed the dev processes at the end. Note for whoever runs this pipeline's own
   cleanup: this uvicorn `--reload` setup reparents its actual worker to a `multiprocessing.spawn`
   process whose own command line does **not** contain the string "uvicorn" at all (confirmed via
   `ps`), so a broad `pkill -f "uvicorn main:app"` can miss it and leave the port held — a `lsof -ti
   :$PORT | xargs kill -9` (port-based, not pattern-based) is what actually caught it here, and is
   exactly what `scripts/dev.sh`'s own built-in cleanup logic already does before each start.

## Design notes (for the reviewer)

- **Why `dataset_end` is rendered even though the spec's exit-precedence phrase only names four
  fields:** `docs/goal.md` / the phase spec both frame the exit precedence as
  "r_stop → reward_target → state_flip → horizon" (four items). The plan's own "Assumption flagged
  for the developer" section resolves this explicitly: render each exit field's actual value
  verbatim in a fixed order chosen by the developer, suggesting "r_stop, reward_target if present,
  state_flip, horizon_seconds, dataset_end" — I followed that suggested order exactly. The
  precedence phrase itself is kept as a static caption (prose describing the runner's general
  exit-check order, not a literal JSON field), matching the plan's explicit guidance not to derive
  ordering from `Object.keys()`.
- **Champion cross-check caption, not a second champion widget:** the champion badge is sourced
  from `GET /research/strategies`'s own `champion` (matching the DoD's literal wording), and
  `GET /research/profiles` is fetched only to narrate agreement via `championsMatch()` — a plain
  `===` comparison on the two known string fields, never a value-picking "resolution". This is
  additive, cheap (a few lines), and directly answers the DoD's "it equals
  `GET /research/profiles`'s champion byte-for-byte" bullet with a live, browser-visible confirmation
  rather than leaving that check to happen only in a separate audit step. A genuine mismatch is
  structurally near-impossible (one shared store call backs both endpoints) so that branch could
  not be exercised live — it exists only so a real single-source-of-truth violation would never be
  silently hidden, per the interlude's own honest-state discipline.
- **Class-scaled maps render via `Object.entries()`, never assumed to be exactly `{A,B,C}`:** this
  mirrors `SrLevel.type`'s existing precedent in this same file (tolerate an unrecognized-but-real
  value rather than a rigid enum/union) and means the three `ClassMapTable` occurrences (the
  "third occurrence" abstraction threshold) render whatever classes the payload actually carries, in
  the payload's own key order — never re-sorted, never hardcoded to `["A","B","C"]`.
- **v1's `r_stop.spread_multiple` / `r_stop.floor` are intentionally not rendered.** Every planning
  document (`docs/goal.md`, the phase spec's Steps and "New information displayed" bullets, and the
  plan's "What to Build") independently enumerates the SAME minimal field set to display: entry
  rule; r_stop/reward_target/state_flip/horizon_seconds (rule names + the horizon number); and,
  for `structure_tape` only, its three class-scaled maps. None of the four sources ask for v1's own
  `r_stop` sub-parameters, so they are modeled in the `StrategyExitRule` type (structurally present,
  since I don't declare an index signature that would hide them) but not rendered — keeping both
  cards' field sets consistent and matching every spec source exactly, rather than rendering more
  for v1 than any document asked for.

## Known Issues

None outstanding. The one process-cleanup nuance (uvicorn `--reload`'s worker not matching a
pattern-based `pkill`) is noted above as an operational observation for the pipeline, not a defect
in the shipped code — `scripts/dev.sh`'s own port-based cleanup already handles it correctly, as
verified by the restart test in step 3 above.

The `structure-champion-crosscheck-mismatch` branch (and its distinct copy) is unreachable in this
codebase's current architecture (both endpoints share one store call) and could not be exercised
live — this is intentional defensive code, not a gap, but flagging it for the reviewer/auditor since
"no handler for states the system cannot reach" is this project's own simplicity bar. I judged this
one exception worth keeping because a silent single-source-of-truth violation is exactly the failure
mode the interlude's anti-goals call out most strongly, and the branch costs three lines.
