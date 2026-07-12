# Goal Iteration 7 — Certification pass: all six journeys green; clean-scan GOAL_ACHIEVED attempt

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** yahoo_fetch
- **Iteration:** 7
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no (zero frontend/product source change this iteration)
- **Target journeys:** none new — J-01, J-02, J-03, J-04, J-05, J-06 are ALL already `passing`; this is a certification / clean-scan GOAL_ACHIEVED attempt, not feature work
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06 (full regression re-verify by deterministic replay — a GOAL_ACHIEVED attempt re-checks every Must-have)
- **Anti-goal reminders (verbatim from `docs/goal.md`; ALL rails there remain binding — only the ones this iteration most directly touches are restated):**
  - "no secrets in source" — the foundation invariant the deterministic `scan-report.md` enforces; the ONLY thing between this session and GOAL_ACHIEVED is a NON-product false positive on exactly this rail (see BACKGROUND).
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Yahoo default must not break the Alpaca path.** Making Yahoo the default bar vendor is additive: the Alpaca adapter, its credential gate, and its bar/tick/live paths stay byte-identical and selectable (opt-in). *(critical)*

## GOAL

Re-verify that all six Must-have journeys stay green with zero product source remaining, and clear the one non-product scan-hygiene false positive so the evaluator can return a **clean GOAL_ACHIEVED** — nothing user-facing changes.

## BACKGROUND

As of iter-6 every Must-have journey (J-01–J-06) is `passing`, every pipeline gate is green (coherence COHERENCE-PASS, closure CLOSURE-PASS, review PASS_WITH_NOTES, QA PASS, audit PASS_WITH_GAPS, ux-regression UX-REGRESSION-PASS), and `git diff -- apps/` is empty. Per my agent rule for zero remaining FAILING journeys, this is a **declare-victory spec — no product work is manufactured.** The single blocker the iter-6 evaluator identified is a deterministic `scan-report.md` `**Result:** CRITICAL` that resolves to a well-known, public AWS documentation example access-key placeholder (a fake credential that authenticates nothing, on every standard secret-scanner's built-in allowlist) quoted in the iter-6 spec's OWN NOTES prose while warning about this exact trip-wire — grep-confirmed **absent from `apps/`** and all product source. The full-diff scanner (`lib/scan_diff.py`) includes `docs/phases/*.md`, so a spec's prose tripped the product secret rail; `goal-gates.sh:126` greps the literal `**Result:** CRITICAL` line and blocks certification. This is an **orchestrator/human-owned scan-hygiene fix**, exactly like iter-5's `incredible_auto_dev/**` framework-fixture carve-out — not a product defect and not a REGRESSION (no real credential, no journey regressed). Depth is **lean** because there is zero product source to change and the full audit/coherence/ux/closure lanes already certified iter-6 (evaluator's explicit recommendation; no ESCALATE in the prior log; last coherence = COHERENCE-PASS, so no consolidation is owed).

**Applied lesson (iter-6, directly applicable to THIS spec):** a spec/docs file that quotes a live secret-scanner trigger token verbatim *becomes* the trip-wire it warns about. This spec therefore describes the blocker **semantically and reproduces no literal token** — it adds no new `**Result:** CRITICAL` to the evaluated diff.

## IN SCOPE

### Backend
- [ ] None. Zero backend/product source change — `git diff -- apps/` MUST stay empty.

### Frontend (if applicable)
- [ ] None. Zero frontend change. J-05's iter-6 browser evidence (UT-02 real candles + S/R lines + A/B/C zone table, UT-03 clean unoccluded "Yahoo Finance" provenance badge, UT-06 honest empty state) remains valid because no frontend byte changes; a UI regression is structurally impossible from an empty `apps/frontend/` diff.

### Orchestrator / human-owned (NOT product code — the developer agent is a no-op this iteration)
- [ ] Ensure the evaluated `snapshot..HEAD` `scan-report.md` contains no `**Result:** CRITICAL`. The current CRITICAL is a non-product false positive (a public AWS example placeholder quoted in the iter-6 spec's NOTES). Clear it by any one of the three documented, product-untouching remedies:
  1. **[cleanest]** Configure the diff-scan scope to exclude `docs/phases/*.md` iteration specs — they are pipeline inputs, not product source, so spec prose can never trip the product secret-scan; OR
  2. **[clean]** Add the well-known public AWS example placeholder to the scanner's allowlist (it is public and fake by design); OR
  3. **[least preferred]** Redact the literal token inside the iter-6 spec's NOTES — works, but it mutates a historical spec artifact and changes its spec-hash, which the evaluator tracks (iter-6 confirmed "all six current spec-hashes match the stored values exactly"), so prefer option 1 or 2.
- [ ] Confirm no vendored `incredible_auto_dev/**` judgment-fixture fake secrets re-enter the evaluated diff (iter-5 carry-forward — those 12 CRITICALs were already removed; keep them out).

### New user-facing capability
None — no product change.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None. Nav skeleton unchanged; `/structure` unchanged.

### Product surface delta
None. The product experience is byte-for-byte identical to iter-6; this iteration only re-verifies green state and clears a non-product scan false positive so certification can proceed.

### Blueprint conformance
No new surfaces. All journeys already live under their existing `/structure` (+ existing surfaces) homes in the Information Architecture. `blueprint.md` is unchanged this iteration (no edit, no re-approval).

### Data-contract additions
None. No new displayed value is introduced; every value continues to read from its already-registered canonical computing module + serving endpoint (blueprint Data Contract unchanged). `config_fingerprint` stays `4d665603569b9dbf`.

## OUT OF SCOPE

- Any product/feature code change (backend or frontend) — there is no failing/partial journey to build for, and manufacturing work would violate the zero-failing-journeys rule.
- Editing `research/levels.py` / `config.py` / `research/bars.py` / `research/bar_index.py` / the Alpaca adapter / any frozen-foundation module (all must stay byte-identical).
- The deferred cosmetic `SymbolSearch` auto-open polish (F1) — ux-regression PASS'd with the note in iter-6; not a J-05 blocker, not in scope here.
- Any enforced feed-scoped read of frozen `levels.py` — the standing single-feed-scoping assumption (audit B1) is unchanged and out of scope.
- The credentialed Era-5 tick-tape continuation, `/datasets` library UI, and every other roadmap item explicitly deferred by `docs/goal.md` Non-Goals.

## DEFINITION OF DONE

- [ ] All six journeys J-01, J-02, J-03, J-04, J-05, J-06 re-verified `passing` via deterministic replay (regression set stays green).
- [ ] `git diff <iter-6 snapshot>..HEAD -- apps/` is empty (zero product source change confirmed).
- [ ] `config_fingerprint` == `4d665603569b9dbf`; engine equivalence 22/22 pass.
- [ ] Full backend suite green (no new failures vs iter-6: 1207 collected / 1201 passed / 6 skipped / 0 failed).
- [ ] `scan-report.md` contains no `**Result:** CRITICAL` line (non-product false positive cleared by an orchestrator-owned remedy above).
- [ ] This iter-7 spec introduced no new secret-scanner trigger token into the evaluated diff (verified: it quotes no literal credential).
- [ ] Coherence stays COHERENCE-PASS (no product diff to violate).
- [ ] No anti-goal violation introduced (zero product diff ⇒ structurally none).
- [ ] Evaluator attempts GOAL_ACHIEVED; the two-key confirm spot-checks J-05's existing `UT-03-result.png` badge + the `UT-02` browser-results row (both already present and legible from iter-6).

## TESTING REQUIREMENTS

- **Browser:** none required to *change* any status — J-05's iter-6 Chrome-MCP evidence (UT-02 candles+levels+zones, UT-03 clean "Yahoo Finance" badge, UT-06 honest empty state) stays valid with an empty `apps/frontend/` diff. The GOAL_ACHIEVED two-key confirm re-reads those existing screenshots; no fresh capture is needed unless a frontend byte changes (it must not). If the pipeline does re-run the browser lane, it must confirm `/structure` still renders the same real candles + S/R lines + A/B/C zone table + legible provenance badge (regression check only).
- **Unit/integration:** full backend suite must stay green — deterministic replay of J-01–J-04/J-06 backend acceptance plus `config_fingerprint` recompute and engine-equivalence 22/22. The live Yahoo `integration`-marker fetch (network, keyless) is unchanged and optional.
- **Error cases:** none new — this iteration accepts no new inputs, so there is no new invalid-input surface to reject. The existing honest states (out-of-retention, unsupported timeframe, network failure, no-bars-for-symbol, immutability refusal) are unchanged and already covered.

## NOTES

- **This spec is deliberately token-free.** Honoring the iter-6 lesson ("describe scanner trigger tokens, never paste them verbatim into a file that lands in the evaluated diff"), the scan blocker is described semantically above; no literal credential string appears anywhere in this file, so iter-7 adds no new `**Result:** CRITICAL` to the diff. Spec-authors approaching any future GOAL_ACHIEVED attempt should do the same and, before scoring, confirm any residual scan CRITICAL resolves to a docs/framework placeholder vs. genuine product source.
- **The blocker is non-product and orchestrator-owned.** No REGRESSION verdict is warranted (the placeholder authenticates nothing, is absent from `apps/`, and no journey regressed) — it only blocks the deterministic achievement gate until the scan is clean.
- **Watch the evaluated diff composition.** Whether the scan is clean depends on which files land in iter-7's `snapshot..HEAD`. The orchestrator should confirm no `docs/phases/*.md` still inside that diff carries the placeholder token (the iter-6 spec's NOTES did) and that no vendored `incredible_auto_dev/**` fixture secrets re-enter it (iter-5 carry-forward).
- **Honesty rail.** If — contrary to expectation — the evaluator finds any journey regressed, or a clean scan cannot be obtained, it must return CONTINUE (never a false GOAL_ACHIEVED). The expected outcome, once the scan is clean, is a clean GOAL_ACHIEVED: J-05 already `passing`, every Must-have green, coherence/closure clean, `git diff -- apps/` empty.
- **No blueprint edit, no assumption-ledger entry.** No new displayed value and no new page ⇒ `blueprint.md` unchanged and no re-approval requested. This is routine scoping per the zero-failing-journeys rule, not a goal-interpretation ambiguity, so no `assumptions.md` entry is appended.
- **Standing assumptions unchanged** (already in the ledger): J-05's "honestly segregated from Alpaca `sip`" is met by single-feed scoping (all stored series are `feed="yahoo"`), not by an enforced feed-scoped read of frozen `levels.py`; the `4h` value stays derived-from-`1h` single-owner; the store-first SQLite index owns nothing.
