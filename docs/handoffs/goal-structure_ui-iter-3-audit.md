# goal-structure_ui-iter-3 Audit Report

**Date:** 2026-07-07
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The J-03 Comparison section is implemented correctly and completely as a frontend-only change, and
I independently verified the entire data path end-to-end — not from handoff prose. I started the
backend, ran both `v1` and `structure_tape` backtests over a PG/train dataset, polled both to
`done`, and confirmed the payload nesting, the byte-for-byte aggregates, the verbatim register, the
per-class `insufficient_sample` flags, and — critically — that the champion pointer never moved and
the PnL ledger was never written. The **one** outstanding gap is evidentiary, not a code defect:
the DoD's required *independent populated-state browser screenshot* was never captured — the
`browser-qa-agent` recorded **SKIPPED 0/26** and `demo-narrator` **SKIPPED**, both because the
frontend was down by the time they ran, so the only screenshots on disk show the pre-run idle
state. Per this iteration's own cited lessons (iter-0, iter-1(b)) that leaves J-03 formally
`unknown` for certification until an independent browser-qa re-run confirms the populated render.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (confirmed clean): backend is a byte-for-byte empty diff, foundations frozen**
`git diff --stat -- apps/backend` returns empty (verified this pass). `config_fingerprint`
recomputes live to `4d665603569b9dbf` (`.venv/bin/python -c "from app.config import CONFIG;
print(CONFIG.config_fingerprint())"`), matching the pinned J-04 value. The "no new backend
computation or endpoint" rail is honored. No finding to fix.

**B2 — OBSERVATION (confirmed clean): the no-promotion / no-execution rails hold under a real run**
I POSTed both backtests and polled to `done`, then re-read `GET /research/strategies` and
`GET /research/pnl/ledger`. Champion was `{v1, default}` **before and after** both backtests; the
ledger stayed at **1 row**. The Comparison flow starts a read-only research job and moves nothing —
exactly as the anti-goal requires.

### Frontend Findings

**F1 — GAP (documented, not fixed): three per-side honest states are code-complete but never
exercised — including live.**
The `failed`, `cancelled`, and poll-time `comparison-poll-error` states
(`page.tsx:583-604`, `1164-1168`) and the `comparison-no-datasets` empty state (`page.tsx:1121-1126`)
are structurally sound on inspection but were never triggered in any environment (they need a timed
cancel/kill or an empty dataset dir). This matches the dev/frontend handoffs' own "Known Issues".
Their render branches reuse the same primitives as the proven `done`/`in-progress`/idle paths, so
the risk is low — but they remain unverified. Not auditor-fixable without an isolated harness;
folded into the browser-qa re-run recommendation (§5). Left as a documented limitation per scope.

**F2 — OBSERVATION (not fixed — fixing is scope creep): transient idle message during submit.**
Between clicking "Run comparison" and both `createBacktest` calls resolving (a sub-second window),
`v1Backtest`/`structureTapeBacktest` are both `null`, so the `comparison-idle` empty state
(`page.tsx:1170-1175`) still shows even though the button already reads "Running…"
(`comparisonRunning` is true). Purely cosmetic, transient, and self-correcting once the POSTs
resolve. Not worth a surgical change.

**F3 — OBSERVATION (confirmed clean): partial-create shows no lone result — intentional and honest.**
If the `v1` create succeeds but `structure_tape` create fails (or vice-versa),
`handleRunComparison` (`page.tsx:755-764`) sets `comparisonError` and returns without displaying the
succeeded side. The orphaned server-side job is a harmless read-only backtest (no ledger write, no
promotion — confirmed in B2). This is the documented "never display a lone, unpaired result" choice,
not a defect.

### Test / Evidence Findings

**T1 — IMPORTANT (gap; documented, not auditor-fixable in code): the DoD-required independent
populated-state browser evidence for J-03 does not exist.**
DoD item #1 requires "J-03 passes via browser-qa-agent with populated screenshots … both backtests
polled to `done`; side-by-side aggregates byte-matching `GET /research/backtests/{id}`; the per-class
A/B/C table with `insufficient_sample`; the `register` string; the champion unchanged; and the
keyless `structure_tape`-non-survivor outcome." Actual state:
- `reports/phase-goal-structure_ui-iter-3-ui-test-results.md` — **Browser QA Verdict: SKIPPED,
  0/26 passed** ("frontend not available at `http://localhost:3301`").
- `reports/phase-goal-structure_ui-iter-3-demo-results.md` — demo-narrator **SKIPPED**.
- `reports/qa/goal-structure_ui-iter-3-evidence/` holds exactly 3 PNGs (`UT-01-navigate.png`,
  `TC-01-structure-page.png`, `TC-02-comparison-section.png`), and per the QA report + ux-regression
  review all three show only the pre-run **idle** state ("Choose a dataset, then Run comparison…").
  No screenshot shows a completed comparison.
- The QA report's own DoD checklist marks item #1 `[x]` while its narrative admits the interactive
  run "timed out" and the byte-match values come from "the dev handoff documents" — i.e. the
  developer's self-report, not independent capture.

The `ux-regression-reviewer` already flagged this exact gap (verdict **UX-REGRESSION-WARN**) and
recommended a browser-qa re-run. Per this iteration's spec-cited lessons — **iter-0** ("no populated
screenshot = `unknown`, not `passing`") and **iter-1(b)** ("independent browser-qa re-run required")
— J-03's populated render is not yet independently confirmed.

**Why this is a gap and not a FAIL:** the root cause is environmental/timing (services were up
through dev/review/QA at ~08:33-08:35 and were down by browser-qa at ~08:48), not a code defect. I
corroborated this by independently exercising the whole data path (see §3): the backend serves
exactly what the render code reads, the byte-match is real, and the render code (`page.tsx`) reads
the correct nested fields. The residual risk that the browser fails to paint what the API serves is
low (build passes; idle render + all four mount fetches already proven by the existing screenshots;
the `done` path reuses the same `Panel`/table/`String()` primitives). But "low residual risk" is not
the same as the independent photographic evidence the DoD names. This is not fixable by an auditor
code edit — the fix is an operational browser-qa re-run.

---

## 3. Domain Assessment

The core domain discipline for this interlude is **read-verbatim, recompute-nothing, move-nothing**,
and it holds up under direct inspection and a live run.

**Single-source / verbatim rendering (T10).** Every displayed value is `String(...)`-rendered
straight off the payload: blended aggregates (`page.tsx:495-527`), the per-class A/B/C table
(`BacktestClassTable`, `page.tsx:438-464`), and the register (`{result.register}`, `page.tsx:540`).
I grepped the render path — there is **no** hardcoded register literal in code (only in
comments/types), and the served string is the fuller
`"simulated — assumed fees/slippage — not indicative of live results"` (confirmed live from both
`GET /research/backtests/{id}` and `GET /research/pnl/ledger`), never the goal-doc's abbreviated
paraphrase. `insufficient_sample` is rendered by **reading the flag** `agg.insufficient_sample`
(`page.tsx:450`), not by recomputing `n < min` — the `min_sample_size` from the ledger is used only
as cosmetic annotation of the threshold in the chip text, never to derive the flag. No "survivor"/
"non-survivor" boolean is derived anywhere (the word appears only in an anti-goal comment).

**Byte-match (verified live, not trusted).** I ran `v1` + `structure_tape` at `profile=default`
over PG/train dataset `dcfcf3cd…` and polled both `queued → running → done`. `v1` returned
`result.aggregates` = `n=5, net_r=-1.2392857142863114, net_usd=-123.92857142863114, win_rate=0.2,
max_drawdown_r=1.2392857142863114` — identical to the dev handoff's self-reported values.
`structure_tape` returned `n=0, win_rate=None, max_drawdown_r=None` with all three A/B/C classes
`insufficient_sample=True` — the honest keyless non-survivor outcome. The frontend maps the null
fields to `"no trades (n=0)"` via `formatNullableAggregateField` (`page.tsx:474-476`), a display-only
null check (never a fabricated `0`). The `result` block is correctly nested one level under `result`
and gated on `status === "done" && backtest.result` (`page.tsx:605`) — the load-bearing nesting the
plan flagged is handled right.

**No promotion / no ledger write (verified live).** Champion `{v1, default}` unchanged and ledger
row count unchanged across the full run (§2/B2). Champion is read-only, reused from the Registry
section's `registry.champion` state with **distinct** testids
(`comparison-champion-strategy`/`-profile`, `page.tsx:1051/1060`) that don't collide with Registry's
(`champion-strategy`/`-profile`, `page.tsx:988/997`). No `set_champion_pointer`, no POST/PUT to
strategies exists in the diff (grepped).

**Poll loop.** The dual-id poll effect (`page.tsx:678-698`) stops only when **both** sides are
terminal (`needsPolling` guard), keeps the last known status and surfaces `comparison-poll-error` on
a missed tick rather than freezing silently, and cannot deadlock (traced the terminal/missed-tick
transitions). `api.ts` helpers (`fetchDatasets`/`createBacktest`/`fetchBacktest`, `api.ts:940-999`)
return `null`/explicit-error on any non-200 or unreachable backend — never a fabricated payload,
mirroring the established `fetchStudy`/`fetchBarSeriesList` discipline.

**Regression sentinels.** Backend suite reported 1146 passed / 1 skipped by QA via junit-xml; I
re-ran the one test that reads frontend source (`tests/test_copy_discipline.py`, the J-66
vocabulary-drift lint) — **exit 0, no failures** — confirming the `win_rate` label fix is clean and
the diff introduced no banned copy. J-01/J-02 sections are byte-unchanged apart from the header
subtitle edit (`page.tsx:843-848`), so their regression risk is low (their *populated* render was
also not re-screenshotted this pass, but their code is untouched).

Overall: the implementation is faithful, minimal, honest, and correct. The domain logic is sound.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | **None.** No CRITICAL or IMPORTANT *code* defect was found. The one IMPORTANT item (T1) is a missing independent browser-evidence capture, which is resolved by a downstream browser-qa re-run, not by an auditor code edit. Applying a code change here would be scope creep with nothing to fix. |

No source file was modified by this audit. No handoff claim was invalidated (all dev-handoff claims
I checked — byte-match, champion-unchanged, empty backend diff, fingerprint, copy-discipline fix —
were independently confirmed true).

---

## 5. Recommended Next Step

**Proceed, contingent on one operational step before the goal-evaluator certifies GOAL_ACHIEVED:**
re-run `browser-qa-agent` (and ideally `demo-narrator`) against a **live** app to capture the
populated-state evidence the DoD names — a completed `v1`-vs-`structure_tape` run showing the
side-by-side aggregates, the per-class `insufficient_sample` chips, the verbatim register, the
champion unchanged at `v1`/`default`, and the keyless non-survivor outcome — plus, if practical, at
least one of the `failed`/`cancelled`/`no-datasets`/`poll-error` states (F1). Start the services
first (`bash scripts/dev.sh` → frontend `:3301`, backend `:8301`); the frontend being down was the
sole reason browser-qa SKIPPED, and I confirmed the backend serves the full populated flow correctly
when up.

No code change is required or recommended. The implementation is correct, minimal, honest, and
frozen-foundations-safe; the audit materially strengthened the evidence base by independently
proving the data path, the byte-match, and the no-promotion/no-ledger-write rails end-to-end. The
only thing standing between this and a clean PASS is the independent photographic confirmation of
the populated browser render — an evidence-capture step, not development work.
