# goal-yahoo_fetch-iter-5 Audit Report

**Date:** 2026-07-10
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-05 — the era's headline "fetch-from-the-app" journey — is genuinely achieved. The `/structure`
"Fetch from Yahoo Finance" control works end-to-end (POST `/research/bars` store-first → reuse of
the existing J-04 levels/zones render path → a data-driven "Yahoo Finance" provenance badge), the
frozen era-4 foundations are byte-identical, and no anti-goal is violated. The gaps that remain are
all GAP/OBSERVATION-level (a confirmed-but-non-blocking dropdown overlay, a pre-existing
whitespace-only query edge, and the carried-forward mixed-feed pooling limitation); none compromise
the phase goal, and I applied no fixes because each would be scope creep or would touch an
out-of-scope shared component.

Independently re-verified (not trusted from the handoffs): full backend suite **1207 passed / 0
failed / 6 skipped** (`pytest tests/ -q`, exit 0); `config_fingerprint == 4d665603569b9dbf`;
`git diff HEAD` **empty** on `levels.py`/`backtests.py`/`strategies.py`/`config.py`/`bars.py`/
`bar_index.py`/`providers/adapters/`/`tape/`/`mcp/`; `tsc --noEmit` exit 0; the 4 QA screenshots
exist and show a real render; the POST contract and the badge's taxonomy-lookup were traced in
source.

---

## 2. Findings

### Backend Findings

**B1 — GAP (carried-forward, do-not-fix): mixed-feed pooling in feed-blind `compute_levels`**
`research/levels.py` selects a symbol's series by symbol alone (feed-blind), so a symbol holding
both a `feed="yahoo"` and an Alpaca `feed="sip"` series over overlapping timeframes would be pooled
into one confluence cluster. Explicitly OUT OF SCOPE this iteration (frozen, fingerprint-locked;
mutating it is a critical anti-goal), logged in `runs/goal-session-yahoo_fetch/state/assumptions.md`.
Verified benign in practice: all 9 series currently in `.data/bars/` are `feed="yahoo"` (a
single-feed store — `record.meta.feed` inspected on every file), so no pooling occurs on the
evidenced path. J-05's "honestly segregated from Alpaca sip" is met at the fetch/store/display layer
(distinct append-only records + the "Yahoo Finance" badge). Not introduced this iteration.

**B2 — GAP (do-not-fix): whitespace-only `?symbol=` still routes to the index path**
`routes.py:1729` normalizes with `symbol.strip().upper() if symbol else None`. A blank `?symbol=`
(empty string) is falsy → `None` → takes the byte-identical `store.list()` path (the DoD's actual
requirement — verified: the new test `test_blank_symbol_param_is_byte_identical_to_no_param_even_with_an_unindexed_series`
passes). But a whitespace-only `?symbol=%20` is truthy → normalizes to `""` (not `None`) → still
falls through to `index.list(symbol="", …)` and returns an empty list, NOT byte-identical to
no-param. This is pre-existing behavior (identical before and after this iteration — the reorder
only changed the empty-string case), not a regression, and the spec's DoD pins only the blank case.
The spec's IN-SCOPE prose said "blank/whitespace", so I record the whitespace half as an unmet
sub-clause. Reviewer flagged the same as a NOTE. A whitespace-only symbol query param is not a
realistic client input; fixing pre-existing behavior beyond the DoD is scope creep — documented, not
fixed.

### Frontend Findings

**F1 — GAP (confirmed, do-not-fix): `SymbolSearch` suggestion dropdown auto-opens over the badge/chart after every successful fetch**
`handleFetchYahoo` (`app/structure/page.tsx:793-795`) seeds the pre-existing Load form's
`symbolInput` on success; `SymbolSearch`'s `useEffect([value])` cannot distinguish a programmatic
set from a keystroke and calls `setOpen(true)`, so every successful fetch pops the "AAPL/AAPB/AAPD…"
suggestion list open directly over the region where the provenance badge (`page.tsx:1094`) and the
top of the level list render. This is visible in QA's own evidence — I confirmed it in
`TC-07-chart-rendered.png` and `TC-08-levels-zones.png`. It does NOT break the journey: the badge
and levels render, data is intact, the dropdown self-dismisses on an outside click, and QA verified
the badge text ("feed Yahoo Finance") via DOM. It is a real interaction/z-index defect that
degrades the headline moment's screenshots. The clean fix lives in `components/SymbolSearch.tsx` — a
shared component NOT in this iteration's `changed_files` that also serves the cockpit and the Load
flow — so fixing it here is scope creep with regression risk; the alternative (not seeding
`symbolInput`) reverts a deliberate design choice and can desync the Load form. Documented for a
future polish pass (as the frontend handoff itself already recommended).

### Test Findings

**T1 — OBSERVATION: TC-11 (no-stored-bars empty state) not exercised in a browser this iteration**
The QA test plan defined TC-11 as a browser test, but it does not appear in the executed QA report's
15-item table (neither pass, fail, nor skip). However the DoD explicitly allows "browser **or**
unit", and the unit level is covered: `tests/test_levels_api.py:330,340` assert
`no_bar_series_for_symbol is True` for an unrecorded symbol, and the frontend render branch
(`app/structure/page.tsx:1066-1068`, `structure-no-bar-series`) is byte-identical to the passing
J-04 baseline. The DoD item is therefore satisfied; only the fresh browser evidence is missing.

**T2 — OBSERVATION: QA report body is duplicated**
`reports/qa/goal-yahoo_fetch-iter-5-qa.md` concatenates two copies of its header/summary (a second
"# QA Validation Report" begins at line 105). Cosmetic; both copies agree and carry the same PASS
verdict. No functional impact.

**O1 — OBSERVATION: the charted timeframe can differ from the fetched timeframe**
The fetch reuses the J-04 render path, which draws the symbol's *representative* (shortest-timeframe)
series via `pickRepresentativeSeries` (`page.tsx:152-167`), not necessarily the timeframe just
fetched (e.g. fetching `1d` renders the pre-existing `5m` series — the chart caption honestly says
"Candles: 5m series"). This is honest (the badge is keyed off the charted series' own `feed`, so
badge and chart always agree; all data is real and verbatim) and is pre-existing J-04 display
behavior the spec mandated reusing. No change warranted.

---

## 3. Domain Assessment

The core domain logic is correct and, importantly, additive. The two new backend values are both
already-owned rows read verbatim, exactly as the Data Contract requires:

- **Taxonomy label** — `FEED_BASIS_LABELS["yahoo"] = "Yahoo Finance"` (`taxonomy.py:45`) is the sole
  owner; `GET /research/taxonomy` serves `{"id":"yahoo","name":"Yahoo Finance"}` automatically.
  Asserted with exact values by the updated canary (`test_research_api.py:154-157`, passing).
- **B2 normalization** — the reorder (`routes.py:1729-1732`) makes a blank `?symbol=`/`?timeframe=`
  take the byte-identical `store.list()` path, proven against an *un-indexed* record (the case the
  bug actually leaked), passing.

The write path is honest and scoped: `POST /research/bars` validates (422/503/504/409, each
nothing-written / nothing-fabricated), runs the store-first coordinator BEFORE any adapter
(`routes.py:1636-1640`: an index hit returns `{"bar_series": store.get(...)}` → 200, zero network,
never a 409 on a repeat window), and returns `{bar_series: meta}`. The frontend contract matches
exactly (`BarRecordRequest` fields `symbol/timeframe/start/end` ↔ the `recordBarSeries` body;
response `bar_series` ↔ the helper's unpack). The provenance badge is genuinely data-driven —
`FeedBasisBadge` computes `feeds.find(f => f.id === dataFeed)?.name ?? dataFeed`
(`FeedBasisBadge.tsx:60`) with no hardcoded label; `grep -r "Yahoo Finance" apps/frontend` hits only
goal.md-mandated button/panel/aria copy and comments, never the badge. The UI recomputes nothing:
levels/zones come from the reused J-04 read path, candles from `GET /research/bars`, the label from
taxonomy — coherence-clean. No execution path, no advice/prediction copy, no champion promotion, no
mutation of frozen computations.

---

## 4. Fixes Applied During This Audit

None. Every finding is GAP- or OBSERVATION-level. Per the auditor contract, GAPs/OBSERVATIONs are
documented, not fixed — fixing F1 would touch the out-of-scope shared `SymbolSearch.tsx`, and fixing
B2's whitespace edge would alter pre-existing behavior the DoD did not require. No CRITICAL or
IMPORTANT issue was found that would warrant a code change.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied (no CRITICAL/IMPORTANT findings). |

---

## 5. Recommended Next Step

**Proceed.** J-05 is functionally complete and independently verified; it is the last Must-have
journey in Era 5, so the goal-evaluator can consider `GOAL_ACHIEVED` once the remaining deterministic
gates (coherence-auditor for iter-5, which has not yet run) confirm — from source inspection I expect
COHERENCE-PASS (zero client recomputation, no new endpoint/bar-store/computation).

Carry two low-effort items into a future polish iteration (neither blocks the goal):
1. Stop `SymbolSearch` from auto-opening its dropdown on a programmatic `value` change (F1) — this
   directly cleans up the headline fetch moment's visuals.
2. Optionally close B2's whitespace half (`if symbol and symbol.strip()`) and record a browser TC-11
   for the fetch-driven empty state, so J-05's honest-empty-state acceptance carries browser
   evidence rather than unit + code-reading alone.
