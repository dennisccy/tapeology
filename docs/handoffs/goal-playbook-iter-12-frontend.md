# goal-playbook-iter-12 Frontend Handoff

**Phase:** goal-playbook-iter-12
**Date:** 2026-08-12
**Agent:** developer
**Status:** complete

## What Was Built

The `/desk` Playbook Evidence section (already-shipped J-08 section, unchanged home) becomes more
legible about its own denominator. Two additive UI changes, no new page, no new nav entry, no new
route, no client-side computation anywhere:

1. **A new "basis" line**, beside the existing "Built from signature:" line, stating the
   pooled/default signature's own record count, contributing dates, and created-at span (e.g.
   *"Basis: 4 records pooled from 2026-06-22, 2026-06-23, 2026-06-24, 2026-08-07 (created
   2026-08-11T09:59:58.149134Z .. 2026-08-11T13:45:47.320003Z)"* -- verified live against the
   operator's real corpus). `data-testid="desk-evidence-basis"`. The existing "Built from
   signature:" line's own text is byte-unchanged.
2. **Five new columns in the cells table**: the signal side gains `unmeas` (n_unmeasured) and
   `sess` (n_sessions) beside its existing `n`/`trunc`; the baseline side gains `trunc`
   (n_truncated), `unmeas` (n_unmeasured), and `sess` (n_sessions) beside its existing `n`. Every
   value is a straight pass-through of `GET /research/desk/playbook/evidence`'s enriched body --
   nothing computed in the browser. New `data-testid`s: `desk-evidence-signal-n-unmeasured`,
   `desk-evidence-signal-n-sessions`, `desk-evidence-baseline-n-truncated`,
   `desk-evidence-baseline-n-unmeasured`, `desk-evidence-baseline-n-sessions`.

**Passenger (unrelated to J-11):** the Playbook Signals section's session-date input now visibly
reddens/ambers on an invalid value instead of staying grey -- a one-line, one-input CSS fix (see
"Passenger fix" below).

## New user-facing capability

The owner can now tell, for any evidence cell, how much of its pooled signal set was actually
usable versus recorded-but-unmeasurable at that horizon (and, separately, truncated), how many
distinct sessions it draws from, and -- for the pooled table as a whole -- exactly which recorded
dates and how many records it is built from. Concretely: `double_top:short` at `1m` on the real
corpus now visibly shows `n: 31` beside `unmeas: 59` (of 90 total), instead of a bare `n: 31` that
could be misread as a small sample.

## New information displayed

Per cell: `n_unmeasured` and `n_sessions` beside the signal side's existing `n`/`n_truncated`;
`n_truncated`, `n_unmeasured`, and `n_sessions` beside the baseline side's existing `n_baseline`. At
the top of the section: a basis line stating the pooled/default signature's own record count,
contributing dates, and created-at span. Passenger: the Playbook Signals date input's border color
now visibly changes on an invalid value.

## New user actions

None. The Evidence section stays a read-only, scroll-only GET view (no new button or control, T-7:
GETs never compute).

## UI surface changes

- `/desk` -> Playbook Evidence section: one new header line (`PlaybookEvidenceBasisLine`), five new
  columns in the existing cells table (two header rows updated: `Signal` colSpan 6->8, `Baseline`
  colSpan 5->8; the cells table's `min-w` widened 900px->1180px to fit them). No other row, column,
  or section in this table changed.
- `/desk` -> Playbook Signals section: the session-date input's border now resolves amber (not
  grey) when `aria-invalid`. No other input, section, or page changed.
- Every other shipped `/desk`, `/structure`, and `/` surface renders exactly as shipped (nothing
  else in `page.tsx` outside these two components was touched -- confirmed by `git diff --stat`
  showing a 54-line diff entirely inside the evidence-section functions and the one date-input
  `className`).

## Component/testid inventory (new)

| Component | data-testid | Notes |
|---|---|---|
| `PlaybookEvidenceBasisLine` (new) | `desk-evidence-basis` | own `basis: DeskPlaybookEvidenceBasis` prop |
| `PlaybookEvidenceCellRow` (extended) | `desk-evidence-signal-n-unmeasured` | new `<td>`, signal side |
| ″ | `desk-evidence-signal-n-sessions` | new `<td>`, signal side |
| ″ | `desk-evidence-baseline-n-truncated` | new `<td>`, baseline side |
| ″ | `desk-evidence-baseline-n-unmeasured` | new `<td>`, baseline side |
| ″ | `desk-evidence-baseline-n-sessions` | new `<td>`, baseline side |

No existing `data-testid` was renamed, removed, or repositioned relative to its own row's other
cells. The row-level `data-testid="desk-evidence-cell-row"` and the below-min-n flag cell are
unchanged.

## Passenger fix: Playbook Signals date input amber border

`ASOF_INPUT_CLASS` (a shared constant styling FIVE inputs across three sections) carries
`border-slate-700`; the Playbook Signals date input conditionally appends a plain
`border-amber-500` on an invalid value. Both are single-class Tailwind border-color utilities of
EQUAL CSS specificity, so the compiled stylesheet's own utility declaration order -- not the JSX
class list's order -- decides which one wins, and it is `border-slate-700` that wins live: the
input stays grey even when `aria-invalid="true"` and the error text is already showing. Fixed by
switching that ONE input's own conditional class to Tailwind's `!` (important) modifier --
`"!border-amber-500"` -- which forces it to win regardless of stylesheet order. Scoped to that one
input's own `className` expression only:

- `ASOF_INPUT_CLASS` itself: byte-unchanged.
- The Refresh Data From/To inputs (`page.tsx` ~4411/4427): share the IDENTICAL, still-unfixed
  collision -- deliberately carried, per this iteration's own scoping decision (out of scope; not a
  regression, since they never worked before either).
- The Backscan/Deep-backfill From/To inputs (~3412/3425/3608/3621): never had the amber affordance
  at all -- unchanged, still four bare `className={ASOF_INPUT_CLASS}` call sites.

## Data flow / no client math

`lib/api.ts`'s `fetchDeskPlaybookEvidence()` needed zero changes -- it already does a pure
`fetch` + `res.json()` pass-through with no field-level logic, so the enriched body (seven new
fields) flows through automatically. `lib/types.ts`'s `DeskPlaybookEvidence`/
`DeskPlaybookEvidenceCellStats`/`DeskPlaybookEvidenceBaselineStats`/
`DeskPlaybookEvidenceOtherSignature` interfaces were widened to match the server's actual shape
(TypeScript would otherwise silently allow reading an untyped field); the new
`DeskPlaybookEvidenceBasis` interface was added. `npx tsc --noEmit` -> zero errors.

Every new numeric is guarded against future client-side recomputation by
`tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` pattern, extended to cover
`cell.signal.n_unmeasured`/`n_sessions`, `cell.baseline.n_truncated`/`n_unmeasured`/`n_sessions`,
and `basis.n_records`, with a seeded counter-test proving the extended pattern actually catches a
violation on each of the six new fields individually (the "a lint that cannot fail proves nothing"
precedent, applied per-field).

## Browser verification status

**Not run by this agent.** Per this session's established division of labor (see the dev handoff's
"Live verification" section and iter-10's own precedent), the formal browser pass -- a real Chrome
screenshot of the basis line and a visible `n_unmeasured > 0` cell after a T-9 clean rebuild
(`rm -rf apps/frontend/.next`) -- is the browser-qa-agent's own pipeline stage. This handoff's
dev-level evidence is a live, read-only REST check against the operator's real backend
(`GET /research/desk/playbook/evidence` on `:8301`) that reproduces the phase spec's own two cited
real-corpus numbers exactly (`double_top:short`@`1m`: `n=31, n_truncated=0, n_unmeasured=59`,
`31+0+59=90`; `capitulation:long`@`4h`: `n=25, n_truncated=4` beside `n_baseline=8`) -- strong
confirmation the SERVED data is correct, offered as a head start for the browser pass, not a
substitute for it. No screenshot exists yet, so J-11's own browser-acceptance line is `unknown`,
never `passing`, until that pass runs.

## Known Issues

Same as the dev handoff -- no browser screenshot yet (deferred to browser-qa-agent), no
demo-narrator walkthrough yet (deferred to that agent's own stage).
