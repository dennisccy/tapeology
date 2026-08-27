# Phase goal-hypothesis-foundry-iter-5 — User-Visible Changes

**Phase:** goal-hypothesis-foundry-iter-5
**Date:** 2026-08-27
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open `/desk`, expand the **Hypothesis Foundry** panel, and click the new **Epoch / Manifest** subsection to see the era's one real, permanently-committed research decision: every one of the 11 required source objects' actual disposition (all currently blocked/excluded/aliased — zero compiled), plus the freeze identity (`epoch_id`, three content hashes, `freeze_commit`, `config_fingerprint`, `outcome_access_census`) and a reference to the committed independent audit report.
- Users can now see, inside **Sources / Compiler**, three fields that were computed all along but never shown on screen: `operative_formula_refs`, `superseded_fields`, and `aliases_lineage_ids` for every one of the 8 fixture rows (empty values show as an explicit `(none)` / `{}` / `[]` rather than being silently omitted).
- Users can now see both halves of the two-variant alias-family example in **Sources / Compiler** — `fixture-variant-a` and `fixture-variant-b` each appear as their own row (previously only `fixture-variant-a` was a top-level row, with `fixture-variant-b` only named inside `fixture-variant-a`'s "Alternatives" line).
- Users can now see a direct text reference to `reports/hypothesis-foundry/source-registry-audit.md` inside the **Sources / Compiler** subsection.
- Users can now see, inside **Hermetic Oracles**, a 7-row `kill_type_mapping` list (each of the 7 practice-test outcome labels — insufficient/null/direction/concentration/economic/fragile/survive — paired with its real internal `foundry_state`) and a new `best_of_n_disclosure` line (`n_variants_tried` / `threshold_bps`).

---

## What Changed in the Visible UI

- The Hypothesis Foundry panel on `/desk` gained a fifth collapsible subsection, **Epoch / Manifest**, appended directly after **Hermetic Oracles**.
- The new Epoch / Manifest subsection carries a distinct emerald-accented "Real Epoch — not a fixture" banner, visually different from the amber "Hermetic Fixture — not the real epoch" banner used on the four sibling subsections — so an operator cannot mistake the one real epoch for a practice/fixture demonstration.
- The panel-header line "Source registry hash" (visible even before expanding any subsection) now shows a real hash value instead of always reading "not_yet_generated" as it did in every prior iteration.
- The Sources/Compiler subsection's fixture list grew from 7 rows to 8 rows (the second alias-family sibling record is now its own row), and each row gained three new labeled lines: "Operative formula refs:", "Superseded fields:", and "Aliases/lineage ids:".
- The Hermetic Oracles subsection gained two new elements below "Outcome types present": a labeled list pairing each outcome label with its `foundry_state`, and a "Best-of-N disclosure:" line.

---

## What Old Behavior Changed

- The Hypothesis Foundry panel's top-level "Source registry hash" line: previously always showed the literal value `not_yet_generated` for every user in every session (hard-coded). It now reads the real, permanently committed value and will only ever show `not_yet_generated` again if the underlying committed files were somehow removed from the repository.
- The Sources/Compiler subsection previously showed exactly 7 fixture rows by design (one alias-family sibling was hidden). It now shows 8 — this is a display completeness fix, not a new dataset; existing users who counted "7 fixtures" will now see 8.

---

## Not Visible Yet

- No compiled candidates exist yet for the real epoch shown in Epoch / Manifest — the "Compiled families" list on that screen is honestly empty (a family/variant manifest UI exists and is wired up, but there is nothing populated to show this round). This is an expected, documented outcome, not a bug.
- The real deterministic exhaust pass (running the compiled candidates against real market data) has no UI or backend entrypoint at all yet — it is explicitly deferred to a future iteration and is not reachable from any screen.
- The optional read-only MCP proxy tool for the Foundry data was not built this iteration (deferrable per the project's own plan); the data is only reachable through the `/desk` UI and the existing REST endpoint, not via a dedicated MCP tool.
