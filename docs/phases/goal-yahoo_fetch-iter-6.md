# Goal Iteration 6 — J-05 closure remediation: land the browser evidence + clean "Yahoo Finance" badge (no source change)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** yahoo_fetch
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-06
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **The UI fetch stores bars only.** The `/structure` fetch control performs an explicit bar fetch/store; it computes no levels, PnL, or champion, and it never promotes. *(critical)*
  - **No fabricated bars, ever.** A symbol/window/timeframe Yahoo cannot serve (out of retention, unsupported interval, network failure) returns an explicit neutral error; the fetch never synthesizes, forward-fills across gaps, or pads a partial window to force a green journey. *(critical)*
  - **Yahoo default must not break the Alpaca path.** Making Yahoo the default bar vendor is additive: the Alpaca adapter, its credential gate, and its bar/tick/live paths stay byte-identical and selectable (opt-in). *(critical)*
  - **No vocabulary drift.** No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.

## GOAL

Flip J-05 from `partial` to `passing` by landing its missing browser evidence — a clean,
unoccluded "Yahoo Finance" provenance-badge screenshot, a browser-captured honest empty state,
and the three absent UI-visibility artifacts — so phase-closure certifies CLOSURE-PASS, **without
changing one byte of product source.**

## BACKGROUND

J-05's feature is genuinely built and mostly evidenced: iter-5 screenshot-captured the `/structure`
fetch control drawing real AAPL candles + S/R level lines + A/B/C confluence-zone table store-first
(TC-05..08), coherence was COHERENCE-PASS, review/QA/audit passed, and every frozen foundation is
byte-identical. iter-5 did **not** close for three evidence/plumbing reasons only: (1) phase-closure
= **CLOSURE-FAIL** because `reports/phase-goal-yahoo_fetch-iter-5-ui-test-results.md` is entirely
absent and the `-ui-test-plan.md` / `-what-to-click.md` are SKIPPED stubs (CLI exit 70 — the
session's recurring quota-throttle signal-kill; `browser-qa-phase.sh` deliberately writes no real
stub when SIGKILLed); (2) the **defining** "Yahoo Finance" badge is DOM/unit/source-verified but
**occluded** in every post-fetch screenshot by the `SymbolSearch` dropdown (defect F1); (3) the
honest empty state is unit-covered but not browser-run (TC-11 absent). This iteration is therefore
a **closure/evidence remediation, not feature work** — exactly what the iter-5 evaluator recommended.

**Depth = full (mandatory).** The lanes that must certify J-05 — **phase-closure-auditor** and
**ux-regression-reviewer** — run only in the full 11-step pipeline, never in the lean cycle. Since
CLOSURE-FAIL is precisely what blocks J-05, full depth is required to re-run and pass those lanes.
Prior depth was full and the iter-5 evaluator recommended full; no ESCALATE was emitted.

**Target selection (priority rubric):** no journey regressed (rule 1 clear); iter-5 coherence was
COHERENCE-PASS so no consolidation is mandated (rule 2 clear); J-05 is the **only** non-passing
journey and closing it unblocks the GOAL_ACHIEVED attempt (rule 3). Single target, smallest possible
change set (rules 4–5).

**Lessons applied (this session's ledger):**
- *iter-5:* a UI journey can pass every functional check yet fail closure on artifact plumbing —
  `browser-qa-phase.sh` writes no stub when signal-killed, and a badge verified in the DOM is **not**
  a badge captured in a screenshot. Both are the exact gaps this iteration closes.
- *iter-2 / iter-0:* the `/structure` browser lane MUST have `:3301` + `:8301` reachable **and**
  Chrome MCP available, or J-05 cannot be evidenced at all — a "passing" without a screenshot is
  unevidenced (a HARD PRE-FLIGHT below).
- *iter-4:* browser-verify **keyless on a single-feed (yahoo-only) pre-seeded fixture** so no
  cross-feed pooling can occur in the accepted path — frozen `levels.py` selects a symbol's series
  feed-blind, so the single-feed scoping is what keeps the "never pooled across feeds" rail satisfied.
- *iter-3:* the route contract is "repeat window = **200**, served store-first (no second fetch)",
  NOT 409 — any browser re-fetch step must expect the 200 store-first serve.

## IN SCOPE

### Backend
- [ ] **None.** No backend source change. `config.py` (fingerprint `4d665603569b9dbf`), `research/levels.py`, `research/backtests.py`, `research/strategies.py`, `research/bars.py` (JSON `BarStore`), `research/bar_index.py`, `providers/adapters/` (Alpaca + Yahoo), the tape engine, `research/taxonomy.py`, and `mcp/` all stay byte-identical.

### Frontend
- [ ] **None.** No product source change. The fetch control, `FeedBasisBadge`, and honest empty state already ship and render correctly. The F1 `SymbolSearch` auto-open fix is **explicitly deferred** (see OUT OF SCOPE) — the badge is captured cleanly by dismissing the dropdown, not by editing a shared component on the certification pass.

### Closure & evidence remediation (the actual work — no product source change)
- [ ] Bring up `:3301` (frontend) + `:8301` (backend) + Chrome MCP and **actually run the browser lane** end-to-end against the real `/structure` page (HARD PRE-FLIGHT — see NOTES).
- [ ] Pre-seed and **index** a single-feed (yahoo-only) committed fixture series so the fetch click serves **store-first** (200, no network) — recorded through the store-first POST path or a one-off `reindex()` so the "instant serve" triggers (iter-3/iter-4 carry-forward).
- [ ] Re-capture the fetch flow: click **Fetch from Yahoo Finance** → real candles + real level lines + A/B/C zone table, read verbatim from `/research/bars` + `/research/levels`.
- [ ] **Capture a CLEAN, unoccluded "Yahoo Finance" badge screenshot:** dismiss the `SymbolSearch` dropdown with an outside click (the auditor confirms it self-dismisses; `SymbolSearch.tsx:71-77`) **before** the shot, so the taxonomy-sourced badge label is fully legible.
- [ ] **Record TC-11 in the browser:** a symbol with no stored bars → the distinct honest empty state, screenshot-captured (currently unit-only).
- [ ] Regenerate the three UI-visibility artifacts with **real content** (not SKIPPED stubs): `reports/phase-goal-yahoo_fetch-iter-6-ui-test-plan.md`, `-what-to-click.md` (via `ui-test-design-phase.sh`), and `-ui-test-results.md` (via `browser-qa-phase.sh`).
- [ ] Re-run **phase-closure-auditor** and **ux-regression-reviewer** to certify CLOSURE-PASS.

### New user-facing capability
None. The fetch-from-the-app capability already ships; this iteration makes it **certifiably
evidenced** end-to-end in the browser.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None. The fetch control, provenance badge, and empty state already render; only the **evidence
capture** of the existing surfaces changes.

### Product surface delta
None functionally. The era's headline "fetch-from-the-app" moment moves from built-but-unevidenced
to browser-certified.

### Blueprint conformance
No new surfaces. The `/structure` fetch control + "Yahoo Finance" provenance badge already live under
their registered Information-Architecture home (blueprint IA table row "J-05 → `/structure`", Structure
nav section). Nav skeleton unchanged. **Blueprint unchanged this iteration** (no additive edit needed).

### Data-contract additions
**None.** No new displayed value is introduced. The "Yahoo Finance" label stays owned by
`research/taxonomy.py` `FEED_BASIS_LABELS` (served by `GET /research/taxonomy`) and the badge reads
it verbatim — the already-registered Data-Contract entry. No second computation or endpoint for any
value.

## OUT OF SCOPE

- **The F1 `SymbolSearch` auto-open source fix** (skipping `setOpen(true)` on a programmatic `value`
  set). Deferred — `SymbolSearch.tsx` is a shared component used by `TopBar.tsx` (every page),
  `StudyCreateForm.tsx`, and `/structure` (twice); changing its interaction behaviour on the
  certification iteration risks regressing existing surfaces (J-06) for cosmetic gain, and the badge
  is fully capturable via the confirmed outside-click self-dismiss. If a future product-quality
  iteration wants to fix the auto-open wart, it does so as its own guarded, ux-regression-verified pass.
- **Any new feature work.** Every Must-have feature (J-01–J-06) is already built.
- **Any change to frozen foundations** — `config.py`, `research/levels.py`, `research/backtests.py`,
  `research/strategies.py`, the tape engine, the JSON `BarStore`, `research/bar_index.py`, the Alpaca
  adapter, and `mcp/` stay byte-identical.
- **A mixed-feed segregation guard** (feed-scoped levels read) — deferred; the browser test runs
  keyless on a yahoo-only single-feed fixture so no cross-feed pooling occurs (iter-4 lesson). If ever
  built it is a versioned path BESIDE frozen `levels.py`, never an edit to it.
- **Resolving the `incredible_auto_dev/**` framework-vendoring churn** — environment/human/orchestrator-owned
  (see NOTES), NOT product source and NOT the developer's scope.

## DEFINITION OF DONE

- [ ] J-05 passes via browser-qa-agent with services reachable (`:3301` + `:8301` + Chrome MCP), evidenced by committed screenshots under `reports/qa/goal-yahoo_fetch-iter-6-evidence/`.
- [ ] A **clean, unoccluded** "Yahoo Finance" provenance badge is captured in a committed screenshot (dropdown dismissed before capture); the badge text derives from the taxonomy label, not a hardcoded literal.
- [ ] The honest empty state (a symbol with no stored bars) is browser-captured (TC-11) as a distinct state.
- [ ] All six UI-visibility artifacts exist with REAL content (no SKIPPED stubs): `reports/phase-goal-yahoo_fetch-iter-6-ui-test-plan.md`, `-what-to-click.md`, `-ui-test-results.md`, plus the evidence screenshots (fetch control, candles, levels/zones, clean badge, empty state).
- [ ] phase-closure = **CLOSURE-PASS**; ux-regression re-run clean.
- [ ] Coherence stays **COHERENCE-PASS**; no anti-goal violation introduced.
- [ ] Required-still-passing J-01, J-02, J-03, J-04, J-06 remain green (deterministic replay + frozen-file byte-identity).
- [ ] **Zero product source change:** `git diff <snapshot>..HEAD -- apps/` is empty over the frozen set; `config_fingerprint` stays `4d665603569b9dbf`; engine equivalence 22/22; full backend suite green (≥1207 passed / 0 failed / 6 skipped).
- [ ] Dev handoff written at `docs/handoffs/goal-yahoo_fetch-iter-6-dev.md`.

## TESTING REQUIREMENTS

- **Browser (J-05 — the load-bearing lane this iteration):** with `:3301` + `:8301` + Chrome MCP up,
  drive the `/structure` fetch control against a pre-seeded, **indexed**, yahoo-only fixture:
  - Fetch control renders (symbol via `SymbolSearch` + timeframe + date range + "Fetch from Yahoo Finance" button).
  - Click → store-first **200** serve (no network); chart draws real candles + level lines + A/B/C zone table read verbatim from `/research/bars` + `/research/levels`.
  - **Clean badge:** dismiss the `SymbolSearch` dropdown (outside click), then capture the "Yahoo Finance" badge unoccluded and legible.
  - **TC-11 empty state:** a symbol with no stored bars → distinct honest empty state, screenshot-captured.
- **Unit/integration:** no new code paths (zero source change). Re-run the full backend suite; it must
  stay green (baseline 1207 passed / 0 failed / 6 skipped), engine equivalence 22/22, `config_fingerprint`
  `4d665603569b9dbf`. The honest empty state remains unit-covered (keep green) — the browser TC-11 adds
  the visual evidence, it does not replace the unit test.
- **Error cases:** the `no_bar_series_for_symbol` empty state must render as a distinct honest state
  (browser + unit). Out-of-retention / unsupported-timeframe / network-failure taxonomy is J-02's,
  already covered — not re-exercised here beyond non-regression.
- **Regression (Required-still-passing):** J-01, J-02, J-03, J-04, J-06 re-verified by deterministic
  replay + `git diff <snapshot>..HEAD` byte-identity over the full frozen set. This is the pre-certification
  full regression of every passing journey (per the decomposer's periodic-widen rule) and refreshes the
  golden scripts for a clean GOAL_ACHIEVED attempt.

## NOTES

**HARD PRE-FLIGHTS the orchestrator MUST satisfy before this run (both are the recurring blockers of this session):**

1. **Services + Chrome MCP reachable.** Provision and verify `:3301` (frontend) + `:8301` (backend)
   reachable AND Chrome MCP available BEFORE the browser lane runs. The lane silently no-op'd in
   iters 0/2/3 (curl exit 7) and was signal-killed in iter-5 (quota-throttle). If the render cannot
   be captured, J-05 must be scored `unknown`/`partial` — **never `passing`** (iter-0 lesson: a
   "passing" without a screenshot is unevidenced for a UI journey). Watch the session's quota-throttle
   history (a subagent ballooning from minutes to hours with few tool calls) — if it recurs, report and
   resume after the interactive allowance resets, or run headless, rather than raising timeouts.

2. **Keep the `incredible_auto_dev/**` framework churn OUT of the evaluated `snapshot..HEAD`**
   (environment/human/orchestrator-owned — NOT product code, NOT in the developer's scope). The
   deterministic GOAL_ACHIEVED gate (`goal-gates.sh:126`) greps the **full-diff** `scan-report.md` for
   `^\*\*Result:\*\* CRITICAL`, and the vendored `incredible_auto_dev/tests/judgment/**` judgment
   fixtures contain **deliberately-planted fake secrets** (e.g. AWS's example key `AKIAIOSFODNN7EXAMPLE`)
   that trip that line. In iter-5 this alone would have demoted a GOAL_ACHIEVED → CONTINUE regardless of
   J-05. Land any framework subtree sync OUTSIDE a goal-iteration window so the product-scoped scan is
   CLEAN before certification. **This is the single largest risk to a clean GOAL_ACHIEVED and it is not
   solvable inside the product diff** — flagging for the evaluator/orchestrator, not the developer.

**Why zero source change is the right scope:** J-05's badge is already correct in the DOM and reads
the taxonomy label verbatim (coherence-verified, `FeedBasisBadge.tsx:60`); the only gap is that the
proof screenshot is cluttered by the F1 dropdown. That is an evidence-capture problem, fully solved by
dismissing the dropdown before the shot — no shared-component behaviour change belongs on the
certification iteration. This keeps the diff empty and makes the closure trivially auditable.

**Assumption ledger:** no new entry — this iteration builds on the iter-5 evaluator's already-logged
reading ("the defining provenance badge must be cleanly visible in a real screenshot") and makes only
routine scoping picks, not a new goal interpretation.

**Blueprint:** unchanged (no new value, no new surface). No re-approval requested.

**On GOAL_ACHIEVED:** once (1) the browser lane runs with services up, (2) the clean badge + TC-11 land,
(3) the three UI-visibility artifacts carry real content, and closure flips to CLOSURE-PASS — and the
framework-churn pre-flight holds — J-05 → `passing` and every Must-have is green with coherence clean,
so the goal-evaluator can consider GOAL_ACHIEVED. The two-key confirm will spot-check J-05's
browser-results row + the clean badge screenshot, so both must be present and legible.
