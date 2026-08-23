# goal-rapid-microscope-iter-23 — UI Test Results

**Phase:** goal-rapid-microscope-iter-23
**Date:** 2026-08-23
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

Lean-mode scope: only J-06 was assigned to this dispatch. J-01, J-02, J-03, J-04, J-05, J-08, J-10
are verified separately by deterministic replay (see
`reports/phase-goal-rapid-microscope-iter-23-regression-replay-results.md`, 7/7 PASS) and are not
re-tested here. J-07 and J-09 are stable/digested per this iteration's own scope and not assigned
to browser QA.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth | happy-path | P1 | `/desk` Microscope Readiness section shows `sealed_tranche.by_universe["rapid-microscope-j06-starter"]` as one opaque-pool aggregate (80 shards/80 symbol-days, matching `joinable_corpus.withheld_excluded: 80`); Validation Vault section shows 21 sealed shard rows keyed by opaque surrogate id with rule/vault-secret commitments (not raw values); no symbol/session-date for any withheld/sealed shard anywhere in the DOM; legacy 12 symbol-days still `exploratory` | Both sections rendered exactly this, against a backend instance pointed at the real `apps/backend/.data/datasets` store (80/80 aggregate confirmed; 21 sealed vault rows confirmed, every non-identity column reading `sealed — opaque`; legacy 18-dataset/12-symbol-day table intact and unchanged; only sha256 commitments shown for rule/vault-secret, never raw values) | PASS | `reports/qa/goal-rapid-microscope-iter-23-evidence/J-06-result.png`, `reports/qa/goal-rapid-microscope-iter-23-evidence/J-06-vault-shards.png` |

---

## Passed Tests

### UT-J-06 — The recorder and the Vault — new tape, sealed at birth
**Verdict:** PASS
**Evidence:**
- `reports/qa/goal-rapid-microscope-iter-23-evidence/J-06-result.png` (Microscope Readiness — Sealed Tranche aggregate)
- `reports/qa/goal-rapid-microscope-iter-23-evidence/J-06-vault-shards.png` (Validation Vault — 21 sealed shard rows + universe commitment)
- `reports/qa/goal-rapid-microscope-iter-23-evidence/J-06-full-page.png` (full-page capture, both sections expanded, for context)

**Setup (per `assumptions.md` iter-23 entry and the dev handoff's explicit instructions):** the
standard fixture-scoped QA rig (`:3301`/`:8301`) points `TAPEOLOGY_DATASET_DIR` at an empty fixture
directory and cannot show the real J-06 tranche. I stood up a SEPARATE, throwaway backend on
`:8302` with no `TAPEOLOGY_DATASET_DIR`/`TAPEOLOGY_BAR_DIR` override (config.py's own default
already resolves to the real `apps/backend/.data/{datasets,bars}` store — the same store the
owner's operator act recorded 80 shards into and the dev's suite runs already warmed
`dataset_index.db` for), read-only GETs only. Paired it with a separate frontend on `:3302`,
isolated from the running `:3301` dev server via `NEXT_DIST_DIR=.next-iter23-j06` (a pre-existing,
purpose-built env hook in `next.config.mjs` for exactly this — avoids any `.next` collision with the
live `:3301`/`:8301` rig used by this iteration's regression replay) and
`NEXT_PUBLIC_API_URL=http://localhost:8302`. Did a warm-up `GET /research/desk/micro/readiness`
first (18.0s, consistent with the dev handoff's documented warm-but-not-hot latency). Both scoped
processes were killed after evidence capture; `:3301`/`:8301` were never touched and were confirmed
still healthy (HTTP 200) afterward.

**Steps executed (goal.md J-06 acceptance, TC-1/TC-2):**
1. Navigated Chrome (attached to the existing headless instance on CDP `:9222`) to
   `http://localhost:3302/desk`.
2. Clicked `[data-testid="desk-section-expand-microReadiness"]` — `aria-expanded` flipped to
   `true`; section rendered Corpus Totals (12 distinct symbol-days / 18 distinct datasets — the
   pre-existing legacy invariant, unchanged), then **Sealed Tranche (Aggregate Only)**: `Sealed
   shard count: 80`, `Sealed symbol-days: 80`, `Joinable corpus — withheld (excluded): 80`, and a
   `Universe` table with exactly one row — `rapid-microscope-j06-starter | 80 | 80`. Then Legacy
   Tick Shards (18 rows, all `exploratory`, all real symbol/date — correctly disclosed since these
   are permanently-exploratory, never part of the withheld pool) and Pilot-Study Floors (all three
   studies `floor_unmet`, 11 < 60 required sessions — the honestly-still-unmet ~150-symbol-day gate
   is consistent: `totals.referee_tick_gate_symbol_days: 150` against `distinct_symbol_days: 12`).
   "No integrity errors." shown.
3. Clicked `[data-testid="desk-section-expand-validationVault"]` — `aria-expanded` flipped to
   `true`; section loaded (brief `validation-vault-loading` skeleton, then resolved) and rendered:
   `Shard ledger chain verification: ok`, `Universe ledger chain verification: ok`, a **Shards**
   table with exactly 21 rows (`vshard-...` opaque ids), every row `State: sealed` and every
   identity column (`Dataset`, `Family root`, `Symbol`, `Session date`, `Assigned at`, `Exposed
   at`, `Content checksum`) reading the literal string `sealed — opaque` — no real value in any of
   those columns for any row — and a **Universes** table with one row:
   `rapid-microscope-j06-starter`, `Rule commitment: b0d6d09e...` (sha256), `Vault secret
   commitment: 68f2bbb382de525d...` (sha256 — matches the TC-9-named prefix `68f2bbb3...`),
   `Disclosure: committed`, `Symbols: 8 (size only — committed)`, `Dates: 10 (size only —
   committed)`, `Nonce: committed — no nonce yet`.
4. Programmatically read `innerText` of both section bodies (`document.getElementById(...)`) to
   cross-check the rendered DOM verbatim (not just visually) — confirms the same 80/80/80/5622 and
   21-sealed-row figures, and confirms no `symbol`/`session_date`/`dataset_id` token appears for any
   sealed row (only for the 18 unrelated legacy rows, which is correct/expected).
5. Screenshotted the two sections (element-scoped crops of a full-page capture, per T-10 — two
   plain viewport screenshots taken after `scrollIntoView` came back blank, a known headless
   rendering quirk this era's memory already documents; the full-page capture rendered correctly
   and was cropped instead).

**Acceptance cross-check against `docs/goal.md` J-06's Acceptance clause:**
- "the tranche exists on disk meeting every §7.6 minimum" — 80 shard pool / 80 symbol-days
  rendered. (Arithmetic detail verified by dev/audit lanes; not re-derived here.)
- "at least the HMAC-assigned subset of tranche shards is `sealed`... no symbol/date served
  pre-exposure" — 21 sealed rows rendered, zero symbol/date leaked anywhere in either section's
  DOM.
- "the legacy 12 symbol-days remain `exploratory`" — confirmed (18/18 legacy rows `exploratory`,
  unchanged from prior iterations).
- "the readiness gate line still reads the ~150-symbol-day research gate as unmet" — confirmed
  (`referee_tick_gate_symbol_days: 150` vs `distinct_symbol_days: 12`; all three Pilot-Study Floors
  `floor_unmet`).
- Vault secret: only the sha256 commitment (`68f2bbb3...`) ever appeared in the DOM, the screenshot,
  or any log/file this dispatch touched — no raw secret bytes anywhere (checked the served JSON,
  the rendered DOM text, and both backend/frontend startup logs).

**A note on this iteration's own TC-1/TC-3 wording:** the iteration spec's TESTING REQUIREMENTS
text asserts `sealed_tranche.by_universe[...].shard_count == 21` on the readiness endpoint. The
dev handoff flagged this as an imprecision in the spec's own phrasing (not a defect): readiness
correctly serves **80** (the whole opaque pool, per the r5 anti-goal against a subtraction attack
from a complete per-shard list), and the vault endpoint/section correctly serves **21** (the sealed
subset). I verified both figures land on the sections the dev handoff said they would — readiness
shows 80, vault shows 21 — and treated that as the correct behavior, consistent with the same
dev-handoff note and with `docs/goal.md` IN SCOPE bullet 4's own framing ("21 sealed, 80 shard
pool").

---

## Golden Replay Script

A golden script already exists at
`runs/goal-session-rapid-microscope/journey-scripts/J-06.json` from an earlier iteration (asserts
only the generic, rig-independent "No integrity errors." text after expanding Microscope
Readiness). I left it **unmodified** this round: this iteration's actual J-06 acceptance evidence
(the 80-shard aggregate, the 21 sealed vault rows) only exists on the real `.data/datasets` store,
which the standard demo_runner replay rig (`:3301`/`:8301`, fixture-scoped, zero registered
universes) cannot reproduce — a script asserting "80" or "21" would hard-fail every future replay
against the standard rig through no fault of the product. Per the agent instructions' own
allowance ("best-effort... skip it, that journey just falls back to the LLM next time"), I skipped
writing a new golden for the real-store-specific evidence rather than mint one that is guaranteed
to false-fail.

---

## Skipped Tests

None. (J-01, J-02, J-03, J-04, J-05, J-08, J-10 were explicitly out of scope for this dispatch —
verified separately by deterministic replay, not by this browser-qa-agent run.)

---

## Environment

- **Frontend URL (regression rig, untouched by this dispatch):** http://localhost:3301
- **Frontend URL (J-06 real-store evidence, scoped/throwaway, torn down after capture):**
  http://localhost:3302 (backend http://localhost:8302, pointed at the real
  `apps/backend/.data/{datasets,bars}` store via config.py's own default — no env override needed)
- **Browser:** Chrome via MCP (headless, CDP `:9222`, pre-existing instance — not relaunched)
- **Test Date:** 2026-08-23
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-23-evidence/`
