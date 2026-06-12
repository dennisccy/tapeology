**Verdict:** COHERENCE-PASS

## Coherence Audit — Iteration 18

**Session:** i_will_be_super_rich_with_my_loved_ones
**Iteration:** 18 (goal-i_will_be_super_rich_with_my_loved_ones-iter-18)
**Blueprint:** `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md`
**Diff base:** `6a7e2e4ec9ab7d27525189afa22a89692e7e31b9`

---

### Files changed (10)

- `apps/backend/app/config.py` — six new study config keys + `study_list_max` exclusion
- `apps/backend/app/main.py` — shutdown drain for in-flight study jobs
- `apps/backend/app/research/routes.py` — four new `/research/studies` endpoints
- `apps/backend/app/research/store.py` — `StudyRecord` dataclass + five new store methods (first writes to `studies`/`study_occurrences` tables)
- `apps/backend/app/research/taxonomy.py` — additive studies display copy
- `apps/frontend/components/NavBar.tsx` — Studies entry `enabled: false` → `enabled: true`
- `apps/frontend/lib/api.ts` — four study API functions
- `apps/frontend/lib/types.ts` — study TypeScript types
- `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` — iter-18 build-out note (row 23/24 additive) + `blueprint.reapproval-requested` marker

Not in the diff (confirmed absent): `app/engine/`, `app/providers/`, the classifier, history buffer, or any engine-adjacent file.

---

### Part A — Data Contract check

**Row 23 (Study results) — single owner, canonical endpoint, persist-once.**

The blueprint registers: computed by the study-runner module under `app/research/`, served by `POST/GET /research/studies` and `GET /research/studies/{id}`, `POST …/cancel`. Results persisted once at their defining moments; the UI computes nothing.

- Single owner: `apps/backend/app/research/studies.py` is the one module that runs studies and builds payloads. The `StudyJobManager` in that file is the only place that creates study payloads; routes in `routes.py` call `jobs.create()` / `jobs.start()` and serve `record.payload` verbatim (`routes.py:1183–1207`). No second computation path exists.
- Canonical endpoint: the four endpoints (`POST /research/studies`, `GET /research/studies`, `GET /research/studies/{id}`, `POST /research/studies/{id}/cancel`) are the exact set registered in row 23. The frontend exclusively calls `createStudy`, `fetchStudies`, `fetchStudy`, `cancelStudy` — each wired to the corresponding canonical endpoint in `apps/frontend/lib/api.ts:653–737`.
- Persist-once discipline: `store.set_study_result()` writes payload and occurrence rows in one `BEGIN IMMEDIATE` transaction at the terminal moment; `update_study_payload()` is used only for mid-run progress ticks (not results). The `StudyRecord` docstring explicitly states "canonical served result is `studies.payload` — occurrence rows mirror it, never a second computation."

**Row 27 (R basis) — registered consumer check.**

Blueprint row 27 states: the study runner (row 23) is the fourth registered consumer of the same `marks.r_basis` helper — never a second formula. Confirmed:
- `apps/backend/app/research/studies.py:80`: `from .marks import r_basis as _r_basis`
- `apps/backend/app/research/studies.py:272–289`: the `_compute_occurrence` function derives the synthetic invalidation (spread-multiple × spread, floored), then calls `r = _r_basis(arm_price, invalidation)`. No second formula. Identical treatment for setup arms and null arms (both call the same helper).

**Row 20 (Excursion outcomes) — registered consumer check.**

The study runner uses `ExcursionTracker` from `excursions.py` for per-occurrence ternary outcomes and truncation flags. `apps/backend/app/research/studies.py:76–79` imports `ExcursionTracker, TERNARY_MINUS, TERNARY_NEITHER, TERNARY_PLUS` from `.excursions`. This is the registered consumer path (row 20 machinery); no second excursion formula introduced.

**Row 24 (Taxonomy) — additive only, no hardcoded labels in frontend.**

The `taxonomy.py` diff adds `STUDY_STATUSES`, `STUDY_STATUS_ABSENCE_COPY`, and `STUDY_COPY` dicts (additive). The studies page (`apps/frontend/app/studies/page.tsx`) fetches taxonomy via `fetchTaxonomy()` → `GET /research/taxonomy`. No label is hardcoded in the frontend for the new studies copy.

**Row 21 (Journal analytics) — no pooling.**

No reference to `GET /research/analytics` in the studies page or any new frontend code. Studies are a separate surface and results are never fed into the analytics endpoint. Confirmed no cross-surface pooling.

**`config_fingerprint` — new keys.**

Five keys (`study_null_arm_count`, `study_arm_sustain_seconds`, `study_arm_cooldown_seconds`, `study_occurrence_r_spread_multiple`, `study_occurrence_r_floor`, `study_null_baseline_seed`) shape persisted study results and are NOT excluded from `config_fingerprint` (`config.py` exclusion set: only `study_list_max` is excluded). The `study_list_max` exclusion follows the documented iter-12 page-size precedent with rationale (it touches no persisted computation). No objective violation.

**No new value duplicates an existing registered value.**

Study results (row 23 build-out) are the pre-registered concept. No new value was introduced that is conceptually the same as rows 1–22 or 24–28.

Part A: no violations.

---

### Part B — Information Architecture check

**New route: `/studies`**

Blueprint IA canonical home: "J-60–J-62 (replay studies + CI reference study)" → `/studies` → nav section **Studies**. Confirmed: the page exists at `apps/frontend/app/studies/page.tsx` (Next.js app-router route `/studies`).

**Navigation path: `/studies` reachable in 1 click.**

- `apps/frontend/components/NavBar.tsx` — `NAV_ITEMS` now contains `{ href: "/studies", label: "Studies", enabled: true }`.
- `apps/frontend/app/layout.tsx` mounts `<NavBar />` in the root layout, so the Studies link appears on every page.
- From any page (Cockpit, Journal) the user clicks the "Studies" link in the persistent top bar → `/studies`. That is 1 click. ≤2 click requirement: satisfied.
- The link resolves: `href="/studies"` and the `apps/frontend/app/studies/page.tsx` file exists at that route.

**No duplicate home.**

The pre-existing IA defines no other page for replay studies. There is no second `/studies`-equivalent page; the entity has exactly one home.

**No parallel shell.**

The `/studies` page is placed inside the existing `apps/frontend/app/` Next.js app-router tree, under the same root `layout.tsx` that mounts `NavBar`. It uses the same dark instrument-panel styling. No new layout wrapper or independent nav was introduced.

**Nav-skeleton change: blueprint updated + `blueprint.reapproval-requested` present.**

The blueprint's iter-18 build-out note documents the skeleton change (Studies entry enabled). The spec's "Blueprint conformance" section confirms `state/blueprint.reapproval-requested` was written. The diff includes edits to `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` (the iter-18 note). This is the approved procedure for the one skeleton change of this session.

Part B: no violations.

---

### Part C — Advisory observations

None. The iteration is tightly scoped: one new route, one nav-enablement, the pre-registered endpoint set, and taxonomy-only copy ownership. No formatting drift, no label inconsistency, and no unregistered-but-new values observed. The `study_list_max` serving-only exclusion follows documented precedent with rationale and is consistent with prior session practice.

---

### Summary

All Data Contract checks (single owner, canonical endpoint, persist-once, R-basis via registered helper, excursion via registered machinery, no pooling, taxonomy-driven copy) pass. The `/studies` page lands at its pre-registered IA home, is reachable in 1 click from the persistent nav, has no duplicate home, and uses the established shell. The nav-skeleton change is documented in the blueprint with a `reapproval-requested` marker per protocol.

No FAIL-eligible violations found in either Part A or Part B.
