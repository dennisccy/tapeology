# goal-structure_ui-iter-2 Audit Report

**Date:** 2026-07-07
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

The phase goal is fully achieved and verified at the source level, not from handoff summaries. J-02's Registry section renders both registered strategies plus the founding champion with every field read verbatim from `GET /research/strategies`, cross-checked byte-for-byte against `GET /research/profiles`; the backend is genuinely untouched (empty `git diff -- apps/backend/`); and J-01's levels-but-no-candles honest state is independently re-verified live (UT-06 computed `z-index:10` via `getComputedStyle`), closing the exact process gap iter-1 left open. No CRITICAL or IMPORTANT issue was found, so no fix was applied; the only open items are cosmetic/intentional GAP-and-OBSERVATION notes documented below.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no change needed): zero backend diff confirmed, single-source-of-truth structural**
Verified directly, not from the handoff: `git diff -- apps/backend/` is empty and `git diff --stat` lists only `apps/frontend/{app/structure/page.tsx, lib/api.ts, lib/types.ts}` (plus the framework `trace.jsonl`). Both champion-serving endpoints call the identical store method: `strategies.py:37` and `profiles.py:58` each return `store.get_champion_pointer()`, whose implementation (`store.py:1387-1403`) returns `{"strategy_id", "profile"}` from a single SQLite row — the two endpoints cannot diverge by construction. `set_champion_pointer` (`store.py:1407`) is not called anywhere in this diff (its only caller is `pnl_scan.py`, unchanged). The "no new backend computation/endpoint" and "champion moved never" anti-goals hold. No action.

### Frontend Findings

**F1 — GAP (observation): `/structure` header subtitle does not preview the new Registry section**
`page.tsx:466-473` — the `<h1>` subtitle and `structure-framing` line still describe only the J-01 Levels & Zones capability and were not updated to mention the Registry/strategy-registry/champion content added this iteration. The ux-regression reviewer flagged this against the codebase's own precedent (`/performance/page.tsx`'s subtitle summarizes every section of that page) and noted it matters slightly more here because, on the keyless fixture, the Registry is the *only* content populated by default. This does **not** compromise the goal: the section renders on mount and is 0-additional-click discoverable (confirmed live by UT-01/UT-02/UT-14), so the capability is genuinely reachable. Non-blocking cosmetic copy item; the spec did not require a subtitle change. Deferred to a future `/structure`-touching iteration (concrete recommendation already recorded in the ux-regression report). Not fixed — fixing GAP-level items is scope creep per the auditor mandate.

**F2 — OBSERVATION (no change needed): unreachable `structure-champion-crosscheck-mismatch` branch**
`page.tsx:454-457` — the champion cross-check ternary has a `mismatch` branch that is structurally unreachable in the current architecture (both endpoints read the one `get_champion_pointer()` source, so they cannot disagree). Self-disclosed by the developer and noted by the reviewer. It is three lines of honest defensive code guarding the critical single-source-of-truth anti-goal; if a real violation were ever introduced it would surface a visible warning rather than silently show a mismatched value. The badge itself always renders `registry.champion.*` (the strategies-endpoint value), never a "resolved" pick. Cheap, honest, keep as-is.

**F3 — OBSERVATION (no change needed): exit-precedence caption names `reward_target` on v1's card**
`page.tsx:211-212, 309` — the static `EXIT_PRECEDENCE_CAPTION` ("Exit precedence: r_stop → reward_target → state_flip → horizon …") renders on both cards, including v1's, even though v1 genuinely has no `reward_target` row. This is the exact canonical phrase from `docs/goal.md` and the phase spec, explicitly framed (in the code comment and the plan's "Assumption flagged for the developer") as prose describing the runner's general exit-check order, not a per-strategy field list. The honesty-critical part — the actual data rows — is faithful: v1's card omits the `reward_target` row because the payload omits the key (`config.py:1382-1391` has no `reward_target` for v1, and `page.tsx:275` guards it). No fabricated value is shown; the caption is spec-sourced framing. Not a defect.

**F4 — OBSERVATION (no change needed): v1's `r_stop.spread_multiple`/`floor` (and `entries.setups`) modeled but not rendered**
`config.py:1383-1387` serves v1's `r_stop` with `spread_multiple`/`floor`, and richer `entries` detail, which the cards do not display. All four planning sources (`docs/goal.md`, phase spec "New information displayed", the DoD, and the plan) independently enumerate the same minimal field set (entry rule; r_stop/reward_target/state_flip/horizon rule names; structure_tape's three class maps). Rendering exactly that set — and no more — is the correct scope, and mirrors the accepted iter-1 precedent of typing-but-not-displaying `SrLevel.touch_count`/`strength`. Honest omission, not a gap.

### Test Findings

**T1 — OBSERVATION (no change needed): UT-13 (loading-skeleton transient) SKIPPED**
The Chrome MCP `use_browser` tool exposes no network-throttling action, so the sub-second loading skeleton could not be reproduced on localhost. The test plan itself states a missed brief flash "is not a defect" (only a permanently-stuck skeleton or a crash would be), and neither was observed across ~15 page loads. Acceptable P3 skip; does not affect the verdict. The `structure-registry-loading` path is present and correct in code (`page.tsx:588-589`).

**T2 — OBSERVATION (no change needed): UT-08 Levels-&-Zones "idle vs degraded" nuance, honestly disclosed**
UT-08's plan text expected the Levels & Zones panel to show a "degraded" message when the backend is down, but it showed its normal *idle* message — because that section only fetches on Load click (never on mount, confirmed by UT-02), and the test never clicked Load, so no request was made to fail. Showing idle for a never-attempted fetch is the correct honest behavior (no fabricated success, no false failure claim), and the section the test actually targets (the Registry honest-state) behaved exactly as specified. The browser-qa-agent flagged this transparently rather than papering over it — good practice. Separately noted (also non-blocking): the reused `champion-*` testid strings are safe because `/structure` and `/performance` never render together (UT-12 confirmed no interference); a future test-hygiene item is to scope `data-testid` queries per-container rather than globally.

---

## 3. Domain Assessment

The core discipline this interlude protects is "the Structure UI recomputes nothing" and "champion read verbatim, moved never" — and the implementation honors both, verified by reading the code rather than trusting the handoff:

- **Verbatim rendering, no client computation.** Every strategy field is `String(...)`-rendered directly off the payload (`page.tsx:265-306`); the three class maps render via `Object.entries(map)` in the payload's own key order, never re-sorted or assumed to be `{A,B,C}` (`page.tsx:232`); `championsMatch` (`page.tsx:340-345`) is a pure `===` used only to select narration copy, never to pick a champion value. There is no aggregation, grading, PnL math, or champion resolution anywhere in the diff.
- **Byte-for-byte shape parity.** The frontend's render path (`exits.r_stop.rule`, `exits.reward_target.rule`, `exits.horizon_seconds`, `exits.state_flip.rule`, `exits.dataset_end.rule`, `size_multiple_by_class`) maps exactly onto `config.py:strategy_definition` (`:1334-1365` for structure_tape, `:1368-1398` for v1). Crucially, every field v1 lacks (`reward_target`, `stop_bps_by_class`, `r_multiple_by_class`, `size_multiple_by_class`) is guarded by a truthiness check before render (`page.tsx:275, 311, 318, 325`), so v1's card shows honest omissions — there is no path that renders the literal string "undefined", which was the single highest-risk failure mode for this kind of verbatim-mirror UI.
- **Single source of truth is structural, not merely asserted.** Both endpoints resolve the champion through one store method returning one shape; the type layer enforces it (`StrategiesPayload.champion = ProfilesPayload["champion"]`, `types.ts:1078`). The browser QA independently curl-verified both endpoints return `{"strategy_id":"v1","profile":"default"}` byte-for-byte (UT-05).
- **J-01 closure is genuine.** The iteration existed to convert iter-1's auditor-in-tree fix into an independently re-verified CLOSURE. UT-06 did exactly that — live `getComputedStyle` proving the empty-state hint computes `z-index:10` above the `lightweight-charts` canvases (`z-index:1/2`), on the current tree, independent of any code read. The five iteration records (review, QA, ui-test-results, ux-regression, status.json) are mutually consistent, unlike iter-1's CLOSURE-FAIL.
- **Honest failure handling.** Backend-down yields the distinct `structure-registry-unavailable` amber panel with no fabricated cards and no hardcoded `v1`/`default` fallback (`page.tsx:590-594`, UT-08); the Levels & Zones section retains its four pre-existing distinct honest states, byte-unchanged.

The domain logic is correct, minimal, and local-first. Nothing in the diff introduces a second computation of any contract value.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | None. No CRITICAL or IMPORTANT issue was found; all findings are GAP/OBSERVATION-level and fixing them would be scope creep. |

---

## 5. Recommended Next Step

**Proceed.** J-02 is built and verified verbatim-parity with its backend source; J-01 is independently re-verified and closed; J-04's regression sentinel is green (`config_fingerprint 4d665603569b9dbf`, backend 1146 passed/1 skipped, 5-link nav intact). Advance to J-03 (`structure_tape`-vs-`v1` on-screen comparison) in iter-3, per the goal's J-01→J-02→J-03 order and the "never bundle two risky journeys" rule.

Carry forward one non-blocking polish item for whichever iteration next touches `/structure`: update the page's header subtitle (`page.tsx:466-473`) to preview the Registry section, matching `/performance`'s own subtitle precedent (finding F1). This is cosmetic and does not gate the phase.
