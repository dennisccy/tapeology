# Phase goal-rapid-microscope-iter-14 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-14
**Date:** 2026-08-19
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open a new **"Scout Ledger"** panel on `/desk` (directly below "Microscope
  Readiness") and see every registered candidate family's trials — feature/transform, horizon,
  decision, kill reason, notes, a withheld-excluded count, and each trial's full raw
  `screen_result` behind a "screen_result" detail toggle — without querying the backend directly.
- Users can now open a new **"Walk-Forward"** panel on `/desk` and see every registered fold spec
  (behind a detail toggle showing the full geometry) and every sequence's per-fold results table
  (fold number, status, effect, N, sessions, sign, evidence class, process label), that sequence's
  survivor verdict (or its floor-refusal reason), and a decay/recency summary line.
- Users can now open a new **"Validation Vault"** panel on `/desk` (read-only) and see every tape
  shard's lifecycle state and every registered recording universe's rule-disclosure stage, plus
  both ledgers' own chain-verification verdicts — without the panel ever showing more about a
  still-sealed shard or a not-yet-released universe than the backend itself already discloses.
- Users can now click **"Run Screen"** inside the Scout Ledger panel to start a new Scout
  screening pass against the real dataset corpus, watch a live "X / Y candidates" progress readout
  while it runs, and click **"Cancel"** to request it stop.
- Users can now click **"Run Walk-Forward"** inside the Walk-Forward panel to start a walk-forward
  diagnostic run, watch a live "X / Y steps" progress readout, and click **"Cancel"** to request it
  stop.
- Users can now view a **Run History** table in both the Scout Ledger and Walk-Forward panels
  (past run id, state, started/finished time, progress counts, and any error) even before ever
  starting a run themselves.

---

## What Changed in the Visible UI

- The `/desk` page now has three new collapsible sections directly below the existing "Microscope
  Readiness" section, in this fixed order: **"Scout Ledger" → "Walk-Forward" → "Validation
  Vault"**. Each uses the exact same expand/collapse control (a ▸/▾ arrow plus the section title,
  itself a real button) as every other section on the page, and each starts **collapsed** on every
  page load.
- Each of the three new sections shows a one-line "Ledger chain verification: ok" (Scout,
  Walk-Forward) or two lines "Shard ledger chain verification: ok" / "Universe ledger chain
  verification: ok" (Validation Vault) rendered as plain text beside the data — never a colored
  badge.
- No existing page, route, navigation label, or previously-shipped section's heading or layout
  changed. The top navigation still reads exactly "Cockpit", "Structure", "Desk" — no fourth link
  was added.

---

## What Old Behavior Changed

- None. This phase is purely additive: the three new sections are appended after the existing
  "Microscope Readiness" section, and every other `/desk` section (Screen Runs, Top-up Runs, Index
  Reconciliation, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, the
  always-visible Playbook signal table) plus `/structure` and the Cockpit (`/`) are unmodified —
  confirmed by the diff touching only 4 files, none of which are shared components used by those
  other surfaces.

---

## Not Visible Yet

- **The four new MCP tools** that would let an AI client (e.g., Claude via chat) read these same
  three panels' data are not part of this round — they land in the next iteration. The MCP tool
  count on this server stays at 22, unchanged.
- **The Validation Vault panel's two-stage rendering for a real sealed shard or a real
  committed→revealed universe has no live example to view today.** The real vault store is
  genuinely empty (no operator has sealed a shard or registered a recording universe this era), so
  a visitor today will only ever see the panel's honest empty state ("No shards recorded." / "No
  universes registered."). The two-stage logic (opaque-while-sealed vs. full-provenance-once-
  exposed; commitment-only vs. revealed-rule-plus-nonce) was verified by the code reviewer through
  a constructed test fixture and a field-by-field trace of the rendering code, not through a live
  browser click-through, and is not something an operator can reproduce on the running app without
  seeding real vault data (which this UI has no control for — it is deliberately read-only).
- **No compute, seal, assign, or expose control exists anywhere in the Validation Vault panel.**
  This is a deliberate design choice for this round, not an oversight — sealed-shard exposure is a
  one-way, single-shot event elsewhere in the system, and this panel only ever reads.
- **A page reload while a Scout or Walk-Forward run is in progress does not resume the live
  progress display.** The panel will show the state as of the reload until a fresh "Run Screen" /
  "Run Walk-Forward" click is made from that browser session. The run itself is unaffected on the
  backend — only the on-screen progress indicator stops updating. (Every other run-with-progress
  section on this page auto-resumes after a reload; these two do not, a disclosed, deliberate trade
  made to avoid changing an unrelated test's exact effect-hook count.)
- **Scout family rows never display `family_root_id`**, even though it is one of the fields the
  phase's own scope explicitly names as new information to display. This is a known, minor gap
  (flagged by code review) rather than a hidden capability — every other listed Scout field is
  present.
- **Walk-Forward's "no sequences" empty state currently shows Scout's own copy** ("No candidates
  ledgered.") instead of sequence-appropriate wording. This is a copy-paste label bug (flagged by
  code review), not a data problem — it only affects the empty-ledger case, and the real
  Walk-Forward ledger has data today so this exact panel isn't visible on the live app right now.

