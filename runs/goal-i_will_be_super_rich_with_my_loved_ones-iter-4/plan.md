# goal-i_will_be_super_rich_with_my_loved_ones-iter-4 Execution Plan

Verdict-transition engine (J-40–J-46) + the thesis-strip visual-evidence debt (J-38/J-39).
Depth: full (mandated by iter-3's ESCALATE). All prerequisites exist: SIM-SHIFT/SIM-REVERSAL
(iter-1), thesis declaration + monitor observer + SQLite store with append-only
`verdict_events` (iter-2, backend green at 332 passed / 1 skipped). The engine, classifier,
features, and providers are UNTOUCHED — the verdict engine composes existing snapshot values
only, observer-side.

## What to Build

- **Verdict evaluator** (NEW module under `apps/backend/app/research/`): a pure per-event
  evaluator invoked from the existing `ResearchMonitor.on_event` seam, mapping each frozen
  engine snapshot to a raw verdict via **config-owned per-setup rule tables** built ONLY
  from existing tape states/features. Per-setup semantics:
  - `absorption_reversal` — confirms on the REVERSAL (flip to matching control with real
    price impact), NEVER on sustained absorption alone (premise met / trigger not-yet) — J-40.
  - `trend_continuation` — confirming while matching control + impact hold; opposing control
    publishes `rejecting` (a judgement, not a resolution — thesis stays active) with
    opposing-control/impact evidence — J-41/J-42.
  - `level_break` — a latch: NO confirmation until last crosses the declared level, however
    strong control is; after latch + control ⇒ confirming citing cross + control — J-45.
  - `failed_move_fade` — deliberate asymmetry with J-40: absorption of the break IS the
    expected behaviour and reads confirming; reclaim keeps it confirming; rejecting needs
    real opposite follow-through — J-46.
- **Dwell + timing record**: per-setup logical-time dwell, restarting at thesis creation
  (confirmation requires post-declaration evidence by construction). Every published
  transition records `rule_first_true` (first logical instant + price the raw rule held)
  and `published_at`. The published verdict NEVER flaps per tick.
- **Confirmed → weakening (J-43)**: once confirmed, fading evidence (tape going
  neutral/unclear) publishes `weakening` after its dwell — never a silent return to
  `pending` — with a distinct "supporting evidence faded" evidence register.
- **Invalidation trigger (J-44)** — dwell-exempt, robust, system-owned, internal monitor
  logic (NOT the user-facing resolve endpoint, which stays out of scope): one print beyond
  the declared invalidation by ≥ the configured spread-multiple ε, OR k consecutive prints
  beyond it (a lone bad print inside the guard does NOT invalidate) ⇒ verdict `invalidated`
  immediately + thesis auto-resolved `invalidated` via the existing store path, with the
  offending print price + logical timestamp recorded as evidence.
- **Append-only timeline**: each published transition appended to `verdict_events` via the
  existing single-writer repository (`logical_ts, wall_ts, verdict, evidence, tape_state,
  confidence, last, rule_first_true`); config-owned timeline cap; never recomputed at read.
- **`GET /research/journal/{id}`** — the blueprint row-16 registered serving endpoint:
  thesis record + persisted verdict timeline verbatim; 404 unknown id. Minimal projection
  only — NO list endpoint, NO analytics, NO review fields.
- **Config (research defaults, documented)** in `app/config.py`: per-setup verdict dwell,
  invalidation ε spread-multiple, k-consecutive count, timeline cap. They enter the
  existing `config_fingerprint` automatically (it hashes the entire frozen config). No
  literals in research code.
- **Evidence strings**: present-tense, descriptive, thesis-attributed, derived from
  canonical snapshot values (e.g. "buyers took control with real upward impact
  (buy_price_impact +0.0042)") — no imperative/predictive/certainty language anywhere.
- **Frontend — ThesisStrip verdict rendering**: live verdict + evidence line with the
  established semantics — `confirming` emerald, `weakening` amber, `rejecting` rose,
  `invalidated` rose with a terminal treatment, `pending` slate. Labels/display copy from
  `GET /research/taxonomy` (row 24 — hardcode none). The strip keeps its single existing
  read path (WS `thesis` key). Terminal invalidated state: resolved treatment with the
  offending evidence — never a silent revert to the idle declare affordance. No new pages,
  no chart changes (thesis geometry is J-48, later).
- **Visual-evidence debt (QA deliverable, zero new code)**: J-38/J-39 re-run with captures
  that VISIBLY contain the thesis strip (scroll into view or full-page screenshot); the
  J-68 strip-idle declare affordance likewise captured visibly. Binding evidence rule: a
  viewport-top capture of a below-the-fold surface is a FAIL, not a soft note.

## Agents Required

- developer: yes -- backend (verdict evaluator module + per-setup rule tables, dwell +
  `rule_first_true`/`published_at`, weakening rule, dwell-exempt robust invalidation +
  auto-resolve, timeline persistence + cap, `GET /research/journal/{id}`, config block,
  full unit-test matrix incl. equivalence re-proof) AND frontend (ThesisStrip verdict
  chip/evidence states + terminal invalidated treatment, taxonomy-driven copy). Single
  developer, both halves.
- backend-data: yes -- as above (verdict engine, timeline persistence, journal endpoint).
- frontend-ux: yes -- as above (strip verdict states; everything else unchanged).

## Frontend Present
yes

## Files to Create/Modify

Backend:
- `apps/backend/app/config.py` -- NEW research verdict defaults: per-setup verdict dwell,
  invalidation ε spread-multiple, k-consecutive count, timeline cap (documented as
  research defaults; auto-included in `config_fingerprint`).
- `apps/backend/app/research/verdict.py` -- NEW: pure per-event verdict evaluator —
  per-setup rule tables over existing snapshot states/features, dwell tracking,
  `rule_first_true`/`published_at`, latch state for level_break, invalidation trigger
  (ε / k-consecutive), evidence-string builders.
- `apps/backend/app/research/monitor.py` -- invoke the evaluator from `on_event`; publish
  transitions into the projection (verdict + evidence replace the fixed `pending`); append
  timeline rows via the writer queue; auto-resolve `invalidated` through the existing
  resolution path; exception isolation unchanged (`monitor_status: failed`, feed never dies).
- `apps/backend/app/research/store.py` -- read API for a thesis + its persisted timeline
  (verbatim rows for the journal endpoint); timeline-cap enforcement on append. Repository
  still exposes NO update/delete on `verdict_events`.
- `apps/backend/app/research/routes.py` -- NEW `GET /research/journal/{id}` (404 unknown).
- `apps/backend/app/research/taxonomy.py` -- confirm/extend verdict display copy for the
  four non-pending states (enums + copy already exist from iter-2; additive copy only).
- `apps/backend/tests/test_verdict_engine.py` -- NEW: one test per setup type asserting the
  J-40/J-42/J-45/J-46 sequences on the seeded scenario streams (unpaced replays), incl. the
  J-40 trap (sustained absorption alone never confirms) and the J-45 latch (no confirm
  pre-cross); J-43 confirmed→weakening and J-41 rejecting with their evidence registers;
  invalidation robustness (lone print inside ε guard does NOT invalidate; ≥ε single print
  and k-consecutive both do; auto-resolution recorded; dwell-exemption asserted); dwell
  (pre-declaration hold never confirms; `rule_first_true` ≠ `published_at` recorded); no
  per-tick flapping; no verdict event ever recorded before declaration.
- `apps/backend/tests/test_research_store.py` -- extend: timeline rows append-only, cap
  enforced.
- `apps/backend/tests/test_research_api.py` -- extend: `GET /research/journal/{id}` serves
  persisted rows verbatim + 404 unknown; existing 404/422/409 declaration matrix
  re-asserted unchanged.
- `apps/backend/tests/test_observer_equivalence.py` -- extend: engine outputs byte-identical
  with an active thesis being verdict-evaluated vs no research layer.

Frontend:
- `apps/frontend/components/ThesisStrip.tsx` -- verdict chip/section: four non-pending
  states with extended color semantics + evidence line; terminal invalidated treatment.
- `apps/frontend/lib/types.ts` -- additive verdict/evidence projection fields if needed
  (read verbatim from the WS `thesis` key — no new read path, no frontend derivation).

## UI Evolution

- New user-facing capability: the declared thesis is continuously judged against the live
  tape — the user watches the verdict move `pending → confirming / weakening / rejecting`,
  with plain-language evidence for every transition, and a print through their invalidation
  hard-resolves the thesis on screen.
- New information displayed: live verdict state + evidence sentence on the thesis strip;
  terminal invalidated treatment with the offending print; the full append-only verdict
  timeline via `GET /research/journal/{id}`.
- New user actions: none (declaration exists; verdicts are system-published; resolve/mark
  controls are J-50/J-52, later).
- UI surface changes: thesis strip only — verdict chip gains the four non-pending states +
  evidence line + terminal treatment. Cockpit otherwise unchanged; no new pages.
- Navigation changes: none.

## Visual Requirements

- Component patterns: hand-built panels per the design system (no component library);
  extend the existing ThesisStrip pill/badge conventions; `font-mono` for all prices.
- Layout: strip stays in place between the chart and the panel grid; verdict chip +
  one-line evidence sentence inside the active-thesis display; no reflow of the grid.
- Key visual effects: verdict semantics exactly per design direction — `confirming`
  emerald, `weakening` amber, `rejecting` rose, `invalidated` rose + terminal treatment,
  `pending` slate. The existing side/impact palette extended, never repurposed. The
  "Descriptive only — not trading advice" line stays.
- States to handle: pending; confirming; weakening; rejecting (thesis still active);
  terminal invalidated (resolved, offending evidence shown — NOT the idle affordance);
  `monitor_status: failed` honesty notice (existing) unchanged.

## Key Test Scenarios

Browser (Chrome MCP, deterministic seeded sims, no credentials; STOP the watch between
journeys so the active thesis auto-expires and re-declaration never 409s; budget ~60s
logical for SIM-SHIFT/SIM-REVERSAL phase 2; prefer event-log/timeline assertions for
transient phase-sequence claims; EVERY capture must visibly contain the asserted element —
scroll into view or full-page):

- **J-40**: SIM-REVERSAL, declare absorption_reversal/long during absorption → pending with
  premise met / trigger not-yet through sustained absorption; confirming (flip-citing
  evidence) only after the buyer_control phase; timeline holds `rule_first_true` +
  `published_at`.
- **J-41**: SIM-SELLER, trend_continuation/long, far invalidation → rejecting with
  seller-control evidence; thesis stays active.
- **J-42**: SIM-BUYER, trend_continuation/long → confirming after dwell; stays confirming
  (no flapping).
- **J-43**: SIM-SHIFT, trend_continuation/long during control → confirming, then weakening
  after the shift (post-dwell), never a silent return to pending; both transitions on the
  timeline.
- **J-44**: SIM-SELLER, any long with invalidation just below last → invalidated
  immediately on the qualifying print, thesis auto-resolved, terminal strip treatment,
  offending print + logical ts in the final timeline entry.
- **J-45**: SIM-BUYER, level_break/long with level above current last → pending pre-cross
  (cross statement not-yet) despite control; confirming after latch + control. (Chart
  level-line clause deferred to J-48.)
- **J-46**: SIM-REVERSAL, failed_move_fade/long during absorption → confirming DURING the
  absorption; remains confirming through the reclaim.
- **J-38/J-39 re-run**: correctly framed captures with the strip visible in pixels
  (active-thesis render for J-38; inline 422 + preserved form values for J-39); REST
  `…/thesis/active` cross-check; J-68 strip-idle affordance captured visibly.
- **Required-still-passing**: J-01–J-09, J-17, J-19, J-21, J-24 remain green.

Unit/integration (pytest, deterministic unpaced replays): the full matrix listed under
Files above — per-setup verdict sequences, J-40 trap, J-45 latch, weakening/rejecting
registers, invalidation robustness with a synthetic outlier print, dwell semantics,
append-only + cap + journal endpoint, observer equivalence with verdict evaluation active,
existing 404/422/409 matrix unchanged, no verdict event before declaration. Backend suite
must stay ≥ 332 passed / 1 skipped plus the new tests, zero regressions.

## Assumptions (documented, not asked)

- The evaluator lives in a new `verdict.py` module called by the monitor — keeps the
  evaluator pure (snapshot in, verdict-decision out) and unit-testable without FastAPI;
  the monitor owns publication, persistence, and the auto-resolve side effect.
- Timeline writes go through the store's existing single writer queue (never from the WS
  serialization path); the `invalidated` auto-resolve reuses the iter-2 resolution path
  with resolution `invalidated` (system-owned, distinct from `expired`).
- An evaluator exception surfaces as `monitor_status: failed` per the existing isolation
  contract and never kills the feeder.
- `taxonomy.py` already serves verdict enums + display copy (iter-2); the frontend reads
  labels from there — any missing non-pending copy is an additive taxonomy edit, not a
  frontend hardcode.
- The projection (row 15) gains verdict + evidence values it was always shaped for — the
  strip's single WS read path is unchanged; REST `…/thesis/active` stays verbatim-equal.

## Scope Notes

- No scope creep detected: everything maps to goal.md capability 24 (verdict engine) + the
  row-16 serving slice of the journal API. Data-contract additions: NONE — rows 15/16/24/26
  already register every value produced; do NOT introduce a second computation or serving
  path for any of them.
- Explicitly OUT: J-48 chart thesis geometry (incl. J-45's level-line parenthetical);
  J-49 risk flags; J-50 resolve endpoint/controls; J-52 action marks; J-53 stance;
  `/journal` page, review, grading, tags (J-51, J-54–J-57); excursions/analytics/studies
  (J-58–J-62); ALL cue surfaces (J-63–J-67, hard-gated by Evidence-before-cues); gap-event
  vocabulary beyond existing monitor-status handling (J-47/J-51); ANY
  engine/classifier/feature/provider change.
- Pipeline notes (binding, from session lessons + ESCALATE context): isolate any frontend
  build from the live dev server's `.next` (`NEXT_DIST_DIR=.next-qa`); kill dev servers by
  port (`fuser -k <port>/tcp`), never `pkill -f "next dev"`; an all-SKIP browser run is
  "frontend unverified" ⇒ FAIL, not SKIP; recount QA pass/fail from the result table, not
  the summary line; the phase-closure-auditor must verify evidence PNGs actually show the
  asserted UI states; this spec declares Frontend Present: yes — downstream steps must not
  repeat iter-3's false "no".
