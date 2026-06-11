**Verdict:** COHERENCE-PASS

## Iteration 11 — Entry risk flags at declaration (J-49)

Audited against blueprint at `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md`.
Diff base: `90274df37b5d8c529a4e2629fd284ee6cb74867d`.

---

## Step 1 — Data Contract

### Row 17: Entry risk flags (computed once at declaration; frozen)

- **Single owner confirmed.** `compute_risk_flags` in `apps/backend/app/research/monitor.py` is the sole function that computes the flag set. It is called exactly once, inside `POST /research/thesis` in `apps/backend/app/research/routes.py:381`, after all validation passes. No second computation path exists anywhere in the diff.
- **No client-side computation.** `apps/frontend/components/ThesisStrip.tsx` renders `thesis.risk_flags` verbatim. The `RiskFlagChips` component maps the frozen `label` and `evidence` strings directly — zero derivation.
- **Canonical serving paths intact.** `build_projection` in `monitor.py:521` conditionally adds `risk_flags` to the projection as a verbatim re-exposure of the frozen `ThesisRecord.risk_flags` field. This serves `GET /research/thesis/active`, the WS `thesis` key (same projection builder), and the surviving/not-evaluated path — all identical. `GET /research/journal/{id}` in `routes.py:265` re-exposes the frozen value verbatim from the stored record. No recomputation at read on any path.
- **Blueprint updated.** Row 15 gained the iter-11 additive note registering the `risk_flags` projection key in the same commit. Consistent with how `geometry` was registered in iter-10.
- **Honest-omission semantics preserved.** `None` (pre-v4, never assessed) → key absent from projection; `[]` (assessed, nothing fired) → key present as empty list. The two states are never collapsed, consistent with the blueprint's contract.

### Row 15: Thesis projection (additive `risk_flags` key)

- Re-exposed verbatim in `build_projection`. Not independently computed. No violation.

### Row 24: Taxonomies + research display copy

- `taxonomy.py` gains `RISK_FLAGS`, `risk_flag_label`, and evidence-copy helpers. These are the single backend owner of chip labels and evidence templates. `GET /research/taxonomy` now includes `risk_flags` in its payload. No second label owner; frontend reads these either from the taxonomy endpoint or (for chips) directly from the frozen per-thesis `label`/`evidence` fields. No violation.

**No Data Contract violations.**

---

## Step 2 — Information Architecture

- **No new routes or pages.** The diff touches only `ThesisStrip.tsx` and `types.ts` on the frontend. The amber risk-flag chips are an additive rendering inside the existing thesis strip on `/` (Cockpit).
- **Canonical home confirmed.** J-49's registered home is `/` thesis strip (Cockpit) per the blueprint IA table. The chips render exactly there — `RiskFlagChips` is placed inside both `ActiveThesis` and `NotEvaluatedThesis` branches of the strip, both already in the Cockpit shell.
- **No nav change.** No sidebar, top-bar, or router file was modified. Existing `Cockpit · Journal · Studies` nav is unchanged.
- **No duplicate home.** No second page for risk flags was introduced.
- **No parallel shell.** The new component lives inside the existing shell.

**No Information Architecture violations.**

---

## Step 3 — Advisory observations (WARN)

- **Minor:** `ThesisStrip.tsx:101` uses a Unicode warning emoji (`⚠`) in the chip label prefix. The established cockpit design system uses text/class-based indicators (no emojis elsewhere in the strip). This is a cosmetic inconsistency — advisory only, not an objective violation.

---

## Summary

| Check | Result |
|---|---|
| Part A — Data Contract | PASS |
| Part B — Information Architecture | PASS |
| Part C — Advisory | 1 minor cosmetic note (emoji in chip label) |

No objective violations from Part A or Part B. The iteration correctly adds the entry risk-flag capability as a strictly additive projection key on an existing endpoint/component, with a single computation owner, verbatim re-exposure everywhere, and zero new routes.
