# Phase goal-playbook-iter-4 — User-Visible Changes

**Phase:** goal-playbook-iter-4
**Date:** 2026-08-11
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On `/desk`, after running the Playbook for a session (same "Session date" input + "Run Playbook"
  button already shipped in J-03), the operator can now see up to three additional setup types fire
  in the Playbook Signals table, each with its own row and its own setup chip:
  - **"Jump-Base Explosion"** (`jbe`, long side) — a tight consolidation base after a sharp move up,
    then a breakout.
  - **"Drop-Base Implosion"** (`dbi`, short side) — the exact mirror, a breakdown after a sharp drop.
  - **"Cup and Handle"** (`cup_handle`, long side) — a rounded pullback-and-recovery followed by a
    smaller pullback, then a breakout above the pattern's own high.
- Users can now click a `jbe` or `dbi` signal row (same click-to-expand row interaction already
  shipped) and see a new geometry disclosure line beneath the trigger/invalidation line, showing:
  base width in MBR and bar count, jump size in MBR, the breakout slot, a "flatline base" note when
  the base range stayed under 1.0 MBR, an "ascending base" note when the base's own lows/highs
  moved the direction-appropriate way, and — only when this is the second firing of a `jbe`/`dbi`
  ladder within the same session — a ladder-step ratio comparing the new leg's jump size to the
  prior leg's.
- Users can now click a `cup_handle` signal row and see its own geometry disclosure line: cup bar
  count and depth (MBR), handle retrace fraction, handle duration fraction (of the cup's own
  duration), the breakout slot, "optimal cup length"/"desirable handle length" notes when those
  thresholds are met, and the three RVOL medians (cup middle third, cup outer thirds, handle).
- Every already-shipped disclosure on that same expanded row — the forward-measurement table, the
  invalidation-breach note, and the baseline-pool note — still renders for these new setup types,
  unchanged, beside the new geometry line (the exact same "what happened afterward" math already
  used for opening-range-break signals).

---

## What Changed in the Visible UI

- The Playbook Signals table's "setup" column (chip cell, both in the row and in the expanded
  detail panel) can now show three additional chip labels: "Jump-Base Explosion", "Drop-Base
  Implosion", "Cup and Handle" — using the exact same chip styling every other setup chip already
  uses. No new column, no new table.
- The expandable per-signal detail panel gained two new conditional lines that render only for the
  matching setup type: one shared jbe/dbi geometry line, one cup-and-handle geometry line. The
  already-shipped opening-range geometry line is now shown only for `open_high_break`/
  `open_low_break` signals (its own wording and values are unchanged for those signals — see "What
  Old Behavior Changed" below for the one nuance).
- No new page, no new route, no new navigation link, no new button, and no new input field. The
  session-date input and "Run Playbook" / poll / cancel controls are pixel-for-pixel the same
  controls J-03 shipped.

---

## What Old Behavior Changed

- **None for opening-range-break signals themselves.** The opening-range geometry line's own text
  and values are unchanged; it is now gated behind an explicit `setup_id` check instead of always
  rendering, but for every `open_high_break`/`open_low_break` signal the rendered output is
  identical to before this iteration (confirmed by the developer's own byte-identical-file proof
  and this iteration's TC-11 requirement).
- **One dated record disappeared from the store as iteration hygiene, not a feature change.** A
  leftover, git-ignored playbook record from a prior QA session
  (`playbook-2026-08-04-e0f249f57785.json`) was deleted from the operator's real
  `.data/playbook/` store as one of this iteration's carried housekeeping items. If an operator
  enters session date `2026-08-04` on `/desk` and no other legitimate record exists for that date,
  the Playbook Signals section will now show "Playbook not computed for this session." where it may
  previously have shown that stray record's signals table. This is disclosed here because it is a
  literal change to what renders for that one specific date query, even though the file itself was
  never a real operator record.

---

## Not Visible Yet

- The climax family (capitulation, euphoria marker — J-05) and the range family (range trades,
  double top/bottom — J-06) are not implemented; no chip, row, or geometry line exists for them.
  Each will land into this SAME Playbook Signals section with no new page when built.
- The back-scan (J-07, a resumable sweep of every recorded session) has not been run. This
  iteration's own dev-time verification stayed fixture-scoped only — nothing in the operator's real
  recorded universe has been checked yet for a genuine jbe/dbi/cup_handle firing, so on an arbitrary
  real session date the operator may see zero new-family signals even where the pattern might
  eventually be found once J-07 sweeps the real data.
- The evidence view (J-08, pooled distribution stats per setup/side/horizon) does not exist; there
  is no UI or API surface yet for "how did jbe signals do across every recorded session."
- The Playbook (all setup types, old and new) has no MCP surface at all yet — verified against
  `apps/backend/app/mcp/__init__.py`, which registers exactly 18 tools and none named
  `desk_playbook`. MCP stays at 18 read-only tools this iteration by design (J-09, "MCP contract
  v4," is explicitly out of scope). An operator using Claude+MCP cannot read any playbook signal —
  new-family or opening-range — today; only the browser at `/desk` and direct REST calls to
  `GET /research/desk/playbook` expose it.
