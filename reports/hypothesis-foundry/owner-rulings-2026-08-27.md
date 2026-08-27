# Owner rulings — Hypothesis Foundry era closure

**Ruled at:** 2026-08-27T19:42:44Z
**Session:** `hypothesis-foundry` · **Branch:** `goal/hypothesis-foundry`
**Authoritative committed epoch:** `epoch:afd19e9c11a6534f`

This file is the owner's durable record of the two dispositions written onto
`runs/goal-session-hypothesis-foundry/state/journey-history.json`, plus the residuals the owner
directed be carried into the closure record rather than repaired. It adds no scientific rule,
changes no source disposition, manifest, threshold, direction, family identity, Scout rule or
evidence-class rule, and touches no freeze-set member.

---

## Ruling 1 — discarded precommit epoch

- **Finding:** `goal-hypothesis-foundry-iter-5`
- **Anti-goal:** "No second real generation epoch."
- **Severity:** minor · **`resolved`: false (unchanged)**
- **Disposition kind:** `deferred_named_revision` · **`blocks_current_era`: false**

The discarded first precommit epoch-generation attempt is **ACKNOWLEDGED as a real historical
generator event**, and the literal uniqueness wording of §8.1 was therefore breached. The finding is
**not** marked resolved and history is **not** rewritten. It does not block closure of this era
because:

- it never crossed the Git-visible committed freeze barrier;
- nothing was committed under that discarded epoch id;
- no Foundry trial ledger row was written under it;
- no candidate outcome was read under it;
- no protected evidence was consumed;
- the unsupported `direction_derivation` was caught by the required independent source audit
  *before* the authoritative committed epoch;
- the regeneration/deletion bypass mechanism has since been mechanically closed;
- the sole authoritative committed epoch remains `epoch:afd19e9c11a6534f`.

> **Ruling (verbatim, as recorded in the ledger).** Owner ruling 2026-08-27: the discarded
> precommit epoch-id remains a disclosed literal uniqueness violation, not a silently erased event.
> Because it never crossed the committed pre-outcome barrier, never produced a trial row, never read
> a candidate outcome and consumed no protected evidence, it does not invalidate the authoritative
> committed epoch or block closure of this era. The recurrence bypass is already mechanically closed.
> Future Foundry methodology must define authoritative epoch identity explicitly at the committed
> freeze barrier and preserve this discarded attempt in the historical record.

**Carried to:** future named revision — *Foundry epoch identity and precommit-generation semantics*.

The discarded id is **not** claimed to have never existed.

---

## Ruling 2 — GET-side lock-file write

- **Finding:** `goal-hypothesis-foundry-iter-6`
- **Anti-goal:** "Persistence stays scoped … every page-load GET is read-only …"
- **Severity:** minor · **`resolved`: false (unchanged)**
- **Disposition kind:** `deferred_named_revision` · **`blocks_current_era`: false**

The seal is **preserved**: `apps/backend/app/research/foundry_runner.py` is **not** edited in this
era, and no second computation/status implementation is added to route around it. The filesystem
write of the gitignored coordination lock file on GET is accepted as a **disclosed MINOR literal
read-only violation for this era only**. The scientific/persistence intent remains satisfied because
the GET records no market data, computes/evaluates no candidate, triggers no exhaust run, writes no
Foundry trial row, changes no trial-ledger chain head, consumes no protected evidence, and touches
only the unprotected gitignored coordination lock file.

> **Ruling (verbatim, as recorded in the ledger).** Owner ruling 2026-08-27: preserve the first-read
> seal rather than edit the sealed runner to remove the GET-side lock probe. The lock-file
> creation/truncation is a real, disclosed minor violation of the literal "read-only" wording, but it
> mutates no scientific state, market data, candidate result, trial ledger or protected evidence. It
> is non-blocking for this completed Foundry epoch and must be corrected in a future named Foundry
> revision before this architecture is reused.

**Carried to:** future named revision — *non-mutating Foundry read-surface / single-flight status probe*.

---

## Non-blocking closure residuals — carried, NOT repaired

These are carried into the closure record as OPEN NON-BLOCKING residuals. None was repaired this
era; none is claimed removed; no historical artifact was rewritten to look cleaner.

1. **Duplicate `frozen_ready_total` computation inside the sealed CLI.** The ledger entry
   (`goal-hypothesis-foundry-iter-6`, "Single source of truth") was closed `resolved: true` in
   iter-7 against its own recorded close condition — one canonical non-sealed owner
   (`micro_routes.compute_frozen_ready_total`) plus an equivalence-pinning test. The **residual**
   is that `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225` permanently retains its
   own inline `sum(len(fm.get('variants', [])) for fm in families)` expression, because that file is
   a freeze-set member. It is **not** removed and **cannot** be removed without breaking the seal.
   The freeze-set is deliberately **not** weakened to reach it.
2. **Defective iter-8 demo walkthrough script.** `reports/demo/goal-hypothesis-foundry-iter-8/` is
   `RECORDED_WITH_NOTES` with all click steps failing; the script targets
   `desk-section-expand-*` testids that do not exist in `apps/frontend/app/desk/page.tsx`, so every
   frame captured the top of `/desk`. Journey evidence itself is unaffected (golden replays and
   `demo_runner --mode verify` pass).
3. **Blank cited PNG where alternate genuine evidence exists.**
   `reports/qa/goal-hypothesis-foundry-iter-8-evidence/final-summary-section.png` is uniformly blank;
   the same claim is carried by non-blank `J-08-verify.png` / `UT-02-result.png`. The blank artifact
   is retained, not replaced.
4. **Stale/incorrect modified-file claims in the iter-8 QA report.** Its Code Review Notes name
   `foundry_runner.py` (sealed, byte-identical) and `lib/api.ts` (never touched) as "modified"; both
   are wrong and appear in no diff. The report is retained unedited.
5. **Other already-recorded non-blocking audit gaps**, including the missing environment metadata on
   the epoch-open row and the non-byte-exact source excerpts (0 of 11), remain as recorded.

---

## Scope of this ruling

Not changed by this ruling: `docs/goal.md`; any freeze-set member; any scientific rule, source
disposition, manifest, candidate spec, threshold, direction, family identity, Scout rule or
evidence-class rule. No new market outcome was read, no epoch was generated, the first-read seal was
not broken, and no withheld/sealed/Vault/OOS evidence was touched.
