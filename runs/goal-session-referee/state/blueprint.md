# App Blueprint — referee (Era 6 "The Referee")

<!--
Coherence contract for this session. Drafted at baseline (iteration 0) from docs/goal.md's
Product Shape + Must-have journeys. Auto-approved by default; pass --require-blueprint-approval
to pause for human review. Additive edits (new value rows, new pages under an existing nav
section) need no re-approval; a nav-skeleton change does.
-->

## Information Architecture

**Layout shell:** persistent top nav + main content area; dark-only, dense, terminal-grade
(tables and text, no dashboard cards/gauges) — unchanged since Era B2.

**Navigation skeleton** (`app/meta.py` `UI_ROUTES` — exactly 3 routes; this era adds sections
to Desk only, no new route):

```
Tapeology
├── Cockpit    `/`          — sim tape + live/historical chart
├── Structure  `/structure` — S/R levels/zones, tradable-map, structure_tape vs v1
└── Desk       `/desk`      — screen ledger, forward returns, refresh chain, briefing,
                              skipped, runs/pins/compare/provenance, Playbook (detectors +
                              band context + cohorts) — ALL SHIPPED (Era B/B2/R-4) —
                              plus, THIS ERA, rendered BELOW every shipped section:
                              Referee Registry / Referee Adjudications / Referee Runs
```

**Feature / journey homes** (≤2 clicks from nav; every Era-6 journey lives under Desk or has
no dedicated page):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 per-family readiness fold (backend fold; surfaces inside the J-07 shortlist) | `GET /research/desk/referee/evidence` | Desk |
| J-02 evidence contract, J-03 stats core (library modules, no page of their own) | n/a — consumed by J-04–J-09 | — |
| J-04 matched nulls — compute controls + ledger | `/desk` → **Referee Runs** | Desk |
| J-05 registry — families/hypotheses/withdrawals/certificates | `/desk` → **Referee Registry** | Desk |
| J-06 adjudication — verdict snapshots + pending fold | `/desk` → **Referee Adjudications** | Desk |
| J-07 starter-family shortlist + registration flow | `/desk` → **Referee Registry** (shortlist sits above the registered-hypotheses table) | Desk |
| J-08 promotion interlock | no new page — reads inside the EXISTING `pnl_scan` report's `promotion` block, wherever the shipped `/desk` sections already render scan reports | Desk |
| J-09 full Referee UI + MCP contract v5 | `/desk`, the three sections above; MCP `desk_referee` / `desk_referee_registry` | Desk |
| J-10 regression sentinel | all three routes, every kept section | Cockpit / Structure / Desk |

## Data Contract

New rows for this era, verbatim from `docs/goal.md` § Product Shape (the canonical source —
do not re-derive):

| Value | Owner (module) | Serving endpoint |
|---|---|---|
| Referee evidence coverage + per-family readiness | new `app/research/referee_evidence.py` | `GET /research/desk/referee/evidence` |
| Matched-null records | new `app/research/referee_null.py` | `GET /research/desk/referee/nulls` (`?id=`) |
| Null compute progress + runs | same module + its log | `POST/GET/POST-cancel /research/desk/referee/nulls/compute`, `GET .../nulls/runs` |
| Registry (families, hypotheses, withdrawals, certificates) | new `app/research/referee_registry.py` | `GET /research/desk/referee/registry`; `POST /research/desk/referee/registry/hypotheses` (operator act) |
| Evaluation records + runs | new `app/research/referee_adjudicate.py` + its log | `GET /research/desk/referee/evaluations`, `POST/GET/POST-cancel .../evaluate`, `GET .../evaluate/runs` |
| Adjudications (snapshots + pending fold) | `referee_adjudicate.py` | `GET /research/desk/referee/adjudications` |
| Promotion authorization verdict | `referee_adjudicate.py` (`authorize_promotion`) | consumed inside `pnl_scan._promote`; surfaced in the scan report's `promotion` block |

**Unchanged owners the Referee reads verbatim (never re-implements — import-ban guard-tested):**
playbook records → `desk_playbook.py`; measurement rail → `desk_forward.py`
(`_measure_from`, `_draw_anchor_indices`, imported, zero diff); band maps →
`desk_playbook_context.BandMapResolver`; session honesty → `desk_sessions.py`; strategy
trades/datasets → `store.py`/`datasets.py`; config fingerprint → `app/config.py`
(`Config().config_fingerprint()` == `08e471b10130e1e2`, frozen this whole era); MCP tool
count → `apps/backend/tests/test_mcp_server.py::EXPECTED_TOOLS` (20 today, 22 after J-09).

<!-- Baseline note (iter-0): confirmed via directory listing that none of the referee_*.py
modules exist yet in app/research/, and EXPECTED_TOOLS has exactly 20 entries with no referee
tools. Every row above is a J-01-J-09 build target for future iterations, not an
already-shipped value. No shared numeric/derived value outside this table is introduced by
this era. -->

<!-- iter-4 note: the "Referee evidence coverage + per-family readiness" row (owner
referee_evidence.py, GET /research/desk/referee/evidence) gains one additive field this
iteration — stale_basis_dates: list[{session_date: str, record_detector_basis: str}] — served
on BOTH playbook_occurrence_readiness()'s response (live at the endpoint above, J-01) and
playbook_observations()'s response (unconsumed by any route this iteration, J-02), computed by
one shared helper both call. Discloses a date whose newest Playbook record's own
(detector_basis, config_fingerprint) does not match the live values, instead of that record
silently contributing zero. No existing field's value changes; the row's owner/endpoint stay
exactly as above — this is a field addition, not a new value or a new canonical source. -->
