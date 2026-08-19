# Iteration State — rapid-microscope

**After iteration:** 14 · **Date:** 2026-08-19 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01..J-05, J-07) · 3 partial (J-06 J-08 J-10) · 1 failing (J-09) — 10 total. J-07 cut
for time twice running (deferred, not tested) — cannot count toward finishing.

## Active blockers

- **none owner-owned** — all coding work; r6/r7/r8 settled every ruling.
- dev · Microscope Readiness drops two fields its endpoint serves (`sealed_tranche`,
  `joinable_corpus.withheld_excluded`): says "Distinct datasets 2" while 3 were withheld.
  `types.ts:2514` + `MicroReadinessSection`. COHERENCE-WARN + audit F3. Render AGGREGATE ONLY —
  a per-shard list reopens the subtraction attack.
- dev · NEW, evaluator-found, missed by all five lanes: `<details>`/`<pre>` inside a `<p>` at
  `apps/frontend/app/desk/page.tsx:6461-6472` — invalid HTML, 5 console errors on expand; the only
  such site in the 12k-line page.
- dev · J-07 "Graduation" needs a genuine re-check (2nd consecutive DEFERRED-BUDGET).
- dev · 3 MINORs: Scout never renders `family_root_id`; Walk-Forward's empty state wrongly reads
  "No candidates ledgered."; Vault's error state drops its `validation-vault-section` testid.
- process · QA graded TC-13 PASS when the results file records it not run (2nd occurrence).
  harness · `state/golden-gaps` auto-deleted a 4th time (framework gap, not product).

## Last 2 verdicts

- iter 14: ESCALATE — J-08 panels shipped and verified on screen (vault opacity holds at BOTH
  stages); iter 15 adds `desk_vault`/`desk_micro_readiness` MCP proxies AND renders the withheld
  disclosure — two opaque-pool-critical surfaces at once, so the auditor is mandatory.
- iter 13: ESCALATE — J-08 was next and only the verdict line binds full depth.

## Do not redo

- Scout / Walk-Forward / Validation Vault `/desk` sections — BUILT, browser-verified (`page.tsx:6123-6763`, mounted `:12034-12084`).
- Vault opacity through the UI — PROVEN at both shard + universe stages (`AUDIT-vault-fixture-both-stages.png`); only re-sweep NEW surfaces.
- Poll-leak + Scout duplicate-key — FIXED in-lane (`microComputePollStopRef` `:9711`; key `:6232`).
- Frozen rails RE-VERIFIED: fingerprint `08e471b10130e1e2`, 6/6 `referee_*.py` byte-identical since era open, `EXPECTED_TOOLS` 22, engine/config + real `.data` store untouched.
- J-02–J-05 evidence-makeup debt CLOSED; Vault stays READ-ONLY; J-06 steps 4-5 and the r8 identity-commitment revision stay shut.
