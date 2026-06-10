# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-4 — UI Surface Map

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-4
**Date:** 2026-06-10
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `ThesisStrip` → `ActiveThesis` — verdict chip (`data-testid="verdict-chip"`) | Changed behavior | Verdict chip previously always showed static "pending" in slate; now reflects live published verdict with per-state color | Watch SIM-BUYER with a trend_continuation/long thesis declared; after ~3 s of tape time confirm the chip changes from slate "pending" to emerald "confirming" and `data-verdict` attribute reads `confirming` |
| `/` | `ThesisStrip` → `ActiveThesis` — verdict evidence line (`data-testid="verdict-evidence"`) | New component | New evidence sentence below the chip was not present before; every verdict now carries plain-language copy | Declare any thesis, wait for any non-pending verdict, and confirm a non-empty sentence appears beneath the chip in the verdict's matching color (emerald/amber/rose) |
| `/` | `ThesisStrip` → `ActiveThesis` — terminal invalidated treatment | Changed behavior | Post-invalidation strip previously cleared to idle "Declare thesis" affordance; now shows rose ringed chip, "✕" prefix, and "Thesis invalidated — resolved" notice | Watch SIM-SELLER with a long thesis whose invalidation price is just below current last; once the qualifying print fires, confirm the chip shows a rose ringed border with the "✕" prefix and the "Thesis invalidated — resolved" line is visible, and the idle declare button does NOT reappear |
| `/` | `ThesisStrip` → `ActiveThesis` — taxonomy fetch for active state | Changed behavior | Taxonomy was previously fetched only when the declare form opened; now fetched as soon as a thesis is active so verdict labels are always taxonomy-owned | Declare a thesis, immediately close and re-open the cockpit page before the form is opened; confirm the verdict chip shows the taxonomy label (e.g. "Confirming") rather than the raw enum string `confirming` |
| `/` | `ThesisStrip` — `weakening` and `rejecting` verdict states | New component | These two verdict states had no visual representation before (only pending existed); they now render with amber (weakening) and rose (rejecting) chips and corresponding evidence lines | Watch SIM-SHIFT with a trend_continuation/long thesis; after the tape shifts to the seller side, confirm the verdict chip turns amber with a non-empty weakening evidence sentence; watch SIM-SELLER with a trend_continuation/long and far invalidation, confirm the chip turns rose with rejecting evidence while the thesis stays active (no "resolved" notice) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/verdict.py` (NEW) — pure per-event verdict evaluator (per-setup rule tables, dwell tracking, invalidation trigger, evidence-string builders); not directly consumed by any frontend route — the monitor wires it into the existing projection and WS feed.
- `apps/backend/app/research/monitor.py` — verdict evaluation added to the existing `on_event` seam; verdict + evidence published onto the WS `thesis` key (the frontend's single existing read path — no new read path or page).
- `apps/backend/app/research/store.py` — `verdict_events` schema gains `rule_first_true_ts`/`rule_first_true_price` columns; timeline-cap enforcement added — no UI surface affected directly.
- `apps/backend/app/research/routes.py` — NEW `GET /research/journal/{id}` endpoint serving thesis + append-only verdict timeline (404 unknown id); no frontend page or component consumes this endpoint yet.
- `apps/backend/app/config.py` — new research verdict config defaults (`verdict_dwell_seconds`, `invalidation_epsilon_spread_multiple`, `invalidation_k_consecutive`, `verdict_timeline_cap`); no env-var change, no UI impact.
- `apps/backend/app/research/taxonomy.py` — additive display copy for the four non-pending verdict states; frontend reads this via the existing `GET /research/taxonomy` call, no new endpoint or component needed.
- `apps/backend/tests/test_verdict_engine.py` (NEW) — unit tests only, no UI surface.
- `apps/backend/tests/test_research_store.py` — extended tests only.
- `apps/backend/tests/test_research_api.py` — extended tests only.
- `apps/backend/tests/test_research_monitor.py` — test construction update only.
- `apps/backend/tests/test_observer_equivalence.py` — test construction update only.
- `apps/frontend/lib/types.ts` — additive `verdict_evidence: string` field on `ThesisProjection`; a type-system change required for the ThesisStrip to render the evidence line — no independent UI surface.

---

## Summary

- **Frontend surfaces changed:** 1 (the thesis strip on `/`)
- **New pages/routes:** 0
- **Modified components:** 1 (`ThesisStrip.tsx` — verdict chip, evidence line, terminal invalidated treatment, taxonomy fetch on active state)
- **Navigation changes:** no
- **Backend-only changes:** 12 (verdict evaluator, monitor wiring, store schema + cap, journal endpoint, config defaults, taxonomy copy additions, 5 test files, 1 type file)
