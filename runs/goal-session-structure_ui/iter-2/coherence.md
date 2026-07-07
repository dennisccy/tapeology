# Iteration 2 — Coherence Audit

**Iteration:** goal-structure_ui-iter-2
**Date:** 2026-07-07
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Registered strategies (`v1`, `structure_tape`) + class-scaled params | OK | Read via new `fetchStrategies()` (`apps/frontend/lib/api.ts:410-424`) → `GET /research/strategies` → `apps/backend/app/research/strategies.py:28-37` (`strategies_projection`, unchanged this iteration, still built from `Config.strategy_definition`). `StrategyCard`/`ClassMapTable` (`apps/frontend/app/structure/page.tsx:118-234`) render every field via `String(value)` / `Object.entries(map)` — no arithmetic, no re-sort, no re-derivation. |
| Champion pointer (founding `v1`/`default`) | OK | Confirmed both serving endpoints call the identical single source: `apps/backend/app/research/strategies.py:37` and `apps/backend/app/research/profiles.py:58` both do `"champion": store.get_champion_pointer()` — no backend diff this iteration (verified: `git diff` touches zero files under `apps/backend/`). Frontend: `registry.champion` (`GET /research/strategies`) is the value badged (`page.tsx:355,364`); `profiles.champion` (`GET /research/profiles`, pre-existing `fetchProfiles()`) is read **only** for the `championsMatch()` equality narration (`page.tsx:240-245`, `296-314`) — it never overrides or resolves the displayed value. `StrategiesPayload.champion` is typed as `ProfilesPayload["champion"]` (`apps/frontend/lib/types.ts:1078`, confirmed `ProfilesPayload.champion: { strategy_id: string; profile: string }` at `types.ts:951-954`) — one shape, not a second one. No `set_champion_pointer` call anywhere in the diff. |
| Exit-precedence caption text | OK (not a contract value) | `EXIT_PRECEDENCE_CAPTION` (`page.tsx:111-112`) is static prose quoting the phase spec's own words describing display order; every individual exit field (`r_stop`, `reward_target`, `state_flip`, `horizon_seconds`, `dataset_end`) still renders its own real value verbatim beside it. Not a computed or fetched value — nothing to register. |

No new displayed value/entity falls outside the blueprint's Data Contract — the Registry section exposes finer-grained fields (entry rule, per-exit rules, class-scaled maps) of the two rows already registered ("Registered strategies…" and "Champion pointer…"), not a new concept.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/structure` Registry section (J-02) | OK | Blueprint IA table row: "J-02 … `/structure` (Registry section) … Structure". The diff adds the section to the existing `apps/frontend/app/structure/page.tsx` (lines 324-384) — no new route file, no new nav entry. Confirmed `git diff` touches neither `apps/frontend/components/NavBar.tsx` nor `apps/backend/app/meta.py` (both empty diffs) — the top-bar's data-driven `UI_ROUTES` list is unchanged, so reachability is unchanged: 1 click from the persistent top bar to `/structure`, then the Registry section is simply further down the same page (no additional click). |
| Champion shown a second time (on `/structure`, alongside its pre-existing `/performance` display) | OK — not a duplicate home | The blueprint's Data Contract explicitly sanctions this: "Champion pointer … one pointer, two read views." `/performance/page.tsx` (pre-existing, unmodified) already renders `champion-summary`/`champion-strategy`/`champion-profile` from `fetchProfiles()`; `/structure` now renders the same value from `fetchStrategies()`. Both are read views of one store pointer, not two competing pages for the same routed feature — no "second results page" pattern applies here. |

No parallel shell introduced (`Panel`, `LoadingPanel`, `UnavailablePanel` are reused, not redefined — confirmed only `StrategyCard`, `ClassMapTable`, and the `championsMatch` helper are new, all local to `page.tsx` and consumed by the existing shell).

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md`'s new "Structure page" bullet (added this iteration, `README.md` line 22) documents only J-01 (levels/zones on a candlestick chart) and does not mention the Registry/champion capability this iteration just shipped; the pre-existing "Strategy registry and a tape-confirmed structure strategy" bullet (unchanged, same file) still reads as if the registry/champion were reachable only "through the research API and the matching machine-readable tool," which is now stale — they are also in-browser at `/structure`. Documentation-only drift (no code/data-source impact); suggest the next README pass (readme-maintainer) cross-reference the new Registry section.
- The new `/structure` Champion panel intentionally reuses `/performance`'s exact `data-testid` strings (`champion-summary`, `champion-strategy`, `champion-profile`) across two different components/routes. This is a deliberate, contract-consistent choice (same value, same shape, same source) rather than a coherence defect, and the ui-surface-map (`reports/phase-goal-structure_ui-iter-2-ui-surface-map.md`) already directs browser-QA to independently re-verify `/performance`'s own badge is unaffected. Noting only so a future DOM-wide test query doesn't accidentally cross-match the wrong page's element.

## Verification performed

- Read blueprint (`runs/goal-session-structure_ui/state/blueprint.md`), iteration spec (`docs/phases/goal-structure_ui-iter-2.md`), ui-surface-map, and the full noise-excluded diff since snapshot `fe218a66cabad30f9fb49706851e30e3b8b3c606` (`iter-diff.md` was absent, so generated directly per the invocation's fallback command; 487 lines, 4 files: `README.md`, `apps/frontend/app/structure/page.tsx`, `apps/frontend/lib/api.ts`, `apps/frontend/lib/types.ts`).
- Excluded-path stat showed only harness bookkeeping (`runs/goal-session-structure_ui/*`, `reports/goal-session-structure_ui-index.html`, iteration-1 summary docs, `telemetry.jsonl`, `trace.jsonl`, `project-story.md`) — no dependency lockfiles changed.
- Confirmed via direct grep: `apps/backend/app/research/strategies.py:37` and `apps/backend/app/research/profiles.py:58` both read `store.get_champion_pointer()` (true single source); `apps/frontend/components/NavBar.tsx` and `apps/backend/app/meta.py` show zero diff (nav/IA untouched); `apps/frontend/components/StructureChart.tsx:99-100` confirmed the J-01 `z-10` empty-state fix is present and byte-unchanged this iteration.
- No backend files appear anywhere in the diff, matching the spec's "zero backend edits" claim.
