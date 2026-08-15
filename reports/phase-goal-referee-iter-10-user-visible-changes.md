# Phase goal-referee-iter-10 — User-Visible Changes

**Phase:** goal-referee-iter-10
**Date:** 2026-08-15
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see every registered hypothesis's verdict by navigating to `/desk` and clicking
  the "Referee Adjudications" section header — each row shows a verdict chip reading one of
  `registered`, `pending_forward_confirmation`, `insufficient_sample`, `fragile`, `no_evidence`,
  `corroborated`, or `basis_retired`.
- Users can now see exactly why a hypothesis's confirmatory output was refused: when a checkpoint
  exists but its self-check fails, the row shows the backend's own refusal sentence ("the
  checkpoint evaluation's oracle attestation is missing, mismatched, or version-stale --
  confirmatory output is refused") instead of a fabricated or silently-passing result.
- Users can now inspect each hypothesis's full evidentiary paper trail in the same panel — the
  evaluation-basis hash, which null and test spec it used, its "seed identity," whether the
  statistical self-check (attestation) passed, the Benjamini-Hochberg fold values
  (`k_star`/`m`/`q`), and any fragility warnings — without leaving `/desk`.
- Users can now trigger a null-baseline compute for either matched-null procedure by clicking
  "Build Null" in the new "Referee Runs" section, and watch its `{done} / {total}` progress update
  live without reloading the page.
- Users can now trigger a full evaluation compute for any registered hypothesis by clicking
  "Evaluate" in the same section, with the same live progress readout.
- Users can now cancel an in-flight null-build or evaluation by clicking its "Cancel" button.
- Users can now review a full history of past null-build and evaluation runs (run id, state,
  start/finish time, error) in two ledger tables below the trigger controls.
- Outside the browser: a Claude connector session can now read the same adjudications and
  registry data through two new read-only tools, `desk_referee` and `desk_referee_registry`,
  joining the 20 tools that already existed (22 total). Nothing on the connector can write.

---

## What Changed in the Visible UI

- The `/desk` page now has two new collapsible sections, "Referee Adjudications" and "Referee
  Runs," inserted directly below the existing "Referee Registry" section — "Referee Runs" is now
  the last section on the page.
- "Referee Adjudications" shows a disclosure paragraph (served verbatim from the backend,
  beginning "Referee verdicts are statistical statements about recorded history under stated
  assumptions...") above a table with columns Hypothesis / Verdict / Status / Provenance /
  Fragility triggers — or the text "No hypotheses registered." if none exist yet.
- "Referee Runs" shows two labeled sub-blocks, "Null Builds" and "Evaluations," each with one
  trigger control per relevant key (one per distinct null spec in use; one per registered
  hypothesis) and its own run-history table underneath.
- Attempting a second trigger for the same null spec or hypothesis while one is already running
  now shows an inline message explaining the refusal, rather than silently doing nothing or
  starting a duplicate run.

---

## What Old Behavior Changed

None. Every previously-shipped `/desk` section (including "Referee Registry" directly above the
two new sections), the cockpit page, and the structure page render and behave exactly as before
this round — per the dev handoff, verified both by an automated source-level scan
(`test_desk_ui_guards.py`, `test_desk_refresh_chain_guard.py`) and by loading the page against a
real backend, after a clean `.next` rebuild, in the same browser session used to check the new
sections.

---

## Not Visible Yet

- The rider-1 certificate-evidence-identity fix (which now scopes evidence pooling to the exact
  candidate a certificate names) has no UI surface and will not have one this round or any prior
  one: the code path it protects (`certificate_mint`) still has zero production callers — no
  button, form, or CLI flag anywhere in the shipped product can reach it. It is a safety fix
  guarding a future wiring, not a capability change today.
- Two of the seven verdict states this panel is designed to show — `fragile` and a
  refused-attestation `insufficient_sample` — depend on fixture data that must be seeded
  separately (documented in the dev handoff's Known Issues) before they will appear on a given
  backend instance. Until that seeding happens, only whatever hypotheses are already registered
  there (as of this round, one: `S-1`, carried over from iteration 8) render in the panel.
