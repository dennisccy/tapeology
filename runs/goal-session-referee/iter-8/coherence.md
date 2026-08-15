# Iteration 8 — Coherence Audit

**Iteration:** goal-referee-iter-8
**Date:** 2026-08-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

<!-- COHERENCE-WARN: only advisory issues; does NOT block GOAL_ACHIEVED -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Starter-family shortlist (S-1..S-5 readiness) — owner `referee_registry.py`, `GET /research/desk/referee/registry/shortlist` | OK | New endpoint matches the row `state/blueprint.md:54` already registers (third endpoint cell added same iteration the row's owner still names). S-1/S-2/S-3 readiness reuses `playbook_occurrence_readiness()` verbatim (`referee_registry.py:1032` calling `referee_evidence.py`'s canonical fold, no second pooling loop). S-4/S-5 readiness (`_starter_context_readiness`, `referee_registry.py:993-1030`) reuses `resolve_occurrence_backing_bucket` + `BandMapResolver(..., compute=False)` from `referee_null.py` / `desk_playbook_context.py` — the SAME primitive `referee_adjudicate.py`'s `_pool_cell_vs_complement` already calls, not a second implementation. |
| `discovery` field addition on registry hypothesis entries — owner `referee_registry.py`, `GET /research/desk/referee/registry` | OK | Registered in `state/blueprint.md:242-250` (iter-8 note) as a field addition, owner/endpoint unchanged. `_hypothesis_discovery` (`referee_registry.py:833-864`) walks the identical `newest_by_date` scan and `_is_stale_basis`/`_record_detector_basis` filter that `_hypothesis_accrual` already uses, just inverted (pre- vs post-boundary) — exact complement, not a duplicate computation. |
| `integrity_errors` on `GET /research/desk/referee/adjudications` — owner `referee_adjudicate.py` | OK | Pre-registered in `state/blueprint.md:200-202` (iter-7 note anticipating this exact iter-8 addition). `adjudications_response()` (`referee_adjudicate.py:1436-1463`) now surfaces `hypothesis_store.list()`'s own errors — same pattern `registry_response()` already uses for its four stores, not a new disclosure shape. |
| Evaluation `role` gating (Rider 1) — owner `referee_adjudicate.py` | OK | Correctness fix on an already-registered row (no new value); write-side gate now matches the read-side's existing `verify_oracle_attestation` check (`referee_adjudicate.py:1024-1027`, `:1160-1161`). |
| Rendered shortlist/registry numerics on `/desk` (`candidate.n`, `.n_sessions`, `.accrual_rate_sessions_per_day`, `.projected_days_to_target`, `hyp.discovery.*`, `hyp.accrual.*`) | OK — re-format only | JSX reads these as straight pass-through with `.toFixed()` formatting or plain "X / Y" string interpolation (`apps/frontend/app/desk/page.tsx:4747-4756`, `:4849-4856`) — no `+`/`-`/`*`/`/` operators between served fields. `test_desk_ui_guards.py:245-251` extends `_PRICE_ARITHMETIC_FIELDS` to cover the new `candidate.*` / `hyp.discovery.*` bindings with seeded counter-tests (`test_desk_ui_guards.py:456-484`). |
| Starter-family BH `q` (`REFEREE_STARTER_FAMILY_Q = 0.1`) sent in the registration POST payload | UNREGISTERED (advisory) | `apps/frontend/app/desk/page.tsx:361-362` pins a literal `0.1` intended to mirror `REFEREE_DEFAULT_Q`, which exists **only** as prose in `docs/referee-statistical-spec.md:50` — no backend module constant of that name exists anywhere in `apps/backend/`. See Advisory notes below; does not meet the FAIL bar. |

**On the `family_q` literal (flagged for explicit judgment):** this is not a Data Contract FAIL under Part A. Part A's rules police a registered value with an established canonical source being *re-derived* or *served from a different source* — I could not find a second point to trace it against: there is no backend `REFEREE_DEFAULT_Q` constant computing this number today, so nothing in code is being duplicated (only a prose spec value is being mirrored). It is also not currently a *displayed* value — the registry table renders `hypothesis_id`/`setup_id`/`side`/`confirmation_start_boundary`/`origin`/`status`/`accrual`/`discovery` (`apps/frontend/app/desk/page.tsx:4839-4858`); `family.q` is never rendered by this iteration's UI, only submitted in a write payload for a family's first-sighting creation. And `_validate_family_consistency` (`referee_registry.py:628-648`) already forecloses any live "numbers don't match" risk: a second registration attempt against the same `family_id` with a different `q` is refused, not silently accepted. That combination — no code-level source to diverge from, not rendered, and future divergence structurally blocked — keeps this below the objective FAIL bar (skill: "if you cannot point at both [places], it is not a FAIL"). It is registered here as a WARN instead, independently of (and in agreement with) this iteration's own hard-audit pass, which already surfaced the identical concern as finding F1 in `docs/handoffs/goal-referee-iter-8-audit.md:123-137` and deliberately left it unfixed as a next-iteration item.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| "Referee Registry" `CollapsibleSection` on `/desk` (J-05/J-07 home) | OK | Matches `state/blueprint.md:36-39` IA rows verbatim: home = `/desk` → Referee Registry, shortlist rendered above the registered-hypotheses table (`apps/frontend/app/desk/page.tsx:4749` shortlist table, `:4820` "Registered Hypotheses" heading + `RefereeHypothesesTable` directly below it in the same section). |
| Nav-skeleton / reachability | OK | `apps/backend/app/meta.py:31-35` `UI_ROUTES` unchanged this iteration — still exactly 3 entries (Cockpit, Structure, Desk), all `nav: true`; confirmed unmodified in the diff and by the ui-surface-map's live `GET /meta/ui-routes` check. `apps/frontend/components/NavBar.tsx:11-16,39-49` renders nav links directly from `GET /meta/ui-routes` (the established single-source-of-truth pattern, no hardcoded list) — `/desk` is reachable in 1 click from any page; expanding the new section is the 2nd click. ≤2-click rule satisfied. |
| Duplicate home / parallel shell | OK | First-ever Referee UI surface (no pre-existing page for this entity to collide with). The new section reuses the page's existing `CollapsibleSection` component and existing `PRIMARY_BUTTON_CLASS`/`CANCEL_BUTTON_CLASS` styling (`apps/frontend/app/desk/page.tsx:4699-4713` component signature, `:9591-9618` mount point) — appended as another `<section>` in the same shell as every other `/desk` section, not a new layout/nav. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **F1 (concurred, WARN): the starter family's BH `q` is an unowned browser literal.** `apps/frontend/app/desk/page.tsx:361-362` (`REFEREE_STARTER_FAMILY_ID`, `REFEREE_STARTER_FAMILY_Q = 0.1`) is the only place in runtime code this value exists; the backend never defines a `REFEREE_DEFAULT_Q` constant (only documented in prose, `docs/referee-statistical-spec.md:50`), the shortlist response carries no family framing, and no test ties the two together. Concrete fix for the decomposer to schedule (naturally alongside J-08, which is where family/promotion mechanics get their next real work, per the hard audit's own recommendation): add `REFEREE_DEFAULT_Q = 0.10` as a module constant in `referee_registry.py`, add `family_id`/`family_q` fields to `shortlist_response()`'s output, register the field addition in `state/blueprint.md`, and have `page.tsx` read both verbatim from the fetched shortlist instead of hardcoding them — closing the ownership gap before a second family (and a second chance to disagree) exists.
- **Minor, not independently pursued (already filed by the reviewer as T2 in the hard audit):** `test_desk_ui_guards.py`'s extended `_PRICE_ARITHMETIC_FIELDS` regex (`:245-251`) covers `hyp.discovery.*` but not the sibling `hyp.accrual.*` pair rendered in the identical "X / Y" idiom one column over (`apps/frontend/app/desk/page.tsx:4849-4852`). No live violation today — confirmed by direct inspection that both are template-string interpolations, not arithmetic — this is a guard-coverage gap, not a coherence violation.
- Readiness numbers ("Accrual / day", "Projected days") render without disclosing they are proxies of a whole-corpus-span estimate; the registry fold's own `accrual.is_proxy` flag is served but not rendered anywhere in this iteration's UI. Cosmetic disclosure completeness, not a Data Contract or IA violation.
