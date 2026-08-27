# Phase goal-hypothesis-foundry-iter-8 — User-Visible Changes

**Phase:** goal-hypothesis-foundry-iter-8
**Date:** 2026-08-27
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see, in one place, the real Hypothesis Foundry epoch's complete final state
  without expanding any of the six existing subsections individually: navigate to
  `http://localhost:3301/desk`, click "Hypothesis Foundry" to expand the panel, then click "Final
  Summary" to expand the new subsection (`data-testid="foundry-final-summary"`).
- Users can now read source counts broken out by outcome bucket (e.g. `BLOCKED_DIRECTION`,
  `ALIASED_PROXY_ONLY`, `EXCLUDED_GATE_CLOSED`, etc.) at the top of the Final Summary subsection,
  with the count for each disposition shown next to its label.
- Users can now see, in one place, the family count, variant count, frozen-ready total, evidence
  class, protected/withheld/sealed read count, freeze-integrity verdict, and epoch status for the
  real epoch — seven values that previously only existed scattered across the six separate
  subsections (or not at all).
- Users can now expand a per-source "Canonical provenance" `<details>` disclosure for any of the
  11 real source records, revealing the mechanism statement, audit note, direction derivation,
  comparator derivation, threshold provenance, superseded fields, alternatives, source hash, and
  every quoted span (exact text + location) that justified how that source was disposed. This
  detail previously existed only in the underlying `docs/hypothesis-foundry/source-registry.json`
  file — nowhere in the app.
- When the real epoch has zero diagnostic survivors (the current state), users see an explicit
  plain-English sentence saying so, rather than a bare "0" that could be mistaken for "not loaded
  yet."
- When the exhaust run has completed, users see an explicit sentence confirming exhaust is
  complete (or, if not, an explicit "not yet complete" sentence).

---

## What Changed in the Visible UI

- A new "Final Summary" collapsible subsection was added to the `/desk` → Hypothesis Foundry
  panel, positioned directly below the panel's era-identity/era-open-baseline header and above the
  six existing subsections (Sources/Compiler, Interpreter Fixtures, Freeze/Integrity, Hermetic
  Oracles, Epoch/Manifest, Runner/Checkpoint). It renders as its own collapsible block, matching
  the visual style (slate/emerald palette, monospace numeric values) of the sibling subsections.
- The panel now shows disposition-count tallies, family/variant/frozen-ready counts, evidence
  class, protected-read count, freeze-integrity verdict, and epoch status — all new visible text
  that did not exist anywhere on the page before.
- Every source-detail `<details>` disclosure inside the new subsection now exposes fields
  (`mechanism_statement`, `audit_note`, `direction_derivation`, `comparator_derivation`,
  `threshold_provenance`, `superseded_fields`, `alternatives`, `source_hash`, `quoted_spans`) that
  were not previously rendered anywhere in the app for the real epoch's source registry.
- No navigation changed: there is no new page, no new top-level route, and no new entry in the top
  nav bar. The feature lives entirely inside the already-shipped `/desk` → Hypothesis Foundry
  panel.

---

## What Old Behavior Changed

- None of the six existing Foundry subsections changed their own rendering or behavior. The
  backend response's `source_dispositions[]` entries are now enriched with additional provenance
  fields, but every field those six subsections already read is unchanged and still renders
  identically.
- No previously-visible number, label, or button moved or changed meaning.

---

## Not Visible Yet

- The optional read-only MCP data-access proxy for this same Final Summary/provenance information
  (`desk_micro_foundry`) was intentionally not built this iteration — explicitly deferred per the
  project's own plan, and it has no user-facing UI surface regardless (MCP is a machine
  interface, not a browser surface).
