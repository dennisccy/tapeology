# goal-playbook-iter-8 Execution Plan

## What to Build

**J-08 "The evidence view"** (target journey, `full` depth mandatory — prior verdict `ESCALATE`):

- `app/research/desk_playbook_evidence.py` (new): reads recorded `PlaybookStore` records via
  `desk_playbook.py`'s existing reader (zero re-implementation), pools per-`(setup_id, side,
  measure)` value lists at the DEFAULT signature (`compute_playbook_input_signature`, imported
  verbatim), behind a derived SQLite projection cache mirroring the `desk_meta_cache.py` contract
  (stat-keyed off the store's own file stats, owns nothing, unopenable/deleted DB = cache miss →
  rebuild, never a failed read — the module docstring should say this explicitly, `desk_meta_cache.py`
  is the copy-paste precedent).
- `GET /research/desk/playbook/evidence` in `desk_routes.py` (optional `?signature=` to inspect a
  non-default signature's own `dates`/`created_span` without pooling it), matching the blueprint's
  already-reserved "Evidence aggregates" Data-Contract row (`runs/goal-session-playbook/state/
  blueprint.md:116`).
- Cell fold per `(setup_id, side, measure)`: `signal {n, n_truncated, median_pct, p25_pct, p75_pct,
  mean_pct}` vs `baseline {n_baseline, median_pct, p25_pct, p75_pct, mean_pct}`, `below_min_n` tag
  under `PLAYBOOK_MIN_N_DISCLOSURE` (already `= 12` at `desk_playbook.py:174`, zero diff needed),
  `invalidation_breached` counts by horizon, `other_signatures` (listed, never pooled),
  `parameters` (verbatim `playbook_parameters()` blob), `register` = new `EVIDENCE_REGISTER`
  module-level tuple (same disclosure pattern as `PLAYBOOK_REGISTER` at `desk_playbook.py:178`).
- **Quantile math is new code, not a rail re-implementation.** `desk_forward.py`'s own `_avg_cell`
  (`:564`) only produces `n`/`mean_pct`/`median_pct`/`n_truncated` — it has no p25/p75. J-08 needs
  its own pooling helper inside `desk_playbook_evidence.py` for the quartiles (e.g.
  `statistics.quantiles`); this does NOT violate the "no second implementation of the measurement
  rail" anti-goal (horizons/MDD/truncation/seed discipline stay imported, zero diff to
  `desk_forward.py`) — it is new evidence-only fold math the rail never had. Pick one deterministic
  quantile method and prove it against TC-1's hand-computed fixture; document the choice in the
  dev handoff so the auditor can verify it, not re-derive it.
- Truncated values excluded from `median_pct`/`mean_pct` pools with the exclusion counted in
  `n_truncated`, never silently dropped (TC-4).
- Source-scan guard test: the evidence cache class exposes no update/delete method; the pooling
  code never merges two signatures into one cell (mirrors the existing store-immutability / rail-
  import guard tests already in the suite).
- `tests/test_copy_discipline.py` extended to cover `EVIDENCE_REGISTER` + new page copy (no
  probability/expectancy/edge/significance/advice language).
- `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` extended with every new served
  numeric (median/p25/p75/mean/n/n_truncated/n_baseline/breached counts).
- Frontend: new `/desk` **Playbook Evidence** section, rendered below the shipped Backscan panel
  (per the blueprint's reserved IA slot) — a table (setup × side × measure), signal-vs-baseline
  columns, `below_min_n` tag visible on tagged cells, `invalidation_breached` counts, the
  `register` copy. No client-side arithmetic — every number a straight pass-through of the
  response (guarded structurally via `_PRICE_ARITHMETIC_FIELDS`, matching every prior playbook
  section). No new user action beyond scrolling (T-7: GETs never compute — no refresh/trigger).

**Five carry items from the last two ESCALATEs (cheap, already-diagnosed fixes — NOT a second
risky journey):**

1. **Back-scan plan 500 on malformed date.** `_planned_dates` (`desk_playbook_backscan.py:198`)
   calls `date.fromisoformat(from_day)`/`date.fromisoformat(to_day)` uncaught — a half-typed date
   like `2026-06-2` raises `ValueError`, which FastAPI turns into an HTTP 500 at
   `GET /research/desk/playbook/backscan/plan` (`desk_routes.py:1179`). Fix: catch the malformed-
   date case and return an honest HTTP 200 empty/disclosed plan, the SAME status-code shape as the
   already-handled `from_day > to_day` case (an empty `dates` list, `total: 0`, `missing: 0` —
   mirror whatever the inverted-range branch already returns). This is a backend response-shape
   fix only — explicitly NOT a frontend debounce/UX change (TC-10 just requires no raw 500/error
   banner on a mid-typed date; the existing per-keystroke refetch cadence is untouched, per IN
   SCOPE / OUT OF SCOPE both saying so). Logged assumption: HTTP 200 (not 4xx) per
   `runs/goal-session-playbook/state/assumptions.md` iter-8 entry — T-5 "fail closed, disclose the
   absence" is the governing rail since neither `docs/goal.md` nor the canonical spec states a
   status code here.
2. **`journey-scripts/J-05.json` step-2 assertion fix.** Its current assertion targets the literal
   substring `"Capitulation"`, which ALSO appears in the section's own static description
   paragraph — so a fixture-mismatched replay (wrong symbol seeded) can false-PASS. Retarget the
   assertion to a selector/text scoped to a real signal row (a `data-testid` or row-scoped string
   that only renders when an actual capitulation signal is present). Prove the fix by running a
   deliberately fixture-mismatched replay and confirming it now FAILS (TC-13) — then run a fresh
   LIVE browser pass (not just replay) to re-confirm the new assertion before trusting it as a
   golden, since the script itself changed this iteration.
3. **Record `journey-scripts/J-06.json`.** No golden exists yet (confirmed: `runs/goal-session-
   playbook/journey-scripts/` currently has J-01 through J-05 and J-07 only) — J-06 (the range/
   double-top section) has been DEFERRED-BUDGET every time the time budget was tight. Record it
   this iteration so it stops being skipped, and verify it passes a deterministic replay on the
   scoped rig (TC-12).
4. **Owed Range Trade row re-capture.** A fresh screenshot of the Range Trade row (opened/
   expanded) on a freshly rebuilt (`rm -rf apps/frontend/.next`) scoped rig, with the full
   geometry disclosure line legible (range MBR width, zone touches, broke-at slot, crossed-
   midrange) — the `evidence_makeup` item carried since iteration 6 (TC-14).
5. **Scope the deterministic replay lane.** Extend (never rewrite)
   `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` forward as the MANDATORY
   launcher for every playbook golden-replay run (J-01..J-08, J-10's playbook-touching steps), so
   no replay script can ever reach the operator's ambient `:8301`/real `.data/` store — this is
   the exact hole the iter-7 lesson identified (the replay lane ran against whatever was already
   listening on `:8301`, which was the operator's real backend). Verify via
   `find apps/backend/.data -newermt "<run start>" -type f` returning zero playbook/backscan
   record or ledger files after a full replay run (TC-11).

**Required-still-passing (widened on ESCALATE per the spec's own rule): J-01, J-02, J-03, J-04,
J-05, J-06, J-07, J-10** — verify via the now-scoped deterministic replay lane, LLM fallback where
a golden is missing/stale, live-browser-verify for J-05 specifically (its script changes this
iteration).

## Agents Required

- backend-data: yes — `desk_playbook_evidence.py` module + cache + route + guard tests + the
  back-scan plan malformed-date fix + the replay-lane scoping script extension + J-06 golden
  recording + the J-05 assertion fix.
- frontend-ux: yes — the `/desk` Playbook Evidence section (table, tags, counts, register copy);
  the owed Range Trade row re-capture is a QA/browser-evidence task, not new frontend code (the
  row already renders — this is a fresh screenshot on a rebuilt rig).

## Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/research/desk_playbook_evidence.py` -- new: pooling module + derived SQLite
  projection cache (`desk_meta_cache` contract) + `EVIDENCE_REGISTER`
- `apps/backend/app/research/desk_routes.py` -- wire `GET /research/desk/playbook/evidence`
  (+ `?signature=`); fix the back-scan plan route/`_planned_dates` to return honest 200 on a
  malformed date instead of letting `ValueError` 500
- `apps/backend/app/research/desk_playbook_backscan.py` -- `_planned_dates`/`plan_backscan`
  malformed-date handling (catch and return the same empty-plan shape as the inverted-range case)
- `apps/backend/tests/test_desk_playbook_evidence.py` -- new: TC-1..TC-7 (pooling math, cache
  cold/warm byte-identity, cache-deleted rebuild, min-n tagging, truncation-exclusion,
  single-signature pooling, copy lint), source-scan guards (no update/delete method, no
  cross-signature merge)
- `apps/backend/tests/test_desk_playbook_backscan.py` -- malformed-date TC-9 coverage
- `apps/backend/tests/test_copy_discipline.py` -- extend for `EVIDENCE_REGISTER` + new page copy
- `apps/backend/tests/test_desk_ui_guards.py` -- extend `_PRICE_ARITHMETIC_FIELDS` for every new
  served numeric
- `apps/backend/tests/test_desk_refresh_chain_guard.py` -- re-derive effect/interval/trigger
  censuses if the new section adds any (likely a mount-time GET only, no new effect/trigger since
  T-7 says GETs never compute here — verify and only touch if actually needed, with the mandatory
  rationale paragraph if so)
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` -- extend forward (never
  rewrite) as the mandatory launcher for the deterministic replay lane
- `apps/frontend/app/desk/page.tsx` -- new Playbook Evidence section below Backscan
- `apps/frontend/lib/api.ts` -- `fetchDeskPlaybookEvidence`
- `apps/frontend/lib/types.ts` -- `DeskPlaybookEvidence*` types
- `runs/goal-session-playbook/journey-scripts/J-06.json` -- new golden replay script
- `runs/goal-session-playbook/journey-scripts/J-05.json` -- fix step-2 assertion (real signal-row
  selector, not the static-copy-colliding "Capitulation" substring)
- `docs/handoffs/goal-playbook-iter-8-dev.md` -- dev handoff (required by Definition of Done)

## UI Evolution

- New user-facing capability: the operator can scroll `/desk` to a new **Playbook Evidence**
  section and see, per setup family and side, how many recorded signals fired and what their
  forward-return/MDD distributions look like against the pooled seeded baseline — with low-n
  cells honestly tagged.
- New information displayed: per-`(setup_id, side, measure)` cell pairs (signal vs. baseline) with
  `n`, `n_truncated`, `n_baseline`, `median_pct`, `p25_pct`, `p75_pct`, `mean_pct`; `below_min_n`
  tags; `invalidation_breached` counts by horizon; `other_signatures` listings; the
  `EVIDENCE_REGISTER` disclosure copy.
- New user actions: none — a pure read-only fold, per T-7 ("GETs never compute"); no
  refresh/compute trigger of its own.
- UI surface changes: `/desk` gains one new section, **Playbook Evidence**, below the shipped
  Backscan panel. No existing section, route, or nav entry changes.
- Navigation changes: none.

## Visual Requirements

- Component patterns: match the existing Playbook Signals / Backscan panel style already shipped
  on `/desk` — a bordered `Panel`-style section with a heading, a dense data table (setup × side ×
  measure rows, signal/baseline column pairs), inline tag badges for `below_min_n` (same badge
  pattern the Backscan plan preview uses for `recorded_at_current_signature`/
  `missing_at_current_signature`).
- Layout: dense, terminal-grade table below the Backscan panel, full-width within the existing
  `/desk` main content column — no new page, no new layout shell.
- Key visual effects: none beyond the established dark-only, dense, no-marketing-chrome house
  style; a visual distinction (badge/dim styling) for `below_min_n`-tagged cells so the operator
  can spot thin data at a glance without any advisory language.
- States to handle: no recorded signals at all (honest empty state, describing absence, never a
  crash); a signature with records but not the current default (rendered under an
  `other_signatures` listing, not folded into the table); a cell with zero recorded signals
  (`n: 0`, shown not omitted); cache cold vs warm (must be visually indistinguishable — latency
  only, content identical).

## Key Test Scenarios

- TC-1..TC-7 (evidence pooling math against a hand-computed fixture; cache cold/warm byte-
  identity; cache-deleted rebuild changes nothing but latency; min-n tagging with numbers still
  populated, not nulled; truncated values excluded from pools with the exclusion counted; two
  signatures present → only the default pools into `cells`, the other lists under
  `other_signatures`; `EVIDENCE_REGISTER` copy-lint clean).
- TC-8: `/desk` Playbook Evidence section shows one `n >= 12` cell and one `below_min_n: true`
  cell both legible in a single screenshot, matching the served JSON verbatim (browser-qa-agent,
  scoped fixture rig).
- TC-9/TC-10: malformed/partial date to `.../backscan/plan` returns honest HTTP 200 (never 500);
  the `/desk` Backscan panel shows no raw 500/error banner on a mid-typed From date.
- TC-11: the deterministic golden-replay lane launches/targets the scoped fixture backend for
  every playbook journey; `find apps/backend/.data -newermt "<run start>" -type f` returns zero
  playbook/backscan files after the run.
- TC-12: `journey-scripts/J-06.json` exists and passes a deterministic replay on the scoped rig.
- TC-13: `journey-scripts/J-05.json`'s new assertion targets a real signal row (not static copy);
  a deliberately fixture-mismatched replay run FAILS on it, proving discrimination.
- TC-14: a fresh Range Trade row screenshot (opened/expanded) on a `rm -rf .next` rebuilt rig,
  full geometry disclosure line legible.
- TC-15: full backend suite exits 0, passed count ≥ 2130, 8 skipped,
  `Config().config_fingerprint()` still prints `08e471b10130e1e2`.
- Required-still-passing regression sweep: J-01..J-07 and J-10 all green via the now-scoped
  replay lane (LLM fallback for any missing/stale golden), J-05 additionally live-browser-verified
  since its script changed this iteration.

## Out of Scope (flagged, excluded per phase spec)

- J-09 (MCP contract v4 / 20 tools) — next iteration.
- The two open owner rulings (§3.7 `range_trade` degenerate-trigger clarification; the three
  narrower-than-spec disclosures) — human-owned, not re-planned.
- Any statistics language (CIs, p-values, significance, expectancy, probability) — era-6
  territory.
- Debouncing the Backscan plan preview's per-keystroke refetch — only the honest-response defect
  is fixed.
- Any real, unscoped back-scan or playbook compute against the operator's live universe — every
  test/browser/replay act runs on the scoped fixture rig only.
- Rewriting/deleting the iter-6 accidental real-store record
  (`.data/playbook/playbook-2026-08-07-84fcd116ebd7.json`).
- Re-opening `desk_playbook_detect.py`'s detector logic — zero diff maintained.

No drift from `docs/goal.md` detected: J-08 is explicitly Must-have journey 8, the six-row Data
Contract already reserves the "Evidence aggregates" row for this exact endpoint, and the five
carry items are all previously-diagnosed defects/hygiene from iter-6/iter-7 ESCALATEs rather than
new scope. Environment note: run `export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-playbook-iter-8.31034" TMP="/home/dennis-chan/.cache/iad/iad.goal-playbook-iter-8.31034" TEMP="/home/dennis-chan/.cache/iad/iad.goal-playbook-iter-8.31034"` before any command that writes temp files.
