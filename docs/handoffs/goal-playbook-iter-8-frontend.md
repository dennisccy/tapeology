# goal-playbook-iter-8 Frontend Handoff

**Phase:** goal-playbook-iter-8
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

The `/desk` **Playbook Evidence** section — a new, third playbook-family section rendered directly
BELOW the shipped Backscan panel (the blueprint's own reserved IA slot), read-only, no compute
control of its own.

- **`apps/frontend/app/desk/page.tsx`**:
  - `PlaybookEvidenceSection` — top-level section component; handles loading (`LoadingPanel`),
    unavailable/error (`UnavailablePanel`), and honest-empty (`EmptyState`, "No playbook signals
    recorded at the current signature yet.") states, matching the established per-section
    convention every other `/desk` section already uses.
  - `PlaybookEvidenceCellsTable` — the setup × side × measure table: 3 identity columns + 6 Signal
    columns (n, trunc, median, p25, p75, mean) + 5 Baseline columns (n, median, p25, p75, mean) + 1
    Flag column (`below_min_n` badge, styled like the Backscan plan preview's own
    `recorded_at_current_signature`/`missing_at_current_signature` badges). Renders the FULL served
    `cells` array unfiltered — every combination the backend serves (270 rows), never a client-side
    subset, matching "renders the served cells as a table" literally.
  - `PlaybookEvidenceBreachTable` — the `invalidation_breached` array (90 rows: setup × side ×
    horizon), `breached_count`/`total_count` verbatim.
  - `PlaybookEvidenceOtherSignatures` — the `other_signatures` listing (signature, date count,
    created span), rendered only when non-empty.
  - **No client-side arithmetic anywhere** — every numeric cell is a direct `fmt(cell.signal.X)` /
    `fmt(cell.baseline.X)` / `fmt(breach.X)` pass-through; the `hasAnySignal` empty-state check
    (`cell.signal.n > 0`) is a comparison for display branching, not a derived value (the same
    pattern `ForwardAvgCellView`'s existing `avgCell.n === 0` check already uses — comparisons are
    not what the price-arithmetic guard polices, only `[-+*/]` operators are).
  - New imports: `fetchDeskPlaybookEvidence` (api), `DeskPlaybookEvidence`/
    `DeskPlaybookEvidenceBreach`/`DeskPlaybookEvidenceCell`/`DeskPlaybookEvidenceOtherSignature`
    (types).
  - New state: `evidenceResult` (`{ ok, data, error } | null`).
  - New effect wiring: the evidence fetch is joined into the EXISTING mount-time `useEffect` (one
    more `.then()` call alongside the Backscan/screen/forward snapshot seeds already there) rather
    than opening a NEW effect — the page's effect/interval/trigger-call census
    (`test_desk_refresh_chain_guard.py`) stays byte-unmodified, verified passing.
  - New section JSX: `<section aria-label="Playbook Evidence" className="mt-6">` with a `Panel`
    titled "Playbook Evidence", rendered as the LAST section on the page, right after the Backscan
    section's closing tag.
- **`apps/frontend/lib/api.ts`**: `fetchDeskPlaybookEvidence()` — a plain `GET
  /research/desk/playbook/evidence`, the `fetchDeskPlaybookBackscanRuns` shape exactly (no params,
  `{ok, data, error?}` result).
- **`apps/frontend/lib/types.ts`**: `DeskPlaybookEvidenceCellStats`,
  `DeskPlaybookEvidenceBaselineStats`, `DeskPlaybookEvidenceCell`, `DeskPlaybookEvidenceBreach`,
  `DeskPlaybookEvidenceOtherSignature`, `DeskPlaybookEvidence`. Deliberately does NOT reuse
  `DeskForwardAvgCell` for the signal/baseline stats shapes — the rail's own avg cell has no
  p25/p75 at all; reusing it would mean either a partial/misleading type or a backend response that
  doesn't match it.

## New User-Facing Capability

The operator can scroll `/desk` to the new **Playbook Evidence** section and see, per setup family
and side, how many recorded signals fired and what their forward-return/max-drawdown distributions
look like against the pooled seeded baseline — with thin (`below_min_n`) cells honestly tagged
rather than hidden.

## New Information Displayed

Per-`(setup_id, side, measure)` cell pairs (signal vs. baseline) with `n`, `n_truncated`,
`n_baseline`, `median_pct`, `p25_pct`, `p75_pct`, `mean_pct`; `below_min_n` tags;
`invalidation_breached` counts by horizon; `other_signatures` listings; the `EVIDENCE_REGISTER`
disclosure paragraph.

## New User Actions

None beyond scrolling — per T-7 ("GETs never compute"), this section carries no refresh/compute
trigger of its own; every other `/desk` section has at least one button, this one has none.

## UI Surface Changes

`/desk` gains ONE new section, **Playbook Evidence**, below the shipped Backscan panel. No
existing section, route, or nav entry changes — nav stays exactly `Cockpit / Structure / Desk`.

## Visual Requirements — how they were met

- **Component pattern**: matches the existing Playbook Signals / Backscan panel style — a bordered
  `Panel` with a heading, a dense `text-xs`/`font-mono` data table, inline badge styling for
  `below_min_n` (`border-amber-800/60 bg-amber-950/40 text-amber-300`, the SAME visual family the
  Backscan plan preview's own `missing_at_current_signature` badge uses).
- **Layout**: dense, full-width within the existing `/desk` main content column; the cells table
  wraps in `overflow-x-auto` (14 columns is wide) so the page body itself never scrolls
  horizontally.
- **States handled**: loading (skeleton via `LoadingPanel`), backend-unavailable (`UnavailablePanel`
  with the standard "nothing cached and nothing fabricated" copy), honest-empty (`EmptyState` when
  every cell has `n === 0` — no recorded signals at all), a signature with records but not current
  (rendered under `other_signatures`, never folded into the table), cache cold vs. warm (verified
  byte-identical at the backend level — TC-2 — so there is nothing for the frontend to distinguish).

## Tests Run

- `npx tsc --noEmit` (from `apps/frontend/`) — zero errors.
- `test_desk_ui_guards.py` (backend, scans this file's source) — 39 passed, including the new
  `_PRICE_ARITHMETIC_FIELDS` entries and their seeded counter-test.
- `test_copy_discipline.py`'s `test_lint_frontend_source_literals_are_clean` — passes with zero
  edits needed (the `app/**/*.tsx` glob already covers the new section's copy).
- Live browser verification (scoped rig, `rm -rf .next` rebuild, :3301/:8301): the section renders
  the register paragraph, the 270-row cells table, the 90-row breach table, and the
  `other_signatures` listing exactly as served — confirmed via a live Chrome-CDP `fullpage`
  screenshot cropped to the section (see the dev handoff's Known Issues for a headless-Chrome
  viewport-screenshot quirk this required working around) and via the page's own extracted
  markdown/DOM text, both matching the raw JSON from `curl`.

## Known Issues

- The cells table always renders all 270 rows (the full declared setup × side × measure cross
  product) rather than filtering to only-populated combinations — this matches the IN SCOPE
  contract's literal "renders the served cells as a table" wording and keeps the frontend a pure,
  unconditional pass-through, but makes the table quite tall on a real corpus. No pagination or
  collapse was added because the spec's own "New user actions: none beyond scrolling" line rules
  out an expand/collapse interaction.
- See the dev handoff's Known Issues for the headless-Chrome CDP screenshot quirk (blank frame
  after any non-zero scroll; worked around with `fullpage: true` + crop) and the session-order
  dependency of the evidence corpus's exact numbers on the scoped browser-QA rig.
