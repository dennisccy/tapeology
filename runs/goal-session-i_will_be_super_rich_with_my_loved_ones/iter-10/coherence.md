**Verdict:** COHERENCE-PASS

## Coherence Audit — iter-10 (J-48: thesis geometry on the price chart)

**Session:** i_will_be_super_rich_with_my_loved_ones
**Iteration:** 10 (lean)
**Snapshot SHA:** 431b8740c53e79396b3170b1c30e8569fd2c2fc4

---

### Step 1 — Data Contract check

**Blueprint row 15 — Thesis projection (the `geometry` key, additive note registered by the decomposer)**

The decomposer registered the `geometry` key as an additive note on row 15: computed ONLY inside the single `build_projection` builder, served by `GET /research/thesis/active?ticker=` + the WS `thesis` key, drawn verbatim by the chart on the row-13 epoch anchor.

Findings:

1. **Computation owner — single path confirmed.** The only implementation of geometry computation is `_build_geometry` in `apps/backend/app/research/monitor.py:151`, called exclusively from `build_projection` at line 316. No second function, no second module, no client-side computation of price-lines or marker positions. No violation.

2. **Serving endpoint — canonical only.** `GET /research/thesis/active?ticker=` is the single endpoint that serves the projection (including `geometry`). The WS `thesis` key re-exposes the same projection verbatim (the existing REST-equals-WS parity test is extended at `apps/backend/tests/test_research_api.py:285` to cover `geometry`). No second endpoint is added. `apps/backend/app/research/routes.py` shows all `build_projection` calls pass `verdict_events` from `self._store.verdict_events(...)` — the canonical append-only store. No violation.

3. **Frontend consumption — verbatim read, no client-side recomputation.** `apps/frontend/components/PriceChart.tsx` reads `thesis?.geometry` verbatim and draws it. The `anchor + logical_ts` mapping is the established row-13 additive display offset (the `toClock` helper pre-exists from J-31 and is reused unchanged for thesis markers at line 299 — it is a display formatting step, not a recomputation of time basis, price, state, or side). The chart computes no verdict/state/price/direction. No violation.

4. **New displayed values — no synonym duplicates.** The `geometry` key (price-lines + markers) is genuinely new (registered by the decomposer in blueprint row 15 as an additive note). It is a pure projection of already-contracted values (row-16 timeline rows, row-18 marks, row-15 thesis prices) and does not recompute any of those values independently. The display-copy labels (`GEOMETRY_INVALIDATION_LINE_LABEL`, `GEOMETRY_LEVEL_LINE_LABEL`, `GEOMETRY_ENTRY_MARK_LABEL`, `GEOMETRY_EXIT_MARK_LABEL`, `GEOMETRY_FIRST_CONFIRMATION_LABEL`, `verdict_marker_label`) are added to `apps/backend/app/research/taxonomy.py` (the registered row-24 canonical module for taxonomies and research display copy) — the frontend hardcodes none of them. No violation.

**All registered Data Contract values: no new independent computation, no non-canonical source. PASS.**

---

### Step 2 — Information Architecture check

**New surfaces in this iteration:** None. The spec explicitly states "No new pages, no nav change, no new panels." The diff confirms: only `monitor.py`, `routes.py`, `taxonomy.py`, `test_research_api.py`, `page.tsx`, `PriceChart.tsx`, and `types.ts` are changed. No new routes, no new nav entries, no new shell.

**J-48's registered home** is `/` chart pane (Cockpit section, 0 clicks from the nav). The iteration adds geometry to the existing `PriceChart` component on the home route. The change is an additive visualization within the already-registered chart pane — not a new page, not a parallel shell.

**No IA violation: no new route to check, no navigation path missing, no duplicate home. PASS.**

---

### Step 3 — Subjective observations (advisory)

No advisory issues to note. The geometry colors mirror the established verdict palette used by the thesis strip (`confirming` emerald, `weakening` amber, `rejecting`/`invalidated` rose, `pending` slate) — color language is consistent across surfaces. Tape-state markers (above-bar arrow-down) and thesis markers (below-bar circle/arrow-up) are visually distinct as the spec requires.

---

### Summary

| Check | Result | Notes |
|---|---|---|
| Row 15 `geometry` — single computation path | PASS | `_build_geometry` at monitor.py:151, called once from `build_projection` |
| Row 15 `geometry` — single serving endpoint | PASS | `GET /research/thesis/active` + WS `thesis` key verbatim; parity test extended |
| Row 24 display copy — canonical owner | PASS | Labels in taxonomy.py; frontend hardcodes none |
| No new routes or nav changes | PASS | Pure visualization within existing `/` chart pane |
| No duplicate home or parallel shell | PASS | No new pages introduced |
| Blueprint row 15 additive note registered | PASS | Decomposer registered it alongside this spec |

No objective violations found. No advisory warnings.
