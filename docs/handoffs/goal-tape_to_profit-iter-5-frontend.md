# goal-tape_to_profit-iter-5 Frontend Handoff

**Phase:** goal-tape_to_profit-iter-5
**Date:** 2026-07-03
**Agent:** developer
**Status:** complete

## What Was Built

- **New page `apps/frontend/app/performance/page.tsx`** — the fourth top-level page, in the
  established dark cockpit design language (slate-950 background, slate-900/60 panels,
  slate-800 borders, `font-mono` for every numeric/id, amber for degraded + insufficient-sample,
  no new effects, no new dependencies). Layout: header → 2-column grid on `lg`
  (ledger left, champion aside right), single column on narrow; the ledger table sits in its own
  `overflow-x-auto` container and fits without scroll from ~700px up.
- **Ledger table rendering `GET /research/pnl/ledger` verbatim.** One panel per enhancement row:
  title, mono enhancement id, "Appended dd-MM-yyyy" (via the existing shared `formatDateDMY`
  helper, operator-local timezone — presentation of a stored instant, not a recomputation). The
  measurements table uses the EXACT committed `reports/pnl/pnl-history.md` shape
  (`side | split | net R | net $ | n | sample`): train and hold-out are separate rows, never
  pooled, no combined figure anywhere; each net $ sits beside its net R and its n.
  - **Numbers render exactly as served:** every value is `String(value)` of the parsed JSON
    number — the same shortest round-trip decimal the API text carries. No rounding, no
    formatting, no arithmetic, no derived figures anywhere on the page (verified in-browser:
    19/19 cell-vs-API equality checks, full precision, e.g. `-0.16000000000001136`).
  - **Founding baseline:** `baseline: null` renders one explicit marker row — "no prior
    incumbent — founding row (the baseline side is explicitly absent, never zeros)" — NEVER a
    fabricated 0.
  - **Insufficient-sample labels** render from the API's per-split `insufficient_sample`
    boolean, with the served `min_sample_size` in the label text (`insufficient sample (n < 5)`)
    — live on both founding-row splits (real n=1 data, not a mock).
  - **Provenance** compact under the table: strategy id, profile, config fingerprint, per-split
    backtest id + dataset id + checksum (mono, break-all).
  - **The register** renders from the payload's `register` field into an amber banner
    (`data-testid="pnl-register"`) — no frontend copy of the string exists anywhere.
- **Champion summary panel rendering `GET /research/profiles` verbatim**
  (`data-testid="champion-summary"`): champion strategy + profile (mono), plus the profile
  registry list with each profile's frozen / default status rendered from the served booleans.
  Purely declarative copy; the champion is read ONLY from this endpoint — never inferred from
  ledger provenance, never hardcoded.
- **States:** loading (pulse placeholder per panel); backend unreachable → explicit per-panel
  unavailable state mirroring the NavBar degraded pattern ("Backend unreachable — is the API
  running?" + "Nothing cached and nothing fabricated is shown in its place."); empty ledger →
  honest explicit empty state (register still shown). All three exercised live at dev time.
- **NO NavBar edit and no hardcoded route/link anywhere** — the Performance link appears on
  every page solely because `UI_ROUTES` in `app/meta.py` gained the entry (row 35 single
  source). Cockpit, Journal, and Studies pages untouched.
- **Support code:** `lib/types.ts` gained the row-32/row-33 payload types; `lib/api.ts` gained
  `fetchPnlLedger` / `fetchProfiles` following the existing `fetchStudies` pattern (explicit
  error results, no caching, no timeout literals).

## Files Changed

- `apps/frontend/app/performance/page.tsx` -- NEW: the /performance page (read-only; no buttons/forms/controls)
- `apps/frontend/lib/types.ts` -- appended PnL-ledger + profiles payload types
- `apps/frontend/lib/api.ts` -- appended `fetchPnlLedger` / `fetchProfiles` helpers (+ two type imports)

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: compiled successfully (type-check + compile); `/performance` in the route table (2.52 kB,
static)

Copy-discipline lint (backend suite, part (c) walks all frontend source literals):
`pytest tests/test_copy_discipline.py` → passed — the page's copy carries no imperative,
prediction, or positive profit/edge/win-rate language (the measurement-framing line is
negation-cleared, matching the studies-page precedent).

Browser verification (Chrome against live seeded backend): 19/19 page-equals-API checks true;
empty state, unavailable state, and 4-link nav verified. Deterministic replay of the new
J-05 golden script: PASS end-to-end.

## Known Issues

- None frontend-specific. The page intentionally has no sorting/filtering/pagination/charts
  (out of scope; one founding row exists) and no client-side number formatting of any kind — if
  display rounding is ever wanted it must come from the serving side.
