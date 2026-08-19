# Phase goal-rapid-microscope-iter-15 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-15
**Date:** 2026-08-19
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see a **"Sealed Tranche (Aggregate Only)"** block inside the existing "Microscope
  Readiness" panel on `/desk` — sealed shard count, sealed symbol-days, and a per-universe
  breakdown table — numbers the panel's own endpoint has served since an earlier round but the page
  was silently dropping. Today's real corpus has zero sealed shards, so an operator will see honest
  zeroes ("0" / "0") and "No sealed shards recorded." rather than blank space.
- Users can now see a **"Joinable corpus — withheld (excluded)"** count in that same new block —
  how many playbook signals were excluded from the joinable-corpus tally because they fall inside a
  still-sealed shard. Today this reads "0" against the real corpus.
- Users can now expand a Walk-Forward sequence's "detail" toggle (the `<details>` under "Sequence
  verdict:") without triggering a red Next.js dev-overlay "Issues" warning — this previously
  happened on every expansion due to invalid HTML nesting.
- Users of the Claude/MCP machine surface (not the web page) can now ask a conversation to read the
  Microscope Readiness, Scout Ledger, Walk-Forward, and Validation Vault bodies directly — four new
  read-only MCP tools (`desk_micro_readiness`, `desk_scout`, `desk_walkforward`, `desk_vault`) bring
  the tool count from 22 to 26. This is not a web-page capability; there is no new button or link
  anywhere in the browser UI for this.

---

## What Changed in the Visible UI

- The **Microscope Readiness** section on `/desk` gains a new block, "Sealed Tranche (Aggregate
  Only)", positioned directly below the existing "Corpus Totals" table and above "Legacy Tick
  Shards". It contains a 3-row table (Sealed shard count / Sealed symbol-days / Joinable corpus —
  withheld (excluded)) plus either a per-universe breakdown table or the empty-state message "No
  sealed shards recorded." — nothing else on the Corpus Totals table above it changed.
- **Scout Ledger**'s per-family header text changes shape, from `"<family_id> — N variants tried"`
  to `"<family_id> (root <family_root_id>) — N variants tried"`. The real Scout ledger has zero
  registered families today, so this new text is not observable on the running app until a family
  exists (see "Not Visible Yet").
- **Walk-Forward**'s empty-sequences message changes from "No candidates ledgered." (Scout's own
  copy, reused by mistake) to "No walk-forward sequences run." The real Walk-Forward ledger already
  has one recorded sequence today, so this exact message is not observable live either (its
  underlying condition — zero sequences — isn't currently true; see "Not Visible Yet").
- **Walk-Forward**'s sequence-verdict block (the "Sequence verdict: ..." line with the "detail"
  toggle) now renders inside a `<div>` instead of a `<p>` — same text, same layout, same
  expand/collapse behavior; only the dev-overlay warning on expand is gone.
- **Validation Vault**'s loading and unreachable/error states now also carry
  `data-testid="validation-vault-section"` (previously only the loaded/success state had it). This
  produces no visible pixel change — it only matters to automated tooling that looks for that
  attribute, which could not find the section at all while the panel was loading or degraded.

---

## What Old Behavior Changed

- The Walk-Forward "detail" toggle previously produced a Next.js hydration-error dev-overlay badge
  (a red "5 Issues" indicator) the instant it was expanded, in every dev/QA environment running the
  app in development mode. It no longer does — expanding it now produces zero new console or
  dev-overlay messages.
- Nothing on the existing "Corpus Totals" table, the "Legacy Tick Shards" table, or the
  per-pilot-study floor table (all inside Microscope Readiness) changed value or meaning — the new
  Sealed Tranche block sits beside them, not inside them.

---

## Not Visible Yet

- **The Sealed Tranche block's non-zero rendering path has never been seen live in a browser.** The
  real `.data` store has zero registered vault universes today, so the running app can only show the
  honest all-zero state. The non-zero rendering (a real sealed shard, a real per-universe row) was
  proven correct via `tsc --noEmit` type-checking against the exact backend-transcribed shape plus
  backend contract tests, and independently traced field-by-field by the code reviewer against a
  constructed multi-universe fixture (through real production write functions, in an isolated
  store) — but not through a live click-through on the running app.
- **`family_root_id` differing from `family_id` has never been seen live**, for the identical
  reason: the real Scout ledger has zero registered families today.
- **`joinable_corpus.total` / `.playbook_signal_count` / `.band_touch_count` / `.by_setup_id` /
  `.playbook_integrity_errors` remain fetched and typed but are still not rendered anywhere on
  screen.** Only `.withheld_excluded` is shown this round; the rest are explicitly deferred (a
  plausible future home is the next journey, J-09).
- **The four new MCP tools have no on-screen equivalent.** There is no button, link, or page that
  exposes "26 tools" or lets a browser user trigger them — they exist only for a Claude/MCP
  conversation to call.
- **No dedicated Graduation UI section exists.** J-07 (`GET /research/desk/micro/graduation`) is
  reachable only by navigating directly to that URL on the backend port
  (`http://localhost:8301/research/desk/micro/graduation`) — there is no link to it, and no page
  renders its content, by design (documented in the route's own docstring).
